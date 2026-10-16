import json, re
from app.ai import prompt_builder
from app.ai.providers.provider import AIError, GroqProvider
from app.models.answer import Answer


def _extract(text):
    m = re.search(r"\{.*\}", text, re.S)       # tolerate extra text / code fences
    d = json.loads(m.group(0) if m else text)
    return d[0] if isinstance(d, list) else d


MULTI = re.compile(r"all that apply|select all|choose all|check all|more than one|"
                   r"multiple (answers|correct|choices|options)|two correct|"
                   r"(select|choose|pick) (two|2|three|3)", re.I)


def _one(ans, q):
    """Map one answer string to a valid option label, or None."""
    a = ans.strip().upper()
    if a.rstrip(".):") in q.options:
        return a.rstrip(".):")
    if a[:1] in q.options and (len(a) == 1 or not a[1].isalnum()):
        return a[:1]                            # "B. Cascading..." -> B
    t = ans.strip().lower()
    if len(t) >= 3:                             # AI gave the option text instead of a letter
        for k, v in q.options.items():
            if t == v.lower() or t in v.lower() or v.lower() in t:
                return k
    return None


def _labels(ans, q):
    parts = [p.strip() for p in re.split(r"[,;/&]|\band\b", ans, flags=re.I) if p.strip()]
    if len(parts) > 1 and all(re.fullmatch(r"[A-Za-z1-9][.):]?", p) for p in parts):
        got = [_one(p, q) for p in parts]       # "select all that apply": "A, C"
        if all(got):
            return list(dict.fromkeys(got))
    one = _one(ans, q)
    return [one] if one else None


class AIService:
    def __init__(self, settings, provider=None):
        self.provider = provider or GroqProvider(settings.api_key, settings["preferred_model"],
                                                 settings["temperature"])

    def answer(self, q) -> Answer:
        prompt = prompt_builder.build(q)
        for _ in range(3):  # retry on unusable output
            try:
                d = _extract(self.provider.generate(prompt))
                ans = d.get("answer", "")
                ans = ", ".join(map(str, ans)) if isinstance(ans, list) else str(ans)
                ans = ans.strip()
            except AIError:
                raise
            except Exception:
                continue
            if not ans:
                continue
            if q.options:
                labels = _labels(ans, q)
                if not labels:
                    continue
                if len(labels) > 1 and not MULTI.search(q.raw):
                    labels = labels[:1]                  # single-choice question: one answer only
                shown = [f"{k}. {q.options[k]}" if q.lettered else q.options[k] for k in labels]
                return Answer(",".join(labels), q.options[labels[0]], "", "\n".join(shown))
            return Answer(ans, "", "", ans[:200])
        raise AIError("AI could not decide on an answer. Try selecting the area again.")
