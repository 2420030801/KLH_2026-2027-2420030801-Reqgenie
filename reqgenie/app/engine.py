"""Orchestration: generate a full result, or adapt an earlier one to changed requirements."""
import re

from .diagrams import build_diagrams
from .diffing import compare
from .nlp import analyse_requirement, split_requirements


def _next_number(stories: list[dict]) -> int:
    nums = [int(m.group(1)) for s in stories if (m := re.match(r"US-(\d+)$", s.get("id", "")))]
    return max(nums, default=0) + 1


def _fmt(n: int) -> str:
    return f"US-{n:03d}"


def generate(text: str) -> dict:
    """First version: analyse every requirement from scratch."""
    requirements = split_requirements(text)
    stories, n = [], 1
    for req in requirements:
        for story in analyse_requirement(req):
            story["id"] = _fmt(n)
            n += 1
            stories.append(story)
    changes = [{"status": "added", "requirement": r, "previous": None, "stories": []}
               for r in requirements]
    for ch in changes:
        ch["stories"] = [s["id"] for s in stories if s["source"] == ch["requirement"]]
    return _result(requirements, stories, changes)


def update(prev_requirements: list[str], prev_stories: list[dict], new_text: str) -> dict:
    """Adaptive update: keep unchanged stories, regenerate only what changed."""
    new_reqs = split_requirements(new_text)
    matches, removed = compare(prev_requirements, new_reqs)
    counter = _next_number(prev_stories)
    stories, changes = [], []

    for req, (status, old_idx) in zip(new_reqs, matches):
        old_source = prev_requirements[old_idx] if old_idx is not None else None
        old_stories = [s for s in prev_stories if s["source"] == old_source] if old_source else []

        if status == "unchanged":
            kept = []
            for s in old_stories:
                s = dict(s, source=req)
                kept.append(s)
            stories += kept
            changes.append({"status": "unchanged", "requirement": req, "previous": None,
                            "stories": [s["id"] for s in kept]})
            continue

        fresh = analyse_requirement(req)
        reusable_ids = [s["id"] for s in old_stories]
        for story in fresh:
            if reusable_ids:
                story["id"] = reusable_ids.pop(0)
            else:
                story["id"] = _fmt(counter)
                counter += 1
        stories += fresh
        changes.append({"status": status, "requirement": req, "previous": old_source,
                        "stories": [s["id"] for s in fresh]})

    for idx in removed:
        gone = prev_requirements[idx]
        ids = [s["id"] for s in prev_stories if s["source"] == gone]
        changes.append({"status": "removed", "requirement": gone, "previous": None,
                        "stories": ids})

    return _result(new_reqs, stories, changes)


def _result(requirements, stories, changes) -> dict:
    summary = {k: 0 for k in ("added", "modified", "removed", "unchanged")}
    for ch in changes:
        summary[ch["status"]] += 1
    return {
        "requirements": requirements,
        "stories": stories,
        "diagrams": build_diagrams(stories),
        "changes": changes,
        "summary": summary,
    }
