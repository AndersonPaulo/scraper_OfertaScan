# database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Carrega as credenciais do Supabase do arquivo .env
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Validação inicial
if not url or not key:
    raise Exception("Credenciais do Supabase (URL e KEY) não encontradas no arquivo .env")

# Cria uma instância única do cliente Supabase para ser usada em todo o projeto
try:
    supabase_client: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
except Exception as e:
    print(f"❌ Falha ao conectar com o Supabase: {e}")
    supabase_client = None