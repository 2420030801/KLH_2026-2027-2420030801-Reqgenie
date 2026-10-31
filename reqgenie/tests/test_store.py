from app import engine, store
from app.export import to_jira_csv, to_markdown


def test_versions_are_numbered_and_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("REQGENIE_DB", str(tmp_path / "t.db"))
    text1 = "Customers can search products.\nAdmin must manage stock."
    text2 = "Customers can search products.\nAdmin must manage stock and view reports."

    pid = store.create_project("Shop")
    r1 = engine.generate(text1)
    assert store.add_version(pid, text1, r1) == 1

    prev = store.get_version(pid)
    r2 = engine.update(prev["requirements"], prev["stories"], text2)
    assert store.add_version(pid, text2, r2) == 2

    assert [v["version"] for v in store.list_versions(pid)] == [1, 2]
    assert len(store.get_version(pid, 1)["stories"]) == 2     # old version is untouched
    assert len(store.get_version(pid, 2)["stories"]) == 3
    assert store.get_version(pid, 99) is None
    assert store.list_projects()[0]["latest_version"] == 2


def test_exports_contain_stories_and_diagrams():
    data = engine.generate("Customers can search products and pay by UPI.")
    md = to_markdown("Shop", 1, data)
    assert "US-001" in md and "```mermaid" in md and "classDiagram" in md
    csv_text = to_jira_csv(data)
    assert csv_text.startswith("Summary,Issue Type,Priority,Description,Labels")
    assert "Highest" in csv_text or "High" in csv_text


def test_pronouns_are_first_person():
    story = engine.generate("Customers must be able to track their orders.")["stories"][0]
    assert "track my orders" in story["text"]
