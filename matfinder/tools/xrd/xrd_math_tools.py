# xrd_math_tools.py
# Módulo com funções matemáticas para a ferramenta PhaseDRX.
# Versão 3.0 - Adicionada a função de redução de ruído por Transformada Wavelet

import numpy as np
from scipy.ndimage import convolve1d

try:
    from scipy.signal import savgol_filter, find_peaks

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("AVISO: A biblioteca 'scipy' não foi encontrada. A suavização e detecção de picos não funcionarão.")
    print("Para instalar, execute: pip install scipy")

# --- NOVA VERIFICAÇÃO DE DEPENDÊNCIA PARA WAVELETS ---
try:
    import pywt

    PYWAVELETS_AVAILABLE = True
except ImportError:
    PYWAVELETS_AVAILABLE = False
    print("AVISO: A biblioteca 'pywavelets' não foi encontrada. A redução de ruído por Wavelet não funcionará.")
    print("Para instalar, execute: pip install PyWavelets")


def smooth_data(y_data, window_length=5, polyorder=2):
    """
    Suaviza os dados do eixo Y usando o filtro Savitzky-Golay.

    Args:
        y_data (list or np.ndarray): A lista de valores do eixo Y a serem suavizados.
        window_length (int): O comprimento da janela do filtro. Deve ser um inteiro ímpar positivo.
        polyorder (int): A ordem do polinômio usado para ajustar as amostras.
                         Deve ser menor que window_length.

    Returns:
        np.ndarray: Um array numpy com os dados suavizados.
                    Retorna os dados originais se o scipy não estiver disponível ou se os parâmetros forem inválidos.
    """
    if not SCIPY_AVAILABLE:
        print("Scipy não está disponível. Retornando dados originais.")
        return np.array(y_data)

    if not isinstance(y_data, np.ndarray):
        y_data = np.array(y_data)

    # Validação dos parâmetros para evitar erros
    if not isinstance(window_length, int) or window_length <= 0 or window_length % 2 == 0:
        print(f"Aviso: window_length ({window_length}) deve ser um inteiro ímpar positivo. Usando valor padrão 5.")
        window_length = 5

    if not isinstance(polyorder, int) or polyorder < 1:
        print(f"Aviso: polyorder ({polyorder}) deve ser um inteiro positivo. Usando valor padrão 2.")
        polyorder = 2

    if polyorder >= window_length:
        print(
            f"Aviso: polyorder ({polyorder}) deve ser menor que window_length ({window_length}). Ajustando polyorder.")
        polyorder = window_length - 1 if window_length > 1 else 0

    if len(y_data) < window_length:
        print("Aviso: Os dados são menores que a janela de suavização. Retornando dados originais.")
        return y_data

    try:
        smoothed_y = savgol_filter(y_data, window_length, polyorder)
        return smoothed_y
    except Exception as e:
        print(f"Erro durante a aplicação do filtro Savitzky-Golay: {e}")
        return y_data


def detect_peaks(y_data, x_data=None, prominence=0.01, width=1):
    """
    Detecta picos nos dados do eixo Y usando a função find_peaks do SciPy.

    Args:
        y_data (np.ndarray): Array de dados de intensidade.
        x_data (np.ndarray, optional): Array de dados de posição (ex: 2-theta).
                                       Se fornecido, as posições dos picos serão retornadas.
        prominence (float): A proeminência mínima de um pico.
        width (int): A largura mínima de um pico em pontos de dados.

    Returns:
        tuple: Uma tupla contendo (peak_positions, peak_intensities).
               Se x_data não for fornecido, peak_positions serão os índices.
    """
    if not SCIPY_AVAILABLE:
        print("Scipy não está disponível. Não é possível detectar picos.")
        return np.array([]), np.array([])

    # Validação: verificar se há dados suficientes
    if len(y_data) == 0:
        print("AVISO: Array de dados vazio. Não é possível detectar picos.")
        return np.array([]), np.array([])

    max_intensity = np.max(y_data)
    min_intensity = np.min(y_data)
    intensity_range = max_intensity - min_intensity

    # Proteção contra dados constantes (todos com mesmo valor)
    if intensity_range < 1e-10:
        print("AVISO: Dados têm intensidade constante. Não é possível detectar picos.")
        return np.array([]), np.array([])

    prominence_value = prominence * intensity_range

    indices, properties = find_peaks(y_data, prominence=prominence_value, width=width)

    peak_intensities = y_data[indices]
    peak_positions = x_data[indices] if x_data is not None else indices

    return peak_positions, peak_intensities


