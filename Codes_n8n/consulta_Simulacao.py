import pandas as pd
import time

def consultar_modelo(pergunta, nome_modelo):
    df = pd.read_csv(f'C:/PokeAI/databases/P&R/Metagame/3-LLM_Judge/LLM_Judge_{nome_modelo}_Perguntas_Metagame.csv')
    indice_pergunta = 318
    contexto = df.iloc[indice_pergunta]['contexto_RAG']
    resposta_certa = df.iloc[indice_pergunta]['resposta']
    resposta_gerada = df.iloc[indice_pergunta]['resposta_gerada']
    resposta = {"resposta": resposta_gerada}
    """print(f'Pergunta: {df.iloc[indice_pergunta]['pergunta']}')
    print(f'Resposta correta: {resposta_certa}')
    print(3*'\n')
    print(f'Modelo: {nome_modelo} > {resposta_gerada}')
    print(f'Modelo: {nome_modelo} > {contexto}')
    print(3*'\n')"""
    time.sleep(5)
    return resposta


#consultar_modelo('pergunta', 'Qwen')
#consultar_modelo('pergunta', 'Gemma')
#consultar_modelo('pergunta', 'DeepSeek')
#consultar_modelo('pergunta', 'Llama')