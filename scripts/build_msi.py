# build_msi.py
# Este script usa a biblioteca padrão msilib para criar um instalador MSI
# a partir do resultado da compilação do PyInstaller na pasta 'dist/MatFinder'.
# Este script DEVE ser executado DEPOIS do PyInstaller.
#
# CAMINHO REFATORADO: MatFinder/scripts/build_msi.py
#

import os
import msilib
from msilib import schema, sequence
from uuid import uuid4

# --- INÍCIO DA CONFIGURAÇÃO ---
# Nome da empresa/desenvolvedor
MANUFACTURER = "LabMat"

# Nome do seu aplicativo
APP_NAME = "MatFinder"
# Versão do seu aplicativo. IMPORTANTE: O MSI armazena em cache com base na versão.
# Mude a versão a cada nova compilação para garantir que a atualização funcione.
APP_VERSION = "3.23.0"

# --- ALTERAÇÃO DE REATORAÇÃO 1: Nome do Executável ---
# Atualizado para corresponder ao 'target_name' do setup.py
APP_EXECUTABLE = f"{APP_NAME}.exe"

# --- ALTERAÇÃO DE REATORAÇÃO 2: Caminho de Entrada (dist) ---
# Adiciona '..' para subir um nível (de 'scripts/' para a raiz)
PYINSTALLER_OUTPUT_DIR = os.path.join('..', 'dist', APP_NAME)

# --- ALTERAÇÃO DE REATORAÇÃO 3: Caminho de Saída (.msi) ---
# Adiciona '..' para salvar o .msi na pasta raiz, e não em 'scripts/'
MSI_OUTPUT_FILE = os.path.join('..', f'{APP_NAME}-{APP_VERSION}.msi')

# UUIDs: Gerados uma vez para o seu projeto. Não os altere depois.
# Você pode gerar novos UUIDs usando `import uuid; print(uuid.uuid4())`
UPGRADE_CODE = '{1b2c4d5e-6f78-4a9b-8c0d-1e2f3a4b5c6d}'


# --- FIM DA CONFIGURAÇÃO ---


