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

model = "gemma3:4b"
modeltradutor = "gemma3:4b"
respostamoondream = ""
nomeimagem = ""
descricao_actual = ""
url = "http://localhost:11434/api/generate"

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

# Função para adicionar a zona de texto abaixo da imagem (altura dinâmica)
def adicionar_texto_abaixo(frame, texto, altura_linha=25, margem=10):
    largura = frame.shape[1]

    # Divide o texto longo em várias linhas
    linhas = []
    max_chars = 60
    while len(texto) > max_chars:
        corte = texto[:max_chars].rfind(' ')
        if corte == -1:
            corte = max_chars
        linhas.append(texto[:corte])
        texto = texto[corte:].lstrip()
    linhas.append(texto)

    n_linhas = min(len(linhas), 5)

    altura_total = n_linhas * altura_linha + 2 * margem

    # Cria uma área preta
    barra = np.zeros((altura_total, largura, 3), dtype=np.uint8)

    font = cv2.FONT_HERSHEY_SIMPLEX
    escala = 0.6
    cor = (255, 255, 255)
    espessura = 1

    # Desenha as linhas na barra
    y = margem + altura_linha - 5
    for linha in linhas[:5]:
        cv2.putText(barra, linha, (10, y), font, escala, cor, espessura, cv2.LINE_AA)
        y += altura_linha

    # Junta a imagem e a barra
    frame_com_barra = np.vstack((frame, barra))
    return frame_com_barra

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

    # MOSTRAR A IMAGEM COM A DESCRIÇÃO IMEDIATAMENTE
    frame_descricao = adicionar_texto_abaixo(frame, descricao_actual)
    cv2.imshow('Camera', frame_descricao)
    cv2.waitKey(5000)  # Mostra durante 1 segundo antes de avançar (podes mudar o tempo)

def audio():
    global respostamoondream, nomeimagem
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

    with open(output_file_path, "a") as output_file:
        print("Listening for speech. Press b to stop.")

        while True:
            data = stream.read(4096)

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                recognized_text = result['text']
                output_file.write(recognized_text + "\n")

                print(recognized_text)
                textocompleto += " " + recognized_text + " "

                if cv2.waitKey(1) == ord('b'):
                    print("Stopping...")
                    break

    stream.stop_stream()
    stream.close()
    p.terminate()
    print(textocompleto)

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


''' with open("resultados.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- NOVA ANÁLISE ---\n")
        f.write(f"Imagem: {nomeimagem}\n")
        f.write(f"Descrição da imagem: {respostamoondream.strip()}\n\n")
        f.write(f"Texto reconhecido do áudio: {textocompleto.strip()}\n\n")
        f.write(f"Análise final combinada: {resposta_completa.strip()}\n")
        f.write(f"---------------------\n")'''


# Loop principal
while True:
    ret, frame = cam.read()
    if not ret:
        print("Error: Can't receive frame.")
        break

    frame_com_texto = adicionar_texto_abaixo(frame, descricao_actual)
    cv2.imshow('Camera', frame_com_texto)

    if cv2.waitKey(1) == ord('s'):
        screenshot()
        audio()

    if cv2.waitKey(1) == ord('b'):
        break

cam.release()
cv2.destroyAllWindows()
