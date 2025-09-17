# scraper_shopee_json.py

import time
import random
from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import json
import re

# --- ⚙️ CONFIGURAÇÕES ---
PRODUCT_OFFER_URL = "https://affiliate.shopee.com.br/offer/product_offer"
OUTPUT_FILE_SHOPEE = "ofertas_shopee.json"
MIN_DISCOUNT_PERCENT = 10
MAX_PAGES_TO_SCRAPE = 6

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 1.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]

js_stealth = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"

def human_click(locator):
    locator.hover()
    time.sleep(random.uniform(0.2, 0.6))
    locator.click(delay=random.uniform(80, 250))

# --- 🤖 INÍCIO DO SCRIPT ---

def scrape_shopee_offers():
    lista_de_ofertas = []
    
    with sync_playwright() as p:
        print("🚀 Conectando ao navegador já aberto na porta 9222...")
        try:
            navegador = p.chromium.connect_over_cdp("http://localhost:9222")
            contexto = navegador.contexts[0]
            pagina = contexto.pages[0]
            pagina.add_init_script(js_stealth)
            print("✅ Conexão bem-sucedida!")
        except Exception as e:
            print(f"❌ ERRO ao conectar ao navegador: {e}")
            return []

        try:
            user_agent_aleatorio = random.choice(USER_AGENTS)
            pagina.set_extra_http_headers({"User-Agent": user_agent_aleatorio})
            print(f"🕵️ Usando User-Agent: {user_agent_aleatorio}")

            if PRODUCT_OFFER_URL not in pagina.url:
                print(f"🌍 Navegando para: {PRODUCT_OFFER_URL}")
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

                        # --- ATUALIZADO: Capturar preço antigo ---
                        preco_antigo_raw_el = card.locator('span.original-price')
                        preco_antigo = None
                        if preco_antigo_raw_el.count() > 0:
                            preco_antigo_raw = preco_antigo_raw_el.inner_text()
                            preco_antigo = f"R$ {preco_antigo_raw}"
                        # --- FIM DA ATUALIZAÇÃO ---
                        
                        imagem_url = card.locator('div.ItemCard__image img').get_attribute('src')
                        taxa_comissao_el = card.locator('div.commRate')
                        taxa_comissao = taxa_comissao_el.inner_text() if taxa_comissao_el.count() > 0 else "N/A"

                        human_click(card.locator('button:has-text("Obter link")'))
                        
                        botao_copiar = pagina.locator('button:has-text("Copiar link")')
                        botao_copiar.wait_for(state="visible", timeout=7000)

                        human_click(botao_copiar)
                        
                        time.sleep(random.uniform(0.5, 1.2))
                        
                        link_afiliado = pagina.evaluate("navigator.clipboard.readText()")
                        print(f"  [+] Link capturado para: {titulo[:40]}...")
                        
                        pagina.keyboard.press("Escape")
                        pagina.locator(seletor_modal_wrap).wait_for(state='hidden', timeout=5000)

                        oferta = {
                            "Plataforma": "Shopee",
                            "Produto": titulo,
                            "Preco": preco,
                            "preco_antigo": preco_antigo, # Campo adicionado
                            "Desconto": f"{discount_value}%",
                            "Comissao": taxa_comissao,
                            "Link Afiliado": link_afiliado,
                            "URL da Imagem": imagem_url,
                            "Data Extracao": datetime.now(timezone.utc).isoformat()
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
                    
                    human_click(next_button)
                    time.sleep(random.uniform(1.5, 3.0))
                    pagina.wait_for_load_state('networkidle', timeout=20000)
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
    
    with open(OUTPUT_FILE_SHOPEE, 'w', encoding='utf-8') as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=4)
        
    print(f"✅ {len(ofertas)} ofertas da Shopee salvas com sucesso em: '{OUTPUT_FILE_SHOPEE}'")

if __name__ == "__main__":
    ofertas_coletadas_shopee = scrape_shopee_offers()
    salvar_em_json_shopee(ofertas_coletadas_shopee)