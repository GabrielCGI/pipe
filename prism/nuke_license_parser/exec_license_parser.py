# import cProfile
# import pstats
# PROFILER = cProfile.Profile()

if __name__ == '__main__':
    
    # PROFILER.enable()
    
    import nuke_license_parser
    import importlib

    def main():
        importlib.reload(nuke_license_parser)
        return nuke_license_parser.main()

    main()
    
    # PROFILER.disable()
    # stats = pstats.Stats(PROFILER)
    # stats.strip_dirs().sort_stats('cumtime').dump_stats(r"R:\pipeline\pipe\prism\nuke_license_parser\stats.prof")