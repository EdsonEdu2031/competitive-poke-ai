import sys
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

nome_modelo = sys.argv[1]

from pathlib import Path
import json
import re
import uuid
import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import pandas as pd
import random
import os
import accelerate
from unsloth import FastLanguageModel, get_chat_template
import gc


# Função de busca no Qdrant
def recuperar_contexto(pergunta, k=5):
    embedding = modelo.encode(pergunta, normalize_embeddings=True).tolist()
    resultados = client.query_points(collection_name=COLECAO, query=embedding, limit=k, with_payload=True)
    resultados = resultados.points
    if not resultados:
        logging.info("Nenhum resultado encontrado.")
        return []
    contextos = []
    for indice, resultado in enumerate(resultados, start=1):
        payload = resultado.payload
        contextos.append({
            "arquivo": payload.get("arquivo"),
            "texto": payload.get("texto", "")
        })
    return contextos

def montar_contexto(contextos):
    if not contextos:
        return "Nenhum contexto relevante foi recuperado pelo sistema RAG."

    partes = []

    for indice, contexto in enumerate(contextos, start=1):
        trecho = f"""
<Fonte numero="{indice}">
Arquivo: {contexto['arquivo']}
Conteúdo:
{contexto['texto']}
</Fonte>
"""
        partes.append(trecho)

    return "\n".join(partes)
# Carregamento do modelo

os.environ["UNSLOTH_DISABLE_FAST_GENERATION"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

nome_modelo_completo = {
    'DeepSeek':'DeepSeek-V4-Pro-Qwen3.5-4B', 
    'Gemma':'gemma-3-4b-it', 
    'Llama':'Llama-3.2-3B-Instruct', 
    'Qwen':'Qwen3.5-4B'
}

path = f'/mnt/di_ruralgpt/users/Edson/PokeAI/Models/{nome_modelo_completo[nome_modelo]}'
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=path,
    max_seq_length=16384,
    load_in_4bit=True,
    device_map="cuda:0",
)

model.generation_config.max_length = None
FastLanguageModel.for_inference(model)

if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# Configurações Qdrant
PASTA_QDRANT = f"/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/RAG/Metagame/qdrant_db_{nome_modelo}"
COLECAO = "pokeai_minilm_text"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Quantidade de trechos para recuperar
K  = 5

modelo = SentenceTransformer(MODELO, device="cuda")
client = QdrantClient(path=PASTA_QDRANT)

# Carregamento do arquivo CSV com as perguntas
df = pd.read_csv("/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/02112026_Perguntas_Metagame.csv")

if "contexto_RAG" not in df.columns:
    df["contexto_RAG"] = ""

if "resposta_gerada" not in df.columns:
    df["resposta_gerada"] = ""

total = len(df)

# Prompt
instruction = open("/mnt/di_ruralgpt/users/Edson/PokeAI/competitive-poke-ai/Codes/Prompts/prompt_Inferência.txt", "r", encoding="utf-8").read()

# Iterar sobre todas as perguntas fazendo a inferência
for index, row in df.iterrows():
    logging.info(f"Gerando resposta para questão {index+1}/{total}")
    pergunta = row['pergunta']

    if pd.notna(row['resposta_gerada']) and row['resposta_gerada'].strip() != "":
        continue

    contextos = recuperar_contexto(pergunta, k=K)
    trechos_RAG = montar_contexto(contextos)
    
    infos = f'''
        Contexto recuperado pelo RAG:

        <contexto>
        {trechos_RAG}
        </contexto>

        Pergunta do usuário:

        <pergunta>
        {pergunta}
        </pergunta>

        Responda seguindo rigorosamente as instruções acima.
    '''

    prompt = instruction + infos
    messages = [{"role": "user", "content": prompt}]

    if nome_modelo in ['Qwen', 'DeepSeek']:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    else:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    #inputs = tokenizer([prompt], return_tensors="pt", padding=True).to("cuda")
    inputs = tokenizer(text=[prompt], return_tensors="pt", padding=True).to("cuda")
    prompt_len = inputs.input_ids.shape[1]

    outputs = model.generate(**inputs, max_new_tokens=2048, use_cache=True, do_sample=False)#, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)

    generated_tokens = outputs[0][prompt_len:]
    hypothesis = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    if "</think>" in hypothesis:
        hypothesis = hypothesis.split("</think>", 1)[1].strip()

    df.at[index, 'contexto_RAG'] = trechos_RAG
    df.at[index, 'resposta_gerada'] = hypothesis
    logging.info(f'\nPergunta {index+1}: {pergunta} \n\n Resposta: {hypothesis}')
    if index % 10 == 0:
        df.to_csv(f"/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/Results/Eval_{nome_modelo}_Perguntas_Metagame.csv", index=False)
        logging.info(f"Progresso salvo após {index+1} perguntas processadas.")
df.to_csv(f"/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/Results/Eval_{nome_modelo}_Perguntas_Metagame.csv", index=False)

client.close()
