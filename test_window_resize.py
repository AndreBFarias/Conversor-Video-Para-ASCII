#!/usr/bin/env python3
# Test script to debug window resizing
import cv2
import numpy as np

# Create a simple test image with text
img = np.zeros((100, 200, 3), dtype=np.uint8)
cv2.putText(img, "TEST IMAGE", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

# Test different window modes
print("Testing WINDOW_NORMAL...")
cv2.namedWindow("TEST", cv2.WINDOW_NORMAL)
cv2.imshow("TEST", img)

print("Window criada. Tente redimensionar a janela.")
print("Pressione 'q' para sair")

while True:
    key = cv2.waitKey(100) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()
print("Teste finalizado")
