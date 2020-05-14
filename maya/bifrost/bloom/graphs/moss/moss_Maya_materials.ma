//Maya ASCII 2020 scene
//Name: moss_Maya_materials.ma
//Last modified: Wed, May 13, 2020 03:20:41 PM
//Codeset: 1252
requires maya "2020";
requires "stereoCamera" "10.0";
requires -nodeType "aiStandardSurface" -nodeType "aiAdd" -nodeType "aiNormalMap"
		 "mtoa" "4.0.3";
requires -dataType "bifData" "bifrostGraph" "2.0.5.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2020";
fileInfo "version" "2020";
fileInfo "cutIdentifier" "202002251615-329d215872";
fileInfo "osv" "Microsoft Windows 10 Technical Preview  (Build 18363)\n";
fileInfo "UUID" "CAE96621-4AC2-384F-785C-39A5AB5B1735";
createNode aiStandardSurface -n "moss_materials:mossAlpha";
	rename -uid "FBDE070E-42AE-B591-6CD8-A58E1A054A33";
	setAttr ".base" 1;
	setAttr ".specular" 0.44999998807907104;
	setAttr ".specular_roughness" 0.30000001192092896;
	setAttr ".subsurface" 0.5;
	setAttr ".thin_walled" yes;
createNode gammaCorrect -n "moss_materials:gammaCorrect1";
	rename -uid "BD6033D3-4B04-C964-EE32-42B04AF4AF0A";
	setAttr ".g" -type "float3" 1.1 1.1 1.1 ;
createNode file -n "moss_materials:shrjefmi_4K_Albedo_1";
	rename -uid "AB85CD24-4AC3-8C97-ACE4-93A9827B81CE";
	setAttr ".co" -type "float3" 0.025569618 0.030120483 0.0058757579 ;
	setAttr ".ftn" -type "string" "B:/prod/ressources/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Albedo.jpg";
	setAttr ".exp" 0.25;
	setAttr ".cs" -type "string" "Utility - sRGB - Texture";
createNode place2dTexture -n "moss_materials:place2dTexture2";
	rename -uid "6256E4FE-427B-769A-C1E2-03A67C16A111";
createNode file -n "moss_materials:file1";
	rename -uid "C2E92BB3-455A-CAA6-ED0C-92944EC0DDA9";
	setAttr ".ftn" -type "string" "B:/prod/ressources/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Opacity.jpg";
	setAttr ".cs" -type "string" "Utility - sRGB - Texture";
createNode place2dTexture -n "moss_materials:place2dTexture1";
	rename -uid "F33A0189-482B-FE7A-D5D5-6BA4F8BEA46B";
createNode aiAdd -n "moss_materials:aiAdd1";
	rename -uid "784A2E91-4E55-5B3A-D56F-C888D83F1777";
createNode file -n "moss_materials:shrjefmi_4K_Translucency_2";
	rename -uid "58C14813-479A-30A0-A99E-5396D29CA4CC";
	setAttr ".co" -type "float3" 0.043136589 0.046979867 0.014975161 ;
	setAttr ".ftn" -type "string" "B:/prod/ressources/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Translucency.jpg";
	setAttr ".cs" -type "string" "Utility - sRGB - Texture";
createNode place2dTexture -n "moss_materials:place2dTexture4";
	rename -uid "A95280ED-47F6-3704-5C8B-51BBA64F2C57";
createNode aiNormalMap -n "moss_materials:aiNormalMap1";
	rename -uid "5AF58BAC-46AE-E0C5-59FD-7685474264DE";
	setAttr ".strength" 0.20000000298023224;
createNode file -n "moss_materials:shrjefmi_4K_Normal_1";
	rename -uid "996400DB-4601-ACDC-F2AB-ED9ECCAFE1EE";
	setAttr ".ftn" -type "string" "B:/prod/ressources/megascan/Downloaded/atlas/moss_atlas_shrjefmi2/shrjefmi_4K_Normal.jpg";
	setAttr ".cs" -type "string" "Utility - Raw";
createNode place2dTexture -n "moss_materials:place2dTexture5";
	rename -uid "3062B6E6-41B1-D925-3CF9-DF9B3D40867A";
select -ne :time1;
	setAttr ".o" 1;
	setAttr ".unw" 1;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -s 5 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 9 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderUtilityList1;
	setAttr -s 7 ".u";
