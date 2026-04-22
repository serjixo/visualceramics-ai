from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    static_dir: Path
    output_dir: Path
    ai_resolution: int = 1024
    segmentation_threshold: float = 0.4
    mask_blur_kernel_size: int = 21


def load_config(base_dir: Path | None = None) -> AppConfig:
    resolved_base_dir = base_dir or Path(__file__).resolve().parent.parent
    static_dir = resolved_base_dir / "static"
    output_dir = static_dir / "masks"
    output_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        base_dir=resolved_base_dir,
        static_dir=static_dir,
        output_dir=output_dir,
    )
