from app.core.email_text import extract_emails


def test_extract_emails_empty():
    assert extract_emails("") == []


def test_extract_emails_one():
    assert extract_emails("enviar para katharine.ribeiro@nava.com.br") == [
        "katharine.ribeiro@nava.com.br"
    ]


def test_extract_emails_dedupe_order():
    text = "a@b.com e depois A@B.COM e c@d.org"
    assert extract_emails(text) == ["a@b.com", "c@d.org"]
