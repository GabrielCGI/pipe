//Maya ASCII 2025ff03 scene
//Name: camRig_Rigging_v002.ma
//Last modified: Mon, Feb 02, 2026 03:35:39 PM
//Codeset: 1252
requires maya "2025ff03";
requires -dataType "czLayerData" "bluePencil" "2.6.1";
requires "stereoCamera" "10.0";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
fileInfo "cutIdentifier" "202407121012-8ed02f4c99";
fileInfo "osv" "Windows 11 Pro v2009 (Build: 26100)";
fileInfo "UUID" "E53DB9B4-44F1-276D-4266-8687E784AB04";
createNode transform -s -n "persp";
	rename -uid "D69D1E29-4447-E742-6AE5-12A2F0BEC84B";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -22.412364808569386 11.547232876092961 -33.701272580405231 ;
	setAttr ".r" -type "double3" -15.938352728214277 927.40000000000111 0 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "731D47FA-490F-E719-7C74-F389B65D2DB3";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 43.273196173719505;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 0 0 -3.2232712805271149 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -n "camRig";
	rename -uid "C4F8C5C1-4BB6-30C2-0640-DDB3F8793BAB";
createNode transform -n "camera" -p "camRig";
	rename -uid "110EE883-4EF4-1DEB-F4AD-A6B00B5F4517";
createNode transform -n "shotCam" -p "camera";
	rename -uid "8426B794-4C75-80A6-EAB2-C783BD0DCE20";
	setAttr ".v" no;
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode camera -n "shotCamShape" -p "shotCam";
	rename -uid "5E879FCE-4D33-8131-FED2-19B264B2A751";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr ".pn" -type "double2" 0.0045686668328022498 0.0024458751220569437 ;
	setAttr ".zom" 1.054041242591802;
	setAttr ".ncp" 1;
	setAttr ".fd" 0;
	setAttr ".coi" 5.6847313948938538;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
	setAttr ".dgo" 1;
	setAttr ".dr" yes;
	setAttr ".dgc" -type "float3" 0 0 0 ;
createNode transform -n "rig" -p "camRig";
	rename -uid "2423D268-42A2-9121-9692-91A225E4260D";
createNode transform -n "controls" -p "rig";
	rename -uid "25136D6D-4352-CBA4-9B43-7E9BA5EA35D1";
createNode transform -n "ctrl_general_OFFSET" -p "controls";
	rename -uid "72BE1566-4BF2-F580-859A-D0BFD0720866";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_general_HOOK" -p "ctrl_general_OFFSET";
	rename -uid "252544F6-46FF-5DE2-2210-B082473C432D";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_general_MOVE" -p "ctrl_general_HOOK";
	rename -uid "250F9F53-420E-9F7F-B37E-C1A4798C9BCF";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_general" -p "ctrl_general_MOVE";
	rename -uid "9BB2EE05-4761-C7BF-A7EE-BFBA4CAD77FF";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "offset" -ln "offset" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "globalScale" -ln "globalScale" -dv 0.1 -min 0.1 -at "double";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.34099999 0.34099999 0.34099999 ;
	setAttr -k on ".ro";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -cb on ".offset";
	setAttr -k on ".globalScale" 1;
createNode nurbsCurve -n "ctrl_generalShape" -p "ctrl_general";
	rename -uid "203AFDD4-4671-0177-BA5A-9E96B84CD92C";
	setAttr -k off ".v";
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1.4142135623730949 2.8284271247461898 4.2426406871192848 5.6568542494923797
		
		5
		2.941220293933007e-16 12 0
		-12 5.882440587866013e-16 0
		-8.8236608817990175e-16 -12 0
		12 -1.1764881175732026e-15 0
		1.4706101469665027e-15 12 0
		;
createNode transform -n "ctrl_options_OFFSET" -p "ctrl_general";
	rename -uid "D692D955-4D46-9A65-A421-1D93DAA71DF0";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_options" -p "ctrl_options_OFFSET";
	rename -uid "0B834D4A-41E0-821A-05B1-9C8F72313814";
	addAttr -ci true -sn "gridOverlay" -ln "gridOverlay" -min 0 -max 3 -en "Off:illogic Square" 
		-at "enum";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "horizontalCam" -ln "horizontalCam" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "aim" -ln "aim" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_02" -ln "divider_02" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "focal" -ln "focal" -dv 12 -min 12 -max 200 -at "double";
	addAttr -ci true -sn "dof" -ln "dof" -nn "Depth of Field" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "fStop" -ln "fStop" -nn "F-Stop" -dv 5.6 -at "double";
	addAttr -ci true -sn "focusDistance" -ln "focusDistance" -at "double";
	addAttr -ci true -sn "distanceTool" -ln "distanceTool" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_03" -ln "divider_03" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "nearClip" -ln "nearClip" -dv 1 -at "double";
	addAttr -ci true -sn "farClip" -ln "farClip" -dv 10000 -at "double";
	addAttr -ci true -sn "overscan" -ln "overscan" -dv 1 -min 0.1 -max 10 -at "double";
	addAttr -ci true -sn "resolutionGate" -ln "resolutionGate" -min 0 -max 3 -en "Fill:Horizontal:Vertical:Overscan" 
		-at "enum";
	addAttr -ci true -sn "divider_04" -ln "divider_04" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "references" -ln "references" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".gridOverlay" 1;
	setAttr -cb on ".divider_01";
	setAttr -k on ".horizontalCam";
	setAttr -k on ".aim";
	setAttr -cb on ".divider_02";
	setAttr -k on ".focal" 35;
	setAttr -cb on ".dof";
	setAttr -k on ".fStop";
	setAttr -k on ".focusDistance";
	setAttr -k on ".distanceTool";
	setAttr -cb on ".divider_03";
	setAttr -cb on ".nearClip";
	setAttr -cb on ".farClip";
	setAttr -cb on ".overscan";
	setAttr -cb on ".resolutionGate" 1;
	setAttr -cb on ".divider_04";
	setAttr -cb on ".references";
createNode nurbsCurve -n "ctrl_optionsShape" -p "ctrl_options";
	rename -uid "72F42D0B-4188-7E9D-CC1A-4EBA27CF3763";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		3 18 2 no 3
		23 -2 -1 0 1 2 3 4 5 6 7 7.5567421640000001 8 8.4590626259999997 9 10 11 12
		 13 14 15 16 17 18
		21
		0.39264623741499377 13.797672661742837 0
		2.4323770812907161e-16 13.875774854369769 0
		-0.39264623741499449 13.797672661742837 0
		-0.7255156445305615 13.575256434691356 0
		-0.94793187158204562 13.242387027575788 0
		-1.0260340642089776 12.849740790160793 0
		-0.94793187158204517 12.457094552745799 0
		-0.7255156445305615 12.124225145630231 0
		-0.71253451640486998 12.137174571402022 0
		-0.018181420919877844 12.822321563306859 0
		0.0022154744739801557 12.84513912412341 0
		0.016319559569948072 12.822321476728632 0
		0.71253451640486998 12.137174398117759 0
		0.72551564453056139 12.124225145630231 0
		0.94793187158204584 12.457094552745795 0
		1.0260340642089771 12.849740790160793 0
		0.9479318715820455 13.24238702757579 0
		0.72551564453056117 13.575256434691354 0
		0.39264623741499377 13.797672661742837 0
		2.4323770812907161e-16 13.875774854369769 0
		-0.39264623741499449 13.797672661742837 0
		;
createNode transform -n "ctrl_general_offset_OFFSET" -p "ctrl_general";
	rename -uid "FECED97C-4F08-3E47-163D-12858E4A35C7";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_general_offset_HOOK" -p "ctrl_general_offset_OFFSET";
	rename -uid "FEB966CA-4812-21C4-959D-1A95176F04AC";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_general_offset_MOVE" -p "ctrl_general_offset_HOOK";
	rename -uid "562F04CB-49CF-6755-606E-218F6CC21FBF";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_general_offset" -p "ctrl_general_offset_MOVE";
	rename -uid "478FA5AE-463F-730D-57DC-BF8FACDB03ED";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.34099999 0.34099999 0.34099999 ;
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_general_offsetShape" -p "ctrl_general_offset";
	rename -uid "C3C5442C-4EB7-AB60-CF33-27AFF12204F6";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1.4142135623730949 2.8284271247461898 4.2426406871192848 5.6568542494923797
		
		5
		2.7836629653969734e-16 11.357175677615032 0
		-11.357175677615034 5.5673259307939457e-16 0
		-8.3509888961909181e-16 -11.357175677615032 0
		11.357175677615034 -1.1134651861587891e-15 0
		1.3918314826984862e-15 11.357175677615032 0
		;
