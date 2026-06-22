"""
raw_parser.py
Parser para formatos binários de difração de raios-X.
Suporta: Shimadzu XRD (.raw), Bruker RAW (v1, v2, v3, v4), Rigaku (.ras),
         XRDML (.xrdml), BRML (.brml), CSV (.csv)

Parte do projeto MatFinder - Copyright (C) 2025 Raynner Valentim (UFAM)
"""

import struct
import os
import logging
import numpy as np
from matfinder.core.translator import ptr

logger = logging.getLogger(__name__)


def read_raw_file(file_path: str) -> tuple:
    """
    Lê um arquivo .RAW e retorna (two_theta, intensities).

    Suporta Shimadzu XRD e Bruker RAW v1, v2, v3 e v4.

    Args:
        file_path: Caminho para o arquivo .raw

    Returns:
        tuple: (two_theta_array, intensity_array) como arrays numpy

    Raises:
        ValueError: Se o formato não for reconhecido
    """
    with open(file_path, 'rb') as f:
        header = f.read(16)
        f.seek(0)

        # Detectar Shimadzu XRD (header começa com "Shimadzu XRD")
        if header[:12] == b'Shimadzu XRD':
            return _read_shimadzu_raw(f)

        # Identificar versão do Bruker RAW
        if header[:4] == b'RAW ':
            return _read_raw_v2(f)
        elif header[:4] == b'RAW2':
            return _read_raw_v2(f)
        elif header[:3] == b'RAW':
            # RAW v3 ou v4 - começa com "RAW" seguido de version byte
            version_byte = header[3:4]
            if version_byte == b'\x01':
                return _read_raw_v3(f)
            elif version_byte == b'\x04':
                return _read_raw_v4(f)
            else:
                return _read_raw_v3(f)  # Tentar v3 como fallback
        else:
            # Tentar RAW v1 (formato mais antigo, sem magic header)
            return _read_raw_v1(f)


