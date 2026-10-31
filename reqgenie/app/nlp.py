"""Requirement analysis: raw client text -> user stories with acceptance criteria.

This is a rule-based analyser, so the project runs offline with no API key.
`analyse_requirement()` is the single entry point; swap its body for an LLM
call later without changing the rest of the system.
"""
import re

ACTORS = {
    "customer", "user", "admin", "administrator", "manager", "student", "teacher",
    "employee", "doctor", "patient", "seller", "vendor", "client", "staff",
    "visitor", "guest", "member", "librarian", "driver", "rider", "parent",
}

VERB_LIST = [
    "search", "browse", "view", "add", "remove", "delete", "edit", "update",
    "create", "pay", "checkout", "track", "login", "log in", "sign in", "register",
    "sign up", "logout", "log out", "upload", "download", "send", "receive",
    "manage", "book", "cancel", "order", "purchase", "buy", "compare", "filter",
    "sort", "rate", "review", "comment", "share", "schedule", "generate", "export",
    "import", "print", "reset", "select", "choose", "apply", "submit", "approve",
    "reject", "monitor", "notify", "chat", "ask", "report", "enroll", "access",
    "save", "join", "find", "read", "write", "check", "make", "get", "see", "use",
    "have", "pay",
]
VERB_RE = "|".join(sorted((re.escape(v) for v in set(VERB_LIST)), key=len, reverse=True))

STRONG_MODAL = (r"(?:must be able to|should be able to|shall be able to|can also|"
                r"can|could|may|must|shall|should|will)")
WEAK_MODAL = r"(?:need to|needs to|want to|wants to|would like to|wish to|have to|has to)"

STOP_WORDS = {"a", "an", "the", "my", "their", "his", "her", "our", "all", "any",
              "some", "own", "your", "its"}
PREPOSITIONS = {"by", "with", "using", "via", "from", "to", "for", "in", "on",
                "through", "at", "of", "into"}

# Verbs whose object is always the same domain entity.
FORCED_ENTITY = {
    "pay": "Payment", "login": "Account", "log in": "Account", "sign in": "Account",
    "register": "Account", "sign up": "Account", "logout": "Account",
    "log out": "Account", "checkout": "Order",
}

BENEFITS = {
    "search": "I can find what I need quickly",
    "browse": "I can discover what is available",
    "view": "I can stay informed",
    "add": "I can build up what I need",
    "remove": "I can correct my choices",
    "delete": "I can keep my data clean",
    "edit": "I can keep my information correct",
    "update": "I can keep my information up to date",
    "create": "I can start new work",
    "pay": "I can complete my purchase securely",
    "checkout": "I can complete my purchase",
    "track": "I know the current status",
    "login": "I can access my account securely",
    "log in": "I can access my account securely",
    "sign in": "I can access my account securely",
    "register": "I can get a personal account",
    "sign up": "I can get a personal account",
    "upload": "I can share my files",
    "download": "I can keep a copy offline",
    "book": "I can reserve what I need in advance",
    "cancel": "I can change my mind without penalty",
    "notify": "I never miss important updates",
    "manage": "I stay in control",
    "report": "I can understand what is happening",
}
DEFAULT_BENEFIT = "I can get my work done efficiently"

SPECIFIC_CRITERIA = {
    "search": ["Matching results appear in under 3 seconds",
               "A clear message is shown when nothing matches"],
    "pay": ["The payment status (success or failure) is shown immediately",
            "A failed payment can be retried without losing the order"],
    "checkout": ["The order total is shown before confirming",
                 "An order confirmation is generated"],
    "login": ["Wrong credentials show a clear error message",
              "Passwords are never displayed in plain text"],
    "register": ["A duplicate email address is rejected",
                 "A confirmation is shown after successful registration"],
    "upload": ["Unsupported file types are rejected with a message",
               "Upload progress is visible to the user"],
    "download": ["The downloaded file opens correctly"],
    "track": ["The latest status is always displayed",
              "Status changes appear without manual refresh"],
    "add": ["The new item appears in the list immediately"],
    "delete": ["The user must confirm before anything is deleted"],
    "cancel": ["The user must confirm before cancelling",
               "The cancellation is reflected in the status"],
    "notify": ["The notification is delivered within 1 minute"],
    "book": ["Double booking of the same slot is prevented"],
    "export": ["The exported file contains all visible data"],
}
SPECIFIC_CRITERIA["log in"] = SPECIFIC_CRITERIA["sign in"] = SPECIFIC_CRITERIA["login"]
SPECIFIC_CRITERIA["sign up"] = SPECIFIC_CRITERIA["register"]


