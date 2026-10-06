# Mosaic Editor — Windows 下載

正式下載：[最新版本](https://github.com/tt840817/mosaic-editor-downloads/releases/latest)。

三種精簡 Core 擇一：

| 檔案 | 使用方式 |
|---|---|
| `MosaicEditor-Setup.exe` | 建議一般使用者選擇；提供安裝、開始功能表、可選桌面捷徑與解除安裝。 |
| `MosaicEditor-Portable.zip` | 完整解壓後雙擊內部 EXE；保留 `_internal` 資料夾。 |
| `MosaicEditor.exe` | 單一 EXE 免安裝；啟動時解壓 Core 到暫存目錄。 |

Windows x64，不需另裝 Python。Core 只含啟動、專案、時間軸、手動遮罩與播放所需依賴。
首次開啟影片／專案需下載 FFmpeg Pack；首次 AI 使用才提示下載對應 Runtime／模型。
NVIDIA 大型 Pack 僅在相容 GPU 且經同意後下載；拒絕後仍可使用 CPU／DirectML。
Pack 以獨立版本與 SHA-256 驗證，快取於 `%LOCALAPPDATA%\MosaicEditor\runtimes`，
更新／解除安裝主程式不清除 Pack、模型或專案。大型 NVIDIA Pack 自動下載三段並合併。
Runtime 檔案位於 [獨立 Runtime Release](https://github.com/tt840817/mosaic-editor-downloads/releases/tag/runtime-v1-20261006)，
由程式自動下載，通常不需要手動下載。

程式以 **AGPL-3.0-only** 發布。完整正式版本原始碼、建置腳本、設定、測試及資源
位於正式版的 `MosaicEditor-Source-v0.1.0.zip`；GitHub 自動產生的 Source code ZIP
只包含這個下載入口 repo，請勿拿它當成 Mosaic Editor 程式原始碼或免安裝版。
開發 repo 與 Git 歷史仍維持私有，公開原始碼 ZIP 沒有 `.git`、個人專案或快取。

第三方元件保留自己的授權。**SCRFD／InsightFace 預訓練模型僅供非商業研究**，
AGPL 不會放寬模型限制。詳見 [授權與來源](LICENSING.md)。

已在 Windows 10／RTX 3060 Ti 測試安裝、解除安裝、三種格式、CPU／DirectML／CUDA
AI 推論、native worker 及 FFmpeg 短片。H.264／HEVC NVENC 在測試機仍失敗（error 21）；
不要將 CUDA AI 成功視為 NVENC 全面通過。乾淨 Windows、其他 GPU、UAC／Program Files、
長片與真人目視驗收仍需補充。EXE 尚未配置 Authenticode 簽章。

檔案大小、SHA-256 與發布驗證記錄隨正式 Release 提供。
