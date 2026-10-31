from app import engine
from app.nlp import split_requirements

SAMPLE = (
    "We need an online shop where customers can search products and pay by UPI.\n"
    "Admin must manage product stock.\n"
    "Customers could write reviews."
)


def test_split_requirements_handles_bullets_and_sentences():
    text = "- Customers can search products.\n2) Admin must manage stock. Users can log in.\nok"
    assert split_requirements(text) == [
        "Customers can search products",
        "Admin must manage stock",
        "Users can log in",
    ]


def test_one_sentence_with_two_actions_gives_two_stories():
    result = engine.generate("We need an online shop where customers can search products and pay by UPI.")
    stories = result["stories"]
    assert [s["id"] for s in stories] == ["US-001", "US-002"]
    assert all(s["actor"] == "Customer" for s in stories)
    assert stories[0]["action"] == "search products"
    assert stories[1]["action"] == "pay by UPI"
    assert stories[0]["priority"] == "Must"
    assert stories[0]["text"].startswith("As a customer, I want to search products")
    assert len(stories[0]["criteria"]) >= 2


def test_priority_levels():
    result = engine.generate(SAMPLE)
    by_actor = {s["actor"]: s["priority"] for s in result["stories"]}
    assert by_actor["Administrator"] == "Must"
    assert result["stories"][-1]["priority"] == "Could"


def test_diagrams_are_valid_mermaid_text():
    d = engine.generate(SAMPLE)["diagrams"]
    assert d["use_case"].startswith("flowchart LR")
    assert d["class"].startswith("classDiagram")
    assert d["sequence"].startswith("sequenceDiagram")
    assert "Customer" in d["class"] and "Payment" in d["class"]


def test_update_only_changes_what_changed():
    v1 = engine.generate(SAMPLE)
    new_text = (
        "We need an online shop where customers can search products and pay by UPI.\n"   # same
        "Admin must manage product stock and view sales reports.\n"                      # edited
        "Customers can track their orders."                                              # new; reviews removed
    )
    v2 = engine.update(v1["requirements"], v1["stories"], new_text)

    assert v2["summary"] == {"added": 1, "modified": 1, "removed": 1, "unchanged": 1}
    ids_v1 = {s["id"] for s in v1["stories"] if s["source"].startswith("We need")}
    ids_v2 = {s["id"] for s in v2["stories"] if s["source"].startswith("We need")}
    assert ids_v1 == ids_v2                      # unchanged requirement keeps its story ids
    new_ids = [s["id"] for s in v2["stories"]]
    assert len(new_ids) == len(set(new_ids))     # no duplicate ids


def test_empty_text_gives_no_stories():
    assert engine.generate("hi")["stories"] == []