select -ne :defaultRenderingList1;
select -ne :defaultTextureList1;
	setAttr -s 4 ".tx";
select -ne :initialShadingGroup;
	setAttr -s 3 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr ".ren" -type "string" "arnold";
	setAttr ".dss" -type "string" "lambert1";
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
select -ne :ikSystem;
	setAttr -s 4 ".sol";
connectAttr "moss_materials:gammaCorrect1.o" "moss_materials:mossAlpha.base_color"
		;
connectAttr "moss_materials:file1.oc" "moss_materials:mossAlpha.opacity";
connectAttr "moss_materials:aiAdd1.out" "moss_materials:mossAlpha.subsurface_color"
		;
connectAttr "moss_materials:aiNormalMap1.out" "moss_materials:mossAlpha.n";
connectAttr "moss_materials:shrjefmi_4K_Albedo_1.oc" "moss_materials:gammaCorrect1.v"
		;
connectAttr ":defaultColorMgtGlobals.cme" "moss_materials:shrjefmi_4K_Albedo_1.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "moss_materials:shrjefmi_4K_Albedo_1.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "moss_materials:shrjefmi_4K_Albedo_1.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "moss_materials:shrjefmi_4K_Albedo_1.ws"
		;
connectAttr "moss_materials:place2dTexture2.c" "moss_materials:shrjefmi_4K_Albedo_1.c"
		;
connectAttr "moss_materials:place2dTexture2.tf" "moss_materials:shrjefmi_4K_Albedo_1.tf"
		;
connectAttr "moss_materials:place2dTexture2.rf" "moss_materials:shrjefmi_4K_Albedo_1.rf"
		;
connectAttr "moss_materials:place2dTexture2.mu" "moss_materials:shrjefmi_4K_Albedo_1.mu"
		;
connectAttr "moss_materials:place2dTexture2.mv" "moss_materials:shrjefmi_4K_Albedo_1.mv"
		;
connectAttr "moss_materials:place2dTexture2.s" "moss_materials:shrjefmi_4K_Albedo_1.s"
		;
connectAttr "moss_materials:place2dTexture2.wu" "moss_materials:shrjefmi_4K_Albedo_1.wu"
		;
connectAttr "moss_materials:place2dTexture2.wv" "moss_materials:shrjefmi_4K_Albedo_1.wv"
		;
connectAttr "moss_materials:place2dTexture2.re" "moss_materials:shrjefmi_4K_Albedo_1.re"
		;
connectAttr "moss_materials:place2dTexture2.of" "moss_materials:shrjefmi_4K_Albedo_1.of"
		;
connectAttr "moss_materials:place2dTexture2.r" "moss_materials:shrjefmi_4K_Albedo_1.ro"
		;
connectAttr "moss_materials:place2dTexture2.n" "moss_materials:shrjefmi_4K_Albedo_1.n"
		;
connectAttr "moss_materials:place2dTexture2.vt1" "moss_materials:shrjefmi_4K_Albedo_1.vt1"
		;
connectAttr "moss_materials:place2dTexture2.vt2" "moss_materials:shrjefmi_4K_Albedo_1.vt2"
		;
connectAttr "moss_materials:place2dTexture2.vt3" "moss_materials:shrjefmi_4K_Albedo_1.vt3"
		;
connectAttr "moss_materials:place2dTexture2.vc1" "moss_materials:shrjefmi_4K_Albedo_1.vc1"
		;
connectAttr "moss_materials:place2dTexture2.o" "moss_materials:shrjefmi_4K_Albedo_1.uv"
		;
connectAttr "moss_materials:place2dTexture2.ofs" "moss_materials:shrjefmi_4K_Albedo_1.fs"
		;
