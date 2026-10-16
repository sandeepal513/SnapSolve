import logging
from app.config.settings import DIR

def get_logger():
    (DIR / "logs").mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("aisa")
    if not log.handlers:
        log.setLevel(logging.INFO)
        h = logging.FileHandler(DIR / "logs" / "app.log", encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        log.addHandler(h)
    return log
