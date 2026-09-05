#!/usr/bin/env python3
"""Validate the structural authoring contract for a Factory Mission brief.

This validator intentionally does not claim to validate Factory runtime
acceptance, semantic quality, architectural correctness, or safety.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


REQUIRED_SECTIONS = (
    "mission type",
    "outcome",
    "validation contract",
    "non-goals",
    "invariants",
    "environment and harness",
    "features",
    "milestones",
    "capabilities and execution",
    "stop conditions",
)

ASSERTION_ID = re.compile(r"\bVAL-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
ASSERTION_START = re.compile(
    r"\*\*(VAL-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b", re.IGNORECASE
)
FEATURE_START = re.compile(r"\*\*(F\d+)\b", re.IGNORECASE)
MILESTONE_START = re.compile(r"\*\*(M\d+)\b", re.IGNORECASE)
FIELD_NAMES = ("Behavior:", "Check:", "Evidence:")


@dataclass
class ValidationResult:
    path: str
    title: str = ""
    word_count: int = 0
    assertions: int = 0
    features: int = 0
    milestones: int = 0
    worker_run_floor: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["valid"] = self.valid
        return data


def extract_brief(text: str) -> tuple[str, list[str]]:
    fenced = re.findall(
        r"```(?:markdown|md)?[ \t]*\r?\n(.*?)```", text, flags=re.IGNORECASE | re.DOTALL
    )
    candidates = [block.strip() for block in fenced if "## Validation contract" in block]
    errors: list[str] = []
    if len(candidates) > 1:
        errors.append("Expected at most one fenced Mission brief.")
    if candidates:
        return candidates[0], errors
    return text.strip(), errors


def split_sections(brief: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##[ \t]+(.+?)[ \t]*$", brief, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(brief)
        key = re.sub(r"\s+", " ", match.group(1).strip().lower())
        sections[key] = brief[start:end].strip()
    return sections


def list_blocks(section: str) -> list[str]:
    pattern = re.compile(
        r"(?ms)^\s*(?:[-*]|\d+\.)\s+(.*?)(?=^\s*(?:[-*]|\d+\.)\s+|\Z)"
    )
    return [re.sub(r"\s+", " ", match.group(1).strip()) for match in pattern.finditer(section)]


def normalized_ids(text: str) -> list[str]:
    return [value.upper() for value in ASSERTION_ID.findall(text.upper())]


def validate_text(text: str, path: str = "<memory>") -> ValidationResult:
    brief, extraction_errors = extract_brief(text)
    result = ValidationResult(path=path, errors=extraction_errors)
    result.word_count = len(re.findall(r"\b[\w][\w'-]*\b", brief, flags=re.UNICODE))

    title_match = re.search(r"^#[ \t]+(?!#)(.+?)[ \t]*$", brief, flags=re.MULTILINE)
    if not title_match:
        result.errors.append("Missing level-one Mission title.")
    else:
        result.title = title_match.group(1).strip()
        title_words = re.findall(r"\b[\w][\w'-]*\b", result.title)
        if not 3 <= len(title_words) <= 8:
            result.errors.append("Mission title must contain 3-8 words.")

    sections = split_sections(brief)
    for required in REQUIRED_SECTIONS:
        if required not in sections or not sections[required].strip():
            result.errors.append(f"Missing or empty section: {required}.")

    if result.word_count > 900:
        result.errors.append(f"Mission brief has {result.word_count} words; maximum is 900.")

    assertion_blocks = list_blocks(sections.get("validation contract", ""))
    assertion_ids: list[str] = []
    milestone_only: set[str] = set()
    for block in assertion_blocks:
        match = ASSERTION_START.search(block)
        if not match:
            result.errors.append("Every validation bullet must start with a bold VAL-* ID.")
            continue
        assertion_id = match.group(1).upper()
        assertion_ids.append(assertion_id)
        missing_fields = [name for name in FIELD_NAMES if name.lower() not in block.lower()]
        if missing_fields:
            result.errors.append(
                f"{assertion_id} is missing fields: {', '.join(missing_fields)}"
            )
        if "milestone-only" in block.lower():
            milestone_only.add(assertion_id)

    result.assertions = len(assertion_ids)
    if not 5 <= result.assertions <= 15:
        result.errors.append(
            f"Validation contract must contain 5-15 assertions; found {result.assertions}."
        )
    duplicates = sorted({value for value in assertion_ids if assertion_ids.count(value) > 1})
    if duplicates:
        result.errors.append(f"Duplicate assertion IDs: {', '.join(duplicates)}")
    valid_assertions = set(assertion_ids)

    feature_blocks = list_blocks(sections.get("features", ""))
    feature_ids: list[str] = []
    feature_coverage: set[str] = set()
    for block in feature_blocks:
        match = FEATURE_START.search(block)
        if not match:
            result.errors.append("Every feature bullet must start with a bold F<number> ID.")
            continue
        feature_id = match.group(1).upper()
        feature_ids.append(feature_id)
        refs = set(normalized_ids(block))
        if not refs:
            result.errors.append(f"{feature_id} does not reference a validation assertion.")
        unknown = sorted(refs - valid_assertions)
        if unknown:
            result.errors.append(f"{feature_id} references unknown assertions: {', '.join(unknown)}")
        feature_coverage.update(refs & valid_assertions)

    result.features = len(feature_ids)
    if not feature_ids:
        result.errors.append("At least one feature is required.")
    duplicate_features = sorted({value for value in feature_ids if feature_ids.count(value) > 1})
    if duplicate_features:
        result.errors.append(f"Duplicate feature IDs: {', '.join(duplicate_features)}")

    milestone_blocks = list_blocks(sections.get("milestones", ""))
    milestone_ids: list[str] = []
    milestone_coverage: set[str] = set()
    for block in milestone_blocks:
        match = MILESTONE_START.search(block)
        if not match:
            result.errors.append("Every milestone bullet must start with a bold M<number> ID.")
            continue
        milestone_id = match.group(1).upper()
        milestone_ids.append(milestone_id)
        if "exit:" not in block.lower():
            result.errors.append(f"{milestone_id} is missing an Exit: clause.")
        refs = set(normalized_ids(block))
        if not refs:
            result.errors.append(f"{milestone_id} has no assertion-based exit criteria.")
        unknown = sorted(refs - valid_assertions)
        if unknown:
            result.errors.append(
                f"{milestone_id} references unknown assertions: {', '.join(unknown)}"
            )
        milestone_coverage.update(refs & valid_assertions)

    result.milestones = len(milestone_ids)
    if not 1 <= result.milestones <= 7:
        result.errors.append(f"Mission must contain 1-7 milestones; found {result.milestones}.")
    elif not 2 <= result.milestones <= 5:
        result.warnings.append(
            f"Found {result.milestones} milestone(s); 2-5 is the usual authoring range."
        )
    duplicate_milestones = sorted(
        {value for value in milestone_ids if milestone_ids.count(value) > 1}
    )
    if duplicate_milestones:
        result.errors.append(f"Duplicate milestone IDs: {', '.join(duplicate_milestones)}")

    uncovered = sorted(valid_assertions - feature_coverage - milestone_only)
    if uncovered:
        result.errors.append(f"Assertions not covered by a feature: {', '.join(uncovered)}")
    missing_milestone_exit = sorted(valid_assertions - milestone_coverage)
    if missing_milestone_exit:
        result.warnings.append(
            "Assertions absent from milestone exit criteria: "
            + ", ".join(missing_milestone_exit)
        )

    result.worker_run_floor = result.features + 2 * result.milestones
    return result


def validate_file(path: Path) -> ValidationResult:
    return validate_text(path.read_text(encoding="utf-8"), str(path))


def render_text(result: ValidationResult) -> str:
    status = "PASS" if result.valid else "FAIL"
    lines = [
        f"{status}: {result.path}",
        f"title: {result.title or '<missing>'}",
        f"words: {result.word_count}",
        f"assertions: {result.assertions}",
        f"features: {result.features}",
        f"milestones: {result.milestones}",
        f"initial worker-run floor: {result.worker_run_floor}",
    ]
    lines.extend(f"ERROR: {message}" for message in result.errors)
    lines.extend(f"WARNING: {message}" for message in result.warnings)
    lines.append(
        "Scope: structural authoring checks only; semantic and Factory runtime review remain required."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path, help="Markdown brief or response containing one")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        result = validate_file(args.brief)
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: unable to read {args.brief}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(render_text(result))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