connectAttr ":defaultColorMgtGlobals.cme" "moss_materials:file1.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "moss_materials:file1.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "moss_materials:file1.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "moss_materials:file1.ws";
connectAttr "moss_materials:place2dTexture1.c" "moss_materials:file1.c";
connectAttr "moss_materials:place2dTexture1.tf" "moss_materials:file1.tf";
connectAttr "moss_materials:place2dTexture1.rf" "moss_materials:file1.rf";
connectAttr "moss_materials:place2dTexture1.mu" "moss_materials:file1.mu";
connectAttr "moss_materials:place2dTexture1.mv" "moss_materials:file1.mv";
connectAttr "moss_materials:place2dTexture1.s" "moss_materials:file1.s";
connectAttr "moss_materials:place2dTexture1.wu" "moss_materials:file1.wu";
connectAttr "moss_materials:place2dTexture1.wv" "moss_materials:file1.wv";
connectAttr "moss_materials:place2dTexture1.re" "moss_materials:file1.re";
connectAttr "moss_materials:place2dTexture1.of" "moss_materials:file1.of";
connectAttr "moss_materials:place2dTexture1.r" "moss_materials:file1.ro";
connectAttr "moss_materials:place2dTexture1.n" "moss_materials:file1.n";
connectAttr "moss_materials:place2dTexture1.vt1" "moss_materials:file1.vt1";
connectAttr "moss_materials:place2dTexture1.vt2" "moss_materials:file1.vt2";
connectAttr "moss_materials:place2dTexture1.vt3" "moss_materials:file1.vt3";
connectAttr "moss_materials:place2dTexture1.vc1" "moss_materials:file1.vc1";
connectAttr "moss_materials:place2dTexture1.o" "moss_materials:file1.uv";
connectAttr "moss_materials:place2dTexture1.ofs" "moss_materials:file1.fs";
connectAttr "moss_materials:gammaCorrect1.o" "moss_materials:aiAdd1.input1";
connectAttr "moss_materials:shrjefmi_4K_Translucency_2.oc" "moss_materials:aiAdd1.input2"
		;
connectAttr ":defaultColorMgtGlobals.cme" "moss_materials:shrjefmi_4K_Translucency_2.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "moss_materials:shrjefmi_4K_Translucency_2.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "moss_materials:shrjefmi_4K_Translucency_2.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "moss_materials:shrjefmi_4K_Translucency_2.ws"
		;
connectAttr "moss_materials:place2dTexture4.c" "moss_materials:shrjefmi_4K_Translucency_2.c"
		;
connectAttr "moss_materials:place2dTexture4.tf" "moss_materials:shrjefmi_4K_Translucency_2.tf"
		;
connectAttr "moss_materials:place2dTexture4.rf" "moss_materials:shrjefmi_4K_Translucency_2.rf"
		;
connectAttr "moss_materials:place2dTexture4.mu" "moss_materials:shrjefmi_4K_Translucency_2.mu"
		;
connectAttr "moss_materials:place2dTexture4.mv" "moss_materials:shrjefmi_4K_Translucency_2.mv"
		;
connectAttr "moss_materials:place2dTexture4.s" "moss_materials:shrjefmi_4K_Translucency_2.s"
		;
connectAttr "moss_materials:place2dTexture4.wu" "moss_materials:shrjefmi_4K_Translucency_2.wu"
		;
connectAttr "moss_materials:place2dTexture4.wv" "moss_materials:shrjefmi_4K_Translucency_2.wv"
		;
connectAttr "moss_materials:place2dTexture4.re" "moss_materials:shrjefmi_4K_Translucency_2.re"
		;
connectAttr "moss_materials:place2dTexture4.of" "moss_materials:shrjefmi_4K_Translucency_2.of"
		;
connectAttr "moss_materials:place2dTexture4.r" "moss_materials:shrjefmi_4K_Translucency_2.ro"
		;
connectAttr "moss_materials:place2dTexture4.n" "moss_materials:shrjefmi_4K_Translucency_2.n"
		;
connectAttr "moss_materials:place2dTexture4.vt1" "moss_materials:shrjefmi_4K_Translucency_2.vt1"
		;
connectAttr "moss_materials:place2dTexture4.vt2" "moss_materials:shrjefmi_4K_Translucency_2.vt2"
		;
connectAttr "moss_materials:place2dTexture4.vt3" "moss_materials:shrjefmi_4K_Translucency_2.vt3"
		;
connectAttr "moss_materials:place2dTexture4.vc1" "moss_materials:shrjefmi_4K_Translucency_2.vc1"
		;
connectAttr "moss_materials:place2dTexture4.o" "moss_materials:shrjefmi_4K_Translucency_2.uv"
		;
connectAttr "moss_materials:place2dTexture4.ofs" "moss_materials:shrjefmi_4K_Translucency_2.fs"
		;
connectAttr "moss_materials:shrjefmi_4K_Normal_1.oc" "moss_materials:aiNormalMap1.input"
		;
