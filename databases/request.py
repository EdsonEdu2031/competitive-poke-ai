import os
import gzip
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configurações para VGC e Bo3 (Best of 3)
BASE_URL = "https://www.smogon.com/stats/"
FORMATOS_ALVO = ["gen9championsvgc2026regmb", "gen9championsvgc2026regmbbo3"]
NIVEL_RANKING = "1760" # High ladder (hank alto)
PASTA_DESTINO = "smogon_metagame_data"

def obter_links(url):
    resposta = requests.get(url)
    resposta.raise_for_status()
    soup = BeautifulSoup(resposta.text, 'html.parser')
    return [a['href'] for a in soup.find_all('a') if a['href'] not in ('../', '/')]

def baixar_e_extrair_gz(url, pasta_destino, nome_arquivo_txt):
    resposta = requests.get(url)
    resposta.raise_for_status()
    
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_completo = os.path.join(pasta_destino, nome_arquivo_txt)
    
    # Descompacta o arquivo .gz para texto puro
    texto = gzip.decompress(resposta.content).decode('utf-8')
    
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write(texto)
    print(f"[+] Arquivo salvo: {caminho_completo}")

def main():
    meses = obter_links(BASE_URL)
    meses_validos = [m for m in meses if m.endswith('/') and "20" in m]
    ultimo_mes = sorted(meses_validos)[-1]
    url_mes_recente = urljoin(BASE_URL, ultimo_mes)
    
    for formato in FORMATOS_ALVO:
        nome_arquivo_gz = f"{formato}-{NIVEL_RANKING}.txt.gz" 
        nome_arquivo_txt = f"{formato}-{NIVEL_RANKING}.txt"
        
        #Baixar as estatísticas gerais de Uso
        url_uso = urljoin(url_mes_recente, nome_arquivo_gz)
        try:
            baixar_e_extrair_gz(url_uso, PASTA_DESTINO, f"uso_geral_{nome_arquivo_txt}")
        except Exception as e:
            print(f"[-] Arquivo de uso não encontrado para {formato}: {e}")

        #Baixar os dados de movesets (Ataques, itens, etc)
        url_moveset = urljoin(url_mes_recente, f"moveset/{nome_arquivo_gz}")
        try:
            baixar_e_extrair_gz(url_moveset, PASTA_DESTINO, f"movesets_{nome_arquivo_txt}")
        except Exception as e:
            print(f"[-] Arquivo de movesets não encontrado para {formato}: {e}")
            
        #Baixar os dados de chaos (Dados Brutos de Correlação)
        url_chaos = urljoin(url_mes_recente, f"chaos/{f"{formato}-{NIVEL_RANKING}.json.gz"}")
        try:
            baixar_e_extrair_gz(url_chaos, PASTA_DESTINO, f"chaos_{f"{formato}-{NIVEL_RANKING}.json"}")
        except Exception as e:
            print(f"[-] Arquivo de chaos não encontrado para {formato}: {e}")
        
        #Baixar os dados de leads (Estatísticas de Abertura)
        url_lead = urljoin(url_mes_recente, f"leads/{nome_arquivo_gz}")
        try:
            baixar_e_extrair_gz(url_lead, PASTA_DESTINO, f"leads_{nome_arquivo_txt}")
        except Exception as e:
            print(f"[-] Arquivo de leads não encontrado para {formato}: {e}")

if __name__ == "__main__":
    main()