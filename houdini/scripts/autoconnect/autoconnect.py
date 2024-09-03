import material
# import hou
import os
import glob
import re


def get_latest_sha():
    pass

def get_sha_from_dir(directory_path):
    
    directory_path = os.path.join(directory_path, "**")
    
    pattern_name = ""
    
    shaders = []
    for file in glob.glob(pathname=directory_path, recursive=True):
        if (".exr" in file) and (not ".rat" in file):
            directory_path, file_name = os.path.split(file)
            
            version_span = re.search("v\d{4}", file_name).span()
            first_key_span = material.firstKeyWord(file_name)
            if first_key_span is not None:
                shader_name =  file_name[version_span[1]+1:first_key_span[0]-1]                
                
                found = False
                for shader in shaders:
                    if shader.name == shader_name:
                        shader.parse(file)
                        found = True
                
                if not found:
                    newShader = material.Shader(shader_name)
                    newShader.parse(file)
                    shaders.append(newShader)
    return shaders
                    

def get_plug_sha():
    pass

def main():
    
    # dir_path = hou.ui.selectFile(file_type=hou.fileType.Directory)
    shaders = get_sha_from_dir(r"I:\ash_2407\03_Production\Assets\Characters\ash\Textures\textures")
    
    # space = " "*3
    # for sh in shaders:
    #     print(sh.name)
    #     for mat in sh.materials:
    #         print(space + mat.path)
    #         print(space + mat.material_type)
    #         print(space + mat.data_type)
    #         print(space + mat.udim)
    
if __name__ == "__main__":
    main()