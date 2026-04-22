import gc
import io
import uuid
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

from .config import AppConfig
from .model_runtime import MODEL_DTYPE, ModelRuntime
from .processing import get_perspective_metadata, process_shadow_catcher_v2, resize_for_ai


def _mask_url(filename: str) -> str:
    return f"/static/masks/{filename}"


def _write_image(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"Failed to write image artifact: {path.name}")


def _prepare_model_inputs(ai_image: Image.Image, label: str, runtime: ModelRuntime) -> dict[str, torch.Tensor]:
    runtime.ensure_ready()
    inputs = runtime.processor(images=ai_image, text=label, return_tensors="pt").to(runtime.device)
    return {
        key: value.to(MODEL_DTYPE) if value.dtype == torch.float32 else value
        for key, value in inputs.items()
    }


def analyze_image(image_bytes: bytes, runtime: ModelRuntime, config: AppConfig) -> dict[str, Any]:
    runtime.ensure_ready()

    job_id = str(uuid.uuid4())[:8]
    raw_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_size = raw_image.size
    img_np = cv2.cvtColor(np.array(raw_image), cv2.COLOR_RGB2BGR)
    ai_image = resize_for_ai(raw_image, config.ai_resolution)

    results_map: dict[str, str] = {}
    geometry_data: dict[str, list[list[float]] | None] = {}
    floor_mask_full: np.ndarray | None = None

    with torch.no_grad():
        for label in ("floor", "wall"):
            inputs = _prepare_model_inputs(ai_image, label, runtime)
            outputs = runtime.model(**inputs)
            result = runtime.processor.post_process_instance_segmentation(
                outputs,
                threshold=config.segmentation_threshold,
                target_sizes=[original_size[::-1]],
            )[0]

            if len(result["masks"]) == 0:
                continue

            mask = torch.sum(result["masks"], dim=0).clamp(0, 1).cpu().numpy()
            geometry_data[f"{label}_points"] = get_perspective_metadata(mask)
            mask_final = cv2.GaussianBlur(
                (mask * 255).astype(np.uint8),
                (config.mask_blur_kernel_size, config.mask_blur_kernel_size),
                0,
            )

            if label == "floor":
                floor_mask_full = mask_final

            filename = f"{job_id}_{label}.png"
            _write_image(config.output_dir / filename, mask_final)
            results_map[label] = _mask_url(filename)

    if floor_mask_full is not None:
        shadow_image = process_shadow_catcher_v2(img_np, floor_mask_full, job_id)
    else:
        shadow_image = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    shadow_filename = f"{job_id}_shadows.png"
    _write_image(config.output_dir / shadow_filename, shadow_image)

    gc.collect()
    return {
        "jobId": job_id,
        "masks": results_map,
        "shadows": _mask_url(shadow_filename),
        "geometry": geometry_data,
        "width": original_size[0],
        "height": original_size[1],
    }