createNode transform -n "ctrl_root_OFFSET" -p "ctrl_general_offset";
	rename -uid "7A441B43-4511-6B67-43AC-3E9081E3D917";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_root_HOOK" -p "ctrl_root_OFFSET";
	rename -uid "A0E52121-4E9F-50FF-3862-2B84366AE13B";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_root_MOVE" -p "ctrl_root_HOOK";
	rename -uid "406C55F1-48E0-560D-2DE2-BB9E5CF09B1A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_root" -p "ctrl_root_MOVE";
	rename -uid "75E5A005-46A9-7817-C460-E2B5DBDE5F90";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "offset" -ln "offset" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -cb on ".offset";
createNode nurbsCurve -n "ctrl_rootShape" -p "ctrl_root";
	rename -uid "4E1641E5-4DE6-3408-913B-AB8844CEE708";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 28 0 no 3
		29 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28
		29
		-2.4990128677423287 4.9980257354846573 -8.3233848738062228e-16
		-2.499012867742322 6.4930220888628476 0
		-3.4986180148392583 6.4930220888628476 0
		0 9.9960514709693147 -1.6646769747612446e-15
		3.4986180148392583 6.4930220888628476 0
		2.4990128677423287 6.4930220888628476 0
		2.4990128677423287 4.9980257354846573 -8.3233848738062228e-16
		4.9980257354846573 2.4990128677423287 -4.1616924369031114e-16
		6.4930220888628476 2.4990128677423287 1.3872308123010372e-16
		6.4930220888628476 3.4986180148392583 2.7744616246020744e-16
		9.9960514709693147 0 0
		6.4930220888628476 -3.4986180148392583 -1.3872308123010372e-16
		6.4930220888628476 -2.4990128677423287 4.1616924369031114e-16
		4.9980257354846573 -2.4990128677423287 4.1616924369031114e-16
		2.4990128677423287 -4.9980257354846573 8.3233848738062228e-16
		2.4990128677423287 -6.4930220888628476 0
		3.4986180148392583 -6.4930220888628476 0
		0 -9.9960514709693147 1.6646769747612446e-15
		-3.4986180148392583 -6.4930220888628476 0
		-2.4990128677423287 -6.4930220888628476 0
		-2.4990128677423287 -4.9980257354846573 8.3233848738062228e-16
		-4.9980257354846573 -2.4990128677423287 4.1616924369031114e-16
		-6.4930220888628476 -2.4990128677423287 4.1616924369031114e-16
		-6.4930220888628476 -3.4986180148392583 -1.3872308123010372e-16
		-9.9960514709693147 0 0
		-6.4930220888628476 3.4986180148392583 2.7744616246020744e-16
		-6.4930220888628476 2.4990128677423287 1.3872308123010372e-16
		-4.9980257354846573 2.4990128677423287 -4.1616924369031114e-16
		-2.4990128677423287 4.9980257354846573 -8.3233848738062228e-16
		;
createNode transform -n "ctrl_root_offset_OFFSET" -p "ctrl_root";
	rename -uid "ECF0868B-45E4-8020-4AC9-4394D9B0EE82";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_root_offset_HOOK" -p "ctrl_root_offset_OFFSET";
	rename -uid "477804ED-4593-72E8-60D0-A7AC37AA6A7A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_root_offset_MOVE" -p "ctrl_root_offset_HOOK";
	rename -uid "D7F208A9-4766-AE88-63D3-7181C598AAE1";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_root_offset" -p "ctrl_root_offset_MOVE";
	rename -uid "752A433C-447A-F6BA-D94F-8E919DB2FB5C";
	setAttr -l on -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_root_offsetShape" -p "ctrl_root_offset";
	rename -uid "D583BE5E-404A-AEB0-E576-ED85E3AB15AE";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 20 0 no 3
		21 0 1 3 5 6 7 8 10 12 13 14 15 17 19 20 21 22 24 26 27 28
		21
		-2.0000000000000031 4.6092903938339118 -8.3233848738062228e-16
		-2 7 0
		0 9 0
		2 7 0
		2 4.6092903938339118 -8.3233848738062228e-16
		4.6092903938339118 2 -4.1616924369031114e-16
		7 2 0
		9 0 0
		7 -2 0
		4.6092903938339118 -2 4.1616924369031114e-16
		2 -4.6092903938339118 8.3233848738062228e-16
		2 -7 0
		0 -9 0
		-2 -7 0
		-2 -4.6092903938339118 8.3233848738062228e-16
		-4.6092903938339118 -2 4.1616924369031114e-16
		-7 -2 0
		-9 0 0
		-7 2 0
		-4.6092903938339118 2 -4.1616924369031114e-16
		-2.0000000000000031 4.6092903938339118 -8.3233848738062228e-16
		;
createNode transform -n "ctrl_shake_OFFSET" -p "ctrl_root_offset";
	rename -uid "FE55394A-47F2-0F89-97C5-8CA18DEE8B84";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_shake_HOOK" -p "ctrl_shake_OFFSET";
	rename -uid "3B6117BF-430A-92D0-0BDA-588D762E501B";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_shake_MOVE" -p "ctrl_shake_HOOK";
	rename -uid "E41CB83D-4A86-2B5E-2616-79AF1603719F";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_shake" -p "ctrl_shake_MOVE";
	rename -uid "D9E6C2CC-4276-422C-EB4C-E09EFE9A5EED";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "offset" -ln "offset" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -cb on ".offset";
createNode nurbsCurve -n "ctrl_shakeShape" -p "ctrl_shake";
	rename -uid "5DCEA206-44E7-017C-388E-8BA22A53BD40";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.40700001 0.28300002 0.83099997 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 8 0 no 3
		9 0 0.21505724700000001 0.89947866030000001 1.1476368939999999 1.7879380090000001
		 2.205490202 2.780111019 3.201068383 4
		9
		-1 4 0
		1 4 0
		4 1 0
		4 -1 0
		1 -4 0
		-1 -4 0
		-4 -1 0
		-4 1 0
		-1 4 0
		;
createNode transform -n "ctrl_shake_offset_OFFSET" -p "ctrl_shake";
	rename -uid "9D980949-4AD8-B920-0D71-E69249391CA7";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_shake_offset_HOOK" -p "ctrl_shake_offset_OFFSET";
	rename -uid "A752408F-4FDF-BA66-B05A-779D60324443";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_shake_offset_MOVE" -p "ctrl_shake_offset_HOOK";
	rename -uid "E41B4C09-41C8-18E3-F678-3198A28D6C91";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_shake_offset" -p "ctrl_shake_offset_MOVE";
	rename -uid "C26AB910-4503-52F9-1E71-6694924C3A77";
	setAttr -l on -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_shake_offsetShape" -p "ctrl_shake_offset";
	rename -uid "78F4FBBD-4E3D-8B35-25F2-189F2AC9DA43";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.40700001 0.28300002 0.83099997 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 8 0 no 3
		9 0 0.21505724700000001 0.89947866030000001 1.1476368939999999 1.7879380090000001
		 2.205490202 2.780111019 3.201068383 4
		9
		-0.86607825950195227 3.4643130380078091 0
		0.86607825950195227 3.4643130380078091 0
		3.4643130380078091 0.86607825950195227 0
		3.4643130380078091 -0.86607825950195227 0
		0.86607825950195227 -3.4643130380078091 0
		-0.86607825950195227 -3.4643130380078091 0
		-3.4643130380078091 -0.86607825950195227 0
		-3.4643130380078091 0.86607825950195227 0
		-0.86607825950195227 3.4643130380078091 0
		;
