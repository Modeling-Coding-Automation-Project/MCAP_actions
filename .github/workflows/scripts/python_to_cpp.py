#!/usr/bin/env python3
"""
Utilities for the python_to_cpp GitHub Actions workflow.

Edit the constants in the "Configuration" section below to customize
the AI model and prompts without touching the workflow YAML.

Usage (called from the workflow YAML):
  python3 python_to_cpp.py branch-name <current_branch>
  python3 python_to_cpp.py model
  python3 python_to_cpp.py prompt <py_file> {hpp,cpp,sil} [--hpp-file ...] [--cpp-file ...] [--py-diff-file ...]
  python3 python_to_cpp.py filter-cpp
  python3 python_to_cpp.py pr-body <file1> [<file2> ...]
"""

import argparse
import os
import re
import sys
import urllib.request

# ============================================================
# Configuration — Edit these values to customize the workflow
# ============================================================

# AI model used for code generation.
# This value is passed to the copilot CLI via --model flag.
# Examples: "claude-sonnet-4.6", "claude-sonnet-4.5", "claude-haiku-4.5",
#  "claude-opus-4.6", "claude-opus-4.6-fast", "claude-opus-4.5",
#  "claude-sonnet-4", "gemini-3-pro-preview", "gpt-5.4",
#  "gpt-5.3-codex", "gpt-5.2-codex", "gpt-5.2", "gpt-5.1-codex-max",
#  "gpt-5.1-codex", "gpt-5.1", "gpt-5.1-codex-mini", "gpt-5-mini", "gpt-4.1".
_AI_MODEL_DEFAULT = "gpt-5-mini"
AI_MODEL = os.environ.get("AI_MODEL_OVERRIDE") or _AI_MODEL_DEFAULT

# ============================================================
# Prompts
# ============================================================

# The shared prompt is fetched from python_to_cpp_skill.md in the
# MCAP_actions repository.  Edit that file to customise the prompt
# without touching workflow YAML or this script.

_SKILL_URL = (
    "https://raw.githubusercontent.com/"
    "Modeling-Coding-Automation-Project/MCAP_actions/main/"
    ".github/workflows/scripts/python_to_cpp_skill.md"
)

_MATRIX_SKILL_URL = (
    "https://raw.githubusercontent.com/"
    "Modeling-Coding-Automation-Project/MCAP_actions/main/"
    ".github/workflows/scripts/python_matrix_to_cpp_skill.md"
)


def _load_skill() -> str:
    """Return the contents of python_to_cpp_skill.md fetched from GitHub."""
    with urllib.request.urlopen(_SKILL_URL) as response:
        return response.read().decode("utf-8")


def _load_matrix_skill() -> str:
    """Return the contents of python_matrix_to_cpp_skill.md fetched from GitHub."""
    with urllib.request.urlopen(_MATRIX_SKILL_URL) as response:
        return response.read().decode("utf-8")


def _uses_numpy(py_content: str) -> bool:
    """Return True if the Python source contains a numpy import."""
    return bool(re.search(r'^\s*import\s+numpy|^\s*from\s+numpy\s+import', py_content, re.MULTILINE))

# ============================================================
# Subcommand implementations
# ============================================================


def cmd_branch_name(args: argparse.Namespace) -> None:
    """Print the cpp_gen branch name derived from the current branch name."""
    print(f"{args.current_branch}_cpp_gen")


def cmd_model(args: argparse.Namespace) -> None:
    """Print the configured AI model identifier."""
    print(AI_MODEL)


