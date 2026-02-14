import requests
import hashlib
import os
import json
import telebot
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES (Via GitHub Secrets)
# ==========================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ARQUIVO_URLS = "urls.txt"
ARQUIVO_DB = "db_hashes.json"

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 2. FUNÇÕES AUXILIARES
# ==========================================

def carregar_urls():
    if not os.path.exists(ARQUIVO_URLS):
        return []
    with open(ARQUIVO_URLS, "r") as f:
        return [linha.strip() for linha in f if linha.strip()]

def carregar_estado():
    if not os.path.exists(ARQUIVO_DB):
        return {}
    try:
        with open(ARQUIVO_DB, "r") as f:
            return json.load(f)
    except:
        return {}

def salvar_estado(dados):
    with open(ARQUIVO_DB, "w") as f:
        json.dump(dados, f, indent=4)

def enviar_telegram(lista_mudancas):
    print(f"[{datetime.now()}] Enviando alerta via Telegram...")
    texto_sites = "\n".join([f"🔗 {url}" for url in lista_mudancas])
    corpo = f"🔔 *Alerta de Mudança!*\n\nDetectamos alterações em:\n\n{texto_sites}"
    try:
        bot.send_message(CHAT_ID, corpo, parse_mode="Markdown")
        print("✅ Mensagem enviada com sucesso.")
    except Exception as e:
        print(f"❌ Erro no Telegram: {e}")

def calcular_hash_url(url):
    """Baixa o conteúdo bruto, exatamente como no seu script original"""
    try:
        # Headers mais fortes para evitar bloqueio do Cebraspe
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        # Adicionamos o 'verify=False' caso o site tenha erro de SSL, comum em órgãos públicos
        r = requests.get(url, headers=headers, timeout=30, verify=True)
        r.raise_for_status()
        
        # Retorna o hash do conteúdo bruto (funciona melhor para o Cebraspe)
        return hashlib.sha256(r.content).hexdigest()
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

# ==========================================
# 3. LÓGICA PRINCIPAL (Adaptada para Nuvem)
# ==========================================

def tarefa_verificar():
    print(f"--- Iniciando Verificação: {datetime.now().strftime('%H:%M:%S')} ---")
    
    urls = carregar_urls()
    if not urls:
        print("Nenhuma URL encontrada.")
        return

    estado_atual = carregar_estado()
    mudancas_detectadas = []
    
    for url in urls:
        print(f"Verificando: {url} ...", end=" ")
        novo_hash = calcular_hash_url(url)
        
        if novo_hash is None:
            print("FALHA")
            continue

        hash_antigo = estado_atual.get(url)

        if hash_antigo is None:
            print("NOVO (Mapeado)")
            estado_atual[url] = novo_hash
        elif novo_hash != hash_antigo:
            print("ALTERAÇÃO DETECTADA!")
            mudancas_detectadas.append(url)
            estado_atual[url] = novo_hash
        else:
            print("Sem alterações")

    salvar_estado(estado_atual)
    
    if mudancas_detectadas:
        enviar_telegram(mudancas_detectadas)
    else:
        print(">> Nenhuma notificação necessária.")

if __name__ == "__main__":
    tarefa_verificar()
