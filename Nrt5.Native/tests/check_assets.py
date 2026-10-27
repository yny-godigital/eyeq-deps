import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

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


def check_package(path, version):
    data = manifest()
    expected = {"lib/net9.0/Nrt5Sdk.dll", "build/Nrt5.Native.targets", "README.md"}
    expected |= {NATIVE + name for name in DLLS}
    expected.add("THIRD-PARTY-NOTICES.txt")
    if (ROOT / "LICENSE.txt").exists():
        expected.add("LICENSE.txt")
    with zipfile.ZipFile(path) as package:
        payload = {
            name for name in package.namelist()
            if not name.endswith("/") and not name.endswith(".nuspec")
            and name not in {"[Content_Types].xml", "_rels/.rels"}
            and not name.startswith("package/services/metadata/")
        }
        require(payload == expected, f"Unexpected package payload: {payload ^ expected}")
        for name, checksum in data["files"].items():
            if name == SOURCE:
                continue
            with package.open(name) as stream:
                require(digest(stream) == checksum, f"Packaged checksum differs: {name}")
        for name in ["README.md", "build/Nrt5.Native.targets", "LICENSE.txt"]:
            if name in expected:
                require(package.read(name) == (ROOT / name).read_bytes(), f"Changed package file: {name}")
        nuspec = next(name for name in package.namelist() if name.endswith(".nuspec"))
        metadata = ET.fromstring(package.read(nuspec)).find("{*}metadata")
        require(metadata.findtext("{*}id") == "Nrt5.Native", "Wrong package ID")
        require(metadata.findtext("{*}version") == version, "Wrong package version")
        require(package.read("lib/net9.0/Nrt5Sdk.dll")[:2] == b"MZ", "Invalid managed assembly")
        license_node = metadata.find("{*}license")
        if "LICENSE.txt" in expected:
            require(license_node is not None and license_node.text == "LICENSE.txt", "Missing license metadata")
            require(license_node.get("type") == "file", "License must identify its file")
        else:
            require(license_node is None, "Validation package must not claim an unapproved license")
    print("PASS: package contents, checksums, and metadata")


def check_output(directory):
    data = manifest()
    for name in DLLS:
        require(file_digest(directory / name) == data["files"][NATIVE + name], f"Deployment differs: {name}")
    require((directory / "Nrt5Sdk.dll").is_file(), "Managed bindings are missing")
    print("PASS: deployed managed assembly and 15 native DLLs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inputs", "package", "output"])
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.action == "inputs":
        check_inputs()
    elif args.action == "package":
        require(args.path is not None and args.version, "Package path and version are required")
        check_package(args.path, args.version)
    else:
        require(args.path is not None, "Output directory is required")
        check_output(args.path)


if __name__ == "__main__":
    main()
