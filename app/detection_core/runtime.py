# app/detection_core/runtime.py
import torch
from .freqnet import freqnet

class _Runtime:
    def __init__(self, ckpt_path: str, device: str):
        self.device = torch.device(device)
        self.model = freqnet()                     # 필요 시 생성자 인자 맞춰주세요
        ckpt = torch.load(ckpt_path, map_location='cpu')
        self.model.load_state_dict(ckpt.get('model', ckpt), strict=False)
        self.model.eval().to(self.device)
        torch.set_grad_enabled(False)
        if self.device.type == 'cuda':
            self.model = self.model.half()         # GPU면 fp16로 메모리 절감

runtime = None

def startup(ckpt_path: str):
    global runtime
    if runtime is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        runtime = _Runtime(ckpt_path, device)
    return runtime
