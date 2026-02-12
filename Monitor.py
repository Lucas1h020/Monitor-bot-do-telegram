import requests
import hashlib
import os
import json
import telebot
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES (Via Variáveis de Ambiente)
# ==========================================
# No PC, ele pega do .env. No GitHub, ele pega dos "Secrets".
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
    corpo = f"🔔 *Alerta de Mudança!*\n\nDetectamos alterações em:\n{texto_sites}"
    
    try:
        bot.send_message(CHAT_ID, corpo, parse_mode="Markdown")
        print("✅ Mensagem enviada.")
    except Exception as e:
        print(f"❌ Erro no Telegram: {e}")

def calcular_hash_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        
        # Lógica específica para o Cebraspe que você criou
        if "cebraspe.org.br" in url:
            h1 = soup.find(lambda tag: tag.name in ["h1", "h2"] and "TCE RS 25" in tag.get_text())
            if h1:
                textos = [h1.get_text(strip=True)]
                for sib in h1.find_all_next():
                    if sib.name == "footer": break
                    textos.append(sib.get_text(" ", strip=True))
                return hashlib.sha256("\n".join(textos).encode("utf-8")).hexdigest()

        # Padrão para outros sites
        return hashlib.sha256(soup.get_text().encode("utf-8")).hexdigest()
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

# ==========================================
# 3. EXECUÇÃO ÚNICA (Para Nuvem)
# ==========================================

def executar():
    urls = carregar_urls()
    if not urls: return

    estado_atual = carregar_estado()
    mudancas_detectadas = []
    
    for url in urls:
        print(f"Verificando: {url}")
        novo_hash = calcular_hash_url(url)
        if novo_hash is None: continue

        hash_antigo = estado_atual.get(url)
        if hash_antigo and novo_hash != hash_antigo:
            mudancas_detectadas.append(url)
        
        estado_atual[url] = novo_hash

    salvar_estado(estado_atual)
    
    if mudancas_detectadas:
        enviar_telegram(mudancas_detectadas)
    else:
        print("Sem alterações.")

if __name__ == "__main__":
    executar()
