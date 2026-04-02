#!/usr/bin/env python3
"""
Parse Thinkbox Deadline task logs (.txt) and emit per-workstation Markdown/HTML stats.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from deadline_benchmark_core import (
    aggregate_logs_from_labeled_texts,
    render_report_html,
)


def run(report_dir: Path, generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now()
    txt_files = sorted(report_dir.glob("*.txt"))
    if not txt_files:
        return f"No .txt files found in `{report_dir}`.\n"

    labeled = []
    for fp in txt_files:
        text = fp.read_text(encoding="utf-8", errors="replace")
        labeled.append((fp.name, text))

    by_ws, skipped = aggregate_logs_from_labeled_texts(labeled)
    source_description = "`{0}`".format(report_dir)
    return render_report_html(by_ws, skipped, generated_at, source_description)


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze Deadline task logs by workstation.")
    p.add_argument(
        "directory",
        nargs="?",
        default=r"C:\Users\g.grapperon\Desktop\Reports_Job",
        type=Path,
        help="Folder containing Deadline .txt task logs",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write report to this path (default: timestamped .md in the log folder)",
    )
    p.add_argument(
        "--stdout",
        action="store_true",
        help="Print the report to stdout instead of writing a file",
    )
    args = p.parse_args()
    report_dir = args.directory.expanduser().resolve()
    if not report_dir.is_dir():
        print(f"Not a directory: {report_dir}", file=sys.stderr)
        return 1

    generated_at = datetime.now()
    md = run(report_dir, generated_at=generated_at)
    if args.stdout:
        sys.stdout.write(md)
        return 0

    out_path = args.output
    if out_path is None:
        stamp = generated_at.strftime("%Y-%m-%d_%H-%M-%S")
        out_path = report_dir / f"deadline_workstation_report_{stamp}.html"
    else:
        out_path = out_path.expanduser().resolve()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
