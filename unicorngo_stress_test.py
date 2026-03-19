import collections
import logging
from typing import Counter, Dict

import requests

from unicorngo_scraper import HEADERS


URL = (
    "https://unicorngo.ru/product/"
    "new-balance-530-white-silver-navy-1001819?sku=600012669&shop=false"
)


def run_stress_test(
    url: str,
    iterations: int = 1000,
    timeout: int = 10,
) -> Dict[str, int]:
    """Делает iterations последовательных запросов к url без пауз.

    Возвращает словарь с количеством:
      - успешных ответов по статус-кодам (200, 403 и т.п.),
      - сетевых ошибок (ключи начинаются с 'err:').
    """
    stats: Counter[str] = collections.Counter()

    session = requests.Session()

    for i in range(1, iterations + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=timeout)
            key = f"status:{resp.status_code}"
            stats[key] += 1
            if i % 50 == 0:
                logging.info(
                    "Iter %d: status=%s (total so far: %s)",
                    i,
                    resp.status_code,
                    dict(stats),
                )
        except requests.RequestException as exc:
            key = f"err:{type(exc).__name__}"
            stats[key] += 1
            logging.warning("Iter %d: error %s", i, exc)

    return dict(stats)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    iterations = 1000
    logging.info(
        "Starting stress test: %d sequential requests to %s", iterations, URL
    )
    stats = run_stress_test(URL, iterations=iterations)

    print("\n=== Итоги стресс-теста ===")
    for key, count in sorted(stats.items()):
        print(f"{key}: {count}")


if __name__ == "__main__":
    main()






