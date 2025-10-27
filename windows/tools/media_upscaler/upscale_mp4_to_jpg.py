import os
import sys
import glob
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)
logger.propagate = False
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)

FFMPEG_PATTERN = "C:/ILLOGIC_APP/Prism/*/app/Tools/FFmpeg/bin/ffmpeg.exe"
FFMPEG = glob.glob(FFMPEG_PATTERN)[-1]


def decodeSubprocessOutput(process: subprocess.Popen[str]):
    for line in process.stdout:
        logger.info(line.strip())


def generateOutputPath(inputPath):
    if not 'Playblasts' in inputPath:
        logger.warning(f'Not a playblast: {inputPath}:')
        return
    
    shot_len = 6
    output_directory = Path(os.path.dirname(inputPath))
    parts = list(output_directory.parts)
    if len(parts) < shot_len:
        logger.warning(f'Ill formed path {parts}')
        return
    
    # Get path informations
    shot_idx = -shot_len
    sequence_idx = -shot_len+1
    task_idx = -shot_len+4
    version_idx = -shot_len+5
    
    # Create basename from shot informations 
    base = (f'{parts[shot_idx]}-{parts[sequence_idx]}'
            f'_{parts[task_idx]}_{parts[version_idx]}')
   
    parts[task_idx] = f'upscaled_{parts[task_idx]}'
    output_directory = Path(*parts)
    os.makedirs(output_directory, exist_ok=True)
   
    basename = f"{base}_upscaled.%04d.jpg"
    
    return (output_directory / basename).as_posix()


def getStartFrame(input_path: str) -> int | None:
    input_directory = os.path.dirname(input_path)
    version_info = os.path.join(input_directory, 'versioninfo.json')
    if not os.path.exists(version_info):
        logger.warning('Version info file do not exists')
        return
    with open(version_info, 'r') as version_file:
        version_data = json.load(version_file)
    startframe = version_data.get('startframe')
    if startframe is None:
        logger.warning('No info about start frame in version info file')
        return
    try:
        return int(startframe)
    except:
        logger.warning(f'Cannot convert "{startframe}" to an integer')
        return
    

def uspcalemp4tojpg(mp4_path, output_path, startframe, resX=6000, resY=6000):
    command = [
        FFMPEG,
        '-i',
        mp4_path,
        '-start_number',
        f'{startframe}',
        '-vf',
        f'scale={resX}x{resY}:flags=lanczos',
        output_path
    ]
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            startupinfo=si    
        )
        decodeSubprocessOutput(process)
        process.wait()
    except Exception as e:
        logger.info(e)
    

def upscale(inputPath):
    output_path = generateOutputPath(inputPath)
    startframe = getStartFrame(inputPath)
    if not startframe:
        return
    uspcalemp4tojpg(inputPath, output_path, startframe)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info(sys.argv)
        raise Exception(
            "Bad arguments number. format: "
            "<path_to_this_script> "
            "<path_to_mp4> "
        )
    path = sys.argv[1]
    upscale(path)