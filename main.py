# main.py (Responsável por enviar dados para o Supabase)
import json
import os
from database import supabase_client # Importa o cliente já inicializado

# Nomes dos arquivos JSON gerados pelos scrapers
JSON_FILES = ["ofertas_shopee.json", "ofertas_mercado_livre.json"]
TABLE_NAME = "ofertas"

def upload_offers_to_supabase():
    """Lê os arquivos JSON locais e faz o upsert na tabela 'ofertas' do Supabase."""
    if not supabase_client:
        print("❌ Upload cancelado. Cliente Supabase não está disponível.")
        return

    all_offers = []
    print("\n--- 📖 Lendo arquivos JSON locais ---")
    for file_name in JSON_FILES:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                offers = json.load(f)
                all_offers.extend(offers)
                print(f"  ✅ {len(offers)} ofertas lidas de '{file_name}'")
        except FileNotFoundError:
            print(f"  ⚠️  Arquivo '{file_name}' não encontrado. Pulando.")
        except json.JSONDecodeError:
            print(f"  ❌ Erro ao decodificar o JSON em '{file_name}'. O arquivo pode estar vazio ou corrompido.")

    if not all_offers:
        print("\n🤷 Nenhuma oferta encontrada nos arquivos para enviar. Encerrando.")
        return

    print(f"\n--- ☁️  Enviando {len(all_offers)} ofertas para o Supabase ---")
    print(f"   (Usando 'upsert' com a coluna 'link_afiliado' para evitar duplicatas)")

    try:
        # 'upsert' insere novas ofertas e atualiza as existentes com base no 'link_afiliado'
        # A coluna 'enviado_telegram' não é modificada se a oferta já existir
        data, count = supabase_client.table(TABLE_NAME).upsert(
            all_offers,
            on_conflict='link_afiliado'
        ).execute()

        print("✅ Operação de Upsert concluída com sucesso!")
        # O 'count' no resultado do upsert pode ser um pouco complexo de interpretar
        # O mais importante é que a operação foi executada sem erros.
        
    except Exception as e:
        print(f"❌ Erro ao enviar dados para o Supabase: {e}")

if __name__ == '__main__':
    # Este script é executado para sincronizar os dados locais com a nuvem.
    upload_offers_to_supabase()