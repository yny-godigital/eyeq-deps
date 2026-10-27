import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
NATIVE = "runtimes/win-x64/native/"
SOURCE = "src/Nrt5Sdk/Generated/nrt.cs"
DLLS = {
    "DirectML.DLL", "dongle_chk.dll", "nrt.dll", "nvinfer_10.dll",
    "nvinfer_builder_resource_10.dll", "nvonnxparser_10.dll",
    "onnxruntime_providers_shared.dll", "opencv_world4120.dll",
    "openvino.dll", "openvino_c.dll", "openvino_intel_cpu_plugin.dll",
    "openvino_intel_gpu_plugin.dll", "openvino_intel_npu_plugin.dll",
    "openvino_onnx_frontend.dll", "tbb12.dll",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(stream):
    return hashlib.file_digest(stream, "sha256").hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def manifest():
    data = json.loads((ROOT / "vendor-manifest.json").read_text())
    require(data["distribution_version"] == "5.0.3.7", "Unexpected distribution")
    require(data["sdk_version"] == "5.0.3", "Unexpected SDK version")
    require(data["entry_point_count"] == 1364, "Unexpected entry-point count")
    expected = {SOURCE, "THIRD-PARTY-NOTICES.txt"} | {NATIVE + name for name in DLLS}
    require(set(data["files"]) == expected, "Unexpected vendor file inventory")
    return data


def check_inputs():
    data = manifest()
    actual = {path.name for path in (ROOT / NATIVE).iterdir() if path.is_file()}
    require(actual == DLLS, "Native file inventory differs")
    for name, expected in data["files"].items():
        require(file_digest(ROOT / name) == expected, f"Checksum differs: {name}")
    source = (ROOT / SOURCE).read_text()
    imports = set(re.findall(r'EntryPoint="([^"]+)"', source))
    require(len(imports) == 1364, "Managed entry-point count differs")
    output = subprocess.check_output(
        ["objdump", "-p", str(ROOT / NATIVE / "nrt.dll")], text=True
    )
    exports = set(re.findall(r"^\s*\[\s*\d+\]\s+(\S+)\s*$", output, re.M))
    require(not imports - exports, f"Missing exports: {sorted(imports - exports)}")
    print("PASS: vendor checksums and 1364 native entry points")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inputs"])
    args = parser.parse_args()
    if args.action == "inputs":
        check_inputs()


if __name__ == "__main__":
    main()
