
if __name__ == '__main__':
    import cProfile
    import pstats
    profiler = cProfile.Profile()
    profiler.enable()
    import nuke_license_parser
    import importlib

    def main():
        importlib.reload(nuke_license_parser)
        return nuke_license_parser.main()
    main()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs().sort_stats('cumtime').dump_stats(r"R:\pipeline\pipe\prism\nuke_license_parser\stats.prof")