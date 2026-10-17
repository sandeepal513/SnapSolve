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


def build_screen(text: str) -> str:
    """Prompt for OCR text of an ENTIRE screen: the AI finds the question, its options, and answers."""
    return ("You are an expert quiz solver. Below is OCR text of an ENTIRE screen (browser, menus, other "
            "windows and page furniture included). It may contain typos or missing spaces; infer the "
            "intended wording.\n\nTask: find the main multiple-choice quiz question on the screen (if "
            "several are visible, take the first complete one: question plus its options), ignore "
            "everything else, and answer it.\n\nSCREEN TEXT:\n" + text +
            '\n\nReturn ONLY this JSON: {"reasoning": "at most 2 short sentences", "question": "the question '
            'text", "options": {"A": "exact option text"}, "labels_shown": true, "multiple": false, '
            '"answer": "option label only, e.g. B"}\n'
            "Rules: copy the question and option texts exactly as on screen (only fix obvious OCR spacing). "
            "Use the labels shown on screen; if none are shown, use A, B, C... in order and set "
            "labels_shown to false. Give exactly ONE answer unless the question says to select multiple / "
            "all that apply (then multiple=true and list every correct label separated by commas). Watch for "
            "NOT / EXCEPT / LEAST / FALSE. If there is a question without options, put its short final "
            'answer in "answer" and use an empty options object. If there is no question on the screen, '
            "return empty strings and an empty options object.")
