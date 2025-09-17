# whatsapp_scheduler.py

import time
import os
import random
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz
from playwright.sync_api import sync_playwright
from database import supabase_client # Importando sua conexão com o Supabase

# --- ⚙️ CONFIGURAÇÕES ---
load_dotenv()
WHATSAPP_USER_DATA_DIR = "/home/anderson/.config/google-chrome/Profile 2"
EXECUTABLE_PATH = "/opt/google/chrome/google-chrome"
NOME_DO_GRUPO = "Oferta Scan # 1"
TABLE_NAME = "ofertas"
if not supabase_client:
    print("❌ ERRO: Verifique a conexão com o Supabase.")
    exit()

# --- FUNÇÕES DE INTERAÇÃO COM O BANCO DE DADOS ---
def get_offer_batch(count=5):
    """Busca um lote de ofertas ainda não enviadas para o WhatsApp."""
    try:
        response = supabase_client.table(TABLE_NAME).select("*").eq("enviado_whatsapp", False).limit(count).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"  -> Erro ao buscar lote de ofertas no Supabase: {e}")
        return []

def mark_offer_as_sent_whatsapp(offer_id):
    """Marca a oferta como enviada no WhatsApp na tabela."""
    try:
        supabase_client.table(TABLE_NAME).update({"enviado_whatsapp": True}).eq("id", offer_id).execute()
        return True
    except Exception as e:
        print(f"  -> Erro ao marcar oferta como enviada no Supabase: {e}")
        return False

# --- FUNÇÃO PRINCIPAL DO AGENDADOR ---
def start_whatsapp_scheduler():
    fuso_horario_local = pytz.timezone("America/Sao_Paulo")

    with sync_playwright() as p:
        print("🚀 Iniciando o navegador com perfil do WhatsApp...")
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=WHATSAPP_USER_DATA_DIR,
            executable_path=EXECUTABLE_PATH,
            headless=False, # Precisa ser visível para o login com QR Code
            args=['--start-maximized'],
            no_viewport=True,
        )
        
        pagina = contexto.new_page()

        try:
            print("🌍 Navegando para o WhatsApp Web...")
            pagina.goto("https://web.whatsapp.com/", timeout=120000)

            print("\n" + "="*50)
            print("🚨 AÇÃO MANUAL NECESSÁRIA (SE FOR A PRIMEIRA VEZ) 🚨")
            print("Se o QR Code aparecer, escaneie com seu celular. O script esperará...")
            print("="*50 + "\n")

            seletor_login_completo = 'div[data-testid="chat-list-search-container"]'
            pagina.wait_for_selector(seletor_login_completo, timeout=120000)
            
            print("✅ Login no WhatsApp Web bem-sucedido!")
            time.sleep(5)

            print(f"🔍 Procurando e abrindo o grupo: '{NOME_DO_GRUPO}'")
            pagina.locator('div[data-testid="chat-list-search"]').click()
            pagina.keyboard.type(NOME_DO_GRUPO, delay=100)
            time.sleep(2)
            pagina.locator(f'span[title="{NOME_DO_GRUPO}"]').click()
            print(f"💬 Grupo '{NOME_DO_GRUPO}' aberto. O bot está pronto para operar.")

            # --- LOOP PRINCIPAL DO AGENDADOR ---
            while True:
                agora = datetime.now(fuso_horario_local)
                hora_atual = agora.hour

                if 7 <= hora_atual < 23:
                    print(f"\n({agora.strftime('%H:%M:%S')}) - ☀️  Hora de trabalho. Buscando novo lote de ofertas...")
                    
                    lote_de_ofertas = get_offer_batch(random.randint(5, 6))

                    if not lote_de_ofertas:
                        print("  -> 🤷 Nenhuma oferta nova encontrada. Dormindo até a próxima hora.")
                        minutos_restantes = 60 - agora.minute
                        segundos_para_proxima_hora = (minutos_restantes * 60) - agora.second
                        time.sleep(segundos_para_proxima_hora)
                        continue

                    print(f"  -> ✅ Lote de {len(lote_de_ofertas)} ofertas encontrado para a hora.")
                    
                    # 1. Envia a primeira oferta
                    primeira_oferta = lote_de_ofertas.pop(0)
                    print(f"  ({datetime.now(fuso_horario_local).strftime('%H:%M:%S')}) - Enviando a 1ª oferta: {primeira_oferta['produto'][:30]}...")
                    enviar_mensagem_formatada(pagina, primeira_oferta)
                    mark_offer_as_sent_whatsapp(primeira_oferta['id'])

                    ultima_oferta = lote_de_ofertas.pop() if lote_de_ofertas else None
                    
                    # 2. Agenda e envia as ofertas do meio
                    if lote_de_ofertas:
                        inicio_janela = agora.replace(minute=2, second=0)
                        fim_janela = agora.replace(minute=58, second=0)
                        
                        timestamps_aleatorios = sorted([
                            datetime.fromtimestamp(random.randint(int(inicio_janela.timestamp()), int(fim_janela.timestamp())), tz=fuso_horario_local)
                            for _ in range(len(lote_de_ofertas))
                        ])

                        for oferta_meio, horario_envio in zip(lote_de_ofertas, timestamps_aleatorios):
                            agora_loop = datetime.now(fuso_horario_local)
                            if horario_envio > agora_loop:
                                tempo_espera = (horario_envio - agora_loop).total_seconds()
                                print(f"  -> Próxima oferta agendada para as {horario_envio.strftime('%H:%M:%S')}. Dormindo por {int(tempo_espera)}s...")
                                time.sleep(tempo_espera)
                                
                                print(f"  ({datetime.now(fuso_horario_local).strftime('%H:%M:%S')}) - Enviando oferta do meio: {oferta_meio['produto'][:30]}...")
                                enviar_mensagem_formatada(pagina, oferta_meio)
                                mark_offer_as_sent_whatsapp(oferta_meio['id'])

                    # 3. Agenda e envia a última oferta
                    if ultima_oferta:
                        horario_ultima_oferta = agora.replace(minute=59, second=random.randint(0, 55))
                        agora_loop = datetime.now(fuso_horario_local)
                        if horario_ultima_oferta > agora_loop:
                            tempo_espera = (horario_ultima_oferta - agora_loop).total_seconds()
                            print(f"  -> Última oferta agendada para as {horario_ultima_oferta.strftime('%H:%M:%S')}. Dormindo por {int(tempo_espera)}s...")
                            time.sleep(tempo_espera)

                            print(f"  ({datetime.now(fuso_horario_local).strftime('%H:%M:%S')}) - Enviando a última oferta: {ultima_oferta['produto'][:30]}...")
                            enviar_mensagem_formatada(pagina, ultima_oferta)
                            mark_offer_as_sent_whatsapp(ultima_oferta['id'])

                    # 4. Dorme até a próxima hora
                    agora_final = datetime.now(fuso_horario_local)
                    minutos_restantes_final = 60 - agora_final.minute
                    segundos_para_proxima_hora_final = (minutos_restantes_final * 60) - agora_final.second
                    print(f"  -> 🏁 Fim do lote da hora. Dormindo por {int(segundos_para_proxima_hora_final)}s até a próxima hora.")
                    if segundos_para_proxima_hora_final > 0:
                        time.sleep(segundos_para_proxima_hora_final)
                else:
                    print(f"({agora.strftime('%H:%M:%S')}) - 😴 Fora do horário. Dormindo até as 7h.")
                    proxima_hora_7 = agora.replace(hour=7, minute=0, second=0, microsecond=0)
                    if agora.hour >= 23: proxima_hora_7 += timedelta(days=1)
                    
                    tempo_espera = (proxima_hora_7 - agora).total_seconds()
                    time.sleep(tempo_espera)

        except Exception as e:
            print(f"❌ Erro crítico: {e}")
        finally:
            print("🚪 Fechando o navegador.")
            contexto.close()

