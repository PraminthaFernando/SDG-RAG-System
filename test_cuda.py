import torch

print("🔥 PyTorch CUDA Test")
print("----------------------")

print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("CUDA version:", torch.version.cuda)
    print("GPU device:", torch.cuda.get_device_name(0))
    print("GPU count:", torch.cuda.device_count())

    # Simple tensor test on GPU
    x = torch.rand(3, 3).cuda()
    print("Tensor on GPU:", x)
else:
    print("❌ CUDA is NOT available. Running on CPU.")