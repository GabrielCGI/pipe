import os
import torch
from textwrap import dedent as cleandoc
from pathlib import PureWindowsPath
import folder_paths
try:
    from comfy.comfy_types.node_typing import IO
except:
    class IO:
        BOOLEAN = "BOOLEAN"
        INT = "INT"
        FLOAT = "FLOAT"
        STRING = "STRING"
        NUMBER = "FLOAT,INT"
        IMAGE = "IMAGE"
        MASK = "MASK"
        ANY = "*"

class ImageSplitList:
    """
    Split a batch of images into N consecutive chunks of length frame_count.
    Example: frame_count=20, tiles_number=2
      - output[0] => images[0:20]
      - output[1] => images[20:40]
    """
    CATEGORY = "Illogic/Image"
    FUNCTION = "doit"
    MAX_TILES = 8  # adjust if you need more outputs

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "frame_count": ("INT", {
                    "default": 20, "min": 1, "max": 4096, "step": 1
                }),
                "tiles_number": ("INT", {
                    "default": 2, "min": 1, "max": s.MAX_TILES, "step": 1
                }),
            }
        }

    RETURN_TYPES = tuple("IMAGE" for _ in range(MAX_TILES))
    RETURN_NAMES = tuple(f"images_{i}" for i in range(MAX_TILES))

    def doit(self, images, frame_count, tiles_number):
        if tiles_number > self.MAX_TILES:
            tiles_number = self.MAX_TILES

        B = images.shape[0]
        outputs = []

        for i in range(tiles_number):
            start = i * frame_count
            end = start + frame_count
            if start >= B:
                outputs.append(None)
            else:
                outputs.append(images[start:min(end, B)])

        while len(outputs) < self.MAX_TILES:
            outputs.append(None)

        return tuple(outputs)

class InsertMasksToBatchIndexed:
    """
    Inserts masks at specified indices into the original mask batch.
    - mode='replace': replace existing items at indices with provided masks.
    - mode='insert' : insert BEFORE each index (indices are on the growing list).
    """
    RETURN_TYPES = ("MASK",)
    FUNCTION = "insertmasksfrombatch"
    CATEGORY = "Illogic/Mask"
    DESCRIPTION = "Insert/replace masks at given indices in a mask batch."

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "original_masks": ("MASK",),
                "masks_to_insert": ("MASK",),
                "indexes": ("STRING", {"default": "0, 1, 2", "multiline": True}),
            },
            "optional": {
                "mode": (["replace", "insert"],),
            }
        }

    def _parse_indices(self, indexes: str):
        if not isinstance(indexes, str):
            return []
        cleaned = indexes.replace("\n", ",").replace(";", ",")
        parts = [p.strip() for p in cleaned.split(",") if p.strip() != ""]
        out = []
        for p in parts:
            try:
                out.append(int(p))
            except ValueError:
                pass
        return out

    def insertmasksfrombatch(self, original_masks, masks_to_insert, indexes, mode="replace"):
        index_list = self._parse_indices(indexes)
        if not index_list:
            return (original_masks,)

        input_masks = original_masks.clone()
        if not isinstance(masks_to_insert, torch.Tensor):
            masks_to_insert = torch.tensor(masks_to_insert)

        B = input_masks.shape[0]

        if mode == "replace":
            # Replace where possible; skip out-of-range indices
            max_pairs = min(len(index_list), masks_to_insert.shape[0])
            for k in range(max_pairs):
                idx = int(index_list[k])
                if 0 <= idx < B:
                    input_masks[idx] = masks_to_insert[k]
            return (input_masks,)

        # mode == "insert"
        sorted_indices = sorted(index_list)
        new_masks = []
        insert_ptr = 0
        read_ptr = 0
        total_inserts = len(sorted_indices)

        # Build new sequence of length B + total_inserts
        for pos in range(B + total_inserts):
            if insert_ptr < total_inserts and pos == int(sorted_indices[insert_ptr]):
                src = masks_to_insert[insert_ptr % masks_to_insert.shape[0]]
                new_masks.append(src)
                insert_ptr += 1
            else:
                if read_ptr < B:
                    new_masks.append(input_masks[read_ptr])
                    read_ptr += 1
                else:
                    # extra inserts beyond end
                    src = masks_to_insert[insert_ptr % masks_to_insert.shape[0]]
                    new_masks.append(src)
                    insert_ptr += 1

        output = torch.stack(new_masks, dim=0)
        return (output,)

class FilePathPicker:
    """
    Pick a media path (image or video) from the input folder, or upload an image.
    Returns only the resolved absolute path as STRING.
    - 'file' lists both images and videos found under ComfyUI's input directory.
    - 'upload_image' gives you the image upload button; if provided, it takes priority.
    """

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        # include both images and videos
        files = folder_paths.filter_files_content_types(files, ["image", "video"])
        files = sorted(files)

        return {
            "required": {
                # Dropdown that includes both images and videos in input/
                "file": (files, {}),
            },
            "optional": {
                # Optional upload button for images (videos can't use this UI control)
                "upload_image": ("IMAGE", {"image_upload": True}),
            }
        }

    CATEGORY = "Illogic/Path"
    RETURN_TYPES = ("STRING",)   # or (IO.STRING,) if you prefer using your IO class
    RETURN_NAMES = ("path",)
    FUNCTION = "get_path"

    def get_path(self, file, upload_image=None):
        # If an image was uploaded via the UI, prefer that
        if upload_image is not None:
            # For IMAGE inputs, ComfyUI still passes a filename token we can resolve
            image_path = folder_paths.get_annotated_filepath(upload_image)
            return (os.path.normpath(image_path),)

        # Otherwise resolve whatever was chosen in the dropdown (image or video)
        media_path = folder_paths.get_annotated_filepath(file)
        return (os.path.normpath(media_path),)

