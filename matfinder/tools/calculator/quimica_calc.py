from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import Element
import traceback
import re
from matfinder.core.translator import ptr

try:
    from chempy import balance_stoichiometry

    CHEMPY_AVAILABLE = True
except ImportError:
    CHEMPY_AVAILABLE = False
    print("AVISO: Biblioteca 'chempy' não encontrada. O balanceamento de equações não funcionará.")
    print("Para instalar, execute: pip install chempy sympy")

# --- CONSTANTES ---
NUMERO_DE_AVOGADRO = 6.022e23


# --- FUNÇÕES DA ETAPA 1 (Parse de Fórmula e Massa Molar) ---
def parse_formula(formula_str: str) -> dict:
    """
    Converte uma string de fórmula química num dicionário de contagem de elementos.
    Ex: "H2SO4" -> {'H': 2.0, 'S': 1.0, 'O': 4.0}
    Retorna um dicionário vazio se o parse falhar.
    """
    try:
        composicao = Composition(formula_str)
        element_counts = {}
        # Iterar diretamente sobre o objeto Composition.
        # Cada 'element_object' será um objeto Element.
        for element_object in composicao:
            # composicao.get_atomic_fraction(element_object) * composicao.num_atoms
            # dá a quantidade total de átomos daquele elemento na fórmula.
            amount = composicao.get_atomic_fraction(element_object) * composicao.num_atoms
            element_counts[element_object.symbol] = amount
            # print(f"Parse da fórmula '{formula_str}': {element_counts}") # Descomentar para depuração
        return element_counts
    except ValueError as ve:
        # Pymatgen levanta ValueError para fórmulas que não consegue interpretar
        print(f"Erro de VALOR ao fazer o parse da fórmula '{formula_str}': {ve}")
        return {}
    except Exception as e:
        print(f"Erro INESPERADO ao fazer o parse da fórmula '{formula_str}': {e}")
        traceback.print_exc()
        return {}


def calcular_massa_molar(parsed_formula_ou_str) -> float:
    """
    Calcula a massa molar de um composto.
    Pode receber um dicionário de contagem de elementos (resultado de parse_formula)
    ou diretamente uma string de fórmula.
    Retorna a massa molar em g/mol, ou 0.0 se houver erro.
    """
    parsed_formula = {}
    if isinstance(parsed_formula_ou_str, str):
        # Chama a parse_formula corrigida
        parsed_formula = parse_formula(parsed_formula_ou_str)
    elif isinstance(parsed_formula_ou_str, dict):
        parsed_formula = parsed_formula_ou_str
    else:
        print("Entrada inválida para calcular_massa_molar.")
        return 0.0

    if not parsed_formula:
        # A mensagem de erro já terá sido impressa por parse_formula se falhou lá
        return 0.0

    massa_molar_total = 0.0
    for elemento_simbolo, quantidade in parsed_formula.items():
        try:
            elemento_obj = Element(elemento_simbolo)
            massa_atomica = elemento_obj.atomic_mass
            massa_molar_total += massa_atomica * quantidade
        except Exception as e:
            print(f"Erro ao obter massa atômica para o elemento '{elemento_simbolo}': {e}")
            return 0.0
    # print(f"Cálculo da massa molar para {parsed_formula}: {massa_molar_total:.4f} g/mol")
    return round(massa_molar_total, 4)


# --- FUNÇÕES DA ETAPA 2 (Parse de Equação e Balanceamento) ---
def parse_equation_string(equation_str: str) -> tuple[list[str], list[str]] | None:
    separators = ['->', '=>', '=']
    reactants_str, products_str = None, None
    for sep in separators:
        if sep in equation_str:
            parts = equation_str.split(sep)
            if len(parts) == 2:
                reactants_str, products_str = parts[0], parts[1]
                break
    if reactants_str is None or products_str is None:
        print(
            f"Erro: Formato de equação inválido ou separador não reconhecido em '{equation_str}'. Use '->', '=>' ou '='.")
        return None
    reactant_formulas = [formula.strip() for formula in reactants_str.split('+') if formula.strip()]
    product_formulas = [formula.strip() for formula in products_str.split('+') if formula.strip()]
    if not reactant_formulas or not product_formulas:
        print(f"Erro: Reagentes ou produtos em falta na equação '{equation_str}'.")
        return None
    # print(f"Parse da equação '{equation_str}': Reagentes={reactant_formulas}, Produtos={product_formulas}")
    return reactant_formulas, product_formulas


