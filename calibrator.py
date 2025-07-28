# O oráculo manual, calibrator.py. Ajusta limites HSV pra verde usando um vídeo fixo. Imprime valores no terminal. Rode com python3 calibrator.py.

# #1. Invocações: cv2, numpy.

# #2. Função Vazia: Pra trackbar.

# #3. Círculo Principal: Abre vídeo fixo, cria trackbars, loop: aplica máscara, exibe. 'q' pra sair e imprimir valores.


import cv2
import numpy as np

#2
def nada(x):
    pass

#3
NOME_VIDEO = 'Luna_triste.mp4'  
caminho_video = '/videos_entrada'

caminho_video = f'videos_entrada/{NOME_VIDEO}'
cap = cv2.VideoCapture(caminho_video)

if not cap.isOpened():
    print(f"Erro: Não foi possível abrir o vídeo '{caminho_video}'")
    exit()

cv2.namedWindow('Controles')
cv2.createTrackbar('H Min', 'Controles', 35, 179, nada)
cv2.createTrackbar('S Min', 'Controles', 40, 255, nada)
cv2.createTrackbar('V Min', 'Controles', 40, 255, nada)
cv2.createTrackbar('H Max', 'Controles', 85, 179, nada)
cv2.createTrackbar('S Max', 'Controles', 255, 255, nada)
cv2.createTrackbar('V Max', 'Controles', 255, 255, nada)

print("Ajuste os controles até a máscara ficar perfeita. Pressione 'q' para sair.")

while True:
    sucesso, frame = cap.read()
    if not sucesso:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos('H Min', 'Controles')
    s_min = cv2.getTrackbarPos('S Min', 'Controles')
    v_min = cv2.getTrackbarPos('V Min', 'Controles')
    h_max = cv2.getTrackbarPos('H Max', 'Controles')
    s_max = cv2.getTrackbarPos('S Max', 'Controles')
    v_max = cv2.getTrackbarPos('V Max', 'Controles')

    lower_bound = np.array([h_min, s_min, v_min])
    upper_bound = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    
    cv2.imshow('Original', frame)
    cv2.imshow('Mascara', mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n--- Valores de Chroma Key Calibrados ---")
        print(f"LOWER_BOUND = np.array([{h_min}, {s_min}, {v_min}])")
        print(f"UPPER_BOUND = np.array([{h_max}, {s_max}, {v_max}])")
        print("-----------------------------------------")
        break

cap.release()
cv2.destroyAllWindows()

# "O conhecimento é o fogo que ilumina a escuridão." - Marco Aurélio, imperador estoico, guiando nossa calibração sutil.