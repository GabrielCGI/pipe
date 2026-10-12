import logging



logger = logging.getLogger("IllogicPlugin."+__name__)



def main(*args, **kwargs):
    logger.info("START: file hook getMediaConverterFFmpegArgs")
    ffmpegArgs = args[1]
    newArgs = [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "slow",
        "-vf", "scale=in_color_matrix=bt709:out_color_matrix=bt709,format=yuv420p",
        "-color_range", "tv",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
    ]

    outputPath = ffmpegArgs[-1]
    inputIdx = ffmpegArgs.index("-i")
    newFfmpegArgs = ffmpegArgs[:inputIdx+2] + newArgs + [outputPath]
    ffmpegArgs[:] = newFfmpegArgs

    logger.info(f"changed ffmpeg args: {ffmpegArgs}")
    logger.info("END: file hook getMediaConverterFFmpegArgs")