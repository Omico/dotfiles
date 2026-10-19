"""Generate a standalone fish completion file after Android CLI upgrades.

Only --help runs during generation. Generated completions execute
no Android CLI or Python processes. Failed generation preserves the old file.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict


class Entry(TypedDict):
    description: str
    takes_value: bool
    path_kind: str


class Command(TypedDict):
    commands: dict[str, str]
    options: dict[str, Entry]
    positionals: list[Entry]


def path_kind(label: str, description: str) -> str:
    text = description.lower()
    if re.search(r"\bfilename\b", text) or label.split("=", 1)[0] == "--screenshot":
        return "file"
    if re.search(r"\b(file|files|apk|apks)\b", text) and (
        re.search(r"\bpaths?\b", text) or "output" in label or "file" in label
    ):
        return "file"
    if re.search(r"\b(directory|directories|folder|project root)\b", text):
        return "directory"
    if label.split("=", 1)[0] == "--sdk":
        return "directory"
    if re.search(r"\bpaths?\b", text):
        return "file"
    return ""


def parse_help(text: str) -> Command:
    result: Command = {"commands": {}, "options": {}, "positionals": []}
    section = "options"  # Root help omits the Options heading.
    label = ""
    fragments: list[str] = []

    def flush() -> None:
        if not label:
            return
        description = " ".join(fragments)
        if section == "commands":
            result["commands"][label] = description
            return
        entry: Entry = {
            "description": description,
            "takes_value": "=" in label or section == "positionals",
            "path_kind": path_kind(label, description),
        }
        if section == "positionals":
            result["positionals"].append(entry)
        else:
            for flag in re.findall(r"(?<!\w)--?[A-Za-z][A-Za-z0-9_-]*", label):
                result["options"][flag] = entry

    for line in text.splitlines():
        heading = line.strip()
        if heading in ("Commands:", "Options:", "Positional Parameters:") or (
            line and not line[0].isspace() and heading.endswith(" options:")
        ):
            flush()
            label, fragments = "", []
            section = (
                "commands"
                if heading == "Commands:"
                else "positionals"
                if heading == "Positional Parameters:"
                else "options"
            )
            continue
        new_entry = (
            re.match(r"^  [a-z][\w-]*\s{2,}", line)
            if section == "commands"
            else re.match(r"^ {2,6}--?[A-Za-z][\w-]*(?:[=, ]|$)", line)
            if section == "options"
            else re.match(r"^  <[^>]+>", line)
        )
        if new_entry:
            flush()
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
            label, fragments = parts[0], parts[1:]
        elif label and line[:1].isspace() and heading:
            fragments.append(heading)
        else:
            flush()
            label, fragments = "", []
    flush()
    if "--help" not in result["options"]:
        raise ValueError("Unrecognized Android help format")
    return result


def invoke(binary: str, args: list[str]) -> str:
    return subprocess.run(
        [binary, *args], capture_output=True, text=True, check=True, timeout=15
    ).stdout.strip()


def generate(binary: str) -> dict[str, Command]:
    commands: dict[str, Command] = {}
    pending: list[list[str]] = [[]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        while pending:
            if len(commands) + len(pending) > 256 or any(len(p) > 12 for p in pending):
                raise ValueError("Unexpected Android command tree")
            records = list(
                pool.map(
                    lambda path: parse_help(invoke(binary, [*path, "--help"])), pending
                )
            )
            next_pending: list[list[str]] = []
            for path, record in zip(pending, records, strict=True):
                commands[" ".join(path)] = record
                # The help pseudo-command mirrors the tree; do not recurse into it.
                next_pending.extend(
                    [*path, child] for child in record["commands"] if child != "help"
                )
            pending = next_pending
    return commands


def quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


RUNTIME = r"""#!/usr/bin/env fish
# Generated from Android CLI help by chezmoi; do not edit.

complete -c android -e
set --erase __android_completion_key

function __android_completion_resolve
    set -l tokens (commandline --current-process --tokenize --cut-at-cursor)
    set -l key (string join \x1e -- $tokens)
    if set -q __android_completion_key; and test "$key" = "$__android_completion_key"
        return
    end
    set -g __android_completion_key "$key"
    set -g __android_completion_context ''
    set -g __android_completion_awaiting ''
    set -g __android_completion_position 0
    set -l end_options 0
    for token in $tokens[2..-1]
        if test -n "$__android_completion_awaiting"
            set -g __android_completion_awaiting ''
            continue
        end
        if test "$token" = --
            set end_options 1
            continue
        end
        if test $end_options -eq 0; and string match --quiet -- "-*" "$token"
            switch "$__android_completion_context|$token"
                case @VALUE_OPTIONS@
                    set -g __android_completion_awaiting "$token"
            end
            continue
        end
        set -l next (string join --no-empty " " -- "$__android_completion_context" "$token")
        if test $end_options -eq 0; and test $__android_completion_position -eq 0
            switch "$next"
                case @COMMAND_PATHS@
                    set -g __android_completion_context "$next"
                    continue
            end
        end
        set -g __android_completion_position (math $__android_completion_position + 1)
    end
