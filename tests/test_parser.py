from app.parser.question_parser import parse

def test_letters():
    q = parse("What does CSS stand for?\nA. Computer\nB) Cascading\nC. Creative\nD. Styling")
    assert list(q.options) == ["A", "B", "C", "D"] and q.lettered

def test_numbered_question_not_an_option():
    q = parse("1. What does CSS stand for?\nA. Computer\nB. Cascading\nC. Creative\nD. Styling\nNext")
    assert list(q.options) == ["A", "B", "C", "D"] and q.question.startswith("1. What")
    assert q.options["D"] == "Styling"            # 'Next' button not glued on

def test_radio_buttons_without_labels():
    q = parse("Which tag makes a link?\nO <a>\nO <p>\n● <div>\nO <img>")
    assert not q.lettered and q.options == {"A": "<a>", "B": "<p>", "C": "<div>", "D": "<img>"}

def test_radio_with_letters():
    q = parse("Pick one?\n○ A. Red\n○ B. Blue")
    assert q.options == {"A": "Red", "B": "Blue"}

def test_wrapped_option():
    q = parse("Q?\nA. Computer\nStyle Sheets\nB. Cascading")
    assert q.options["A"] == "Computer Style Sheets"

def test_fallback():
    assert parse("Just some text").options == {}

def test_glued_glyph_and_lowercase_labels():
    q = parse("Metadata in a data warehouse is best described as:\nOa. Business measures stored in fact tables\n"
              "Ob.Hierarchies in dimensional models\nOc. Data about data that defines warehouse objects\n"
              "Od. Summarized values used in OLAP queries")
    assert list(q.options) == ["A", "B", "C", "D"] and q.lettered
    assert q.options["C"].startswith("Data about data")

def test_unlabeled_strips_stray_labels():
    q = parse("Metadata is best described as:\na.Business measures\nb.Hierarchies\nc.Data about data\n")
    assert list(q.options) == ["A", "B", "C"] and q.options["C"] == "Data about data"

def test_user_sample_after_space_fix():
    from app.ocr.ocr_engine import fix_spaces
    raw = ("Which of the following is NoT a characteristic of a data warehouse according to Inmon's definition?\n"
           "a. Integrated\nb.  Frequentlyupdatedv\nC. Time-variant\nd. Subject-oriented")
    q = parse("\n".join(fix_spaces(l) for l in raw.splitlines()))
    assert list(q.options) == ["A", "B", "C", "D"] and q.lettered
    assert q.options["B"] == "Frequently updated" and q.options["C"] == "Time-variant"
