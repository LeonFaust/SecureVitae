#!/usr/bin/python3
import cv2
import base64
import os
import socket
import time

# Configurações do servidor
server_ip = '127.0.0.1'  # Altere conforme necessário
server_port = 12346

# Intervalo entre capturas (em segundos)
CAPTURE_INTERVAL = 10

# Função para obter nome único de imagem
def get_next_image_filename(prefix='foto', extension='.png'):
    num = 0
    while True:
        filename = f'{prefix}{num}{extension}'
        if not os.path.exists(filename):
            return filename
        num += 1

# Inicia a webcam
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Erro ao abrir a câmara.")
    exit()

print(f"Vai tirar uma foto a cada {CAPTURE_INTERVAL} segundos. Pressione 'q' para sair.")

# Tempo da última captura
last_capture_time = time.time()

while True:
    ret, frame = cam.read()
    if not ret:
        print("Erro ao capturar frame da câmara.")
        break

    # Mostra a imagem em tempo real
    cv2.imshow('Camera (automaticamente tira fotos)', frame)
    key = cv2.waitKey(1)

    current_time = time.time()

    # Verifica se já passou o intervalo desde a última captura
    if current_time - last_capture_time >= CAPTURE_INTERVAL:
        # Guarda imagem com nome único
        image_filename = get_next_image_filename()
        cv2.imwrite(image_filename, frame)
        print(f"Imagem capturada e guardada como {image_filename}")

        # Codifica imagem em base64
        with open(image_filename, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        # Envia via socket
        try:
            s = socket.socket()
            s.connect((server_ip, server_port))
            s.sendall(img_base64.encode())
            s.close()
            print("Imagem enviada com sucesso ao servidor.")
        except Exception as e:
            print("Erro ao enviar imagem:", e)

        # Atualiza o tempo da última captura
        last_capture_time = current_time

    # Sai do loop se pressionar 'q'
    if key == ord('q'):
        break

# Libera recursos
cam.release()
cv2.destroyAllWindows()