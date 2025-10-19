from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Product:
    id: str
    name: str
    price_usd: float
    category: str
    emoji: str
    description: str
    stock: int = 100  # Запас на складі

class ProductsDatabase:
    def __init__(self):
        self.products = self._load_products()

    def _load_products(self) -> Dict[str, Product]:
        # Початкова база товарів (легко редагувати)
        return {
            "zinc": Product(
                id="zinc",
                name="Цинк Піколінат",
                price_usd=1.3,
                category="minerals",
                emoji="🛡️",
                description="Підтримка тестостерону, імунітет, шкіра"
            ),
            "magnesium": Product(
                id="magnesium",
                name="Магній Хелат",
                price_usd=2.6,
                category="minerals",
                emoji="⚡",
                description="Сон, м’язи, нервова система"
            ),
            "ashwagandha": Product(
                id="ashwagandha",
                name="Ашваганда",
                price_usd=2.6,
                category="adaptogens",
                emoji="🌱",
                description="Стрес, кортизол, тестостерон"
            ),
            "niacinamide_serum": Product(
                id="niacinamide_serum",
                name="Сироватка з ніацинамідом",
                price_usd=2.6,
                category="skincare",
                emoji="💧",
                description="Пори, зволоження, антиейджинг"
            ),
            "retinol_serum": Product(
                id="retinol_serum",
                name="Сироватка з ретинолом",
                price_usd=2.6,
                category="antiaging",
                emoji="⏳",
                description="Зморшки, колаген, шкіра"
            ),
            "vitamin_d": Product(
                id="vitamin_d",
                name="Вітамін D3",
                price_usd=1.3,
                category="vitamins",
                emoji="☀️",
                description="Кістки, імунітет, тестостерон"
            ),
            "dopa_mucuna": Product(
                id="dopa_mucuna",
                name="Допа мукуна",
                price_usd=2.6,
                category="nootropics",
                emoji="🧠",
                description="Дофамін, настрій, мотивація"
            ),
            "collagen": Product(
                id="collagen",
                name="Колаген пептиди",
                price_usd=2.6,
                category="antiaging",
                emoji="🦴",
                description="Шкіра, суглоби, волосся"
            ),
            "berberine": Product(
                id="berberine",
                name="Берберин",
                price_usd=2.6,
                category="pharma",
                emoji="🌿",
                description="Глюкоза, інсулін, метаболізм"
            )
            # Додай нові товари тут (для жіночого здоров’я, дієт, антифітнесу, косметології, фарми)
        }

    def get_products(self, category: str = None) -> List[Product]:
        """Отримати продукти з фільтром за категорією."""
        if category:
            return [p for p in self.products.values() if p.category == category]
        return list(self.products.values())

    def get_product(self, product_id: str) -> Optional[Product]:
        """Отримати конкретний товар."""
        return self.products.get(product_id)

    def add_product(self, product: Product) -> str:
        """Додати новий товар (для редагування)."""
        self.products[product.id] = product
        return product.id

    def update_product(self, product_id: str, updates: Dict) -> Optional[Product]:
        """Оновити товар (для редагування)."""
        if product_id in self.products:
            for key, value in updates.items():
                setattr(self.products[product_id], key, value)
            return self.products[product_id]
        return None

    def delete_product(self, product_id: str) -> bool:
        """Видалити товар."""
        return self.products.pop(product_id, None) is not None
