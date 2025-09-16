# sender_whatsapp.py

import time
import pandas as pd
from playwright.sync_api import sync_playwright
import os
import random

# --- ⚙️ CONFIGURAÇÕES (ATUALIZADAS COM SEUS DADOS) ---
# Caminho do perfil do Chrome dedicado ao WhatsApp.
WHATSAPP_USER_DATA_DIR = "/home/anderson/.config/google-chrome/Profile 2" # ATUALIZADO

# Caminho do executável do Chrome (o mesmo de antes)
EXECUTABLE_PATH = "/opt/google/chrome/google-chrome"

# Nome EXATO do seu grupo no WhatsApp
NOME_DO_GRUPO = "Oferta Scan # 1" # ATUALIZADO

# Nome do arquivo de onde vamos ler as ofertas
ARQUIVO_OFERTAS = "ofertas_ml_hub.xlsx"

# --- 🤖 INÍCIO DO SCRIPT ---

def enviar_ofertas_whatsapp():
    """
    Lê as ofertas de uma planilha Excel e as envia para um grupo específico do WhatsApp.
    """
    
    print(f"📄 Carregando ofertas do arquivo: {ARQUIVO_OFERTAS}")
    try:
        df = pd.read_excel(ARQUIVO_OFERTAS)
        if df.empty:
            print("🤷 Planilha de ofertas está vazia. Nada a enviar.")
            return
    except FileNotFoundError:
        print(f"❌ ERRO: Arquivo '{ARQUIVO_OFERTAS}' não encontrado. Execute o scraper primeiro.")
        return

    ofertas = df.to_dict('records')
    
    with sync_playwright() as p:
        print("🚀 Iniciando o navegador com perfil do WhatsApp...")
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=WHATSAPP_USER_DATA_DIR,
            executable_path=EXECUTABLE_PATH,
            headless=False,
            args=['--start-maximized'],
            no_viewport=True,
        )
        
        pagina = contexto.new_page()

        try:
            print("🌍 Navegando para o WhatsApp Web...")
            pagina.goto("https://web.whatsapp.com/", timeout=120000)

            # --- LÓGICA DE LOGIN (LEITURA DE QR CODE) ---
            print("\n" + "="*50)
            print("🚨 AÇÃO MANUAL NECESSÁRIA (APENAS NA PRIMEIRA VEZ) 🚨")
            print("Se o QR Code aparecer, escaneie com seu celular para logar no WhatsApp Web.")
            print("O script vai esperar até que o login seja completado...")
            print("="*50 + "\n")

            # Espera por um elemento que só aparece DEPOIS do login
            seletor_login_completo = 'div[data-testid="chat-list-search-container"]'
            pagina.wait_for_selector(seletor_login_completo, timeout=120000) # 2 minutos para escanear
            
            print("✅ Login no WhatsApp Web bem-sucedido!")
            time.sleep(5)

            # --- ENCONTRANDO E ABRINDO O GRUPO ---
            print(f"🔍 Procurando pelo grupo: '{NOME_DO_GRUPO}'")
            # Clica na barra de busca de conversas
            pagina.locator('div[data-testid="chat-list-search"]').click()
            # Digita o nome do grupo para encontrá-lo
            pagina.keyboard.type(NOME_DO_GRUPO, delay=100)
            time.sleep(2)
            # Clica no resultado da busca para abrir a conversa
            pagina.locator(f'span[title="{NOME_DO_GRUPO}"]').click()
            print(f"💬 Grupo '{NOME_DO_GRUPO}' aberto.")
            time.sleep(3)

            # --- ENVIANDO AS MENSAGENS ---
            print("\n🚀 Iniciando o envio das ofertas...")
            for i, oferta in enumerate(ofertas):
                mensagem = oferta["Mensagem Pronta"].strip()
                print(f"  -> Enviando oferta {i+1}/{len(ofertas)}: {oferta['Produto'][:40]}...")

                # Localiza a caixa de texto do chat
                caixa_de_texto = pagina.locator('div[contenteditable="true"][data-tab="10"]')
                caixa_de_texto.click()

                # Divide a mensagem em linhas e envia uma por uma, simulando "Shift+Enter"
                linhas = mensagem.split('\n')
                for linha in linhas:
                    if linha.strip(): # Ignora linhas vazias
                        caixa_de_texto.type(linha.strip())
                        pagina.keyboard.press("Shift+Enter") # Cria uma nova linha
                        time.sleep(0.5)
                
                pagina.keyboard.press("Enter") # Envia a mensagem completa

                # Pausa longa e aleatória entre os envios para simular humano
                intervalo = random.randint(25, 50)
                print(f"  ✅ Mensagem enviada. Próximo envio em {intervalo} segundos...")
                time.sleep(intervalo)
            
            print("\n🎉 Todas as ofertas foram enviadas com sucesso!")

        except Exception as e:
            print(f"❌ Erro crítico durante a execução do envio: {e}")
        finally:
            print("🚪 Fechando o navegador.")
            contexto.close()

# --- EXECUÇÃO DO SCRIPT ---
if __name__ == "__main__":
    enviar_ofertas_whatsapp()