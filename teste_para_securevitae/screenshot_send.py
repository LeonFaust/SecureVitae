#!/usr/bin/python3
import cv2
import base64
import os
import socket
import time

# Configurações do servidor
server_ip = '127.0.0.1'  # Altere conforme necessário
server_port = 12346
 
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

print("Pressione 's' para tirar uma foto e enviar ao servidor. Pressione 'q' para sair.")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Erro ao capturar frame da câmara.")
        break

    # Mostra a imagem em tempo real
    cv2.imshow('Camera (pressione "s" para capturar)', frame)
    key = cv2.waitKey(1)

    if key == ord('s'):
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
            print("Imagem enviada com sucesso ao servidor.")


        except Exception as e:
            print("Erro ao enviar imagem:", e)

    elif key == ord('q'):
        break

# Libera recursos
cam.release()
cv2.destroyAllWindows()
