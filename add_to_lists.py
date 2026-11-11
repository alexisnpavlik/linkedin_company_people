import os
import random
import re
import sys

import pandas as pd

from modules.browser import open_linkedin
from modules.sales_nav_lists import add_lead_to_list, open_lead_page
from modules.storage import load_progress, save_progress

LISTS_PROGRESS_FILE = os.getenv("LISTS_PROGRESS_FILE", "output/sn_lists_progress.json")
LIST_PREFIX = os.getenv("LIST_PREFIX", "Perú - ")
ONLY_CORRELATION = os.getenv("ONLY_CORRELATION", "Sí")
LIMIT = int(os.getenv("LIMIT", "0"))
PAUSE_SECONDS = (int(os.getenv("PAUSE_MIN_SECONDS", "3")), int(os.getenv("PAUSE_MAX_SECONDS", "6")))


def list_name_for(category):
    """'1. Marca / Branding' -> 'Perú - Marca / Branding'."""
    return f"{LIST_PREFIX}{re.sub(r'^\s*\d+\.\s*', '', str(category)).strip()}"[:75]


def main():
    """Guarda cada perfil clasificado en una lista de Sales Navigator por categoría."""
    path = sys.argv[1] if len(sys.argv) > 1 else "input/empleados_clasificados_Listas.xlsx"
    df = pd.read_excel(path, sheet_name="Clasificados", dtype=str).fillna("")
    if ONLY_CORRELATION:
        df = df[df["correlacion"] == ONLY_CORRELATION]
    progress = load_progress(LISTS_PROGRESS_FILE)
    pending = df[~df["perfil_url"].isin(progress["done"].keys())]
    if LIMIT:
        pending = pending.head(LIMIT)
    print(f"{len(df)} perfiles ({ONLY_CORRELATION or 'todos'}); {len(pending)} pendientes.")

    with open_linkedin() as page:
        for index, (_, row) in enumerate(pending.iterrows(), start=1):
            list_name = list_name_for(row["categoria"])
            print(f"[{index}/{len(pending)}] {row['nombre']} -> {list_name}")
            lead_page = None
            try:
                lead_page = open_lead_page(page, row["perfil_url"])
                status = add_lead_to_list(lead_page, list_name)
            except Exception as e:
                status = f"error: {str(e).splitlines()[0][:150]}"
                target = lead_page or page
                os.makedirs("output/errores", exist_ok=True)
                target.screenshot(path=f"output/errores/{index:03d}.png")
                print(f"  {status}")
            finally:
                if lead_page is not None:
                    lead_page.close()
            progress["done"][row["perfil_url"]] = {"nombre": row["nombre"], "lista": list_name, "estado": status}
            save_progress(LISTS_PROGRESS_FILE, progress)
            print(f"  {status}")
            page.wait_for_timeout(random.randint(*PAUSE_SECONDS) * 1000)

    errors = [v for v in progress["done"].values() if v["estado"].startswith("error")]
    print(f"Listo: {len(progress['done'])} procesados, {len(errors)} con error.")


if __name__ == "__main__":
    main()
