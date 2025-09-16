# Robô de Ofertas para Afiliados

Este projeto consiste em dois robôs principais:
1.  **Scrapers (`scraper_compraCerta.py`, `scraper_shopee.py`):** Responsáveis por coletar ofertas das plataformas de afiliados e salvá-las em arquivos Excel.
2.  **Sender (`sender_telegram.py`):** Responsável por ler os arquivos Excel e enviar as ofertas para um canal do Telegram.

---

## Como Executar

### 🤖 Scraper do Mercado Livre

O scraper do Mercado Livre é o mais simples.

1.  Ative o ambiente virtual:
    ```bash
    source venv/bin/activate
    ```
2.  Execute o script:
    ```bash
    python scraper_compraCerta.py
    ```
3.  O script usará o `Profile 1` do Chrome e fará o login automaticamente (após a primeira vez). Ao final, gerará o arquivo `ofertas_ml_hub.xlsx`.

---

### 🛍️ Scraper da Shopee (Processo Especial)

Devido à segurança avançada da Shopee, este scraper exige um processo manual de 2 passos para iniciar.

**Passo 1: Iniciar o Navegador em Modo de Depuração**
* Abra um **primeiro terminal** e execute o comando abaixo. Uma janela do Chrome irá se abrir.
* **Faça o login** na sua conta de afiliado Shopee nesta janela.
* **Deixe esta janela e este terminal abertos** em segundo plano.

    ```bash
    /opt/google/chrome/google-chrome --remote-debugging-port=9222 --user-data-dir="/home/anderson/.config/google-chrome/Profile 3"
    ```

**Passo 2: Executar o Script de Coleta**
* Abra um **segundo terminal**.
* Ative o ambiente virtual:
    ```bash
    source venv/bin/activate
    ```
* Execute o script. Ele irá se conectar ao navegador que você deixou aberto e começará a trabalhar.
    ```bash
    python scraper_shopee.py
    ```
* Ao final, ele gerará o arquivo `ofertas_shopee.xlsx` e o primeiro terminal (com o navegador) poderá ser fechado.

---

### ✈️ Enviador para o Telegram

Este script envia as ofertas coletadas para o seu canal.

1.  Garanta que os arquivos `.xlsx` com as ofertas já foram gerados pelos scrapers.
2.  Ative o ambiente virtual:
    ```bash
    source venv/bin/activate
    ```
3.  Execute o script:
    ```bash
    python sender_telegram.py
    ```
4.  O robô começará a enviar as ofertas em lotes, respeitando o horário de funcionamento (5h - 22h).