import base64
import requests
import time
import os
import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import subprocess

log_file = None

# Try to import Prism USD plugin API if available
try:
    import core
    prism_available = True
except ImportError:
    prism_available = False

def log(msg):
    print(msg)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

def generate_3d_model_with_textures(image_path):
    global log_file

    # Validate image path
    if not os.path.isfile(image_path):
        log(f"Invalid image path: {image_path}")
        subprocess.Popen(["code", log_file], shell=True)
        return
    
    # Prepare output folder
    base_dir = os.path.dirname(image_path)
    output_folder = os.path.join(base_dir, "AI")
    os.makedirs(output_folder, exist_ok=True)

    # Prepare log file
    log_file = os.path.join(output_folder, "meshai_log.txt")

    if os.path.exists(log_file):
        os.remove(log_file)

    log("Starting MeshAI conversion task...")
    subprocess.Popen(["code", log_file], shell=True)
    # Encode image
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    data_uri = f"data:image/png;base64,{encoded_string}"

    # Prepare payload
    payload = {
        "image_url": data_uri,
        "enable_pbr": False,
        "should_remesh": True,
        "should_texture": True
    }

    
    key = "msy_LxT8ye3YCL9ppmLoxx3QVkZdAam5Yv7AzlT7"
    #key = "msy_dummy_api_key_for_test_mode_12345678"
    headers = {
        "Authorization": f"Bearer {key}"
    }

    # Submit task
    response = requests.post(
        "https://api.meshy.ai/openapi/v1/image-to-3d",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    task_id = response.json()["result"]
    log("Task created. ID: " + task_id)

    # Poll for completion
    while True:
        task_status = requests.get(
            f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}",
            headers=headers
        )
        task_status.raise_for_status()
        status_data = task_status.json()

        status = status_data["status"]
        progress = status_data.get("progress", 0)

        if status == "SUCCEEDED":
            log("Task finished.")
            break
        elif status == "FAILED":
            raise RuntimeError("Image-to-3D task failed.")

        log(f"Status: {status} | Progress: {progress}% | Retrying in 5s...")
        time.sleep(5)

    # Save .obj model
    model_urls = status_data.get("model_urls", {})
    if "obj" in model_urls:
        obj_url = model_urls["obj"]
        obj_filename = os.path.splitext(os.path.basename(image_path))[0] + "_model.obj"
        obj_path = os.path.join(output_folder, obj_filename)
        obj_response = requests.get(obj_url)
        obj_response.raise_for_status()
        with open(obj_path, "wb") as f:
            f.write(obj_response.content)
        log(f"Model saved to {obj_path}")

    usdz_path = None

    # Save .usdz model
    if "usdz" in model_urls:
        usdz_url = model_urls["usdz"]
        usdz_filename = os.path.splitext(os.path.basename(image_path))[0] + "_model.usdz"
        usdz_path = os.path.join(output_folder, usdz_filename)
        usdz_response = requests.get(usdz_url)
        usdz_response.raise_for_status()
        with open(usdz_path, "wb") as f:
            f.write(usdz_response.content)
        log(f"USDZ model saved to {usdz_path}")
    else:
        log("No USDZ model found.")

    # Save textures
    texture_sets = status_data.get("texture_urls", [])
    if not texture_sets:
        log("No textures found.")
    else:
        for i, texture_set in enumerate(texture_sets):
            for texture_type, url in texture_set.items():
                texture_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_tex_{texture_type}.png"
                texture_path = os.path.join(output_folder, texture_filename)
                try:
                    tex_response = requests.get(url)
                    tex_response.raise_for_status()
                    with open(texture_path, "wb") as tex_file:
                        tex_file.write(tex_response.content)
                    log(f"Texture saved: {texture_filename}")
                except Exception as e:
                    log(f"Error downloading texture '{texture_type}': {e}")

    log("All outputs saved to: " + output_folder)
    
    subprocess.Popen(["explorer", os.path.realpath(output_folder)])


def run():
    Tk().withdraw()
    image_path = askopenfilename(
        title="Select an image file",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
    )

    if not image_path:
        log("⚠️ No file selected. Exiting.")
        return

    if not os.path.isfile(image_path):
        log(f"\n❌ File not found or invalid path:\n{image_path}")
    else:
        generate_3d_model_with_textures(image_path)

run()