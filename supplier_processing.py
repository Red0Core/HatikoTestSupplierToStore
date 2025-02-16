import csv
from locale import normalize
from os import name
from pathlib import Path
import re

from csv_processing import find_delimiter
from store_processing import BRAND_SYNONYMS, generate_keywords

class SupplierProduct:
    def __init__(self, name: str, brand: str, model: str, supplier_name: str, synonyms: set[str],
                 price: int, ram: int | None = None, storage: int | None = None, color: str | None = None):
        self.model = model
        self.supplier_name = supplier_name
        self.price = price
        self.ram = ram
        self.storage = storage
        self.color = color
        self.name = name
        self.synonyms = synonyms
        self.brand = brand
    
    def __repr__(self):
        return f"SupplierProduct(name='{self.name}', model='{self.model}', brand='{self.brand}', supplier_name='{self.supplier_name}', " \
               f"price={self.price}, ram={self.ram}, storage={self.storage}, color={self.color}, synonyms={self.synonyms})"
    
    def __dict__(self) -> dict:
        return {
            "model": self.model,
            "supplier_name": self.supplier_name,
            "price": self.price,
            "ram": self.ram,
            "storage": self.storage,
            "color": self.color,
            "synonyms": list(self.synonyms),
            "name": self.name,
            "brand": self.brand
        }


def extract_brand_or_model(text):
    """
    Извлекает бренд или модель из строки, если нет кириллических символов, цены и имеет странные разделители в двух сторонах.
    """
    pattern = re.compile(r"^(?!.*[а-яА-Я]+)(?!.*\d+\s?[₽$€])[\W]+\s*([\w\d\s]+?)\s*[\W]+$")
    match = pattern.match(text)

    if match:
        return match.group(1).strip().lower()
    return None

def normalize_model(model):
    """Удаляет не ASCII символы и приводит строку к стандартному виду."""
    model = re.sub(r"[^\w\s\-/]", "", model)  # Убираем спецсимволы
    return model.strip()

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
    match = re.search(r"(\d{1,2})\s?[/\\+\- ]\s?(\d{2,4})[GBgb]*", text)  # Ищем "8/256gb", "8+256GB"
    if match:
        ram = int(match.group(1))
        storage = int(match.group(2))
        replacer_str = f"{ram}/{str(storage) + "GB" if storage < 1000 else '1TB'}" # Заменяем на "8/256GB" или "8/1TB"
        model = text.replace(match.group(0), replacer_str).strip()
        return model, replacer_str, ram, storage
    return text, "", None, None

def map_supplier_color_to_store(supplier_color: str, store_color_synonyms: dict[str, set[str]]) -> str | None:
    """Сопоставляет цвет поставщика со словарем магазина."""""
    supplier_color = supplier_color.lower()
    for russian_color, synonyms in store_color_synonyms.items():
        if supplier_color in synonyms:
            return russian_color
    return None

def extract_color(text: str, store_color_synonyms: dict[str, set[str]]) -> tuple[str, str | None]:
    """Ищет цвет в названии и приводит его к стандартному формату магазина."""
    for russian_color, synonyms in store_color_synonyms.items():
        # В приоритете более длинные цвета, так как black и black stormy могут быть в тексте
        sorted_synonyms = sorted(synonyms, key=len, reverse=True)
        for color in sorted_synonyms:
            if color in text.lower():
                return text.lower().replace(color, "").strip(), russian_color
    return text, None

def normalize_brand(brand: str) -> str:
    """Приводит бренд к стандартному написанию из BRAND_SYNONYMS."""
    for key_brand, variations in BRAND_SYNONYMS.items():
        if brand in variations:
            return key_brand
    return brand

def detect_brand_from_model(model: str) -> str | None:
    """Определяет бренд из модели, используя BRAND_SYNONYMS."""
    for brand in BRAND_SYNONYMS:
        if brand in model:
            return brand
    return None  # Если бренд не найден

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
    with open(file_path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimeter)
        for row in reader:
            if len(row) < 2:
                continue

            product_name = row[0].strip().lower().replace("pro + ", "pro+ ").replace("pro+ ", "pro plus ").replace('-','')
            supplier_name = row[1].strip()

            # Проверяем, является ли строка заголовком бренда
            match = extract_brand_or_model(product_name)
            if match:
                current_brand = normalize_brand(match)  # Запоминаем бренд
                continue
            
            detected_brand = detect_brand_from_model(product_name)

            # Если модель уже содержит какой-то бренд, используем его как `current_brand`
            if detected_brand:
                current_brand = detected_brand

            # Извлекаем цену
            model, price = extract_price(product_name)

            if price is None or '[' in model:
                continue  # Пропускаем мусор

            # Извлекаем RAM и Storage и приводит к единому формату
            model, replace_ram_storage, ram, storage = extract_memory(model)
            product_name = model # Обновляем название товара к унифицированному
            model = model.replace(replace_ram_storage, "")  # Убираем RAM и Storage из модели
            # Отделяем цвет (если есть)
            model, supplier_color = extract_color(model, store_color_synonyms)

            # Очищаем модель и имя
            model = normalize_model(model)
            product_name = normalize_model(product_name)

            # Если бренд найден ранее, добавляем его к модели при условии, что в имени нет любого другого бренда
            if current_brand:
                for orig_brand, variations in BRAND_SYNONYMS.items():
                    if current_brand in variations:
                        current_brand = orig_brand
                        break

                if current_brand not in model:
                    model = f"{current_brand} {model}"
                if current_brand not in product_name:
                    product_name = f"{current_brand} {product_name}"

            if current_brand == "xiaomi" and "note" in model and "redmi" not in model:
                model = model.replace("xiaomi", "xiaomi redmi")  # Автоматически добавляем Redmi, если модель xiaomi note..
                product_name = product_name.replace("xiaomi", "xiaomi redmi")

            product_name = ' '.join(product_name.split()) # Убираем лишние пробелы
            model = ' '.join(model.split()) # Убираем лишние пробелы

            # Генерируем ключевые слова
            keywords = generate_keywords(product_name, store_color_synonyms, ram, storage, supplier_color)

            # Добавляем обработанный товар
            supplier_data.append(SupplierProduct(product_name, current_brand, model,
                                                 supplier_name, keywords, price, ram, storage, supplier_color))

    return supplier_data
