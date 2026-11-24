import time

def avaliar(respostas):
    time.sleep(5)
    return {
        "resposta_escolhida": respostas['resposta4']['resposta'],
        "nova_consulta": 1,
        "pergunta_nova_consulta": 'Qual é a diferença entre o Perish Song de Politoed e o Perish Song de Mega Gengar?'
    }

