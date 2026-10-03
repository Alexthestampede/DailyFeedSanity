#!/usr/bin/env python3
"""
Sync the vendored ModuLLe copy (lib/modulle/) with upstream main.

Upstream uses absolute imports ('from modulle.X import Y', assuming the
package is pip-installed); the vendored copy lives at lib/modulle inside
DailyFeedSanity where the real package name is 'lib.modulle'. This script
also rewrites those imports to package-relative form so the vendored copy
stays self-contained.

Usage:
    python scripts/sync_modulle.py             # sync from origin/main
    python scripts/sync_modulle.py --ref dev   # sync from a branch/tag
    python scripts/sync_modulle.py --check     # report drift only, no changes

Steps:
1. Locate the upstream repo (~/Aish/ModuLLe or --repo flag)
2. Fetch + verify the requested ref exists
3. rsync-style copy of modulle/ into lib/modulle/ (prunes removed files)
4. Rewrite absolute imports to package-relative
5. Compile-check + import-check with 'modulle' poisoned in sys.modules
   (catches the pip-editable-install masking bug)
"""
import argparse
import py_compile
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VENDORED = PROJECT_ROOT / "lib" / "modulle"

# Vendored files must never be touched by the sync
PRESERVE_FILES = {"response_cleaner.py", "json_extractor.py"}


def run_git(repo: Path, *args):
    """Run a git command in the repo, return stdout."""
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def find_upstream(cli_path):
    """Locate the upstream ModuLLe checkout."""
    if cli_path:
        repo = Path(cli_path).expanduser().resolve()
    else:
        repo = Path.home() / "Aish" / "ModuLLe"
    if not (repo / "modulle" / "__init__.py").exists():
        raise SystemExit(
            f"Upstream ModuLLe checkout not found at {repo}.\n"
            "Pass --repo /path/to/ModuLLe"
        )
    return repo


def import_style_fix(repo: Path, ref: str, dry_run: bool) -> int:
    """Count of files that would need import rewriting (upstream style)."""
    # Files using absolute imports, from the upstream tree
    out = run_git(
        repo, "grep", "-l", "from modulle\\.", f"{ref}", "--", "modulle/"
    )
    return len([l for l in out.splitlines() if l.strip()])


