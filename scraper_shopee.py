# scraper_shopee_json.py

import time
import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import re
import json

# --- ⚙️ CONFIGURAÇÕES ---
SHOPEE_USER_DATA_DIR = "/home/anderson/.config/google-chrome/Profile 3"
EXECUTABLE_PATH = "/opt/google/chrome/google-chrome"
PRODUCT_OFFER_URL = "https://affiliate.shopee.com.br/offer/product_offer"
OUTPUT_FILE_SHOPEE = "ofertas_shopee.json"  # Alterado para .json
MIN_DISCOUNT_PERCENT = 20
MAX_PAGES_TO_SCRAPE = 5

# --- 🤖 INÍCIO DO SCRIPT ---

def scrape_shopee_offers():
    lista_de_ofertas = []
    
    with sync_playwright() as p:
        print("🚀 Conectando ao navegador já aberto na porta 9222...")
        try:
            navegador = p.chromium.connect_over_cdp("http://localhost:9222")
            contexto = navegador.contexts[0]
            pagina = contexto.pages[0]
            print("✅ Conexão bem-sucedida!")
        except Exception:
            print("❌ ERRO: Não foi possível conectar ao navegador da Shopee.")
            return []

        try:
            if PRODUCT_OFFER_URL not in pagina.url:
                pagina.goto(PRODUCT_OFFER_URL, timeout=90000)
            print("✅ Página de ofertas da Shopee carregada. Iniciando coleta...")
            
            for page_num in range(1, MAX_PAGES_TO_SCRAPE + 1):
                print(f"\n--- 📄 Processando Página {page_num}/{MAX_PAGES_TO_SCRAPE} ---")
                pagina.wait_for_selector('div.product-offer-item', timeout=30000)
                cards_produtos = pagina.locator('div.product-offer-item').all()
                print(f"🛍️  Encontrados {len(cards_produtos)} produtos nesta página.")

                for card in cards_produtos:
                    seletor_modal_wrap = 'div.ant-modal-wrap'
                    try:
                        try:
                            discount_text = card.locator('span.DiscountBadge__discount').inner_text(timeout=2000)
                            discount_value = int(re.sub(r'\D', '', discount_text))
                        except:
                            discount_value = 0

                        if discount_value < MIN_DISCOUNT_PERCENT:
                            continue

                        titulo = card.locator('div.ItemCard__name').inner_text()
                        preco_raw = card.locator('span.price').inner_text()
                        preco = f"R$ {preco_raw}"
                        imagem_url = card.locator('div.ItemCard__image img').get_attribute('src')
                        taxa_comissao_el = card.locator('div.commRate')
                        taxa_comissao = taxa_comissao_el.inner_text() if taxa_comissao_el.count() > 0 else "N/A"

                        card.locator('button:has-text("Obter link")').click()
                        botao_copiar = pagina.locator('button:has-text("Copiar link")')
                        botao_copiar.wait_for(state="visible", timeout=7000)
                        botao_copiar.click()
                        time.sleep(0.5)
                        
                        link_afiliado = pagina.evaluate("navigator.clipboard.readText()")
                        print(f"  [+] Link capturado para: {titulo[:40]}...")
                        
                        pagina.keyboard.press("Escape")
                        pagina.locator(seletor_modal_wrap).wait_for(state='hidden', timeout=5000)

                        oferta = {
                            "Plataforma": "Shopee", "Produto": titulo, "Preço": preco,
                            "Desconto": f"{discount_value}%", "Comissão": taxa_comissao,
                            "Link Afiliado": link_afiliado, "URL da Imagem": imagem_url,
                            "Data Extracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        lista_de_ofertas.append(oferta)
                    
                    except Exception as e:
                        print(f"  [x] Erro ao processar produto: {e}")
                        modal_wrap = pagina.locator(seletor_modal_wrap)
                        if modal_wrap.count() > 0 and modal_wrap.is_visible():
                             pagina.keyboard.press("Escape")
                             modal_wrap.wait_for(state='hidden', timeout=5000)
                        continue
                
                print(f"  -> Fim da página {page_num}. Total de ofertas coletadas: {len(lista_de_ofertas)}")
                next_button = pagina.locator('span.page-item.page-next:not(.disabled)')
                if next_button.count() > 0 and page_num < MAX_PAGES_TO_SCRAPE:
                    print("  -> Clicando no botão 'Próxima Página'...")
                    next_button.click()
                    pagina.wait_for_load_state('networkidle', timeout=15000)
                else:
                    print("🏁 Fim da navegação da Shopee.")
                    break
        except Exception as e:
            print(f"❌ Erro crítico no scraper da Shopee: {e}")
            
    return lista_de_ofertas

def salvar_em_json_shopee(ofertas):
    if not ofertas:
        print("🤷 Nenhuma oferta da Shopee foi encontrada para salvar.")
        return
    
    # Salva a lista de dicionários diretamente em um arquivo JSON
    with open(OUTPUT_FILE_SHOPEE, 'w', encoding='utf-8') as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=4)
        
    print(f"✅ {len(ofertas)} ofertas da Shopee salvas com sucesso em: '{OUTPUT_FILE_SHOPEE}'")

if __name__ == "__main__":
    ofertas_coletadas_shopee = scrape_shopee_offers()
    salvar_em_json_shopee(ofertas_coletadas_shopee)