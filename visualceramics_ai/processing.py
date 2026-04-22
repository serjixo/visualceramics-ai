import time

import cv2
import numpy as np
from PIL import Image


def resize_for_ai(raw_image: Image.Image, ai_resolution: int) -> Image.Image:
    ratio = ai_resolution / max(raw_image.size)
    ai_size = (int(raw_image.size[0] * ratio), int(raw_image.size[1] * ratio))
    return raw_image.resize(ai_size, Image.LANCZOS)


def process_shadow_catcher_v2(img_bgr: np.ndarray, floor_mask: np.ndarray, job_id: str) -> np.ndarray:
    t_start = time.time()

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    _, _, value_channel = cv2.split(hsv)

    floor_value_channel = cv2.bitwise_and(value_channel, value_channel, mask=floor_mask)
    grout_mask = cv2.adaptiveThreshold(
        floor_value_channel,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2,
    )
    grout_mask = cv2.bitwise_and(grout_mask, floor_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    grout_mask = cv2.dilate(grout_mask, kernel, iterations=1)

    value_channel_inpainted = cv2.inpaint(value_channel, grout_mask, 3, cv2.INPAINT_TELEA)
    value_channel_smooth = cv2.medianBlur(value_channel_inpainted, 21)
    value_channel_refined = cv2.bilateralFilter(value_channel_smooth, 9, 75, 75)

    value_channel_ambient = cv2.GaussianBlur(value_channel_refined, (121, 121), 0)
    shadow_map = cv2.divide(value_channel_refined, value_channel_ambient, scale=255)
    final_value_channel = np.where(floor_mask > 0, shadow_map, value_channel)

    print(f"[JOB {job_id}] shadow catcher ready in {time.time() - t_start:.2f}s")
    return final_value_channel


def get_perspective_metadata(mask_np: np.ndarray) -> list[list[float]] | None:
    mask_uint8 = (mask_np * 255).astype(np.uint8)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    epsilon = 0.015 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    height, width = mask_np.shape
    return [[float(point[0][0] / width), float(point[0][1] / height)] for point in approx]
