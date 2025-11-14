# test_lookup.py

from tpsl_planner.io.company_lookup import (
    JP_TICKER_PATTERN,
    normalize_ticker,
    get_company_name,
)

def main():
    print("=== TESTING JP TICKER 147A ===")

    # 1. Pattern test
    print("JP_TICKER_PATTERN matches 147A:",
          bool(JP_TICKER_PATTERN.fullmatch("147A")))

    # 2. Normalization
    norm = normalize_ticker("147A")
    print("normalize_ticker('147A') ->", norm)

    # 3. Company name fetch
    name = get_company_name("147A")
    print("get_company_name('147A') ->", name)

    print("=== DONE ===")

if __name__ == "__main__":
    main()
