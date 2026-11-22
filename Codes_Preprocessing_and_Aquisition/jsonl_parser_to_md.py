import json

def text_moveset(data: dict) -> str:
    pkm = data.get("pokemon", "Desconhecido")
    d = data.get("data", {})
    stats = d.get("stats", {})
    
    # Formatação de listas
    abilities_str = ", ".join([f"{a['name']} ({a['percentage']:.3f}%)" for a in d.get("abilities", {}).get("entries", [])])
    items_str = ", ".join([f"{i['name']} ({i['percentage']:.3f}%)" for i in d.get("items", {}).get("entries", [])])
    moves_str = ", ".join([f"{m['name']} ({m['percentage']:.3f}%)" for m in d.get("moves", {}).get("entries", [])])
    spreads_str = ", ".join([f"{s['name']} ({s['percentage']:.3f}%)" for s in d.get("spreads", {}).get("entries", [])])
    team_str = ", ".join([f"{t['name']} ({t['percentage']:.3f}%)" for t in d.get("teammates", {}).get("entries", [])])

    text = (
        f"No metagame competitivo de Pokémon, a análise detalhada do Pokémon {pkm} é baseada em uma amostra de "
        f"{stats.get('raw_count', 0):,} batalhas (raw count), apresentando um peso médio de partida (avg weight) de "
        f"{stats.get('avg_weight', 0):.4f} e um teto de viabilidade (viability ceiling) de {stats.get('viability_ceiling', 0)}. "
        f"Em relação às suas habilidades (abilities), as opções registradas são: {abilities_str}. "
        f"Quanto aos itens segurados (held items) mais populares para {pkm}, destacam-se: {items_str}. "
        f"No seu repertório de movimentos e golpes (moveset), {pkm} utiliza: {moves_str}. "
        f"Em relação à distribuição de EVs e Natures (spreads), as configurações registradas são: {spreads_str}. "
        f"Em termos de sinergia de equipe e parceiros de time (teammates), {pkm} é frequentemente utilizado ao lado de: {team_str}."
    )
    return f"# Pokémon: {pkm} - Moveset e Sinergia\n{text}\n\n"

def text_usage(data: dict) -> str:
    pkm = data.get("pokemon", "Desconhecido")
    text = (
        f"No ranking geral de utilização do metagame competitivo de Pokémon, o Pokémon {pkm} ocupa a "
        f"{data.get('rank', 0)}ª posição (Rank {data.get('rank', 0)}). Ele registra uma taxa de uso ponderada (usage percent) de "
        f"{data.get('usage_percent', 0):.5f}% em um universo de {data.get('total_battles', 0):,} batalhas analisadas. "
        f"Em números brutos de aparições (raw count), {pkm} esteve presente em {data.get('raw', 0):,} batalhas, o que equivale "
        f"a uma porcentagem bruta de presença de {data.get('raw_percent', 0):.3f}%. Ao ajustar pelas batalhas de alto nível (real count), "
        f"ele contabilizou {data.get('real', 0):,} aparições, representando uma porcentagem real de {data.get('real_percent', 0):.3f}%. "
        f"O peso médio das equipes que contêm este Pokémon (avg weight team) é de {data.get('avg_weight_team', 0)}."
    )
    return f"# Pokémon: {pkm} - Ranking Geral\n{text}\n\n"

def text_lead(data: dict) -> str:
    pkm = data.get("pokemon", "Desconhecido")
    text = (
        f"No ranking de escolhas para a abertura de batalha (primeiro turno / lead usage), o Pokémon {pkm} ocupa a "
        f"{data.get('rank', 0)}ª posição (Lead Rank {data.get('rank', 0)}). Ele possui uma taxa de utilização como lead "
        f"(usage percent) de {data.get('usage_percent', 0):.5f}% considerando um total de {data.get('total_leads', 0):,} batalhas "
        f"com dados de abertura analisados. Em termos de contagem bruta como lead (raw count), {pkm} foi enviado como primeiro "
        f"Pokémon em campo em {data.get('raw', 0):,} partidas, o que representa uma porcentagem de {data.get('percentage', 0):.3f}% "
        f"sobre o total de aberturas registradas no metagame."
    )
    return f"# Pokémon: {pkm} - Ranking de Lead\n{text}\n\n"

def process_file(input_file: str, output_file: str, file_type: int):
    formatters = {1: text_moveset, 2: text_usage, 3: text_lead}
    formatter = formatters[file_type]

    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
        for line in infile:
            if not line.strip():
                continue
            item = json.loads(line)
            outfile.write(formatter(item))


process_file("/home/yan/Documents/GitHub/competitive-poke-ai123/documents/54_pokemon_moveset_regmb.jsonl", "54_pokemon_moveset_regmb.md", 1)
process_file("/home/yan/Documents/GitHub/competitive-poke-ai123/documents/70_pokemon_geral_regmb.jsonl", "70_pokemon_geral_regmb.md", 2)
process_file("/home/yan/Documents/GitHub/competitive-poke-ai123/documents/49_pokemon_lead_regmb.jsonl", "49_pokemon_lead_regmb.md", 3)

process_file("/home/yan/Documents/GitHub/competitive-poke-ai123/documents/74_pokemon_moveset_regmb_bo3.jsonl", "74_pokemon_moveset_regmb_bo3.md", 1)
process_file("/home/yan/Documents/GitHub/competitive-poke-ai123/documents/18_pokemon_geral_regmb_b03.jsonl", "18_pokemon_geral_regmb_b03.md", 2)
process_file("/home/yan/Documents/GitHub/competitive-poke-ai123/documents/55_pokemon_lead_regmb_bo3.jsonl", "55_pokemon_lead_regmb_bo3.md", 3)