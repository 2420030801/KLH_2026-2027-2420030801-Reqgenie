"""Export a version as Markdown (with Mermaid diagrams) or a JIRA-importable CSV."""
import csv
import io

JIRA_PRIORITY = {"Must": "Highest", "Should": "High", "Could": "Medium", "Won't": "Low"}


def to_markdown(name: str, version: int, data: dict) -> str:
    out = [f"# {name} (version {version})", "", "## User stories", ""]
    for s in data["stories"]:
        out.append(f"### {s['id']} [{s['priority']}]")
        out.append(s["text"])
        out.append("")
        out.append("Acceptance criteria:")
        out += [f"- {c}" for c in s["criteria"]]
        out.append("")
    titles = {"use_case": "Use case diagram", "class": "Class diagram",
              "sequence": "Sequence diagram"}
    for key, title in titles.items():
        out += [f"## {title}", "", "```mermaid", data["diagrams"][key], "```", ""]
    return "\n".join(out)


def to_jira_csv(data: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Summary", "Issue Type", "Priority", "Description", "Labels"])
    for s in data["stories"]:
        description = s["text"] + "\n\nAcceptance criteria:\n" + "\n".join(
            f"* {c}" for c in s["criteria"])
        summary = s["action"][:1].upper() + s["action"][1:]
        writer.writerow([f"{s['id']} {summary}", "Story",
                         JIRA_PRIORITY.get(s["priority"], "Medium"), description, "reqgenie"])
    return buf.getvalue()
