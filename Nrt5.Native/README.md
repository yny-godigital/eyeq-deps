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
