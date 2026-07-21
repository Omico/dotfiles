#!/usr/bin/env python3
"""Parse VS Code JSONC without changing source positions."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from typing import Any


class JsoncError(ValueError):
    """A JSONC error with stable source coordinates."""

    def __init__(self, message: str, *, line: int, column: int) -> None:
        super().__init__(message)
        self.line = line
        self.column = column


def source_coordinates(source: str, offset: int) -> tuple[int, int]:
    line = source.count("\n", 0, offset) + 1
    line_start = source.rfind("\n", 0, offset) + 1
    return line, offset - line_start + 1


def find_unquoted_token(source: str, token: str) -> int:
    index = 0
    in_string = False
    escaped = False

    while index < len(source):
        character = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue

        if character == '"':
            in_string = True
            index += 1
            continue
        if source.startswith(token, index):
            return index
        index += 1

    return 0


def strip_comments(source: str) -> str:
    characters = list(source)
    index = 0
    in_string = False
    escaped = False

    while index < len(characters):
        character = characters[index]

        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue

        if character == '"':
            in_string = True
            index += 1
            continue

        if character != "/" or index + 1 >= len(characters):
            index += 1
            continue

        marker = characters[index + 1]
        if marker == "/":
            while index < len(characters) and characters[index] not in "\r\n":
                characters[index] = " "
                index += 1
            continue

        if marker != "*":
            index += 1
            continue

        comment_start = index
        characters[index] = " "
        characters[index + 1] = " "
        index += 2
        while index + 1 < len(characters):
            if characters[index] == "*" and characters[index + 1] == "/":
                characters[index] = " "
                characters[index + 1] = " "
                index += 2
                break
            if characters[index] not in "\r\n":
                characters[index] = " "
            index += 1
        else:
            line, column = source_coordinates(source, comment_start)
            raise JsoncError(
                "unterminated block comment",
                line=line,
                column=column,
            )

    return "".join(characters)


def strip_trailing_commas(source: str) -> str:
    characters = list(source)
    index = 0
    in_string = False
    escaped = False

    while index < len(characters):
        character = characters[index]

        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue

        if character == '"':
            in_string = True
        elif character == ",":
            lookahead = index + 1
            while lookahead < len(characters) and characters[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < len(characters) and characters[lookahead] in "}]":
                previous = index - 1
                while previous >= 0 and characters[previous] in " \t\r\n":
                    previous -= 1
                if previous >= 0 and characters[previous] not in "{[,:":
                    characters[index] = " "
        index += 1

    return "".join(characters)


def normalize_jsonc(source: str) -> str:
    return strip_trailing_commas(strip_comments(source))


def load_jsonc_object(path: pathlib.Path) -> dict[str, Any]:
    if path.is_symlink():
        raise OSError(f"input path is a symlink: {path}")
    source = path.read_text(encoding="utf-8-sig")
    normalized = normalize_jsonc(source)

    def error_for_token(message: str, token: str) -> JsoncError:
        line, column = source_coordinates(normalized, find_unquoted_token(normalized, token))
        return JsoncError(message, line=line, column=column)

    def reject_constant(value: str) -> None:
        raise error_for_token(f"invalid JSON constant: {value}", value)

    def parse_finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise error_for_token(f"JSON number is out of range: {value}", value)
        return parsed

    def parse_finite_int(value: str) -> int:
        if not math.isfinite(float(value)):
            raise error_for_token(f"JSON number is out of range: {value}", value)
        return int(value)

    try:
        data = json.loads(
            normalized,
            parse_constant=reject_constant,
            parse_float=parse_finite_float,
            parse_int=parse_finite_int,
        )
    except json.JSONDecodeError as error:
        raise JsoncError(
            error.msg,
            line=error.lineno,
            column=error.colno,
        ) from error

    if not isinstance(data, dict):
        raise JsoncError("expected a JSON object", line=1, column=1)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a VS Code JSONC object to JSON")
    parser.add_argument("path", type=pathlib.Path, help="Path to a JSONC object")
    args = parser.parse_args()

    try:
        data = load_jsonc_object(args.path)
    except (OSError, UnicodeError) as error:
        print(f"Error: failed to read {args.path}: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except JsoncError as error:
        print(
            f"Error: invalid JSONC in {args.path}:{error.line}:{error.column}: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    json.dump(data, sys.stdout, ensure_ascii=False, indent=2, allow_nan=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
