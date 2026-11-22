import sys
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# Todos modelos disponíveis
modelos_disponiveis = ['DeepSeek', 'Gemma', 'Llama', 'Qwen']

# O código receberá, via terminal, o modelo que deverá ser executado:
# Puxando o nome do juiz direto pela execução do terminal, rodando: python <nome_codigo>.py <nome_modelo_juiz>
juiz = sys.argv[1]
checkpoint = 10

# Checando se o nome é válido
if juiz not in modelos_disponiveis:
    logging.info(f'Esse modelo não é válido, tente: {modelos_disponiveis[0]}, {modelos_disponiveis[1]}, {modelos_disponiveis[2]} ou {modelos_disponiveis[3]}')
    sys.exit(0)

import pandas as pd
import numpy as np
import json
import os
import accelerate
import torch
from unsloth import FastLanguageModel, get_chat_template
import re
import gc

os.environ["UNSLOTH_DISABLE_FAST_GENERATION"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"


# Função para extrair a avaliação da resposta dos juizes, recebe o texto gerado pelo juiz, e o converte para uma lista
def extrair_avaliacao(texto):
    avaliacao = {}

    for linha in texto.splitlines():
        # Captura valores de 1 a 5 (ou 1.0 a 5.0), aceitando '=' ou ':'
        match = re.match(r'^\s*(?:\*\*|\*|\b)(.+?)(?:\*\*|\*|\b)?\s*[:=]\s*([1-5](?:\.0+)?)\s*$', linha, re.IGNORECASE)

        if match:
            criterio = match.group(1).strip()
            nota = int(float(match.group(2)))
            avaliacao[criterio] = nota

    return avaliacao

# TextoC: Irá pedir 9 critérios: fluencia, coerencia, coesao, relevancia, factualidade, completude, contextualizacao, utilidade e proposito.
textoC = open("/mnt/di_ruralgpt/users/Edson/PokeAI/competitive-poke-ai/Codes_Eval/Prompts/prompt_LLM_Judge.txt", "r", encoding="utf-8").read()

# Função 'avaliacao': irá solicitar ao juiz a avaliação específica.
# Parâmetros: modelo e tokenizer já carregados, pergunta, resposta do modelo e resposta esperada (gabarito) para avaliação, nome do modelo (usado somente para controle)
def avaliacao(model, tokenizer, pergunta, resposta_do_modelo, resposta_esperada, juiz):
    infos = f'''
    <INICIO DA PARTE PARA AVALIAÇÃO>
        <INICIO PERGUNTA>
        {pergunta}
        <FIM PERGUNTA>

        <INICIO GABARITO>
        {resposta_esperada}
        <FIM GABARITO>

        <INICIO RESPOSTA GERADA>
        {resposta_do_modelo}
        <FIM RESPOSTA GERADA>
    <FIM DA PARTE PARA AVALIAÇÃO>
    '''
    prompt = textoC + infos

    # Todos hiperparâmetros dos modelos são os padrões fornecidos pelo seu desenvolvedor, com exceção do chat template que foi especificado pelo Givanildo
    # O que tornou necessário mudar os terminators
    messages = [{"role": "user", "content": prompt}]

    if juiz in ['Qwen', 'DeepSeek']:
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

    logging.info(f'\n\nSaida (LIMPA) = {hypothesis}\n\n')
    return extrair_avaliacao(hypothesis)

# Dicionário para mapear os nomes simplificados nos nomes reais
nome_modelo_completo = {
    'DeepSeek':'DeepSeek-V4-Pro-Qwen3.5-4B', 
    'Gemma':'gemma-3-4b-it', 
    'Llama':'Llama-3.2-3B-Instruct', 
    'Qwen':'Qwen3.5-4B'
}

logging.info(f'Avaliação iniciada! \n\n\nCarregando {juiz}')

path_juiz = f'/mnt/di_ruralgpt/users/Edson/PokeAI/Models/{nome_modelo_completo[juiz]}'
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=path_juiz,
    max_seq_length=16384,
    load_in_4bit=True,
    device_map="cuda:0",
)

model.generation_config.max_length = None
FastLanguageModel.for_inference(model)

#tokenizer = get_chat_template(tokenizer, chat_template=chat_templates[juiz])

if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id


for modelo_a_avaliar in modelos_disponiveis:
    if modelo_a_avaliar == juiz:
        continue
    arquivo = f'/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/Automatic/Eval_Automatic_{modelo_a_avaliar}_Perguntas_Metagame.csv'
    arquivo_saida = f'/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/LLM_Judge/LLM_Judge_{juiz}_{modelo_a_avaliar}_Perguntas_Metagame.csv'
    try:
        df = pd.read_csv(arquivo)
    except:
        logging.info(f'Arquivo não encontrado, pulando! Caminho: {arquivo}')
        sys.exit(1)

    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    # Checando se o arquivo existe, se não existir, será um cópia do arquivo atual
    if os.path.exists(arquivo_saida):
        df_saida = pd.read_csv(arquivo_saida)
    else:
        df_saida = df.copy()

    colunas_avaliacao = [f'{criterio}_{juiz}' for criterio in ['fluencia', 'coerencia', 'coesao', 'completude', 'relevancia', 'factualidade', 'contextualizacao', 'utilidade', 'proposito']]

    for coluna in colunas_avaliacao:
        if coluna not in df_saida.columns:
            df_saida[coluna] = pd.NA

    logging.info(f'    Iniciando a avaliação do Modelo: {modelo_a_avaliar} - Juiz: {juiz}')

    for index, row in df.iterrows():
        # Verificando se a questão já foi avaliada
        # Se pelo menos uma nota estiver faltando, irá rodar novamente.
        if df_saida.loc[index, colunas_avaliacao].notna().all():

            logging.info(f'    Questão {index} pulada! (Juiz: {juiz})')
            continue
        pergunta = row['pergunta']
        resposta_esperada = row['resposta']
        resposta_gerada = row['resposta_gerada']

        notas_finais = {
            f'{criterio}_{juiz}': [] 
            for criterio in ['fluencia', 'coerencia', 'coesao', 'completude', 'relevancia', 'factualidade', 'contextualizacao', 'utilidade', 'proposito']
        }
        logging.info(f'Questão {index}\n\n')

        saida_juiz = avaliacao(model, tokenizer, pergunta, resposta_gerada, resposta_esperada, juiz)
        for chave, valor in saida_juiz.items():
            col = f'{chave.lower()}_{juiz}'

            if col in colunas_avaliacao:
                df_saida.loc[index, col] = valor
        
        logging.info(f'    Questão {index} processada! (Juiz: {juiz} - {len(saida_juiz)} Notas geradas)')
        # Salvando a cada checkpoint
        if (index + 1) % checkpoint == 0:
            df_saida.to_csv(arquivo_saida, index=False)

    # Salva o restante
    df_saida.to_csv(arquivo_saida, index=False)

del model
del tokenizer
gc.collect()
torch.cuda.empty_cache()
torch.cuda.ipc_collect()

logging.info(f'Avaliação finalizada!')
