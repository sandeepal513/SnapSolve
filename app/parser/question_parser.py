import re
from app.models.question import Question

# radio/bullet glyphs (or an OCR'd "O") that may precede an option
GLYPH = r"(?:[○●◯◉•▪■□☐☑\-\*©®]|[OoQ0@](?=\s))"
OPT = re.compile(r"^\s*" + GLYPH + r"?\s*[OoQ0@]?\(?([A-Ha-h]|[1-9])\s?[\.\)\:]\s*(.+)$")
BULLET = re.compile(r"^\s*" + GLYPH + r"\s*")
UI = re.compile(r"^(next|previous|prev|back|submit|skip|finish|continue|save|check|clear|reset|"
                r"question\s*\d+\s*(of|/)\s*\d+|\d+\s*/\s*\d+|\d+\s+of\s+\d+)$", re.I)


def parse(text: str) -> Question:
    lines = [l.strip() for l in text.splitlines() if l.strip() and not UI.match(l.strip())]
    q = Question(raw=text)

    # 1) labelled options: keep the longest sequential run starting at A or 1
    items = []
    for i, l in enumerate(lines):
        m = OPT.match(l)
        if m:
            items.append((i, m.group(1).upper(), m.group(2).strip()))
    best = []
    for s, it in enumerate(items):
        run = [it]
        for nxt in items[s + 1:]:
            if ord(nxt[1]) == ord(run[-1][1]) + 1:
                run.append(nxt)
        if len(run) >= len(best):
            best = run
    if len(best) >= 2:
        first, last_idx = best[0][0], best[-1][0]
        starts = {b[0]: b for b in best}
        q.question = " ".join(lines[:first])
        cur, wrapped = None, False
        for i in range(first, len(lines)):
            if i in starts:
                cur = starts[i][1]; q.options[cur] = starts[i][2]
            elif cur:
                if i < last_idx:
                    q.options[cur] += " " + lines[i]            # wrapped option text
                elif not wrapped and lines[i][:1].islower() and len(lines[i]) < 80:
                    q.options[cur] += " " + lines[i]; wrapped = True
        return q

    # 2) unlabelled options (radio buttons): lines after the last "...?" / "...:" line
    cands = [i for i, l in enumerate(lines) if re.search(r"[?:：]\s*$", l) and i <= len(lines) - 3]
    if cands:
        k = cands[-1]
        opts = []
        for l in lines[k + 1:][:8]:
            m = OPT.match(l)                       # drop a stray "a." label if present
            opts.append(m.group(2).strip() if m else BULLET.sub("", l))
        q.question = " ".join(lines[:k + 1])
        q.options = {chr(65 + i): o for i, o in enumerate(opts)}
        q.lettered = False
        return q

    # 3) nothing recognised: send everything to the AI
    q.question, q.lettered = text.strip(), False
    return q
