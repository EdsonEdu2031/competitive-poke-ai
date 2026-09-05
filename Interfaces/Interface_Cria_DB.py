import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(page_title = "PokeAI - Criador Benchmark", page_icon = "logo.jpg", layout="wide")

st.title("Criador de Benchmark")

try:
    df = pd.read_csv('Perguntas_Metagame.csv')
    st.write(f"Há {len(df)} questões! ")
except (ValueError, FileNotFoundError):
    st.write("Não há questões cadastradas!")

pergunta = st.text_area("Informe a pergunta: ", placeholder="Pergunta", key="pergunta")
resposta = st.text_area("Informe a resposta: ", placeholder="Resposta", key="resposta")

if st.button("Salvar", type="primary"):
    try:
        df = pd.read_csv("Perguntas_Metagame.csv")
    except (ValueError, FileNotFoundError):
        df = pd.DataFrame(columns=["pergunta", "resposta"])

    df.loc[len(df)] = {"pergunta": pergunta, "resposta": resposta}

    df.to_csv("Perguntas_Metagame.csv", index=False)
    st.success("Pergunta salva com sucesso!")
    time.sleep(0.5)
    st.rerun()