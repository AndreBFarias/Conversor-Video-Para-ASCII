import cv2
import numpy as np


def sharpen_frame(frame: np.ndarray, sharpen_amount: float = 0.5) -> np.ndarray:
    if sharpen_amount <= 0:
        return frame
    gaussian = cv2.GaussianBlur(frame, (5, 5), 1.0)
    sharpened = cv2.addWeighted(frame, 1.0 + sharpen_amount, gaussian, -sharpen_amount, 0)
    return sharpened


def apply_morphological_refinement(mask: np.ndarray, erode_size: int = 2, dilate_size: int = 2) -> np.ndarray:
    erode_size = int(erode_size)
    dilate_size = int(dilate_size)
    if erode_size > 0:
        kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erode_size*2+1, erode_size*2+1))
        mask = cv2.erode(mask, kernel_erode, iterations=1)
    if dilate_size > 0:
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_size*2+1, dilate_size*2+1))
        mask = cv2.dilate(mask, kernel_dilate, iterations=1)
    return mask
