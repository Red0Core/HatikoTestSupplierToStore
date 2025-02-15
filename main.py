import sys
from pathlib import Path
from pprint import pprint
from store_processing import generate_product_synonyms

def main():
    if len(sys.argv) < 3:
        print('Usage: python main.py <supplier_filename>.csv <store_filename>.csv')
        return
    filename_supplier = sys.argv[1]
    filename_store = sys.argv[2]
    print('Supplier filename:', filename_supplier)
    print('Store filename:', filename_store)

    for name, synonyms in generate_product_synonyms(Path(filename_store)).items():
        print(f"Product: {name} -> Synonyms: {synonyms}\n")

if __name__ == '__main__':
    main()
