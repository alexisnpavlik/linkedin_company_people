import time
from contextlib import contextmanager

from playwright.sync_api import sync_playwright

from config.config import HEADLESS, LOGIN_WAIT_SECONDS, PROFILE_DIR

FEED_URL = "https://www.linkedin.com/feed/"
LOGGED_IN_NAV_SELECTOR = (
    "input[placeholder*='Buscar'], input[placeholder*='Search'], "
    "[aria-label*='Mensajes'], [aria-label*='Messaging']"
)


def is_logged_in(page):
    """True si la página no es login/authwall y existe la barra de usuario logueado."""
    if any(marker in page.url for marker in ("/login", "/authwall", "/checkpoint", "/uas/")):
        return False
    return page.locator(LOGGED_IN_NAV_SELECTOR).count() > 0


def wait_for_manual_login(page):
    """Espera a que el usuario se loguee a mano en la ventana abierta.

    No se completan credenciales automáticamente: cada intento fallido es lo que
    dispara los checkpoints de LinkedIn.
    """
    if HEADLESS:
        raise RuntimeError("Sesión vencida. Corré con HEADLESS=false y logueate en la ventana.")
    print(f"Sesión no válida. Logueate en la ventana de Chromium (espero {LOGIN_WAIT_SECONDS}s)...")
    deadline = time.time() + LOGIN_WAIT_SECONDS
    while time.time() < deadline:
        page.wait_for_timeout(3000)
        if "/feed" in page.url and is_logged_in(page):
            print("Login detectado, sesión guardada en el perfil.")
            return
    raise RuntimeError("No se detectó el login a tiempo.")


@contextmanager
def open_linkedin():
    """Abre Chromium con el perfil persistente y garantiza sesión activa."""
    playwright = sync_playwright().start()
    context = None
    try:
        context = playwright.chromium.launch_persistent_context(
            PROFILE_DIR, headless=HEADLESS, viewport={"width": 1280, "height": 900}
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(FEED_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        if not is_logged_in(page):
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=60000)
            wait_for_manual_login(page)
        print("Sesión verificada.")
        yield page
    finally:
        try:
            if context is not None:
                context.close()
        finally:
            playwright.stop()