# tiny helper: remove only OUTER quotes, not inner ones
def _dequote(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    pairs = [
        ('"', '"'),
        ("'", "'"),
        ("“", "”"),
        ("‘", "’"),
    ]
    for lq, rq in pairs:
        if s.startswith(lq) and s.endswith(rq) and len(s) >= 2:
            return s[1:-1].strip()
    return s

class PathProcessor():
    """
    PathProcessor rewrites a drive-rooted Windows path under a configurable base,
    and produces:
      - output_path: full rewritten file path with a configurable suffix inserted before the extension
      - output_dir: directory containing output_path
      - job_name: original filename (with extension)
      - deadline_dir: original input directory with an appended '\\upscale'
                      (e.g. I:\\some\\dir\\file.mp4 -> I:\\some\\dir\\upscale)

    Notes:
    - Accepts paths with surrounding quotes, e.g. "I:/foo/bar.mp4" or 'I:\\foo\\bar.mp4'
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": (IO.STRING, {"default": ""}),
                "replacement_base": (IO.STRING, {"default": "I:/tmp/__comfy/USDU"}),
                "filename_suffix": (IO.STRING, {"default": "_upscale_"}),
            }
        }

    RETURN_TYPES = (IO.STRING, IO.STRING, IO.STRING, IO.STRING)
    RETURN_NAMES = ("output_path", "output_dir", "job_name", "deadline_dir")
    CATEGORY = "Illogic/PathProcessor"
    DESCRIPTION = cleandoc(__doc__ or "")
    FUNCTION = "process"

    def process(self, path: str, replacement_base: str, filename_suffix: str) -> tuple[str, str, str, str]:
        """
        Rewrites any drive-rooted/UNC Windows path under replacement_base and appends the suffix
        before the extension. If the input path has no drive, it is treated as relative and
        placed under replacement_base.

        Also returns deadline_dir which is the input path's parent directory with '\\upscale' appended.
        """
        # Dequote & sanitize inputs
        raw_path = _dequote(path or "")
        raw_path = raw_path.strip()
        base = _dequote(replacement_base or "").strip().rstrip("\\/")

        # Fallbacks if missing inputs
        if not raw_path:
            return ("", base.replace("/", "\\"), "", "")

        def winstr(pw: PureWindowsPath) -> str:
            return str(pw).replace("/", "\\")

        try:
            p = PureWindowsPath(raw_path)
        except Exception:
            # If parsing fails, return passthrough-ish outputs
            dirname = os.path.dirname(raw_path)
            basename = os.path.basename(raw_path)
            deadline_dir = os.path.join(dirname, "upscale")
            return (raw_path, dirname, basename, deadline_dir)

        # Original filename (job name)
        orig_filename = p.name

        # Drop drive/UNC anchor to build relative segment
        parts = p.parts
        rel = PureWindowsPath(*parts[1:]) if parts else PureWindowsPath()

        # If path has no drive/root, treat as relative
        if not p.drive and not p.root:
            rel = PureWindowsPath(str(p).lstrip("\\/"))

        # Compute filename with suffix before full extension (handles multi-suffix)
        ext = "".join(p.suffixes)
        stem = p.name[:-len(ext)] if ext else p.stem
        new_filename = f"{stem}{filename_suffix}{ext}"

        # Target base
        base_pw = PureWindowsPath(base) if base else PureWindowsPath()

        # Preserve relative dir structure under base
        rel_parent = rel.parent if str(rel.parent) not in ("", ".") else PureWindowsPath()
        out_dir_pw = base_pw.joinpath(rel_parent)
        out_path_pw = out_dir_pw.joinpath(new_filename)

        # Deadline dir = input parent + "upscale"
        input_parent_pw = p.parent
        deadline_dir_pw = input_parent_pw.joinpath("upscale")

        output_dir = winstr(out_dir_pw)
        output_path = winstr(out_path_pw)
        job_name = orig_filename
        deadline_dir = winstr(deadline_dir_pw)

        return (output_path, output_dir, job_name, deadline_dir)


# ---- Node registration ----

NODE_CLASS_MAPPINGS = {
    "illogic ImageSplitList": ImageSplitList,
    "illogic PathProcessor": PathProcessor,
    "illogic InsertMasksToBatchIndexed": InsertMasksToBatchIndexed,
    "illogic FilePathPicker": FilePathPicker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "illogic ImageSplitList": "ImageSplitList",
    "illogic PathProcessor": "PathProcessor",
    "illogic InsertMasksToBatchIndexed": "InsertMasksToBatchIndexed",
    "illogic FilePathPicker": "FilePathPicker",
}