createNode aimConstraint -n "ctrl_shake_MOVE_aimConstraint1" -p "ctrl_shake_MOVE";
	rename -uid "DFC25C9D-4CB6-0809-019D-FD8DC55408D6";
	addAttr -dcb 0 -ci true -sn "w0" -ln "ctrl_aim_offsetW0" -dv 1 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr ".a" -type "double3" 0 0 -1 ;
	setAttr -k on ".w0";
createNode transform -n "ctrl_cam_OFFSET" -p "controls";
	rename -uid "E9B82DDA-4F48-65FD-C142-FAA1DE7F8EE8";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_cam_HOOK" -p "ctrl_cam_OFFSET";
	rename -uid "9ECD45B3-4E86-A8D2-4495-E4AFABF726E8";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_cam_MOVE" -p "ctrl_cam_HOOK";
	rename -uid "974E0858-48CB-2314-DDE3-8F8C1B34A4DA";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_cam" -p "ctrl_cam_MOVE";
	rename -uid "1F24D826-455C-B083-F917-2581FA5E1EBB";
	setAttr -l on -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_camShape" -p "ctrl_cam";
	rename -uid "A99A0AD9-439B-09F1-4714-9A925791FB51";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.56099999 0.56099999 0.56099999 ;
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		1 24 0 no 3
		25 0 0.26105238444010315 0.52210476888020629 0.78315715332030944 1.0442095377604126
		 1.3052619222005157 1.5663143066406189 1.827366691080722 2.0884190755208252 2.3494714599609283
		 2.6105238444010315 2.8715762288411346 3.1326286132812378 3.3936809977213409 3.6547333821614441
		 3.9157857666015472 4.1768381510416503 4.4378905354817535 4.6989429199218566 4.9599953043619598
		 5.2210476888020629 5.4821000732421661 5.7431524576822692 6.0042048421223724 6.2652572265624755
		
		25
		5.7888721284916658e-09 -0.58581626829108824 -1.2724111209116984e-09
		-0.41423465834823286 -0.41423466413710519 -1.2724111209116984e-09
		-0.58864351602701848 -0.58864351602701837 -0.45045112981318769
		-0.41423465004915477 -0.41423465583802666 -1.2724111209116984e-09
		-0.58581623500416924 -8.0566573359098291e-17 -1.2724111209116984e-09
		-0.83246758801433962 -4.1799512731071242e-17 -0.45045112981318769
		-0.58581623500416924 -8.0566573359098291e-17 -1.2724111209116984e-09
		-0.41423465834823286 0.41423466413710519 -1.2724111209116984e-09
		-0.58864351602701848 0.58864351602701837 -0.45045112981318769
		-0.41423465004915477 0.41423465583802616 -1.2724111209116984e-09
		5.7888717984731961e-09 0.58581624079303951 -1.2724111209116984e-09
		-4.1799512731071242e-17 0.83246758801433907 -0.45045112981318769
		5.7888717803355224e-09 0.58581626829108824 -1.2724111209116984e-09
		0.41423466992597779 0.41423466413710519 -1.2724111209116984e-09
		0.58864351602701848 0.58864351602701837 -0.45045112981318769
		0.41423466162689931 0.41423465583802715 -1.2724111209116984e-09
		0.58581624658191112 3.9006956945587429e-16 -1.2724111209116984e-09
		0.83246758801433962 4.1799512731071242e-17 -0.45045112981318769
		0.58581627407996195 4.0436587093938223e-16 -1.2724111209116984e-09
		0.41423466992597779 -0.41423466413710519 -1.2724111209116984e-09
		0.58864351602701848 -0.58864351602701837 -0.45045112981318769
		0.41423466162690004 -0.41423465583802616 -1.2724111209116984e-09
		5.7888721514502912e-09 -0.58581624079303951 -1.2724111209116984e-09
		4.1799512731071242e-17 -0.83246758801433907 -0.45045112981318769
		5.7888726488010403e-09 -0.58581626829108846 -1.2724111209116984e-09
		;
createNode nurbsCurve -n "ctrl_camShape1" -p "ctrl_cam";
	rename -uid "70E48904-489F-F5D4-241B-648BC699B62B";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.56099999 0.56099999 0.56099999 ;
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		1 8 0 no 3
		9 0 0.76536686473017967 1.5307337294603593 2.296100594190539 3.0614674589207187
		 3.8268343236508984 4.592201188381078 5.3575680531112582 6.1229349178414374
		9
		5.0973940745485997e-17 -0.83246762709013034 -0.45045110460369975
		-0.58864350423370559 -0.58864350423370526 -0.45045110460369975
		-0.83246762709013045 -5.0973940745485972e-17 -0.45045110460369975
		-0.58864350423370559 0.58864350423370526 -0.45045110460370008
		-5.0973940745485997e-17 0.83246762709013034 -0.45045110460370008
		0.58864350423370559 0.58864350423370526 -0.45045110460370008
		0.83246762709013045 5.0973940745485972e-17 -0.45045110460369975
		0.58864350423370559 -0.58864350423370526 -0.45045110460369975
		5.0973940745485997e-17 -0.83246762709013034 -0.45045110460369975
		;
createNode nurbsCurve -n "curveShape1" -p "ctrl_cam";
	rename -uid "12EF9F10-451D-74A6-14C3-508CEF915499";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.56099999 0.56099999 0.56099999 ;
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		1 12 0 no 3
		13 0 1 2 3 4 5 6 7 8 9 10 11 12
		13
		1.0199641277312597 -1.0199641009433902 -1.2724113429563033e-09
		1.0199641074721815 -1.0199641342600505 1.5178382284772234
		1.0199641277312597 -1.0199641009433902 -1.2724113429563033e-09
		-1.0199641277312597 -1.0199641009433902 -1.2724113429563033e-09
		-1.0199641074721815 -1.0199641342600505 1.5178409985757957
		-1.0199641277312597 -1.0199641009433902 -1.2724113429563033e-09
		-1.0199641277312597 1.0199641009433902 -1.2724106768224885e-09
		-1.0199641074721815 1.0199641342600505 1.5178401959324175
		-1.0199641277312597 1.0199641009433902 -1.2724106768224885e-09
		1.0199641277312597 1.0199641009433902 -1.2724106768224885e-09
		1.0199641074721815 1.0199641342600505 1.5178366694646501
		1.0199641277312597 1.0199641009433902 -1.2724106768224885e-09
		1.0199641277312597 -1.0199641009433902 -1.2724113429563033e-09
		;
createNode transform -n "ctrl_distanceTool_OFFSET" -p "ctrl_cam";
	rename -uid "9735BE50-4A16-58BE-3E19-5893995F1A88";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_distanceTool_MOVE" -p "ctrl_distanceTool_OFFSET";
	rename -uid "152C9ECF-4696-EC9A-0A88-498E1A9CF631";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_distanceTool" -p "ctrl_distanceTool_MOVE";
	rename -uid "BAA9D486-4253-CE1F-98B6-B79DA543A755";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "distance" -ln "distance" -at "double";
	setAttr -k off ".v";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -cb on ".distance";
createNode nurbsCurve -n "ctrl_distanceToolShape" -p "ctrl_distanceTool";
	rename -uid "91EAB756-45B3-2E25-5393-42999B92B9EE";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.052999973 0.352 1 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-0.66746712145181009 0 0
		0.66746712145181009 0 0
		;
createNode nurbsCurve -n "ctrl_distanceToolShape1" -p "ctrl_distanceTool";
	rename -uid "C847E819-44AE-9A8E-60D1-28B11EA6CE45";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.052999973 0.352 1 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 0.66746712145181009 0
		0 -0.66746712145181009 0
		;
createNode nurbsCurve -n "ctrl_distanceToolShape2" -p "ctrl_distanceTool";
	rename -uid "889AC325-4572-7B11-63C2-4CBBD6595365";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.052999973 0.352 1 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 0 -0.66746712145181009
		0 0 0.66746712145181009
		;
createNode transform -n "filmGate_OFFSET" -p "ctrl_cam";
	rename -uid "4FD7C373-4F92-C05B-333E-41A0132899BA";
	setAttr ".t" -type "double3" 0 0 -1 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "filmGate_MOVE" -p "filmGate_OFFSET";
	rename -uid "47868D8D-48E2-D4CD-280B-589EC8BBBF19";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "imagePlane_squareIllogic" -p "filmGate_MOVE";
	rename -uid "360AF5B8-4952-313A-745D-528807B5F401";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".t" -type "double3" 0 1.865174681370263e-14 0 ;
	setAttr ".s" -type "double3" 0.23400943216761111 0.23400943216761111 0.23400943216761111 ;
