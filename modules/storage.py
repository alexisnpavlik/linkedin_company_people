import json
import os
from datetime import datetime

import pandas as pd

OUTPUT_COLUMNS = ["empresa", "hoja", "empresa_url", "nombre", "perfil_url", "cargo", "upload_date"]
SUMMARY_COLUMNS = ["empresa", "hoja", "empresa_url", "miembros_linkedin", "extraidos", "anonimos", "estado", "upload_date"]


def load_progress(path):
    """Lee el avance guardado; vacío si es la primera corrida."""
    if not os.path.exists(path):
        return {"done": {}, "rows": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_progress(path, progress):
    """Guarda el avance tras cada empresa para poder retomar si la corrida se corta."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=1)
    os.replace(tmp_path, path)


def write_excel(path, progress):
    """Escribe el Excel final: hoja Empleados + hoja Resumen por empresa."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    employees = pd.DataFrame(progress["rows"], columns=OUTPUT_COLUMNS[:-1])
    employees["upload_date"] = upload_date
    summary = pd.DataFrame(progress["done"].values(), columns=SUMMARY_COLUMNS[:-1])
    summary["upload_date"] = upload_date
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        employees.to_excel(writer, sheet_name="Empleados", index=False)
        summary.to_excel(writer, sheet_name="Resumen", index=False)