def balance_chemical_equation(reactant_formulas: list[str], product_formulas: list[str]) -> tuple[dict, dict] | None:
    if not CHEMPY_AVAILABLE:
        print("Balanceamento não pode ser realizado: chempy não disponível.")
        return None
    if not reactant_formulas or not product_formulas:
        print("Erro: Listas de reagentes e produtos vazias para balanceamento.")
        return None
    try:
        reac_set = set(reactant_formulas)
        prod_set = set(product_formulas)
        balanced_reac_coeffs, balanced_prod_coeffs = balance_stoichiometry(reac_set, prod_set)
        # print(f"Equação balanceada (bruto): Reagentes={balanced_reac_coeffs}, Produtos={balanced_prod_coeffs}")
        return balanced_reac_coeffs, balanced_prod_coeffs
    except Exception as e:
        print(f"Erro ao tentar balancear a equação com chempy: {e}")
        # traceback.print_exc() # Descomentar para ver o erro completo do Chempy se necessário
        return None


def format_balanced_equation(reactant_formulas: list[str], product_formulas: list[str],
                             balanced_reac_coeffs: dict, balanced_prod_coeffs: dict) -> str:
    if not balanced_reac_coeffs or not balanced_prod_coeffs:
        return ptr("Não foi possível formatar a equação (coeficientes em falta).")

    def format_side(formulas_ordered, coeffs_dict):
        terms = []
        for formula in formulas_ordered:
            coeff = coeffs_dict.get(formula, 0)
            if coeff == 1:
                terms.append(formula)
            elif coeff > 0:
                terms.append(f"{int(coeff)}{formula}")
        return " + ".join(terms)

    reac_str = format_side(reactant_formulas, balanced_reac_coeffs)
    prod_str = format_side(product_formulas, balanced_prod_coeffs)
    return f"{reac_str} -> {prod_str}"


# --- FUNÇÕES DA ETAPA 3 (Conversões) ---
def massa_para_moles(massa_gramas: float, formula_str_ou_massa_molar) -> float | None:
    massa_molar = 0.0
    if isinstance(formula_str_ou_massa_molar, (float, int)):
        massa_molar = float(formula_str_ou_massa_molar)
    elif isinstance(formula_str_ou_massa_molar, str):
        massa_molar = calcular_massa_molar(formula_str_ou_massa_molar)
    else:
        print("Erro em massa_para_moles: 'formula_str_ou_massa_molar' deve ser string ou float/int.")
        return None
    if massa_molar == 0.0:
        # A mensagem de erro já terá sido impressa por calcular_massa_molar se a fórmula for inválida
        return None
    return round(massa_gramas / massa_molar, 6)


def moles_para_massa(moles: float, formula_str_ou_massa_molar) -> float | None:
    massa_molar = 0.0
    if isinstance(formula_str_ou_massa_molar, (float, int)):
        massa_molar = float(formula_str_ou_massa_molar)
    elif isinstance(formula_str_ou_massa_molar, str):
        massa_molar = calcular_massa_molar(formula_str_ou_massa_molar)
    else:
        print("Erro em moles_para_massa: 'formula_str_ou_massa_molar' deve ser string ou float/int.")
        return None
    if massa_molar == 0.0: return None
    return round(moles * massa_molar, 4)


def moles_para_particulas(moles: float) -> float:
    return moles * NUMERO_DE_AVOGADRO


def particulas_para_moles(numero_particulas: float) -> float:
    return numero_particulas / NUMERO_DE_AVOGADRO


def calcular_quantidade_equivalente(
        formula_conhecida: str,
        quantidade_conhecida_moles: float,
        formula_desejada: str,
        equacao_balanceada: tuple[dict, dict]  # (reac_coeffs, prod_coeffs)
) -> float | None:
    reac_coeffs, prod_coeffs = equacao_balanceada
    coef_conhecido = reac_coeffs.get(formula_conhecida) or prod_coeffs.get(formula_conhecida)
    coef_desejado = reac_coeffs.get(formula_desejada) or prod_coeffs.get(formula_desejada)
    if coef_conhecido is None: print(f"Erro: Fórmula '{formula_conhecida}' não encontrada na equação."); return None
    if coef_desejado is None: print(f"Erro: Fórmula '{formula_desejada}' não encontrada na equação."); return None
    if coef_conhecido == 0: print(f"Erro: Coeficiente de '{formula_conhecida}' é zero."); return None
    moles_desejados = (quantidade_conhecida_moles * coef_desejado) / coef_conhecido
    return round(moles_desejados, 6)


