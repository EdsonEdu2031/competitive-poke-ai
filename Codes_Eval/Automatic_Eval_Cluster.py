# Métricas: BLEU, BERTScore, MoverScore, METEOR e ROUGE

# No Cluster dá erro essa parte, foi calculado a parte
#import nltk
#nltk.download('wordnet')
#from nltk.translate.meteor_score import meteor_score
import pandas as pd
import sacrebleu
from rouge_score import rouge_scorer
from bert_score import score as bert_score
rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
import os
os.environ['MOVERSCORE_MODEL'] = 'neuralmind/bert-base-portuguese-cased'
import torch
import numpy as np
import pandas as pd
import moverscore_v2
from transformers import PreTrainedTokenizerBase
from moverscore_v2 import get_idf_dict, word_mover_score

# Adaptações para MoverScore
np.float = float
np.int = int
np.bool = bool

PreTrainedTokenizerBase.max_len = property(lambda self: self.model_max_length)

# Correção no collate_idf (sincronização de tokens e retorno em np.array)
def collate_idf_fixed(arr, tokenize, numericalize, idf_dict, pad="[PAD]", device='cuda:0'):
    tokens = [["[CLS]"] + tokenize(s)[:510] + ["[SEP]"] for s in arr]
    numerical_arr = [numericalize(token) for token in tokens]
    
    pad_id = numericalize([pad])[0]
    maxlen = min(max(len(s) for s in numerical_arr), 512)
    
    padded_sens = [s[:maxlen] + [pad_id] * max(0, maxlen - len(s)) for s in numerical_arr]
    padded_idf = [[idf_dict[token] for token in s[:maxlen]] + [0.0] * max(0, maxlen - len(s)) for s in tokens]
    
    lens = [min(len(s), maxlen) for s in numerical_arr]
    mask = [[1] * min(len(s), maxlen) + [0] * max(0, maxlen - len(s)) for s in numerical_arr]
    
    tokens = [t[:maxlen] for t in tokens]
    
    return padded_sens, np.array(padded_idf), lens, mask, tokens

moverscore_v2.collate_idf = collate_idf_fixed

# Correção no bert_encode para extrair hidden_states
def bert_encode_fixed(model, x, attention_mask):
    model.eval()
    dev = next(model.parameters()).device if hasattr(model, 'parameters') else 'cuda:0'
    
    x_tensor = torch.as_tensor(x, dtype=torch.long, device=dev)
    mask_tensor = torch.as_tensor(attention_mask, dtype=torch.long, device=dev)

    with torch.no_grad():
        outputs = model(x_tensor, attention_mask=mask_tensor, output_hidden_states=True)
        return outputs.hidden_states

moverscore_v2.bert_encode = bert_encode_fixed

nome_modelo = 'Gemma'
for nome_modelo in ['DeepSeek', 'Gemma', 'Llama', 'Qwen']:
    df = pd.read_csv(f'/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/Results/Eval_{nome_modelo}_Perguntas_Metagame.csv')

    referencias = df['resposta'].fillna('').astype(str).tolist()
    predicoes = df['resposta_gerada'].fillna('').astype(str).tolist()

    # BERTScore
    precisao, recall, f1 = bert_score(predicoes, referencias, lang="pt", verbose=False, batch_size=8)
    df['bertscore_precision'] = precisao.tolist()
    df['bertscore_recall'] = recall.tolist()
    df['bertscore_f1'] = f1.tolist()

    idf_ref = get_idf_dict(referencias)
    idf_pred = get_idf_dict(predicoes)

    # MoverScore
    notas_moverscore = word_mover_score(referencias, predicoes, idf_ref, idf_pred, stop_words=[], n_gram=1, remove_subwords=True)
    df['moverscore'] = notas_moverscore

    for indice, row in df.iterrows():
        referencia = row['resposta']
        predicao = row['resposta_gerada']

        # ROUGE
        notas_rouge = rouge.score(referencia, predicao)

        # BLEU
        nota_bleu = sacrebleu.sentence_bleu(predicao, [referencia]).score

        # METEOR
        #nota_meteor = meteor_score([referencia.split()], predicao.split())

        df.at[indice, 'rougeL'] = notas_rouge['rougeL'].fmeasure
        df.at[indice, 'rouge1'] = notas_rouge['rouge1'].fmeasure
        df.at[indice, 'rouge2'] = notas_rouge['rouge2'].fmeasure
        df.at[indice, 'bleu'] = nota_bleu
        #df.at[indice, 'meteor'] = nota_meteor
    df.to_csv(f'/mnt/di_ruralgpt/users/Edson/PokeAI/database/databases/P&R/Metagame/Automatic/Eval_Automatic_{nome_modelo}_Perguntas_Metagame.csv', index=False)