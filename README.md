# Mosaic Editor — Windows 下載

**Mosaic Editor 是一套專為影片打碼設計的 AI 輔助編輯工具。**

它可以先用 AI 自動辨識並建立打碼遮罩，再用手動工具補上 AI 漏掉的區域；如果自動遮罩蓋到不該遮的地方，也可以使用 **反遮罩** 把指定區域排除。

> **AI 先完成大部分工作，剩下的用繪製遮罩與反遮罩精修。**

## 主要功能

- **AI 自動打碼**：自動辨識影片中的目標並建立追蹤遮罩。
- **自由繪製遮罩**：直接在畫面上補上需要額外打碼的區域。
- **反遮罩**：把指定區域從打碼範圍中排除。
- **AI + 手動精修**：自動遮罩、手動畫面遮罩與反遮罩可搭配使用。
- **時間軸編輯**：調整遮罩持續時間、位置與結果。
- **影片輸出**：完成檢查後直接輸出成品。

## 下載

正式下載：[最新版本](https://github.com/tt840817/mosaic-editor-downloads/releases/latest)

一般使用者建議下載：

**`MosaicEditor-Setup.exe`**

| 檔案 | 使用方式 |
|---|---|
| `MosaicEditor-Setup.exe` | **建議一般使用者選擇。** 標準安裝版，提供開始功能表、可選桌面捷徑與解除安裝。 |
| `MosaicEditor-Portable.zip` | 免安裝版。完整解壓縮後雙擊內部 EXE；請保留 `_internal` 資料夾。 |
| `MosaicEditor.exe` | 單一 EXE 免安裝版；啟動時會將 Core 解壓到暫存目錄。 |

三種版本的主要功能相同。

## 系統需求

- Windows x64
- 不需要另裝 Python
- 不需要自行設定 PATH

## 第一次使用與 Runtime

為了降低主程式下載大小，FFmpeg、AI Runtime、模型及部分 GPU 元件會在**第一次真正需要時**才提示下載。

首次開啟影片或專案時需要 FFmpeg Pack。  
首次使用 AI 時，程式才會提示下載對應的 AI Runtime 與模型。

NVIDIA 大型 Runtime Pack 只會在相容 GPU 上、且取得使用者同意後下載；拒絕後仍可使用 CPU／DirectML。

下載完成的 Runtime 與模型會快取於：

`%LOCALAPPDATA%\MosaicEditor\runtimes`

更新或解除安裝主程式不會自動刪除這些 Runtime Pack、模型或使用者專案。

Runtime 檔案位於：

[獨立 Runtime Release](https://github.com/tt840817/mosaic-editor-downloads/releases/tag/runtime-v1-20261006)

一般情況下不需要手動下載。

## 授權

Mosaic Editor 以 **AGPL-3.0-only** 發布。

完整正式版本原始碼、建置腳本、設定、測試與資源位於正式 Release 內的：

`MosaicEditor-Source-v0.1.0.zip`

請注意：GitHub 自動產生的 `Source code.zip` / `Source code.tar.gz` 只包含這個公開下載入口 repository，**不是 Mosaic Editor 的完整程式原始碼，也不是免安裝版**。

開發 repository 與 Git 歷史仍維持私有；公開原始碼 ZIP 不包含 `.git`、個人專案或快取。

第三方元件與 AI 模型保留各自授權。

**SCRFD／InsightFace 預訓練模型僅供非商業研究用途。**  
AGPL 授權不會放寬第三方模型的使用限制。

詳見：[授權與來源](LICENSING.md)

## v0.1.0 已知事項

已在 Windows 10／RTX 3060 Ti 測試：

- 安裝與解除安裝
- Setup／Portable／單一 EXE
- CPU／DirectML／CUDA AI 推論
- native worker
- FFmpeg 基本短片流程

目前測試機上的 **H.264／HEVC NVENC 硬體編碼仍會發生 error 21**。  
CUDA AI 可正常運作，不代表 NVENC 硬體編碼一定可用，兩者是不同的 GPU 功能。

EXE 目前尚未配置 Authenticode 數位簽章，因此 Windows 第一次執行時可能顯示未知發行者相關提示。

檔案大小、SHA-256 與發布驗證記錄會隨正式 Release 提供。
