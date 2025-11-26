#!/usr/bin/env python
"""Quick GPU and CUDA check."""

import torch

print("=" * 60)
print("GPU & CUDA CHECK")
print("=" * 60)

print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"CUDNN version: {torch.backends.cudnn.version()}")
    print(f"\nGPU Information:")
    print(f"  Device count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"\n  GPU {i}:")
        print(f"    Name: {props.name}")
        print(f"    Capability: {props.major}.{props.minor}")
        print(f"    Total Memory: {props.total_memory / 1e9:.1f} GB")
        print(f"    Allocated: {torch.cuda.memory_allocated(i) / 1e9:.1f} GB")
        print(f"    Reserved: {torch.cuda.memory_reserved(i) / 1e9:.1f} GB")

    # Test GPU computation
    print(f"\nGPU Computation Test:")
    try:
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        print(f"  ✓ GPU computation works")
    except Exception as e:
        print(f"  ✗ GPU computation failed: {e}")

else:
    print("\n⚠ CUDA NOT AVAILABLE!")
    print("This means PyTorch is not using GPU acceleration.")
    print("\nTo fix:")
    print("  1. Check if GPU is detected by OS: nvidia-smi")
    print("  2. Reinstall PyTorch with CUDA support:")
    print("     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("  3. Set CUDA_HOME: export CUDA_HOME=/usr/local/cuda")

print("\n" + "=" * 60)
