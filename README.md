
# Dokumentace

## Význam

Skript slouží k procházení sdílené SMB složky a vytváření souboru CSV podle dvou zadaných kritérií:

- **prázdné složky** (označí jako `EMPTY`)
- **soubory větší než 500 Mb** (označí jako `EXCEEDED`)

Výsledkem je CSV soubor s třemi sloupci: `Path`, `Name`, `Flag` seřazený podle `Flag`.

---

## Použité technologie

- Připojení k SMB sdílené složce pomocí knihovny `smbclient`
- Bezpečné prostředí (`.env`) pro uložení přihlašovacích údajů k SMB
- Rekurzivní průchod složkou a vyhodnocení stavu každého objektu
- Export výsledků do `.csv` pomocí knihovny `csv`

---

## Popis funkcí

### `is_dir(path)`
Zjišťuje, zda daná cesta na SMB vede na složku.

- Pokud ano → vrací `True`
- Pokud ne nebo nastane chyba (např. nedostupná cesta) → vrací `False`
- Případné chyby vypisuje v konzoli

---

### `search_smb(path, results)`
Rekurzivně projde zadanou složku a hledá:

1. **Prázdné složky** – pokud `listdir(xxx)` vrátí prázdný seznam, přidá se do výsledků záznam s flag: `EMPTY`.
2. **Velké soubory** – pokud velikost souboru překročí 500 Mb, přidá se záznam s flag: `EXCEEDED`.

Každý záznam je uložen jako dictionary do listu `results`:
```python
{
    "Path": "...",  # celá cesta k souboru/složce
    "Name": "...",  # název položky
    "Flag": "EMPTY" nebo "EXCEEDED"
}
```

---

### `compose_csv(results, output_file)`
Vytvoří CSV soubor z výsledků.

- Zapisuje sloupce `Path`, `Name`, `Flag`
- Soubor se vytváří ve formátu UTF-8 a a je přepisován, pokud existuje

---

## Hlavní skript

V `if __name__ == '__main__':` proběhne skript:

1. Načte přihlašovací údaje ze souboru `.env`
2. Připojí se k SMB
3. Spustí prohledání složek pomocí `search_smb(...)`
4. Výsledky seřadí podle `Flag` (nejdřív `EMPTY`, pak `EXCEEDED`)
5. Výsledky zapíše do CSV souboru `static/output.csv` (složka static musí existovat!)

---

## Výstup CSV

CSV soubor bude obsahovat např.:

| Path                                     | Name        | Flag      |
|------------------------------------------|-------------|-----------|
| `\\192.168.1.10\pkv_share\prazdna_slozka` | prazdna_slozka | EMPTY     |
| `\\192.168.1.10\pkv_share\film.mkv`      | film.mkv    | EXCEEDED  |

---

## Co je potřeba mít připraveno

- `.env` soubor s přihlašovacími údaji:
  ```
  SMB_SERVER=192.168.1.10
  SMB_USERNAME=uzivatel
  SMB_PASSWORD=heslo
  ```
- Sdílená složka musí být dostupná z vašeho počítače a správně nasdílená (např. `pkv_share`)
- Nainstalované pluginy z `requirements.txt`

---

## Spuštění

```bash
python script.py
```

Výsledný vygenerovaný soubor se nachází ve složce `static/output.csv`.

## Testování

Projekt obsahuje testy v `test_smbscanner.py`. Testy ověřují  funkce skriptu bez nutnosti připojení k  SMB serveru – díky použití mocking (`unittest.mock`).

### Přehled testovaných funkcí

| Testovací metoda                 | Co ověřuje                                                             |
|----------------------------------|-------------------------------------------------------------------------|
| `test_is_dir_true()`             | Funkce `is_dir` vrátí `True`, pokud zadaná cesta odkazuje na složku     |
| `test_is_dir_false()`            | Funkce `is_dir` vrátí `False`, pokud cesta vede na soubor          |
| `test_search_smb_empty_dir()`    | Funkce `search_smb` identifikuje prázdnou složku (`EMPTY`)        |
| `test_search_smb_large_file()`   | Funkce `search_smb` označí soubor větší než 500 MB (`EXCEEDED`)   |
| `test_compose_csv()`             | Funkce `compose_csv` vytvoří CSV soubor s očekávaným počtem řádků |

> Všechny testy používají `patch` pro nahrazení skutečných volání `smbclient.stat()` a `smbclient.listdir()` testovacími daty.

---

### Spuštění testů

Nejprve se ujistěte, že máte nainstalovaný `pytest`, ostatně je zohledněno v `requirements.txt`:

```bash
pip install pytest
```

Test spouštíme následujícím příkazem s příznakem `-v` verbose:
```bash
pytest -v test_smbscanner.py
```
Testy používají unittest a unittest.mock, nevyžadují připojení k SMB serveru ani .env soubor.