# -*- coding: utf-8 -*-
"""
Deadline Monitor script: selected jobs -> fetch report logs from Repository -> HTML benchmark.

Deploy this file next to deadline_benchmark_core.py (same folder), or place the core under
I:\\tmp\\GABI\\benchmark so it can be imported.

Output: <OUTPUT_DIR>\\deadline_workstation_report_<jobname>_<timestamp>.html
"""

from __future__ import division

import codecs
import os
import sys
import webbrowser
from datetime import datetime

try:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = ""

_CORE_DIRS = [_SCRIPT_DIR, r"R:\pipeline\pipe\deadline\benchmark_ranch"]
for _d in _CORE_DIRS:
    if _d and os.path.isdir(_d) and _d not in sys.path:
        sys.path.insert(0, _d)

try:
    from deadline_benchmark_core import run_from_labeled_texts
except ImportError:
    run_from_labeled_texts = None

OUTPUT_DIR = r"R:\pipeline\pipe\deadline\benchmark_ranch\output"

# Deadline uses reserved task IDs for pre/post job script tasks (see report Task ID in Monitor).
_EXCLUDED_PRE_POST_TASK_IDS = frozenset((-2, -3))


def _report_type_str(report):
    for attr in ("ReportTypeOf", "ReportType"):
        if hasattr(report, attr):
            try:
                return u"{0}".format(getattr(report, attr))
            except Exception:
                pass
    return u""


def _is_pre_or_post_report(report):
    """True if this report is for a pre-job or post-job task (not a normal render task)."""
    try:
        tid = int(report.ReportTaskID)
    except Exception:
        tid = None
    if tid is not None and tid in _EXCLUDED_PRE_POST_TASK_IDS:
        return True

    try:
        frame = u"{0}".format(report.ReportFrameString).strip().lower()
    except Exception:
        frame = u""
    if not frame:
        pass
    elif frame in (u"pre", u"post"):
        return True
    elif u"pre job" in frame or u"post job" in frame:
        return True

    rtype = _report_type_str(report).lower()
    if rtype:
        if u"prejob" in rtype or u"postjob" in rtype:
            return True
        if u"pre job" in rtype or u"post job" in rtype:
            return True

    return False


def _ensure_dir(path):
    if os.path.isdir(path):
        return
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def _sanitize_filename(s):
    if s is None:
        return "job"
    s = u"{0}".format(s)
    bad = '<>:"/\\|?*'
    out = []
    for c in s:
        if c in bad or ord(c) < 32:
            out.append("_")
        else:
            out.append(c)
    out = u"".join(out).strip("._")
    if len(out) > 120:
        out = out[:120]
    return out or u"job"


def _write_utf8(path, text):
    with codecs.open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _open_in_default_browser(path, log_fn=None):
    """Open a file with the OS default handler (browser for .html). Windows: os.startfile."""
    path = os.path.normpath(os.path.abspath(path))
    try:
        os.startfile(path)
        if log_fn:
            log_fn("Opened in default browser: " + path)
        return
    except (AttributeError, OSError):
        pass
    try:
        uri = "file:///" + path.replace("\\", "/")
        webbrowser.open(uri)
        if log_fn:
            log_fn("Opened in default browser: " + path)
    except Exception as e:
        if log_fn:
            log_fn("Could not open browser for {0}: {1}".format(path, e))


def __main__(*args):
    from Deadline.Scripting import ClientUtils, MonitorUtils, RepositoryUtils

    if run_from_labeled_texts is None:
        ClientUtils.LogText(
            "deadline_benchmark_core.py not found. Place it next to this script or on a path in _CORE_DIRS."
        )
        return

    selected_jobs = MonitorUtils.GetSelectedJobs()
    if not selected_jobs:
        ClientUtils.LogText("No jobs selected.")
        return

    try:
        _ensure_dir(OUTPUT_DIR)
    except Exception as e:
        ClientUtils.LogText("Cannot create output dir {0}: {1}".format(OUTPUT_DIR, e))
        return

    generated_at = datetime.now()
    stamp = generated_at.strftime("%Y-%m-%d_%H-%M-%S")
    written = []

    for job in selected_jobs:
        job_id = job.JobId
        job_name = job.JobName
        labeled = []

        try:
            report_collection = RepositoryUtils.GetJobReports(job_id)
            reports = report_collection.GetAllReports()
        except Exception as e:
            ClientUtils.LogText("GetJobReports failed for {0}: {1}".format(job_id, e))
            continue

        for i in range(len(reports)):
            report = reports[i]
            if _is_pre_or_post_report(report):
                continue
            label = u"{0}_report_{1}_{2}".format(job_id, i, report.ReportID)
            try:
                log_content = RepositoryUtils.GetJobReportLog(report)
            except Exception as e:
                ClientUtils.LogText("GetJobReportLog {0}: {1}".format(label, e))
                continue
            if log_content is None:
                continue
            labeled.append((label, log_content))

        if not labeled:
            ClientUtils.LogText("No report logs for job: {0}".format(job_name))
            continue

        source_description = u"Job **{0}** (`{1}`) — {2} report log(s) from Repository".format(
            job_name, job_id, len(labeled)
        )
        html_body = run_from_labeled_texts(
            labeled, generated_at=generated_at, source_description=source_description
        )

        safe_name = _sanitize_filename(job_name)
        out_name = u"deadline_workstation_report_{0}_{1}.html".format(safe_name, stamp)
        out_path = os.path.join(OUTPUT_DIR, out_name)

        try:
            _write_utf8(out_path, html_body)
            written.append(out_path)
            ClientUtils.LogText("Wrote: " + out_path)
            _open_in_default_browser(out_path, log_fn=ClientUtils.LogText)
        except Exception as e:
            ClientUtils.LogText("Failed to write {0}: {1}".format(out_path, e))

    if not written:
        ClientUtils.LogText("No HTML files were written.")
    else:
        ClientUtils.LogText("Done. {0} file(s).".format(len(written)))
