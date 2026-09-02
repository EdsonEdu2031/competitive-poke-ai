import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title = "PokeAI - Criador Benchmark", page_icon = "logo.jpg", layout="wide")


st.title("Criador de Benchmark")

#df = pd.read_json('Perguntas_Metagame.json')
#st.write(f"Há {len(df)} questões! ")

pergunta = st.text_area("Informe a pergunta: ", placeholder="Pergunta")
resposta = st.text_area("Informe a resposta: ", placeholder="Resposta")

if st.button("Salvar", type="primary"):

    arquivo = "Perguntas_Metagame.json"

    try:
        df = pd.read_json(arquivo)
    except (ValueError, FileNotFoundError):
        df = pd.DataFrame(columns=["pergunta", "resposta"])

    df.loc[len(df)] = {"pergunta": pergunta, "resposta": resposta}

    df.to_json(arquivo, orient="records", force_ascii=False, indent=4)

    st.success("Pergunta salva com sucesso!")
    st.rerun()