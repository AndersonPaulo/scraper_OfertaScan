# scraper_amazon_json.py

import time
import random
from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime, timezone
import json
import re

# --- ⚙️ CONFIGURAÇÕES ---
CDP_URL = "http://localhost:9222"
OUTPUT_FILE = "scraper_amazon.json"
MAX_PAGES_TO_SCRAPE = 5

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 1.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]

# --- 🤖 INÍCIO DO SCRIPT DE SCRAPING ---
def scrape_amazon_associates():
    lista_de_dados = []
    
    with sync_playwright() as p:
        print(f"🚀 Tentando conectar ao navegador na porta {CDP_URL}...")
        try:
            navegador = p.chromium.connect_over_cdp(CDP_URL)
            contexto = navegador.contexts[0]
            pagina = contexto.pages[0]
            print("✅ Conexão bem-sucedida! Assumindo controle da primeira aba.")
        
        except Exception as e:
            print(f"❌ ERRO: Não foi possível conectar ao navegador.")
            print(f"   Verifique se você iniciou o Chrome com o comando: --remote-debugging-port=9222")
            return []

        try:
            print(f"🔗 URL atual da página controlada: {pagina.url}")

            seletor_obter_link = '#amzn-ss-get-link-button'
            print(f"\n🔎 Verificando a presença do botão 'Obter link' ('{seletor_obter_link}')...")
            
            try:
                pagina.wait_for_selector(seletor_obter_link, state='visible', timeout=20000)
                print("✅ Barra de Associados e botão 'Obter link' encontrados! Prosseguindo...")
            except TimeoutError:
                print("\n❌ ERRO CRÍTICO: O botão 'Obter link' da barra de associados não foi encontrado.")
                pagina.screenshot(path='screenshot_erro_final.png')
                print("📸 Um screenshot ('screenshot_erro_final.png') foi salvo para análise.")
                return []

            print("\n--- 🤖 Iniciando a lógica de scraping... ---")
            pagina_atual = 1

            while pagina_atual <= MAX_PAGES_TO_SCRAPE:
                print(f"\n--- 📄 Processando Página {pagina_atual}/{MAX_PAGES_TO_SCRAPE} ---")
                
                seletor_card_produto = '#gridItemRoot'
                pagina.wait_for_selector(seletor_card_produto, timeout=30000)
                todos_os_itens = pagina.locator(seletor_card_produto).all()
                print(f"🔍 Encontrados {len(todos_os_itens)} produtos na página.")

                for item in todos_os_itens:
                    try:
                        titulo_loc = item.locator('a.a-link-normal img')
                        titulo = titulo_loc.get_attribute('alt') if titulo_loc.count() > 0 else "N/A"

                        preco_loc = item.locator('span._cDEzb_p13n-sc-price_3mJ9Z')
                        preco = preco_loc.inner_text() if preco_loc.count() > 0 else "N/A"
                        
                        # --- ATUALIZADO: Capturar preço antigo ---
                        preco_antigo_loc = item.locator('span.a-text-strike')
                        preco_antigo = None
                        if preco_antigo_loc.count() > 0:
                            preco_antigo_raw = preco_antigo_loc.inner_text().replace("R$", "").strip()
                            preco_antigo = f"R$ {preco_antigo_raw}"
                        # --- FIM DA ATUALIZAÇÃO ---

                        imagem_url_loc = item.locator('a.a-link-normal img')
                        imagem_url = imagem_url_loc.get_attribute('src') if imagem_url_loc.count() > 0 else "N/A"

                        if titulo == "N/A" or preco == "N/A": continue

                        print(f"  🛒 Produto: {titulo[:50]}...")
                        
                        get_link_button = pagina.locator(seletor_obter_link)
                        get_link_button.click()

                        link_textarea_selector = '#amzn-ss-text-shortlink-textarea'
                        pagina.locator(link_textarea_selector).wait_for(state='visible', timeout=10000)
                        
                        link_afiliado = pagina.locator(link_textarea_selector).input_value()
                        print(f"    🔗 Link de afiliado capturado: {link_afiliado}")
                        
                        pagina.keyboard.press("Escape")
                        pagina.locator(link_textarea_selector).wait_for(state='hidden', timeout=5000)

                        dado = {
                            "Plataforma": "Amazon",
                            "Produto": titulo.strip(),
                            "Preco": preco.strip(),
                            "preco_antigo": preco_antigo, # Campo adicionado
                            "Link Afiliado": link_afiliado.strip(),
                            "URL da Imagem": imagem_url,
                            "Data Extracao": datetime.now(timezone.utc).isoformat()
                        }
                        lista_de_dados.append(dado)

                    except Exception as e:
                        print(f"  [x] Erro ao processar um item: {e}")
                        try:
                            pagina.keyboard.press("Escape")
                        except:
                            pass
                        continue

                next_button_selector = 'li.a-last a'
                next_button = pagina.locator(next_button_selector)

                if next_button.count() > 0 and pagina_atual < MAX_PAGES_TO_SCRAPE:
                    print(f"  -> Indo para a página {pagina_atual + 1}...")
                    next_button.click()
                    pagina.wait_for_load_state('networkidle', timeout=30000)
                    pagina_atual += 1
                else:
                    print("🏁 Não há mais páginas para navegar ou limite atingido. Fim do scraping.")
                    break

            print("\n✅ Scraping concluído com sucesso!")

        except Exception as e:
            print(f"❌ Erro crítico durante o scraping: {e}")
            pagina.screenshot(path='screenshot_erro_amazon.png')
            print("📸 Screenshot 'screenshot_erro_amazon.png' salvo para análise.")
            
    return lista_de_dados

def salvar_em_json(dados):
    if not dados:
        print("🤷 Nenhum dado foi extraído para salvar.")
        return
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
        
    print(f"💾 {len(dados)} registros salvos com sucesso em: '{OUTPUT_FILE}'")

if __name__ == "__main__":
    dados_coletados = scrape_amazon_associates()
    salvar_em_json(dados_coletados)