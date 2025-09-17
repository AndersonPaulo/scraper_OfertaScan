# sender_telegram.py (VERSÃO FINAL COM AJUSTE DE FUSO HORÁRIO)
import time
import requests
import os
import random
from dotenv import load_dotenv
from datetime import datetime, timezone # timezone é necessário
import pytz # NOVO: Biblioteca para fusos horários

# --- CONFIGURAÇÕES E VALIDAÇÕES (sem mudanças) ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN_TELEGRAM")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TABLE_NAME = "ofertas"
if not BOT_TOKEN or not CHANNEL_ID or not supabase_client:
    print("❌ ERRO: Verifique as variáveis de ambiente e a conexão com o Supabase.")
    exit()
MESSAGE_TEMPLATES = [
    "🔥 OFERTA IMPERDÍVEL NA {plataforma} 🔥\n\n{produto}\n💰 Por apenas: {preco}\n\n🛒 Compre aqui:\n{link}",
    "Oferta encontrada: 👀\n\n📦 {produto}\n👉 Por: {preco}\n\nConfira aqui:\n{link}",
    "Pesquisando preços... Achei! 👇\n\n✅ {produto} em promoção:\n💰 Agora: {preco}\n\n➡️ {link}",
    "Boa oportunidade pra quem estava procurando:\n\n✅ {produto}\n💰 Preço com desconto: {preco}\n\nConfira aqui 👉 {link}"
]

# --- FUNÇÕES DE BANCO DE DADOS E ENVIO (sem mudanças) ---
def get_unsent_offer(plataforma: str):
    try:
        response = supabase_client.table(TABLE_NAME).select("*").eq("enviado_telegram", False).eq("plataforma", plataforma).limit(1).execute()
        if response.data: return response.data[0]
        return None
    except Exception as e: return None
def mark_offer_as_sent(offer_id):
    try:
        supabase_client.table(TABLE_NAME).update({"enviado_telegram": True}).eq("id", offer_id).execute()
        return True
    except Exception as e: return False
def send_telegram_photo(token, channel, photo_url, caption):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"; payload = {'chat_id': channel, 'photo': photo_url, 'caption': caption}
    try:
        response = requests.post(url, data=payload, timeout=30); response_json = response.json()
        if response_json.get("ok"): return True
        else: return False
    except requests.exceptions.RequestException as e: return False


# --- LÓGICA PRINCIPAL DO BOT ---
def start_telegram_sender():
    print("🚀 Bot de envio do Telegram iniciado com lógica de alternância...")
    proxima_plataforma = "Shopee"
    
    # NOVO: Define o fuso horário do Brasil
    fuso_horario_local = pytz.timezone("America/Sao_Paulo")

    while True:
        # MODIFICADO: Converte a hora para o fuso horário local antes de verificar
        utc_now = datetime.now(timezone.utc)
        hora_local_obj = utc_now.astimezone(fuso_horario_local)
        hora_atual = hora_local_obj.hour
        
        print(f"({hora_local_obj.strftime('%H:%M:%S')}) - ❤️  Iniciando novo ciclo de busca (Horário Local)...")

        if 5 <= hora_atual < 23:
            # (O restante da lógica de envio permanece o mesmo)
            print(f"({hora_local_obj.strftime('%H:%M')}) - 🔎 Buscando oferta da plataforma: {proxima_plataforma}...")
            oferta = get_unsent_offer(proxima_plataforma)
            if not oferta:
                plataforma_alternativa = "Mercado Livre" if proxima_plataforma == "Shopee" else "Shopee"
                print(f"  -> Nenhuma oferta encontrada para '{proxima_plataforma}'. Tentando '{plataforma_alternativa}'...")
                oferta = get_unsent_offer(plataforma_alternativa)
            if oferta:
                print(f"  -> ✅ Oferta encontrada: {oferta.get('produto', 'N/A')[:40]}...")
                template_escolhido = random.choice(MESSAGE_TEMPLATES)
                legenda_final = template_escolhido.format(
                    plataforma=oferta['plataforma'].upper(), produto=oferta['produto'],
                    preco=oferta['preco'], link=oferta['link_afiliado']
                )
                if send_telegram_photo(BOT_TOKEN, CHANNEL_ID, oferta['url_imagem'], legenda_final):
                    if mark_offer_as_sent(oferta['id']):
                        print(f"    -> ✅ Enviada e marcada no DB.")
                else: print(f"    -> ❌ Falha no envio para o Telegram.")
                intervalo = random.randint(60, 90)
                print(f"    -> Pausando por {intervalo} segundos...")
                time.sleep(intervalo)
            else:
                print(f"({hora_local_obj.strftime('%H:%M')}) - 🤷 Nenhuma oferta nova no banco. Verificando novamente em 10 minutos.")
                time.sleep(600)
            proxima_plataforma = "Mercado Livre" if proxima_plataforma == "Shopee" else "Shopee"
        else:
            print(f"({hora_local_obj.strftime('%H:%M')}) - 😴 Fora do horário. Bot dormindo por 30 minutos.")
            time.sleep(1800)

if __name__ == "__main__":
    start_telegram_sender()