# sender_telegram.py (versão final com alternância de plataforma)

import time
import requests
import os
import random
from dotenv import load_dotenv
from datetime import datetime
from database import supabase_client

# --- ⚙️ CONFIGURAÇÕES ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN_TELEGRAM")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TABLE_NAME = "ofertas"

# --- Validações (mesmo código de antes) ---
if not BOT_TOKEN or not CHANNEL_ID or not supabase_client:
    print("❌ ERRO: Verifique as variáveis de ambiente e a conexão com o Supabase.")
    exit()

# --- Modelos de Mensagem (mesmo código de antes) ---
MESSAGE_TEMPLATES = [
    "🔥 OFERTA IMPERDÍVEL NA {plataforma} 🔥\n\n{produto}\n💰 Por apenas: {preco}\n\n🛒 Compre aqui:\n{link}",
    "Oferta encontrada: 👀\n\n📦 {produto}\n👉 Por: {preco}\n\nConfira aqui:\n{link}",
    "Pesquisando preços... Achei! 👇\n\n✅ {produto} em promoção:\n💰 Agora: {preco}\n\n➡️ {link}",
    "Boa oportunidade pra quem estava procurando:\n\n✅ {produto}\n💰 Preço com desconto: {preco}\n\nConfira aqui 👉 {link}"
]

# --- FUNÇÕES DE BANCO DE DADOS ---

# MODIFICADO: A função agora aceita o nome da plataforma como argumento
def get_unsent_offer(plataforma: str):
    """Busca UMA oferta não enviada de uma plataforma específica."""
    try:
        response = supabase_client.table(TABLE_NAME)\
            .select("*")\
            .eq("enviado_telegram", False)\
            .eq("plataforma", plataforma)\
            .limit(1)\
            .execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"  [!] Erro ao buscar oferta de '{plataforma}' no Supabase: {e}")
        return None

# Função de marcar como enviado (continua a mesma)
def mark_offer_as_sent(offer_id):
    try:
        supabase_client.table(TABLE_NAME).update({"enviado_telegram": True}).eq("id", offer_id).execute()
        return True
    except Exception as e:
        print(f"  [!] Erro ao atualizar oferta {offer_id} no Supabase: {e}")
        return False

# Função de envio para o Telegram (continua a mesma)
def send_telegram_photo(token, channel, photo_url, caption):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {'chat_id': channel, 'photo': photo_url, 'caption': caption}
    try:
        response = requests.post(url, data=payload, timeout=30)
        response_json = response.json()
        if response_json.get("ok"):
            return True
        else:
            print(f"  [!] Erro do Telegram: {response_json.get('description', 'Erro desconhecido')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [!] Exceção de rede ao chamar a API do Telegram: {e}")
        return False

# --- LÓGICA PRINCIPAL DO BOT ---
def start_telegram_sender():
    print("🚀 Bot de envio do Telegram iniciado com lógica de alternância...")
    
    # NOVO: Variável para controlar qual plataforma buscar
    proxima_plataforma = "Shopee"

    while True:
        hora_atual = datetime.now().hour
        
        if 5 <= hora_atual < 23:
            # MODIFICADO: Busca a oferta da plataforma da vez
            print(f"({datetime.now().strftime('%H:%M')}) - 🔎 Buscando oferta da plataforma: {proxima_plataforma}...")
            oferta = get_unsent_offer(proxima_plataforma)

            # Se não encontrar oferta da plataforma atual, tenta a outra
            if not oferta:
                plataforma_alternativa = "Mercado Livre" if proxima_plataforma == "Shopee" else "Shopee"
                print(f"  -> Nenhuma oferta encontrada para '{proxima_plataforma}'. Tentando '{plataforma_alternativa}'...")
                oferta = get_unsent_offer(plataforma_alternativa)

            if oferta:
                print(f"  -> ✅ Oferta encontrada: {oferta.get('produto', 'N/A')[:40]}...")
                
                # Montagem da legenda (lógica continua a mesma)
                template_escolhido = random.choice(MESSAGE_TEMPLATES)
                legenda_final = template_escolhido.format(
                    plataforma=oferta['plataforma'].upper(),
                    produto=oferta['produto'],
                    preco=oferta['preco'],
                    link=oferta['link_afiliado']
                )
                
                if send_telegram_photo(BOT_TOKEN, CHANNEL_ID, oferta['url_imagem'], legenda_final):
                    if mark_offer_as_sent(oferta['id']):
                        print(f"    -> ✅ Enviada e marcada no DB.")
                else:
                    print(f"    -> ❌ Falha no envio para o Telegram.")
                
                # Pausa entre envios (seu intervalo de 60 a 90 segundos)
                intervalo = random.randint(60, 90)
                print(f"    -> Pausando por {intervalo} segundos...")
                time.sleep(intervalo)
            
            else:
                # Nenhuma oferta nova encontrada em NENHUMA plataforma
                print(f"({datetime.now().strftime('%H:%M')}) - 🤷 Nenhuma oferta nova no banco. Verificando novamente em 10 minutos.")
                time.sleep(600) # Dorme por 10 minutos
            
            # NOVO: Inverte a plataforma para a próxima busca
            proxima_plataforma = "Mercado Livre" if proxima_plataforma == "Shopee" else "Shopee"

        else:
            # Fora do horário de funcionamento
            print(f"({datetime.now().strftime('%H:%M')}) - 😴 Fora do horário. Bot dormindo por 30 minutos.")
            time.sleep(1800)

if __name__ == "__main__":
    start_telegram_sender()