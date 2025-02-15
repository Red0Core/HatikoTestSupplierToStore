import csv
from pathlib import Path

def find_delimiter(path: Path) -> str:
    sniffer = csv.Sniffer()
    with open(path, encoding='utf-8') as fp:
        delimiter = sniffer.sniff(fp.read(5000)).delimiter
    return delimiter
