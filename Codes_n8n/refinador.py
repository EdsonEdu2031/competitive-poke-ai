import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import pandas as pd
import os
import accelerate
from unsloth import FastLanguageModel
import re

caminho_base = 'C:/PokeAI' # Local
#caminho_base = '/mnt/di_ruralgpt/users/Edson/PokeAI' # No Cluster


def interpretar_refinador(hypothesis):

    # Extrair o indicador de nova consulta
    match = re.search(r'^2-\s*([01])\s*$', hypothesis, re.MULTILINE)

    if not match:
        raise ValueError("Indicador de nova consulta inválido.")

    nova_consulta = int(match.group(1))

    # Extrair a resposta escolhida
    match_resposta = re.search(
        r'1-\s*(.*?)\n2-',
        hypothesis,
        re.DOTALL
    )

    if not match_resposta:
        raise ValueError("Resposta escolhida não encontrada.")

    resposta_escolhida = match_resposta.group(1).strip()

    # Extrair a pergunta para nova consulta
    match_pergunta = re.search(
        r'^3-\s*(.*)',
        hypothesis,
        re.MULTILINE
    )

    pergunta_nova = match_pergunta.group(1).strip() if match_pergunta else ""

    # Retorno estruturado
    return {
        "resposta_escolhida": resposta_escolhida,
        "nova_consulta": nova_consulta,
        "pergunta_nova_consulta": pergunta_nova
    }


def avaliar(respostas):
    path = f'{caminho_base}/Models/Llama-3.2-3B-Instruct'
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
    # Prompt
    instruction = open(f"{caminho_base}/competitive-poke-ai/Codes_Eval/Prompts/prompt_Refinador.txt", "r", encoding="utf-8").read()

    infos = f'''
<resposta_avaliar>
Resposta 1:
{respostas['resposta1']['resposta']}

Resposta 2:
{respostas['resposta2']['resposta']}

Resposta 3:
{respostas['resposta3']['resposta']}

Resposta 4:
{respostas['resposta4']['resposta']}
</resposta_avaliar>
    '''

    prompt = instruction + infos
    messages = [{"role": "user", "content": prompt}]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(text=[prompt], return_tensors="pt", padding=True).to("cuda")
    prompt_len = inputs.input_ids.shape[1]

    outputs = model.generate(**inputs, max_new_tokens=2048, use_cache=True, do_sample=False)

    generated_tokens = outputs[0][prompt_len:]
    hypothesis = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    if "</think>" in hypothesis:
        hypothesis = hypothesis.split("</think>", 1)[1].strip()
    print(hypothesis)
    return interpretar_refinador(hypothesis)