def create_msi():
    """Função principal para criar o instalador MSI."""

    # Validação: Verifica se a pasta de saída do PyInstaller existe
    if not os.path.exists(PYINSTALLER_OUTPUT_DIR):
        print(f"ERRO: A pasta de compilação '{PYINSTALLER_OUTPUT_DIR}' não foi encontrada.")
        print("Certifique-se de executar o PyInstaller antes deste script.")
        print(f"(Caminho procurado: {os.path.abspath(PYINSTALLER_OUTPUT_DIR)})")
        return

    print(f"Iniciando a criação do instalador MSI para {APP_NAME} v{APP_VERSION}...")

    # Estrutura do diretório no instalador
    # Geralmente: ProgramFilesFolder -> ManufacturerFolder -> AppFolder
    dir_structure = [
        ("TARGETDIR", "SourceDir", "."),
        ("ProgramFilesFolder", "TARGETDIR", "PFiles"),
        (f"{MANUFACTURER}Folder", "ProgramFilesFolder", MANUFACTURER[:10]),
        ("APPDIR", f"{MANUFACTURER}Folder", APP_NAME[:10]),
    ]

    # Coletar todos os arquivos da pasta de saída do PyInstaller
    files_to_add = []
    component_id_map = {}
    root_dir = os.path.abspath(PYINSTALLER_OUTPUT_DIR)

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            # O caminho relativo é necessário para a estrutura do MSI
            relative_path = os.path.relpath(full_path, root_dir)

            # Cada arquivo precisa de um ID de componente único
            # ComponentId deve ser um identificador válido (sem hífens, começando com letra)
            file_id = "file_" + os.path.normpath(relative_path).replace(os.sep, '_').replace('-', '_').replace('.', '_')
            component_id = "comp_" + file_id

            files_to_add.append((file_id, component_id, relative_path, full_path))
            component_id_map[component_id] = str(uuid4())

    # ID do componente para o atalho
    shortcut_component_id = "ShortcutComponent"
    component_id_map[shortcut_component_id] = str(uuid4())

    # Inicia a criação do banco de dados MSI
    db = msilib.init_database(
        MSI_OUTPUT_FILE,
        schema,
        f"{APP_NAME} v{APP_VERSION} Installer",
        f"{APP_NAME}",
        APP_VERSION,
        MANUFACTURER,
    )

    msilib.add_tables(db, sequence)

    # Propriedades do instalador
    msilib.add_data(db, 'Property', [
        ('ALLUSERS', '1'),
        ('MSIINSTALLPERUSER', ''),
        ('UpgradeCode', UPGRADE_CODE),
        ('Manufacturer', MANUFACTURER),
        ('ProductName', APP_NAME),
        ('ProductVersion', APP_VERSION),
    ])

    # Adiciona a estrutura de diretórios ao banco de dados
    cab = msilib.FCICreate(f'{APP_NAME}.cab')
    msilib.add_data(db, 'Directory', dir_structure)

    # Adiciona os componentes (arquivos e atalhos)
    feature_components = []

    print(f"Adicionando {len(files_to_add)} arquivos ao MSI...")
    file_count = 0

    # Verifica se o executável principal está na lista
    main_exe_file_id = None

    for file_id, component_id, relative_path, full_path in files_to_add:
        # Adiciona o arquivo ao arquivo CAB
        cab.add_file(full_path, relative_path)

        # Adiciona a entrada do arquivo ao banco de dados MSI
        msilib.add_data(db, 'File', [(file_id, component_id, relative_path, 0, os.path.getsize(full_path), None)])

        # Adiciona a entrada do componente ao banco de dados MSI
        # O último parâmetro é o KeyPath (arquivo chave do componente)
        msilib.add_data(db, 'Component', [(component_id, component_id_map[component_id], "APPDIR", 0, None, file_id)])

        feature_components.append((f"feat_{component_id}", component_id))
        file_count += 1

        # Armazena o file_id do executável principal
        if relative_path == APP_EXECUTABLE:
            main_exe_file_id = file_id

    print(f"{file_count} arquivos adicionados.")
    cab.commit(db)

    # Verifica se o executável foi encontrado
    if not main_exe_file_id:
        print(f"ERRO CRÍTICO: O executável principal '{APP_EXECUTABLE}' não foi encontrado na pasta de build.")
        print("O atalho não será criado.")
    else:
        # Cria o atalho no Menu Iniciar
        print("Criando atalho...")
        msilib.add_data(db, 'Component',
                        [(shortcut_component_id, component_id_map[shortcut_component_id], "APPDIR", 0, None, None)])

        msilib.add_data(db, 'Shortcut', [
            ('AppShortcut', 'ProgramMenuFolder', f'MatFinder', shortcut_component_id, main_exe_file_id, None, None,
             None,
             None, None, None)
        ])
        feature_components.append(("feat_Shortcut", shortcut_component_id))

    # Define a "Feature" principal, que agrupa todos os componentes
    msilib.add_data(db, 'Feature', [('MainFeature', '', 'Instala o MatFinder', 1, 1, 'APPDIR')])
    msilib.add_data(db, 'FeatureComponents', [('MainFeature', comp[1]) for comp in feature_components])

    # Lógica de atualização (remove versões antigas)
    msilib.add_data(db, 'Upgrade', [
        (UPGRADE_CODE, None, APP_VERSION, None, 513, None, 'REMOVEOLD'),
        (UPGRADE_CODE, APP_VERSION, None, None, 257, None, 'REMOVENEW'),
    ])

    # Ações da sequência de instalação
    msilib.add_data(db, 'InstallExecuteSequence', [
        ('RemoveExistingProducts', 'VersionNT AND UPGRADECODEFOUND', 1400),
        ('FindRelatedProducts', 'VersionNT', 400),
    ])

    db.Commit()
    print(f"\nInstalador '{os.path.abspath(MSI_OUTPUT_FILE)}' criado com sucesso!")


if __name__ == '__main__':
    create_msi()