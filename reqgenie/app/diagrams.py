"""Build Mermaid UML diagrams (use case, class, sequence) from user stories."""
import re


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 \-]", "", text)).strip()


def _ident(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text) or "X"


def use_case_diagram(stories: list[dict]) -> str:
    if not stories:
        return "flowchart LR\n  Empty[\"No requirements yet\"]"
    lines = ["flowchart LR"]
    actors, cases = {}, {}
    for s in stories:
        if s["actor"] not in actors:
            actors[s["actor"]] = f"A{len(actors) + 1}"
            lines.append(f'  {actors[s["actor"]]}(["{_clean(s["actor"])}"])')
    for s in stories:
        key = s["action"]
        if key not in cases:
            cases[key] = f"UC{len(cases) + 1}"
            cleaned = _clean(key)
            label = (cleaned[:1].upper() + cleaned[1:]) or "Use case"
            lines.append(f'  {cases[key]}("{label}")')
        lines.append(f"  {actors[s['actor']]} --> {cases[key]}")
    return "\n".join(lines)


def class_diagram(stories: list[dict]) -> str:
    lines = ["classDiagram"]
    if not stories:
        return "classDiagram\n  class Empty"
    actor_methods: dict[str, set] = {}
    entities: set = set()
    relations: set = set()
    for s in stories:
        actor = _ident(s["actor"])
        method = re.sub(r"[^a-z]", "", s["verb"].lower()) or "act"
        actor_methods.setdefault(actor, set()).add(method)
        entity = _ident(s["entity"])
        entities.add(entity)
        relations.add((actor, entity, method))
    for actor, methods in actor_methods.items():
        lines.append(f"  class {actor} {{")
        lines += [f"    +{m}()" for m in sorted(methods)]
        lines.append("  }")
    for entity in sorted(entities - set(actor_methods)):
        lines.append(f"  class {entity} {{")
        lines.append("    +id")
        lines.append("    +status")
        lines.append("  }")
    for actor, entity, method in sorted(relations):
        if actor != entity:
            lines.append(f"  {actor} --> {entity} : {method}")
    return "\n".join(lines)


def sequence_diagram(stories: list[dict], limit: int = 8) -> str:
    lines = ["sequenceDiagram", "  autonumber"]
    if not stories:
        return "sequenceDiagram\n  Note over System: No requirements yet"
    actors = []
    for s in stories:
        if s["actor"] != "System" and s["actor"] not in actors:
            actors.append(s["actor"])
    for a in actors:
        lines.append(f"  actor {_ident(a)}")
    lines.append("  participant System")
    lines.append("  participant Database")
    for s in stories[:limit]:
        who = "System" if s["actor"] == "System" else _ident(s["actor"])
        action = _clean(s["action"])[:60] or "request"
        lines.append(f"  {who}->>System: {action}")
        lines.append("  System->>Database: read or save data")
        lines.append("  Database-->>System: result")
        if who != "System":
            lines.append(f"  System-->>{who}: confirmation")
    return "\n".join(lines)


def build_diagrams(stories: list[dict]) -> dict:
    return {
        "use_case": use_case_diagram(stories),
        "class": class_diagram(stories),
        "sequence": sequence_diagram(stories),
    }
