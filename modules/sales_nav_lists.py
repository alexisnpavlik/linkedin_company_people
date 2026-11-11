import re

SAVE_BUTTON_RE = re.compile(r"^\s*(Guardar|Guardado|Save|Saved)\s*$")
MORE_BUTTON_RE = re.compile(r"^\s*(More|Más)\s*$")
VIEW_IN_SN_RE = re.compile(r"(View|Ver) in Sales Navigator|Ver en Sales Navigator")
CREATE_LIST_RE = re.compile(r"Crear lista|Create list")
CREATE_AND_SAVE_RE = re.compile(r"Crear y guardar|Create and save")


def open_lead_page(page, profile_url):
    """Abre el perfil y devuelve la pestaña de Sales Navigator de ese lead (menú Más → Ver en Sales Navigator)."""
    page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
    more = page.locator("main button").filter(has_text=MORE_BUTTON_RE).first
    more.wait_for(state="visible", timeout=20000)
    more.click()
    page.get_by_text(VIEW_IN_SN_RE).first.wait_for(state="attached", timeout=10000)
    with page.context.expect_page(timeout=30000) as new_page_info:
        page.get_by_text(VIEW_IN_SN_RE).first.dispatch_event("click")
    lead_page = new_page_info.value
    lead_page.wait_for_load_state("domcontentloaded")
    lead_page.locator("button").filter(has_text=SAVE_BUTTON_RE).first.wait_for(state="visible", timeout=30000)
    lead_page.get_by_text(re.compile(r"(Listas|Lists) \(\d+\)")).first.wait_for(timeout=15000)
    if "/sales/lead/" not in lead_page.url and "/sales/people/" not in lead_page.url:
        lead_page.close()
        raise RuntimeError(f"Sales Navigator no abrió la ficha del lead: {lead_page.url[:120]}")
    return lead_page


def list_menu_item(lead_page, list_name):
    """Ítem del menú 'Añadir a la lista' cuyo texto es el nombre de la lista (con o sin contador)."""
    pattern = re.compile(rf"^\s*{re.escape(list_name)}\s*(\(\d+\))?\s*$")
    return lead_page.locator("[role=menu] li, [role=menu] button, .artdeco-dropdown__content li").filter(has_text=pattern)


def add_lead_to_list(lead_page, list_name):
    """Agrega el lead abierto a la lista; la crea si no existe. Devuelve 'agregado' o 'creada'."""
    lead_page.locator("button").filter(has_text=SAVE_BUTTON_RE).first.click()
    lead_page.get_by_text(CREATE_LIST_RE).first.wait_for(state="attached", timeout=10000)
    lead_page.wait_for_timeout(500)
    item = list_menu_item(lead_page, list_name)
    if item.count() > 0:
        before = lead_list_count(lead_page)
        item.first.click()
        lead_page.wait_for_timeout(1500)
        after = lead_list_count(lead_page)
        if after == before - 1:
            # El ítem es un interruptor: si el lead ya estaba, el clic lo sacó.
            item.first.click()
            lead_page.wait_for_timeout(1500)
            after = lead_list_count(lead_page)
            if after != before:
                raise RuntimeError(f"no se pudo reponer al lead en la lista ({before} -> {after})")
            return "ya estaba"
        if after != before + 1:
            raise RuntimeError(f"el contador de listas no subió ({before} -> {after})")
        return "agregado"
    lead_page.locator("button").filter(has_text=CREATE_LIST_RE).last.dispatch_event("click")
    dialog = lead_page.locator("[role=dialog]").filter(has_text=CREATE_AND_SAVE_RE)
    dialog.wait_for(state="visible", timeout=15000)
    name_input = dialog.locator("input").first
    name_input.click()
    name_input.press_sequentially(list_name, delay=40)
    dialog.locator("button").filter(has_text=CREATE_AND_SAVE_RE).first.click()
    lead_page.wait_for_timeout(1500)
    return "creada"


def lead_list_count(lead_page):
    """Número del encabezado 'Listas (n)' de la ficha: en cuántas listas está el lead."""
    match = re.search(r"(?:Listas|Lists) \((\d+)\)", lead_page.inner_text("main"))
    if not match:
        raise RuntimeError("no se encontró el contador 'Listas (n)' en la ficha")
    return int(match.group(1))
