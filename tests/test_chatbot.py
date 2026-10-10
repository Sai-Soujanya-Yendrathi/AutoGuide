from chatbot import prepare_evidence, valid_public_url, build_prompt


def test_url_validation():
    assert valid_public_url("https://www.nhtsa.gov/vehicle-safety")
    assert not valid_public_url("https://example.com/nhtsa.gov")
    assert not valid_public_url("http://www.nhtsa.gov")


def test_rejects_unverified_sources():
    chunks = [{"id": "x", "text": "Some statement", "url": ""}, {"id": "y", "text": "Supported text", "url": "https://www.nhtsa.gov/test", "title": "Doc"}]
    evidence = prepare_evidence(chunks)
    assert len(evidence) == 1
    assert evidence[0]["id"] == "y"
    assert "Supported text" in build_prompt("What?", evidence)
