from dataclasses import dataclass

import torch
from transformers import Sam3Model, Sam3Processor


MODEL_ID = "facebook/sam3"
MODEL_DTYPE = torch.float16


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@dataclass
class ModelRuntime:
    device: torch.device
    model: Sam3Model | None
    processor: Sam3Processor | None
    load_error: Exception | None = None

    def ensure_ready(self) -> None:
        if self.model is not None and self.processor is not None:
            return
        raise RuntimeError("SAM3 model runtime is not available.") from self.load_error


def load_model_runtime() -> ModelRuntime:
    device = select_device()

    try:
        model = Sam3Model.from_pretrained(MODEL_ID, torch_dtype=MODEL_DTYPE).to(device)
        processor = Sam3Processor.from_pretrained(MODEL_ID)
        print("SAM3 loaded.")
        return ModelRuntime(device=device, model=model, processor=processor)
    except Exception as exc:
        print(f"SAM3 load error: {exc}")
        return ModelRuntime(device=device, model=None, processor=None, load_error=exc)
