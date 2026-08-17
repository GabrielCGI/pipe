import subprocess
import shutil
import re
import os



# --- extensions reconnues -------------------------------------------------
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".tga", ".dpx", ".exr", ".bmp"}


class CreateBurnIn(object):
    def __init__(self,ffmpeg="ffmpeg", fontcolor="white", font= r"C:/Windows/Fonts/consola.ttf", opacity=0.25):
        self.box_opacity = opacity
        self.fontcolor = fontcolor
        self.font = font

        self.ffmpeg = r"C:\ILLOGIC_APP\Prism\2.0.18\app\Tools\FFmpeg\bin\ffmpeg.exe"
        self.ffprobe = self._guess_ffprobe(ffmpeg)

    def burn(self, input_path, output_path=None, user="", camera="", focal="", department="", task="", start_frame=1001, end_frame=None, timestamp=None, overwrite=True):
        if not shutil.which(self.ffmpeg) and not os.path.isfile(self.ffmpeg):
            raise RuntimeError("ffmpeg introuvable : %r" % self.ffmpeg)

        kind, pattern, detected_start = self._analyze(input_path)
        if start_frame is None:
            start_frame = detected_start

        if output_path is None:
            output_path = self._default_output(pattern, kind)

        sample = pattern if kind != "sequence" else self._first_frame(input_path)
        height = self._probe_height(sample)

        # frame de fin (total) : nb de frames -> derniere frame absolue
        if end_frame is None:
            count = self._frame_count(kind, pattern, sample)
            if count:
                end_frame = int(start_frame) + count - 1

        vf = self._build_filter(user, camera, focal, department, task,
                                start_frame, end_frame, height, timestamp)

        cmd = [self.ffmpeg, "-y" if overwrite else "-n"]
        if kind == "sequence":
            cmd += ["-start_number", str(detected_start), "-i", pattern]
        else:
            cmd += ["-i", pattern]
        cmd += ["-vf", vf]

        if kind == "sequence":
            cmd += ["-start_number", str(detected_start), output_path]
        elif kind == "image":
            cmd += [output_path]
        else:
            cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "medium", output_path]

        self._run(cmd)
        return output_path


    def _build_filter(self, user, camera, focal, department, task,
                      start_frame, end_frame, height, timestamp=None):
        fs = max(14, int((height or 1080) / 48))
        pad = int(fs * 0.9)
        y = "h-th-%d" % pad          # ligne du bas
        y_top = "%d" % pad           # ligne du haut

        # date/heure figee au moment du burn (surchargeable via `timestamp`)
        if timestamp is None:
            import datetime as _dt
            timestamp = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")

        # bloc d'options commun a tous les drawtext
        common = [
            "fontfile=" + self._esc_path(self.font),
            "fontsize=%d" % fs,
            "fontcolor=%s" % self.fontcolor,
            "shadowcolor=black@0.9",
            "shadowx=2",
            "shadowy=2",
        ]
        if self.box_opacity > 0:
            common += [
                "box=1",
                "boxcolor=black@%s" % self.box_opacity,
                "boxborderw=%d" % max(4, fs // 4),
            ]
        
        common = ":".join(common)

        mid_text = " ".join(t for t in (camera, focal) if t)

        # frame courante (dynamique) + total : "Frame: 1035/1100"
        cur = "%{eif\\:n+" + str(int(start_frame)) + "\\:d}"
        if end_frame is not None:
            frame_text = self._esc_text("Frame: ") + cur + self._esc_text("/%d" % int(end_frame))
        else:
            frame_text = self._esc_text("Frame: ") + cur


        #----------- create tout les layers pour chaque info qu'on veux burnIn sur l'image ------------
        layers = []

        parts = [p for p in (("User: " + user) if user else "",
                             ("Dept: " + department) if department else "",
                             ("Task: " + task) if task else "") if p]
        left_line = "  | ".join(parts)
        if left_line:
            layers.append(self._drawtext(left_line, "%d" % pad, y, common, literal=True))

        layers.append(self._drawtext(mid_text, "(w-tw)/1.5", y, common, literal=True))
        layers.append(self._drawtext(frame_text, "w-tw-%d" % pad, y, common, literal=False))
        layers.append(self._drawtext(timestamp, "w-tw-%d" % pad, y_top, common, literal=True))


        return ",".join(layers)

    def _drawtext(self, text, x, y, common, literal):
        value = self._esc_text(text) if literal else text
        return "drawtext=text='%s':x=%s:y=%s:%s" % (value, x, y, common)

    # -------------------------------------------------------- analyse entree
    def _analyze(self, input_path):
        ext = os.path.splitext(input_path)[1].lower()
        if ext in VIDEO_EXT:
            return "video", input_path, 0

        if ext in IMAGE_EXT:
            if re.search(r"%0?\d*d", input_path):
                start = self._scan_start(input_path)
                return "sequence", input_path, start

            m = re.search(r"(#+)", input_path)
            if m:
                pat = input_path.replace(m.group(1), "%%0%dd" % len(m.group(1)))
                start = self._scan_start(pat)
                return "sequence", pat, start
            # fichier numerote : shot.1001.jpg -> shot.%04d.jpg
            base = os.path.basename(input_path)
            nums = list(re.finditer(r"\d+", base))
            if nums:
                last = nums[-1]
                width = len(last.group(0))
                pat_base = base[:last.start()] + ("%%0%dd" % width) + base[last.end():]
                pattern = os.path.join(os.path.dirname(input_path), pat_base)
                start = int(last.group(0))

                if self._count_frames(pattern) > 1:
                    return "sequence", pattern, start
            return "image", input_path, 0

        return "video", input_path, 0

    def _scan_start(self, pattern):
        start = self._first_index(pattern)
        return start if start is not None else 0

    def _first_frame(self, input_path):
        ext = os.path.splitext(input_path)[1].lower()
        if ext in IMAGE_EXT and not re.search(r"%0?\d*d|#+", input_path):
            return input_path
        
        _, pattern, start = self._analyze(input_path)
        try:
            return pattern % start
        except TypeError:
            return input_path

    def _first_index(self, pattern):
        d = os.path.dirname(pattern) or "."
        base = os.path.basename(pattern)
        rx = re.escape(base)
        rx = re.sub(r"\\?%0?\d*d", r"(\\d+)", rx)
        rx = "^" + rx + "$"
        indices = []
        try:
            for f in os.listdir(d):
                m = re.match(rx, f)
                if m:
                    indices.append(int(m.group(1)))
        except OSError:
            return None
        return min(indices) if indices else None

    def _count_frames(self, pattern):
        d = os.path.dirname(pattern) or "."
        base = os.path.basename(pattern)
        rx = re.escape(base)
        rx = re.sub(r"\\?%0?\d*d", r"(\\d+)", rx)
        rx = "^" + rx + "$"
        try:
            return sum(1 for f in os.listdir(d) if re.match(rx, f))
        except OSError:
            return 0

    def _default_output(self, pattern, kind):
        d = os.path.dirname(pattern)
        base = os.path.basename(pattern)
        stem, ext = os.path.splitext(base)
        if kind == "sequence":
            # insere _burnin avant le pattern numerique
            m = re.search(r"%0?\d*d", stem)
            if m:
                stem = stem[:m.start()].rstrip(".") + "_burnin." + stem[m.start():]
            else:
                stem = stem + "_burnin"
        else:
            stem = stem + "_burnin"
        return os.path.join(d, stem + ext)

    # ---------------------------- fonction FFMPEG ----------------------------
    def _probe_height(self, sample):
        if not self.ffprobe:
            return None
        
        data = [self.ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "csv=p=0", sample]
        try:
            out = subprocess.check_output(data, stderr=subprocess.STDOUT)
            return int(out.decode("utf-8", "ignore").strip().splitlines()[0])
        except Exception:
            return None

    def _frame_count(self, kind, pattern, sample):
        if kind == "sequence":
            return self._count_frames(pattern)
        if kind == "image":
            return 1
        if not self.ffprobe:
            return None
        for entry in ("nb_frames", "nb_read_frames"):
            data = [self.ffprobe, "-v", "error", "-select_streams", "v:0"]
            if entry == "nb_read_frames":
                data += ["-count_frames"]
            data += ["-show_entries", "stream=%s" % entry, "-of", "csv=p=0", sample]
            try:
                out = subprocess.check_output(data, stderr=subprocess.STDOUT)
                val = out.decode("utf-8", "ignore").strip().splitlines()[0]
                if val and val != "N/A":
                    return int(val)
            except Exception:
                continue
        return None

    def _guess_ffprobe(self, ffmpeg):
        cand = re.sub(r"ffmpeg(\.exe)?$", lambda m: "ffprobe" + (m.group(1) or ""), ffmpeg, flags=re.IGNORECASE)
        if shutil.which(cand) or os.path.isfile(cand):
            return cand
        
        return shutil.which("ffprobe") or None

    # ------------------------------------------------------------- helpers
    def _esc_path(self, path):
        p = path.replace("\\", "/").replace(":", "\\:")
        return "'%s'" % p

    def _esc_text(self, text):
        text = str(text)
        text = text.replace("\\", "\\\\")
        text = text.replace("%", "\\%")
        text = text.replace(":", "\\:")
        text = text.replace("'", "’")
        return text

    def _run(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                "ffmpeg a echoue (code %d):\n%s"
                % (proc.returncode, out.decode("utf-8", "ignore")[-2000:]))
        return out


# --------------------------------------------------------------------- CLI
# def _main():
#     import argparse
#     p = argparse.ArgumentParser(description="Burn-in autonome pour playblast.")
#     p.add_argument("input")
#     p.add_argument("-o", "--output", default=None)
#     p.add_argument("--user", default="")
#     p.add_argument("--camera", default="")
#     p.add_argument("--focal", default="")
#     p.add_argument("--department", "--dept", default="", help="departement (sous l'artiste)")
#     p.add_argument("--task", default="", help="task (sous le departement)")
#     p.add_argument("--start", type=int, default=None, help="numero de la 1ere frame")
#     p.add_argument("--end", type=int, default=None, help="numero de la derniere frame (defaut: auto)")
#     p.add_argument("--date", default=None, help="timestamp affiche en haut a droite (defaut: maintenant)")
#     p.add_argument("--ffmpeg", default="ffmpeg")
#     args = p.parse_args()

#     burner = CreateBurnIn()
#     out = burner.burn(input_path=args.input, output_path=args.output, user=args.user,
#                       camera=args.camera, focal=args.focal, department=args.department, task=args.task,
#                       start_frame=args.start, end_frame=args.end, timestamp=args.date)

#     print(out)


# if __name__ == "__main__":
#     _main()
