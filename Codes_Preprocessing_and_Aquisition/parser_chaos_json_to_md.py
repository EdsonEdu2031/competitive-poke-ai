import json
import os

def gerar_documentos_chaos_json(caminho_chaos_json, formato, pasta_saida="rag_dados_processados"):
    
    # Lê o arquivo chaos .json do Smogon e calcula as porcentagen ponderadas corretamente pelo total da própria categoria
    os.makedirs(pasta_saida, exist_ok=True)
    caminho_arquivo_rag = os.path.join(pasta_saida, f"pokemon_chaos_{formato}.md")

    try:
        with open(caminho_chaos_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho_chaos_json}.")
        return
    except Exception as e:
        print(f"Erro ao ler o JSON: {e}")
        return

    pokemon_dict = dados.get("data", {})

    with open(caminho_arquivo_rag, 'w', encoding='utf-8') as f_out:
        f_out.write("# Detailed Knowledge Base: Regulation M-B, VGC 2026 (Rank 1760) – Metagame and Synergies\n\n")

        for pokemon, stats in pokemon_dict.items():
            
            # Abilities (Ponderado pela soma das habilidades)
            abilities_dict = {k: v for k, v in stats.get("Abilities", {}).items() if k != "Nothing"}
            total_abilities = sum(abilities_dict.values()) or 1
            abilities = sorted(abilities_dict.items(), key=lambda x: x[1], reverse=True)
            abilities_str = ", ".join([f"{k} ({(v / total_abilities) * 100:.2f}%)" for k, v in abilities])
            if not abilities_str:
                abilities_str = "Nenhuma habilidade registrada"

            # Items (Ponderado pela soma dos itens registrados)
            items_dict = {k: v for k, v in stats.get("Items", {}).items() if k != "Nothing"}
            total_items = sum(items_dict.values()) or 1
            itens = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)[:4]
            itens_str = ", ".join([f"{k} ({(v / total_items) * 100:.2f}%)" for k, v in itens])
            if not itens_str: 
                itens_str = "Nenhum item de destaque"

            # Moves (Ponderado pelo total de batalhas/items para manter escala correta de moveset)
            moves_dict = {k: v for k, v in stats.get("Moves", {}).items() if k != "Nothing"}
            
            # Um pokémon carrega até 4 moves por batalha, então a soma total de contagens de moves / 4 dá o total de batalhas com moveset
            total_battles_moves = (sum(moves_dict.values()) / 4.0) or 1.0
            moves = sorted(moves_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            moves_str = ", ".join([f"{k} ({(v / total_battles_moves) * 100:.2f}%)" for k, v in moves])
            if not moves_str:
                moves_str = "Nenhum move de destaque"

            # Teammates (Ponderado pelo total de inserções de parceiros)
            teammates_dict = stats.get("Teammates", {})
            total_teammates_battles = total_items  # O total de partidas do pokémon é igual ao total de itens usados
            teammates = sorted(teammates_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            teammates_str = ", ".join([f"{k} ({(v / total_teammates_battles) * 100:.2f}%)" for k, v in teammates])
            if not teammates_str:
                teammates_str = "Nenhum parceiro dominante registrado"

            # Spreads (EVs e Natures)
            spreads_dict = stats.get("Spreads", {})
            total_spreads = sum(spreads_dict.values()) or 1
            spreads = sorted(spreads_dict.items(), key=lambda x: x[1], reverse=True)[:2]
            spreads_str = " e ".join([f"{k} ({(v / total_spreads) * 100:.2f}%)" for k, v in spreads])
            if not spreads_str:
                spreads_str = "Padrões variados"

            # Escrevendo o bloco descritivo
            f_out.write(f"# Comprehensive Competitive Profile: {pokemon}\n")
            f_out.write(f"- **Most frequently used abilities:** {abilities_str}.\n")
            f_out.write(f"- **Most frequently used items:** {itens_str}.\n")
            f_out.write(f"- **Main moveset:** {moves_str}.\n")
            f_out.write(f"- **EV and Nature Distribution (Spreads):** {spreads_str}.\n")
            f_out.write(f"- **Teambuilding Synergy (Common Partners):** {teammates_str}.\n")
            f_out.write("=" * 60 + "\n\n")

    print(f"Arquivo de contexto Chaos processado com sucesso em: {caminho_arquivo_rag}")

if __name__ == '__main__':
    print("Processando arquivo Chaos JSON (linha única) do Smogon...\n")

    arquivo_chaos = "/home/yan/Documents/GitHub/competitive-poke-ai123/databases/smogon_metagame_data/chaos_gen9championsvgc2026regmb-1760.json"
    gerar_documentos_chaos_json(arquivo_chaos, "regmb")