def _read_shimadzu_raw(f) -> tuple:
    """
    Parser para Shimadzu XRD RAW format (v4.x e v3.x).

    Estrutura do arquivo Shimadzu XRD:
    - Offset 0-12: "Shimadzu XRD" (identificador)
    - Offset 16-24: "Ver X.X" (versão)
    - Offset 48: uint32 - tamanho do header
    - Offset 52: uint32 - tamanho da seção de dados em bytes
    - Offset 608: uint32 - start_2theta * 10000
    - Offset 612: uint32 - end_2theta * 10000
    - Offset 624: uint32 - número de pontos
    - Dados: uint32 (contagens inteiras) no final do arquivo
    """
    f.seek(0)
    data = f.read()
    file_size = len(data)

    if file_size < 968:
        raise ValueError(ptr("Shimadzu XRD: Arquivo muito pequeno"))

    # Ler versão
    version_str = data[16:24].decode('ascii', errors='replace').strip('\x00').strip()
    logger.info(f"Shimadzu XRD format detectado: {version_str}")

    # Ler parâmetros do scan
    data_size = struct.unpack('<I', data[52:56])[0]  # Tamanho dos dados em bytes
    n_points = struct.unpack('<I', data[624:628])[0]  # Número de pontos
    start_raw = struct.unpack('<I', data[608:612])[0]  # start_2theta * 10000
    end_raw = struct.unpack('<I', data[612:616])[0]    # end_2theta * 10000

    # Validar parâmetros
    if n_points < 1 or n_points > 100000:
        raise ValueError(ptr("Shimadzu XRD: Numero de pontos invalido: {}").format(n_points))

    # Converter 2theta
    start_2theta = start_raw / 10000.0
    end_2theta = end_raw / 10000.0

    # Validar ângulos
    if not (0 <= start_2theta <= 180) or not (0 < end_2theta <= 180):
        # Tentar outros fatores de escala
        for scale in [1000.0, 100000.0, 100.0]:
            s = start_raw / scale
            e = end_raw / scale
            if 0 <= s <= 180 and 0 < e <= 180 and e > s:
                start_2theta = s
                end_2theta = e
                break
        else:
            raise ValueError(ptr("Shimadzu XRD: Angulos invalidos: start={}, end={}").format(start_raw, end_raw))

    if end_2theta <= start_2theta:
        raise ValueError(ptr("Shimadzu XRD: end_2theta ({}) <= start_2theta ({})").format(end_2theta, start_2theta))

    # Calcular offset dos dados (dados ficam no final do arquivo)
    data_offset = file_size - (n_points * 4)

    # Alternativa: usar data_size do header
    alt_data_offset = file_size - data_size

    # Escolher o offset que faz mais sentido
    if alt_data_offset > 0 and alt_data_offset < file_size:
        data_offset = alt_data_offset

    if data_offset < 0 or data_offset >= file_size:
        raise ValueError(ptr("Shimadzu XRD: Offset de dados invalido: {}").format(data_offset))

    # Recalcular n_points baseado no espaço disponível
    available_bytes = file_size - data_offset
    max_points = available_bytes // 4

    if n_points > max_points:
        n_points = max_points

    # Ler contagens (uint32)
    counts = []
    for i in range(n_points):
        pos = data_offset + i * 4
        if pos + 4 > file_size:
            break
        val = struct.unpack('<I', data[pos:pos+4])[0]
        counts.append(float(val))

    if len(counts) < 10:
        raise ValueError(ptr("Shimadzu XRD: Muito poucos pontos ({})").format(len(counts)))

    # Gerar array de 2theta
    two_theta = np.linspace(start_2theta, end_2theta, len(counts))
    intensities = np.array(counts, dtype=float)

    step = (end_2theta - start_2theta) / (len(counts) - 1) if len(counts) > 1 else 0
    logger.info(f"Shimadzu XRD: {len(counts)} pontos, "
                f"2theta: {start_2theta:.2f} - {end_2theta:.2f}, "
                f"step: {step:.4f}, "
                f"counts: {int(min(counts))} - {int(max(counts))}")

    return two_theta, intensities


def _read_raw_v1(f) -> tuple:
    """
    Parser para Bruker RAW v1 (formato antigo Siemens/Bruker).
    Formato simples com header fixo.
    """
    f.seek(0)
    data = f.read()

    # RAW v1: header de 4 bytes com número de pontos, depois dados float32
    # Tentar interpretar como formato simples
    try:
        # Formato: 4 bytes (n_points), 4 bytes (start_2theta), 4 bytes (step_size)
        # Seguido por n_points * 4 bytes de intensidades (float32)
        n_points = struct.unpack('<I', data[0:4])[0]

        # Validar: n_points deve ser razoável (1 a 100000)
        if n_points < 1 or n_points > 100000:
            raise ValueError(ptr("RAW v1: Numero de pontos invalido"))

        start_2theta = struct.unpack('<f', data[4:8])[0]
        step_size = struct.unpack('<f', data[8:12])[0]

        # Validar: start_2theta entre -10 e 180, step entre 0.001 e 1
        if not (-10 <= start_2theta <= 180) or not (0.001 <= step_size <= 1.0):
            raise ValueError(ptr("RAW v1: Parametros de 2theta invalidos"))

        # Ler intensidades
        offset = 12
        intensities = []
        for i in range(n_points):
            if offset + 4 > len(data):
                break
            intensity = struct.unpack('<f', data[offset:offset+4])[0]
            intensities.append(intensity)
            offset += 4

        if len(intensities) < 10:
            raise ValueError(ptr("RAW v1: Muito poucos pontos de dados"))

        two_theta = np.array([start_2theta + i * step_size for i in range(len(intensities))])
        intensities = np.array(intensities, dtype=float)

        logger.info(f"RAW v1: {len(intensities)} pontos, 2theta: {two_theta[0]:.2f} - {two_theta[-1]:.2f}")
        return two_theta, intensities

    except (struct.error, ValueError) as e:
        raise ValueError(ptr("Formato RAW v1 nao reconhecido: {}").format(e))


