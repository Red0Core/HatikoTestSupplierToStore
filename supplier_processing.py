import csv
from pathlib import Path
import re

from csv_processing import find_delimiter
from store_processing import BRAND_SYNONYMS, generate_keywords

class SupplierProduct:
    def __init__(self, model: str, supplier_name: str, synonyms: set[str],
                 price: int, ram: int | None = None, storage: int | None = None, color: str | None = None):
        self.model = model
        self.supplier_name = supplier_name
        self.price = price
        self.ram = ram
        self.storage = storage
        self.synonyms = synonyms
    
    def __repr__(self):
        return f"SupplierProduct(model='{self.model}', supplier_name='{self.supplier_name}', " \
               f"price={self.price}, ram={self.ram}, storage={self.storage}, keywords={self.synonyms})"

def extract_brand_or_model(text):
    """
    Извлекает бренд или модель из строки, если нет кириллических символов, цены и имеет странные разделители в двух сторонах.
    """
    pattern = re.compile(r"^(?!.*[а-яА-Я]+)(?!.*\d+\s?[₽$€])[\W]+\s*([\w\d\s]+?)\s*[\W]+$")
    match = pattern.match(text)

    if match:
        return match.group(1).strip().lower()
    return None

def normolize_model(model):
    """Убирает все не ASCII символы из строки"""
    return ''.join([i if ord(i) < 128 else '' for i in model]).strip(" -")

def extract_price(text: str):
    """Извлекает цену, если она есть в конце строки"""
    match = re.search(r"(\d{4,6})\s?[₽$€]?", text)  # Ищем число 4-6 цифр в конце
    if match:
        price = int(match.group(1))  # Преобразуем в число
        model = text[: match.start()].strip()  # Убираем цену из модели
        return model, price
    return text, None

def extract_memory(text: str):
    """Убирает объем RAM и Storage из текста"""
    if "tb" in text.lower(): # Меняем терабайты на гигабайты
        text.replace("tb", "024GB").replace("TB", "024GB")
    match = re.search(r"(\d{1,2})\s?[/\\+\-]\s?(\d{2,4})", text)  # Ищем "8/256", "8+256"
    if match:
        ram = int(match.group(1))
        storage = int(match.group(2))
        replacer_str = f"{ram}/{str(storage) + 'GB' if storage < 1000 else '1TB'}" # Заменяем на "8/256GB" или "8/1TB"
        model = text.replace(match.group(0), replacer_str).strip()
        return model, ram, storage
    return text, None, None

def extract_from_color_synonyms_all_english_colors(store_color_synonyms: dict[str, set[str]]) -> set[str]:
    """Извлекает все английские цвета из словаря магазина"""
    english_synonyms = set()
    for synonyms in store_color_synonyms.values():
        for color in synonyms:
            if all(ord('a') <= ord(ch) <= ord('z') for ch in color.lower()):
                english_synonyms.add(color)
    return english_synonyms

def map_supplier_color_to_store(supplier_color: str, store_color_synonyms: dict[str, set[str]]) -> str | None:
    """
    Ищет английский цвет поставщика в словаре магазина и возвращает его русский эквивалент.
    Если совпадение не найдено, возвращает None.
    """
    supplier_color = supplier_color.lower()

    for russian_color, synonyms in store_color_synonyms.items():
        if supplier_color in synonyms:
            return russian_color  # Возвращаем русский цвет из магазина

    return None  # Если цвет не найден

def load_and_process_supplier_data(file_path, store_color_synonyms):
    """
    Загружает, очищает и обрабатывает данные поставщиков.
    - Определяет текущий бренд (например, "📱SAMSUNG📱").
    - Извлекает модель, цену, RAM, Storage, цвет.
    - Приводит цвет к формату магазина через словарь `store_color_synonyms`.
    """
    delimeter = find_delimiter(file_path)
    supplier_data: list[SupplierProduct] = []
    current_brand = None
    all_english_colors = extract_from_color_synonyms_all_english_colors(store_color_synonyms)
    with open(file_path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimeter)
        for row in reader:
            if len(row) < 2:
                continue

            product_name = row[0].strip().lower()
            supplier_name = row[1].strip().lower()

            # Проверяем, является ли строка заголовком бренда
            match = extract_brand_or_model(product_name)
            if match:
                current_brand = match  # Запоминаем бренд
                continue

            # Извлекаем цену
            model, price = extract_price(product_name)

            if price is None:
                continue  # Пропускаем мусор

            # Извлекаем RAM и Storage
            model, ram, storage = extract_memory(model)

            # Извлекаем цвет (если есть)
            supplier_color = None
            for color in all_english_colors:
                if color in model.lower():
                    supplier_color = color
                    break

            # Приводим цвет к русскому варианту из магазина
            store_color = map_supplier_color_to_store(supplier_color, store_color_synonyms) if supplier_color else None

            # Очищаем модель
            model = normolize_model(model)

            # Если бренд найден ранее, добавляем его к модели
            if current_brand and not any(brand in model for brand in BRAND_SYNONYMS):
                model = f"{current_brand} {model}"

            # Генерируем ключевые слова
            keywords = generate_keywords(model, store_color_synonyms, ram, storage, store_color)

            # Добавляем обработанный товар
            supplier_data.append(SupplierProduct(model, supplier_name, keywords, price, ram, storage, store_color))

    return supplier_data
