import time
import os
import argparse

from pxr import Sdf, UsdUtils

def getDependencies(usd_file):

    asset_path = Sdf.AssetPath(usd_file)

    dependencies = UsdUtils.ComputeAllDependencies(asset_path)
    layers, assets, unresolved_paths = dependencies

    layers_path = []
    for layer in layers:
        layers_path += layer.GetCompositionAssetDependencies()
    layers_path = [layer for layer in layers_path if layer != '']

    relative_paths = list(set(layers_path + assets + unresolved_paths))

    absolute_paths = []
    current_usd_directory = os.path.dirname(usd_file)
    for file_path in relative_paths:
        
        abs_file_path = os.path.join(current_usd_directory, file_path)
        abs_file_path = os.path.abspath(abs_file_path)
        absolute_paths.append(abs_file_path)
            
    return relative_paths, absolute_paths

def run(stage):
    print(stage)
    pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Parse every dependecies from an usd file")
    parser.add_argument("usd_file")
    args = parser.parse_args()
    usd_file = args.usd_file

    start = time.process_time_ns()

    rel_paths, abs_paths = getDependencies(usd_file)

    time_ns = time.process_time_ns() - start
    time_sec = time_ns / 1000000000

    print("Relative paths:")
    for path in rel_paths:
        print(f"--- {path}")

    print("Absolute paths:")
    for path in abs_paths:
        print(f"--- {path}")
    
    print(f"Time taken : {time_sec} s | {time_ns} ns")