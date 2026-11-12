#!/usr/bin/env python3
"""Require TODO and FIXME comments to name a GitHub issue.

The tag is case-insensitive. The issue number is in parentheses, then a colon
and a description on the same line:

    TODO(#123): description
    FIXME(#123): description

Only comment markers count. Identifiers such as todo-list, loadTodos, and a
YAML key todos: are ignored. Paths in scripts/todo_issue_excludes.txt are not
scanned.

    python3 scripts/check_todo_issues.py
    python3 scripts/check_todo_issues.py --self-test
    python3 scripts/check_todo_issues.py /path/to/sample
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDES_PATH = Path(__file__).resolve().with_name("todo_issue_excludes.txt")

# A marker is the whole word, any case, and not the start of an identifier
# (todo-list, loadTodos, todos).
MARKER_RE = re.compile(r"(?i)(?<![\w])(TODO|FIXME)(?![\w-])")
# Positive issue number, no leading zero. Description is required on this line.
LINKED_RE = re.compile(r"(?i)\A(TODO|FIXME)\(#[1-9][0-9]*\):\s*\S")

DESCRIPTION = """
Check that every TODO and FIXME comment names a GitHub issue.

Form (the tag is any case; the description stays on the same line):
  TODO(#123): description
  FIXME(#123): description

Excluded paths: scripts/todo_issue_excludes.txt
""".strip()


@dataclass(frozen=True)
class Syntax:
    """Comment and string openers for one language family."""

    line_comments: tuple[str, ...] = ()
    block_comments: tuple[tuple[str, str], ...] = ()
    quotes: tuple[str, ...] = ()
    triple_quotes: bool = False
    template_quotes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Violation:
    relative_path: str
    line: int
    text: str


PYTHON_SYNTAX = Syntax(line_comments=("#",), quotes=("'", '"'), triple_quotes=True)
HASH_SYNTAX = Syntax(line_comments=("#",), quotes=("'", '"'))
JS_SYNTAX = Syntax(
    line_comments=("//",),
    block_comments=(("/*", "*/"),),
    quotes=("'", '"'),
    template_quotes=("`",),
)
C_SYNTAX = Syntax(line_comments=("//",), block_comments=(("/*", "*/"),), quotes=("'", '"'))
CSS_SYNTAX = Syntax(block_comments=(("/*", "*/"),), quotes=("'", '"'))
SCSS_SYNTAX = Syntax(
    line_comments=("//",),
    block_comments=(("/*", "*/"),),
    quotes=("'", '"'),
)
HTML_SYNTAX = Syntax(
    line_comments=("//",),
    block_comments=(("<!--", "-->"), ("/*", "*/")),
    quotes=("'", '"'),
    template_quotes=("`",),
)
SQL_SYNTAX = Syntax(line_comments=("--",), block_comments=(("/*", "*/"),), quotes=("'", '"'))
PHP_SYNTAX = Syntax(
    line_comments=("//", "#"),
    block_comments=(("/*", "*/"),),
    quotes=("'", '"'),
)

SYNTAX_BY_EXTENSION: dict[str, Syntax] = {
    ".py": PYTHON_SYNTAX,
    ".pyi": PYTHON_SYNTAX,
    ".js": JS_SYNTAX,
    ".jsx": JS_SYNTAX,
    ".ts": JS_SYNTAX,
    ".tsx": JS_SYNTAX,
    ".mjs": JS_SYNTAX,
    ".cjs": JS_SYNTAX,
    ".vue": HTML_SYNTAX,
    ".svelte": HTML_SYNTAX,
    ".css": CSS_SYNTAX,
    ".scss": SCSS_SYNTAX,
    ".sass": SCSS_SYNTAX,
    ".less": SCSS_SYNTAX,
    ".html": HTML_SYNTAX,
    ".htm": HTML_SYNTAX,
    ".sql": SQL_SYNTAX,
    ".sh": HASH_SYNTAX,
    ".bash": HASH_SYNTAX,
    ".zsh": HASH_SYNTAX,
    ".ps1": HASH_SYNTAX,
    ".php": PHP_SYNTAX,
    ".yml": HASH_SYNTAX,
    ".yaml": HASH_SYNTAX,
    ".toml": HASH_SYNTAX,
    ".go": C_SYNTAX,
    ".rs": C_SYNTAX,
    ".java": C_SYNTAX,
    ".kt": C_SYNTAX,
    ".kts": C_SYNTAX,
    ".c": C_SYNTAX,
    ".h": C_SYNTAX,
    ".cc": C_SYNTAX,
    ".cpp": C_SYNTAX,
    ".hpp": C_SYNTAX,
    ".rb": HASH_SYNTAX,
    ".cs": C_SYNTAX,
    ".swift": C_SYNTAX,
}

SYNTAX_BY_FILENAME: dict[str, Syntax] = {
    "dockerfile": HASH_SYNTAX,
    "containerfile": HASH_SYNTAX,
    "makefile": HASH_SYNTAX,
}


def syntax_for(path: Path) -> Syntax | None:
    """Return the comment syntax for a source file, or None when it is not source."""
    special = SYNTAX_BY_FILENAME.get(path.name.lower())
    if special is not None:
        return special
    return SYNTAX_BY_EXTENSION.get(path.suffix.lower())


def load_exclude_patterns(path: Path) -> list[str]:
    """Load non-comment patterns from the exclude file."""
    if not path.is_file():
        raise FileNotFoundError(f"Exclude file not found: {path}")
    patterns: list[str] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip().replace("\\", "/")
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    if not patterns:
        raise ValueError(f"No exclude patterns in {path}")
    return patterns


def _normalize_relative(relative_path: str) -> str:
    """Normalize a path. Keep a leading dot in names such as .cursor and .git."""
    relative = relative_path.replace("\\", "/").strip()
    while relative.startswith("./"):
        relative = relative[2:]
    return relative


def is_excluded(relative_path: str, patterns: list[str]) -> bool:
    """Return True when a repo-relative path matches an exclude pattern."""
    relative = _normalize_relative(relative_path)
    if relative == ".git" or relative.startswith(".git/"):
        return True
    return any(_pattern_matches(relative, pattern) for pattern in patterns)


def _pattern_matches(relative: str, pattern: str) -> bool:
    if pattern.startswith("**/"):
        rest = pattern[3:]
        if rest.endswith("/"):
            return rest[:-1] in relative.split("/")
        base_name = relative.rsplit("/", 1)[-1]
        return fnmatch.fnmatch(base_name, rest) or fnmatch.fnmatch(relative, rest)
    if pattern.endswith("/"):
        return relative == pattern[:-1] or relative.startswith(pattern)
    if any(token in pattern for token in "*?["):
        return fnmatch.fnmatch(relative, pattern)
    return relative == pattern


def comment_lines(source: str, syntax: Syntax) -> dict[int, str]:
    """Return 1-based line numbers mapped to the comment text on that line.

    Strings are skipped. Template literals (JS backticks) stay opaque except
    for ${} interpolations, which are scanned as code. A "://" sequence does
    not open a line comment.
    """
    text = source.replace("\r\n", "\n").replace("\r", "\n")
    line_openers = tuple(sorted(syntax.line_comments, key=len, reverse=True))
    block_openers = tuple(sorted(syntax.block_comments, key=lambda pair: len(pair[0]), reverse=True))
    length = len(text)
    index = 0
    line_number = 1
    # ("code", brace) brace > 0 means this frame is a ${} interpolation.
    # ("line",) ("block", closer) ("string", quote, triple) ("template",)
    frames: list[tuple] = [("code", 0)]
    buffers: dict[int, list[str]] = {}

    def add(chunk: str) -> None:
        if chunk:
            buffers.setdefault(line_number, []).append(chunk)

    while index < length:
        kind = frames[-1][0]
        char = text[index]

        if kind == "line":
            if char == "\n":
                frames.pop()
                line_number += 1
            else:
                add(char)
            index += 1
            continue

        if kind == "block":
            closer = frames[-1][1]
            if text.startswith(closer, index):
                frames.pop()
                index += len(closer)
                continue
            if char == "\n":
                line_number += 1
            else:
                add(char)
            index += 1
            continue

        if kind == "string":
            quote, is_triple = frames[-1][1], frames[-1][2]
            if char == "\\" and index + 1 < length:
                if text[index + 1] == "\n":
                    line_number += 1
                index += 2
                continue
            end = quote * 3 if is_triple else quote
            if text.startswith(end, index):
                frames.pop()
                index += len(end)
                continue
            if char == "\n":
                line_number += 1
            index += 1
            continue

        if kind == "template":
            if char == "\\" and index + 1 < length:
                if text[index + 1] == "\n":
                    line_number += 1
                index += 2
                continue
            if text.startswith("${", index):
                frames.append(("code", 1))
                index += 2
                continue
            if char == "`":
                frames.pop()
                index += 1
                continue
            if char == "\n":
                line_number += 1
            index += 1
            continue

        brace = frames[-1][1]
        if char == "\n":
            line_number += 1
            index += 1
            continue
        if brace > 0 and char == "{":
            frames[-1] = ("code", brace + 1)
            index += 1
            continue
        if brace > 0 and char == "}":
            if brace == 1:
                frames.pop()
            else:
                frames[-1] = ("code", brace - 1)
            index += 1
            continue

        line_opener = _matching_line_opener(text, index, line_openers)
        if line_opener is not None:
            frames.append(("line",))
            index += len(line_opener)
            continue

        block_pair = _matching_block_opener(text, index, block_openers)
        if block_pair is not None:
            opener, closer = block_pair
            frames.append(("block", closer))
            index += len(opener)
            continue

        opened = _open_string(text, index, syntax)
        if opened is not None:
            frames.append(opened[0])
            index += opened[1]
            continue

        index += 1

    return {line_no: "".join(parts) for line_no, parts in buffers.items()}


def _matching_line_opener(text: str, index: int, openers: tuple[str, ...]) -> str | None:
    for opener in openers:
        if not text.startswith(opener, index):
            continue
        # "http://..." is a URL, not a line comment.
        if opener == "//" and index > 0 and text[index - 1] == ":":
            return None
        return opener
    return None


def _matching_block_opener(
    text: str,
    index: int,
    openers: tuple[tuple[str, str], ...],
) -> tuple[str, str] | None:
    for opener, closer in openers:
        if text.startswith(opener, index):
            return opener, closer
    return None


def _open_string(text: str, index: int, syntax: Syntax) -> tuple[tuple, int] | None:
    """Return (frame, width) when a string or template starts at index."""
    if syntax.triple_quotes:
        for quote in ("'", '"'):
            if quote in syntax.quotes and text.startswith(quote * 3, index):
                return ("string", quote, True), 3
    for quote in syntax.template_quotes:
        if text.startswith(quote, index):
            return ("template",), len(quote)
    for quote in syntax.quotes:
        if text.startswith(quote, index):
            return ("string", quote, False), len(quote)
    return None


def unlinked_markers(comment_text: str) -> list[re.Match[str]]:
    """Return markers in one comment line that miss the issue form."""
    missing: list[re.Match[str]] = []
    for match in MARKER_RE.finditer(comment_text):
        if LINKED_RE.match(comment_text[match.start():]) is None:
            missing.append(match)
    return missing


def _read_source(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def _shorten(text: str, limit: int = 200) -> str:
    collapsed = " ".join(text.strip().split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def scan_tree(root: Path, patterns: list[str]) -> tuple[list[Violation], int]:
    """Scan source files under root. Returns violations and files read."""
    violations: list[Violation] = []
    scanned = 0
    root_resolved = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        relative_dir = Path(dirpath).resolve().relative_to(root_resolved).as_posix()
        if relative_dir == ".":
            relative_dir = ""
        kept_dirs: list[str] = []
        for dirname in dirnames:
            relative = f"{relative_dir}/{dirname}" if relative_dir else dirname
            if dirname == ".git" or is_excluded(relative, patterns):
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            relative = f"{relative_dir}/{filename}" if relative_dir else filename
            if is_excluded(relative, patterns):
                continue
            path = Path(dirpath) / filename
            syntax = syntax_for(path)
            if syntax is None:
                continue
            source = _read_source(path)
            if source is None:
                continue
            scanned += 1
            # Markers are whole words. A file with neither substring cannot match.
            folded = source.lower()
            if "todo" not in folded and "fixme" not in folded:
                continue
            source_lines = source.splitlines()
            for line_number, comment_text in comment_lines(source, syntax).items():
                if not unlinked_markers(comment_text):
                    continue
                line_text = source_lines[line_number - 1] if line_number <= len(source_lines) else comment_text
                violations.append(
                    Violation(
                        relative_path=relative,
                        line=line_number,
                        text=_shorten(line_text),
                    )
                )
    return violations, scanned


def render_report(violations: list[Violation]) -> str:
    """Format violations for a terminal or a CI log."""
    rows = [f"{item.relative_path}:{item.line}: {item.text}" for item in violations]
    count = len(violations)
    noun = "comment" if count == 1 else "comments"
    rows.append("")
    rows.append("Expected form: TODO(#123): description  or  FIXME(#123): description")
    rows.append(f"{count} unlinked TODO/FIXME {noun}.")
    return "\n".join(rows)


def render_success(scanned: int) -> str:
    noun = "file" if scanned == 1 else "files"
    return f"OK: scanned {scanned} source {noun}, no unlinked TODO/FIXME comments."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        help="Directory to scan (default: repository root)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in samples and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        patterns = load_exclude_patterns(EXCLUDES_PATH)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.self_test:
        return run_self_test(patterns)
    root = args.root if args.root is not None else REPO_ROOT
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2
    violations, scanned = scan_tree(root, patterns)
    if violations:
        print(render_report(violations))
        return 1
    print(render_success(scanned))
    return 0


@dataclass(frozen=True)
class Sample:
    name: str
    files: dict[str, str]
    lines: tuple[tuple[str, int], ...]


LOGOUT_LEGACY = "# todo разобраться как реализовать разлогин - можно по токену, можно по id\n"
LOGOUT_LINKED = "# TODO(#5): разобраться как реализовать разлогин - можно по токену, можно по id\n"

SAMPLES: tuple[Sample, ...] = (
    Sample("legacy logout comment", {"auth.py": LOGOUT_LEGACY}, (("auth.py", 1),)),
    Sample("issue 5 logout comment", {"auth.py": LOGOUT_LINKED}, ()),
    Sample("lowercase tag with issue", {"a.py": "# todo(#2): lower case tag\n"}, ()),
    Sample("mixed-case fixme", {"a.py": "# Fixme(#3): mixed case\n"}, ()),
    Sample("tight slashes", {"a.js": "//TODO(#6):tight\n"}, ()),
    Sample("tight hash", {"a.py": "#TODO(#6):tight\n"}, ()),
    Sample(
        "missing pieces",
        {
            "a.py": (
                "# TODO (#8): space before paren\n"
                "# TODO(#8) missing colon\n"
                "# TODO(#8):\n"
                "# TODO(#0): zero is not an issue\n"
                "# TODO(#08): leading zero\n"
            )
        },
        (("a.py", 1), ("a.py", 2), ("a.py", 3), ("a.py", 4), ("a.py", 5)),
    ),
    Sample(
        "names are not markers",
        {
            "a.py": (
                "# selector #todo-list and loadTodos and todos: are names\n"
                "loadTodos = 1\n"
                "label = '#todo-list'\n"
            ),
            "notes.yaml": (
                "todos:\n"
                "  - id: draw-graph\n"
                "selector: \"#todo-list\"\n"
                "helper: loadTodos\n"
            ),
        },
        (),
    ),
    Sample(
        "yaml comment is a marker",
        {"notes.yaml": "# FIXME: forgot the issue\ntodos:\n  - id: one\n"},
        (("notes.yaml", 1),),
    ),
    Sample(
        "docstring is not a comment",
        {"a.py": 'def f():\n    """TODO: in a docstring"""\n    # TODO(#4): in a comment\n'},
        (),
    ),
    Sample(
        "string continuation is not a comment",
        {"a.py": 's = "foo\\\n# TODO: still a string"\nt = 1  # TODO(#2): real\n'},
        (),
    ),
    Sample(
        "js block and template",
        {
            "ok.js": "const value = `safe # TODO: inside ${/* TODO(#1): real comment */ 1}`;\n",
            "bad.js": "const value = `safe ${/* TODO: missing */ 1}`;\n",
            "nested.js": "const value = `a ${\n  `b ${// TODO: nested\n1}`\n}`;\n",
        },
        (("bad.js", 1), ("nested.js", 2)),
    ),
    Sample(
        "css id versus block comment",
        {
            "ok.css": "#todo-list { color: red; } /* FIXME(#2): contrast */\n",
            "bad.css": "#todo-list { color: red; } /* TODO: color */\n",
        },
        (("bad.css", 1),),
    ),
    Sample(
        "html and sql",
        {
            "page.html": '<ul id="todo-list"></ul>\n<!-- TODO: wire click -->\n',
            "query.sql": "-- TODO(#4): add index\nSELECT 1; -- FIXME: missing issue\n",
        },
        (("page.html", 2), ("query.sql", 2)),
    ),
    Sample(
        "quoted url is not a comment",
        {
            "a.js": 'const url = "http://example.com/todo";\n',
            "page.html": '<a href="http://example.com/todo">link</a>\n',
        },
        (),
    ),
    Sample(
        "excluded player, learn, plan, and vendor trees",
        {
            "nine-to-eighteen/ui/src/game/code/tasks.ts": (
                "// TODO: shown to players\n"
                "export const starter = `# TODO: placeholder`;\n"
            ),
            "nine-to-eighteen/ui/src/data/learn/episodes.ts": (
                "function loadTodos() {}\n"
                "const selector = '#todo-list';\n"
                "// TODO: lesson text\n"
            ),
            ".cursor/plans/note.py": "# TODO: plan frontmatter lives next to this\n",
            "pkg/node_modules/left.js": "// TODO: dependency\n",
            "dist/app.js": "// TODO: build output\n",
            "app/real.ts": "// TODO: product code\nconst selector = '#todo-list';\n",
        },
        (("app/real.ts", 1),),
    ),
    Sample(
        "makefile comment",
        {"Makefile": "# TODO(#7): rebuild images\n"},
        (),
    ),
)

EXCLUDED_PATHS: tuple[str, ...] = (
    "nine-to-eighteen/ui/src/game/code/tasks.ts",
    "nine-to-eighteen/ui/src/game/sql/tasks.ts",
    "nine-to-eighteen/ui/src/data/learn/js/js04-dom-events.md",
    "nine-to-eighteen/ui/src/data/learn/episodes.ts",
    ".cursor/plans/admin_projects_access_ec87398c.plan.md",
    "ui-app/node_modules/typescript/lib/typescript.js",
    "node_modules/left.js",
    "ui-app/dist/assets/index.js",
    "build/output.js",
    "package-lock.json",
    "ui-app/package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
    "app.min.js",
)

INCLUDED_PATHS: tuple[str, ...] = (
    "auth/routers/auth.py",
    "scripts/check_todo_issues.py",
    "nine-to-eighteen/ui/src/App.tsx",
    "ui-app/src/main.tsx",
    "nine-to-eighteen/ui/src/game-extra/tasks.ts",
)


def _write_tree(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def run_self_test(patterns: list[str]) -> int:
    """Check the matcher, the exclude list, and a few sample trees."""
    failures: list[str] = []
    for relative in EXCLUDED_PATHS:
        if not is_excluded(relative, patterns):
            failures.append(f"expected exclude: {relative}")
    for relative in INCLUDED_PATHS:
        if is_excluded(relative, patterns):
            failures.append(f"expected to scan: {relative}")

    for sample in SAMPLES:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_tree(root, sample.files)
            violations, _scanned = scan_tree(root, patterns)
            actual = tuple(sorted((item.relative_path, item.line) for item in violations))
            expected = tuple(sorted(sample.lines))
            if actual != expected:
                failures.append(f"{sample.name}: got {actual}, expected {expected}")
                continue
            for item in violations:
                if MARKER_RE.search(item.text) is None:
                    failures.append(f"{sample.name}: report line has no marker: {item.text}")

    if failures:
        print("self-test failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"self-test passed ({len(SAMPLES)} samples)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
