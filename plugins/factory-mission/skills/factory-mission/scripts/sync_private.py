#!/usr/bin/env python3
"""Synchronize a public skill into a private user-level skill with an overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MANIFEST_NAME = ".factory-mission-sync.json"


class SyncError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise SyncError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise SyncError(f"Unsupported overlay schema: {path}")
    return data


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def safe_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise SyncError(f"Unsafe relative path: {value}")
    return path


def copy_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts or path.name == MANIFEST_NAME:
            continue
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def apply_overlay(staging: Path, overlay_dir: Path, overlay: dict[str, Any]) -> None:
    for operation in overlay.get("text_operations", []):
        relative = safe_relative(str(operation.get("path", "")))
        path = staging / relative
        if not path.is_file():
            raise SyncError(f"Text operation target is missing: {relative}")
        text = path.read_text(encoding="utf-8")
        anchor = operation.get("after")
        fragment_file = safe_relative(str(operation.get("fragment", "")))
        fragment = (overlay_dir / fragment_file).read_text(encoding="utf-8")
        if not isinstance(anchor, str) or text.count(anchor) != 1:
            raise SyncError(f"Expected one insertion anchor in {relative}")
        path.write_text(text.replace(anchor, anchor + fragment), encoding="utf-8", newline="\n")

    for item in overlay.get("files", []):
        source = overlay_dir / safe_relative(str(item.get("source", "")))
        destination = staging / safe_relative(str(item.get("target", "")))
        if not source.is_file():
            raise SyncError(f"Overlay file is missing: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    skill = staging / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    suffix = overlay.get("version_suffix", "")
    if suffix:
        marker = "  version: "
        lines = text.splitlines()
        matches = [index for index, line in enumerate(lines) if line.startswith(marker)]
        if len(matches) != 1:
            raise SyncError("SKILL.md must contain one metadata version")
        index = matches[0]
        lines[index] = lines[index] + str(suffix)
        metadata = overlay.get("metadata", {})
        for key, value in metadata.items():
            encoded = json.dumps(value) if not isinstance(value, str) else value
            lines.insert(index + 1, f"  {key}: {encoded}")
            index += 1
        text = "\n".join(lines) + "\n"
        skill.write_text(text, encoding="utf-8", newline="\n")

    evals = staging / "evals" / "evals.json"
    if evals.is_file() and suffix:
        data = json.loads(evals.read_text(encoding="utf-8"))
        data["version"] = str(data["version"]) + str(suffix)
        extra_file = overlay.get("extra_evals")
        if extra_file:
            extra = json.loads((overlay_dir / safe_relative(str(extra_file))).read_text(encoding="utf-8"))
            data["cases"].extend(extra)
        evals.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")

    replays = staging / "evals" / "replay" / "cases.json"
    extra_replays = overlay.get("extra_replays")
    if replays.is_file() and extra_replays:
        data = json.loads(replays.read_text(encoding="utf-8"))
        extra = json.loads(
            (overlay_dir / safe_relative(str(extra_replays))).read_text(encoding="utf-8")
        )
        data["cases"].extend(extra)
        replays.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def files_with_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != MANIFEST_NAME and "__pycache__" not in path.parts
    }


def ensure_no_unexpected_modifications(target: Path, previous: dict[str, Any]) -> None:
    for relative, expected in previous.get("files", {}).items():
        path = target / safe_relative(relative)
        if path.exists() and sha256(path) != expected:
            raise SyncError(f"Private managed file changed since the last sync: {relative}")


def install(
    staging: Path,
    target: Path,
    backup: Path | None,
    adopt_existing: bool,
    source_label: str,
) -> dict[str, Any]:
    target_existed = target.exists()
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / MANIFEST_NAME
    previous = read_json(manifest_path) if manifest_path.exists() else {"schema_version": 1, "files": {}}
    if target_existed and not manifest_path.exists() and files_with_hashes(target) != files_with_hashes(staging) and not adopt_existing:
        raise SyncError(
            "Target contains unmanaged differences; inspect with a dry run, then use --adopt-existing"
        )
    ensure_no_unexpected_modifications(target, previous)
    desired = files_with_hashes(staging)

    if backup:
        backup = backup.resolve()
        if backup.exists():
            raise SyncError(f"Backup already exists: {backup}")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, backup)

    for relative, old_hash in previous.get("files", {}).items():
        if relative not in desired:
            path = target / safe_relative(relative)
            if path.is_file() and sha256(path) == old_hash:
                path.unlink()
    for relative in desired:
        source = staging / safe_relative(relative)
        destination = target / safe_relative(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".sync-tmp")
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)

    result = {
        "schema_version": SCHEMA_VERSION,
        "source": source_label,
        "files": desired,
    }
    atomic_write_json(manifest_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Public skill directory")
    parser.add_argument("--target", required=True, help="Private skill directory")
    parser.add_argument("--overlay", required=True, help="Private overlay directory")
    parser.add_argument("--apply", action="store_true", help="Write the synchronized result")
    parser.add_argument("--backup", help="Optional backup directory used with --apply")
    parser.add_argument(
        "--adopt-existing",
        action="store_true",
        help="Allow the first sync to replace reviewed, unmanaged target differences",
    )
    args = parser.parse_args(argv)
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    overlay_dir = Path(args.overlay).resolve()
    try:
        if not (source / "SKILL.md").is_file():
            raise SyncError(f"Public skill is missing: {source}")
        overlay = read_json(overlay_dir / "overlay.json")
        with tempfile.TemporaryDirectory(prefix="factory-mission-private-") as temporary:
            staging = Path(temporary) / "skill"
            staging.mkdir()
            copy_tree(source, staging)
            apply_overlay(staging, overlay_dir, overlay)
            desired = files_with_hashes(staging)
            current = files_with_hashes(target) if target.exists() else {}
            changed = sorted(
                relative
                for relative in set(desired) | set(current)
                if desired.get(relative) != current.get(relative)
            )
            result: dict[str, Any] = {
                "aligned": not changed,
                "changed_files": changed,
                "desired_version": next(
                    line.strip().split(":", 1)[1].strip()
                    for line in (staging / "SKILL.md").read_text(encoding="utf-8").splitlines()
                    if line.startswith("  version:")
                ),
            }
            if args.apply:
                result["install"] = install(
                    staging,
                    target,
                    Path(args.backup) if args.backup else None,
                    args.adopt_existing,
                    str(source),
                )
                result["aligned"] = True
            print(json.dumps(result, indent=2))
            return 0 if result["aligned"] else 1
    except (SyncError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
