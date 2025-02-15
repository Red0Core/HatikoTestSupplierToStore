import csv
from pathlib import Path
import re

from csv_processing import find_delimiter

class StoreProduct:
    def __init__(self, name: str, synonyms: set[str], code: str,
                 ram: int | None = None, storage: int | None = None) -> None:
        self.name = name
        self.synonyms = synonyms
        self.code = code
        self.ram = ram
        self.storage = storage

    def __repr__(self) -> str:
        return f"StoreProduct(name='{self.name}', code='{self.code}', " \
               f"ram={self.ram}, storage={self.storage}, synonyms={self.synonyms})"

BRAND_SYNONYMS = {
        "xiaomi": ["mi", "redmi", "poco", "сяоми", "ксиаоми"],
        "samsung": ["galaxy", "note", "a", "s", "m", "tab", "самсунг", "гелекси", "гэлэкси"],
        "iphone": ["se", "xr", "x", "xs", "max", "pro", "plus", "айфон"],
        "ipad": ["pro", "mini", "air", "айпад"],
        "imac": ["pro", "аймак"],
        "macbook": ["pro", "air", "макбук"],
        "apple": ["watch", "airpods", "iphone", "ipad", "macbook", "imac", "эпл", "эппл", "айпад", "айфон", "аймак", "макбук"],
        "huawei": ["p", "mate", "nova", "y", "pura", "хуавей", "хуавэй"],
        "microsoft": ["surface", "майкрософт"],
        "realme": ["c", "narzo", "x", "gt", "реалми", "реалме", "реалмэ", "рилми"],
        "tecno": ["camon", "spark", "phantom", "текно", "техно"],
        "vivo": ["y", "v", "x", "iqoo", "виво"],
        "asus": ["rog", "zenfone", "асус"],
        "blackview": ["active", "tab", "блэквью"],
        "google": ["pixel", "tablet", "xl", "гугл"],
        "honor": ["pad", "magic", "pro", "x", "хонор"],
        "infinix": ["hot", "note", "zero", "smart", "инфиникс"],
        "itel": ["a", "vision", "ител"],
        "motorola": ["moto", "razr", "моторола"],
        "nothing": ["phone", "cmf", "нотхинг", "нофинг"],
        "oneplus": ["nord", "pro", "t", "ce", "one", "one+", "ванплюс"],
        "oppo": ["a", "find", "reno", "oppo"],
        "sony": ["xperia", "сони"],
        "zte": ["red", "magic", "redmagic", "nubia", "neo", "зте"],
    }

def get_memory_synonyms(ram: int) -> set[str]:
    """Генерирует синонимы для объема памяти"""
    synonyms = {f"{ram} gb", f"{ram}гб", f"{ram} гб", f"{ram}gb", ram}
    if ram == 1024:
        synonyms.update(["1 tb", "1тб", "1 тб", "1tb"])
    return synonyms

def get_model_synonyms(model) -> set[str]:
    """Генерирует синонимы для модели"""
    model_lower = model.lower()
    synonyms = set()
    
    # Базовое название модели
    synonyms.add(model_lower)
    
    # Упрощённые формы (убираем пробелы, дефисы)
    synonyms.add(model_lower.replace(" ", ""))
    synonyms.add(model_lower.replace("-", ""))
    
    # Разделяем на слова (чтобы искать по отдельным частям)
    words = model_lower.split()
    for word in words:
        synonyms.add(word)

    for brand, models in BRAND_SYNONYMS.items():
        if brand in model_lower:
            for model in models:
                synonyms.add(model)

    return synonyms

def generate_color_synonyms(path: Path) -> dict[str, set[str]]:
    """Генерирует синонимы для цветов"""
    color_regex = re.compile(r"([А-Яа-я]+)\s\((\w+)\)") # Регулярка для Iphone Синий (Blue), получает Blue
    delimiter = find_delimiter(path)

    with open(path, encoding='utf-8') as fp:
        reader = csv.reader(fp, delimiter=delimiter)
        header = next(reader)
        color_index = header.index('Цвет')
        color_synonyms = {}
        for row in reader:
            color_russian = row[color_index].lower()
            if color_russian == '':
                continue

            if color_synonyms.get(color_russian) is None:
                color_synonyms[color_russian] = set()
                color_synonyms[color_russian].add(color_russian) # Добавляем сам цвет из магазина

            synonims = color_regex.search(row[header.index("Наименование")].lower())
            if synonims is not None:
                for synonim in synonims.groups():
                    color_synonyms[color_russian].add(synonim)

            if 'ё' in color_russian:
                color_synonyms[color_russian].add(color_russian.replace('ё', 'е'))
        
        return color_synonyms

def generate_keywords(name: str, color_synonyms: dict[str, set[str]], ram: int | None = None, storage: int | None = None, color: str | None = None) -> set:
    """Генерирует ключевые слова для товара"""
    keywords = set()

    # Добавляем название модели в разных форматах
    name = name.lower().strip()
    keywords.add(name)
    keywords.add(name.replace(" ", ""))  # Без пробелов
    keywords.add(name.replace("-", ""))  # Без дефисов
    keywords.add(name.replace("ё", "е"))

    # Разбиваем название на слова
    words = name.split()
    for word in words:
        keywords.add(word)

    # Добавляем синонимы модели (например, Xiaomi = Mi, Redmi)
    keywords.update(get_model_synonyms(name))

    if ram:
        keywords.update(get_memory_synonyms(ram))

    if storage:
        keywords.update(get_memory_synonyms(storage))

    if color:
        keywords.update(color_synonyms[color])

    return keywords

def generate_product_synonyms(path: Path) -> list[StoreProduct]:
    """Генерирует синонимы для товаров"""
    delimiter = find_delimiter(path)
    color_synonyms = generate_color_synonyms(path)
    with open(path, encoding='utf-8') as fp:
        reader = csv.reader(fp, delimiter=delimiter)
        header = next(reader)
        product_index = header.index('Наименование')
        ram_index = header.index('Оперативная память (Gb)')
        storage_index = header.index('Встроенная память')
        color_index = header.index('Цвет')
        products: list[StoreProduct] = list()
        for row in reader:
            product_name = row[product_index].lower()
            if product_name == '':
                continue
            
            product = StoreProduct(product_name, set(), row[header.index("Внешний код")])

            # Добавляем объем оперативной памяти и цвета и модели
            ram = row[ram_index]
            if ram:
                product.ram = int(ram)
            color = row[color_index]
            color = color.lower() if color else None

            # Добавляем объем памяти
            storage = row[storage_index]
            if storage:
                if any(x in ["tb", "тб"] for x in storage.lower()):
                    product.storage = 1024
                else:
                    number = 0
                    for id, ch in enumerate(storage):
                        if not ch.isdigit():
                            number = int(storage[:id])
                            break
                    product.storage = int(number)
            # Генерируем ключевые слова через универсальную функцию
            product.synonyms = generate_keywords(product_name, color_synonyms, product.ram, product.storage, color)

            products.append(product)
        return products