createNode imagePlane -n "imagePlane_squareIllogicShape" -p "imagePlane_squareIllogic";
	rename -uid "D7A8059F-4E6D-73B6-A092-BB893E4BE7F5";
	setAttr -k off ".v";
	setAttr ".fc" 153;
	setAttr ".imn" -type "string" "R:/pipeline/pipe/assetsDefault/assets/Cameras/camRig/Libraries/imagePlanes/square_noCross.png";
	setAttr ".cov" -type "short2" 1280 1280 ;
	setAttr ".ag" 0.5;
	setAttr ".dlc" no;
	setAttr ".w" 12.8;
	setAttr ".h" 12.8;
	setAttr ".cs" -type "string" "sRGB - Texture";
createNode transform -n "reference_OFFSET" -p "ctrl_cam";
	rename -uid "EA3BD273-41BC-B733-39B0-27ADD567CBA0";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "reference_MOVE" -p "reference_OFFSET";
	rename -uid "3EDE7EDE-4F1E-B344-C77D-6FA85B3CCE6C";
	setAttr ".t" -type "double3" 0 0 -50 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "imagePlane_ref_01" -p "reference_MOVE";
	rename -uid "BEDBA9C0-429F-9015-FFAD-179E1DCAE6AE";
createNode imagePlane -n "imagePlane_ref_01Shape" -p "imagePlane_ref_01";
	rename -uid "3610D6B9-431E-3136-4521-1E9892759279";
	setAttr -k off ".v";
	setAttr ".fc" 153;
	setAttr ".dlc" no;
	setAttr ".w" 10;
	setAttr ".h" 10;
	setAttr ".cs" -type "string" "sRGB - Texture";
createNode aimConstraint -n "ctrl_cam_MOVE_aimCon" -p "ctrl_cam_MOVE";
	rename -uid "24F9A3F1-4FC2-FADB-3CFB-EB91500CABA3";
	addAttr -dcb 0 -ci true -sn "w0" -ln "ctrl_horizontalCam_aimW0" -dv 1 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr ".a" -type "double3" 0 0 -1 ;
	setAttr ".wut" 0;
	setAttr -k on ".w0";
createNode parentConstraint -n "ctrl_cam_HOOK_pCon" -p "ctrl_cam_HOOK";
	rename -uid "DD630F57-4805-3F9A-FCAD-ECB8F9BDBF55";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_shake_offsetW0" -dv 1 -min 0 
		-at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr -k on ".w0";
createNode transform -n "ctrl_horizontalCam_aim_OFFSET" -p "controls";
	rename -uid "2289F437-4D06-FF5E-B5FF-D78B032BCADB";
	setAttr ".t" -type "double3" 0 0 -3 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_horizontalCam_aim_HOOK" -p "ctrl_horizontalCam_aim_OFFSET";
	rename -uid "556046C4-49FA-DBBA-4FFE-F0B9AA68D415";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_horizontalCam_aim_MOVE" -p "ctrl_horizontalCam_aim_HOOK";
	rename -uid "50783C4D-4965-6CC2-4E7B-319555E525FA";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_horizontalCam_aim" -p "ctrl_horizontalCam_aim_MOVE";
	rename -uid "D30DE172-46FD-7100-8E42-9583D78909F2";
	setAttr ".v" no;
createNode nurbsCurve -n "ctrl_horizontalCam_aimShape" -p "ctrl_horizontalCam_aim";
	rename -uid "DD1FA8AC-49FD-F9A8-35E1-FC9D372D1E43";
	setAttr -k off ".v";
	setAttr ".tw" yes;
	setAttr -s 5 ".cp[0:4]" -type "double3" 0 1 0 0 0 0 0 0 0 0 0 0 0 
		1 0;
createNode parentConstraint -n "ctrl_horizontalCam_aim_HOOK_pCon" -p "ctrl_horizontalCam_aim_HOOK";
	rename -uid "382E63EF-40BE-7F66-0086-06B0B8C904A9";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_shake_offsetW0" -dv 1 -min 0 
		-at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr ".tg[0].tot" -type "double3" 0 0 -3 ;
	setAttr -k on ".w0";
createNode transform -n "ctrl_aim_OFFSET" -p "controls";
	rename -uid "756B8204-44BE-F3A3-A8CF-F6A746B25B00";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_aim_HOOK" -p "ctrl_aim_OFFSET";
	rename -uid "2DA5FE98-4A9F-6A01-1131-05BD8F197F99";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_aim_MOVE" -p "ctrl_aim_HOOK";
	rename -uid "76EF657A-4393-1EA4-786B-4ABFD55B17A8";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_aim" -p "ctrl_aim_MOVE";
	rename -uid "FD80A6F1-424A-5290-DEB5-BE806D1BED32";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "offset" -ln "offset" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "parent" -ln "parent" -min 0 -max 2 -en "World:General:Root" 
		-at "enum";
	addAttr -ci true -sn "divider_02" -ln "divider_02" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "upVector" -ln "upVector" -min 0 -max 4 -en "Scene Up:Object Up:Object Rotation Up:Vector:None" 
		-at "enum";
	addAttr -ci true -sn "vectorX" -ln "vectorX" -min -1 -max 1 -at "double";
	addAttr -ci true -sn "vectorY" -ln "vectorY" -dv 1 -min -1 -max 1 -at "double";
	addAttr -ci true -sn "vectorZ" -ln "vectorZ" -min -1 -max 1 -at "double";
	setAttr -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -cb on ".offset";
	setAttr -k on ".parent";
	setAttr -cb on ".divider_02";
	setAttr -k on ".upVector";
	setAttr -k on ".vectorX";
	setAttr -k on ".vectorY";
	setAttr -k on ".vectorZ";
createNode nurbsCurve -n "ctrl_aimShape" -p "ctrl_aim";
	rename -uid "1150ED83-4AC9-A5B4-42FE-EAAEC87D6415";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		4.7982373409884725e-17 0.7836116248912246 -0.78361162489122449
		4.1550626846842558e-33 1.1081941875543877 -6.7857323231109122e-17
		-4.7982373409884725e-17 0.78361162489122438 0.78361162489122449
		-6.7857323231109146e-17 5.7448982375248304e-17 1.1081941875543881
		-4.7982373409884725e-17 -0.78361162489122449 0.78361162489122449
		-6.7973144778085889e-33 -1.1081941875543884 1.1100856969603225e-16
		4.7982373409884725e-17 -0.78361162489122438 -0.78361162489122449
		6.7857323231109146e-17 -1.511240500779959e-16 -1.1081941875543881
		4.7982373409884725e-17 0.7836116248912246 -0.78361162489122449
		4.1550626846842558e-33 1.1081941875543877 -6.7857323231109122e-17
		-4.7982373409884725e-17 0.78361162489122438 0.78361162489122449
		;
createNode nurbsCurve -n "ctrl_aimShape1" -p "ctrl_aim";
	rename -uid "C2DBFA84-4248-0E0C-2AFD-5781EA73B711";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.78361162489122449 4.7982373409884731e-17 -0.7836116248912246
		6.7857323231109122e-17 6.7857323231109122e-17 -1.1081941875543877
		-0.78361162489122449 4.7982373409884719e-17 -0.78361162489122438
		-1.1081941875543881 3.5177356190060272e-33 -5.7448982375248304e-17
		-0.78361162489122449 -4.7982373409884725e-17 0.78361162489122449
		-1.1100856969603225e-16 -6.7857323231109171e-17 1.1081941875543884
		0.78361162489122449 -4.7982373409884719e-17 0.78361162489122438
		1.1081941875543881 -9.2536792101100989e-33 1.511240500779959e-16
		0.78361162489122449 4.7982373409884731e-17 -0.7836116248912246
		6.7857323231109122e-17 6.7857323231109122e-17 -1.1081941875543877
		-0.78361162489122449 4.7982373409884719e-17 -0.78361162489122438
		;
