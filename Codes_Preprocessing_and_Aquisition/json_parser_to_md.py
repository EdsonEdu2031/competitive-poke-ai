import json
from pathlib import Path

def convert_pokemons(data):
    paragraphs = []
    for p in data:
        types_str = " e ".join(p.get("types", []))
        stats = p.get("stats", {})
        hp, atk, dfe = stats.get("hp", 0), stats.get("atk", 0), stats.get("def", 0)
        spa, spd, spe = stats.get("spa", 0), stats.get("spd", 0), stats.get("spe", 0)
        bst = hp + atk + dfe + spa + spd + spe
        abilities_str = ", ".join(p.get("abilities", []))
        name = p.get("name")
        p_id = p.get("id", "N/A")

        text = (
            f"O Pokémon {name} (#{p_id}) é uma criatura do(s) tipo(s) {types_str}. "
            f"Suas estatísticas base são {hp} de HP, {atk} de Ataque, {dfe} de Defesa, "
            f"{spa} de Ataque Especial, {spd} de Defesa Especial e {spe} de Velocidade, "
            f"totalizando um BST de {bst}. As habilidades de {name} são: {abilities_str}."
        )
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

def convert_moves(data):
    paragraphs = []
    for m in data:
        name = m.get("name")
        cat = m.get("category", "")
        m_type = m.get("type", "")
        power = m.get("power", "N/A")
        acc = m.get("accuracy", "N/A")
        pp = m.get("pp", "N/A")
        effect = m.get("effect", "")

        text = (
            f"O golpe {name} é um movimento da categoria {cat} do tipo {m_type} "
            f"com {power} de poder base, {acc}% de precisão e {pp} PP. {effect}"
        )
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

def convert_abilities(data):
    paragraphs = []
    for a in data:
        name = a.get("name")
        desc = a.get("description", "")
        text = f"A habilidade {name} possui o seguinte efeito em batalha: {desc}"
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

def convert_items(data):
    paragraphs = []
    for i in data:
        name = i.get("name")
        desc = i.get("description", "")
        text = f"O item {name} é um item segurável que possui o seguinte efeito: {desc}"
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

def convert_natures(data):
    paragraphs = []
    for n in data:
        name = n.get("name")
        inc = n.get("increased_stat", "")
        dec = n.get("decreased_stat", "")
        if inc and dec:
            text = (
                f"A natureza {name} aumenta em 10% o status de {inc} "
                f"e reduz em 10% o status de {dec} do Pokémon."
            )
        else:
            text = f"A natureza {name} é neutra e não altera nenhum status do Pokémon."
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

def convert_types(data):
    paragraphs = []
    for t in data:
        name = t.get("name")
        super_eff = ", ".join(t.get("super_effective", []))
        resist = ", ".join(t.get("resisted", []))
        text = (
            f"O tipo {name} causa dano super efetivo (2x) contra os tipos {super_eff}. "
            f"Defensivamente, o tipo {name} possui resistência (0.5x) contra ataques dos tipos {resist}."
        )
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

def convert_type_mechanics(data):
    paragraphs = []
    for tm in data:
        title = tm.get("title", "")
        desc = tm.get("description", "")
        text = f"A mecânica de tipo referente a {title} funciona da seguinte forma: {desc}"
        paragraphs.append(text)
    return "\n\n".join(paragraphs)

file_mappings = {
    "79_pokemon_pokedex.json": ("79_pokemon_pokedex.md", convert_pokemons),
    "35_pokemon_moves.json": ("35_pokemon_moves.md", convert_moves),
    "31_pokemon_abilities.json": ("31_pokemon_abilities.md", convert_abilities),
    "73_pokemon_items.json": ("73_pokemon_items.md", convert_items),
    "22_pokemon_natures.json": ("22_pokemon_natures.md", convert_natures),
    "47_pokemon_types.json": ("47_pokemon_types.md", convert_types),
    "56_pokemon_type_stats.json": ("56_pokemon_type_stats.md", convert_type_mechanics),
}

def process_all():
    base_path = Path("/home/yan/Documents/GitHub/competitive-poke-ai123/documents")
    for json_name, (md_name, converter) in file_mappings.items():
        json_file = base_path / json_name
        if json_file.exists():
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            output_text = converter(data)
            with open(base_path / md_name, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"Gerado com sucesso: {md_name}")

if __name__ == "__main__":
    process_all()
    