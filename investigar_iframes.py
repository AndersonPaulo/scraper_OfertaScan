# investigar_iframes.py

from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9222"

def find_iframes_on_page():
    with sync_playwright() as p:
        try:
            print(f"🚀 Conectando ao navegador na porta {CDP_URL} para investigar...")
            navegador = p.chromium.connect_over_cdp(CDP_URL)
            contexto = navegador.contexts[0]
            pagina = contexto.pages[0]
            print(f"✅ Conectado com sucesso à página: {pagina.title()}")
            print("-" * 50)
        except Exception as e:
            print(f"❌ Não foi possível conectar ao navegador. Verifique se ele foi iniciado com a porta 9222.")
            print(f"   Erro: {e}")
            return

        print("🔎 Procurando por todos os iframes na página...")
        
        # Espera um pouco para garantir que todos os scripts da página carregaram
        pagina.wait_for_timeout(5000) # Espera 5 segundos

        # Pega todos os elementos iframe
        iframes = pagina.locator('iframe').all()

        if not iframes:
            print("🤷 Nenhum iframe foi encontrado na página.")
            return

        print(f"✅ Encontrados {len(iframes)} iframes. Listando detalhes:")
        print("-" * 50)

        # Itera sobre cada iframe encontrado e imprime seus atributos
        for i, iframe_element in enumerate(iframes):
            frame_id = iframe_element.get_attribute('id')
            frame_name = iframe_element.get_attribute('name')
            frame_src = iframe_element.get_attribute('src')
            
            print(f"🔎 Iframe #{i+1}:")
            print(f"   ID:    {frame_id or 'Nenhum'}")
            print(f"   Name:  {frame_name or 'Nenhum'}")
            print(f"   SRC:   {frame_src or 'Nenhum'}")
            print("-" * 50)

if __name__ == "__main__":
    find_iframes_on_page()