createNode nurbsCurve -n "ctrl_aimShape2" -p "ctrl_aim";
	rename -uid "04591344-4095-1E15-1C50-45AF1207818B";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.78361162489122449 0.7836116248912246 0
		6.7857323231109122e-17 1.1081941875543877 0
		-0.78361162489122449 0.78361162489122438 0
		-1.1081941875543881 5.7448982375248304e-17 0
		-0.78361162489122449 -0.78361162489122449 0
		-1.1100856969603225e-16 -1.1081941875543884 0
		0.78361162489122449 -0.78361162489122438 0
		1.1081941875543881 -1.511240500779959e-16 0
		0.78361162489122449 0.7836116248912246 0
		6.7857323231109122e-17 1.1081941875543877 0
		-0.78361162489122449 0.78361162489122438 0
		;
createNode transform -n "ctrl_aim_offset_OFFSET" -p "ctrl_aim";
	rename -uid "F3348E10-4212-23A1-49FF-DF9196004D1A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_aim_offset_HOOK" -p "ctrl_aim_offset_OFFSET";
	rename -uid "99245000-4CA6-8039-E6E1-21A26BAF9356";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_aim_offset_MOVE" -p "ctrl_aim_offset_HOOK";
	rename -uid "ECDB8018-415F-DD9B-263F-10BC94B3BF5A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_aim_offset" -p "ctrl_aim_offset_MOVE";
	rename -uid "C1DC1B9A-43A1-3C94-5462-B2A74FAD6302";
	setAttr -l on -k off ".v";
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_aim_offsetShape" -p "ctrl_aim_offset";
	rename -uid "FFD13E67-40F1-9724-84EB-A1AC2451CCA6";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1.4142135623730949 2.8284271247461898 4.2426406871192848 5.6568542494923797
		
		5
		4.7354291337076179e-17 4.7354291337076179e-17 -0.77335426622673686
		-0.77335426622673686 5.7992281311841558e-33 -9.4708582674152359e-17
		-1.4206287401122854e-16 -4.7354291337076179e-17 0.77335426622673686
		0.77335426622673686 -1.1598456262368312e-32 1.8941716534830472e-16
		2.367714566853809e-16 4.7354291337076179e-17 -0.77335426622673686
		;
createNode nurbsCurve -n "ctrl_aim_offsetShape1" -p "ctrl_aim_offset";
	rename -uid "EC48CA72-4880-0F26-46B8-13911AFF2853";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1.4142135623730949 2.8284271247461898 4.2426406871192848 5.6568542494923797
		
		5
		2.8996140655920779e-33 0.77335426622673686 -4.7354291337076179e-17
		-4.7354291337076179e-17 9.4708582674152359e-17 0.77335426622673686
		-8.6988421967762351e-33 -0.77335426622673686 1.4206287401122854e-16
		4.7354291337076179e-17 -1.8941716534830472e-16 -0.77335426622673686
		1.4498070327960396e-32 0.77335426622673686 -2.367714566853809e-16
		;
createNode nurbsCurve -n "ctrl_aim_offsetShape2" -p "ctrl_aim_offset";
	rename -uid "3201ACFA-4D4E-188B-470E-0B83268F28F3";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1.4142135623730949 2.8284271247461898 4.2426406871192848 5.6568542494923797
		
		5
		4.7354291337076179e-17 0.77335426622673686 0
		-0.77335426622673686 9.4708582674152359e-17 0
		-1.4206287401122854e-16 -0.77335426622673686 0
		0.77335426622673686 -1.8941716534830472e-16 0
		2.367714566853809e-16 0.77335426622673686 0
		;
createNode parentConstraint -n "ctrl_aim_MOVE_pCon" -p "ctrl_aim_MOVE";
	rename -uid "A74362FD-41E8-DE07-6547-32B52DA0C31F";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_general_offsetW0" -dv 1 -min 
		0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_root_offsetW1" -dv 1 -min 0 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr -s 2 ".tg";
	setAttr -k on ".w0";
	setAttr -k on ".w1";
createNode transform -n "ctrl_aim_objectUp_OFFSET" -p "controls";
	rename -uid "0A9C6B3D-4241-DE44-83AA-6DB98C68D9FC";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_aim_objectUp_HOOK" -p "ctrl_aim_objectUp_OFFSET";
	rename -uid "55FE637B-4EDF-0E18-C2B1-F2B46813E475";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_aim_objectUp_MOVE" -p "ctrl_aim_objectUp_HOOK";
	rename -uid "F04C256E-4ACE-42C5-66BB-75BEB7498A2A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_aim_objectUp" -p "ctrl_aim_objectUp_MOVE";
	rename -uid "E5FB9A0D-4ECA-D48D-1E1A-BFB65D074248";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "parent" -ln "parent" -min 0 -max 3 -en "World:General:Root:Aim" 
		-at "enum";
	setAttr -k off ".v";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -k on ".parent" 3;
createNode nurbsCurve -n "ctrl_aim_objectUpShape" -p "ctrl_aim_objectUp";
	rename -uid "2F9EA0E0-430B-9960-657C-E09E5A014295";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 0.19499999 0.024999976 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		-0.41858149318748733 0 0
		0 1.8128984338233904 0
		0.41858149318748733 0 0
		0 -0.41858149318748733 0
		-0.41858149318748733 0 0
		;
createNode nurbsCurve -n "ctrl_aim_objectUpShape1" -p "ctrl_aim_objectUp";
	rename -uid "AAA436AF-415B-33D7-C008-B883F238420C";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 0.19499999 0.024999976 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		-0.41858149318748733 0 0
		0 0 0.41858149318748733
		0.41858149318748733 0 0
		0 0 -0.41858149318748733
		-0.41858149318748733 0 0
		;
createNode nurbsCurve -n "ctrl_aim_objectUpShape2" -p "ctrl_aim_objectUp";
	rename -uid "0E310D04-4284-39DE-2C90-04B02CFFD27B";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 0.19499999 0.024999976 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		0 0 0.41858149318748761
		0 1.8128984338233904 0
		0 0 -0.41858149318748761
		0 -0.41858149318748733 0
		0 0 0.41858149318748761
		;
createNode parentConstraint -n "ctrl_aim_objectUp_HOOK_pCon" -p "ctrl_aim_objectUp_HOOK";
	rename -uid "26C523B9-43AB-D320-09BE-C4B170B3C5D3";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_general_offsetW0" -dv 1 -min 
		0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_root_offsetW1" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w2" -ln "ctrl_aim_offsetW2" -dv 1 -min 0 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr -s 3 ".tg";
	setAttr -k on ".w0";
	setAttr -k on ".w1";
	setAttr -k on ".w2";
createNode transform -n "constraints" -p "rig";
	rename -uid "E638C72B-4F82-F5D5-CCE0-DCAA2A0788D6";
createNode parentConstraint -n "camera_pConstraint" -p "constraints";
	rename -uid "08481EF2-4AE2-ACE4-4F3F-D79CEBF74EAF";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_camW0" -dv 1 -min 0 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr -k on ".w0";
createNode distanceBetween -n "distanceBetween1";
	rename -uid "9CEF433F-43BE-F9CF-F5A5-5CADB06D4FE1";
createNode remapValue -n "remapValue_viewGrid_tZ";
	rename -uid "5BD93F34-43B7-6939-9438-02BC49603B25";
	setAttr ".imn" 12;
	setAttr ".imx" 200;
	setAttr ".omx" -15.659999847412109;
	setAttr -s 2 ".vl[0:1]"  0 0 1 1 1 1;
	setAttr -s 2 ".cl";
	setAttr ".cl[0].clp" 0;
	setAttr ".cl[0].clc" -type "float3" 0 0 0 ;
	setAttr ".cl[0].cli" 1;
	setAttr ".cl[1].clp" 1;
	setAttr ".cl[1].clc" -type "float3" 1 1 1 ;
	setAttr ".cl[1].cli" 1;
createNode condition -n "cond_filmGate_illogicSquare_vis";
	rename -uid "80530E91-4AB7-291C-188D-23A2D397754A";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_horizontal_bool";
	rename -uid "A8208DC7-4E5A-2E71-6BA9-8E9C9DEEAC3A";
	setAttr ".op" 3;
