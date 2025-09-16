# main.py (Versão FINAL CORRIGIDA)
import json
import os
import unicodedata
from database import supabase_client

# Nomes dos arquivos JSON gerados pelos scrapers
JSON_FILES = ["ofertas_shopee.json", "ofertas_mercado_livre.json"]
TABLE_NAME = "ofertas"


# --- Função para normalizar as chaves ---
def normalize_key(key_string):
    """
    Converte uma string para o formato de coluna de DB.
    """
    nfkd_form = unicodedata.normalize('NFKD', key_string)
    ascii_string = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    # MODIFICADO: Adicionado .replace('_da_', '_') para corrigir o nome da coluna da imagem
    return ascii_string.lower().replace(' ', '_').replace('_da_', '_')


def upload_offers_to_supabase():
    """Lê os arquivos JSON, formata as chaves para o padrão do DB e faz o upsert."""
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
            print(f"  ❌ Erro ao decodificar o JSON em '{file_name}'.")

    if not all_offers:
        print("\n🤷 Nenhuma oferta encontrada para enviar. Encerrando.")
        return

    print("\n--- 🔄 Formatando dados para o padrão do banco de dados (snake_case) ---")
    formatted_offers = []
    for offer in all_offers:
        formatted_offer = {
            normalize_key(key): value for key, value in offer.items()
        }
        
        expected_columns = ['plataforma', 'produto', 'preco', 'categoria', 'desconto', 'comissao', 'link_afiliado', 'url_imagem', 'data_extracao']
        for col in expected_columns:
            if col not in formatted_offer:
                formatted_offer[col] = None
        
        formatted_offers.append(formatted_offer)
    print("  ✅ Formatação concluída.")

    print(f"\n--- ☁️  Enviando {len(formatted_offers)} ofertas para o Supabase ---")
    print(f"   (Usando 'upsert' com a coluna 'link_afiliado' para evitar duplicatas)")

    try:
        data, count = supabase_client.table(TABLE_NAME).upsert(
            formatted_offers,
            on_conflict='link_afiliado'
        ).execute()
        print("✅ Operação de Upsert concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao enviar dados para o Supabase: {e}")

if __name__ == '__main__':
    upload_offers_to_supabase()