#!/bin/bash
#PBS -N Infe_DeepSeek_PokeAI
#PBS -q workq
#PBS -l select=1:modelgpu=A100:ngpus=1
#PBS -V

# Redireciona os logs usando as variáveis que agora existem em tempo de execução
exec > "/mnt/di_ruralgpt/users/Edson/PokeAI/competitive-poke-ai/Codes/Jobs/logs/${PBS_JOBNAME}_${PBS_JOBID}.out" 2> "/mnt/di_ruralgpt/users/Edson/PokeAI/competitive-poke-ai/Codes/Jobs/logs/${PBS_JOBNAME}_${PBS_JOBID}.err"

/mnt/di_ruralgpt/users/Edson/PokeAI/.venv/bin/python /mnt/di_ruralgpt/users/Edson/PokeAI/competitive-poke-ai/Codes/Inferência_Cluster.py DeepSeek
