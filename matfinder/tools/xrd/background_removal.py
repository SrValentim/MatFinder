# background_removal.py
# Módulo para remoção de background em dados de difração de raios X (XRD)
# Implementa os melhores métodos: SNIP, arPLS e Polynomial Fitting

import numpy as np
import logging
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.signal import savgol_filter
from scipy.interpolate import UnivariateSpline


# ============================================================================
# MÉTODO 1: SNIP (Statistics-sensitive Non-linear Iterative Peak-clipping)
# ============================================================================
# ⭐ RECOMENDADO - Melhor método automático para XRD

def snip_background(y_data, iterations=40, smooth=False):
    """
    Remove background usando algoritmo SNIP.

    SNIP é o método mais usado em XRD profissional (HighScore, BGMN, etc).
    É totalmente automático e muito robusto.

    Parameters:
    -----------
    y_data : array
        Dados de intensidade
    iterations : int
        Número de iterações (20-100). Valores maiores = background mais baixo.
        Padrão: 40
    smooth : bool
        Se True, aplica suavização antes (recomendado para dados ruidosos)

    Returns:
    --------
    background : array
        Background estimado

    Reference:
    ----------
    Ryan, C.G., et al. (1988). "SNIP, a statistics-sensitive background
    treatment for the quantitative analysis of PIXE spectra in geoscience
    applications." Nuclear Instruments and Methods in Physics Research
    Section B: Beam Interactions with Materials and Atoms.
    """
    try:
        y = np.array(y_data, dtype=float)

        # Garantir que não há valores negativos
        y = np.maximum(y, 0)

        # Suavização opcional (reduz ruído)
        if smooth and len(y) > 11:
            try:
                y = savgol_filter(y, window_length=11, polyorder=3)
                y = np.maximum(y, 0)
            except:
                pass

        # Transformação logarítmica (parte do algoritmo SNIP)
        # Referência: Ryan et al. (1988), LLS transformation
        v = np.log(np.log(np.sqrt(y + 1) + 1) + 1)

        # Guardar valores originais das bordas (transformados)
        v_original = v.copy()

        # Iterações SNIP
        for i in range(1, iterations + 1):
            # Janelas deslizantes
            v_left = np.roll(v, i)
            v_right = np.roll(v, -i)

            # Peak clipping
            v = np.minimum(v, (v_left + v_right) / 2)

            # Corrigir bordas - usar valores transformados originais
            # (evita artefatos nas bordas)
            v[:i] = v_original[:i]
            v[-i:] = v_original[-i:]

        # Transformação inversa (LLS inversa)
        background = (np.exp(np.exp(v) - 1) - 1) ** 2 - 1
        background = np.maximum(background, 0)

        # Garantir que background não excede os dados originais
        background = np.minimum(background, y_data)

        logging.debug(f"SNIP background calculado: {iterations} iterações")
        return background

    except Exception as e:
        logging.error(f"Erro no SNIP: {e}")
        return np.zeros_like(y_data)


# ============================================================================
# MÉTODO 2: arPLS (Asymmetrically Reweighted Penalized Least Squares)
# ============================================================================
# 🥈 Excelente método automático, muito usado em espectroscopia

