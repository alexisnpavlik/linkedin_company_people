import random
import sys

from config.config import INPUT_FILE, OUTPUT_FILE, PAUSE_BETWEEN_COMPANIES, PROGRESS_FILE
from modules.browser import open_linkedin
from modules.input_reader import read_companies
from modules.people_scraper import scrape_company
from modules.storage import load_progress, save_progress, write_excel


def main():
    """Scrapea la pestaña Personas de cada empresa del Excel de entrada y genera el Excel de salida."""
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    companies = read_companies(input_file)
    if not companies:
        print(f"No encontré URLs de linkedin.com/company/ en {input_file}")
        sys.exit(1)

    progress = load_progress(PROGRESS_FILE)
    pending = [c for c in companies if c["slug"] not in progress["done"]]
    print(f"{len(companies)} empresas en {input_file}; {len(pending)} pendientes.")

    with open_linkedin() as page:
        for index, company in enumerate(pending, start=1):
            print(f"[{index}/{len(pending)}] {company['empresa']} -> {company['people_url']}")
            try:
                rows, reported, anonymous = scrape_company(page, company)
                status = "ok"
            except Exception as e:
                print(f"  error: {e}")
                if "sesión" in str(e).lower():
                    break
                rows, reported, anonymous, status = [], None, 0, f"error: {str(e)[:150]}"
            progress["rows"].extend(rows)
            progress["done"][company["slug"]] = {
                "empresa": company["empresa"],
                "hoja": company.get("hoja", ""),
                "empresa_url": company["people_url"].replace("people/", ""),
                "miembros_linkedin": reported,
                "extraidos": len(rows),
                "anonimos": anonymous,
                "estado": status,
            }
            save_progress(PROGRESS_FILE, progress)
            write_excel(OUTPUT_FILE, progress)
            print(f"  {len(rows)} personas (LinkedIn informa {reported}, anónimos {anonymous})")
            if index < len(pending):
                page.wait_for_timeout(random.randint(*PAUSE_BETWEEN_COMPANIES) * 1000)

    write_excel(OUTPUT_FILE, progress)
    print(f"Listo: {len(progress['rows'])} personas en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
