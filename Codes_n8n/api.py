
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from consulta import consultar_modelo
from refinador import avaliar

app = FastAPI(title="n8n PokeAI API")

gpu_lock = threading.Lock()


# Requisição para os agentes
class Requisicao(BaseModel):
    pergunta: str
    nome_modelo: str

# Estrutura da resposta de cada agente
class RespostaModelo(BaseModel):
    resposta: str

# Requisição para o refinador
class RequisicaoAvaliacao(BaseModel):
    resposta1: RespostaModelo
    resposta2: RespostaModelo
    resposta3: RespostaModelo
    resposta4: RespostaModelo

@app.post("/responder")
def responder(dados: Requisicao):
    with gpu_lock:
        try:
            resposta = consultar_modelo(
                dados.pergunta,
                dados.nome_modelo
            )
            return resposta

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/avaliar")
def avaliar_respostas(dados: RequisicaoAvaliacao):
    with gpu_lock:
        try:
            respostas = dados.model_dump()
            avaliacao = avaliar(respostas)

            return avaliacao

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    PORTA = 8000

    print(f"API do PokeAI no ar: http://localhost:{PORTA}")

    uvicorn.run(app, host="0.0.0.0", port=PORTA)