createNode condition -n "cond_aim_bool";
	rename -uid "E3C8E7F4-4D81-B5A8-F6F9-AEBC9431380A";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode makeNurbCircle -n "makeNurbCircle1";
	rename -uid "1F00EF79-4342-92D6-4B5D-D98260970811";
	setAttr ".nr" -type "double3" 0 0 0 ;
	setAttr ".d" 1;
	setAttr ".s" 4;
createNode condition -n "cond_aimParent_ctrl_general_offset";
	rename -uid "B4A8790A-44BA-11C0-58ED-8BBDA67DF603";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimParent_ctrl_root_offset";
	rename -uid "6DE48D25-471A-2804-5639-048E0F6A18E8";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode plusMinusAverage -n "PMA_aim_objectUp_vis_logicGate";
	rename -uid "AFF2724F-4912-94B4-F17A-FFB20C5DBE44";
	setAttr -s 2 ".i1";
	setAttr -s 2 ".i1";
createNode condition -n "cond_aim_objectUp_visibility";
	rename -uid "572038B2-4FF4-22CB-A149-A2B279617AA7";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aim_objectUpRotation_visibility";
	rename -uid "B487572B-496E-00C0-C920-40A2F1F046A0";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimObjectUp_parentSpace_general";
	rename -uid "6990E93C-43C0-3E70-D930-60BCC45A5F26";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimObjectUp_parentSpace_root";
	rename -uid "35039BB3-4BDF-E839-56EB-939C0186F61D";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimObjectUp_parentSpace_aim";
	rename -uid "08025056-4557-A968-F791-EFAEAE859165";
	setAttr ".st" 3;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
select -ne :time1;
	setAttr ".o" 125;
	setAttr ".unw" 125;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
	setAttr ".rtfm" 1;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 5 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderUtilityList1;
	setAttr -s 14 ".u";
select -ne :defaultRenderingList1;
select -ne :standardSurface1;
	setAttr ".bc" -type "float3" 0.40000001 0.40000001 0.40000001 ;
	setAttr ".sr" 0.5;
select -ne :initialShadingGroup;
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr ".dss" -type "string" "standardSurface1";
select -ne :defaultResolution;
	setAttr ".w" 1024;
	setAttr ".h" 1024;
	setAttr ".pa" 1;
	setAttr ".dar" 1;
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "R:/pipeline/networkInstall/OpenColorIO-Configs/PRISM/illogic_V01-cg-config-v1.0.0_aces-v1.3_ocio-v2.1.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 - SDR Video (sRGB - Display)";
	setAttr ".vn" -type "string" "ACES 1.0 - SDR Video";
	setAttr ".dn" -type "string" "sRGB - Display";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 - SDR Video (sRGB - Display)";
	setAttr ".potn" -type "string" "ACES 1.0 - SDR Video (sRGB - Display)";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
connectAttr "camera_pConstraint.ctx" "camera.tx";
connectAttr "camera_pConstraint.cty" "camera.ty";
connectAttr "camera_pConstraint.ctz" "camera.tz";
connectAttr "camera_pConstraint.crx" "camera.rx";
connectAttr "camera_pConstraint.cry" "camera.ry";
connectAttr "camera_pConstraint.crz" "camera.rz";
connectAttr "ctrl_options.focal" "shotCamShape.fl";
connectAttr "ctrl_options.focusDistance" "shotCamShape.fd";
connectAttr "ctrl_options.farClip" "shotCamShape.fcp";
connectAttr "ctrl_options.nearClip" "shotCamShape.ncp";
connectAttr "ctrl_options.fStop" "shotCamShape.fs";
connectAttr "ctrl_options.overscan" "shotCamShape.ovr";
connectAttr "ctrl_options.dof" "shotCamShape.dof";
connectAttr "ctrl_options.resolutionGate" "shotCamShape.ff";
connectAttr "ctrl_general.globalScale" "ctrl_general.sx" -l on;
connectAttr "ctrl_general.globalScale" "ctrl_general.sy" -l on;
connectAttr "ctrl_general.globalScale" "ctrl_general.sz" -l on;
connectAttr "ctrl_general.offset" "ctrl_general_offsetShape.lodv";
connectAttr "ctrl_root.offset" "ctrl_root_offsetShape.lodv";
connectAttr "ctrl_shake_MOVE_aimConstraint1.crx" "ctrl_shake_MOVE.rx";
connectAttr "ctrl_shake_MOVE_aimConstraint1.cry" "ctrl_shake_MOVE.ry";
connectAttr "ctrl_shake_MOVE_aimConstraint1.crz" "ctrl_shake_MOVE.rz";
connectAttr "ctrl_shake.offset" "ctrl_shake_offsetShape.lodv";
connectAttr "ctrl_options.aim" "ctrl_shake_MOVE_aimConstraint1.w0";
connectAttr "ctrl_shake_MOVE.pim" "ctrl_shake_MOVE_aimConstraint1.cpim";
connectAttr "ctrl_shake_MOVE.t" "ctrl_shake_MOVE_aimConstraint1.ct";
connectAttr "ctrl_shake_MOVE.rp" "ctrl_shake_MOVE_aimConstraint1.crp";
connectAttr "ctrl_shake_MOVE.rpt" "ctrl_shake_MOVE_aimConstraint1.crt";
connectAttr "ctrl_shake_MOVE.ro" "ctrl_shake_MOVE_aimConstraint1.cro";
connectAttr "ctrl_aim_offset.t" "ctrl_shake_MOVE_aimConstraint1.tg[0].tt";
connectAttr "ctrl_aim_offset.rp" "ctrl_shake_MOVE_aimConstraint1.tg[0].trp";
connectAttr "ctrl_aim_offset.rpt" "ctrl_shake_MOVE_aimConstraint1.tg[0].trt";
connectAttr "ctrl_aim_offset.pm" "ctrl_shake_MOVE_aimConstraint1.tg[0].tpm";
connectAttr "ctrl_shake_MOVE_aimConstraint1.w0" "ctrl_shake_MOVE_aimConstraint1.tg[0].tw"
		;
