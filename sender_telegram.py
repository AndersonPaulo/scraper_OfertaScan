# sender_telegram.py (VERSÃO MELHORADA)
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

# --- FUNÇÃO DE FORMATAÇÃO DE PREÇO (NOVO) ---
def formatar_preco(preco_novo, preco_antigo):
    """Formata a string de preço para exibir 'De/Por' quando aplicável."""
    if preco_antigo and preco_antigo.strip():
        return f"💰 De: ~{preco_antigo}~\n💰 Por apenas: {preco_novo}"
    else:
        return f"💰 Por apenas: {preco_novo}"

# --- TEMPLATES ATUALIZADOS ---
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

def send_telegram_photo(token, channel, photo_url, caption):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {'chat_id': channel, 'photo': photo_url, 'caption': caption, 'parse_mode': 'MarkdownV2'} # Habilitar Markdown
    try:
        response = requests.post(url, data=payload, timeout=30)
        response_json = response.json()
        if response_json.get("ok"): return True
        else:
            print(f"    -> Erro do Telegram: {response_json.get('description')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"    -> Erro de conexão: {e}")
        return False

# --- LÓGICA PRINCIPAL DO BOT (COM MELHORIAS 2 e 3) ---
def start_telegram_sender():
    print("🚀 Bot de envio do Telegram iniciado (v2 - Intervalos ajustados e busca corrigida)...")
    plataformas = ["Shopee", "Mercado Livre", "Amazon"] # Lista de plataformas para rodízio
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

            # MELHORIA 3: Loop para garantir que todas as plataformas sejam verificadas
            while not oferta_encontrada and plataformas_verificadas < len(plataformas):
                plataforma_atual = plataformas[indice_plataforma_atual]
                print(f"({hora_local_obj.strftime('%H:%M')}) - 🔎 Buscando oferta da plataforma: {plataforma_atual}...")
                oferta_encontrada = get_unsent_offer(plataforma_atual)
                
                # Prepara para a próxima plataforma no rodízio
                indice_plataforma_atual = (indice_plataforma_atual + 1) % len(plataformas)
                plataformas_verificadas += 1

                if oferta_encontrada:
                    print(f"  -> ✅ Oferta encontrada para '{plataforma_atual}': {oferta_encontrada.get('produto', 'N/A')[:40]}...")
                elif plataformas_verificadas < len(plataformas):
                     print(f"  -> Nenhuma oferta para '{plataforma_atual}'. Tentando próxima...")
            
            if oferta_encontrada:
                # Usa a nova função para formatar o preço
                preco_formatado = formatar_preco(oferta_encontrada['preco'], oferta_encontrada.get('preco_antigo'))
                
                template_escolhido = random.choice(MESSAGE_TEMPLATES)
                legenda_final = template_escolhido.format(
                    plataforma=oferta_encontrada['plataforma'].upper(), 
                    produto=oferta_encontrada['produto'],
                    preco_formatado=preco_formatado, # Usa a string de preço já formatada
                    link=oferta_encontrada['link_afiliado']
                )

                # Prepara para Markdown (escapa caracteres especiais)
                legenda_final = legenda_final.replace('.', '\\.').replace('-', '\\-').replace('!', '\\!').replace('~', '~~')

                if send_telegram_photo(BOT_TOKEN, CHANNEL_ID, oferta_encontrada['url_imagem'], legenda_final):
                    if mark_offer_as_sent(oferta_encontrada['id']):
                        mensagens_enviadas_no_lote += 1
                        print(f"    -> ✅ Enviada e marcada no DB. (Mensagem {mensagens_enviadas_no_lote}/5 do lote)")

                        # MELHORIA 2: Novos intervalos de tempo
                        if mensagens_enviadas_no_lote >= 5:
                            print("    -> 🏁 Fim do lote de 5 mensagens. Pausando por 15 minutos...")
                            time.sleep(900)  # Pausa longa de 15 minutos
                            mensagens_enviadas_no_lote = 0 # Reinicia o contador
                        else:
                            intervalo = random.randint(60, 900) # Sorteia entre 1 min (60s) e 15 min (900s)
                            print(f"    -> Pausando por {intervalo // 60} minutos e {intervalo % 60} segundos...")
                            time.sleep(intervalo)
                else:
                    print(f"    -> ❌ Falha no envio para o Telegram. Tentando novamente no próximo ciclo.")
                    time.sleep(60)
            else:
                print(f"({hora_local_obj.strftime('%H:%M')}) - 🤷 Nenhuma oferta nova em NENHUMA plataforma. Verificando novamente em 15 minutos.")
                time.sleep(900)
        else:
            print(f"({hora_local_obj.strftime('%H:%M')}) - 😴 Fora do horário. Bot dormindo por 30 minutos.")
            time.sleep(1800)

if __name__ == "__main__":
    start_telegram_sender()