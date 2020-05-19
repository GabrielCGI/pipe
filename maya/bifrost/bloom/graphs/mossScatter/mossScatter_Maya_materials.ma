//Maya ASCII 2020 scene
//Name: mossScatter_Maya_materials.ma
//Last modified: Tue, May 19, 2020 04:26:41 PM
//Codeset: 1252
requires maya "2020";
requires "stereoCamera" "10.0";
requires -nodeType "aiStandardSurface" -nodeType "aiAdd" -nodeType "aiNormalMap"
		 "mtoa" "4.0.3";
requires -dataType "bifData" "bifrostGraph" "2.0.5.0";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t pal;
fileInfo "application" "maya";
fileInfo "product" "Maya 2020";
fileInfo "version" "2020";
fileInfo "cutIdentifier" "202002251615-329d215872";
fileInfo "osv" "Microsoft Windows 10 Technical Preview  (Build 18363)\n";
fileInfo "UUID" "6B6CAFC8-4356-32AF-E237-F5BAFA40C5E2";
createNode aiStandardSurface -n "mossScatter_materials:moss_materials:mossAlpha";
	rename -uid "154B4F2E-445D-274D-84C4-168D2455C9E2";
	setAttr ".base" 1;
	setAttr ".specular" 0.44999998807907104;
	setAttr ".specular_roughness" 0.30000001192092896;
	setAttr ".subsurface" 0.5;
	setAttr ".thin_walled" yes;
createNode gammaCorrect -n "mossScatter_materials:moss_materials:gammaCorrect1";
	rename -uid "2EAC6EED-4EE7-001F-030F-9C9957DB3B37";
	setAttr ".g" -type "float3" 1.1 1.1 1.1 ;
createNode file -n "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1";
	rename -uid "DF972307-4B6D-0286-F6DE-C4975681E2DC";
	setAttr ".co" -type "float3" 0.025569618 0.030120483 0.0058757579 ;
	setAttr ".ftn" -type "string" "B:/ressources/lib/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Albedo.jpg";
	setAttr ".exp" 0.25;
	setAttr ".cs" -type "string" "Utility - sRGB - Texture";
createNode place2dTexture -n "mossScatter_materials:moss_materials:place2dTexture2";
	rename -uid "02E8C1F5-4A0E-26AB-4043-B796CC4659ED";
createNode file -n "mossScatter_materials:moss_materials:file1";
	rename -uid "163E8E93-4145-FDD0-7465-E6A6A1A93EA1";
	setAttr ".ftn" -type "string" "B:/ressources/lib/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Opacity.jpg";
	setAttr ".cs" -type "string" "Utility - sRGB - Texture";
createNode place2dTexture -n "mossScatter_materials:moss_materials:place2dTexture1";
	rename -uid "9717A78F-45BE-CF96-4BF7-508990B12653";
createNode aiAdd -n "mossScatter_materials:moss_materials:aiAdd1";
	rename -uid "9184B084-4D15-A4AD-79C9-8A86C566C723";
createNode file -n "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2";
	rename -uid "E03AB898-4B6F-634D-9898-29BA16580F1C";
	setAttr ".co" -type "float3" 0.043136589 0.046979867 0.014975161 ;
	setAttr ".ftn" -type "string" "B:/ressources/lib/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Translucency.jpg";
	setAttr ".cs" -type "string" "Utility - sRGB - Texture";
createNode place2dTexture -n "mossScatter_materials:moss_materials:place2dTexture4";
	rename -uid "6437129A-4E25-66BC-0F2E-8B92133C16FC";
createNode aiNormalMap -n "mossScatter_materials:moss_materials:aiNormalMap1";
	rename -uid "92743ED8-4CDE-3085-46DF-6B9C2FD7BF0D";
	setAttr ".strength" 0.20000000298023224;
createNode file -n "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1";
	rename -uid "534B504C-4046-1110-B7EE-87B5DEFE4183";
	setAttr ".ftn" -type "string" "B:/ressources/lib/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Normal.jpg";
	setAttr ".cs" -type "string" "Utility - Raw";
createNode place2dTexture -n "mossScatter_materials:moss_materials:place2dTexture5";
	rename -uid "05CF15DF-4237-C229-5AF5-B3BDDD694661";
select -ne :time1;
	setAttr ".o" 1.0416666666666667;
	setAttr ".unw" 1.0416666666666667;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 6 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderUtilityList1;
	setAttr -s 7 ".u";
select -ne :defaultRenderingList1;
select -ne :defaultTextureList1;
	setAttr -s 4 ".tx";
select -ne :initialShadingGroup;
	setAttr -s 2 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "B:/ressources/pipeline/networkInstall/OpenColorIO-Configs/aces_1.2/config.ocio";
	setAttr ".vtn" -type "string" "sRGB (ACES)";
	setAttr ".wsn" -type "string" "ACES - ACEScg";
	setAttr ".otn" -type "string" "sRGB (ACES)";
	setAttr ".potn" -type "string" "sRGB (ACES)";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
connectAttr "mossScatter_materials:moss_materials:gammaCorrect1.o" "mossScatter_materials:moss_materials:mossAlpha.base_color"
		;