def enviar_mensagem_formatada(pagina, oferta):
    """Constrói e envia a mensagem de oferta formatada no WhatsApp."""
    try:
        preco_formatado = f"💰 Por apenas: {oferta['preco']}"
        if oferta.get('preco_antigo') and str(oferta.get('preco_antigo')).strip():
            # A formatação do WhatsApp para riscado é com ~texto~
            preco_formatado = f"💰 De: ~{oferta['preco_antigo']}~\n💰 Por apenas: {oferta['preco']}"

        # Monta a mensagem final com a URL da imagem no início
        mensagem = (
            f"{oferta['url_imagem']}\n\n"
            f"🔥 *OFERTA IMPERDÍVEL NA {oferta['plataforma'].upper()}* 🔥\n\n"
            f"{oferta['produto']}\n"
            f"{preco_formatado}\n\n"
            f"🛒 *Compre aqui:*\n{oferta['link_afiliado']}"
        )

        caixa_de_texto = pagina.locator('div[contenteditable="true"][data-tab="10"]')
        caixa_de_texto.click()
        
        # O WhatsApp Web agora renderiza a imagem e o link automaticamente
        # Enviar a mensagem de uma vez é mais natural
        caixa_de_texto.fill(mensagem)
        time.sleep(random.uniform(1, 3)) # Pequena pausa para o preview do link aparecer
        pagina.keyboard.press("Enter")
        print("    ✅ Mensagem enviada.")

    except Exception as e:
        print(f"    ❌ Falha ao enviar mensagem formatada: {e}")


# --- EXECUÇÃO DO SCRIPT ---
if __name__ == "__main__":
    print("="*60)
    print("⚠️ ATENÇÃO: A AUTOMATIZAÇÃO DO WHATSAPP WEB É CONTRA OS TERMOS DE SERVIÇO ⚠️")
    print("   O USO DESTE SCRIPT PODE RESULTAR NO BANIMENTO PERMANENTE DO SEU NÚMERO.")
    print("   USE POR SUA CONTA E RISCO. RECOMENDA-SE USAR UM NÚMERO SECUNDÁRIO.")
    print("="*60)
    start_whatsapp_scheduler()