def sync_tree(repo: Path, ref: str, apply: bool):
    """Copy modulle/ from the given ref into lib/modulle/, mirroring deletions."""
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", ref, "modulle"],
        capture_output=True, check=True,
    )
    if not apply:
        # Dry run: report what would change by extracting to temp and diffing
        import tarfile, tempfile, filecmp, os

        summary = {"added": [], "changed": [], "removed": []}
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(fileobj=__import__("io").BytesIO(archive.stdout)) as tar:
                tar.extractall(tmp)
            src = Path(tmp) / "modulle"
            for path in sorted(src.rglob("*")):
                if path.is_dir() or "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(src)
                dst = VENDORED / rel
                if not dst.exists():
                    summary["added"].append(str(rel))
                elif not filecmp.cmp(path, dst, shallow=False):
                    summary["changed"].append(str(rel))
            for path in sorted(VENDORED.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(VENDORED)
                if rel.parts[0] == "utils" and rel.name in PRESERVE_FILES:
                    continue
                if not (src / rel).exists():
                    summary["removed"].append(str(rel))
        return summary

    import io
    import tarfile
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(tmp)
        src = Path(tmp) / "modulle"

        # Mirror-copy: copy everything, remove vendored files absent upstream
        import shutil
        if VENDORED.exists():
            for path in sorted(VENDORED.rglob("*"), reverse=True):
                if "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(VENDORED)
                if rel.parts[0] == "utils" and rel.name in PRESERVE_FILES:
                    continue  # keep local utility files
                target = src / rel
                if not target.exists():
                    if path.is_dir():
                        path.rmdir()
                    else:
                        path.unlink()

        shutil.copytree(src, VENDORED, dirs_exist_ok=True)
    return None


def rewrite_imports(root: Path) -> int:
    """
    Rewrite 'from modulle.X import Y' to package-relative imports.

    Depth-aware: providers/x/ uses ..., tools/ + web/ + cli/ use ..
    (relative to the lib.modulle package root).
    """
    pattern = re.compile(
        r"^(\s*)from modulle\.([a-zA-Z_]+(?:\.[a-zA-Z_]+)*) import (.+)$", re.M
    )
    simple = re.compile(r"^(\s*)from modulle import (.+)$", re.M)
    count = 0

    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        depth = len(py.relative_to(root).parts) - 1
        dots = "." * (depth + 1)
        text = py.read_text()

        def repl(m):
            indent, mod, names = m.group(1), m.group(2), m.group(3)
            return f"{indent}from {dots}{mod} import {names}"

        new_text = pattern.sub(repl, text)
        new_text = simple.sub(rf"\g<1>from {dots} import \g<2>", new_text)
        if new_text != text:
            py.write_text(new_text)
            count += 1
    return count


def verify_selfcontained():
    """
    Import-check the vendored package with top-level 'modulle' poisoned,
    in a submodule process. Catches residual absolute imports that would
    otherwise be masked by a pip-editable install of ModuLLe.
    """
    check_code = (
        "import sys\n"
        "sys.modules['modulle'] = None\n"
        "sys.path.insert(0, r'%s')\n"
        "import lib.modulle\n"
        "from lib.modulle import create_ai_client\n"
        "from lib.modulle.utils.response_cleaner import clean_response, parse_yes_no\n"
        "from lib.modulle.utils.json_extractor import extract_json\n"
        "c, t, v = create_ai_client(provider='ollama', text_model='m',\n"
        "                           base_url='http://localhost:11434',\n"
        "                           request_timeout=300)\n"
        "assert c.request_timeout == 300\n"
        "assert parse_yes_no('No, it is not clickbait') is False\n"
        "print('verify: PASS')\n" % PROJECT_ROOT
    )
    result = subprocess.run(
        [sys.executable, "-c", check_code],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=None, help="Path to upstream ModuLLe checkout")
    parser.add_argument("--ref", default="origin/main", help="Git ref to sync from")
    parser.add_argument("--check", action="store_true", help="Report drift only")
    args = parser.parse_args()

    repo = find_upstream(args.repo)

    # Fetch latest so origin/main is fresh
    print("Fetching upstream...")
    subprocess.run(["git", "-C", str(repo), "fetch", "origin"], check=True)

    upstream_commit = run_git(repo, "rev-parse", "--short", args.ref)
    print(f"Syncing from {args.ref} ({upstream_commit})")

    if args.check:
        summary = sync_tree(repo, args.ref, apply=False)
        n_absolute = import_style_fix(repo, args.ref, dry_run=True)
        changed = summary["changed"] + summary["added"] + summary["removed"]
        print(f"\nDrift vs vendored copy: {len(changed)} file(s)")
        for key in ("added", "changed", "removed"):
            for rel in summary[key]:
                print(f"  [{key}] {rel}")
        if len(changed) == 0:
            print("\nUp to date.")
        elif n_absolute:
            print(f"\nNOTE: {n_absolute} upstream file(s) use absolute imports "
                  "- sync would rewrite them")
        return 0

    summary = sync_tree(repo, args.ref, apply=True)
    rewritten = rewrite_imports(VENDORED)
    print(f"Import rewrites: {rewritten} file(s)")

    # Compile check
    failed = []
    for py in sorted(VENDORED.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as e:
            failed.append(f"{py.relative_to(VENDORED)}: {e}")
    if failed:
        print("\nCOMPILE ERRORS:")
        for f in failed:
            print(f"  {f}")
        return 1

    # Import check (poisoned top-level module)
    result = verify_selfcontained()
    if result.returncode != 0:
        print("\nVERIFY FAILED:\n" + result.stdout + result.stderr)
        return 1
    print(result.stdout.strip())

    print(f"\nSync complete: lib/modulle == upstream {upstream_commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())