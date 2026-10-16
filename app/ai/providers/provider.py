import time
import requests
from app.utils.logger import get_logger

log = get_logger()
SESSION = requests.Session()  # keep-alive: reuses the TLS connection


class AIError(Exception):
    pass


class Provider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class GroqProvider(Provider):
    """Groq (OpenAI-compatible API). Tries OpenAI's open gpt-oss models first, then Llama."""
    BASE = "https://api.groq.com/openai/v1/"
    PREFERRED = ["openai/gpt-oss-120b", "openai/gpt-oss-20b",
                 "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    SKIP = ("whisper", "tts", "guard", "compound", "distil", "playai", "orpheus", "safeguard")
    _cache = {"models": None, "dead": set()}

    def __init__(self, api_key, model="", temperature=0.0):
        self.key, self.model, self.temp = api_key, model, temperature

    def _candidates(self):
        c = self._cache
        if c["models"] is None:
            try:
                r = SESSION.get(self.BASE + "models", timeout=8,
                                headers={"Authorization": "Bearer " + self.key})
                if r.status_code == 200:
                    c["models"] = [m["id"] for m in r.json().get("data", [])
                                   if not any(x in m["id"] for x in self.SKIP)]
            except Exception:
                pass
        avail = c["models"]
        out = []
        for m in ([self.model] if self.model else []) + self.PREFERRED + (avail or []):
            if m and m not in out and m not in c["dead"] and (avail is None or m in avail):
                out.append(m)
        if not out:
            c["dead"].clear(); out = self.PREFERRED[:]
        return out[:4]

    def _payload(self, m, prompt, json_mode):
        p = {"model": m, "temperature": self.temp,
             "messages": [{"role": "user", "content": prompt}]}
        if "gpt-oss" in m:                       # reasoning model: keep thinking short and fast
            p["reasoning_effort"] = "low"; p["max_completion_tokens"] = 1000
        else:
            p["max_completion_tokens"] = 400
        if json_mode:
            p["response_format"] = {"type": "json_object"}
        return p

    def _post(self, m, prompt):
        r = SESSION.post(self.BASE + "chat/completions", timeout=25,
                         headers={"Authorization": "Bearer " + self.key},
                         json=self._payload(m, prompt, True))
        if r.status_code == 400 and ("response_format" in r.text.lower() or "json" in r.text.lower()):
            r = SESSION.post(self.BASE + "chat/completions", timeout=25,
                             headers={"Authorization": "Bearer " + self.key},
                             json=self._payload(m, prompt, False))   # JSON is extracted anyway
        return r

    def generate(self, prompt):
        if not self.key:
            raise AIError("API key not set. Use the tray menu > Set API Key.")
        last, net_err, deadline = None, False, time.time() + 40
        for attempt in range(3):
            fatal = False
            for m in self._candidates():
                try:
                    r = self._post(m, prompt)
                except requests.RequestException:
                    net_err = True
                    continue
                if r.status_code == 200:
                    try:
                        t = r.json()["choices"][0]["message"]["content"]
                    except Exception:
                        t = None
                    if t:
                        return t
                    continue
                log.info("Groq model %s -> HTTP %s", m, r.status_code)
                if r.status_code in (400, 404) and "model" in r.text.lower():
                    self._cache["dead"].add(m)          # decommissioned / unsupported: skip it
                    continue
                if last is None or r.status_code in (429, 500, 502, 503):
                    last = r
                if r.status_code in (401, 403):
                    last, fatal = r, True
                    break
            if fatal or time.time() > deadline:
                break
            time.sleep(1 + attempt)
        if last is None:
            raise AIError("Unable to connect to AI service." if net_err
                          else "No Groq model available. Try again in a minute.")
        try:
            detail = last.json()["error"]["message"][:140]
        except Exception:
            detail = ""
        log.info("Groq HTTP %s: %s", last.status_code, detail)
        msgs = {400: "Request rejected by Groq.",
                401: "Groq API key invalid. Re-enter it from the tray menu.",
                403: "Groq API key not allowed. Check it in the Groq console.",
                429: "Groq rate limit reached. Wait a few seconds and retry.",
                500: "Groq had an internal error. Try again.",
                503: "Groq is overloaded. Try again in a moment."}
        raise AIError(f"[{last.status_code}] " + msgs.get(last.status_code, "AI service unavailable.")
                      + (f"\n{detail}" if detail else ""))
