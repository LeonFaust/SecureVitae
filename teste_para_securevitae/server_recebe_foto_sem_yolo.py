#!/usr/bin/python3
import socket
import base64
import os
import requests
import mysql.connector
from datetime import datetime
from unidecode import unidecode

# Configurações
HOST = '0.0.0.0'
PORT = 12346
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5vl:3b"

# Conexão com a base de dados
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Altere se necessário
        password="",  # Adicione senha se definida
        database="teste2",
        port=3306
    )

# Função para salvar imagem e retornar o caminho
def salvar_imagem_base64(base64_str):
    try:
        image_data = base64.b64decode(base64_str)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"imagem_{timestamp}.png"
        caminho = os.path.join(os.getcwd(), filename)
        with open(caminho, 'wb') as f:
            f.write(image_data)
        print(f"[✔] Imagem salva como: {filename}")
        return caminho
    except Exception as e:
        print(f"[✖] Erro ao salvar imagem: {e}")
        return None

# Função para descrever imagem com Ollama
def descrever_imagem(path_imagem):
    try:
        with open(path_imagem, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        payload = {
            "model": MODEL,
            "prompt": "Describe the image in 30 words or less.",
            "stream": False,
            "images": [img_base64]
        }

        print("[📤] Enviando imagem ao Ollama...")
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()

        descricao = response.json()['response']
        descricao_sem_acentos = unidecode(descricao.strip())
        print("[🧠] Descrição gerada pelo modelo:")
        print(descricao_sem_acentos)
        return descricao_sem_acentos
    except Exception as e:
        print(f"[✖] Erro ao descrever imagem: {e}")
        return None

# Função para inserir no banco de dados
def inserir_na_bd(descricao):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Use a tua senha do MySQL aqui se houver
            database="teste2",
            port=3306
        )
        cursor = conn.cursor()

        datahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO teste2 (Texto, data) VALUES (%s, %s)", (descricao, datahora))
        conn.commit()
        print("[💾] Descrição inserida na base de dados com sucesso.")

    except mysql.connector.Error as err:
        print(f"[✖] Erro ao inserir na base de dados: {err}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Inicia o servidor
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[🔌] Servidor a escuta no {HOST}:{PORT}...")

    while True:
        conn, addr = server.accept()
        print(f"[→] Conexão de: {addr}")
        with conn:
            data = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk

            try:
                base64_str = data.decode()
                caminho_imagem = salvar_imagem_base64(base64_str)
                if caminho_imagem:
                    descricao = descrever_imagem(caminho_imagem)
                    if descricao:
                        inserir_na_bd(descricao)
            except Exception as e:
                print(f"[✖] Erro ao processar dados: {e}")
