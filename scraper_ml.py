# scraper_compraCerta.py (VERSÃO FINAL E FUNCIONAL)

import time
import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import random

# --- ⚙️ CONFIGURAÇÕES ---
USER_DATA_DIR = "/home/anderson/.config/google-chrome/Profile 1"
EXECUTABLE_PATH = "/opt/google/chrome/google-chrome"
HUB_URL = "https://www.mercadolivre.com.br/afiliados/hub#menu-user"
OUTPUT_FILE = "ofertas_mercado_livre.xlsx"
CATEGORIAS_ALVO = ["MAIS VENDIDO", "OFERTA DO DIA", "OFERTA RELÂMPAGO"]

# --- 🤖 INÍCIO DO SCRIPT ---

def scrape_affiliate_hub():
    lista_de_ofertas = []
    titulos_ja_processados = set()

    with sync_playwright() as p:
        print("🚀 Iniciando o navegador (usando seu perfil 'Profile 1')...")
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=EXECUTABLE_PATH,
            headless=False,
            args=['--start-maximized'],
            no_viewport=True,
        )
        pagina = contexto.new_page()
        try:
            print(f"🌍 Navegando para o Hub de Afiliados: {HUB_URL}")
            pagina.goto(HUB_URL, timeout=90000)
            print("🔍 Verificando se o login está ativo para o perfil 'OfertaScan'...")
            seletor_login_check = "h3:text('OfertaScan')"
            pagina.wait_for_selector(seletor_login_check, timeout=30000)
            print("✅ Login confirmado para 'OfertaScan'!")
            
            print("📜 Iniciando rolagem e colheita de produtos...")
            numero_de_rolagens = 50
            seletor_card_produto = "div.poly-card--grid-card"

            for i in range(numero_de_rolagens):
                print(f"  -> Rolagem {i+1}/{numero_de_rolagens}... Coletando novos produtos...")
                cards_visiveis = pagina.locator(seletor_card_produto).all()
                
                for card in cards_visiveis:
                    try:
                        titulo_el = card.locator("a.poly-component__title")
                        if not titulo_el.count(): continue
                        titulo = titulo_el.inner_text(timeout=2000)

                        if titulo in titulos_ja_processados:
                            continue
                        
                        titulos_ja_processados.add(titulo)

                        seletor_highlight = "span.poly-component__highlight"
                        highlight_element = card.locator(seletor_highlight)
                        if not highlight_element.count(): continue
                        
                        highlight_text = highlight_element.inner_text().strip()
                        if highlight_text not in CATEGORIAS_ALVO: continue

                        print(f"    [+] Encontrado: {titulo[:50]}...")
                        preco = card.locator("span.andes-money-amount__fraction").inner_text()
                        imagem_url = card.locator("img.poly-component__picture").get_attribute("src")

                        # --- LÓGICA FINAL PARA PEGAR O LINK ---
                        # 1. Clica em compartilhar no card para abrir o pop-up
                        card.locator("button:has-text('Compartilhar')").click()
                        
                        # 2. Dentro do pop-up, clica no botão "Copiar link" usando seu ID
                        botao_copiar_link_modal = pagina.locator('button#copy_link-undefined')
                        botao_copiar_link_modal.wait_for(state='visible', timeout=5000)
                        botao_copiar_link_modal.click()

                        # 3. Espera pela mensagem de confirmação (opcional, mas bom para garantir)
                        pagina.wait_for_selector('p.andes-snackbar__message:has-text("Você copiou o link")', timeout=5000)
                        
                        # 4. Lê o link da área de transferência
                        link_afiliado = pagina.evaluate("navigator.clipboard.readText()")
                        
                        # 5. Mostra o link capturado no console, como você pediu
                        print(f"      -> Link Capturado: {link_afiliado}")
                        
                        # 6. Fecha o pop-up
                        pagina.locator('button[aria-label="Fechar"]').click()
                        time.sleep(0.5)
                        
                        oferta = { "Produto": titulo, "Preço": f"R$ {preco}", "Categoria": highlight_text, "Link Afiliado": link_afiliado, "URL da Imagem": imagem_url, "Data Extracao": datetime.now().strftime("%Y-%m-%d %H-%M:%S")}
                        lista_de_ofertas.append(oferta)
                        print(f"      -> Sucesso! Total de ofertas na lista: {len(lista_de_ofertas)}")

                    except Exception as e:
                        if pagina.locator('button[aria-label="Fechar"]').count() > 0:
                            pagina.locator('button[aria-label="Fechar"]').click()
                        continue
                
                pagina.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
        
        except Exception as e:
            print(f"❌ Erro crítico durante a execução: {e}")
        finally:
            print("🚪 Fechando o navegador.")
            contexto.close()
            
    return lista_de_ofertas

def salvar_em_excel(ofertas):
    if not ofertas:
        print("🤷 Nenhuma oferta encontrada para salvar.")
        return
    df = pd.DataFrame(ofertas)
    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    print(f"✅ {len(ofertas)} ofertas salvas com sucesso no arquivo: '{OUTPUT_FILE}'")

if __name__ == "__main__":
    ofertas_coletadas = scrape_affiliate_hub()
    salvar_em_excel(ofertas_coletadas)