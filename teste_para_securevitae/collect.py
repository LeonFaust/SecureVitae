import mysql.connector
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox, Toplevel

# Configurações da base de dados
host = "localhost"
user = "root"
password = ""
database = "teste2"
output_file = "mysql_database_dump.txt"


# Função para exportar e analisar os dados
def exportar_e_analisar():
    try:
        texto_saida.delete(1.0, tk.END)
        texto_saida.insert(tk.END, "Thinking...\n")
        texto_saida.update_idletasks()

        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        # Verificar se há dados na base
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]

        total_linhas = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
            count = cursor.fetchone()[0]
            total_linhas += count

        if total_linhas == 0:
            messagebox.showinfo("Aviso", "A base de dados está vazia. Não há dados para analisar.")
            texto_saida.delete(1.0, tk.END)
            texto_saida.insert(tk.END, "Base de dados vazia.\n")
            cursor.close()
            conn.close()
            return

        dados_texto = ""

        with open(output_file, 'w', encoding='utf-8') as f:
            for table in tables:
                cursor.execute(f"DESCRIBE `{table}`;")
                schema = cursor.fetchall()

                filtered_columns = [col[0] for col in schema if col[0].lower() != 'id']
                column_list = ", ".join(f"`{col}`" for col in filtered_columns)

                cursor.execute(f"SELECT {column_list} FROM `{table}`;")
                rows = cursor.fetchall()

                for row in rows:
                    linha = " | ".join(str(cell) for cell in row) + "\n"
                    f.write(linha)
                    dados_texto += linha

                f.write("\n\n")
                dados_texto += "\n\n"

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Erro de Base de Dados", str(err))
        return

    # Enviar diretamente os dados para a API do Ollama
    try:
        payload = {
            "model": "qwen2.5vl:3b",
            "messages": [
                {
                    "role": "user",
                    "content": f"{dados_texto}\n\nFaz uma análise geral dos dados e matem a tua analise com um maximo de 60 palavras."
                }
            ],
            "stream": False
        }

        response = requests.post("http://localhost:11434/api/chat", json=payload)

        if response.status_code == 200:
            result = response.json()
            texto_saida.delete(1.0, tk.END)
            texto_saida.insert(tk.END, result["message"]["content"])
        else:
            messagebox.showerror("Erro na API", f"Erro {response.status_code}:\n{response.text}")

    except Exception as e:
        messagebox.showerror("Erro", str(e))


# Função para eliminar todos os dados da base
def eliminar_dados():
    resposta = messagebox.askyesno("Confirmar", "Tem a certeza que deseja eliminar TODOS os dados da base de dados?")
    if not resposta:
        return

    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"DELETE FROM `{table}`;")
        conn.commit()

        cursor.close()
        conn.close()

        messagebox.showinfo("Sucesso", "Todos os dados foram eliminados com sucesso.")
        texto_saida.delete(1.0, tk.END)
        texto_saida.insert(tk.END, "Dados eliminados.\n")

    except mysql.connector.Error as err:
        messagebox.showerror("Erro de Base de Dados", str(err))


# Nova função para mostrar as últimas 10 linhas das tabelas
def abrir_live_feed():
    def atualizar_dados():
        text_live.delete(1.0, tk.END)
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = conn.cursor()

            cursor.execute("SHOW TABLES;")
            tables = [table[0] for table in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"DESCRIBE `{table}`;")
                schema = cursor.fetchall()
                filtered_columns = [col[0] for col in schema if col[0].lower() != 'id']
                column_list = ", ".join(f"`{col}`" for col in filtered_columns)

                cursor.execute(f"SELECT {column_list} FROM `{table}` ORDER BY id DESC LIMIT 10;")
                rows = cursor.fetchall()

                text_live.insert(tk.END, f"--- Últimas 10 linhas da tabela: {table} ---\n")
                for row in rows:
                    linha = " | ".join(str(cell) for cell in row) + "\n"
                    text_live.insert(tk.END, linha)
                text_live.insert(tk.END, "\n")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            text_live.insert(tk.END, f"Erro ao carregar dados: {err}\n")

    # Criar nova janela
    live_window = Toplevel(janela)
    live_window.title("Live Feed - Últimas 10 Linhas")
    live_window.geometry("800x600")

    frame_botoes = tk.Frame(live_window)
    frame_botoes.pack(pady=10)

    btn_atualizar = tk.Button(frame_botoes, text="Atualizar", command=atualizar_dados, font=("Arial", 12))
    btn_atualizar.pack(side=tk.LEFT, padx=5)

    global text_live
    text_live = scrolledtext.ScrolledText(live_window, wrap=tk.WORD, font=("Courier", 10), width=100, height=30)
    text_live.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Carregar os dados iniciais
    atualizar_dados()


# Interface gráfica com Tkinter
janela = tk.Tk()
janela.title("Análise de Base de Dados com Ollama")
janela.geometry("800x600")

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=10)

botao_exportar = tk.Button(frame_botoes, text="Exportar e Analisar", command=exportar_e_analisar, font=("Arial", 12))
botao_exportar.pack(side=tk.LEFT, padx=5)

botao_eliminar = tk.Button(frame_botoes, text="Eliminar Dados", command=eliminar_dados, font=("Arial", 12), fg="red")
botao_eliminar.pack(side=tk.LEFT, padx=5)

botao_live_feed = tk.Button(frame_botoes, text="Live Feed", command=abrir_live_feed, font=("Arial", 12), fg="blue")
botao_live_feed.pack(side=tk.LEFT, padx=5)

texto_saida = scrolledtext.ScrolledText(janela, wrap=tk.WORD, font=("Courier", 10), width=100, height=30)
texto_saida.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

janela.mainloop()