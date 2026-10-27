# Nrt5.Native

Nrt5.Native exposes the vendor's full NRT v5 C# API to .NET 9 applications on Windows x64.

Reference the package and target `win-x64`, or use an x64 Windows application. The managed assembly is `Nrt5Sdk.dll`. Its namespace is `nrt`.

The package contains the matching Windows Release DLLs. Native assets must remain beside the application in build and publish output. Install CodeMeter and obtain a valid NRT license. Install the device drivers and system prerequisites required by your selected backend.

The package does not install machine prerequisites or change environment variables. It does not support Linux, Windows x86, or Windows ARM64. Do not reference the v4 Nrt.Native package in the same application.

Use the vendor's status codes, error reporting, and disposal rules. Finish inference and dispose owned objects before global cleanup. The package does not add automatic global cleanup.

The vendor distribution is Neuro-R 5.0.3.7, containing SDK v5.0.3. Native binaries retain their vendor license terms. THIRD-PARTY-NOTICES.txt contains supplied open-source notices. Publication requires approved redistribution terms in LICENSE.txt and a licensed Windows inference test. A local validation package without LICENSE.txt is not approved for publication.

Build a local validation package with:

```bash
dotnet pack Nrt5.Native/Nrt5.Native.csproj -c Release -p:PackageVersion=0.0.0-local -o Nrt5.Native/.artifacts
```

## Windows runtime validation

Run this check on a licensed Windows x64 machine against a consumer restored and published from the exact candidate package. The model and image stay outside the package and are supplied by the tester:

```powershell
$consumer = "Nrt5.Native/.artifacts/publish/Consumer.dll"
$model = "C:/nrt-test/cla_ex_model.net"
$image = "C:/nrt-test/normal0.png"
dotnet $consumer --smoke $model $image DEVICE_CPU
Get-FileHash "Nrt5.Native/.artifacts/Nrt5.Native.0.0.0-local.nupkg" -Algorithm SHA256
```

`--smoke` takes a classification model, one image, and the name of an `nrt.DevType` member. Select a different backend if the license requires one. It infers twice, first from the paths as given and then from copies with Unicode file names, and it confirms that an invalid model path reports a vendor error. The program calls `nrt.cleanup()` and removes its temporary directory, then prints `PASS: licensed Windows smoke test` only after cleanup succeeds.

A passing run records:

- Operating system and .NET runtime versions
- Backend, device index, and device driver versions
- CodeMeter version
- Package SHA-256
- The complete command output, including an actual inference result

A successful native-library load is not sufficient. Record a real classification result. Publication requires this validation to pass against the same package hash that is published.

Run the program without arguments for the managed API check alone. That path does not invoke native inference and does not require a license.