def arpls_background(y_data, lam=1e6, ratio=0.001, max_iter=100):
    """
    Remove background usando algoritmo arPLS.

    arPLS é muito eficaz para backgrounds complexos e variáveis.
    Usado em espectroscopia Raman, IR e XRD.

    Parameters:
    -----------
    y_data : array
        Dados de intensidade
    lam : float
        Parâmetro de suavidade (10^3 - 10^9)
        Valores maiores = background mais suave
        Padrão: 1e6
    ratio : float
        Critério de convergência (0.0001 - 0.01)
        Padrão: 0.001
    max_iter : int
        Número máximo de iterações
        Padrão: 100

    Returns:
    --------
    background : array
        Background estimado

    Reference:
    ----------
    Baek, S.-J., Park, A., Ahn, Y.-J., & Choo, J. (2015).
    "Baseline correction using asymmetrically reweighted penalized least
    squares smoothing." Analyst, 140, 250-257.
    """
    try:
        y = np.array(y_data, dtype=float)
        L = len(y)

        # Construir matriz de diferenças de segunda ordem corretamente
        # D é uma matriz (L-2) x L que calcula a segunda derivada discreta
        diag_0 = np.ones(L - 2)
        diag_1 = -2 * np.ones(L - 2)
        diag_2 = np.ones(L - 2)
        D = sparse.diags([diag_0, diag_1, diag_0], [0, 1, 2], shape=(L - 2, L))

        # H = lambda * D^T * D (matriz de penalização)
        H = lam * D.T.dot(D)

        # Pesos iniciais (todos = 1)
        w = np.ones(L)

        # Iterações arPLS
        z = y.copy()
        for iteration in range(max_iter):
            # Matriz diagonal de pesos
            W = sparse.diags(w, 0, format='csr')

            # Resolver sistema: (W + H) * z = W * y
            # z é o background estimado
            try:
                z = spsolve(W + H, w * y)
            except Exception as solve_error:
                logging.warning(f"arPLS spsolve falhou na iteração {iteration}: {solve_error}")
                break

            # Calcular resíduos (diferença entre dados e background)
            d = y - z

            # Estatísticas dos resíduos negativos (onde o background está acima dos dados)
            dn = d[d < 0]

            if len(dn) == 0:
                # Sem resíduos negativos - convergiu
                logging.debug(f"arPLS convergiu (sem resíduos negativos) na iteração {iteration}")
                break

            m = np.mean(dn)
            s = np.std(dn)

            if s < 1e-10:
                # Desvio padrão muito pequeno - convergiu
                break

            # Atualizar pesos assimetricamente
            # Resíduos positivos (picos) recebem peso menor
            # Resíduos negativos (background) recebem peso maior
            wt = 1.0 / (1.0 + np.exp(2.0 * (d - (2.0 * s - m)) / s))

            # Verificar convergência pela mudança nos pesos
            weight_change = np.linalg.norm(w - wt) / (np.linalg.norm(w) + 1e-10)
            if weight_change < ratio:
                logging.debug(f"arPLS convergiu na iteração {iteration}, mudança de peso: {weight_change:.6f}")
                break

            w = wt

        # Garantir que background seja não-negativo e não exceda dados originais
        background = np.array(z)
        background = np.maximum(background, 0)
        background = np.minimum(background, np.array(y_data))

        logging.debug(f"arPLS background calculado: {iteration+1} iterações, lambda={lam:.2e}")
        return background

    except Exception as e:
        logging.error(f"Erro no arPLS: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return np.zeros_like(y_data)


# ============================================================================
# MÉTODO 3: Polynomial Fitting with Manual Points
# ============================================================================
# 🥉 Método com controle manual - usuário seleciona pontos de background

def polynomial_background(x_data, y_data, points_x, degree=3):
    """
    Remove background usando ajuste polinomial em pontos selecionados.

    Usuário seleciona pontos que considera background, e um polinômio
    é ajustado a esses pontos.

    Parameters:
    -----------
    x_data : array
        Dados de 2θ (ou eixo X)
    y_data : array
        Dados de intensidade
    points_x : list
        Lista de valores X selecionados pelo usuário como background
    degree : int
        Grau do polinômio (2-6)
        Padrão: 3 (cúbico)

    Returns:
    --------
    background : array
        Background estimado
    """
    try:
        if len(points_x) < degree + 1:
            logging.warning(f"Polynomial: Pontos insuficientes ({len(points_x)}) para grau {degree}")
            return np.zeros_like(y_data)

        # Encontrar valores Y correspondentes aos pontos X selecionados
        points_y = []
        for px in points_x:
            # Encontrar índice mais próximo
            idx = np.argmin(np.abs(x_data - px))
            points_y.append(y_data[idx])

        points_x = np.array(points_x)
        points_y = np.array(points_y)

        # Ajustar polinômio
        coeffs = np.polyfit(points_x, points_y, degree)
        background = np.polyval(coeffs, x_data)

        # Garantir não-negatividade
        background = np.maximum(background, 0)
        background = np.minimum(background, y_data)

        logging.debug(f"Polynomial background: {len(points_x)} pontos, grau {degree}")
        return background

    except Exception as e:
        logging.error(f"Erro no Polynomial: {e}")
        return np.zeros_like(y_data)


# ============================================================================
# MÉTODO EXTRA: Spline Interpolation with Manual Points
# ============================================================================

def spline_background(x_data, y_data, points_x, smoothing=0):
    """
    Remove background usando spline cúbica em pontos selecionados.

    Similar ao polynomial, mas usa spline para melhor suavidade.

    Parameters:
    -----------
    x_data : array
        Dados de 2θ
    y_data : array
        Dados de intensidade
    points_x : list
        Pontos X selecionados
    smoothing : float
        Fator de suavização (0 = interpolação exata)
        Valores > 0 = suavização

    Returns:
    --------
    background : array
        Background estimado
    """
    try:
        if len(points_x) < 3:
            logging.warning("Spline: mínimo 3 pontos necessários")
            return np.zeros_like(y_data)

        # Encontrar valores Y
        points_y = []
        for px in points_x:
            idx = np.argmin(np.abs(x_data - px))
            points_y.append(y_data[idx])

        points_x = np.array(points_x)
        points_y = np.array(points_y)

        # Ordenar pontos por X
        sort_idx = np.argsort(points_x)
        points_x = points_x[sort_idx]
        points_y = points_y[sort_idx]

        # Criar spline
        spline = UnivariateSpline(points_x, points_y, s=smoothing, k=3)
        background = spline(x_data)

        background = np.maximum(background, 0)
        background = np.minimum(background, y_data)

        logging.debug(f"Spline background: {len(points_x)} pontos")
        return background

    except Exception as e:
        logging.error(f"Erro no Spline: {e}")
        return np.zeros_like(y_data)


# ============================================================================
# FUNÇÃO AUXILIAR: Calcular Background
# ============================================================================

def calculate_background(x_data, y_data, method='snip', params=None):
    """
    Função principal para calcular background usando o método escolhido.

    Parameters:
    -----------
    x_data : array
        Dados de 2θ
    y_data : array
        Dados de intensidade
    method : str
        Método: 'snip', 'arpls', 'polynomial', 'spline'
    params : dict
        Parâmetros específicos do método

    Returns:
    --------
    background : array
        Background estimado
    """
    if params is None:
        params = {}

    method = method.lower()

    if method == 'snip':
        iterations = params.get('iterations', 40)
        smooth = params.get('smooth', False)
        return snip_background(y_data, iterations, smooth)

    elif method == 'arpls':
        lam = params.get('lam', 1e6)
        ratio = params.get('ratio', 0.001)
        max_iter = params.get('max_iter', 100)
        return arpls_background(y_data, lam, ratio, max_iter)

    elif method == 'polynomial':
        points_x = params.get('points_x', [])
        degree = params.get('degree', 3)
        return polynomial_background(x_data, y_data, points_x, degree)

    elif method == 'spline':
        points_x = params.get('points_x', [])
        smoothing = params.get('smoothing', 0)
        return spline_background(x_data, y_data, points_x, smoothing)

    else:
        logging.error(f"Método desconhecido: {method}")
        return np.zeros_like(y_data)


# ============================================================================
# FUNÇÕES AUXILIARES PARA RECOMENDAÇÕES
# ============================================================================

def get_recommended_params(y_data, method='snip'):
    """
    Retorna parâmetros recomendados baseados nos dados.

    Parameters:
    -----------
    y_data : array
        Dados de intensidade
    method : str
        Método escolhido

    Returns:
    --------
    params : dict
        Parâmetros recomendados
    """
    if method == 'snip':
        # Estimar largura média dos picos
        data_range = np.max(y_data) - np.min(y_data)
        if data_range > 1000:
            iterations = 50
        else:
            iterations = 40

        return {'iterations': iterations, 'smooth': False}

    elif method == 'arpls':
        # Lambda baseado na escala dos dados
        data_max = np.max(y_data)
        if data_max > 10000:
            lam = 1e7
        elif data_max > 1000:
            lam = 1e6
        else:
            lam = 1e5

        return {'lam': lam, 'ratio': 0.001, 'max_iter': 100}

    elif method == 'polynomial':
        return {'degree': 3}

    elif method == 'spline':
        return {'smoothing': 0}

    return {}


def get_method_description(method):
    """Retorna descrição do método."""
    descriptions = {
        'snip': (
            "SNIP (Statistics-sensitive Non-linear Iterative Peak-clipping)\n\n"
            "⭐ RECOMENDADO - Método mais usado em XRD profissional\n\n"
            "✅ Totalmente automático\n"
            "✅ Muito robusto e confiável\n"
            "✅ Rápido\n"
            "✅ Funciona bem com backgrounds complexos\n\n"
            "Usado em: HighScore, BGMN, PyMca, etc."
        ),
        'arpls': (
            "arPLS (Asymmetrically Reweighted Penalized Least Squares)\n\n"
            "🥈 Excelente método automático\n\n"
            "✅ Muito eficaz para backgrounds variáveis\n"
            "✅ Automático\n"
            "✅ Usado em espectroscopia Raman/IR/XRD\n"
            "⚠️ Requer ajuste de lambda\n\n"
            "Melhor para: Backgrounds ondulados complexos"
        ),
        'polynomial': (
            "Polynomial Fitting (Ajuste Polinomial)\n\n"
            "🎯 Método com controle manual\n\n"
            "✅ Controle total do usuário\n"
            "✅ Simples e intuitivo\n"
            "⚠️ Requer seleção manual de pontos\n\n"
            "Melhor para: Backgrounds suaves e previsíveis"
        ),
        'spline': (
            "Spline Interpolation (Interpolação Spline)\n\n"
            "📊 Método manual com suavidade\n\n"
            "✅ Interpolação suave entre pontos\n"
            "✅ Flexível\n"
            "⚠️ Requer seleção manual de pontos\n\n"
            "Melhor para: Backgrounds curvados"
        ),
    }

    return descriptions.get(method, "Método desconhecido")