def _read_raw_v2(f) -> tuple:
    """
    Parser para Bruker RAW v2 (DIFFRAC Plus).
    Header: "RAW " ou "RAW2" + metadados + dados.
    """
    f.seek(0)
    magic = f.read(4)

    # Ler header (varia de 48 a 712 bytes dependendo da versão)
    if magic == b'RAW ':
        # RAW v2 com header "RAW " (Bruker antigo)
        f.seek(4)
        # Próximos 4 bytes: número de ranges
        n_ranges = struct.unpack('<I', f.read(4))[0]

        if n_ranges == 0 or n_ranges > 100:
            n_ranges = 1

        all_two_theta = []
        all_intensity = []

        for range_idx in range(n_ranges):
            # Ler informações do range
            try:
                # Header do range (48 bytes mínimo)
                range_header_size = struct.unpack('<I', f.read(4))[0]

                if range_header_size < 12 or range_header_size > 10000:
                    range_header_size = 48

                # Voltar e ler todo o header do range
                f.seek(f.tell() - 4)
                range_data = f.read(range_header_size)

                # Extrair campos essenciais
                n_steps = struct.unpack('<I', range_data[0:4])[0]
                start_theta = struct.unpack('<d', range_data[4:12])[0]
                step_size = struct.unpack('<d', range_data[12:20])[0]

                # Ler intensidades
                for i in range(n_steps):
                    intensity = struct.unpack('<f', f.read(4))[0]
                    theta = start_theta + i * step_size
                    all_two_theta.append(theta)
                    all_intensity.append(intensity)

            except struct.error:
                break

        if not all_two_theta:
            raise ValueError(ptr("RAW v2: Nenhum dado encontrado"))

        two_theta = np.array(all_two_theta, dtype=float)
        intensities = np.array(all_intensity, dtype=float)

        logger.info(f"RAW v2: {len(intensities)} pontos, 2theta: {two_theta[0]:.2f} - {two_theta[-1]:.2f}")
        return two_theta, intensities

    elif magic == b'RAW2':
        # RAW2 format
        return _read_raw2_format(f)

    else:
        raise ValueError(ptr("Header RAW v2 nao reconhecido: {}").format(magic))


def _read_raw2_format(f) -> tuple:
    """Parser para formato RAW2."""
    f.seek(4)  # Pular "RAW2"

    # RAW2 header: 4 bytes version seguido de metadados
    header_data = f.read(168)  # Header típico de 168 bytes

    n_steps = struct.unpack('<I', header_data[0:4])[0]

    # Offsets podem variar, tentar diferentes layouts
    try:
        start_theta = struct.unpack('<d', header_data[8:16])[0]
        step_size = struct.unpack('<d', header_data[16:24])[0]
    except struct.error:
        start_theta = struct.unpack('<f', header_data[4:8])[0]
        step_size = struct.unpack('<f', header_data[8:12])[0]

    # Validar
    if not (0 <= start_theta <= 180) or not (0.001 <= step_size <= 1.0):
        raise ValueError(ptr("RAW2: Parametros invalidos: start={}, step={}").format(start_theta, step_size))

    if n_steps < 1 or n_steps > 100000:
        raise ValueError(ptr("RAW2: Numero de pontos invalido: {}").format(n_steps))

    # Ler intensidades (float32)
    intensities = []
    for i in range(n_steps):
        try:
            val = struct.unpack('<f', f.read(4))[0]
            intensities.append(val)
        except struct.error:
            break

    two_theta = np.array([start_theta + i * step_size for i in range(len(intensities))])
    intensities = np.array(intensities, dtype=float)

    logger.info(f"RAW2: {len(intensities)} pontos, 2theta: {two_theta[0]:.2f} - {two_theta[-1]:.2f}")
    return two_theta, intensities


