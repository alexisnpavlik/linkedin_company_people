import os

INPUT_FILE = os.getenv("INPUT_FILE", "input/empresas.xlsx")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "output/empleados.xlsx")
PROGRESS_FILE = os.getenv("PROGRESS_FILE", "output/progress.json")

PROFILE_DIR = os.path.expanduser(os.getenv("PROFILE_DIR", "~/.linkedin_people_profile"))
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
LOGIN_WAIT_SECONDS = int(os.getenv("LOGIN_WAIT_SECONDS", "300"))

# Cada clic en "Mostrar más resultados" trae ~12 personas; LinkedIn corta en ~1000.
MAX_SHOW_MORE_CLICKS = int(os.getenv("MAX_SHOW_MORE_CLICKS", "100"))
DRY_SCROLLS_TO_STOP = int(os.getenv("DRY_SCROLLS_TO_STOP", "3"))
PAUSE_BETWEEN_COMPANIES = (
    int(os.getenv("PAUSE_MIN_SECONDS", "20")),
    int(os.getenv("PAUSE_MAX_SECONDS", "45")),
)