# --- FUNÇÕES DA ETAPA 4 e 5 (Reagente Limitante, Rendimento Teórico, Percentagem Rendimento) ---
def identificar_reagente_limitante(
        reagentes_quantidades_moles: dict,
        reac_coeffs_balanceados: dict
) -> str | None:
    if not reagentes_quantidades_moles: print("Erro: Dicionário de quantidades de reagentes está vazio."); return None
    if not reac_coeffs_balanceados: print(
        "Erro: Dicionário de coeficientes de reagentes balanceados está vazio."); return None
    min_proporcao = float('inf')
    reagente_limitante = None

    # print("\nCalculando reagente limitante:") # Descomentar para depuração detalhada
    for formula_reagente, moles_disponiveis in reagentes_quantidades_moles.items():
        coef_estequiometrico = reac_coeffs_balanceados.get(formula_reagente)
        if coef_estequiometrico is None:
            print(f"Aviso: Reagente '{formula_reagente}' não encontrado nos coeficientes. Será ignorado.");
            continue
        if coef_estequiometrico == 0:
            print(f"Aviso: Coeficiente para '{formula_reagente}' é zero. Será ignorado.");
            continue
        if moles_disponiveis < 0: print(f"Erro: Moles de '{formula_reagente}' não pode ser negativo."); return None
        proporcao = moles_disponiveis / coef_estequiometrico
        # print(f"  Reagente: {formula_reagente}, Moles: {moles_disponiveis}, Coef: {coef_estequiometrico}, Proporção: {proporcao:.4f}")
        if proporcao < min_proporcao:
            min_proporcao = proporcao
            reagente_limitante = formula_reagente

    if reagente_limitante is None and reagentes_quantidades_moles:
        # Se nenhum reagente válido foi encontrado (ex: todos não estavam na equação)
        print("Não foi possível determinar o reagente limitante com os reagentes válidos fornecidos.")
    return reagente_limitante


def calcular_rendimento_teorico(
        formula_produto_desejado: str,
        reagente_limitante_formula: str,
        quantidade_reagente_limitante_moles: float,
        equacao_balanceada: tuple[dict, dict]
) -> float | None:
    """Calcula o rendimento teórico de um produto em MOLES."""
    if not reagente_limitante_formula:
        print("Erro: Reagente limitante não fornecido para calcular rendimento teórico.")
        return None
    if quantidade_reagente_limitante_moles < 0:
        print("Erro: Quantidade do reagente limitante não pode ser negativa.")
        return None

    moles_produto_teorico = calcular_quantidade_equivalente(
        formula_conhecida=reagente_limitante_formula,
        quantidade_conhecida_moles=quantidade_reagente_limitante_moles,
        formula_desejada=formula_produto_desejado,
        equacao_balanceada=equacao_balanceada
    )
    return moles_produto_teorico


def calcular_percentagem_rendimento(rendimento_real: float, rendimento_teorico: float) -> float | None:
    """
    Calcula a percentagem de rendimento.
    Ambos os rendimentos devem estar na mesma unidade (ex: moles ou gramas).
    """
    if rendimento_teorico is None or rendimento_teorico <= 1e-9:  # Evita divisão por zero ou por valores muito pequenos
        print("Erro: Rendimento teórico é zero ou muito pequeno para calcular a percentagem.")
        return None
    if rendimento_real < 0:
        print("Erro: Rendimento real não pode ser negativo.")
        return None

    percentagem = (rendimento_real / rendimento_teorico) * 100
    return round(percentagem, 2)