def _read_raw_v3(f) -> tuple:
    """
    Parser para Bruker RAW v3 (DIFFRAC.SUITE).
    Formato mais complexo com múltiplos ranges.
    """
    f.seek(0)
    magic = f.read(4)  # "RAW" + version byte

    # Ler header principal (712 bytes para v3)
    f.seek(0)
    full_header = f.read(712)

    if len(full_header) < 712:
        raise ValueError(ptr("RAW v3: Arquivo muito pequeno"))

    # Campos do header principal RAW v3
    # Offset 12: n_steps (uint32)
    # Offset 16: start_2theta (double)
    # Offset 24: end_2theta (double)
    # Offset 32: step_size (double)

    try:
        n_ranges = struct.unpack('<I', full_header[4:8])[0]

        if n_ranges == 0:
            n_ranges = 1
        if n_ranges > 100:
            n_ranges = 1

        all_two_theta = []
        all_intensity = []

        # O header principal é seguido por headers de cada range
        # Header do range: tipicamente 304 bytes em RAW v3
        range_header_size = 304

        pos = 712  # Após header principal

        for range_idx in range(n_ranges):
            f.seek(pos)
            range_header = f.read(range_header_size)

            if len(range_header) < range_header_size:
                break

            # Extrair info do range
            # Offset 0-4: header size (verifica)
            rh_size = struct.unpack('<I', range_header[0:4])[0]
            if rh_size > 0 and rh_size < 10000:
                range_header_size = rh_size

            n_steps = struct.unpack('<I', range_header[4:8])[0]

            # Ler 2theta start e step
            start_theta = struct.unpack('<d', range_header[8:16])[0]
            step_size = struct.unpack('<d', range_header[16:24])[0]

            if n_steps < 1 or n_steps > 100000:
                break
            if not (0.001 <= abs(step_size) <= 5.0):
                # Tentar outros offsets
                start_theta = struct.unpack('<d', range_header[16:24])[0]
                step_size = struct.unpack('<d', range_header[24:32])[0]

            # Ler dados (após header do range)
            pos = f.tell()

            for i in range(n_steps):
                try:
                    val = struct.unpack('<f', f.read(4))[0]
                    theta = start_theta + i * step_size
                    all_two_theta.append(theta)
                    all_intensity.append(val)
                except struct.error:
                    break

            pos = f.tell()

        if not all_two_theta:
            raise ValueError(ptr("RAW v3: Nenhum dado extraido"))

        two_theta = np.array(all_two_theta, dtype=float)
        intensities = np.array(all_intensity, dtype=float)

        logger.info(f"RAW v3: {len(intensities)} pontos, 2theta: {two_theta[0]:.2f} - {two_theta[-1]:.2f}")
        return two_theta, intensities

    except (struct.error, ValueError) as e:
        raise ValueError(ptr("RAW v3: Erro ao ler: {}").format(e))


def _read_raw_v4(f) -> tuple:
    """
    Parser para Bruker RAW v4 (formato mais recente).
    Similar ao v3 com headers expandidos.
    """
    f.seek(0)
    data = f.read()

    # V4 tem header principal maior, seguido por headers de range e dados
    try:
        # Tentar layout v4
        main_header_size = struct.unpack('<I', data[4:8])[0]

        if main_header_size < 100 or main_header_size > 10000:
            main_header_size = 712

        n_ranges = struct.unpack('<I', data[8:12])[0]
        if n_ranges == 0 or n_ranges > 100:
            n_ranges = 1

        all_two_theta = []
        all_intensity = []

        pos = main_header_size

        for range_idx in range(n_ranges):
            if pos + 48 > len(data):
                break

            range_header_size = struct.unpack('<I', data[pos:pos+4])[0]
            if range_header_size < 20 or range_header_size > 10000:
                range_header_size = 304

            n_steps = struct.unpack('<I', data[pos+4:pos+8])[0]
            start_theta = struct.unpack('<d', data[pos+8:pos+16])[0]
            step_size = struct.unpack('<d', data[pos+16:pos+24])[0]

            if n_steps < 1 or n_steps > 100000:
                break

            data_start = pos + range_header_size

            for i in range(n_steps):
                data_pos = data_start + i * 4
                if data_pos + 4 > len(data):
                    break
                val = struct.unpack('<f', data[data_pos:data_pos+4])[0]
                theta = start_theta + i * step_size
                all_two_theta.append(theta)
                all_intensity.append(val)

            pos = data_start + n_steps * 4

        if not all_two_theta:
            raise ValueError(ptr("RAW v4: Nenhum dado extraido"))

        two_theta = np.array(all_two_theta, dtype=float)
        intensities = np.array(all_intensity, dtype=float)

        logger.info(f"RAW v4: {len(intensities)} pontos, 2theta: {two_theta[0]:.2f} - {two_theta[-1]:.2f}")
        return two_theta, intensities

    except (struct.error, ValueError) as e:
        raise ValueError(ptr("RAW v4: Erro ao ler: {}").format(e))


