import csv
from statistics import median
import sys
from pathlib import Path
from store_processing import generate_color_synonyms, load_and_process_store_data
from supplier_processing import load_and_process_supplier_data
from matcher import match_supplier_to_store

def main():
    if len(sys.argv) < 3:
        print('Usage: python main.py <supplier_filename>.csv <store_filename>.csv')
        return
    filename_supplier = sys.argv[1]
    filename_store = sys.argv[2]
    print('Supplier filename:', filename_supplier)
    print('Store filename:', filename_store)

    color_synonyms = generate_color_synonyms(Path(filename_store))
    store_products = load_and_process_store_data(Path(filename_store), color_synonyms)
    supplier_products = load_and_process_supplier_data(Path(filename_supplier), color_synonyms)

    scores = []
    matches = match_supplier_to_store(supplier_products, store_products)
    for matched in matches:
        scores.append(matched.match_score)
    scores.sort()
    med = median(scores)

    print(f"Медиана: {med}\n{scores}")

    # Создаем словарь {код товара из магазина -> {название: ..., цены: [(цена, поставщик), ...]}}
    final_table = {}
    max_suppliers = 0
    for matched in matches:
        if matched.match_score >= med:
            store_product = matched.store_product
            supplier_product = matched.supplier_product

            code = store_product.code
            name = store_product.name
            price = supplier_product.price
            supplier_name = supplier_product.supplier_name

            # Если товара еще нет в таблице - создаем
            if code not in final_table:
                final_table[code] = {"name": name, "prices": []}

            # Добавляем цену и поставщика
            if (price, supplier_name) not in final_table[code]["prices"]:
                final_table[code]["prices"].append((price, supplier_name))

            max_suppliers = max(max_suppliers, len(final_table[code]["prices"]))
            
    # Подготавливаем данные к записи в CSV
    csv_data = []

    # Заголовки CSV
    headers = ["Код", "Название"]
    for i in range(1, max_suppliers + 1):
        headers.extend([f"Поставщик {i}", f"Цена {i}"])

    # Заполняем строки CSV
    for code, data in final_table.items():
        row = [code, data["name"]]
        
        # Сортируем цены от меньшей к большей
        sorted_prices = sorted(data["prices"], key=lambda x: x[0])

        # Добавляем цены и поставщиков в строку
        for price, supplier in sorted_prices:
            row.extend([supplier, price])

        # Дополняем пустыми значениями, если поставщиков меньше max_suppliers
        while len(row) < len(headers):
            row.append("")

        csv_data.append(row)

    # Записываем в CSV
    output_file = "final_prices.csv"
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(csv_data)

    print(f"\n✅ Итоговый CSV-файл сохранен как {output_file}")
if __name__ == '__main__':
    main()
