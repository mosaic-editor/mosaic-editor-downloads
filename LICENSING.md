# Mosaic Editor v0.1.0 licenses and corresponding source

Mosaic Editor is released under GNU AGPL-3.0-only with the owner's authorization.
The complete release source snapshot, build scripts, configuration, tests and
resources are provided as `MosaicEditor-Source-v0.1.0.zip` on the same release:
https://github.com/mosaic-editor/mosaic-editor-downloads/releases/tag/v0.1.0
The private development repository and Git history are not required to obtain
the released source. Source archives do not include personal projects or caches.

Third-party copyrights and license terms remain in force. They are not relicensed
under Mosaic Editor's license. Bundled package license texts accompany the Core
and Runtime Packs; Forenche and face-parser MIT notices accompany the Core.

## Models

- SCRFD `det_10g.onnx` is a pretrained InsightFace buffalo_l model. InsightFace
  code is MIT, but its pretrained models/data are restricted to **non-commercial
  research purposes only**. Do not interpret this release as granting commercial
  model rights. Policy: https://github.com/deepinsight/insightface#license
  Original mirror: https://huggingface.co/deepghs/insightface
- Forenche `segmentation_model.pt`: the original repository is MIT; its YOLO
  architecture/runtime remains subject to Ultralytics AGPL terms.
  https://github.com/Forenche/nsfw_detector_annotator/tree/release
- Face parsing `resnet18.onnx`, release v0.0.2: project MIT license and original
  dataset/model terms remain applicable. https://github.com/yakhyo/face-parsing

## Runtime upstreams and source

- PySide6/Qt 6.8.3 (LGPLv3): https://code.qt.io/cgit/pyside/pyside-setup.git/
  and https://code.qt.io/cgit/qt/ . DLLs remain separate from the application.
- FFmpeg GPLv3 build `N-118351-ga0a89efd07-20250125`: exact FFmpeg source commit
  https://github.com/FFmpeg/FFmpeg/tree/a0a89efd07 . Original Windows build scripts,
  dependency source references and configuration: https://github.com/BtbN/FFmpeg-Builds .
  https://ffmpeg.org/legal.html ; build configuration can be obtained with
  the installed `ffmpeg.exe -buildconf`.
- Ultralytics 8.4.164 (AGPLv3): https://github.com/ultralytics/ultralytics
  and https://www.ultralytics.com/license . Its Python source is included in
  the Genital AI dependency Pack; the complete application source is supplied above.
- PyTorch 2.14.0 / torchvision 0.29.0: https://github.com/pytorch/pytorch
  and https://github.com/pytorch/vision . CPU and CUDA wheel licenses are included.
- ONNX Runtime 1.24.4: https://github.com/microsoft/onnxruntime . MIT license included.
- NumPy 2.2.4: https://github.com/numpy/numpy ; OpenCV 4.11.0.86:
  https://github.com/opencv/opencv-python . Their license texts accompany the Core.

Runtime Pack versions, archive/segment digests and model digests are pinned in
`runtime-catalog.json`. The release does not offer model training-data rights.
