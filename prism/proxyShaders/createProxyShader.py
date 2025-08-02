from pxr import Sdf
import os 



NAME_VAR_LOW = "low"
NAME_VAR_HIGH = "high"
NAME_SET = "res"

def setProxyShd(usdFolder):
    fileMTL = os.path.join(usdFolder, "mtl.usdc")
    if not os.path.exists(fileMTL):
        print("file not found")
        return None
    
    materials = []
    shader_names = []
    file_mtl = Sdf.Layer.FindOrOpen(fileMTL)
    Error = False
    for prim in file_mtl.rootPrims:
        if not materials or not shader_names:
            getMaterialAndShaders(prim, file_mtl, materials, shader_names)
        
        if prim.specifier != Sdf.SpecifierDef:
            continue
    
        
        try:
            primRES = Sdf.VariantSetSpec(prim, NAME_SET)
            variantHigh = Sdf.VariantSpec(primRES, NAME_VAR_HIGH)
            variantLow = Sdf.VariantSpec(primRES, NAME_VAR_LOW)

            prim.variantSelections[NAME_SET] = NAME_VAR_HIGH
            prim.variantSetNameList.Prepend(NAME_SET)

            
            overMtl = Sdf.PrimSpec(variantLow.primSpec, "mtl", Sdf.SpecifierOver, "")
            WriteVariant(overMtl, materials, shader_names)
        except:Error = True

    if not Error:
        file_mtl.Save()
        print('\nfile save')
    else:
        print('une erreur est survenue')

def getMaterialAndShaders(prim, file, materials, shader_names):
    primAssetPath = None
    PrimOVERAssetsPath = None
    variant = True
    for primchild in prim.nameChildren.values():
        print(primchild)
        if str(primchild.path).endswith("/ASSET"):
            primAssetPath = primchild
        else:
            PrimOVERAssetsPath = primchild.name
        
        print(PrimOVERAssetsPath)

    if not primAssetPath or not PrimOVERAssetsPath: print('is not a variant');variant = False
    
    print("recupe la liste des mat et des shaders à mipmap----------")
    materialMtlPath = None
    if variant:
        materialMtlPath = file.GetPrimAtPath(Sdf.Path(f"{prim.path}/{PrimOVERAssetsPath}/mtl"))
    else:
        materialMtlPath = file.GetPrimAtPath(Sdf.Path(f"{prim.path}/{PrimOVERAssetsPath}"))
    
    if not materialMtlPath:
        return None
    
    
    for child in materialMtlPath.nameChildren.values():
        materials.append(child.name)
        for shader in child.nameChildren.values():
            if not shader.name in shader_names:
                shader_names.append(shader.name)

def WriteVariant(prim, materials, shader_names):
    for mat in materials:
        print(mat)
        shader_prim = Sdf.PrimSpec(prim, mat, Sdf.SpecifierOver, "")
        for shader in shader_names:
            inputM_prim = Sdf.PrimSpec(shader_prim, shader, Sdf.SpecifierOver, "")
            attr = Sdf.AttributeSpec(inputM_prim, "inputs:karma_width", Sdf.ValueTypeNames.Float, Sdf.VariabilityVarying)
            attr.default = 80.0
            