def split_requirements(text: str) -> list[str]:
    """Split raw notes into one requirement per sentence or bullet."""
    out = []
    for line in re.split(r"[\r\n]+", text or ""):
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        if not line:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip().rstrip(".!?").strip()
            if len(sentence.split()) >= 3:
                out.append(sentence)
    return out


def find_actor(sentence: str) -> str:
    low = sentence.lower()
    if re.search(r"\b(?:system|application|app|platform|website|portal)\s+"
                 r"(?:should|must|shall|will|can)\b", low):
        return "System"
    for word in re.findall(r"[a-z]+", low):
        base = word[:-1] if word.endswith("s") and word[:-1] in ACTORS else word
        if base in ACTORS:
            return "Administrator" if base in ("admin", "administrator") else base.capitalize()
    return "User"


def detect_priority(sentence: str) -> str:
    low = sentence.lower()
    if re.search(r"\b(won't|will not|later|future|out of scope)\b", low):
        return "Won't"
    if re.search(r"\b(must|shall|mandatory|required|essential|critical|need|needs|have to|has to)\b", low):
        return "Must"
    if re.search(r"\b(could|may|optional|nice to have|if possible)\b", low):
        return "Could"
    return "Should"


def find_action_phrase(sentence: str) -> str:
    m = re.search(rf"\b{STRONG_MODAL}\b\s+(.+)$", sentence, re.I)
    if not m:
        m = re.search(rf"\b{WEAK_MODAL}\b\s+(.+)$", sentence, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b(?:need|needs|want|wants|require|requires)\s+(.+)$", sentence, re.I)
    if m:
        return "have " + m.group(1)
    return sentence


def split_actions(phrase: str) -> list[str]:
    phrase = re.split(r"\b(?:so that|in order to|because)\b", phrase, flags=re.I)[0]
    phrase = phrase.strip(" ,;")
    parts = re.split(rf"(?:,\s*(?:and\s+)?|\s+and\s+)(?=(?:{VERB_RE})\b)", phrase, flags=re.I)
    return [p.strip(" ,;") for p in parts if p.strip(" ,;")]


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ss") or not word.endswith("s"):
        return word
    return word[:-1]


def find_verb_and_entity(action: str) -> tuple[str, str]:
    low = action.lower()
    m = re.match(rf"({VERB_RE})\b\s*(.*)", low)
    if m:
        verb, rest = m.group(1), m.group(2)
    else:
        parts = low.split()
        verb, rest = (parts[0] if parts else "do"), " ".join(parts[1:])
    if verb in FORCED_ENTITY:
        return verb, FORCED_ENTITY[verb]
    words = []
    for w in re.findall(r"[a-z]+", rest):
        if w in PREPOSITIONS:
            if words:
                break
            continue
        if w in STOP_WORDS:
            continue
        words.append(w)
    entity = _singular(words[-1]).capitalize() if words else "Record"
    return verb, entity


def find_benefit(sentence: str, verb: str) -> str:
    m = re.search(r"\b(?:so that|in order to)\s+(.+)$", sentence, re.I)
    if m:
        return m.group(1).strip()
    return BENEFITS.get(verb, DEFAULT_BENEFIT)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def acceptance_criteria(actor: str, action: str, verb: str) -> list[str]:
    criteria = [f"Given the {actor.lower()} is on the application, when they {action}, "
                f"then the system completes the request and shows a confirmation"]
    criteria += SPECIFIC_CRITERIA.get(verb, [])[:2]
    if len(criteria) < 3:
        criteria.append("A clear error message is shown if the request fails")
    return criteria


def analyse_requirement(sentence: str) -> list[dict]:
    """One requirement sentence -> one or more user stories (no ids yet)."""
    actor = find_actor(sentence)
    priority = detect_priority(sentence)
    stories = []
    for action in split_actions(find_action_phrase(sentence)):
        action = re.sub(r"\b(?:their|his|her)\b", "my", action[:1].lower() + action[1:])
        verb, entity = find_verb_and_entity(action)
        benefit = find_benefit(sentence, verb)
        lead = "the system" if actor == "System" else f"{_article(actor)} {actor.lower()}"
        stories.append({
            "actor": actor,
            "action": action,
            "verb": verb,
            "entity": entity,
            "benefit": benefit,
            "priority": priority,
            "text": f"As {lead}, I want to {action} so that {benefit}.",
            "criteria": acceptance_criteria(actor, action, verb),
            "source": sentence,
        })
    return stories
