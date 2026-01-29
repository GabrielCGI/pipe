
import os
import sys
import subprocess
import json

settingsFile = sys.argv[3]
endFrame = int(sys.argv[2])
startFrame = int(sys.argv[1])

executable = os.getenv("HUSK_PATH")
if not executable or not os.path.exists(executable):
    executable = os.getenv("PRISM_DEADLINE_HUSK_PATH")
    if not executable or not os.path.exists(executable):
        raise Exception("The Husk render executable is not defined or doesn't exist. Use \"HUSK_PATH\" or \"PRISM_DEADLINE_HUSK_PATH\" environment varialbe to specify a path.")

with open(os.path.dirname(__file__) + "/" + settingsFile, "r") as f:
    settings = json.load(f)

renderer = settings["renderer"]
renderSettings = settings["rendersettings"]
imgOutput = settings["outputpath"]
usdFilePath = settings["usdfile"]
frameCount = str(endFrame-startFrame+1)
useTiles = settings.get("useTiles", False)
tilesX = settings.get("tilesX", 1)
tilesY = settings.get("tilesY", 1)
if useTiles:
    tileFrame = int(settings.get("startFrame", 1))
    tileIdx = startFrame - tileFrame
    startFrame = endFrame = tileFrame
    frameCount = "1"
    base, ext = os.path.splitext(imgOutput)
    if "$F4" in imgOutput:
        base = base.replace("$F4", "%04d" % startFrame).strip(".")
        ext = base[-5:] + ext
        base = base[:-5]

    xtile = tileIdx % tilesX
    ytile = int(tileIdx/tilesY)
    tileSuffix = "_tile_%sx%s_%sx%s_" % (xtile+1, ytile+1, tilesX, tilesY)

def readStdout(proc):
    while True:
        line = proc.stdout.readline()
        line = line.decode("utf-8", errors="ignore")
        if "ALF_PROGRESS" in line:
            print("Progress: %s" % line.replace("ALF_PROGRESS ", ""))

        if line == '' and proc.poll() is not None:
            break

        print(line)


# imgOutput = "\"%s\"" % imgOutput
usdFilePath = usdFilePath.replace("####", "$F4")
args = [
    executable,
    usdFilePath,
    "--output",
    imgOutput,
    "--frame",
    str(startFrame),
    "--frame-count",
    frameCount,
    "--renderer",
    renderer,
    "--verbose",
    "aC6",
    "--settings",
    renderSettings,
#   "--windows-console",
#    "wait",
]

if settings.get("legacyExrMode"):
    args += ["--exrmode", settings.get("legacyExrMode")]

if settings.get("camera"):
    args += ["--camera", settings.get("camera")]

if settings.get("width") and settings.get("height"):
    width = settings.get("width")
    height = settings.get("height")
    args += ["--res", str(width), str(height)]

if useTiles:
    args += ["--tile-count", str(tilesX), str(tilesY)]
    args += ["--tile-index", str(tileIdx)]
    args += ["--tile-suffix", tileSuffix]

print("command args: %s" % (args))
p = subprocess.Popen(args, stdout=subprocess.PIPE)
readStdout(p)

lastFrame = imgOutput.replace("$F4", "%04d" % (endFrame))
if useTiles:
    base, ext = os.path.splitext(lastFrame)
    lastFrame = base + tileSuffix + ext

if p.returncode:
    raise RuntimeError("renderer exited with code %s" % p.returncode)
elif not os.path.exists(lastFrame):
    raise RuntimeError("expected output doesn't exist %s" % (lastFrame))
else:
    print("task completed successfully")
