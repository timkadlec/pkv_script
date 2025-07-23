import unittest
from unittest.mock import patch
from script import is_dir, search_smb, compose_csv
import os


class TestSMBScanner(unittest.TestCase):

    @patch('script.smbclient.stat')
    def test_is_dir_true(self, mock_stat):
        """
            Testuj funkci is_dir - když vrátí True, je to složka.
        """
        mock_stat.return_value.st_mode = 0o040000 #složka
        self.assertTrue(is_dir('fake_path'))

    @patch('script.smbclient.stat')
    def test_is_dir_false(self, mock_stat):
        """
            Ověřuje, že funkce is_dir vrátí False, pokud se jedná o soubor.
            Simuluje cestu, která není adresářem, ale obyč souborem.
            Očekávaný výstup funkce is_dir je False == nejedná se o složku.
            """
        mock_stat.return_value.st_mode = 0o100644  #regular file
        self.assertFalse(is_dir('fake_file'))

    @patch('script.smbclient.stat')
    @patch('script.smbclient.listdir')
    def test_search_smb_empty_dir(self, mock_listdir, mock_stat):
        """
            Ověřuje, že funkce search_smb správně pozná prázdnou složku.

            Simuluje cestu, která neobsahuje žádné položky (listdir vrací prázdný list).
            Výsledkem by měl být jeden záznam s Flagem 'EMPTY'.
            """
        mock_listdir.return_value = []
        results = []
        search_smb('fake_path', results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['Flag'], 'EMPTY')

    @patch('script.smbclient.stat')
    @patch('script.smbclient.listdir')
    def test_search_smb_large_file(self, mock_listdir, mock_stat):
        """
            Ověřuje, že funkce search_smb označí soubor větší než 500 Mb Flagem 'EXCEEDED'.

            Simuluje složku o jednom souboru velikosti 600 Mb. Funkce by měla
            vrátit jeden záznam s Flagem 'EXCEEDED'.
        """
        mock_listdir.return_value = ['bigfile.txt']
        mock_stat.return_value.st_mode = 0o100644
        mock_stat.return_value.st_size = 600 * 1024 * 1024  # 600 Mb

        results = []
        search_smb('fake_path', results)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['Flag'], 'EXCEEDED')

    def test_compose_csv(self):
        """
            Ověřuje, že funkce compose_csv správně vytvoří CSV soubor ze záznamy.

            Vytvoří ukázkový seznam výsledků, zavolá compose_csv a následně zkontroluje,
            že výstupní soubor obsahuje tři řádky.
            Na závěr test po sobě uklidí a soubor smaže.
            """
        sample_results = [
            {"Path": "a", "Name": "A", "Flag": "EMPTY"},
            {"Path": "b", "Name": "B", "Flag": "EXCEEDED"}
        ]
        output_path = "test_output.csv"
        compose_csv(sample_results, output_path)

        with open(output_path, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)

        os.remove(output_path)  # uklidíme po sobě