connectAttr ":defaultColorMgtGlobals.cme" "moss_materials:shrjefmi_4K_Normal_1.cme"
		;
connectAttr ":defaultColorMgtGlobals.cfe" "moss_materials:shrjefmi_4K_Normal_1.cmcf"
		;
connectAttr ":defaultColorMgtGlobals.cfp" "moss_materials:shrjefmi_4K_Normal_1.cmcp"
		;
connectAttr ":defaultColorMgtGlobals.wsn" "moss_materials:shrjefmi_4K_Normal_1.ws"
		;
connectAttr "moss_materials:place2dTexture5.c" "moss_materials:shrjefmi_4K_Normal_1.c"
		;
connectAttr "moss_materials:place2dTexture5.tf" "moss_materials:shrjefmi_4K_Normal_1.tf"
		;
connectAttr "moss_materials:place2dTexture5.rf" "moss_materials:shrjefmi_4K_Normal_1.rf"
		;
connectAttr "moss_materials:place2dTexture5.mu" "moss_materials:shrjefmi_4K_Normal_1.mu"
		;
connectAttr "moss_materials:place2dTexture5.mv" "moss_materials:shrjefmi_4K_Normal_1.mv"
		;
connectAttr "moss_materials:place2dTexture5.s" "moss_materials:shrjefmi_4K_Normal_1.s"
		;
connectAttr "moss_materials:place2dTexture5.wu" "moss_materials:shrjefmi_4K_Normal_1.wu"
		;
connectAttr "moss_materials:place2dTexture5.wv" "moss_materials:shrjefmi_4K_Normal_1.wv"
		;
connectAttr "moss_materials:place2dTexture5.re" "moss_materials:shrjefmi_4K_Normal_1.re"
		;
connectAttr "moss_materials:place2dTexture5.of" "moss_materials:shrjefmi_4K_Normal_1.of"
		;
connectAttr "moss_materials:place2dTexture5.r" "moss_materials:shrjefmi_4K_Normal_1.ro"
		;
connectAttr "moss_materials:place2dTexture5.n" "moss_materials:shrjefmi_4K_Normal_1.n"
		;
connectAttr "moss_materials:place2dTexture5.vt1" "moss_materials:shrjefmi_4K_Normal_1.vt1"
		;
connectAttr "moss_materials:place2dTexture5.vt2" "moss_materials:shrjefmi_4K_Normal_1.vt2"
		;
connectAttr "moss_materials:place2dTexture5.vt3" "moss_materials:shrjefmi_4K_Normal_1.vt3"
		;
connectAttr "moss_materials:place2dTexture5.vc1" "moss_materials:shrjefmi_4K_Normal_1.vc1"
		;
connectAttr "moss_materials:place2dTexture5.o" "moss_materials:shrjefmi_4K_Normal_1.uv"
		;
connectAttr "moss_materials:place2dTexture5.ofs" "moss_materials:shrjefmi_4K_Normal_1.fs"
		;
connectAttr "moss_materials:mossAlpha.msg" ":defaultShaderList1.s" -na;
connectAttr "moss_materials:place2dTexture1.msg" ":defaultRenderUtilityList1.u" 
		-na;
connectAttr "moss_materials:place2dTexture2.msg" ":defaultRenderUtilityList1.u" 
		-na;
connectAttr "moss_materials:place2dTexture4.msg" ":defaultRenderUtilityList1.u" 
		-na;
connectAttr "moss_materials:aiAdd1.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "moss_materials:place2dTexture5.msg" ":defaultRenderUtilityList1.u" 
		-na;
connectAttr "moss_materials:aiNormalMap1.msg" ":defaultRenderUtilityList1.u" -na
		;
connectAttr "moss_materials:gammaCorrect1.msg" ":defaultRenderUtilityList1.u" -na
		;
connectAttr "moss_materials:file1.msg" ":defaultTextureList1.tx" -na;
connectAttr "moss_materials:shrjefmi_4K_Albedo_1.msg" ":defaultTextureList1.tx" 
		-na;
connectAttr "moss_materials:shrjefmi_4K_Translucency_2.msg" ":defaultTextureList1.tx"
		 -na;
connectAttr "moss_materials:shrjefmi_4K_Normal_1.msg" ":defaultTextureList1.tx" 
		-na;
connectAttr "moss_materials:aiAdd1.out" ":internal_soloShader.ic";
// End of moss_Maya_materials.ma
