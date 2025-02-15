import csv
from pathlib import Path
import re
from csv_processing import find_delimiter

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

    base_synonyms = {
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
    for brand, models in base_synonyms.items():
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

def generate_product_synonyms(path: Path) -> dict[str, set[str]]:
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
        product_synonyms = {}
        for row in reader:
            product_name = row[product_index].lower()
            if product_name == '':
                continue

            if product_synonyms.get(product_name) is None:
                product_synonyms[product_name] = set()
                product_synonyms[product_name].add(product_name)

            tokens = product_name.split()
            for token in tokens:
                product_synonyms[product_name].add(token)

            if 'ё' in product_name:
                product_synonyms[product_name].add(product_name.replace('ё', 'е'))

            # Добавляем синонимы для объема оперативной памяти и цвета и модели
            product_synonyms[product_name].update(get_model_synonyms(product_name))
            ram = row[ram_index]
            if ram:
                product_synonyms[product_name].update(get_memory_synonyms(int(ram)))
            color = row[color_index]
            if color:
                product_synonyms[product_name].update(color_synonyms[color.lower()])

            # Добавляем синонимы для объема памяти
            storage = row[storage_index]
            if storage:
                if any(["tb", "тб"] for x in storage.lower()):
                    product_synonyms[product_name].update(get_memory_synonyms(1024))
                else:
                    number = 0
                    for id, ch in enumerate(storage):
                        if not ch.isdigit():
                            number = int(storage[:id])
                            break
                    product_synonyms[product_name].update(get_memory_synonyms(number))

        return product_synonyms
