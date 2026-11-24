import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import pandas as pd
import os
import accelerate
from unsloth import FastLanguageModel
import gc

caminho_base = 'C:/PokeAI' # Local
#caminho_base = '/mnt/di_ruralgpt/users/Edson/PokeAI' # No Cluster

PASTA_QDRANT = f"{caminho_base}/databases/RAG/Metagame/qdrant_db"
COLECAO = "pokeai_minilm_text"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Quantidade de trechos para recuperar
K  = 5

if "modelo_qdrant" not in globals():
    modelo_qdrant = SentenceTransformer(MODELO, device="cuda")

if "client" not in globals():
    client = QdrantClient(path=PASTA_QDRANT)

# Função de busca no Qdrant
def recuperar_contexto(pergunta):
    # Configurações Qdrant
    embedding = modelo_qdrant.encode(pergunta, normalize_embeddings=True).tolist()
    resultados = client.query_points(collection_name=COLECAO, query=embedding, limit=5, with_payload=True)
    resultados = resultados.points
    if not resultados:
        print("Nenhum resultado encontrado.")
        return []
    contextos = []
    for indice, resultado in enumerate(resultados, start=1):
        payload = resultado.payload
        contextos.append({
            "arquivo": payload.get("arquivo"),
            "texto": payload.get("texto", "")
        })
    return contextos

# Função para montar o contexto pra inferência
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

os.environ["UNSLOTH_DISABLE_FAST_GENERATION"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

def carregar_modelo(nome_modelo):
    nome_modelo_completo = {
        'DeepSeek':'DeepSeek-V4-Pro-Qwen3.5-4B', 
        'Gemma':'gemma-3-4b-it', 
        'Llama':'Llama-3.2-3B-Instruct', 
        'Qwen':'Qwen3.5-4B'
    }
    path = f'{caminho_base}/Models/{nome_modelo_completo[nome_modelo]}'
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=path,
        max_seq_length=8192, # 16384
        load_in_4bit=True,
        device_map="cuda:0",
    )

    model.generation_config.max_length = None
    FastLanguageModel.for_inference(model)

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    return model, tokenizer

def consultar_modelo(pergunta, nome_modelo):
    model, tokenizer = carregar_modelo(nome_modelo)
    
    # Prompt
    instruction = open(f"{caminho_base}/competitive-poke-ai/Codes_Eval/Prompts/prompt_Inferência.txt", "r", encoding="utf-8").read()

    contextos = recuperar_contexto(pergunta)
    trechos_RAG = montar_contexto(contextos)
    #trechos_RAG = 'Bacana'
    
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

    inputs = tokenizer(text=[prompt], return_tensors="pt", padding=True).to("cuda")
    prompt_len = inputs.input_ids.shape[1]

    outputs = model.generate(**inputs, max_new_tokens=2048, use_cache=True, do_sample=False)

    generated_tokens = outputs[0][prompt_len:]
    hypothesis = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    if "</think>" in hypothesis:
        hypothesis = hypothesis.split("</think>", 1)[1].strip()

    #hypothesis = 'Não sei com base nas informações disponíveis.'
    #trechos_RAG = 'Bacana'
    resposta = {"resposta": hypothesis, "contexto": [contexto["texto"] for contexto in contextos]}

    del inputs, outputs, model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()

    return resposta