connectAttr "ctrl_aim.upVector" "ctrl_shake_MOVE_aimConstraint1.wut";
connectAttr "ctrl_aim.vectorX" "ctrl_shake_MOVE_aimConstraint1.wux";
connectAttr "ctrl_aim.vectorY" "ctrl_shake_MOVE_aimConstraint1.wuy";
connectAttr "ctrl_aim.vectorZ" "ctrl_shake_MOVE_aimConstraint1.wuz";
connectAttr "ctrl_aim_objectUp.wm" "ctrl_shake_MOVE_aimConstraint1.wum";
connectAttr "ctrl_cam_HOOK_pCon.ctx" "ctrl_cam_HOOK.tx";
connectAttr "ctrl_cam_HOOK_pCon.cty" "ctrl_cam_HOOK.ty";
connectAttr "ctrl_cam_HOOK_pCon.ctz" "ctrl_cam_HOOK.tz";
connectAttr "ctrl_cam_HOOK_pCon.crx" "ctrl_cam_HOOK.rx";
connectAttr "ctrl_cam_HOOK_pCon.cry" "ctrl_cam_HOOK.ry";
connectAttr "ctrl_cam_HOOK_pCon.crz" "ctrl_cam_HOOK.rz";
connectAttr "ctrl_cam_MOVE_aimCon.crx" "ctrl_cam_MOVE.rx";
connectAttr "ctrl_cam_MOVE_aimCon.cry" "ctrl_cam_MOVE.ry";
connectAttr "ctrl_cam_MOVE_aimCon.crz" "ctrl_cam_MOVE.rz";
connectAttr "ctrl_general.s" "ctrl_cam.s";
connectAttr "ctrl_options.distanceTool" "ctrl_distanceTool.v";
connectAttr "distanceBetween1.d" "ctrl_distanceTool.distance";
connectAttr "remapValue_viewGrid_tZ.ov" "filmGate_MOVE.tz";
connectAttr "cond_filmGate_illogicSquare_vis.ocr" "imagePlane_squareIllogic.v";
connectAttr ":defaultColorMgtGlobals.cme" "imagePlane_squareIllogicShape.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "imagePlane_squareIllogicShape.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "imagePlane_squareIllogicShape.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "imagePlane_squareIllogicShape.ws";
connectAttr "shotCamShape.msg" "imagePlane_squareIllogicShape.ltc";
connectAttr "ctrl_options.references" "reference_MOVE.v";
connectAttr ":defaultColorMgtGlobals.cme" "imagePlane_ref_01Shape.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "imagePlane_ref_01Shape.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "imagePlane_ref_01Shape.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "imagePlane_ref_01Shape.ws";
connectAttr ":perspShape.msg" "imagePlane_ref_01Shape.ltc";
connectAttr "cond_horizontal_bool.ocr" "ctrl_cam_MOVE_aimCon.w0";
connectAttr "ctrl_cam_MOVE.pim" "ctrl_cam_MOVE_aimCon.cpim";
connectAttr "ctrl_cam_MOVE.t" "ctrl_cam_MOVE_aimCon.ct";
connectAttr "ctrl_cam_MOVE.rp" "ctrl_cam_MOVE_aimCon.crp";
connectAttr "ctrl_cam_MOVE.rpt" "ctrl_cam_MOVE_aimCon.crt";
connectAttr "ctrl_cam_MOVE.ro" "ctrl_cam_MOVE_aimCon.cro";
connectAttr "ctrl_horizontalCam_aim.t" "ctrl_cam_MOVE_aimCon.tg[0].tt";
connectAttr "ctrl_horizontalCam_aim.rp" "ctrl_cam_MOVE_aimCon.tg[0].trp";
connectAttr "ctrl_horizontalCam_aim.rpt" "ctrl_cam_MOVE_aimCon.tg[0].trt";
connectAttr "ctrl_horizontalCam_aim.pm" "ctrl_cam_MOVE_aimCon.tg[0].tpm";
connectAttr "ctrl_cam_MOVE_aimCon.w0" "ctrl_cam_MOVE_aimCon.tg[0].tw";
connectAttr "ctrl_cam_HOOK.ro" "ctrl_cam_HOOK_pCon.cro";
connectAttr "ctrl_cam_HOOK.pim" "ctrl_cam_HOOK_pCon.cpim";
connectAttr "ctrl_cam_HOOK.rp" "ctrl_cam_HOOK_pCon.crp";
connectAttr "ctrl_cam_HOOK.rpt" "ctrl_cam_HOOK_pCon.crt";
connectAttr "ctrl_shake_offset.t" "ctrl_cam_HOOK_pCon.tg[0].tt";
connectAttr "ctrl_shake_offset.rp" "ctrl_cam_HOOK_pCon.tg[0].trp";
connectAttr "ctrl_shake_offset.rpt" "ctrl_cam_HOOK_pCon.tg[0].trt";
connectAttr "ctrl_shake_offset.r" "ctrl_cam_HOOK_pCon.tg[0].tr";
connectAttr "ctrl_shake_offset.ro" "ctrl_cam_HOOK_pCon.tg[0].tro";
connectAttr "ctrl_shake_offset.s" "ctrl_cam_HOOK_pCon.tg[0].ts";
connectAttr "ctrl_shake_offset.pm" "ctrl_cam_HOOK_pCon.tg[0].tpm";
connectAttr "ctrl_cam_HOOK_pCon.w0" "ctrl_cam_HOOK_pCon.tg[0].tw";
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.ctx" "ctrl_horizontalCam_aim_HOOK.tx"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.cty" "ctrl_horizontalCam_aim_HOOK.ty"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.ctz" "ctrl_horizontalCam_aim_HOOK.tz"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.crx" "ctrl_horizontalCam_aim_HOOK.rx"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.cry" "ctrl_horizontalCam_aim_HOOK.ry"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.crz" "ctrl_horizontalCam_aim_HOOK.rz"
		;
connectAttr "makeNurbCircle1.oc" "ctrl_horizontalCam_aimShape.cr";
connectAttr "ctrl_horizontalCam_aim_HOOK.ro" "ctrl_horizontalCam_aim_HOOK_pCon.cro"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK.pim" "ctrl_horizontalCam_aim_HOOK_pCon.cpim"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK.rp" "ctrl_horizontalCam_aim_HOOK_pCon.crp"
		;
connectAttr "ctrl_horizontalCam_aim_HOOK.rpt" "ctrl_horizontalCam_aim_HOOK_pCon.crt"
		;
connectAttr "ctrl_shake_offset.t" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].tt";
connectAttr "ctrl_shake_offset.rp" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].trp";
connectAttr "ctrl_shake_offset.rpt" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].trt"
		;
connectAttr "ctrl_shake_offset.r" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].tr";
connectAttr "ctrl_shake_offset.ro" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].tro";
connectAttr "ctrl_shake_offset.s" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].ts";
connectAttr "ctrl_shake_offset.pm" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].tpm";
connectAttr "ctrl_horizontalCam_aim_HOOK_pCon.w0" "ctrl_horizontalCam_aim_HOOK_pCon.tg[0].tw"
		;
connectAttr "ctrl_aim_MOVE_pCon.ctx" "ctrl_aim_MOVE.tx";
connectAttr "ctrl_aim_MOVE_pCon.cty" "ctrl_aim_MOVE.ty";
connectAttr "ctrl_aim_MOVE_pCon.ctz" "ctrl_aim_MOVE.tz";
connectAttr "ctrl_aim_MOVE_pCon.crx" "ctrl_aim_MOVE.rx";
connectAttr "ctrl_aim_MOVE_pCon.cry" "ctrl_aim_MOVE.ry";
connectAttr "ctrl_aim_MOVE_pCon.crz" "ctrl_aim_MOVE.rz";
connectAttr "ctrl_options.aim" "ctrl_aim.v";
connectAttr "ctrl_general.s" "ctrl_aim.s";
connectAttr "ctrl_aim.offset" "ctrl_aim_offset.lodv";
connectAttr "ctrl_aim_MOVE.ro" "ctrl_aim_MOVE_pCon.cro";
connectAttr "ctrl_aim_MOVE.pim" "ctrl_aim_MOVE_pCon.cpim";
connectAttr "ctrl_aim_MOVE.rp" "ctrl_aim_MOVE_pCon.crp";
connectAttr "ctrl_aim_MOVE.rpt" "ctrl_aim_MOVE_pCon.crt";
connectAttr "ctrl_general_offset.t" "ctrl_aim_MOVE_pCon.tg[0].tt";
connectAttr "ctrl_general_offset.rp" "ctrl_aim_MOVE_pCon.tg[0].trp";
connectAttr "ctrl_general_offset.rpt" "ctrl_aim_MOVE_pCon.tg[0].trt";
connectAttr "ctrl_general_offset.r" "ctrl_aim_MOVE_pCon.tg[0].tr";
connectAttr "ctrl_general_offset.ro" "ctrl_aim_MOVE_pCon.tg[0].tro";
connectAttr "ctrl_general_offset.s" "ctrl_aim_MOVE_pCon.tg[0].ts";
connectAttr "ctrl_general_offset.pm" "ctrl_aim_MOVE_pCon.tg[0].tpm";
connectAttr "ctrl_aim_MOVE_pCon.w0" "ctrl_aim_MOVE_pCon.tg[0].tw";
connectAttr "ctrl_root_offset.t" "ctrl_aim_MOVE_pCon.tg[1].tt";
connectAttr "ctrl_root_offset.rp" "ctrl_aim_MOVE_pCon.tg[1].trp";
connectAttr "ctrl_root_offset.rpt" "ctrl_aim_MOVE_pCon.tg[1].trt";
connectAttr "ctrl_root_offset.r" "ctrl_aim_MOVE_pCon.tg[1].tr";
connectAttr "ctrl_root_offset.ro" "ctrl_aim_MOVE_pCon.tg[1].tro";
connectAttr "ctrl_root_offset.s" "ctrl_aim_MOVE_pCon.tg[1].ts";
connectAttr "ctrl_root_offset.pm" "ctrl_aim_MOVE_pCon.tg[1].tpm";
connectAttr "ctrl_aim_MOVE_pCon.w1" "ctrl_aim_MOVE_pCon.tg[1].tw";
connectAttr "cond_aimParent_ctrl_general_offset.ocr" "ctrl_aim_MOVE_pCon.w0";
connectAttr "cond_aimParent_ctrl_root_offset.ocr" "ctrl_aim_MOVE_pCon.w1";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.ctx" "ctrl_aim_objectUp_HOOK.tx";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.cty" "ctrl_aim_objectUp_HOOK.ty";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.ctz" "ctrl_aim_objectUp_HOOK.tz";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.crx" "ctrl_aim_objectUp_HOOK.rx";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.cry" "ctrl_aim_objectUp_HOOK.ry";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.crz" "ctrl_aim_objectUp_HOOK.rz";
connectAttr "PMA_aim_objectUp_vis_logicGate.o1" "ctrl_aim_objectUp.v" -l on;
connectAttr "ctrl_aim_objectUp_HOOK.ro" "ctrl_aim_objectUp_HOOK_pCon.cro";
connectAttr "ctrl_aim_objectUp_HOOK.pim" "ctrl_aim_objectUp_HOOK_pCon.cpim";
connectAttr "ctrl_aim_objectUp_HOOK.rp" "ctrl_aim_objectUp_HOOK_pCon.crp";
connectAttr "ctrl_aim_objectUp_HOOK.rpt" "ctrl_aim_objectUp_HOOK_pCon.crt";
connectAttr "ctrl_general_offset.t" "ctrl_aim_objectUp_HOOK_pCon.tg[0].tt";
connectAttr "ctrl_general_offset.rp" "ctrl_aim_objectUp_HOOK_pCon.tg[0].trp";
connectAttr "ctrl_general_offset.rpt" "ctrl_aim_objectUp_HOOK_pCon.tg[0].trt";
connectAttr "ctrl_general_offset.r" "ctrl_aim_objectUp_HOOK_pCon.tg[0].tr";
connectAttr "ctrl_general_offset.ro" "ctrl_aim_objectUp_HOOK_pCon.tg[0].tro";
connectAttr "ctrl_general_offset.s" "ctrl_aim_objectUp_HOOK_pCon.tg[0].ts";
connectAttr "ctrl_general_offset.pm" "ctrl_aim_objectUp_HOOK_pCon.tg[0].tpm";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.w0" "ctrl_aim_objectUp_HOOK_pCon.tg[0].tw"
		;
