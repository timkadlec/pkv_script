import os, stat
from dotenv import load_dotenv
import smbclient
import csv

load_dotenv()


def get_smb_path():
    smb_username = os.getenv('SMB_USERNAME')
    smb_password = os.getenv('SMB_PASSWORD')
    smb_server = os.getenv('SMB_SERVER')

    smbclient.register_session(server=smb_server, username=smb_username, password=smb_password)

    return f"\\\\{smb_server}\\pkv_share"


def is_dir(path):
    """
    Ověř, zda daná SMB cesta je složka.

    Parameters:
    ----------
    path: str
        Absolutní SMB cesta k položce, jejíž typ se má ověřit.

    Returns:
    ------------------
    bool
        Vrací True, pokud je cesta platná a odkazuje na složku.
        Vrací False v případě, že:
            - je cesta neplatná nebo nepřístupná,
            - dojde k chybě při dotazu na metadata,
            - nebo jde o běžný soubor.
    """
    try:
        return stat.S_ISDIR(smbclient.stat(path).st_mode)
    except Exception as e:
        print(f"Chyba u souboru {path}: {e}")
        return False


def search_smb(path, results):
    """
    Prohledej SMB

    Rekurzivní procházení dané cesty SMB shromažďování informací o prázdných složkách
    a souborech, jejichž velikost je větší než 500 Mb.

    Parameters
    ----------
    path: str
        Absolutní SMB path k aktuálně zpracovávané složce (např. "\\\\server\\share\\folder").

    results: list of dict
        List of dictionaries, do kterého se přidávají výsledky nalezené v průběhu rekurze.
        Každý záznam má strukturu:
            {
                "Path": <celá cesta k souboru nebo složce>,
                "Name": <název položky>,
                "Flag": "EMPTY" nebo "EXCEEDED"
            }

    Behaviour
    --------
    - Pokud složka neobsahuje žádné položky, je "EMPTY".
    - Pokud je nalezený soubor větší než 500 Mb, je "EXCEEDED".
    - Ostatní soubory a složky jsou ignorovány.

    Exceptions
    --------
    Pokud dojde k chybě při volání `smbclient.stat()`, položka je přeskočena
    a chyba je vypsána.

    Example
    ----------------
    results = []
    search_smb("\\\\localhost\\shared", results)
    """

    items = smbclient.listdir(path)
    if not items:
        results.append({"Path": path, "Name": os.path.basename(path), "Flag": "EMPTY"})
        return
    for item in items:
        full_path = os.path.join(path, item).replace("/", "\\")
        try:
            st = smbclient.stat(full_path)
        except Exception as e:
            print(f"Chyba u souboru {full_path}: {e}")
            continue
        if is_dir(full_path):
            search_smb(full_path, results)
        else:
            if st.st_size > 500 * 1024 * 1024:  # 500 MB
                results.append({"Path": full_path, "Name": item, "Flag": "EXCEEDED"})


def compose_csv(results, output_file):
    """
    Vytvoř csv soubor ze seznamu výsledků.

    Parameters
    ----------
    results : list of dict
        Každý dict představuje jeden řádek v CSV.
        Předpokládané klíče: "Path", "Name", "Flag".

    output_file : str
        Výsledný cesta k CSV souboru.

    Returns
    -------
    CSV soubor se záhlavím a řádky odpovídajícími obsahu `results`.
    Každý řádek reprezentuje nalezený soubor nebo složku v rámci SMB
    s příznakem "EMPTY" nebo "EXCEEDED".

    Examples
    --------
    compose_csv(results, "static/output.csv")
    """
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Path", "Name", "Flag"])
        writer.writeheader()
        writer.writerows(results)


if __name__ == '__main__':
    smb_path = get_smb_path()
    results = []

    # Projdi složky a soubory
    search_smb(smb_path, results)

    # Seřaď výsledky podle Flag
    results.sort(key=lambda x: x["Flag"])

    # Vytvoř csv
    compose_csv(results, output_file="static/output.csv")
