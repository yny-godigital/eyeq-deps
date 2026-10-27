using nrt;

if (args.Length == 0)
{
    Console.WriteLine(typeof(PredictorV2).Assembly.GetName().Name);
    Console.WriteLine(typeof(ModelV2).FullName);
    Console.WriteLine(typeof(InputV2).FullName);
    Console.WriteLine(typeof(FlowchartV2).FullName);
    return;
}
if (args.Length != 4 || args[0] != "--smoke")
    throw new ArgumentException("Usage: --smoke MODEL IMAGE BACKEND");
if (!OperatingSystem.IsWindows() || !Environment.Is64BitProcess)
    throw new PlatformNotSupportedException("Native tests require Windows x64.");

Smoke(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Enum.Parse<DevType>(args[3]));

static void Check(bool condition, string message)
{
    if (!condition)
        throw new InvalidOperationException(message);
}

static void CheckStatus(Status status, string operation)
{
    Check(status == Status.STATUS_SUCCESS, $"{operation}: {nrt.nrt.get_last_error_msg()}");
}

static void Infer(string model, string image, DevType backend)
{
    using var predictor = new PredictorV2(model, ModelV2.MODELIO_DEFAULT, 0, 1, false, false, backend);
    CheckStatus(predictor.get_status(), "Predictor initialization");
    using var input = new InputV2();
    CheckStatus(input.extend(image, 3), "Image input");
    using var result = predictor.predict(input);
    CheckStatus(result.get_status(), "Inference");
    using var classes = result.classes;
    using var probabilities = result.probs;
    Check(classes is not null && classes.get_count() == 1, "Expected one classification result.");
    Check(probabilities is not null, "Classification probabilities are missing.");
    using var classification = classes!.get(0);
    Check(classification.idx >= 0 && classification.idx < predictor.get_num_classes(), "Invalid class index.");
    var probability = probabilities!.get(0, classification.idx);
    Check(float.IsFinite(probability) && probability >= 0 && probability <= 1, "Invalid class probability.");
    Console.WriteLine($"Class: {predictor.get_class_name(classification.idx)}, probability: {probability}");
}

static void CheckInvalidModel(string directory)
{
    string failure = "";
    try
    {
        using var model = new ModelV2(Path.Combine(directory, "missing.net"));
        if (model.get_status() != Status.STATUS_SUCCESS)
            failure = nrt.nrt.get_last_error_msg();
    }
    catch (Exception error) when (error is not DllNotFoundException
                                and not EntryPointNotFoundException
                                and not BadImageFormatException)
    {
        failure = error.Message;
    }
    Check(!string.IsNullOrWhiteSpace(failure), "The invalid model path did not report an error.");
    Console.WriteLine($"Expected invalid-model error: {failure}");
}

static void Smoke(string model, string image, DevType backend)
{
    Check(File.Exists(model) && File.Exists(image), "The model and image must exist.");
    var directory = Path.Combine(Path.GetTempPath(), $"nrt5-测试-{Guid.NewGuid():N}");
    Directory.CreateDirectory(directory);
    bool nativeLoaded = false;
    try
    {
        var version = nrt.nrt.get_version_str();
        nativeLoaded = true;
        Check(version.Contains("5.0.3"), $"Unexpected native version: {version}");
        Console.WriteLine($"Native version: {version}, backend: {backend}, device index: 0");
        var unicodeModel = Path.Combine(directory, "模型.net");
        var unicodeImage = Path.Combine(directory, "图像" + Path.GetExtension(image));
        File.Copy(model, unicodeModel);
        File.Copy(image, unicodeImage);
        Infer(model, image, backend);
        Infer(unicodeModel, unicodeImage, backend);
        CheckInvalidModel(directory);
    }
    finally
    {
        if (nativeLoaded)
            nrt.nrt.cleanup();
        Directory.Delete(directory, true);
    }
    Console.WriteLine("PASS: licensed Windows smoke test");
}