def read_brml_file(file_path: str) -> tuple:
    """
    Lê um arquivo .brml do Bruker (formato ZIP/XML).

    Returns:
        tuple: (two_theta_array, intensity_array)
    """
    import zipfile
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            # Procurar o XML com os dados dentro do ZIP
            xml_files = [f for f in z.namelist() if f.endswith('.xml')]

            if not xml_files:
                raise ValueError(ptr("BRML: Nenhum XML encontrado dentro do arquivo"))

            # Normalmente o arquivo principal é o maior ou contém "RawData"
            target_xml = None
            for xf in xml_files:
                if 'RawData' in xf or 'DataContainer' in xf:
                    target_xml = xf
                    break
            if target_xml is None:
                target_xml = xml_files[0]

            with z.open(target_xml) as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Procurar dados 2theta e intensidade
                # Namespace Bruker
                ns = {'b': 'http://www.2dimensional.com/2005'}

                # Tentar diferentes paths no XML
                two_theta = []
                intensities = []
                start = None
                step = None

                # Path genérico: procurar elementos com dados numéricos
                for elem in root.iter():
                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if tag in ('StartPosition', 'Start2Theta'):
                        start = float(elem.text)
                    elif tag in ('EndPosition', 'End2Theta'):
                        pass  # end não usado diretamente
                    elif tag in ('StepSize', 'Step2Theta'):
                        step = float(elem.text)
                    elif tag in ('Intensities', 'RawIntensities', 'CorrectedIntensities'):
                        if elem.text:
                            intensities = [float(v) for v in elem.text.strip().split()]

                if intensities and start is not None and step is not None:
                    two_theta = [start + i * step for i in range(len(intensities))]

                if not two_theta:
                    raise ValueError(ptr("BRML: Dados de 2theta/intensidade nao encontrados no XML"))

                result_2theta = np.array(two_theta, dtype=float)
                result_intensity = np.array(intensities, dtype=float)

                logger.info(f"BRML: {len(result_intensity)} pontos, "
                           f"2theta: {result_2theta[0]:.2f} - {result_2theta[-1]:.2f}")
                return result_2theta, result_intensity

    except zipfile.BadZipFile:
        raise ValueError(ptr("BRML: Arquivo nao e um ZIP valido"))
    except Exception as e:
        raise ValueError(ptr("BRML: Erro ao ler: {}").format(e))


