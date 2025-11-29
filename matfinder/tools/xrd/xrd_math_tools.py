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
def denoise_with_wavelets(y_data, wavelet='sym8', level_percentage=0.1):
    """
    Reduz o ruído de um sinal 1D usando a Transformada Wavelet.

    Args:
        y_data (np.ndarray): O array de dados de intensidade.
        wavelet (str): O nome da wavelet a ser usada (ex: 'db4', 'sym8').
        level_percentage (float): Um fator (de 0 a 1) para ajustar o limiar.
                                  Valores maiores removem mais ruído (e potencialmente mais sinal).

    Returns:
        np.ndarray: O array de dados com ruído reduzido.
    """
    if not PYWAVELETS_AVAILABLE:
        print("PyWavelets não está disponível. Retornando dados originais.")
        return y_data

    # 1. Decomposição do sinal
    # Decompõe o sinal em coeficientes de aproximação (baixa frequência) e de detalhe (alta frequência)
    coeffs = pywt.wavedec(y_data, wavelet, mode='per')

    # 2. Cálculo do Limiar (Threshold)
    # Usa um limiar universal (VisuShrink) que é bom para sinais com ruído gaussiano.
    # Validação: verificar se há coeficientes de detalhe suficientes
    if len(coeffs) < 2 or len(coeffs[-1]) == 0:
        print("AVISO: Coeficientes wavelet insuficientes. Retornando dados originais.")
        return y_data

    detail_coeffs = coeffs[-1]
    median_detail = np.median(detail_coeffs)
    mad = np.median(np.abs(detail_coeffs - median_detail))

    # Proteção contra divisão por zero ou MAD muito pequeno
    if mad < 1e-10:
        print("AVISO: MAD muito pequeno, dados podem ser constantes. Retornando dados originais.")
        return y_data

    sigma = mad / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(y_data)))

    # Ajusta o limiar com base no input do usuário para dar mais controle
    adjusted_threshold = threshold * (1 + level_percentage * 5)  # Mapeia de 0-1 para um range mais efetivo

    # 3. Limiarização dos Coeficientes (Thresholding)
    # Aplica o "soft thresholding" nos coeficientes de detalhe.
    # Isso encolhe os coeficientes em direção a zero pelo valor do limiar.
    new_coeffs = [coeffs[0]]  # Mantém os coeficientes de aproximação intactos
    for c in coeffs[1:]:
        new_coeffs.append(pywt.threshold(c, value=adjusted_threshold, mode='soft'))

    # 4. Reconstrução do Sinal
    # Reconstrói o sinal a partir dos coeficientes modificados.
    denoised_y = pywt.waverec(new_coeffs, wavelet, mode='per')

    # Garante que o sinal reconstruído tenha o mesmo tamanho do original
    if len(denoised_y) != len(y_data):
        return denoised_y[:len(y_data)]

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
