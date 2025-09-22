# # app/detection_core/runtime.py
# import torch
# from .freqnet import freqnet

# class _Runtime:
#     def __init__(self, ckpt_path: str, device: str):
#         self.device = torch.device(device)
#         self.model = freqnet()                     # 필요 시 생성자 인자 맞춰주세요
#         ckpt = torch.load(ckpt_path, map_location='cpu')
#         self.model.load_state_dict(ckpt.get('model', ckpt), strict=False)
#         self.model.eval().to(self.device)
#         torch.set_grad_enabled(False)
#         if self.device.type == 'cuda':
#             self.model = self.model.half()         # GPU면 fp16로 메모리 절감

# runtime = None

# def startup(ckpt_path: str):
#     global runtime
#     if runtime is None:
#         device = 'cuda' if torch.cuda.is_available() else 'cpu'
#         runtime = _Runtime(ckpt_path, device)
#     return runtime

# app/detection_core/runtime.py
import os, torch, gc

class _Runtime:
    def __init__(self, ckpt_path: str, device: str):
        self.device = torch.device(device)
        from .freqnet import freqnet
        self.model = freqnet().eval()

        # ✅ weights_only=True로 로드(메모리/로드속도↓)
        ckpt = torch.load(ckpt_path, map_location='cpu', weights_only=True)
        state = ckpt.get('model', ckpt)
        self.model.load_state_dict(state, strict=False)

        # ✅ 모든 파라미터는 학습비활성화(그라디언트 추적 방지)
        for p in self.model.parameters():
            p.requires_grad_(False)

        self.model.to(self.device)
        torch.set_grad_enabled(False)

runtime = None

def startup(ckpt_path: str):
    global runtime
    if runtime is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        runtime = _Runtime(ckpt_path, device)
        gc.collect()
    return runtime
