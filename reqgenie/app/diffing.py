"""Change detection: compare old and new requirement lists (the adaptive part)."""
import re
from difflib import SequenceMatcher


# Two sentences at least this similar count as "the same requirement, edited".
SIMILARITY_THRESHOLD = 0.6


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


def compare(old: list[str], new: list[str]):
    """Return (matches, removed).

    matches[i] = (status, old_index) for new[i]; status is
    'unchanged', 'modified' or 'added'. removed = old indexes with no match.
    """
    unused = set(range(len(old)))
    matches = [None] * len(new)

    for i, n in enumerate(new):                       # pass 1: identical text
        for j in sorted(unused):
            if _norm(old[j]) == _norm(n):
                matches[i] = ("unchanged", j)
                unused.discard(j)
                break

    for i, n in enumerate(new):                       # pass 2: similar text = edited
        if matches[i] is not None:
            continue
        best, best_j = 0.0, None
        for j in unused:
            ratio = SequenceMatcher(None, _norm(old[j]), _norm(n)).ratio()
            if ratio >= SIMILARITY_THRESHOLD and ratio > best:
                best, best_j = ratio, j
        if best_j is None:
            matches[i] = ("added", None)
        else:
            matches[i] = ("modified", best_j)
            unused.discard(best_j)

    return matches, sorted(unused)
