"""
This Module:
- Handles the material setup for each renderer (Redshift, Vray, Arnold)
"""
import maya.cmds as mc
import maya.mel as melc

from Megascans.ImporterSetup import importerSetup
instance = importerSetup.getInstance()


#MATERIAL SETUP FUNCTIONS


#########################################################################################

"""Arnold3_Setup creates a Redshift material setup. """

class Arnold():
    def __init__(self):
        self.shaderList = instance.defaultShaderList
        self.ShaderName = ""
        if instance.isMultiMat:
            for index,shader in enumerate(self.shaderList):
                if instance.MultiMaterial[index].lower() == 'glass':
                    self.GlassSetup(shader)
                else:
                    self.OpaqueSetup(shader)
        else:
            self.OpaqueSetup(None)

    def OpaqueSetup(self, shader):
        nodes_ = mc.allNodeTypes()
        #print(nodes_)

        #Standard Surface is not available in 2019 and 2018
        if "standardSurface" in nodes_:
            self.ShaderName = "standardSurface"
        else:
            self.ShaderName = "aiStandardSurface"

        if len(instance.tex_nodes) >= 1 and self.ShaderName in nodes_:

            # Set the material and shading group

            arn_mat = mc.shadingNode(self.ShaderName, asShader=True, name=(instance.Name + "_Mat"))
            if not shader == None:
                arn_sg = shader
            else:
                arn_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=arn_mat, destination=arn_sg)

            maps_ = [item[1] for item in instance.tex_nodes]
            used_maps = []

            #print(maps_)

#start BLOOM EDIT
            if "normal" in maps_:
                if instance.Type == "3dplant":
                    arn_normal = mc.shadingNode('bump2d', asUtility=True, name=(instance.ID + "_bump2d"))
                    mc.setAttr(arn_normal+".bumpInterp",1)
                    mc.setAttr(arn_normal+".aiFlipR",0)
                    mc.setAttr(arn_normal+".aiFlipG",0)
                    normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                    mc.connectAttr((normal_+".outAlpha"), (arn_normal+".bumpValue"))
                    mc.connectAttr((arn_normal+".outNormal"), (arn_mat+".normalCamera"))
                    used_maps.append(arn_normal)
                    mc.setAttr(normal_+'.colorSpace', "Raw", type="string") #BLOOM EDIT
