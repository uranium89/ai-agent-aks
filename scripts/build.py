#!/usr/bin/env python3
"""Generate dist/<tool>/ from shared/ and templates/<tool>/.

Usage:
  python3 scripts/build.py           # rebuild dist/
  python3 scripts/build.py --check   # exit 1 if dist/ is out of date

Every file under templates/<tool>/ is copied to dist/<tool>/ at the same
path, with these directives expanded (paths are relative to the repo root):
  {{include PATH}}      full contents of PATH
  {{body PATH}}         a shared agent prompt without its front matter
  {{description PATH}}  the `description:` value from a shared agent's front matter
shared/project/ (access, environment, architecture, risks, backlog, work items + example incident)
is copied into dist/<tool>/aks-team/ for every tool.
"""
import filecmp
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRECTIVE = re.compile(r"\{\{(include|body|description) ([^}]+)\}\}")
SKIP = {".DS_Store", "__pycache__"}


def split_agent(path):
    text = (ROOT / path).read_text()
    m = re.match(r"---\ndescription: (.+)\n---\n\n?(.*)", text, re.S)
    if not m:
        sys.exit(f"{path}: expected front matter with a single 'description:' line")
    return m.group(1), m.group(2).rstrip("\n")


def render(text):
    def expand(m):
        kind, arg = m.group(1), m.group(2).strip()
        if kind == "include":
            return (ROOT / arg).read_text().rstrip("\n")
        description, body = split_agent(arg)
        return body if kind == "body" else description

    return DIRECTIVE.sub(expand, text)


def build(out):
    for tool_dir in sorted(p for p in (ROOT / "templates").iterdir() if p.is_dir()):
        dest = out / tool_dir.name
        shutil.copytree(ROOT / "shared" / "project", dest / "aks-team", ignore=shutil.ignore_patterns(*SKIP))
        for src in sorted(tool_dir.rglob("*")):
            if src.is_file() and src.name not in SKIP:
                target = dest / src.relative_to(tool_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(render(src.read_text()))


def differences(a, b, prefix=""):
    cmp = filecmp.dircmp(a, b, ignore=list(SKIP))
    diffs = [prefix + n for n in cmp.left_only + cmp.right_only]
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    diffs += [prefix + n for n in mismatch + errors]
    for sub in cmp.common_dirs:
        diffs += differences(Path(a) / sub, Path(b) / sub, f"{prefix}{sub}/")
    return diffs


def main():
    dist = ROOT / "dist"
    if "--check" in sys.argv[1:]:
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp))
            diffs = differences(tmp, dist) if dist.exists() else ["dist/ (missing)"]
        if diffs:
            print("dist/ is out of date; run python3 scripts/build.py\n  " + "\n  ".join(diffs))
            sys.exit(1)
        print("dist/ is up to date")
        return
    shutil.rmtree(dist, ignore_errors=True)
    build(dist)
    print(f"built {', '.join(sorted(p.name for p in dist.iterdir()))} into dist/")


if __name__ == "__main__":
    main()
