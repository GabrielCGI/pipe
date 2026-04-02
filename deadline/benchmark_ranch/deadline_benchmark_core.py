# -*- coding: utf-8 -*-
"""
Shared parsing and HTML report generation for Deadline task logs.
Compatible with CPython 3 and IronPython 2.7 (Deadline Monitor).
"""

from __future__ import division

import re
from collections import defaultdict
from datetime import datetime

WORKER_NAME_RE = re.compile(r"^Worker Name:\s*(.+?)\s*$", re.MULTILINE)
VIDEO_CARD_RE = re.compile(r"^Video Card:\s*(.+?)\s*$", re.MULTILINE)
WALL_CLOCK_RE = re.compile(
    r"Total Wall Clock Time:\s*(\d+):(\d{1,2}):(\d{1,2})(?:\.(\d+))?",
    re.IGNORECASE,
)

RENDERER_GPU_RES = [
    re.compile(r'CUDA/OptiX device with name "([^"]+)"', re.IGNORECASE),
    re.compile(r'KarmaXPU: Device \d+[^\n]*name "([^"]+)"', re.IGNORECASE),
    re.compile(r'OptiX[^\n]*device[^\n]*name "([^"]+)"', re.IGNORECASE),
    re.compile(r'Using GPU:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
    re.compile(r"GPU(?: device)?:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
]

VIRTUAL_ADAPTER_HINTS = (
    "parsec",
    "virtual display",
    "remote",
    "microsoft basic",
    "basic render",
    "sunlogin",
    "teamviewer",
    "rdp",
)

TIER1_BENCHMARK_WORKSTATIONS = frozenset(
    (
        "RANCH-135",
        "RANCH-138",
        "RANCH-139",
        "RANCH-140",
        "RANCH-141",
        "RANCH-142",
        "RANCH-143",
        "RANCH-144",
    )
)


def _frac_to_seconds(frac):
    if not frac:
        return 0.0
    return int(frac) / (10 ** len(frac))


def parse_wall_clock_seconds(text):
    matches = list(WALL_CLOCK_RE.finditer(text))
    if not matches:
        return None
    m = matches[-1]
    h, mi, s, frac = m.group(1), m.group(2), m.group(3), m.group(4)
    return int(h) * 3600 + int(mi) * 60 + int(s) + _frac_to_seconds(frac)


def _is_placeholder_video_card(name):
    lower = name.lower()
    return any(h in lower for h in VIRTUAL_ADAPTER_HINTS)


def extract_video_card(text):
    vm = VIDEO_CARD_RE.search(text)
    primary = vm.group(1).strip() if vm else None

    renderer_gpu = None
    for rx in RENDERER_GPU_RES:
        mm = rx.search(text)
        if mm:
            renderer_gpu = mm.group(1).strip()
            break

    if primary and not _is_placeholder_video_card(primary):
        return primary
    if renderer_gpu:
        return renderer_gpu
    return primary


def parse_log_text(text):
    """
    Parse one task log body (same format as a saved .txt report).
    Returns (worker_name or None, wall_seconds or None, gpu_string or None).
    """
    if text is None:
        return None, None, None
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    else:
        # IronPython / .NET string -> Python unicode string for regex
        try:
            text = u"{0}".format(text)
        except Exception:
            pass
    wm = WORKER_NAME_RE.search(text)
    worker = wm.group(1).strip() if wm else None
    wall = parse_wall_clock_seconds(text)
    gpu = extract_video_card(text)
    return worker, wall, gpu


def format_mm_ss(seconds):
    total = int(round(seconds))
    m, s = divmod(total, 60)
    return "{0:02d}:{1:02d}".format(m, s)


def workstation_avg_seconds(entries):
    timed = [t for t, _ in entries if t is not None]
    if not timed:
        return None
    return sum(timed) / len(timed)


def format_perf_ratio(ratio):
    s = "{0:.2f}".format(ratio).rstrip("0").rstrip(".")
    if s in ("", "-0"):
        s = "0"
    if "." not in s:
        s = s + ".0"
    return s + "x"


def html_escape(s):
    if s is None:
        return ""
    s = s if isinstance(s, type(u"")) else str(s)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def compute_benchmark_seconds(by_ws):
    """
    Returns (benchmark_seconds or None, mode, detail_lines).
    mode is 'tier1', 'fallback', or 'none'.
    """
    tier1_avgs = []
    for name in sorted(TIER1_BENCHMARK_WORKSTATIONS):
        if name not in by_ws:
            continue
        avg = workstation_avg_seconds(by_ws[name])
        if avg is not None:
            tier1_avgs.append((name, avg))

    if tier1_avgs:
        bench = sum(a for _, a in tier1_avgs) / len(tier1_avgs)
        names = ", ".join(html_escape(n) for n, _ in tier1_avgs)
        detail = [
            "Tier 1 benchmark: mean of {0} workstation(s) ({1}) = <strong>{2}</strong>".format(
                len(tier1_avgs), names, html_escape(format_mm_ss(bench))
            ),
        ]
        return bench, "tier1", detail

    candidates = []
    for ws, entries in by_ws.items():
        avg = workstation_avg_seconds(entries)
        if avg is not None:
            candidates.append((ws, avg))

    if not candidates:
        return None, "none", ["No wall-clock data; performance ratio unavailable."]

    fastest_ws, fastest_sec = min(candidates, key=lambda x: x[1])
    detail = [
        "<strong>Note:</strong> None of the Tier 1 workstations (RANCH-135, RANCH-138, "
        "RANCH-139, RANCH-140, RANCH-141, RANCH-142, RANCH-143, RANCH-144) appear in "
        "this dataset with timed render data. Benchmark set to the fastest workstation: "
        "<strong>{0}</strong> (avg <strong>{1}</strong>).".format(
            html_escape(fastest_ws), html_escape(format_mm_ss(fastest_sec))
        ),
    ]
    return fastest_sec, "fallback", detail


def aggregate_logs_from_labeled_texts(labeled_texts):
    """
    labeled_texts: iterable of (label, log_text) e.g. (u"job_report_0", content).
    Returns (by_ws, skipped_labels) where by_ws[worker] = list of (wall, gpu).
    """
    by_ws = defaultdict(list)
    skipped = []
    for label, text in labeled_texts:
        worker, wall, gpu = parse_log_text(text)
        if not worker:
            skipped.append(label)
            continue
        by_ws[worker].append((wall, gpu))
    return by_ws, skipped


def render_report_html(by_ws, skipped, generated_at, source_description):
    """
    Build the same HTML/Markdown hybrid report as the CLI tool.
    source_description: short line shown in header (e.g. job name + id).
    """
    if not by_ws and not skipped:
        return "No task logs with a Worker Name were found.\n"

    all_timed_seconds = []
    total_tasks = 0
    row_cells = []

    for ws in sorted(by_ws.keys()):
        entries = by_ws[ws]
        total_tasks += len(entries)
        timed = [t for t, _ in entries if t is not None]
        all_timed_seconds.extend(timed)

        physical = sorted({g for _, g in entries if g and not _is_placeholder_video_card(g)})
        placeholders = sorted({g for _, g in entries if g and _is_placeholder_video_card(g)})
        if len(physical) == 1:
            gpu_col = physical[0]
        elif len(physical) > 1:
            gpu_col = "mixed: " + "; ".join(physical)
        elif placeholders:
            gpu_col = placeholders[0] if len(placeholders) == 1 else "mixed: " + "; ".join(placeholders)
        else:
            gpu_col = u"\u2014"

        avg_sec = workstation_avg_seconds(entries)
        if avg_sec is not None:
            avg_fmt = format_mm_ss(avg_sec)
        else:
            avg_fmt = u"\u2014"

        row_cells.append((ws, gpu_col, len(entries), avg_fmt, avg_sec))

    benchmark_sec, benchmark_mode, benchmark_detail = compute_benchmark_seconds(by_ws)

    rows_html = []
    for ws, gpu_col, n_tasks, avg_fmt, avg_sec in row_cells:
        if avg_sec is not None and benchmark_sec is not None and benchmark_sec > 0:
            ratio_str = format_perf_ratio(avg_sec / benchmark_sec)
        else:
            ratio_str = u"\u2014"

        rows_html.append(
            (
                "<tr>"
                '<td style="padding:0.55rem 0.65rem;vertical-align:top;word-break:break-word;">{0}</td>'
                '<td style="padding:0.55rem 0.65rem;vertical-align:top;word-break:break-word;">{1}</td>'
                '<td style="padding:0.55rem 0.65rem;text-align:right;vertical-align:top;'
                'font-variant-numeric:tabular-nums;white-space:nowrap;">{2}</td>'
                '<td style="padding:0.55rem 0.65rem;text-align:right;vertical-align:top;'
                'font-variant-numeric:tabular-nums;white-space:nowrap;">{3}</td>'
                '<td style="padding:0.55rem 0.65rem;text-align:right;vertical-align:top;'
                'font-variant-numeric:tabular-nums;white-space:nowrap;">{4}</td>'
                "</tr>"
            ).format(
                html_escape(ws),
                html_escape(gpu_col),
                n_tasks,
                html_escape(avg_fmt),
                html_escape(ratio_str),
            )
        )

    ts_file = generated_at.strftime("%Y-%m-%d_%H-%M-%S")
    ts_readable = generated_at.strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Deadline workstation report",
        "",
        "**Generated:** {0}  ".format(ts_readable),
        "**Source:** {0}  ".format(source_description),
        "**Report file stamp:** `{0}`".format(ts_file),
        "",
        "## Per-workstation summary",
        "",
        '<p style="font-size:0.9rem;line-height:1.5;color:#3f3f46;margin:0 0 0.75em 0;">'
        "<strong>Performance ratio</strong> = (this workstation&rsquo;s average render time) "
        "&divide; (benchmark average). Values above <strong>1.0x</strong> are slower than the "
        "benchmark; below <strong>1.0x</strong> are faster.</p>",
        '<table style="width:100%;border-collapse:collapse;table-layout:fixed;margin:0.75em 0;'
        'box-shadow:0 1px 3px rgba(0,0,0,0.08);border:1px solid #d4d4d8;border-radius:6px;'
        'overflow:hidden;font-size:0.92rem;line-height:1.45;">',
        "<colgroup>",
        '<col style="width:21%">',
        '<col style="width:30%">',
        '<col style="width:10%">',
        '<col style="width:13%">',
        '<col style="width:14%">',
        "</colgroup>",
        "<thead>",
        '<tr style="background:#f4f4f5;border-bottom:2px solid #d4d4d8;">',
        '<th scope="col" style="text-align:left;padding:0.65rem 0.75rem;font-weight:600;">'
        "Workstation</th>",
        '<th scope="col" style="text-align:left;padding:0.65rem 0.75rem;font-weight:600;">'
        "Video card</th>",
        '<th scope="col" style="text-align:right;padding:0.65rem 0.75rem;font-weight:600;">'
        "Tasks</th>",
        '<th scope="col" style="text-align:right;padding:0.65rem 0.75rem;font-weight:600;">'
        "Avg render</th>",
        '<th scope="col" style="text-align:right;padding:0.65rem 0.75rem;font-weight:600;">'
        "Performance ratio</th>",
        "</tr>",
        "</thead>",
        "<tbody>",
    ]
    for i, row in enumerate(rows_html):
        bg = "#fafafa" if i % 2 else "#ffffff"
        lines.append(
            row.replace("<tr>", '<tr style="background:{0};border-bottom:1px solid #ececee;">'.format(bg))
        )
    lines.extend(["</tbody>", "</table>", ""])

    lines.append("### Benchmark")
    lines.append("")
    for para in benchmark_detail:
        lines.append('<p style="font-size:0.9rem;line-height:1.55;margin:0.35em 0;">{0}</p>'.format(para))
    lines.append("")

    lines.append("## Global summary")
    lines.append("")
    untimed = total_tasks - len(all_timed_seconds)
    summary_rows = [
        ("Total tasks (all logs)", str(total_tasks)),
    ]
    if untimed:
        summary_rows.append(("Logs without wall-clock time", str(untimed)))
    if all_timed_seconds:
        overall = sum(all_timed_seconds) / len(all_timed_seconds)
        summary_rows.append(
            (
                "Overall avg render (timed tasks only)",
                "{0} (n={1})".format(format_mm_ss(overall), len(all_timed_seconds)),
            )
        )
    else:
        summary_rows.append(("Overall avg render", u"\u2014 (no wall-clock data)"))

    if benchmark_sec is not None:
        label = (
            "Benchmark avg (Tier 1 pool)"
            if benchmark_mode == "tier1"
            else "Benchmark avg (fastest workstation fallback)"
        )
        summary_rows.append((label, format_mm_ss(benchmark_sec)))

    lines.append(
        '<table style="width:100%;max-width:42rem;border-collapse:collapse;table-layout:fixed;'
        'margin:0.5em 0;border:1px solid #d4d4d8;border-radius:6px;overflow:hidden;font-size:0.92rem;">'
    )
    for label, value in summary_rows:
        lines.append(
            (
                "<tr>"
                '<td style="padding:0.5rem 0.75rem;background:#f4f4f5;font-weight:500;width:55%;'
                'word-break:break-word;border-bottom:1px solid #ececee;">{0}</td>'
                '<td style="padding:0.5rem 0.75rem;text-align:right;font-variant-numeric:tabular-nums;'
                'word-break:break-word;border-bottom:1px solid #ececee;">{1}</td>'
                "</tr>"
            ).format(html_escape(label), html_escape(value))
        )
    lines.append("</table>")

    if skipped:
        lines.extend(["", "## Skipped logs (no Worker Name)", ""])
        lines.append(
            '<ul style="margin:0.35em 0;padding-left:1.25rem;line-height:1.5;font-size:0.92rem;">'
        )
        for name in skipped:
            lines.append("<li><code>{0}</code></li>".format(html_escape(name)))
        lines.append("</ul>")

    return "\n".join(lines) + "\n"


def run_from_labeled_texts(labeled_texts, generated_at=None, source_description=u""):
    """End-to-end: labeled logs -> HTML string."""
    generated_at = generated_at or datetime.now()
    by_ws, skipped = aggregate_logs_from_labeled_texts(labeled_texts)
    return render_report_html(by_ws, skipped, generated_at, source_description)
