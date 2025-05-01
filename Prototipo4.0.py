#!/usr/bin/python3
import cv2
import numpy as np
import os
import vosk
from vosk import SetLogLevel
SetLogLevel(-1)
import pyaudio
import json
import requests
import base64
from unidecode import unidecode 
import socket

model = "gemma3:4b"
modeltradutor = "gemma3:4b"
respostamoondream = ""
nomeimagem = ""
descricao_actual = ""
texto_audio_actual = ""
analise_final_actual = ""
url = "http://localhost:11434/api/generate"
server_ip = '192.168.1.79'
port = 12345
s = socket.socket()

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 400)

if not cam.isOpened():
    print("Error: Could not open video.")
    exit()

# Função para obter o próximo nome de ficheiro que não existe (evitar sobrescrever)
def get_next_image_filename(prefix='test', extension='.png'):
    num = 0
    while True:
        filename = f'{prefix}{num}{extension}'
        if not os.path.exists(filename):
            return filename, num
        num += 1

# Função para adicionar múltiplas caixas de texto abaixo da imagem com título
def adicionar_multiplos_textos_abaixo(frame, blocos_texto, altura_linha=25, margem=10):
    largura = frame.shape[1]
    frame_resultado = frame.copy()

    for titulo, texto, cor_fundo in blocos_texto:
        # Junta o título ao texto
        texto_com_titulo = f"{titulo}:\n{texto.strip()}"

        # Divide o texto longo em várias linhas
        linhas = []
        max_chars = 60
        for linha in texto_com_titulo.split('\n'):
            while len(linha) > max_chars:
                corte = linha[:max_chars].rfind(' ')
                if corte == -1:
                    corte = max_chars
                linhas.append(linha[:corte])
                linha = linha[corte:].lstrip()
            linhas.append(linha)

        n_linhas = min(len(linhas), 8)
        altura_total = n_linhas * altura_linha + 2 * margem

        # Cria a área com a cor de fundo especificada
        barra = np.full((altura_total, largura, 3), cor_fundo, dtype=np.uint8)

        font = cv2.FONT_HERSHEY_SIMPLEX
        escala = 0.6
        cor_texto = (255, 255, 255)
        espessura = 1

        # Desenha as linhas na barra
        y = margem + altura_linha - 5
        for linha in linhas[:8]:
            cv2.putText(barra, linha, (10, y), font, escala, cor_texto, espessura, cv2.LINE_AA)
            y += altura_linha

        # Junta a nova barra ao frame actual
        frame_resultado = np.vstack((frame_resultado, barra))

    return frame_resultado

def screenshot():
    global cam, respostamoondream, nomeimagem, descricao_actual

    # Obtem um nome de ficheiro que não existe ainda
    image_filename, _ = get_next_image_filename()
    nomeimagem = image_filename

    # Guarda a imagem capturada pela câmara
    ret, frame = cam.read()
    cv2.imwrite(image_filename, frame)
    print(f"Imagem guardada como {image_filename}")

    # Lê a imagem e converte para base64 para enviar para o Ollama
    with open(image_filename, 'rb') as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    payload = {
        "model": model,
        "prompt": "escreva um breve e curto texto sobre a imagem",
        "max_new_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "repetition_penalty": 1.2,
        "stop_sequence": "###",
        "stream": False,
        "images": [img_base64],
    }

    # Faz o pedido ao Ollama e imprime a resposta
    response = requests.post(url, json=payload)
    respostamoondream = response.json()['response']

    # Remove acentos ao actualizar a descrição visível
    descricao_actual = unidecode(respostamoondream.strip())
    print(respostamoondream)