# Prompts for full (from-scratch) generation
_FILE_TYPE_SUFFIX_FULL = {
    "hpp": (
        "Now, generate ONLY the .hpp header file for the Python code above.\n"
        "Do NOT include the .cpp implementation or the _SIL.cpp file — output the header file only.\n"
        "Output ONLY raw C++ code. No explanations, no markdown fences, no preamble, no summary.\n"
        "Do not describe what you will generate. Just output the header file code directly to stdout."
    ),
    "cpp": (
        "Now, generate ONLY the .cpp implementation file for the Python code above.\n"
        "Do NOT include the .hpp header or the _SIL.cpp file — output the implementation file only.\n"
        "Output ONLY raw C++ code. No explanations, no markdown fences, no preamble, no summary.\n"
        "Do not describe what you will generate. Just output the implementation file code directly to stdout."
    ),
    "sil": (
        "Now, generate ONLY the _SIL.cpp Pybind11 Software-In-the-Loop file for the Python code above.\n"
        "Do NOT include the .hpp header or the .cpp implementation — output the _SIL.cpp file only.\n"
        "Output ONLY raw C++ code. No explanations, no markdown fences, no preamble, no summary.\n"
        "Do not describe what you will generate. Just output the SIL file code directly to stdout."
    ),
}

# Prompts for diff-based (incremental) update: used when the .py file was modified
# and the corresponding C++ files already exist.
_FILE_TYPE_SUFFIX_DIFF = {
    "hpp": (
        "The Python source file has been modified. The git diff shown above indicates exactly what changed.\n"
        "Update ONLY the .hpp header file to reflect those Python changes.\n"
        "Keep all existing C++ code that was NOT affected by the Python changes.\n"
        "Do NOT include the .cpp implementation or the _SIL.cpp file — output the header file only.\n"
        "Output ONLY raw C++ code. No explanations, no markdown fences, no preamble, no summary.\n"
        "Just output the complete updated header file code directly to stdout."
    ),
    "cpp": (
        "The Python source file has been modified. The git diff shown above indicates exactly what changed.\n"
        "Update ONLY the .cpp implementation file to reflect those Python changes.\n"
        "Keep all existing C++ code that was NOT affected by the Python changes.\n"
        "Do NOT include the .hpp header or the _SIL.cpp file — output the implementation file only.\n"
        "Output ONLY raw C++ code. No explanations, no markdown fences, no preamble, no summary.\n"
        "Just output the complete updated implementation file code directly to stdout."
    ),
    "sil": (
        "The Python source file has been modified. The git diff shown above indicates exactly what changed.\n"
        "Update ONLY the _SIL.cpp Pybind11 Software-In-the-Loop file to reflect those Python changes.\n"
        "Keep all existing C++ code that was NOT affected by the Python changes.\n"
        "Do NOT include the .hpp header or the .cpp implementation — output the _SIL.cpp file only.\n"
        "Output ONLY raw C++ code. No explanations, no markdown fences, no preamble, no summary.\n"
        "Just output the complete updated SIL file code directly to stdout."
    ),
}


def cmd_prompt(args: argparse.Namespace) -> None:
    """Print the C++ generation prompt for a given Python source file.

    If --py-diff-file is provided and existing C++ files are present,
    the prompt switches to diff-based update mode: the AI is instructed
    to modify only the parts that correspond to the changed Python code.
    """
    with open(args.py_file, encoding="utf-8") as f:
        py_content = f.read()

    already_generated = ""
    if getattr(args, "hpp_file", None) and os.path.isfile(args.hpp_file):
        with open(args.hpp_file, encoding="utf-8") as f:
            already_generated += (
                "\n\nThe following .hpp header file has already been generated "
                "from the Python code above. Use it as the basis for your output:\n"
                f"```cpp\n{f.read()}\n```"
            )
    if getattr(args, "cpp_file", None) and os.path.isfile(args.cpp_file):
        with open(args.cpp_file, encoding="utf-8") as f:
            already_generated += (
                "\n\nThe following .cpp implementation file has already been generated "
                "from the Python code above. Use it as the basis for your output:\n"
                f"```cpp\n{f.read()}\n```"
            )

    # Diff-based update mode: include the Python diff and instruct the AI to
    # update only the affected C++ sections.
    py_diff_section = ""
    is_diff_mode = False
    if getattr(args, "py_diff_file", None) and os.path.isfile(args.py_diff_file):
        with open(args.py_diff_file, encoding="utf-8") as f:
            diff_content = f.read().strip()
        if diff_content and already_generated:
            py_diff_section = (
                "\n\nThe following git diff shows what changed in the Python source file:\n"
                f"```diff\n{diff_content}\n```"
            )
            is_diff_mode = True

    suffix = _FILE_TYPE_SUFFIX_DIFF[args.file_type] if is_diff_mode else _FILE_TYPE_SUFFIX_FULL[args.file_type]

    skill = _load_skill()
    if _uses_numpy(py_content):
        skill += "\n\n" + _load_matrix_skill()

    sys.stdout.write(skill + "\n\n" + py_content +
                     already_generated + py_diff_section + "\n\n" + suffix)


