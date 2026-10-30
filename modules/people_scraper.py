import re

from config.config import DRY_SCROLLS_TO_STOP, MAX_SHOW_MORE_CLICKS
from modules.browser import is_logged_in

# Una sola pasada sobre el DOM: las clases CSS de LinkedIn son hashes que cambian
# en cada deploy, así que se identifica cada tarjeta por su texto ("Contacto de
# 2.º grado", "Miembro de LinkedIn") y no por selectores de estilo.
EXTRACT_CARDS_JS = r"""
() => {
  const main = document.querySelector('main');
  if (!main) return [];
  const cardRe = /grado|degree|Miembro de LinkedIn|LinkedIn Member/;
  return [...main.querySelectorAll('li')]
    .filter(li => cardRe.test(li.innerText))
    .map(li => {
      const a = li.querySelector('a[href*="/in/"]');
      return {
        url: a ? a.href.split('?')[0] : null,
        lines: li.innerText.split('\n').map(s => s.trim()).filter(Boolean),
      };
    });
}
"""

SHOW_MORE_JS = r"""
() => {
  const b = [...document.querySelectorAll('main button')]
    .find(x => /Mostrar más resultados|Show more results/i.test(x.innerText));
  if (!b || b.disabled) return false;
  b.click();
  return true;
}
"""

MEMBER_COUNT_RE = re.compile(r"([\d.,]+)\s+(?:miembros? asociados?|associated members?)", re.IGNORECASE)


def parse_card(card):
    """Convierte una tarjeta cruda en {nombre, perfil_url, cargo}; None si es anónima."""
    if not card["url"]:
        return None
    lines = card["lines"]
    name = lines[0]
    # El titular es la línea que sigue al grado de contacto ("· 2º", "· 3er").
    degree_index = next((i for i, line in enumerate(lines) if line.startswith("·")), None)
    title = ""
    if degree_index is not None and degree_index + 1 < len(lines):
        title = lines[degree_index + 1]
    elif len(lines) > 1:
        title = lines[1]
    profile_url = card["url"].replace("http://", "https://").rstrip("/")
    return {"nombre": name, "perfil_url": profile_url, "cargo": title}


def load_all_people(page):
    """Scrollea y clickea 'Mostrar más resultados' hasta que no aparezca gente nueva."""
    clicks = 0
    dry = 0
    last_count = 0
    while clicks < MAX_SHOW_MORE_CLICKS and dry < DRY_SCROLLS_TO_STOP:
        page.mouse.wheel(0, 6000)
        page.wait_for_timeout(1500)
        if page.evaluate(SHOW_MORE_JS):
            clicks += 1
            page.wait_for_timeout(2500)
        count = len(page.evaluate(EXTRACT_CARDS_JS))
        dry = dry + 1 if count == last_count else 0
        last_count = count
    return clicks


def scrape_company(page, company):
    """Devuelve (filas de empleados, total de miembros que informa LinkedIn, anónimos)."""
    page.goto(company["people_url"], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    if not is_logged_in(page):
        raise RuntimeError("La sesión se cayó en medio de la corrida.")
    if "/people" not in page.url:
        raise RuntimeError(f"LinkedIn redirigió a {page.url}: la URL no es de una empresa válida.")

    load_all_people(page)
    cards = page.evaluate(EXTRACT_CARDS_JS)
    match = MEMBER_COUNT_RE.search(page.inner_text("main"))
    reported = int(re.sub(r"[.,]", "", match.group(1))) if match else None

    rows = []
    seen = set()
    anonymous = 0
    for card in cards:
        parsed = parse_card(card)
        if parsed is None:
            anonymous += 1
            continue
        if parsed["perfil_url"] in seen:
            continue
        seen.add(parsed["perfil_url"])
        rows.append({"empresa": company["empresa"], "hoja": company.get("hoja", ""), "empresa_url": company["people_url"].replace("people/", ""), **parsed})
    return rows, reported, anonymous