def read_xrdml_file(file_path: str) -> tuple:
    """
    Lê um arquivo .xrdml (PANalytical/Malvern Panalytical).
    Formato XML com dados de difração.

    Returns:
        tuple: (two_theta_array, intensity_array)
    """
    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Namespace PANalytical
        ns_map = {}
        for event, elem in ET.iterparse(file_path, events=['start-ns']):
            ns_map[elem[0]] = elem[1]

        # Re-parse com namespace
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Obter namespace padrão
        ns = ''
        if root.tag.startswith('{'):
            ns = root.tag.split('}')[0] + '}'

        two_theta = []  # type: list
        intensities = []  # type: list
        start = None  # type: float | None
        end = None  # type: float | None

        # Procurar scan data
        for data_points in root.iter(f'{ns}dataPoints'):
            # Posições 2theta
            positions = data_points.find(f'{ns}positions')
            if positions is not None:
                start_elem = positions.find(f'{ns}startPosition')
                end_elem = positions.find(f'{ns}endPosition')
                if start_elem is not None and end_elem is not None:
                    start = float(start_elem.text)
                    end = float(end_elem.text)

            # Intensidades (counts ou intensities)
            for tag_name in ['counts', 'intensities', 'countingTime']:
                counts_elem = data_points.find(f'{ns}{tag_name}')
                if counts_elem is not None and counts_elem.text:
                    intensities = [float(v) for v in counts_elem.text.strip().split()]
                    break

            if intensities and start is not None and end is not None:
                n_points = len(intensities)
                calc_step = (end - start) / (n_points - 1) if n_points > 1 else 0.02
                two_theta = [start + i * calc_step for i in range(n_points)]
                break

        if not two_theta:
            raise ValueError(ptr("XRDML: Dados de 2theta/intensidade nao encontrados"))

        result_2theta = np.array(two_theta, dtype=float)
        result_intensity = np.array(intensities, dtype=float)

        logger.info(f"XRDML: {len(result_intensity)} pontos, "
                    f"2theta: {result_2theta[0]:.2f} - {result_2theta[-1]:.2f}")
        return result_2theta, result_intensity

    except ET.ParseError as e:
        raise ValueError(ptr("XRDML: Erro de parsing XML: {}").format(e))
    except Exception as e:
        raise ValueError(ptr("XRDML: Erro ao ler: {}").format(e))


