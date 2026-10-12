"""Mirror of stdout/stderr into the Logs tab, with de-duplicated auto-refresh output."""

import sys

from .qt import QtGui


def _append(widget, text):
    cursor = widget.textCursor()
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.insertText(text)
    widget.setTextCursor(cursor)
    widget.ensureCursorVisible()


class _TeeStream:
    """File-like tee: original stream + QPlainTextEdit, or a capture
    buffer while `buffer` is set."""

    def __init__(self, original, widget):
        self.original = original
        self.widget = widget
        self.buffer = None

    def write(self, text):
        if not text:
            return
        if self.buffer is not None:
            self.buffer.append(text)
            return
        if self.original is not None:
            try:
                self.original.write(text)
            except Exception:
                pass
        if self.widget is None:
            return
        try:
            _append(self.widget, text)
        except Exception:  # widget already destroyed
            self.widget = None

    def flush(self):
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:
                pass

    def isatty(self):
        return False


class LogConsole:
    """Installs the tee streams for the lifetime of the dialog."""

    def __init__(self, widget):
        self.widget = widget
        self._original_out = sys.stdout
        self._original_err = sys.stderr
        sys.stdout = _TeeStream(sys.stdout, widget)
        sys.stderr = _TeeStream(sys.stderr, widget)
        self._last_output = {}

    def restore(self):
        if self._original_out is not None and isinstance(sys.stdout, _TeeStream):
            sys.stdout = self._original_out
        if self._original_err is not None and isinstance(sys.stderr, _TeeStream):
            sys.stderr = self._original_err
        self._original_out = self._original_err = None

    def run_deduped(self, fn, key):
        """Run `fn` with its output captured; replay it only when it differs
        from the previous run with the same `key`, so an unchanged 15s
        refresh writes nothing. Streams are always released, even when
        `fn` raises."""
        streams = [s for s in (sys.stdout, sys.stderr) if isinstance(s, _TeeStream)]
        captured = []
        for stream in streams:
            stream.buffer = captured
        try:
            fn()
        finally:
            for stream in streams:
                stream.buffer = None

        output = "".join(captured)
        if output and output != self._last_output.get(key, ""):
            # stdout/stderr provenance is lost in the buffer: replay once.
            for stream in streams:
                if stream.original is not None:
                    try:
                        stream.original.write(output)
                    except Exception:
                        pass
                    break
            try:
                _append(self.widget, output)
            except Exception:
                pass
        self._last_output[key] = output