# --- NOVA FUNÇÃO DE REDUÇÃO DE RUÍDO (WAVELET) ---
def denoise_with_wavelets(y_data, wavelet='sym8', level_percentage=0.1, method='bayesshrink'):
    """
    Reduz o ruído de um sinal 1D usando a Transformada Wavelet.

    Implementa dois métodos de threshold:
    - BayesShrink (padrão): Threshold adaptativo por nível, melhor para preservar detalhes
    - VisuShrink: Threshold universal, mais agressivo na remoção de ruído

    Args:
        y_data (np.ndarray): O array de dados de intensidade.
        wavelet (str): O nome da wavelet a ser usada.
                       Recomendados para XRD: 'sym8' (Symlet-8), 'db4' (Daubechies-4)
        level_percentage (float): Fator de ajuste fino (0 a 1).
                                  0.0 = threshold mínimo (preserva mais detalhes)
                                  1.0 = threshold máximo (remove mais ruído)
        method (str): Método de threshold - 'bayesshrink' (padrão) ou 'visushrink'

    Returns:
        np.ndarray: O array de dados com ruído reduzido.

    References:
        - Chang, S.G.; Yu, B.; Vetterli, M. (2000). "Adaptive wavelet thresholding
          for image denoising and compression". IEEE Trans. Image Processing. 9(9): 1532-1546.
        - Donoho, D.L.; Johnstone, I.M. (1994). "Ideal spatial adaptation by
          wavelet shrinkage". Biometrika. 81(3): 425-455.
    """
    if not PYWAVELETS_AVAILABLE:
        print("PyWavelets não está disponível. Retornando dados originais.")
        return y_data

    y = np.array(y_data, dtype=float)
    n = len(y)

    # Calcular nível máximo de decomposição
    try:
        max_level = pywt.dwt_max_level(n, pywt.Wavelet(wavelet).dec_len)
        level = min(max_level, 6)  # Limitar a 6 níveis para XRD
    except:
        level = None

    # 1. Decomposição do sinal (DWT)
    coeffs = pywt.wavedec(y, wavelet, mode='per', level=level)

    if len(coeffs) < 2 or len(coeffs[-1]) == 0:
        print("AVISO: Coeficientes wavelet insuficientes. Retornando dados originais.")
        return y_data

    # 2. Estimar nível de ruído usando MAD do nível mais fino
    detail_finest = coeffs[-1]
    sigma_noise = np.median(np.abs(detail_finest - np.median(detail_finest))) / 0.6745

    if sigma_noise < 1e-10:
        print("AVISO: Ruído estimado muito baixo. Retornando dados originais.")
        return y_data

    # 3. Aplicar threshold em cada nível de detalhe
    new_coeffs = [coeffs[0]]  # Manter coeficientes de aproximação

    for i, detail_coeffs in enumerate(coeffs[1:], 1):
        if len(detail_coeffs) == 0:
            new_coeffs.append(detail_coeffs)
            continue

        if method.lower() == 'bayesshrink':
            # ============================================
            # BayesShrink: Threshold adaptativo por nível
            # Referência: Chang et al. (2000)
            # ============================================

            # Variância total dos coeficientes neste nível
            sigma_y_squared = np.var(detail_coeffs)

            # Variância do sinal = variância total - variância do ruído
            sigma_signal_squared = max(sigma_y_squared - sigma_noise**2, 0)

            if sigma_signal_squared > 0:
                # Threshold BayesShrink: λ = σ_noise² / σ_signal
                threshold = (sigma_noise**2) / np.sqrt(sigma_signal_squared)
            else:
                # Se não há sinal detectável, usar VisuShrink como fallback
                threshold = sigma_noise * np.sqrt(2 * np.log(n))

        else:
            # ============================================
            # VisuShrink: Threshold universal
            # Referência: Donoho & Johnstone (1994)
            # ============================================
            threshold = sigma_noise * np.sqrt(2 * np.log(n))

        # Ajuste do usuário (fator de 0.5 a 2.0)
        # level_percentage = 0 → fator = 0.5 (preserva mais)
        # level_percentage = 1 → fator = 2.0 (remove mais)
        adjustment_factor = 0.5 + level_percentage * 1.5
        adjusted_threshold = threshold * adjustment_factor

        # Soft thresholding (preserva continuidade do sinal)
        thresholded = pywt.threshold(detail_coeffs, value=adjusted_threshold, mode='soft')
        new_coeffs.append(thresholded)

    # 4. Reconstrução do Sinal (IDWT)
    denoised_y = pywt.waverec(new_coeffs, wavelet, mode='per')

    # Garantir mesmo tamanho do sinal original
    if len(denoised_y) != n:
        denoised_y = denoised_y[:n]

    return denoised_y


# --- FUNÇÕES DE ANÁLISE AVANÇADA EXISTENTES ---

def apply_lp_correction(x_data_2theta_deg, y_data):
    """
    Aplica a correção de intensidade de Lorentz-polarização a um difratograma.
    """
    epsilon = 1e-8
    two_theta_rad = np.radians(x_data_2theta_deg)
    theta_rad = two_theta_rad / 2.0
    numerator = 1 + np.cos(two_theta_rad) ** 2
    denominator = (np.sin(theta_rad) ** 2 * np.cos(theta_rad)) + epsilon
    lp_factor = numerator / denominator
    y_corrected = y_data / lp_factor
    return y_corrected


def calculate_sonneveld_visser_background(y_data, width, iterations=20):
    """
    Calcula o fundo usando o algoritmo iterativo de Sonneveld-Visser.
    """
    if not isinstance(y_data, np.ndarray):
        y_data = np.array(y_data)
    n_points = len(y_data)
    baseline = np.linspace(y_data[0], y_data[-1], n_points)
    yield baseline
    filter_width = 2 * int(width) + 1
    kernel = np.ones(filter_width) / filter_width
    for _ in range(iterations):
        baseline_candidate = np.minimum(y_data, baseline)
        baseline = convolve1d(baseline_candidate, kernel, mode='nearest')
        yield baseline


def calculate_second_derivative(y_data):
    """
    Calcula a segunda derivada de um array de dados.
    """
    if not isinstance(y_data, np.ndarray):
        y_data = np.array(y_data)
    first_derivative = np.gradient(y_data)
    second_derivative = np.gradient(first_derivative)
    return second_derivative
