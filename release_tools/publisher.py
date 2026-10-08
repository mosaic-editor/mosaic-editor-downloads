"""Publish an isolated, pinned binary smoke release using this repository's token.

No private checkout, source archive export, existing asset replacement or deletion.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

REPOSITORY = "mosaic-editor/mosaic-editor-downloads"
BOT = "github-actions[bot]"
SMOKE_TAG = re.compile(r"identity-smoke-[0-9]{8}-[0-9]+\Z")
ASSET_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CORE_NAMES = {"MosaicEditor-Setup.exe", "MosaicEditor-Portable.zip", "MosaicEditor.exe"}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_lock(lock):
    if lock.get("schema") != 1 or lock.get("repository") != REPOSITORY:
        raise ValueError("Unexpected publishing repository or lock schema")
    names = set()
    for asset in [*lock["assets"], lock["catalog"]]:
        name = asset["name"]
        if not ASSET_NAME.fullmatch(name) or name in names:
            raise ValueError("Invalid or duplicate asset name")
        names.add(name)
        if not SHA256.fullmatch(asset["sha256"]) or type(asset["bytes"]) is not int or asset["bytes"] <= 0:
            raise ValueError("Missing pinned digest or size")
        tag = asset["source_tag"]
        allowed = (tag == "v0.1.1" and name in CORE_NAMES) or (
            tag == "runtime-v1-20261006" and (name == "runtime-catalog.json" or
            name.startswith("mosaic-runtime-") and re.fullmatch(r".*\.zip(?:\.part[0-9]{3})?", name)))
        expected = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{name}"
        if not allowed or asset["url"] != expected:
            raise ValueError("Only explicitly pinned public binary/runtime assets may be copied")
    if not CORE_NAMES <= names or "runtime-catalog.json" not in names:
        raise ValueError("Core formats and runtime catalog are required")
    if lock["catalog"]["name"] != "runtime-catalog.json":
        raise ValueError("Catalog is a verification input, not a newly uploaded legacy text asset")


def validate_catalog(lock, directory):
    asset = lock["catalog"]
    path = Path(directory) / asset["name"]
    if path.stat().st_size != asset["bytes"] or digest(path) != asset["sha256"]:
        raise ValueError("Catalog digest mismatch")
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if catalog.get("schema") != 1 or catalog.get("abi") != "cp312-win_amd64":
        raise ValueError("Unsupported runtime catalog")
    parts = {}
    for pack in catalog["packs"].values():
        for part in pack["parts"]:
            if part["name"] in parts:
                raise ValueError("Duplicate catalog part")
            parts[part["name"]] = part
    pinned = {a["name"]: a for a in lock["assets"] if a["name"] not in CORE_NAMES}
    if parts.keys() != pinned.keys() or any(
            part["bytes"] != pinned[name]["bytes"] or part["sha256"] != pinned[name]["sha256"]
            for name, part in parts.items()):
        raise ValueError("Runtime assets must exactly match the published catalog's versions and hashes")


def download(asset, directory, opener=urlopen):
    target = Path(directory) / asset["name"]
    if target.is_file() and target.stat().st_size == asset["bytes"] and digest(target) == asset["sha256"]:
        return target
    temporary = target.with_name(target.name + ".partial")
    for attempt in range(3):
        try:
            # Public downloads deliberately receive no authentication header.
            request = Request(asset["url"], headers={"Accept-Encoding": "identity"})
            with opener(request, timeout=120) as response, temporary.open("wb") as output:
                if response.status != 200:
                    raise ValueError("Expected a complete HTTP 200 asset")
                size = 0
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > asset["bytes"]:
                        raise ValueError("Asset exceeds its pinned size")
                    output.write(chunk)
            if size != asset["bytes"] or digest(temporary) != asset["sha256"]:
                raise ValueError("Public asset SHA-256 or size mismatch")
            temporary.replace(target)
            return target
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


class GitHub:
    def __init__(self, token, opener=urlopen):
        self.token = token
        self.opener = opener

    def request(self, method, endpoint, payload=None, file=None, missing_ok=False):
        if method not in {"GET", "POST"}:
            raise ValueError("This publisher never deletes or changes existing releases/assets")
        if endpoint.startswith("https://"):
            url = endpoint
        else:
            url = "https://api.github.com/repos/" + REPOSITORY + endpoint
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc not in {"api.github.com", "uploads.github.com"}:
            raise ValueError("Refusing to send credentials outside the GitHub API")
        expected_prefix = "/repos/" + REPOSITORY + "/"
        if not parsed.path.startswith(expected_prefix):
            raise ValueError("Refusing to write outside the publishing repository")
        headers = {"Authorization": "Bearer " + self.token,
                   "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        data = json.dumps(payload).encode() if payload is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        if file is not None:
            headers.update({"Content-Type": "application/octet-stream", "Content-Length": str(Path(file.name).stat().st_size)})
            data = file
        request = Request(url, data=data, headers=headers, method=method)
        # API redirects must never forward the token to another host/repository.
        from urllib.request import HTTPRedirectHandler, build_opener

        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = build_opener(NoRedirect()).open if self.opener is urlopen else self.opener
        try:
            with opener(request, timeout=300) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 404 and missing_ok:
                return None
            raise RuntimeError(f"GitHub {method} failed with HTTP {exc.code}; response body omitted") from None


def verify_assets(release, assets, lock):
    if release["author"]["login"] != BOT or not release["draft"] or not release["prerelease"]:
        raise ValueError("Smoke release must remain a draft prerelease authored by Actions")
    expected = {a["name"]: a for a in lock["assets"]}
    seen = set()
    for asset in assets:
        pinned = expected.get(asset["name"])
        if pinned is None or asset["name"] in seen:
            raise ValueError("Unexpected or duplicate uploaded asset")
        seen.add(asset["name"])
        if (asset["uploader"]["login"] != BOT or asset["size"] != pinned["bytes"] or
                asset.get("digest") != "sha256:" + pinned["sha256"] or asset.get("state") != "uploaded"):
            raise ValueError("Uploader identity, size, digest or upload state mismatch")
    return seen


def publish(api, lock, directory, tag, target):
    validate_lock(lock)
    if not SMOKE_TAG.fullmatch(tag) or not re.fullmatch(r"[0-9a-f]{40}", target):
        raise ValueError("Only isolated smoke tags at an explicit commit are supported")
    # Complete and validate every download before performing any external write.
    for asset in lock["assets"]:
        path = Path(directory) / asset["name"]
        if not path.is_file() or path.stat().st_size != asset["bytes"] or digest(path) != asset["sha256"]:
            raise ValueError("All staged files must match the lock before publishing")
    validate_catalog(lock, directory)
    # The tag endpoint is for published releases; enumerate authenticated drafts
    # too, so rerunning an interrupted draft never creates another release.
    matches = []
    for page in range(1, 101):
        listed = api.request("GET", f"/releases?per_page=100&page={page}")
        matches.extend(item for item in listed if item["tag_name"] == tag)
        if len(listed) < 100:
            break
    else:
        raise ValueError("Release listing exceeded safety limit")
    if len(matches) > 1:
        raise ValueError("Duplicate smoke drafts require manual inspection")
    release = matches[0] if matches else None
    if release is None:
        if api.request("GET", "/git/ref/tags/" + tag, missing_ok=True) is not None:
            raise ValueError("Existing tag without smoke release requires manual inspection")
        release = api.request("POST", "/releases", {
            "tag_name": tag, "target_commitish": target, "name": "Publisher identity verification",
            "body": "Isolated identity test. Copies existing pinned public binaries; not a new product version.",
            "draft": True, "prerelease": True, "make_latest": "false", "generate_release_notes": False})
    if release["tag_name"] != tag or release["target_commitish"] != target:
        raise ValueError("Existing smoke release does not match this tag and commit")
    assets = api.request("GET", f"/releases/{release['id']}/assets?per_page=100")
    seen = verify_assets(release, assets, lock)
    upload_url = release["upload_url"].split("{", 1)[0]
    expected_upload = f"https://uploads.github.com/repos/{REPOSITORY}/releases/{release['id']}/assets"
    if upload_url != expected_upload:
        raise ValueError("Unexpected asset upload endpoint")
    for asset in lock["assets"]:
        if asset["name"] in seen:
            continue
        with (Path(directory) / asset["name"]).open("rb") as stream:
            # No automatic POST retry: rerun lists committed assets and verifies them first.
            api.request("POST", upload_url + "?name=" + quote(asset["name"], safe=""), file=stream)
    final = api.request("GET", f"/releases/{release['id']}")
    assets = api.request("GET", f"/releases/{release['id']}/assets?per_page=100")
    if len(verify_assets(final, assets, lock)) != len(lock["assets"]):
        raise ValueError("Incomplete smoke release")
    return {"tag": tag, "release_id": final["id"], "author": BOT, "asset_count": len(assets),
            "draft": True, "prerelease": True, "sha256_verified": True}


def require_actions(environment):
    if (environment.get("GITHUB_ACTIONS") != "true" or environment.get("GITHUB_REPOSITORY") != REPOSITORY or
            not environment.get("GITHUB_ACTOR", "").endswith("[bot]")):
        raise ValueError("Publishing requires a bot-triggered Actions run in the public repository")
    if not environment.get("GITHUB_TOKEN"):
        raise ValueError("Missing repository GITHUB_TOKEN")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=Path("release_tools/smoke-lock.json"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    require_actions(os.environ)
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    validate_lock(lock)
    args.directory.mkdir(parents=True, exist_ok=True)
    for asset in [*lock["assets"], lock["catalog"]]:
        download(asset, args.directory)
    result = publish(GitHub(os.environ["GITHUB_TOKEN"]), lock, args.directory, args.tag, os.environ["GITHUB_SHA"])
    print(json.dumps(result))
    (args.directory / "identity-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
