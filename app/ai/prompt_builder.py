from app.models.question import Question

def build(q: Question) -> str:
    if q.options:
        opts = "\n".join(f"{k}. {v}" for k, v in q.options.items())
        body = f"Question:\n{q.question}\n\nOptions:\n{opts}"
        fmt = '{"reasoning": "at most 2 short sentences", "answer": "option label only, e.g. B"}'
        rule = ("Pick the option that is actually correct. This is single-choice (exactly ONE answer) unless the "
                "text says to select multiple / all that apply; then list every correct label "
                "separated by commas. Use only the labels shown.")
    else:
        body = f"Text from screen:\n{q.raw}"
        fmt = '{"reasoning": "at most 2 short sentences", "answer": "the final answer only, as short as possible"}'
        rule = "The answer must contain no explanation, only the answer itself."
    return ("You are an expert quiz solver. The text was captured by OCR and may contain typos, "
            "missing characters or odd line breaks; infer the intended wording (e.g. 'NoT' means NOT). "
            "Watch for negations such as NOT / EXCEPT / LEAST / FALSE.\n\n" + body +
            "\n\nThink briefly, then return ONLY this JSON: " + fmt + "\n" + rule)
