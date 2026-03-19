import argparse
import dataclasses
import logging
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.9"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


@dataclasses.dataclass
class UnicorngoProduct:
    url: str
    title: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    price: Optional[str]
    sizes: List[str]
    properties: Dict[str, str]


def fetch_page(url: str, timeout: int = 20) -> str:
    """Запрос страницы unicorngo, возвращает HTML или кидает исключение."""
    logging.info("GET %s", url)
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    logging.info("Status code: %s", resp.status_code)
    resp.raise_for_status()
    return resp.text


def parse_product(html: str, url: str = "") -> UnicorngoProduct:
    """Разбор HTML карточки товара unicorngo с помощью BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # Заголовок: <h1 class="hero-show-off-variant_productHero_showOff_sneaker_title__...">
    title_tag = soup.find("h1")
    title: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    if title_tag:
        # Внутри есть <br/>, поэтому берём текст с разделителем.
        title_text = title_tag.get_text(" ", strip=True)
        title = re.sub(r"\s+", " ", title_text)
        # Грубое разбиение: первая часть — бренд, остальное — модель.
        parts = title.split(" ", 2)
        if len(parts) >= 2:
            brand = " ".join(parts[:2])  # "New Balance"
            model = parts[2] if len(parts) == 3 else None

    # Цена: берём первую кнопку с ценой вида "10 990 ₽В корзину".
    price: Optional[str] = None
    def _has_class_fragment(class_value: object, fragment: str) -> bool:
        """Проверка, содержит ли атрибут class подстроку fragment (учёт строк/списков)."""
        if not class_value:
            return False
        if isinstance(class_value, (list, tuple, set)):
            classes = class_value
        else:
            classes = [class_value]
        return any(fragment in str(cls) for cls in classes)

    buy_button = soup.find(
        "button",
        class_=lambda c: _has_class_fragment(c, "button_button__"),
    )
    if buy_button:
        text = buy_button.get_text(" ", strip=True)
        match = re.search(r"([\d\s\u00A0]+₽)", text)
        if match:
            price = match.group(1).replace("\u00A0", " ").strip()

    # Размеры: div.size-selector_size__... (включая активный, у которого ещё один класс).
    sizes: List[str] = []
    for div in soup.find_all(
        "div",
        class_=lambda c: _has_class_fragment(c, "size-selector_size__"),
    ):
        txt = div.get_text(strip=True)
        if txt:
            sizes.append(txt)
    # Убираем дубликаты, сохраняем порядок.
    seen: set[str] = set()
    unique_sizes: List[str] = []
    for s in sizes:
        if s not in seen:
            seen.add(s)
            unique_sizes.append(s)

    # Характеристики: блоки product-properties_property__...
    properties: Dict[str, str] = {}
    for prop_block in soup.find_all(
        "div",
        class_=lambda c: _has_class_fragment(c, "product-properties_property__"),
    ):
        title_div = prop_block.find(
            "div",
            class_=lambda c: _has_class_fragment(c, "product-properties_property_title__"),
        )
        if not title_div:
            continue
        key = title_div.get_text(" ", strip=True)
        if not key:
            continue
        # Значение — текст всего блока минус ключ в начале.
        full_text = prop_block.get_text(" ", strip=True)
        value = full_text.replace(key, "", 1).strip()
        properties[key] = value

    return UnicorngoProduct(
        url=url,
        title=title,
        brand=brand,
        model=model,
        price=price,
        sizes=unique_sizes,
        properties=properties,
    )


def scrape_unicorngo_product(url: str) -> Dict:
    """Скачать страницу unicorngo и распарсить её в словарь."""
    html = fetch_page(url)
    product = parse_product(html, url=url)
    return dataclasses.asdict(product)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Парсер карточки товара unicorngo (requests + bs4)."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=(
            "https://unicorngo.ru/product/"
            "new-balance-530-white-silver-navy-1001819?sku=600012669&shop=false"
        ),
        help="URL страницы товара unicorngo",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        data = scrape_unicorngo_product(args.url)
    except Exception as e:  # noqa: BLE001
        logging.exception("Ошибка при парсинге товара: %s", e)
        print("Не удалось распарсить товар, см. логи выше.")
        return

    print("\n=== Данные товара ===")
    for key, value in data.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()