# --- Bloco de Teste Atualizado ---
if __name__ == "__main__":
    print("--- Testando Funções da Calculadora Química (Todas Etapas) ---")

    # Dicionário para guardar massas molares calculadas para usar nos testes
    massas_molares_calculadas_dict = {}

    test_formulas_para_mm = ["H2O", "CO2", "CH4", "O2", "NH3", "N2", "H2", "H2SO4"]
    print("\n--- Calculando Massas Molares de Referência ---")
    for formula in test_formulas_para_mm:
        mm = calcular_massa_molar(formula)
        if mm > 0:
            massas_molares_calculadas_dict[formula] = mm
            print(f"Massa Molar de {formula}: {mm:.4f} g/mol")
        else:
            print(f"Falha ao calcular massa molar para {formula}")

    print("\n--- Testes de Conversão Massa-Moles-Partículas ---")
    massa_h2o_teste = 36.0306
    print(f"\nPara {massa_h2o_teste}g de H2O:")
    moles_h2o_calc = massa_para_moles(massa_h2o_teste, "H2O")
    if moles_h2o_calc is not None:
        print(f"  {massa_h2o_teste}g de H2O são {moles_h2o_calc:.4f} moles. (Esperado: ~2.0)")
        massa_calculada_h2o = moles_para_massa(moles_h2o_calc, "H2O")
        if massa_calculada_h2o is not None: print(
            f"  {moles_h2o_calc:.4f} moles de H2O são {massa_calculada_h2o:.4f}g.")
        particulas_h2o = moles_para_particulas(moles_h2o_calc)
        print(f"  {moles_h2o_calc:.4f} moles de H2O contêm {particulas_h2o:.3e} moléculas.")

    print("\n--- Testes de Reagente Limitante, Rendimento Teórico e Percentagem ---")

    eq_str_ch4 = "CH4 + O2 -> CO2 + H2O"
    print(f"\nAnalisando Equação: {eq_str_ch4}")
    parsed_ch4_eq = parse_equation_string(eq_str_ch4)

    if CHEMPY_AVAILABLE and parsed_ch4_eq:
        reactants_ch4, products_ch4 = parsed_ch4_eq
        balanced_coeffs_ch4 = balance_chemical_equation(reactants_ch4, products_ch4)

        if balanced_coeffs_ch4:
            reac_c_ch4, prod_c_ch4 = balanced_coeffs_ch4
            full_balanced_eq_ch4 = (reac_c_ch4, prod_c_ch4)
            print(
                f"  Equação Formatada: {format_balanced_equation(reactants_ch4, products_ch4, reac_c_ch4, prod_c_ch4)}")

            # Caso A: O2 é limitante
            quant_reag_A = {"CH4": 1.0, "O2": 1.0}
            print(f"\n  Caso A: Quantidades Iniciais = {quant_reag_A}")
            limitante_A = identificar_reagente_limitante(quant_reag_A, reac_c_ch4)
            print(f"    Reagente Limitante: {limitante_A} (Esperado: O2)")

            if limitante_A:
                moles_limitante_A = quant_reag_A[limitante_A]
                rt_co2_A_moles = calcular_rendimento_teorico("CO2", limitante_A, moles_limitante_A,
                                                             full_balanced_eq_ch4)
                if rt_co2_A_moles is not None:
                    print(f"    Rendimento Teórico de CO2: {rt_co2_A_moles:.4f} moles (Esperado: 0.5)")
                    rt_co2_A_gramas = moles_para_massa(rt_co2_A_moles, "CO2")
                    if rt_co2_A_gramas is not None: print(f"      (equivalente a {rt_co2_A_gramas:.4f}g de CO2)")

                    rr_co2_A_moles = 0.45
                    perc_rend_A = calcular_percentagem_rendimento(rr_co2_A_moles, rt_co2_A_moles)
                    if perc_rend_A is not None:
                        print(
                            f"    Com {rr_co2_A_moles} moles de CO2 (real), Percentagem de Rendimento: {perc_rend_A}% (Esperado: 90.0%)")

            # Caso B: CH4 é limitante, cálculo de rendimento de H2O em gramas
            quant_reag_B = {"CH4": 0.5, "O2": 3.0}
            print(f"\n  Caso B: Quantidades Iniciais = {quant_reag_B}")
            limitante_B = identificar_reagente_limitante(quant_reag_B, reac_c_ch4)
            print(f"    Reagente Limitante: {limitante_B} (Esperado: CH4)")

            if limitante_B:
                moles_limitante_B = quant_reag_B[limitante_B]
                rt_h2o_B_moles = calcular_rendimento_teorico("H2O", limitante_B, moles_limitante_B,
                                                             full_balanced_eq_ch4)
                if rt_h2o_B_moles is not None:
                    print(f"    Rendimento Teórico de H2O: {rt_h2o_B_moles:.4f} moles (Esperado: 1.0)")
                    rt_h2o_B_gramas = moles_para_massa(rt_h2o_B_moles, "H2O")
                    if rt_h2o_B_gramas is not None:
                        print(f"      (equivalente a {rt_h2o_B_gramas:.4f}g de H2O)")

                        rr_h2o_B_gramas = 17.0
                        perc_rend_B_massa = calcular_percentagem_rendimento(rr_h2o_B_gramas, rt_h2o_B_gramas)
                        if perc_rend_B_massa is not None:
                            print(
                                f"    Com {rr_h2o_B_gramas}g de H2O (real), Percentagem de Rendimento (baseado em massa): {perc_rend_B_massa}% (Esperado: ~94.36%)")
    else:
        print("\nTestes de balanceamento para CH4 pulados.")

    print("\n--- Testes Concluídos ---")