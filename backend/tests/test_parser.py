from backend.parser import parse_document
import os


def test_parser():
    with open(f"{os.path.dirname(__file__)}/data/page2.pdf", "rb") as pdf:
        parsed_doc = parse_document("page2.pdf", pdf.read())
    text = parsed_doc.document_obj.export_to_text()
    assert "PRKC" in text
    assert "PhosphoDisco" in text
    assert "Division of Precision Medicine, Department of Medicine" in text
