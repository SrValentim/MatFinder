import os
from mp_api.client import MPRester
import traceback

# --- Configuração da Chave API ---
API_KEY_ENV_VAR = "MP_API_KEY"

# --- ALTERAÇÃO DE REATORAÇÃO: Caminho do Ficheiro de Config ---
# Aponta para o novo local do ficheiro, dentro da pasta 'assets'
API_KEY_FILE = "../matfinder/assets/config/config_console_test.txt"
# --- FIM DA ALTERAÇÃO ---


def get_api_key(provided_key=None):
    """Obtém a chave da API de uma chave fornecida, variáveis de ambiente, arquivo ou input do usuário."""
    if provided_key and len(provided_key) == 32:
        print(f"Chave API fornecida diretamente para a função.")
        return provided_key

    api_key = os.getenv(API_KEY_ENV_VAR)
    if api_key:
        print(f"Chave API carregada da variável de ambiente {API_KEY_ENV_VAR}.")
        return api_key

    try:
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, "r") as f:
                api_key = f.readline().strip()
                if api_key and len(api_key) == 32:
                    print(f"Chave API carregada do arquivo {API_KEY_FILE}.")
                    return api_key
                else:
                    print(f"Chave API no arquivo {API_KEY_FILE} é inválida. Ignorando.")
    except Exception as e:
        print(f"Erro ao ler chave do arquivo {API_KEY_FILE}: {e}")

    while True:
        api_key = input("Por favor, insira sua chave da API do Materials Project (32 caracteres): ").strip()
        if api_key and len(api_key) == 32:
            try:
                with open(API_KEY_FILE, "w") as f:
                    f.write(api_key)
                print(f"Chave API salva em {API_KEY_FILE} para uso futuro.")
            except Exception as e:
                print(f"Aviso: Não foi possível salvar a chave API em {API_KEY_FILE}: {e}")
            return api_key
        else:
            print("Chave API inválida. Deve ter 32 caracteres.")


def fetch_material_icsd_ids(material_id: str, api_key: str):
    """
    Busca e imprime os códigos ICSD para um dado ID de material.
    """
    print(f"\nBuscando dados para o material ID: {material_id}...")
    if not api_key or len(api_key) != 32:
        print("Erro: Chave API inválida ou não fornecida para fetch_material_icsd_ids.")
        return

    try:
        with MPRester(api_key=api_key) as mpr:
            docs = mpr.materials.summary.search(
                material_ids=[material_id],
                fields=["database_IDs", "formula_pretty", "material_id"]
            )

            if not docs:
                print(f"Material com ID '{material_id}' não encontrado.")
                return

            material_doc = docs[0]
            formula = material_doc.formula_pretty
            retrieved_material_id = material_doc.material_id
            print(f"Material encontrado: {formula} (ID: {retrieved_material_id})")

            icsd_codes_full_str = []  # Para armazenar "icsd-XXXXX"

            # O campo database_IDs é um objeto, mas quando convertido para dict via model_dump()
            # ou acessado como dict, ele tem chaves como 'icsd'.
            if material_doc.database_IDs:
                # O objeto DatabaseIDs pode ser convertido para um dicionário
                db_ids_dict = {}
                if hasattr(material_doc.database_IDs, 'model_dump'):  # Preferencial para Pydantic V2+
                    db_ids_dict = material_doc.database_IDs.model_dump(exclude_none=True)
                elif isinstance(material_doc.database_IDs, dict):  # Fallback se já for um dict
                    db_ids_dict = material_doc.database_IDs
                else:  # Tentar converter para dict se for um objeto Pydantic V1
                    try:
                        db_ids_dict = material_doc.database_IDs.dict(exclude_none=True)
                    except AttributeError:
                        print(f"  AVISO: Não foi possível converter database_IDs para dict para {material_id}.")

                print(
                    f"  Conteúdo de 'database_IDs' (após conversão para dict se necessário): {db_ids_dict}")  # Para depuração

                # Agora acessamos a chave 'icsd' no dicionário
                raw_icsd_list = db_ids_dict.get('icsd')  # Retorna None se a chave 'icsd' não existir

                print(f"  Valor de 'database_IDs.get('icsd')': {raw_icsd_list} (Tipo: {type(raw_icsd_list)})")

                if raw_icsd_list is not None:
                    if isinstance(raw_icsd_list, list):
                        if raw_icsd_list:
                            # Os códigos já vêm como "icsd-XXXXX"
                            icsd_codes_full_str = [str(code) for code in raw_icsd_list]
                        else:
                            print(f"  A chave 'icsd' está presente em database_IDs mas a lista de códigos está vazia.")
                    else:
                        print(
                            f"  AVISO: O valor da chave 'icsd' em database_IDs não é uma lista. Tipo: {type(raw_icsd_list)}, Valor: {raw_icsd_list}")
                else:
                    print(f"  A chave 'icsd' não foi encontrada em database_IDs ou seu valor é None.")
            else:
                print(f"  Campo 'database_IDs' não encontrado ou é None no documento do material.")

            if icsd_codes_full_str:
                print(f"\n  Códigos ICSD (formato 'icsd-XXXXX') encontrados para {formula} ({retrieved_material_id}):")
                for code_full in icsd_codes_full_str:
                    print(f"    - {code_full}")
                    # Extrair apenas o número para a URL do FIZ
                    numeric_part = code_full.replace("icsd-", "")
                    if numeric_part.isdigit():
                        print(f"      Link FIZ: https://icsd.fiz-karlsruhe.de/linkicsd.xhtml?coll_code={numeric_part}")
                    else:
                        print(f"      Não foi possível extrair o número do código: {code_full}")

            else:
                print(f"\n  Nenhum código ICSD encontrado ou processado para {formula} ({retrieved_material_id}).")

    except Exception as e:
        print(f"\nOcorreu um erro ao buscar dados do Materials Project:")
        print(f"  Tipo de Erro: {type(e).__name__}")
        print(f"  Mensagem: {e}")
        print("  Traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    user_provided_api_key = "JRMb12mbrwJC2q8fZxHqATIO1bWgf0ip"
    print(f"Utilizando a chave API fornecida diretamente: {user_provided_api_key[:5]}...")

    if not user_provided_api_key or len(user_provided_api_key) != 32:
        print("A chave API fornecida diretamente é inválida. Verifique a chave.")
    else:
        target_material_id = "mp-20243"
        fetch_material_icsd_ids(target_material_id, user_provided_api_key)

        print("\n--- Fim do Teste ---")