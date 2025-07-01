import ollama
import os.path as path

# Modelo a usar
model = "qwen2.5vl:3b"

# Caminho da imagem
imagem_path = "imagemteste.jpg"

if not path.exists(imagem_path):
    print("Erro: Imagem não encontrada.")
    exit()

# Criar cliente
client = ollama.Client("http://localhost:11434")

# Enviar pedido ao modelo
response = client.generate(
    model=model,
    images=[imagem_path],
    ##prompt="Analise a imagem em dez palavras ou menos."
    prompt="Analise descreva a imagem em dez palavras ou menos"
)

# Preparar texto para salvar
texto = f"Modelo usado: {model}\nResposta: {response.response}\n\n"

# Texto explicativo sobre o Ollama a adicionar

# Gravar no ficheiro, acrescentando ao conteúdo existente
with open("resultado.txt", "a", encoding="utf-8") as f:
    f.write(texto)

print("Resultado e explicação sobre Ollama guardados em 'resultado.txt'.")