end

function __android_completion_command
    __android_completion_resolve
    test "$__android_completion_context" = "$argv[1]"; or return 1
    test -z "$__android_completion_awaiting"; or return 1
    test $__android_completion_position -eq 0; or return 1
    not string match --quiet -- "-*" (commandline --current-token)
end

function __android_completion_option
    __android_completion_resolve
    contains -- "$__android_completion_context" $argv[2..-1]; or return 1
    if test -n "$__android_completion_awaiting"
        test "$__android_completion_awaiting" = "$argv[1]"
    else
        string match --quiet -- "-*" (commandline --current-token)
    end
end

function __android_completion_positional
    __android_completion_resolve
    test "$__android_completion_context" = "$argv[1]"; or return 1
    test -z "$__android_completion_awaiting"; or return 1
    test "$__android_completion_position" -eq "$argv[2]"; or return 1
    not string match --quiet -- "-*" (commandline --current-token)
end

complete -c android -f
"""


def render(commands: dict[str, Command]) -> str:
    value_options = [
        f"{context}|{flag}"
        for context, record in commands.items()
        for flag, entry in record["options"].items()
        if entry["takes_value"]
    ]
    runtime = RUNTIME.replace(
        "@VALUE_OPTIONS@", " ".join(map(quote, value_options)) or quote("<none>")
    )
    runtime = runtime.replace(
        "@COMMAND_PATHS@", " ".join(quote(c) for c in commands if c) or quote("<none>")
    )
    lines = [runtime.rstrip()]
    options: dict[tuple[str, str, bool, str], list[str]] = {}
    for context, record in commands.items():
        for child, description in record["commands"].items():
            condition = f"__android_completion_command {quote(context)}"
            lines.append(
                f"complete -c android -n {quote(condition)} -a {quote(child)} -d {quote(short(description))}"
            )
        for flag, entry in record["options"].items():
            key = flag, entry["description"], entry["takes_value"], entry["path_kind"]
            options.setdefault(key, []).append(context)
        for index, entry in enumerate(record["positionals"]):
            if not entry["path_kind"]:
                continue
            condition = f"__android_completion_positional {quote(context)} {index}"
            rule = f"complete -c android -n {quote(condition)}"
            rule += (
                " -F"
                if entry["path_kind"] == "file"
                else " -a '(__fish_complete_directories)'"
            )
            lines.append(rule)
    for (flag, description, takes_value, kind), contexts in options.items():
        condition = "__android_completion_option " + " ".join(
            map(quote, [flag, *contexts])
        )
        option = (
            "-l " + quote(flag[2:])
            if flag.startswith("--")
            else "-s " + quote(flag[1:])
        )
        rule = f"complete -c android -n {quote(condition)} {option} -d {quote(short(description))}"
        if takes_value:
            if kind == "file":
                rule += " -r -F"
            else:
                rule += " -x"
                if kind == "directory":
                    rule += " -a '(__fish_complete_directories)'"
        lines.append(rule)
    return "\n".join(lines) + "\n"


def short(description: str) -> str:
    return (
        description
        if len(description) <= 100
        else description[:97].rsplit(" ", 1)[0] + "..."
    )


def write_completion(binary: str, output: Path) -> None:
    text = render(generate(binary))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as stream:
            temporary = stream.name
            stream.write(text)
        subprocess.run(
            ["fish", "--no-execute", temporary],
            check=True,
            capture_output=True,
            timeout=15,
        )
        if formatter := shutil.which("fish_indent"):
            subprocess.run(
                [formatter, "-w", temporary],
                check=True,
                capture_output=True,
                timeout=15,
            )
        os.chmod(temporary, output.stat().st_mode & 0o777 if output.exists() else 0o644)
        os.replace(temporary, output)
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


def main() -> int:
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android", default=shutil.which("android"))
    parser.add_argument(
        "--output", type=Path, default=config / "fish/completions/android.fish"
    )
    args = parser.parse_args()
    if not args.android:
        parser.error("android is not on PATH")
    try:
        write_completion(args.android, args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(
            f"Android completion generation failed; previous file preserved: {error}",
            file=sys.stderr,
        )
        return 1
    print("Generated Android fish completions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