#END BLOOM EDIT

            if "albedo" in maps_:
                albedo_ = [item[0] for item in instance.tex_nodes if item[1] == "albedo"][0]

                #BLOOM EDIT DELETE AO
                mc.connectAttr((albedo_+".outColor"), (arn_mat+".baseColor"))
                mc.setAttr((arn_mat+".base"),1) #BLOOM EDIT


                used_maps.append(albedo_)

                mc.setAttr(albedo_+'.colorSpace', "sRGB", type="string") #BLOOM EDIT

            # Create the specular setup
            if "specular" in maps_:
                specular_ = [item[0] for item in instance.tex_nodes if item[1] == "specular"][0]
                mc.connectAttr((specular_+".outColor"), (arn_mat+".specularColor"))
                mc.setAttr(arn_mat + ".specular",1) #BLOOM EDIT
                mc.setAttr(specular_ +'.colorSpace', "Raw", type="string") #BLOOM EDIT


            if "roughness" in maps_:
                arn_rough_range = mc.shadingNode('remapValue', asUtility=True, name=(instance.ID + "_Rough_Range"))
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outColor.outColorR"), (arn_rough_range+".inputValue"))
                mc.connectAttr((arn_rough_range+".outValue"), (arn_mat+".specularRoughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)

                mc.setAttr(roughness_ +'.colorSpace', "Raw", type="string") #BLOOM EDIT


                used_maps.append(roughness_)
            elif "gloss" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".output"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)

                used_maps.append(gloss_)

                mc.setAttr(gloss_ +'.colorSpace', "Raw", type="string") #BLOOM EDIT

            if "displacement" in maps_:
                #START EDIT BLOOM
                if instance.Type != "3dplant":
                    arn_disp_shr = mc.shadingNode('displacementShader', asTexture=True, name=(instance.ID + "_Displacement_shr"))

                    subNode = mc.shadingNode('aiSubtract', asTexture=True, name=(instance.ID + "_aiDispMid"))
                    mc.setAttr(subNode+'.input2',0.75, 0.75, 0.75, typ='double3' ) #MEGASCAN MID DISPLACE OFTEN AT 0,75... Why ? Idk.
                    displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                    mc.setAttr(displacement_ +'.colorSpace', "Raw", type="string") #BLOOM EDIT
                    mc.connectAttr((displacement_+".outColorR"), (subNode+".input1.input1R"))
                    mc.connectAttr((subNode+".outColor.outColorR"), (arn_disp_shr+".displacement"))
                    mc.connectAttr((arn_disp_shr+".displacement"), (arn_sg+".displacementShader"))
                    mc.setAttr(displacement_+".alphaIsLuminance", 1)
                    mc.setAttr(arn_disp_shr+".scale", 10)
                    mc.setAttr(arn_disp_shr+".aiDisplacementZeroValue", 0)

                    used_maps.append(displacement_)
                #END EDIT BLOOM



            if "metalness" in maps_:
                metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
                mc.connectAttr((metalness_+".outAlpha"), (arn_mat+".metalness"))
                mc.setAttr(metalness_+".alphaIsLuminance", 1)

                used_maps.append(metalness_)

                mc.setAttr(metalness_ +'.colorSpace', "Raw", type="string") #BLOOM EDIT

            #START BLOOM EDIT
            if "translucency" in maps_:
                translucency_ = [item[0] for item in instance.tex_nodes if item[1] == "translucency"][0]
                addNode = mc.shadingNode('aiAdd', asTexture=True, name=(instance.ID + "_aiAdd"))
                mc.connectAttr((translucency_+".outColor"), (addNode+".input1"))
                mc.connectAttr((albedo_+".outColor"), (addNode+".input2"))
                mc.connectAttr((addNode+".outColor"), (arn_mat+".subsurfaceColor"), f=True)
                mc.setAttr(arn_mat+".subsurface", 1)
                mc.setAttr(arn_mat+".thinWalled", 1)
                mc.setAttr(arn_mat+".subsurface", 0.35)
                mc.setAttr(translucency_ +'.colorSpace', "sRGB", type="string") #BLOOM EDIT

                used_maps.append(translucency_)
                #END BLOOM EDIT
            elif "transmission" in maps_:
                transmission_ = [item[0] for item in instance.tex_nodes if item[1] == "transmission"][0]
                mc.connectAttr((transmission_+".outColor.outColorR"), (arn_mat+".transmission"))

                used_maps.append(transmission_)


            if "opacity" in maps_:
                opacity_ = [item[0] for item in instance.tex_nodes if item[1] == "opacity"][0]
                mc.connectAttr((opacity_+".outColor"), (arn_mat+".opacity"))
                mc.setAttr(opacity_+".alphaIsLuminance", 1)
                mc.setAttr(arn_mat+".thinWalled", 1)

                used_maps.append(opacity_)

                mc.setAttr(opacity_ +'.colorSpace', "Raw", type="string") #BLOOM EDIT

            if len(instance.mesh_transforms) >= 1:
                for mesh_ in instance.mesh_transforms:

                    if "displacement" in maps_:
                        mc.setAttr(mesh_+".aiSubdivType", 1)
                        mc.setAttr(mesh_+".aiSubdivIterations", 3)
                        if instance.Type in ["3dplant", "3d"]:
                            mc.setAttr(mesh_+".aiDispHeight", 1)
                            #mc.setAttr(mesh_+".aiDispZeroValue", 0.5) BLOOM EDIT
                            #mc.setAttr(mesh_+".aiDispZeroValue", 0.5) BLOOM EDIT
                        #else: BLOOM EDIT
                            #mc.setAttr(mesh_+".aiDispHeight", 10) BLOOM EDIT
                            #mc.setAttr(mesh_+".aiDispZeroValue", 5) BLOOM EDIT
                            #mc.setAttr(mesh_+".aiDispZeroValue", 0.5) BLOOM EDIT

                    if "opacity" in maps_:
                        mc.setAttr(mesh_+".aiOpaque", 0)

                    if "normal" not in maps_:
                        mc.setAttr(mesh_+".aiDispAutobump", 1)

                    mc.select(mesh_)
                    melc.eval('sets -e -forceElement '+arn_sg)

            #print(used_maps)
        else:
            print("Please make sure you have the latest version of Arnold installed. Go to SolidAngle.com to get it.")

    def GlassSetup(self, shader):
        nodes_ = mc.allNodeTypes()
        #print(nodes_)

        if "standardSurface" in nodes_:
            self.ShaderName = "standardSurface"
        else:
            self.ShaderName = "aiStandardSurface"

        if len(instance.tex_nodes) >= 1 and self.ShaderName in nodes_:

            # Set the material and shading group

            arn_mat = mc.shadingNode(self.ShaderName, asShader=True, name=(instance.Name + "_Mat"))
            if not shader == None:
                arn_sg = shader
            else:
                arn_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=arn_mat, destination=arn_sg)

            maps_ = [item[1] for item in instance.tex_nodes]
            used_maps = []

            #print(maps_)


            if "normal" in maps_:
                arn_normal = mc.shadingNode('aiNormalMap', asShader=True, name=(instance.ID + "_Normal"))
                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                mc.connectAttr((arn_normal+".outValue"), (arn_mat+".normalCamera"))
                mc.connectAttr((normal_+".outColor"), (arn_normal+".input"))

                used_maps.append(arn_normal)

            if "roughness" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outColor"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)

                used_maps.append(roughness_)
            elif "gloss" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".output"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)

                used_maps.append(gloss_)

            mc.setAttr(arn_mat+".transmission", 0.85)

            #print(used_maps)
        else:
            print("Please make sure you have the latest version of Arnold installed. Go to SolidAngle.com to get it.")