connectAttr "mossScatter_materials:moss_materials:file1.oc" "mossScatter_materials:moss_materials:mossAlpha.opacity"
		;
connectAttr "mossScatter_materials:moss_materials:aiAdd1.out" "mossScatter_materials:moss_materials:mossAlpha.subsurface_color"
		;
connectAttr "mossScatter_materials:moss_materials:aiNormalMap1.out" "mossScatter_materials:moss_materials:mossAlpha.n"
		;
connectAttr "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.oc" "mossScatter_materials:moss_materials:gammaCorrect1.v"
		;
connectAttr ":defaultColorMgtGlobals.cme" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.ws"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.c" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.c"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.tf" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.tf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.rf" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.rf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.mu" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.mu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.mv" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.mv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.s" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.s"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.wu" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.wu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.wv" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.wv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.re" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.re"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.of" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.of"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.r" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.ro"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.n" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.n"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.vt1" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.vt1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.vt2" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.vt2"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.vt3" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.vt3"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.vc1" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.vc1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.o" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.uv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.ofs" "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.fs"
		;
connectAttr ":defaultColorMgtGlobals.cme" "mossScatter_materials:moss_materials:file1.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "mossScatter_materials:moss_materials:file1.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "mossScatter_materials:moss_materials:file1.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "mossScatter_materials:moss_materials:file1.ws"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.c" "mossScatter_materials:moss_materials:file1.c"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.tf" "mossScatter_materials:moss_materials:file1.tf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.rf" "mossScatter_materials:moss_materials:file1.rf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.mu" "mossScatter_materials:moss_materials:file1.mu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.mv" "mossScatter_materials:moss_materials:file1.mv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.s" "mossScatter_materials:moss_materials:file1.s"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.wu" "mossScatter_materials:moss_materials:file1.wu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.wv" "mossScatter_materials:moss_materials:file1.wv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.re" "mossScatter_materials:moss_materials:file1.re"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.of" "mossScatter_materials:moss_materials:file1.of"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.r" "mossScatter_materials:moss_materials:file1.ro"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.n" "mossScatter_materials:moss_materials:file1.n"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.vt1" "mossScatter_materials:moss_materials:file1.vt1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.vt2" "mossScatter_materials:moss_materials:file1.vt2"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.vt3" "mossScatter_materials:moss_materials:file1.vt3"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.vc1" "mossScatter_materials:moss_materials:file1.vc1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.o" "mossScatter_materials:moss_materials:file1.uv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.ofs" "mossScatter_materials:moss_materials:file1.fs"
		;
connectAttr "mossScatter_materials:moss_materials:gammaCorrect1.o" "mossScatter_materials:moss_materials:aiAdd1.input1"
		;
connectAttr "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.oc" "mossScatter_materials:moss_materials:aiAdd1.input2"
		;
connectAttr ":defaultColorMgtGlobals.cme" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.ws"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.c" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.c"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.tf" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.tf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.rf" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.rf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.mu" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.mu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.mv" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.mv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.s" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.s"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.wu" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.wu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.wv" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.wv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.re" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.re"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.of" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.of"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.r" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.ro"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.n" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.n"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.vt1" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.vt1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.vt2" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.vt2"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.vt3" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.vt3"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.vc1" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.vc1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.o" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.uv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.ofs" "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.fs"
		;
connectAttr "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.oc" "mossScatter_materials:moss_materials:aiNormalMap1.input"
		;
connectAttr ":defaultColorMgtGlobals.cme" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.ws"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.c" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.c"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.tf" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.tf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.rf" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.rf"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.mu" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.mu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.mv" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.mv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.s" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.s"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.wu" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.wu"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.wv" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.wv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.re" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.re"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.of" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.of"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.r" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.ro"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.n" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.n"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.vt1" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.vt1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.vt2" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.vt2"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.vt3" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.vt3"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.vc1" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.vc1"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.o" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.uv"
		;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.ofs" "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.fs"
		;
connectAttr "mossScatter_materials:moss_materials:mossAlpha.msg" ":defaultShaderList1.s"
		 -na;
connectAttr "mossScatter_materials:moss_materials:place2dTexture1.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:place2dTexture2.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:place2dTexture4.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:aiAdd1.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:place2dTexture5.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:aiNormalMap1.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:gammaCorrect1.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "mossScatter_materials:moss_materials:file1.msg" ":defaultTextureList1.tx"
		 -na;
connectAttr "mossScatter_materials:moss_materials:shrjefmi_4K_Albedo_1.msg" ":defaultTextureList1.tx"
		 -na;
connectAttr "mossScatter_materials:moss_materials:shrjefmi_4K_Translucency_2.msg" ":defaultTextureList1.tx"
		 -na;
connectAttr "mossScatter_materials:moss_materials:shrjefmi_4K_Normal_1.msg" ":defaultTextureList1.tx"
		 -na;
connectAttr "mossScatter_materials:moss_materials:aiAdd1.out" ":internal_soloShader.ic"
		;
// End of mossScatter_Maya_materials.ma
