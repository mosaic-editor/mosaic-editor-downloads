import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import publisher as p


class FakeGitHub:
    def __init__(self):
        self.release = None
        self.assets = []
        self.calls = []
        self.fail_after_upload = False

    def request(self, method, endpoint, payload=None, file=None, missing_ok=False):
        self.calls.append((method, endpoint, payload))
        if method == "GET" and endpoint.startswith("/releases?"):
            return [copy.deepcopy(self.release)] if self.release else []
        if method == "GET" and "/git/ref/" in endpoint:
            return None
        if method == "GET" and "/assets" in endpoint:
            return copy.deepcopy(self.assets)
        if method == "GET":
            return copy.deepcopy(self.release)
        if method == "POST" and endpoint == "/releases":
            self.release = dict(payload, id=1, author={"login": p.BOT},
                upload_url=f"https://uploads.github.com/repos/{p.REPOSITORY}/releases/1/assets{{?name,label}}")
            return copy.deepcopy(self.release)
        if method == "POST" and file is not None:
            data = file.read()
            self.assets.append({"name": Path(file.name).name, "size": len(data),
                "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "uploader": {"login": p.BOT}, "state": "uploaded"})
            if self.fail_after_upload:
                self.fail_after_upload = False
                raise RuntimeError("Connection interrupted after a committed upload")
            return copy.deepcopy(self.assets[-1])
        raise AssertionError("Unexpected API mutation")


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.lock = {"schema": 1, "repository": p.REPOSITORY, "assets": []}
        for name in sorted(p.CORE_NAMES):
            self.lock["assets"].append(self.asset(name, b"pinned core", "v0.1.1"))
        runtime = self.asset("mosaic-runtime-ffmpeg-version-r1.zip", b"pinned runtime", "runtime-v1-20261006")
        self.lock["assets"].append(runtime)
        catalog = {"schema": 1, "abi": "cp312-win_amd64", "packs": {"ffmpeg": {"parts": [
            {k: runtime[k] for k in ("name", "bytes", "sha256")} ]}}}
        self.lock["catalog"] = self.asset("runtime-catalog.json", json.dumps(catalog).encode(), "runtime-v1-20261006")
        self.api = FakeGitHub()
        self.tag = "identity-smoke-20261008-1"

    def asset(self, name, data, tag):
        (self.directory / name).write_bytes(data)
        return {"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "source_tag": tag, "url": f"https://github.com/{p.REPOSITORY}/releases/download/{tag}/{name}"}

    def publish(self):
        return p.publish(self.api, self.lock, self.directory, self.tag, "a" * 40)

    def test_draft_bot_release_all_pins_and_no_deletions(self):
        result = self.publish()
        self.assertEqual(result["asset_count"], 4)
        self.assertEqual(self.api.release["make_latest"], "false")
        self.assertTrue(self.api.release["draft"])
        self.assertTrue(all(method in {"GET", "POST"} for method, _, _ in self.api.calls))
        self.assertNotIn("runtime-catalog.json", [a["name"] for a in self.api.assets])

    def test_idempotent_verified_assets_not_uploaded_twice(self):
        self.publish()
        self.api.calls.clear()
        self.publish()
        self.assertTrue(all(method == "GET" for method, _, _ in self.api.calls))

    def test_duplicate_drafts_are_rejected_without_mutation(self):
        self.publish()
        original = self.api.request
        def duplicate(method, endpoint, **kwargs):
            if endpoint.startswith("/releases?"):
                return [self.api.release, self.api.release]
            return original(method, endpoint, **kwargs)
        self.api.request = duplicate
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.publish()

    def test_interrupted_committed_upload_resumes_without_overwrite(self):
        self.api.fail_after_upload = True
        with self.assertRaises(RuntimeError):
            self.publish()
        self.assertEqual(len(self.api.assets), 1)
        self.publish()
        self.assertEqual(len(self.api.assets), 4)
        self.assertEqual(len({a["name"] for a in self.api.assets}), 4)

    def test_corrupt_staging_prevents_any_api_write(self):
        (self.directory / self.lock["assets"][-1]["name"]).write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(self.api.calls, [])

    def test_manifest_version_hash_mismatch_prevents_write(self):
        catalog = json.loads((self.directory / "runtime-catalog.json").read_text())
        catalog["packs"]["ffmpeg"]["parts"][0]["sha256"] = "b" * 64
        self.lock["catalog"] = self.asset("runtime-catalog.json", json.dumps(catalog).encode(), "runtime-v1-20261006")
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(self.api.calls, [])

    def test_formal_tags_and_unpinned_targets_rejected(self):
        for tag in ("v0.1.1", "runtime-v1-20261006", "../../main", "identity-smoke-20261008-1;echo injected"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                p.publish(self.api, self.lock, self.directory, tag, "a" * 40)
        with self.assertRaises(ValueError):
            p.publish(self.api, self.lock, self.directory, self.tag, "main")
        self.assertEqual(self.api.calls, [])

    def test_personal_author_uploader_or_wrong_digest_rejected(self):
        self.publish()
        for field, value in (("uploader", {"login": "human"}), ("digest", "sha256:" + "b" * 64),
                             ("state", "starter"), ("size", 1)):
            wrong = copy.deepcopy(self.api.assets)
            wrong[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                p.verify_assets(self.api.release, wrong, self.lock)
        release = copy.deepcopy(self.api.release)
        release["author"]["login"] = "human"
        with self.assertRaises(ValueError):
            p.verify_assets(release, self.api.assets, self.lock)

    def test_source_exports_private_urls_traversal_and_duplicates_rejected(self):
        for field, value in (("name", "../private.key"), ("url", "https://example.test/private"),
                             ("source_tag", "v9.9.9")):
            lock = copy.deepcopy(self.lock)
            lock["assets"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                p.validate_lock(lock)
        lock = copy.deepcopy(self.lock)
        lock["assets"].append(lock["assets"][0])
        with self.assertRaises(ValueError):
            p.validate_lock(lock)

    def test_workflow_boundary_personal_dispatch_and_wrong_repo_rejected(self):
        good = {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": p.REPOSITORY,
                "GITHUB_ACTOR": "organization-publisher[bot]", "GITHUB_TOKEN": "not-a-real-token"}
        p.require_actions(good)
        for field, value in (("GITHUB_ACTIONS", "false"), ("GITHUB_REPOSITORY", "private/source"),
                             ("GITHUB_ACTOR", "human"), ("GITHUB_TOKEN", "")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                p.require_actions(dict(good, **{field: value}))

    def test_download_never_authenticates_and_reuses_verified_file(self):
        asset = self.lock["assets"][0]
        path = self.directory / asset["name"]
        data = path.read_bytes()
        path.unlink()
        calls = []
        def opener(request, timeout):
            calls.append(request)
            self.assertNotIn("Authorization", request.headers)
            response = io.BytesIO(data)
            response.status = 200
            return response
        p.download(asset, self.directory, opener)
        p.download(asset, self.directory, opener)
        self.assertEqual(len(calls), 1)

    def test_download_wrong_sha_or_partial_response_not_committed(self):
        asset = self.lock["assets"][0]
        path = self.directory / asset["name"]
        path.unlink()
        def opener(request, timeout):
            response = io.BytesIO(b"damaged file")
            response.status = 200
            return response
        with patch.object(p.time, "sleep"), self.assertRaises(ValueError):
            p.download(asset, self.directory, opener)
        self.assertFalse(path.exists())

    def test_api_credential_host_scope_and_response_redaction(self):
        api = p.GitHub("private-token-value", opener=lambda *args, **kwargs: None)
        for url in ("https://example.test/upload", "https://api.github.com/repos/private/source/releases"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                api.request("POST", url)
        def failed(request, timeout):
            raise HTTPError(request.full_url, 403, "private-token-value", {}, io.BytesIO(b"private-token-value"))
        with self.assertRaisesRegex(RuntimeError, "HTTP 403") as caught:
            p.GitHub("private-token-value", opener=failed).request("POST", "/releases")
        self.assertNotIn("private-token-value", str(caught.exception))
        with self.assertRaises(ValueError):
            api.request("DELETE", "/releases/1")


if __name__ == "__main__":
    unittest.main()
