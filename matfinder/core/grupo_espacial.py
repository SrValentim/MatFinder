# grupo_espacial.py
# Este módulo armazena informações sobre grupos espaciais e seus sistemas cristalinos.

# NOTA: Esta lista é um subconjunto representativo e não contém todos os 230 grupos espaciais.
# A numeração e os detalhes completos devem ser verificados com as Tabelas Internacionais de Cristalografia.
# Símbolos com "₁", "₂", "₃", "₄" são representados com "_" (ex: P2_1/c) para facilidade de uso em código.

LISTA_GRUPOS_ESPACIAIS = [
    # --- Triclínico ---
    {"numero": 1, "simbolo_hm": "P1", "simbolos_alternativos": [], "sistema_cristalino": "Triclínico", "ponto_grupo": "1", "descricao_adicional": "Sem simetria adicional além da translação."},
    {"numero": 2, "simbolo_hm": "P-1", "simbolos_alternativos": ["Pī"], "sistema_cristalino": "Triclínico", "ponto_grupo": "-1 (ī)", "descricao_adicional": "Com centro de inversão."},

    # --- Monoclínico ---
    # (O PDF lista 13 grupos monoclínicos. Aqui estão alguns exemplos)
    {"numero": 3, "simbolo_hm": "P2", "simbolos_alternativos": [], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2", "descricao_adicional": "Eixo binário único."},
    {"numero": 4, "simbolo_hm": "P2_1", "simbolos_alternativos": ["P21"], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2", "descricao_adicional": "Eixo helicoidal binário."},
    {"numero": 5, "simbolo_hm": "C2", "simbolos_alternativos": [], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2", "descricao_adicional": "Centrado na face C, eixo binário."},
    {"numero": 10, "simbolo_hm": "P2/m", "simbolos_alternativos": [], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2/m", "descricao_adicional": "Eixo binário perpendicular a um plano de espelho."},
    {"numero": 11, "simbolo_hm": "P2_1/m", "simbolos_alternativos": ["P21/m"], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2/m", "descricao_adicional": "Eixo helicoidal binário perpendicular a um plano de espelho."},
    {"numero": 12, "simbolo_hm": "C2/m", "simbolos_alternativos": [], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2/m", "descricao_adicional": "Centrado C, eixo binário perpendicular a plano de espelho."},
    {"numero": 13, "simbolo_hm": "P2/c", "simbolos_alternativos": [], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2/m", "descricao_adicional": "Eixo binário perpendicular a plano de deslizamento c."},
    {"numero": 14, "simbolo_hm": "P2_1/c", "simbolos_alternativos": ["P21/c"], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2/m", "descricao_adicional": "Muito comum; eixo helicoidal binário perpendicular a plano de deslizamento c."},
    {"numero": 15, "simbolo_hm": "C2/c", "simbolos_alternativos": [], "sistema_cristalino": "Monoclínico", "ponto_grupo": "2/m", "descricao_adicional": "Centrado C, eixo binário perpendicular a plano de deslizamento c."},

    # --- Ortorrômbico ---
    # (O PDF lista 59 grupos ortorrômbicos. Aqui estão alguns exemplos)
    {"numero": 16, "simbolo_hm": "P222", "simbolos_alternativos": [], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "222", "descricao_adicional": "Três eixos binários perpendiculares."},
    {"numero": 17, "simbolo_hm": "P222_1", "simbolos_alternativos": ["P2221"], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "222", "descricao_adicional": ""},
    {"numero": 18, "simbolo_hm": "P2_12_12", "simbolos_alternativos": ["P21212"], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "222", "descricao_adicional": ""},
    {"numero": 19, "simbolo_hm": "P2_12_12_1", "simbolos_alternativos": ["P212121"], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "222", "descricao_adicional": "Comum para moléculas quirais."},
    {"numero": 25, "simbolo_hm": "Pmm2", "simbolos_alternativos": [], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "mm2", "descricao_adicional": "Polar."},
    {"numero": 36, "simbolo_hm": "Cmc2_1", "simbolos_alternativos": ["Cmc21"], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "mm2", "descricao_adicional": "Comum em materiais ferroelétricos."},
    {"numero": 47, "simbolo_hm": "Pmmm", "simbolos_alternativos": [], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "mmm", "descricao_adicional": "Centrossimétrico."},
    {"numero": 62, "simbolo_hm": "Pnma", "simbolos_alternativos": [], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "mmm", "descricao_adicional": "Muito comum, estrutura da perovskita distorcida (ex: GdFeO₃)."},
    {"numero": 71, "simbolo_hm": "Immm", "simbolos_alternativos": [], "sistema_cristalino": "Ortorrômbico", "ponto_grupo": "mmm", "descricao_adicional": "De corpo centrado."},

    # --- Tetragonal ---
    # (O PDF lista 68 grupos. Exemplos:)
    {"numero": 75, "simbolo_hm": "P4", "simbolos_alternativos": [], "sistema_cristalino": "Tetragonal", "ponto_grupo": "4", "descricao_adicional": ""},
    {"numero": 76, "simbolo_hm": "P4_1", "simbolos_alternativos": ["P41"], "sistema_cristalino": "Tetragonal", "ponto_grupo": "4", "descricao_adicional": ""},
    {"numero": 83, "simbolo_hm": "P4/m", "simbolos_alternativos": [], "sistema_cristalino": "Tetragonal", "ponto_grupo": "4/m", "descricao_adicional": ""},
    {"numero": 123, "simbolo_hm": "P4/mmm", "simbolos_alternativos": [], "sistema_cristalino": "Tetragonal", "ponto_grupo": "4/mmm", "descricao_adicional": "Célula tetragonal primitiva simples."},
    {"numero": 139, "simbolo_hm": "I4/mmm", "simbolos_alternativos": [], "sistema_cristalino": "Tetragonal", "ponto_grupo": "4/mmm", "descricao_adicional": "De corpo centrado, comum em supercondutores."},
    {"numero": 141, "simbolo_hm": "I4_1/amd", "simbolos_alternativos": ["I41/amd"], "sistema_cristalino": "Tetragonal", "ponto_grupo": "4/mmm", "descricao_adicional": "Estrutura da anatásio (TiO₂)."},


    # --- Trigonal ---
    # (O PDF lista 25 grupos. Exemplos:)
    {"numero": 143, "simbolo_hm": "P3", "simbolos_alternativos": [], "sistema_cristalino": "Trigonal", "ponto_grupo": "3", "descricao_adicional": ""},
    {"numero": 147, "simbolo_hm": "P-3", "simbolos_alternativos": ["P3bar"], "sistema_cristalino": "Trigonal", "ponto_grupo": "-3", "descricao_adicional": ""},
    {"numero": 160, "simbolo_hm": "R3m", "simbolos_alternativos": [], "sistema_cristalino": "Trigonal", "ponto_grupo": "3m", "descricao_adicional": "Configuração romboédrica ou hexagonal (ex: BiFeO₃)."},
    {"numero": 166, "simbolo_hm": "R-3m", "simbolos_alternativos": ["R3barm"], "sistema_cristalino": "Trigonal", "ponto_grupo": "-3m", "descricao_adicional": "Configuração romboédrica ou hexagonal (ex: α-Al₂O₃ - Coríndon)."},

    # --- Hexagonal ---
    # (O PDF lista 27 grupos. Exemplos:)
    {"numero": 168, "simbolo_hm": "P6", "simbolos_alternativos": [], "sistema_cristalino": "Hexagonal", "ponto_grupo": "6", "descricao_adicional": ""},
    {"numero": 177, "simbolo_hm": "P6/m", "simbolos_alternativos": [], "sistema_cristalino": "Hexagonal", "ponto_grupo": "6/m", "descricao_adicional": ""},
    {"numero": 191, "simbolo_hm": "P6/mmm", "simbolos_alternativos": [], "sistema_cristalino": "Hexagonal", "ponto_grupo": "6/mmm", "descricao_adicional": ""},
    {"numero": 194, "simbolo_hm": "P6_3/mmc", "simbolos_alternativos": ["P63/mmc"], "sistema_cristalino": "Hexagonal", "ponto_grupo": "6/mmm", "descricao_adicional": "Grafite, Wurtzita (ZnS), Mg."},

    # --- Cúbico ---
    # (O PDF lista 36 grupos. Exemplos:)
    {"numero": 195, "simbolo_hm": "P23", "simbolos_alternativos": [], "sistema_cristalino": "Cúbico", "ponto_grupo": "23", "descricao_adicional": ""},
    {"numero": 200, "simbolo_hm": "Pm-3", "simbolos_alternativos": ["Pm3"], "sistema_cristalino": "Cúbico", "ponto_grupo": "m-3", "descricao_adicional": ""}, # Pm₃
    {"numero": 207, "simbolo_hm": "P432", "simbolos_alternativos": [], "sistema_cristalino": "Cúbico", "ponto_grupo": "432", "descricao_adicional": ""},
    {"numero": 221, "simbolo_hm": "Pm-3m", "simbolos_alternativos": ["Pm3m"], "sistema_cristalino": "Cúbico", "ponto_grupo": "m-3m", "descricao_adicional": "Perovskita cúbica ideal (ex: SrTiO₃)."}, # Pm₃m
    {"numero": 225, "simbolo_hm": "Fm-3m", "simbolos_alternativos": ["Fm3m"], "sistema_cristalino": "Cúbico", "ponto_grupo": "m-3m", "descricao_adicional": "Estrutura do sal de rocha (NaCl), blenda de zinco (ZnS)."}, # Fm₃m
    {"numero": 227, "simbolo_hm": "Fd-3m", "simbolos_alternativos": ["Fd3m"], "sistema_cristalino": "Cúbico", "ponto_grupo": "m-3m", "descricao_adicional": "Estrutura do diamante, espinélio (MgAl₂O₄)."}, # Fd₃m
    {"numero": 230, "simbolo_hm": "Ia-3d", "simbolos_alternativos": ["Ia3d"], "sistema_cristalino": "Cúbico", "ponto_grupo": "m-3m", "descricao_adicional": "Estrutura da granada (ex: Y₃Al₅O₁₂)."}, # Ia₃d
]

def obter_info_grupo_espacial(identificador):
    """
    Busca informações de um grupo espacial pelo seu símbolo Hermann-Mauguin ou número.

    Args:
        identificador (str ou int): O símbolo HM (ex: "Pnma", "P2_1/c") ou o número internacional.

    Returns:
        dict: Um dicionário com as informações do grupo espacial encontrado,
              ou None se não for encontrado.
              O dicionário contém: 'numero', 'simbolo_hm', 'simbolos_alternativos',
                                   'sistema_cristalino', 'ponto_grupo', 'descricao_adicional'.
    """
    if isinstance(identificador, str):
        identificador_lower = identificador.lower()
        # Normalizar traços e barras para consistência na busca, se necessário
        # (ex: "R-3m" vs "R 3m", "P6_3/mmc" vs "P63/mmc")
        # Para esta implementação, a busca será literal nos símbolos principais e alternativos.
        for grupo in LISTA_GRUPOS_ESPACIAIS:
            if grupo["simbolo_hm"].lower() == identificador_lower:
                return grupo
            for alt_simbolo in grupo.get("simbolos_alternativos", []):
                if alt_simbolo.lower() == identificador_lower:
                    return grupo
    elif isinstance(identificador, int):
        for grupo in LISTA_GRUPOS_ESPACIAIS:
            if grupo["numero"] == identificador:
                return grupo
    return None

if __name__ == '__main__':
    # Exemplos de uso:
    print("--- Testando obter_info_grupo_espacial ---")

    simbolos_para_testar = ["Pnma", "P2_1/c", "P21/c", "Fm-3m", "P6_3/mmc", "P1", "R-3m", "NaoExiste"]
    numeros_para_testar = [1, 14, 62, 225, 230, 999]

    for s in simbolos_para_testar:
        info = obter_info_grupo_espacial(s)
        if info:
            print(f"Info para '{s}': Número {info['numero']}, Sistema: {info['sistema_cristalino']}, Ponto: {info.get('ponto_grupo', 'N/A')}, Desc: {info.get('descricao_adicional', 'N/A')}")
        else:
            print(f"Nenhuma informação encontrada para o símbolo: '{s}'")

    print("\n")
    for n in numeros_para_testar:
        info = obter_info_grupo_espacial(n)
        if info:
            print(f"Info para número {n}: Símbolo {info['simbolo_hm']}, Sistema: {info['sistema_cristalino']}, Ponto: {info.get('ponto_grupo', 'N/A')}, Desc: {info.get('descricao_adicional', 'N/A')}")
        else:
            print(f"Nenhuma informação encontrada para o número: {n}")

    # Teste específico para Pnma
    info_pnma = obter_info_grupo_espacial("Pnma")
    if info_pnma:
        print(f"\nTeste Pnma: {info_pnma}")

    info_ia3d = obter_info_grupo_espacial("Ia-3d")
    if info_ia3d:
        print(f"\nTeste Ia-3d: {info_ia3d}")
