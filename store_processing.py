import csv
from pathlib import Path
import re
from turtle import color

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
    """Генерирует синонимы для цветов, используя цвет из `Наименование` как основной."""
    color_regex = re.compile(r"([А-Яа-я\-]+)\s\(([\s\w]+)\)")  # Регулярка для "Темно-Синий (Dark Blue)"
    delimiter = find_delimiter(path)

    # Группы похожих цветов (унификация названий)
    COLOR_MAPPING = {
        # Серебро
        "серебристый": "серебро",
        "серебряный": "серебро",
        "серебрянный": "серебро",
        "silver": "серебро",
        "platinum": "серебро",
        "titanium silver": "серебро",
        "еребристый": "серебро",
        
        # Серый
        "cерый": "серый", # Здесь первая буква английская с, а не русская с
        "серый космос": "серый",
        "космос": "серый",
        "графит": "серый",
        "графитовый": "серый",
        "серый": "серый",
        "титан": "серый",
        "титановый": "серый",
        "gray": "серый",
        "grey": "серый",
        "graphite": "серый",
        "space gray": "серый",
        "titanium gray": "серый",

        # Черный
        "черный": "черный",
        "obsidian": "черный",
        "midnight": "черный",
        "ночь": "черный",
        "onyx": "черный",

        # Зеленый
        "зеленый": "зеленый",
        "green": "зеленый",
        "olive": "зеленый",

        # Фиолетовый
        "фиолетовый": "фиолетовый",
        "purple": "фиолетовый",
        "lavender": "фиолетовый",
        "violet": "фиолетовый",

        # Синий
        "синий": "синий",
        "голубой": "синий",
        "blue": "синий",
        "navy": "синий",
        "ультрамарин": "синий",
    }

    with open(path, encoding='utf-8') as fp:
        reader = csv.reader(fp, delimiter=delimiter)
        header = next(reader)
        color_index = header.index('Цвет')
        name_index = header.index("Наименование")

        # Основной словарь {основной русский цвет → множество синонимов}
        color_synonyms = {}

        for row in reader:
            name = row[name_index].lower().replace('ё', 'е').replace('-', ' ').strip()
            color_from_column = row[color_index].lower().replace('ё', 'е').replace('-', ' ').strip() if row[color_index] else None

            # 1Ищем основной цвет в `Наименование`
            primary_color = None
            match = color_regex.search(name)
            if match:
                primary_color = match.group(1).strip()  # Берём русский цвет
                english_color = match.group(2).strip()  # Берём английский синоним

            # Если не найдено в `Наименование`, берём из `Цвет`
            if not primary_color and color_from_column:
                primary_color = color_from_column
                english_color = None

            # Если даже `Цвет` пустой, пропускаем строку
            if not primary_color:
                continue

            # Унифицируем цвет (заменяем на стандартный)
            unified_primary_color = COLOR_MAPPING.get(primary_color, primary_color)

            # Создаём группу синонимов
            if unified_primary_color not in color_synonyms:
                color_synonyms[unified_primary_color] = set()
            color_synonyms[unified_primary_color].add(primary_color)  # Сам цвет

            # Добавляем английский цвет (если есть)
            if english_color:
                unified_english_color = COLOR_MAPPING.get(english_color, unified_primary_color)
                color_synonyms[unified_english_color].add(english_color)

            # Добавляем цвет из `Цвет`, если он отличается
            if color_from_column:
                unified_column_color = COLOR_MAPPING.get(color_from_column, color_from_column)
                if unified_column_color != unified_primary_color and unified_column_color not in color_synonyms.keys():  # Если цвет реально другой
                    color_synonyms[unified_primary_color].add(unified_column_color)

        return color_synonyms


def generate_keywords(name: str, color_synonyms: dict[str, set[str]], ram: int | None = None, storage: int | None = None, color: str | None = None) -> set:
    """Генерирует ключевые слова для товара"""
    keywords = set()

    # Добавляем название модели в разных форматах
    name = name.lower().strip().replace("ё", "е")
    keywords.add(name)
    keywords.add(name.replace(" ", ""))  # Без пробелов
    keywords.add(name.replace("-", ""))  # Без дефисов

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

            ram = row[ram_index]
            if ram:
                product.ram = int(ram)

            # Получаем цвет из таблицы
            color_russian = row[color_index]
            color_russian = color_russian.lower().replace('ё', 'е').replace('-', ' ').strip() if color_russian else None
            color_english = color_synonyms.get(color_russian, None) if color_russian else None
            # Проверяем, есть ли цвет в названии товара
            found_color = None
            for color in color_synonyms.keys():
                if color in product_name:
                    found_color = color
                    break
            # Если цвет в столбце "Цвет" не совпадает с названием
            if color_russian and found_color and color_russian != found_color:
                print(f"⚠️ Несовпадение цвета в магазине: {product_name} → '{color_russian}' vs '{found_color}'")
                # Используем цвет из "Наименование", так как он вероятно более точный
                color = found_color
            
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