def read_ras_file(file_path: str) -> tuple:
    """
    Lê um arquivo .ras (Rigaku).
    Formato texto com headers e dados.

    Returns:
        tuple: (two_theta_array, intensity_array)
    """
    two_theta = []
    intensities = []
    in_data_section = False
    start_angle = None
    step_size = None

    try:
        # Tentar diferentes encodings
        for encoding in ['utf-8', 'latin-1', 'shift_jis', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            raise ValueError(ptr("RAS: Nao foi possivel decodificar o arquivo"))

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Headers Rigaku
            if line.startswith('*MEAS_SCAN_START'):
                start_angle = float(line.split('=')[-1].strip().strip('"'))
            elif line.startswith('*MEAS_SCAN_STEP'):
                step_size = float(line.split('=')[-1].strip().strip('"'))
            elif line.startswith('*COUNT'):
                # Seção de contagens
                in_data_section = True
                continue
            elif line.startswith('*END'):
                in_data_section = False
                continue
            elif line.startswith('*'):
                continue  # Outros headers

            if in_data_section:
                try:
                    parts = line.split()
                    if len(parts) >= 1:
                        intensities.append(float(parts[0]))
                except ValueError:
                    continue

        if intensities and start_angle is not None and step_size is not None:
            two_theta = [start_angle + i * step_size for i in range(len(intensities))]
        elif not two_theta:
            # Tentar formato alternativo: colunas 2theta, intensity
            two_theta = []
            intensities = []
            for line in lines:
                line = line.strip()
                if line.startswith('*') or not line:
                    continue
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        two_theta.append(float(parts[0]))
                        intensities.append(float(parts[1]))
                except ValueError:
                    continue

        if not two_theta or not intensities:
            raise ValueError(ptr("RAS: Nenhum dado encontrado"))

        result_2theta = np.array(two_theta, dtype=float)
        result_intensity = np.array(intensities, dtype=float)

        logger.info(f"RAS: {len(result_intensity)} pontos, "
                    f"2theta: {result_2theta[0]:.2f} - {result_2theta[-1]:.2f}")
        return result_2theta, result_intensity

    except Exception as e:
        raise ValueError(ptr("RAS: Erro ao ler: {}").format(e))


def read_csv_file(file_path: str) -> tuple:
    """
    Lê um arquivo .csv com colunas 2theta e intensidade.
    Aceita separadores: vírgula, ponto-e-vírgula, tab.

    Returns:
        tuple: (two_theta_array, intensity_array)
    """
    two_theta = []
    intensities = []

    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(ptr("CSV: Nao foi possivel decodificar o arquivo"))

    # Detectar separador
    for sep in [',', ';', '\t']:
        first_data_line = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            first_data_line = line
            break

        if first_data_line and sep in first_data_line:
            parts = first_data_line.split(sep)
            if len(parts) >= 2:
                try:
                    float(parts[0].replace(',', '.'))
                    float(parts[1].replace(',', '.'))
                    # Este separador funciona
                    break
                except ValueError:
                    continue
    else:
        sep = None  # Whitespace

    header_skipped = False
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if sep:
            parts = line.split(sep)
        else:
            parts = line.split()

        if len(parts) < 2:
            continue

        try:
            x = float(parts[0].replace(',', '.'))
            y = float(parts[1].replace(',', '.'))
            two_theta.append(x)
            intensities.append(y)
        except ValueError:
            if not header_skipped:
                header_skipped = True
                continue
            continue

    if not two_theta:
        raise ValueError(ptr("CSV: Nenhum dado numerico encontrado"))

    result_2theta = np.array(two_theta, dtype=float)
    result_intensity = np.array(intensities, dtype=float)

    logger.info(f"CSV: {len(result_intensity)} pontos, "
                f"2theta: {result_2theta[0]:.2f} - {result_2theta[-1]:.2f}")
    return result_2theta, result_intensity


def read_diffraction_file(file_path: str) -> tuple:
    """
    Função principal: detecta o formato e lê o arquivo de difração.

    Formatos suportados:
        .raw  - Shimadzu XRD / Bruker RAW (v1-v4)
        .brml - Bruker BRML (ZIP/XML)
        .xrdml - PANalytical XRDML
        .ras  - Rigaku RAS
        .csv  - CSV genérico
        .xy, .dat, .asc, .int, .txt - Texto com colunas

    Args:
        file_path: Caminho para o arquivo

    Returns:
        tuple: (two_theta_array, intensity_array) como arrays numpy
    """
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == '.raw':
            return read_raw_file(file_path)
        elif ext == '.brml':
            return read_brml_file(file_path)
        elif ext == '.xrdml':
            return read_xrdml_file(file_path)
        elif ext == '.ras':
            return read_ras_file(file_path)
        elif ext == '.csv':
            return read_csv_file(file_path)
        elif ext in ('.xy', '.dat', '.asc', '.int', '.txt', '.udf'):
            return _read_text_columns(file_path)
        else:
            # Tentar como texto primeiro, depois como binário
            try:
                return _read_text_columns(file_path)
            except ValueError:
                return read_raw_file(file_path)

    except Exception as e:
        raise ValueError(ptr("Erro ao ler '{}': {}").format(os.path.basename(file_path), e))


def _read_text_columns(file_path: str) -> tuple:
    """
    Lê arquivo texto com colunas (2theta, intensity, ...).
    Fallback para formatos texto genéricos.
    """
    two_theta = []
    intensities = []

    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(ptr("Nao foi possivel decodificar o arquivo"))

    for line in lines:
        parts = line.replace(',', ' ').strip().split()
        if not parts:
            continue
        try:
            vals = [float(p) for p in parts]
            if len(vals) >= 2:
                two_theta.append(vals[0])
                intensities.append(vals[1])
        except ValueError:
            continue

    if not two_theta:
        raise ValueError(ptr("Nenhum dado numerico encontrado"))

    result_2theta = np.array(two_theta, dtype=float)
    result_intensity = np.array(intensities, dtype=float)

    return result_2theta, result_intensity
