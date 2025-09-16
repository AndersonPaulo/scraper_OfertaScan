# main.py (ou um script de orquestração)
import time
import threading
from scraper_ml import scrape_mercado_livre # Ajuste o caminhoscraper
from scraper_shopee import ShopeeScraper
from sender_telegram import start_telegram_sender
from database import initialize_database # Ajuste o caminho

# Tempo para rodar os scrapers (ex: a cada 30 minutos)
SCRAPER_RUN_INTERVAL_MINUTES = 30

def run_scrapers_periodically():
    while True:
        print('\n--- Iniciando raspagem de dados ---')
        # Garante que o DB está inicializado antes de cada raspagem (já acontece no database.py)
        # initialize_database() 
        
        try:
            # Chame suas funções de raspagem aqui
            # Exemplo: (você precisará adaptar isso para como suas funções de raspagem são chamadas)
            scrape_mercado_livre("exemplo de pesquisa ml") # Substitua pela sua chamada real
            scrape_shopee("exemplo de pesquisa shopee") # Substitua pela sua chamada real
        except Exception as e:
            print(f"Erro durante a raspagem: {e}")
        
        print('--- Raspagem de dados concluída ---')
        time.sleep(SCRAPER_RUN_INTERVAL_MINUTES * 60)

def main():
    initialize_database() # Garante que o DB esteja pronto no início da aplicação

    # Inicia o serviço de envio do Telegram em uma thread separada
    telegram_sender_thread = threading.Thread(target=start_telegram_sender)
    telegram_sender_thread.daemon = True # Permite que o programa principal saia mesmo se esta thread estiver rodando
    telegram_sender_thread.start()

    # Inicia o serviço de raspagem em uma thread separada
    scraper_thread = threading.Thread(target=run_scrapers_periodically)
    scraper_thread.daemon = True
    scraper_thread.start()

    # Mantém o programa principal rodando para que as threads em daemon não morram
    try:
        while True:
            time.sleep(3600) # Espera uma hora, pode ser qualquer tempo longo
    except KeyboardInterrupt:
        print("\n[Main] Encerrando aplicação. Limpeza em andamento...")
        # As threads daemon serão encerradas automaticamente
        print("[Main] Aplicação finalizada.")

if __name__ == '__main__':
    main()