connectAttr "ctrl_root_offset.t" "ctrl_aim_objectUp_HOOK_pCon.tg[1].tt";
connectAttr "ctrl_root_offset.rp" "ctrl_aim_objectUp_HOOK_pCon.tg[1].trp";
connectAttr "ctrl_root_offset.rpt" "ctrl_aim_objectUp_HOOK_pCon.tg[1].trt";
connectAttr "ctrl_root_offset.r" "ctrl_aim_objectUp_HOOK_pCon.tg[1].tr";
connectAttr "ctrl_root_offset.ro" "ctrl_aim_objectUp_HOOK_pCon.tg[1].tro";
connectAttr "ctrl_root_offset.s" "ctrl_aim_objectUp_HOOK_pCon.tg[1].ts";
connectAttr "ctrl_root_offset.pm" "ctrl_aim_objectUp_HOOK_pCon.tg[1].tpm";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.w1" "ctrl_aim_objectUp_HOOK_pCon.tg[1].tw"
		;
connectAttr "ctrl_aim_offset.t" "ctrl_aim_objectUp_HOOK_pCon.tg[2].tt";
connectAttr "ctrl_aim_offset.rp" "ctrl_aim_objectUp_HOOK_pCon.tg[2].trp";
connectAttr "ctrl_aim_offset.rpt" "ctrl_aim_objectUp_HOOK_pCon.tg[2].trt";
connectAttr "ctrl_aim_offset.r" "ctrl_aim_objectUp_HOOK_pCon.tg[2].tr";
connectAttr "ctrl_aim_offset.ro" "ctrl_aim_objectUp_HOOK_pCon.tg[2].tro";
connectAttr "ctrl_aim_offset.s" "ctrl_aim_objectUp_HOOK_pCon.tg[2].ts";
connectAttr "ctrl_aim_offset.pm" "ctrl_aim_objectUp_HOOK_pCon.tg[2].tpm";
connectAttr "ctrl_aim_objectUp_HOOK_pCon.w2" "ctrl_aim_objectUp_HOOK_pCon.tg[2].tw"
		;
connectAttr "cond_aimObjectUp_parentSpace_general.ocr" "ctrl_aim_objectUp_HOOK_pCon.w0"
		;
connectAttr "cond_aimObjectUp_parentSpace_root.ocr" "ctrl_aim_objectUp_HOOK_pCon.w1"
		;
connectAttr "cond_aimObjectUp_parentSpace_aim.ocr" "ctrl_aim_objectUp_HOOK_pCon.w2"
		;
connectAttr "camera.ro" "camera_pConstraint.cro";
connectAttr "camera.pim" "camera_pConstraint.cpim";
connectAttr "camera.rp" "camera_pConstraint.crp";
connectAttr "camera.rpt" "camera_pConstraint.crt";
connectAttr "ctrl_cam.t" "camera_pConstraint.tg[0].tt";
connectAttr "ctrl_cam.rp" "camera_pConstraint.tg[0].trp";
connectAttr "ctrl_cam.rpt" "camera_pConstraint.tg[0].trt";
connectAttr "ctrl_cam.r" "camera_pConstraint.tg[0].tr";
connectAttr "ctrl_cam.ro" "camera_pConstraint.tg[0].tro";
connectAttr "ctrl_cam.s" "camera_pConstraint.tg[0].ts";
connectAttr "ctrl_cam.pm" "camera_pConstraint.tg[0].tpm";
connectAttr "camera_pConstraint.w0" "camera_pConstraint.tg[0].tw";
connectAttr "ctrl_cam.t" "distanceBetween1.p1";
connectAttr "ctrl_distanceTool.t" "distanceBetween1.p2";
connectAttr "ctrl_options.focal" "remapValue_viewGrid_tZ.i";
connectAttr "ctrl_options.gridOverlay" "cond_filmGate_illogicSquare_vis.ft";
connectAttr "cond_aim_bool.ocr" "cond_horizontal_bool.ft";
connectAttr "ctrl_options.horizontalCam" "cond_horizontal_bool.st";
connectAttr "ctrl_options.aim" "cond_aim_bool.ft";
connectAttr "ctrl_aim.parent" "cond_aimParent_ctrl_general_offset.ft";
connectAttr "ctrl_aim.parent" "cond_aimParent_ctrl_root_offset.ft";
connectAttr "cond_aim_objectUp_visibility.ocr" "PMA_aim_objectUp_vis_logicGate.i1[0]"
		;
connectAttr "cond_aim_objectUpRotation_visibility.ocr" "PMA_aim_objectUp_vis_logicGate.i1[1]"
		;
connectAttr "ctrl_aim.upVector" "cond_aim_objectUp_visibility.ft";
connectAttr "ctrl_aim.upVector" "cond_aim_objectUpRotation_visibility.ft";
connectAttr "ctrl_aim_objectUp.parent" "cond_aimObjectUp_parentSpace_general.ft"
		;
connectAttr "ctrl_aim_objectUp.parent" "cond_aimObjectUp_parentSpace_root.ft";
connectAttr "ctrl_aim_objectUp.parent" "cond_aimObjectUp_parentSpace_aim.ft";
connectAttr "cond_aim_bool.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_horizontal_bool.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_aimParent_ctrl_general_offset.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_aimParent_ctrl_root_offset.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_aimObjectUp_parentSpace_general.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_aimObjectUp_parentSpace_root.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_aimObjectUp_parentSpace_aim.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_aim_objectUp_visibility.msg" ":defaultRenderUtilityList1.u" -na
		;
connectAttr "cond_aim_objectUpRotation_visibility.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "PMA_aim_objectUp_vis_logicGate.msg" ":defaultRenderUtilityList1.u" 
		-na;
connectAttr "distanceBetween1.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "remapValue_viewGrid_tZ.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_filmGate_illogicSquare_vis.msg" ":defaultRenderUtilityList1.u"
		 -na;
// End of camRig_Rigging_v002.ma