def audio():
    global respostamoondream, nomeimagem, texto_audio_actual, analise_final_actual
    textocompleto = ""
    model_path = "vosk-model-small-pt-0.3"

    vosk_model = vosk.Model(model_path)
    vosk_model = vosk.Model(lang="pt")

    rec = vosk.KaldiRecognizer(vosk_model, 16000)

    p = pyaudio.PyAudio()
    mic_index = 2
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8192,
                    input_device_index=mic_index)

    output_file_path = "teste.txt"

    print("Listening for speech. Press b to stop.")
    with open(output_file_path, "a") as output_file:
        while True:
            data = stream.read(4096)
            
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                recognized_text = result['text']
                output_file.write(recognized_text + "\n")

                textocompleto += " " + recognized_text + " "
                texto_audio_actual = unidecode(textocompleto.strip())

            else:
                # Obtem resultado parcial (em tempo real)
                partial_result = json.loads(rec.PartialResult())
                recognized_partial = partial_result.get('partial', '')

                # Actualiza o texto visível em tempo real com a frase parcial + o já reconhecido
                texto_audio_actual = unidecode((textocompleto + " " + recognized_partial).strip())
                # Mostrar imagem com as 3 caixas (imagem, texto audio em tempo real, analise final vazia)
                ret, frame = cam.read()
                caixas_texto = [
                ("Descricao da imagem", descricao_actual, (0, 0, 0)),
                ("Texto audio", texto_audio_actual, (50, 50, 50)),
                ("Analise final", analise_final_actual, (80, 80, 80))
            ]
            frame_com_textos = adicionar_multiplos_textos_abaixo(frame, caixas_texto)
            cv2.imshow('Camera', frame_com_textos)

            if cv2.waitKey(1) == ord('b'):
                print("Stopping audio capture...")
                break

    stream.stop_stream()
    stream.close()
    p.terminate()
    print(textocompleto)

    # Enviar para análise e guardar
    response = requests.post(url, json={
        "model": modeltradutor,
        "prompt": "não se esqueça de utilizar portugues de portugal analise o seguinte texto mantenha a analise tente contextualizar breve apenas responda uma frase com a sua conclusão: " + textocompleto,
        "max_new_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "repetition_penalty": 1.2,
        "stop_sequence": "###",
        "stream": False
    })

    resposta_audio = response.json()['response']
    print(resposta_audio)

    responsecompleta = requests.post(url, json={
        "model": modeltradutor,
        "prompt": "não se esqueça de utilizar portugues de portugal analise o seguinte texto mantenha a analise a situação e nao a linguagem breve apenas responda uma frase com a sua conclusão: " + textocompleto + " e o seguinte texto que descreve a imagem a ser vista:" + respostamoondream,
        "max_new_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "repetition_penalty": 1.2,
        "stop_sequence": "###",
        "stream": False
    })
    resposta_completa = responsecompleta.json()['response']
    print("A resposta completa é:")
    print(resposta_completa)

    # Guardar análise final
    analise_final_actual = unidecode(resposta_completa.strip())


    with open("resultados.html", "a", encoding="utf-8") as f:
         f.write(f"""
                 <hr>
                <h2>Nova Análise</h2>
                <p><strong>Imagem:</strong></p>
                <img src="{nomeimagem}" alt="Imagem capturada" width="400"><br><br>

                <p><strong>Descrição da imagem:</strong><br>{respostamoondream.strip()}</p>

                <p><strong>Texto reconhecido do áudio:</strong><br>{textocompleto.strip()}</p>

                <p><strong>Análise final combinada:</strong><br>{resposta_completa.strip()}</p>

                <hr>
                """)
    s.connect((server_ip, port))
    message = (
    f"Analise de imagem: {respostamoondream.strip()}\n"
    f"Texto ouvido: {textocompleto.strip()}\n"
    f"Texto finalizado: {analise_final_actual.strip()}\n"
              )

    s.sendall(message.encode())
    #s.sendall(f"Analise de imagem: {respostamoondream.strip()}\n".encode())
    #s.sendall(f"Texto ouvido: {textocompleto.strip()}\n".encode())
    #s.sendall(f"Texto ouvido: {resposta_completa().strip()}\n".encode())
    data = s.recv(1024)
    if data:
        print("Received from server:", data.decode())

    s.close()
    print("Socket closed")


# Loop principal
while True:
    ret, frame = cam.read()
    if not ret:
        print("Error: Can't receive frame.")
        break

    # Mostrar a imagem + caixas normais
    caixas_texto = [
        ("Descricao da imagem", descricao_actual, (0, 0, 0)),
        ("Texto audio", texto_audio_actual, (50, 50, 50)),
        ("Analise final", analise_final_actual, (80, 80, 80))
    ]

    frame_com_textos = adicionar_multiplos_textos_abaixo(frame, caixas_texto)
    cv2.imshow('Camera', frame_com_textos)

    key = cv2.waitKey(1)
    if key == ord('s'):
        screenshot()
        audio()

    if key == ord('b'):
        break

cam.release()
cv2.destroyAllWindows()
