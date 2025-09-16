# sender_telegram.py (versão Agendador Inteligente com TEXTO SIMPLES)

import time
import pandas as pd
import requests
import os
import random
from dotenv import load_dotenv
from datetime import datetime

# --- ⚙️ CONFIGURAÇÕES ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN_TELEGRAM")
CHANNEL_ID = "@OfertaScanCanal"
ARQUIVO_OFERTAS = "ofertas_ml_hub.xlsx"

# --- Validação inicial do Token ---
if not BOT_TOKEN:
    print("❌ ERRO: Token do Telegram não encontrado.")
    print("   Verifique se:")
    print("   1. O arquivo se chama '.env' (com o ponto).")
    print("   2. O arquivo está na mesma pasta do script.")
    print("   3. A variável dentro dele se chama 'BOT_TOKEN_TELEGRAM'.")
    exit()




# --- FUNÇÃO DE ENVIO ---
def send_telegram_photo(token, channel, photo_url, caption):
    """Envia uma FOTO com LEGENDA para um canal do Telegram como texto simples."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    # IMPORTANTE: O parâmetro 'parse_mode' foi REMOVIDO para evitar erros.
    payload = {'chat_id': channel, 'photo': photo_url, 'caption': caption}
    
    try:
        response = requests.post(url, data=payload, timeout=30)
        response_json = response.json()
        if response_json.get("ok"):
            return True
        else:
            error_desc = response_json.get('description', 'Erro desconhecido')
            print(f"  [!] Erro ao enviar para o Telegram: {error_desc}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [!] Exceção de rede ao chamar a API do Telegram: {e}")
        return False

# --- FUNÇÃO PRINCIPAL (AGORA UM AGENDADOR) ---
def iniciar_agendador():
    """
    Mantém o bot rodando em um ciclo infinito, respeitando horários e pausas.
    """
    while True:
        hora_atual = datetime.now().hour
        
        if 5 <= hora_atual < 22:
            print(f"\n({datetime.now().strftime('%H:%M')}) - 🌞 Modo ativo. Iniciando ciclo de envio.")
            
            try:
                df = pd.read_excel(ARQUIVO_OFERTAS)
                if df.empty:
                    print("  -> Planilha de ofertas vazia. Descansando por 30 minutos.")
                    time.sleep(1800)
                    continue
                ofertas = df.to_dict('records')
            except FileNotFoundError:
                print(f"  -> Arquivo '{ARQUIVO_OFERTAS}' não encontrado. Descansando por 30 minutos.")
                time.sleep(1800)
                continue

            print(f"  -> {len(ofertas)} ofertas carregadas. Iniciando envio em lotes de 5.")
            for i, oferta in enumerate(ofertas):
                if not (5 <= datetime.now().hour < 22):
                    print("  -> Horário de operação encerrado no meio do ciclo. Entrando em modo 'dormindo'.")
                    break

                print(f"    -> Enviando oferta {i+1}/{len(ofertas)}: {oferta.get('Produto', 'N/A')[:40]}...")
                
                try:
                    highlight = oferta['Categoria']
                    titulo = oferta['Produto']
                    preco = oferta['Preço']
                    link = oferta['Link Afiliado']
                    imagem_url = oferta['URL da Imagem']

                    # --- MENSAGEM MONTADA COMO TEXTO SIMPLES ---
                    legenda_final = f"""🔥 {highlight} NO MERCADO LIVRE 🔥

{titulo}
💰 Por apenas: {preco}

🛒 Compre aqui:
{link}"""
                    
                    if len(legenda_final) > 1024:
                        legenda_final = legenda_final[:1020] + "..."

                    if send_telegram_photo(BOT_TOKEN, CHANNEL_ID, imagem_url, legenda_final):
                        intervalo_curto = random.randint(15, 30)
                        print(f"      ✅ Enviada. Pausa curta de {intervalo_curto}s.")
                        time.sleep(intervalo_curto)
                    else:
                        print(f"      ❌ Falha. Pulando para próxima oferta.")

                    if (i + 1) % 5 == 0 and (i + 1) < len(ofertas):
                        print(f"  -> Fim do lote de 5. Descansando por 10 minutos...")
                        time.sleep(600)
                        print("  -> Retomando o envio...")

                except KeyError as e:
                    print(f"  [!] Erro de dado ausente na planilha (Coluna {e}). Pulando oferta.")
                    continue
            
            print("\n  -> Fim do ciclo de envios. Descansando por 1 hora antes de recomeçar.")
            time.sleep(3600)

        else:
            print(f"({datetime.now().strftime('%H:%M')}) - 😴 Fora do horário de operação. Bot dormindo por 30 minutos.")
            time.sleep(1800)

# --- EXECUÇÃO DO SCRIPT ---
if __name__ == "__main__":
    iniciar_agendador()