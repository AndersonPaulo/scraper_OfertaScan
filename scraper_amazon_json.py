import time
import random
import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# --- ⚙️ CONFIGURAÇÕES ---
USER_DATA_DIR = "/home/anderson/.config/google-chrome/Profile 2"  # ajuste para o perfil logado
EXECUTABLE_PATH = "/opt/google/chrome/google-chrome"
AMAZON_BESTSELLERS_URL = "https://www.amazon.com.br/gp/bestsellers/?ref_=nav_em_cs_bestsellers_0_1_1_2"
OUTPUT_FILE_AMAZON = "ofertas_amazon.json"
MAX_PRODUTOS = 100  # limite de produtos (pode aumentar)

# --- 🤖 SCRAPER AMAZON ---

def scrape_amazon_bestsellers():
    ofertas = []

    with sync_playwright() as p:
        print("🚀 Iniciando navegador (perfil logado na Amazon)...")
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=EXECUTABLE_PATH,
            headless=False,
            args=['--start-maximized'],
            no_viewport=True,
        )
        pagina = contexto.new_page()

        try:
            print(f"🌍 Acessando: {AMAZON_BESTSELLERS_URL}")
            pagina.goto(AMAZON_BESTSELLERS_URL, timeout=90000)
            pagina.wait_for_load_state("networkidle", timeout=60000)
            print("✅ Página dos Mais Vendidos carregada!")

            coletados = 0

            # --- LOOP DE PÁGINAS ---
            while True:
                cards_produtos = pagina.locator("div.p13n-sc-uncoverable-faceout").all()
                print(f"\n📦 {len(cards_produtos)} produtos encontrados nesta página.")

                for card in cards_produtos:
                    if coletados >= MAX_PRODUTOS:
                        print("⚠️ Limite de produtos atingido.")
                        break

                    try:
                        titulo = card.locator("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1").inner_text(timeout=3000)
                        preco_atual = card.locator("span.p13n-sc-price")
                        preco_antigo = card.locator("span.a-text-price")

                        # 🔎 Só continua se for oferta (tem preço riscado)
                        if preco_antigo.count() == 0:
                            continue

                        preco = preco_atual.inner_text() if preco_atual.count() > 0 else "N/A"
                        imagem_url = card.locator("img").get_attribute("src")

                        # Captura link de afiliado
                        botao_link = card.locator("button#amzn-ss-get-link-button")
                        if botao_link.count() == 0:
                            print("  [x] Botão 'Obter link' não encontrado, pulando...")
                            continue

                        botao_link.first.click()
                        pagina.wait_for_selector("textarea#amzn-ss-text-shortlink-textarea", timeout=5000)
                        link_afiliado = pagina.locator("textarea#amzn-ss-text-shortlink-textarea").input_value()

                        # Fechar modal
                        if pagina.locator("button[data-action='a-popover-close']").count() > 0:
                            pagina.locator("button[data-action='a-popover-close']").click()
                            time.sleep(0.3)

                        oferta = {
                            "Plataforma": "Amazon",
                            "Produto": titulo,
                            "Preço Atual": preco,
                            "Preço Antigo": preco_antigo.inner_text(),
                            "Link Afiliado": link_afiliado,
                            "URL da Imagem": imagem_url,
                            "Data Extracao": datetime.now(timezone.utc).isoformat()
                        }
                        ofertas.append(oferta)
                        coletados += 1
                        print(f"  [+] Oferta capturada: {titulo[:50]}... ({coletados} no total)")

                    except Exception as e:
                        print(f"  [x] Erro ao processar produto: {e}")
                        continue

                # 👉 Próxima página
                if coletados >= MAX_PRODUTOS:
                    break

                botao_next = pagina.locator("li.a-last a i.a-icon-next")
                if botao_next.count() > 0 and botao_next.first.is_visible():
                    print("➡️ Avançando para próxima página...")
                    botao_next.first.click()
                    pagina.wait_for_load_state("networkidle", timeout=20000)
                    time.sleep(2)
                else:
                    print("🏁 Fim da navegação.")
                    break

        except Exception as e:
            print(f"❌ Erro crítico no scraper da Amazon: {e}")
        finally:
            print("🚪 Fechando navegador.")
            contexto.close()

    return ofertas


# --- 💾 SALVAR EM JSON ---
def salvar_em_json_amazon(ofertas):
    if not ofertas:
        print("🤷 Nenhuma oferta encontrada para salvar.")
        return

    with open(OUTPUT_FILE_AMAZON, 'w', encoding='utf-8') as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=4)

    print(f"✅ {len(ofertas)} ofertas salvas com sucesso em: '{OUTPUT_FILE_AMAZON}'")


if __name__ == "__main__":
    ofertas_coletadas_amazon = scrape_amazon_bestsellers()
    salvar_em_json_amazon(ofertas_coletadas_amazon)
