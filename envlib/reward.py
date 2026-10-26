"""Shaped reward from scene state, error taxonomy, and code extraction."""
import re

from .tasks import checks_for

# Partial credit for running cleanly and for each passed check, plus a bonus for a full pass.
DEFAULT_WEIGHTS = {"ran": 0.1, "checks": 0.5, "full": 0.4}

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)
_THINK = re.compile(r"<think>.*?</think>", re.S)


def extract_code(text: str) -> str:
    text = _THINK.sub("", text or "")
    blocks = _FENCE.findall(text)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    if "```" in text:              # unterminated fence: take what follows it
        return text.split("```", 1)[1].removeprefix("python").strip() + "\n"
    return text.strip() + "\n"


def score(state, err, task, weights=None):
    """Returns (reward, passed_checks list)."""
    w = weights or DEFAULT_WEIGHTS
    if err is not None or state is None:
        return 0.0, []
    passed = checks_for(task)(state)
    frac = sum(passed) / len(passed) if passed else 0.0
    full = bool(passed) and all(passed)
    return w["ran"] + w["checks"] * frac + w["full"] * full, passed


def classify_error(err, passed=None):
    if err is None:
        return "pass" if passed and all(passed) else "ran_but_failed"
    if err == "timeout":
        return "timeout"
    if "SyntaxError" in err or "IndentationError" in err:
        return "syntax"
    if "AttributeError" in err or "has no attribute" in err:
        return "bpy_attribute"
    if "TypeError" in err or "keyword" in err:
        return "bpy_type_or_arg"
    if "KeyError" in err or "not found" in err:
        return "key_or_lookup"
    if "RuntimeError" in err or "context is incorrect" in err or "poll()" in err:
        return "bpy_runtime"
    if "NameError" in err or "ImportError" in err or "ModuleNotFoundError" in err:
        return "name_or_import"
    return "other_error"