def cmd_filter_cpp(args: argparse.Namespace) -> None:
    """Filter Copilot CLI stdout to retain only valid C++ code.

    The Copilot CLI sometimes writes tool-call logs and status messages
    (lines starting with '✗', '●', shell commands, etc.) to stdout before
    the actual generated code.  This command reads stdin, discards every
    line that precedes the first recognisable C++ line, and strips any
    remaining Markdown code-fence lines (```...).
    """
    cpp_start_re = re.compile(
        r'^(#|//|/\*|class\b|struct\b|namespace\b|template\b|typedef\b|using\b)'
    )
    fence_re = re.compile(r'^```')

    lines = sys.stdin.readlines()
    start = next(
        (i for i, line in enumerate(lines) if cpp_start_re.match(line)),
        None,
    )
    if start is None:
        return
    for line in lines[start:]:
        if not fence_re.match(line):
            sys.stdout.write(line)


def cmd_pr_body(args: argparse.Namespace) -> None:
    """Print the pull-request body in Markdown."""
    files_list = "\n".join(f"- {f}" for f in args.files)
    body = f"""\
## 自動生成されたC++コード

Pythonクラスから自動的にC++コード（.hpp / .cpp）が生成されました。

### 対象Pythonファイル
{files_list}

### 確認事項
- [ ] メンバー変数の型が適切か
- [ ] メンバー関数のシグネチャが正しいか
- [ ] ヘッダーファイルと実装ファイルの分割が適切か
- [ ] コンパイルエラーがないか
"""
    sys.stdout.write(body)


# ============================================================
# CLI entry point
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Utilities for the python_to_cpp GitHub Actions workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # branch-name <current_branch>
    p_branch = sub.add_parser(
        "branch-name", help="Output the cpp_gen branch name for the given branch.")
    p_branch.add_argument(
        "current_branch", help="Current git branch name.")
    p_branch.set_defaults(func=cmd_branch_name)

    # model
    p_model = sub.add_parser(
        "model", help="Output the configured AI model identifier.")
    p_model.set_defaults(func=cmd_model)

    # prompt <py_file> <file_type> [--hpp-file ...] [--cpp-file ...]
    p_prompt = sub.add_parser(
        "prompt", help="Output the C++ generation prompt.")
    p_prompt.add_argument("py_file", help="Path to the Python source file.")
    p_prompt.add_argument(
        "file_type", choices=["hpp", "cpp", "sil"],
        help="Type of file to generate: hpp (header), cpp (implementation), sil (Pybind11 SIL).")
    p_prompt.add_argument(
        "--hpp-file", dest="hpp_file", default=None,
        help="Path to the already-generated .hpp file to include in the prompt (used for cpp/sil).")
    p_prompt.add_argument(
        "--cpp-file", dest="cpp_file", default=None,
        help="Path to the already-generated .cpp file to include in the prompt (used for cpp/sil).")
    p_prompt.add_argument(
        "--py-diff-file", dest="py_diff_file", default=None,
        help="Path to a file containing the git diff of the Python source file. "
             "When provided together with existing C++ files, enables diff-based "
             "incremental update mode instead of full regeneration.")
    p_prompt.set_defaults(func=cmd_prompt)

    # filter-cpp  (reads from stdin)
    p_filter = sub.add_parser(
        "filter-cpp",
        help="Filter Copilot CLI output from stdin, writing only C++ code to stdout.",
    )
    p_filter.set_defaults(func=cmd_filter_cpp)

    # pr-body <file1> [<file2> ...]
    p_pr = sub.add_parser("pr-body", help="Output the pull-request body.")
    p_pr.add_argument("files", nargs="+", help="List of changed Python files.")
    p_pr.set_defaults(func=cmd_pr_body)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
