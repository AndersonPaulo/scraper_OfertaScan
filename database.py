# src/database.py
import sqlite3
import os
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'ads.db')

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True) # Garante que o diretório 'data' exista
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anuncios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origem TEXT NOT NULL,           -- 'Mercado Livre' ou 'Shopee'
            nome_produto TEXT NOT NULL,
            preco_original REAL,
            preco_oferta REAL NOT NULL,
            link TEXT UNIQUE NOT NULL,      -- Link único para evitar duplicatas
            imagem_url TEXT,
            data_coleta TEXT NOT NULL,      -- Data da última raspagem (ISO format)
            status_envio TEXT DEFAULT 'pendente', -- 'pendente', 'enviado', 'erro'
            data_ultimo_envio TEXT,         -- Quando foi enviado ao Telegram pela última vez (ISO format)
            ignorar_ate TEXT                -- Data até quando o anúncio deve ser ignorado para evitar spam (ISO format)
        );
    ''')
    conn.commit()
    conn.close()
    print(f"[SQLite] Banco de dados '{DB_PATH}' e tabela 'anuncios' verificados/criados.")

def save_ad(ad):
    conn = get_db_connection()
    cursor = conn.cursor()

    origem = ad.get('origem')
    nome_produto = ad.get('nome_produto')
    preco_original = ad.get('preco_original')
    preco_oferta = ad.get('preco_oferta')
    link = ad.get('link')
    imagem_url = ad.get('imagem_url')
    data_coleta = datetime.now().isoformat()

    try:
        # UPSERT: Tenta atualizar ou inserir um anúncio
        cursor.execute('''
            INSERT INTO anuncios (origem, nome_produto, preco_original, preco_oferta, link, imagem_url, data_coleta)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(link) DO UPDATE SET
                nome_produto = EXCLUDED.nome_produto,
                preco_original = EXCLUDED.preco_original,
                preco_oferta = EXCLUDED.preco_oferta,
                imagem_url = EXCLUDED.imagem_url,
                data_coleta = EXCLUDED.data_coleta,
                status_envio = 'pendente'; -- Marca como pendente novamente se houver atualização
        ''', (origem, nome_produto, preco_original, preco_oferta, link, imagem_url, data_coleta))
        conn.commit()
        # print(f"[SQLite] Anúncio salvo/atualizado: {nome_produto}")
    except sqlite3.Error as e:
        print(f"[SQLite] Erro ao salvar anúncio {nome_produto}: {e}")
    finally:
        conn.close()

def get_pending_ads(origem, limit=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        SELECT * FROM anuncios 
        WHERE origem = ? 
          AND status_envio = 'pendente' 
          AND (ignorar_ate IS NULL OR ignorar_ate < ?)
        ORDER BY data_coleta ASC 
        LIMIT ?
    ''', (origem, now, limit))
    ads = cursor.fetchall()
    conn.close()
    return [dict(ad) for ad in ads] # Converte para lista de dicionários

def mark_ad_as_sent(ad_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_envio = datetime.now().isoformat()
    # Ignorar por 24 horas após o envio
    ignorar_ate = (datetime.now() + timedelta(hours=24)).isoformat() 
    try:
        cursor.execute('''
            UPDATE anuncios 
            SET status_envio = 'enviado', data_ultimo_envio = ?, ignorar_ate = ?
            WHERE id = ?
        ''', (data_envio, ignorar_ate, ad_id))
        conn.commit()
        # print(f"[SQLite] Anúncio ID {ad_id} marcado como enviado.")
    except sqlite3.Error as e:
        print(f"[SQLite] Erro ao marcar anúncio ID {ad_id} como enviado: {e}")
    finally:
        conn.close()

# Garante que o DB seja inicializado ao importar o módulo
initialize_database()

if __name__ == '__main__':
    # Exemplo de uso e teste
    print("Testando database.py...")
    ad1 = {
        'origem': 'Mercado Livre',
        'nome_produto': 'Produto Teste ML',
        'preco_original': 100.0,
        'preco_oferta': 80.0,
        'link': 'http://link.ml/teste1',
        'imagem_url': 'http://img.ml/teste1.jpg'
    }
    ad2 = {
        'origem': 'Shopee',
        'nome_produto': 'Produto Teste Shopee',
        'preco_original': 50.0,
        'preco_oferta': 35.0,
        'link': 'http://link.shopee/teste1',
        'imagem_url': 'http://img.shopee/teste1.jpg'
    }

    save_ad(ad1)
    save_ad(ad2)

    pending_ml = get_pending_ads('Mercado Livre', limit=1)
    if pending_ml:
        print(f"Anúncio pendente ML: {pending_ml[0]}")
        mark_ad_as_sent(pending_ml[0]['id'])
        print(f"Anúncio {pending_ml[0]['id']} marcado como enviado.")
    
    pending_shopee = get_pending_ads('Shopee', limit=1)
    if pending_shopee:
        print(f"Anúncio pendente Shopee: {pending_shopee[0]}")
    
    print("Teste concluído.")