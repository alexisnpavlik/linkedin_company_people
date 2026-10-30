import re

import pandas as pd

COMPANY_URL_RE = re.compile(r"linkedin\.com/company/([\w.%-]+)", re.IGNORECASE)
NAME_COLUMN_HINTS = ("empresa", "company", "nombre", "marca")


def normalize_company_url(raw_url):
    """Devuelve (slug, url de la pestaña Personas) o None si no es una URL de empresa."""
    match = COMPANY_URL_RE.search(str(raw_url))
    if not match:
        return None
    slug = match.group(1).strip().lower()
    return slug, f"https://www.linkedin.com/company/{slug}/people/"


def find_name_column(columns):
    """Primera columna cuyo encabezado sugiera el nombre de la empresa; None si no hay."""
    for hint in NAME_COLUMN_HINTS:
        for column in columns:
            if hint in str(column).lower():
                return column
    return None


def read_companies(path):
    """Lee todas las hojas del Excel y devuelve las empresas con URL de LinkedIn, sin duplicados.

    La URL es la primera celda de la fila que contenga linkedin.com/company/
    (sirve cualquier subdominio, como pe.linkedin.com). El nombre sale de la
    columna Empresa/Company/Nombre/Marca; si no hay, se usa el slug.
    """
    sheets = pd.read_excel(path, sheet_name=None, dtype=str)
    companies = []
    seen = set()
    for sheet_name, df in sheets.items():
        df = df.fillna("")
        name_column = find_name_column(df.columns)
        for _, row in df.iterrows():
            parsed = next((normalize_company_url(c) for c in row.tolist() if normalize_company_url(c)), None)
            if not parsed:
                continue
            slug, people_url = parsed
            if slug in seen:
                continue
            seen.add(slug)
            name = row[name_column].strip() if name_column else ""
            companies.append({"empresa": name or slug, "hoja": sheet_name, "slug": slug, "people_url": people_url})
    return companies
