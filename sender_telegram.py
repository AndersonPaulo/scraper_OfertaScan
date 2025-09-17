# sender_telegram.py (VERSÃO CORRIGIDA PARA ENVIO DE IMAGEM)
import time
import requests
import os
import random
from dotenv import load_dotenv
from datetime import datetime, timezone
import pytz
from database import supabase_client

# --- CONFIGURAÇÕES E VALIDAÇÕES ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN_TELEGRAM")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TABLE_NAME = "ofertas"
if not BOT_TOKEN or not CHANNEL_ID or not supabase_client:
    print("❌ ERRO: Verifique as variáveis de ambiente e a conexão com o Supabase.")
    exit()

# --- FUNÇÃO DE FORMATAÇÃO DE PREÇO ---
def formatar_preco(preco_novo, preco_antigo):
    if preco_antigo and preco_antigo.strip():
        # Markdown do Telegram para riscado é com ~~texto~~
        return f"💰 De: ~{preco_antigo}~\n💰 Por apenas: {preco_novo}"
    else:
        return f"💰 Por apenas: {preco_novo}"

# --- TEMPLATES ---
MESSAGE_TEMPLATES = [
    "🔥 OFERTA IMPERDÍVEL NA {plataforma} 🔥\n\n{produto}\n{preco_formatado}\n\n🛒 Compre aqui:\n{link}",
    "Oferta encontrada: 👀\n\n📦 {produto}\n{preco_formatado}\n\nConfira aqui:\n{link}",
    "Pesquisando preços... Achei! 👇\n\n✅ {produto} em promoção:\n{preco_formatado}\n\n➡️ {link}",
    "Boa oportunidade pra quem estava procurando:\n\n✅ {produto}\n{preco_formatado}\n\nConfira aqui 👉 {link}"
]

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

# --- FUNÇÃO DE ENVIO CORRIGIDA ---
def send_telegram_photo(token, channel, photo_url, caption):
    """
    Baixa a imagem da URL e a envia como um anexo, em vez de passar a URL diretamente.
    Isso é mais robusto e evita erros com formatos como .webp.
    """
    try:
        # 1. Baixar a imagem da URL
        print("    -> Baixando imagem da URL...")
        image_response = requests.get(photo_url, stream=True, timeout=20)
        image_response.raise_for_status()  # Gera um erro se o status não for 200 (OK)
        
        # 2. Preparar para enviar os dados da imagem
        files = {'photo': image_response.content}
        payload = {'chat_id': channel, 'caption': caption, 'parse_mode': 'Markdown'}

        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        
        # 3. Enviar a imagem como anexo
        print("    -> Enviando imagem como anexo para o Telegram...")
        response = requests.post(url, data=payload, files=files, timeout=30)
        response_json = response.json()
        
        if response_json.get("ok"):
            return True
        else:
            print(f"    -> Erro do Telegram: {response_json.get('description')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"    -> Erro de conexão ao baixar ou enviar imagem: {e}")
        return False
# --- FIM DA CORREÇÃO ---


def start_telegram_sender():
    print("🚀 Bot de envio do Telegram iniciado (v3 - Envio de imagem corrigido)...")
    plataformas = ["Shopee", "Mercado Livre", "Amazon"]
    fuso_horario_local = pytz.timezone("America/Sao_Paulo")
    
    mensagens_enviadas_no_lote = 0
    indice_plataforma_atual = 0

    while True:
        utc_now = datetime.now(timezone.utc)
        hora_local_obj = utc_now.astimezone(fuso_horario_local)
        hora_atual = hora_local_obj.hour
        
        print(f"({hora_local_obj.strftime('%H:%M:%S')}) - ❤️  Iniciando novo ciclo de busca (Lote: {mensagens_enviadas_no_lote}/5)...")

        if 7 <= hora_atual < 23:
            oferta_encontrada = None
            plataformas_verificadas = 0

            while not oferta_encontrada and plataformas_verificadas < len(plataformas):
                plataforma_atual = plataformas[indice_plataforma_atual]
                print(f"({hora_local_obj.strftime('%H:%M')}) - 🔎 Buscando oferta da plataforma: {plataforma_atual}...")
                oferta_encontrada = get_unsent_offer(plataforma_atual)
                
                indice_plataforma_atual = (indice_plataforma_atual + 1) % len(plataformas)
                plataformas_verificadas += 1

                if oferta_encontrada:
                    print(f"  -> ✅ Oferta encontrada para '{plataforma_atual}': {oferta_encontrada.get('produto', 'N/A')[:40]}...")
                elif plataformas_verificadas < len(plataformas):
                     print(f"  -> Nenhuma oferta para '{plataforma_atual}'. Tentando próxima...")
            
            if oferta_encontrada:
                preco_formatado = formatar_preco(oferta_encontrada['preco'], oferta_encontrada.get('preco_antigo'))
                
                template_escolhido = random.choice(MESSAGE_TEMPLATES)
                legenda_final = template_escolhido.format(
                    plataforma=oferta_encontrada['plataforma'].upper(), 
                    produto=oferta_encontrada['produto'],
                    preco_formatado=preco_formatado,
                    link=oferta_encontrada['link_afiliado']
                )

                if send_telegram_photo(BOT_TOKEN, CHANNEL_ID, oferta_encontrada['url_imagem'], legenda_final):
                    if mark_offer_as_sent(oferta_encontrada['id']):
                        mensagens_enviadas_no_lote += 1
                        print(f"    -> ✅ Enviada e marcada no DB. (Mensagem {mensagens_enviadas_no_lote}/5 do lote)")

                        if mensagens_enviadas_no_lote >= 5:
                            print("    -> 🏁 Fim do lote de 5 mensagens. Pausando por 15 minutos...")
                            time.sleep(900)
                            mensagens_enviadas_no_lote = 0
                        else:
                            intervalo = random.randint(60, 900)
                            print(f"    -> Pausando por {intervalo // 60} minutos e {intervalo % 60} segundos...")
                            time.sleep(intervalo)
                else:
                    print(f"    -> ❌ Falha no envio para o Telegram. Tentando novamente no próximo ciclo.")
                    # Em caso de falha no envio, também marcamos como "enviado" para não tentar repetidamente
                    # uma imagem quebrada. Você pode comentar a linha abaixo se preferir que ele tente de novo.
                    mark_offer_as_sent(oferta_encontrada['id'])
                    print("    -> Oferta marcada para não tentar novamente.")
                    time.sleep(60)
            else:
                print(f"({hora_local_obj.strftime('%H:%M')}) - 🤷 Nenhuma oferta nova em NENHUMA plataforma. Verificando novamente em 15 minutos.")
                time.sleep(900)
        else:
            print(f"({hora_local_obj.strftime('%H:%M')}) - 😴 Fora do horário. Bot dormindo por 30 minutos.")
            time.sleep(1800)

if __name__ == "__main__":
    start_telegram_sender()