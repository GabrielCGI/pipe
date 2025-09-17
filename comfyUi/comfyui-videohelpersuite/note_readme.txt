J'ai modifier comfui video hlper suite pour permetre d'exposer le path de la video en entrée.


What we added

Goal: have the upload loader also output the absolute file path (for Deadline), without breaking existing nodes.

1) load_video_nodes.py

New node: LoadVideoUploadWithPath (copy/subclass of LoadVideoUpload)
Changes:

Adds a 5th output: ("STRING") named "path".

Resolves the dropdown filename to an absolute path and passes that downstream.

Also injects the path into video_info for convenience.

Core lines:

from comfy import folder_paths
import os

class LoadVideoUploadWithPath(LoadVideoUpload):
    RETURN_TYPES = (imageOrLatent, "INT", "AUDIO", "VHS_VIDEOINFO", "STRING")
    RETURN_NAMES = ("IMAGE", "frame_count", "audio", "video_info", "path")

    def load_video(self, **kwargs):
        abs_path = folder_paths.get_annotated_filepath(strip_path(kwargs["video"]))
        abs_path = os.path.realpath(os.path.abspath(abs_path))  # robust for Deadline/UNC
        kwargs["video"] = abs_path

        images_or_latent, frame_count, audio, video_info = load_video(**kwargs)

        if isinstance(video_info, dict):
            video_info.setdefault("source_path", abs_path)
            video_info.setdefault("source_name", os.path.basename(abs_path))

        return (images_or_latent, frame_count, audio, video_info, abs_path)


Notes:

Keep the input widget name "video" (the web UI hook relies on it).

2) nodes.py

Register the new node so old graphs keep working and the new one exposes path.

NODE_CLASS_MAPPINGS.update({
    "VHS_LoadVideoUploadWithPath": LoadVideoUploadWithPath,
})

NODE_DISPLAY_NAME_MAPPINGS.update({
    "VHS_LoadVideoUploadWithPath": "Load Video (Upload + Path) 🎥🅥🅗🅢",
})

3) web/js/VHS.core.js

Teach the VHS frontend about the new node so the “Choose video to upload” UI and parameter wiring appear.

Add to convDict with the same param order as VHS_LoadVideo:

const convDict = {
  // ...
  VHS_LoadVideo: ["video","force_rate","force_size","frame_load_cap","skip_first_frames","select_every_nth"],
  VHS_LoadVideoPath: ["video","force_rate","force_size","frame_load_cap","skip_first_frames","select_every_nth"],
  VHS_LoadVideoUploadWithPath: ["video","force_rate","force_size","frame_load_cap","skip_first_frames","select_every_nth"], // <-- added
};


Include it in the video upload branch so the callback runs:

} else if (
  nodeData?.name == "VHS_LoadVideo" ||
  nodeData?.name == "VHS_LoadVideoFFmpeg" ||
  nodeData?.name == "VHS_LoadVideoUploadWithPath"   // <-- added
) {
  chainCallback(nodeType.prototype, "onNodeCreated", function() {
    const pathWidget = this.widgets.find((w) => w.name === "video");
    chainCallback(pathWidget, "callback", (value) => {
      if (!value) return;
      let extension = value.slice(value.lastIndexOf(".")+1);
      let format = ["gif","webp","avif"].includes(extension) ? "image" : "video";
      format += "/" + extension;
      this.updateParameters({ filename: value, type: "input", format: format }, true);
    });
  });
}


After editing the JS:

Restart ComfyUI.

Hard-refresh the browser (disable cache in DevTools or Ctrl/Cmd+Shift+R).

Usage & pipeline notes

The new node outputs (IMAGE, frame_count, audio, video_info, **path**).

path is an absolute (normalized) path—ideal for Deadline workers.

Old nodes remain untouched; existing graphs won’t break.

That’s it.