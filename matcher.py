from rapidfuzz import fuzz
from store_processing import BRAND_SYNONYMS, StoreProduct
from supplier_processing import SupplierProduct

class MatchedProduct:
    def __init__(self, supplier_product: SupplierProduct, store_product: StoreProduct, match_score: float):
        self.supplier_product = supplier_product
        self.store_product = store_product
        self.match_score = match_score

    def __repr__(self):
        return f"MatchedProduct(supplier='{self.supplier_product.model}', store='{self.store_product.name}', " \
               f"score={self.match_score})"

    def __dict__(self) -> dict:
        return {
            "supplier_product": self.supplier_product.__dict__(),
            "store_product": self.store_product.__dict__(),
            "match_score": self.match_score
        }

# Кэш для уже обработанных моделей
brand_clean_cache = {}

# Создаем set всех возможных брендов и вариаций
all_brand_variations = set(variation for variations in BRAND_SYNONYMS.values() for variation in variations)

def remove_brand_variations(text: str) -> str:
    """
    Удаляет бренд и его вариации из строки
    """
    if text in brand_clean_cache:
        return brand_clean_cache[text]

    words = text.lower().split()  # Разбиваем текст на слова
    cleaned_words = [word for word in words if word not in all_brand_variations]  # Убираем бренды
    cleaned_text = " ".join(cleaned_words).strip()  # Склеиваем обратно

    brand_clean_cache[text] = cleaned_text  # Кэшируем
    return cleaned_text

def calculate_similarity(model_1: str, model_2: str) -> float:
    """
    Сравнивает две модели по схожести.
    Возвращает коэффициент схожести от 0 до 100.
    """
    model_1_clean = remove_brand_variations(model_1)
    model_2_clean = remove_brand_variations(model_2)

    if model_1_clean == model_2_clean:
        return 100.0  # Полное совпадение

    return fuzz.ratio(model_1_clean, model_2_clean)  # Отношение схожести (0-100)


def match_supplier_to_store(supplier_products: list[SupplierProduct], store_products: list[StoreProduct]) -> list[MatchedProduct]:
    """
    Сопоставляет товары поставщиков с товарами магазина.
    - Использует ключевые слова (`synonyms`) для поиска наиболее похожих товаров.
    - Учитывает совпадение RAM, Storage, цвета и модели.
    """
    matched_products: list[MatchedProduct] = []

    for supplier_product in supplier_products:
        best_match = None
        best_score = 0

        for store_product in store_products:
            common_keywords = supplier_product.synonyms & store_product.synonyms
            score = len(common_keywords) * 1.5  # 1.5 балла за каждое совпадение (раньше было 1)
            # Цвета английского теперь мало в синонимах, поэтому все хорошо

            # Полное совпадение модели
            if supplier_product.model == store_product.model:
                score += 30

            # Полное совпадение бренда
            if supplier_product.brand == store_product.brand:
                score += 20

                # Сравнение моделей по схожести (без учета бренда)
                similarity = calculate_similarity(supplier_product.model, store_product.model)
                if similarity > 83: # Опытным путем подобрано
                    score += similarity / 5
                else:
                    score -= 15

            else:
                score -= 50  # Штраф за разные бренды

            # RAM и Storage дают очки, если оба присутствуют
            if not supplier_product.storage:
                # Из-за гугл пикселя пытаююсь предсказать потенциальый объем внутренний памяти
                for predicted_storage in ["64", "128", "256", "512", "1024"]:
                    if predicted_storage in supplier_product.model:
                        supplier_product.storage = int(predicted_storage)
                        supplier_product.model = supplier_product.model.replace(predicted_storage, "").strip()
                        break

            if supplier_product.ram and store_product.ram and supplier_product.ram == store_product.ram:
                score += 15
            if supplier_product.storage and store_product.storage and supplier_product.storage == store_product.storage:
                score += 15

            # За схожесть унифицированного русского цвета + 3 балла
            if supplier_product.color and supplier_product.color == store_product.color:
                score += 3

            # Фильтрация по минимуму баллов
            if score > best_score:
                best_match = store_product
                best_score = score

        if best_match:
            matched_products.append(MatchedProduct(supplier_product, best_match, best_score))

    return matched_products
