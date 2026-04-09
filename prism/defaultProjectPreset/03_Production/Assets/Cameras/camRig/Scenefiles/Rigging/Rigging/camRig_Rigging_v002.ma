//Maya ASCII 2025ff03 scene
//Name: camRig_002.ma
//Last modified: Thu, Jan 29, 2026 11:53:29 AM
//Codeset: 1252
requires maya "2025ff03";
requires "stereoCamera" "10.0";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
fileInfo "cutIdentifier" "202407121012-8ed02f4c99";
fileInfo "osv" "Windows 11 Pro v2009 (Build: 26100)";
fileInfo "UUID" "C01249C5-4505-2F13-6863-668028D4CF90";
fileInfo "PrismStates" "{\n    \"states\": [\n        {\n            \"statename\": \"publish\",\n            \"comment\": \"\",\n            \"description\": \"\"\n        }\n    ]\n}";
createNode transform -s -n "persp";
	rename -uid "D69D1E29-4447-E742-6AE5-12A2F0BEC84B";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -12.148100935780777 10.703476880473156 -15.669603836429843 ;
	setAttr ".r" -type "double3" -29.738352729016597 579.79999999999086 0 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "731D47FA-490F-E719-7C74-F389B65D2DB3";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 24.709818704635545;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "C44EA726-4B45-CCB2-0414-8F99CEB4D40C";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -1.1247909815638719 1000.1 1.2904786227187881 ;
	setAttr ".r" -type "double3" -90 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "FD6B7441-4F59-5FF6-C9C2-7B8BEBF1DE8D";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 27.556708540602038;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	rename -uid "2F246EDE-4D58-4B6E-15A4-51AA3CAF80E7";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1.2170565319500013 2.1233422481986097 1000.1000252885148 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "9493FDD1-4838-E161-1048-AA82045393E7";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1000252885148;
	setAttr ".ow" 35.127957867742872;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".tp" -type "double3" -2.6645352591003757e-15 0 0 ;
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	rename -uid "187764A0-4E5C-AF71-6566-FA8143A1395A";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 90 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "A6A0163A-41CB-3CE3-314D-348FE5BD1B0D";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
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
	setAttr ".ff" 0;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
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
	addAttr -ci true -sn "gridOverlay" -ln "gridOverlay" -min 0 -max 3 -en "Off:illogic Square:HD:Cinemascope" 
		-at "enum";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "horizontalCam" -ln "horizontalCam" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "aim" -ln "aim" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_02" -ln "divider_02" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "focal" -ln "focal" -dv 35 -at "double";
	addAttr -ci true -sn "dof" -ln "dof" -nn "Depth of Field" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "fStop" -ln "fStop" -nn "F-Stop" -dv 5.6 -at "double";
	addAttr -ci true -sn "focusDistance" -ln "focusDistance" -at "double";
	addAttr -ci true -sn "distanceTool" -ln "distanceTool" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_03" -ln "divider_03" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "ref" -ln "ref" -nn "References" -min 0 -max 4 -en "Off:World:General:Root:Shake" 
		-at "enum";
	addAttr -ci true -sn "divider_04" -ln "divider_04" -nn " " -min 0 -max 0 -en " " 
		-at "enum";
	addAttr -ci true -sn "nearClip" -ln "nearClip" -dv 1 -at "double";
	addAttr -ci true -sn "farClip" -ln "farClip" -dv 10000 -at "double";
	addAttr -ci true -sn "overscan" -ln "overscan" -dv 1 -min 0.1 -max 10 -at "double";
	addAttr -ci true -sn "resolutionGate" -ln "resolutionGate" -min 0 -max 3 -en "Fill:Horizontal:Vertical:Overscan" 
		-at "enum";
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
	setAttr -cb on ".gridOverlay";
	setAttr -cb on ".divider_01";
	setAttr -k on ".horizontalCam";
	setAttr -k on ".aim";
	setAttr -cb on ".divider_02";
	setAttr -k on ".focal";
	setAttr -cb on ".dof";
	setAttr -k on ".fStop";
	setAttr -k on ".focusDistance";
	setAttr -k on ".distanceTool";
	setAttr -cb on ".divider_03";
	setAttr -cb on ".ref";
	setAttr -cb on ".divider_04";
	setAttr -cb on ".nearClip";
	setAttr -cb on ".farClip";
	setAttr -cb on ".overscan";
	setAttr -cb on ".resolutionGate" 1;
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
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.34099999 0.34099999 0.34099999 ;
	setAttr -k on ".ro";
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
	setAttr -k on ".ro";
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
	setAttr -k on ".ro";
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
	setAttr -k on ".ro";
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
	setAttr -k on ".ro";
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
	setAttr -k on ".ro";
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
	setAttr -k on ".ro";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -cb on ".offset" yes;
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
createNode lightLinker -s -n "lightLinker1";
	rename -uid "1C68B71B-430D-D299-0B48-B99A625ED312";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "40E43233-440B-7AAA-BFB5-72A0B127E281";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "A538ADD0-42C4-C71F-2750-7AB5805558BE";
createNode displayLayerManager -n "layerManager";
	rename -uid "A65CBA42-4CDA-3360-AF60-5A8037DFA01B";
createNode displayLayer -n "defaultLayer";
	rename -uid "670BBA40-43B8-303D-F778-E68C9BEFEDB9";
	setAttr ".ufem" -type "stringArray" 0  ;
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "5F6C6ABB-4A49-08DD-159E-518F8E7DCE28";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "94FB00BB-4DAD-119D-622C-76B1A62945A8";
	setAttr ".g" yes;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "6B060652-40D6-C2A8-8FA1-EC842DF8F5F2";
	setAttr ".b" -type "string" (
		"// Maya Mel UI Configuration File.\n//\n//  This script is machine generated.  Edit at your own risk.\n//\n//\n\nglobal string $gMainPane;\nif (`paneLayout -exists $gMainPane`) {\n\n\tglobal int $gUseScenePanelConfig;\n\tint    $useSceneConfig = $gUseScenePanelConfig;\n\tint    $nodeEditorPanelVisible = stringArrayContains(\"nodeEditorPanel1\", `getPanel -vis`);\n\tint    $nodeEditorWorkspaceControlOpen = (`workspaceControl -exists nodeEditorPanel1Window` && `workspaceControl -q -visible nodeEditorPanel1Window`);\n\tint    $menusOkayInPanels = `optionVar -q allowMenusInPanels`;\n\tint    $nVisPanes = `paneLayout -q -nvp $gMainPane`;\n\tint    $nPanes = 0;\n\tstring $editorName;\n\tstring $panelName;\n\tstring $itemFilterName;\n\tstring $panelConfig;\n\n\t//\n\t//  get current state of the UI\n\t//\n\tsceneUIReplacement -update $gMainPane;\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Top View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Top View\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|top\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n"
		+ "            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n"
		+ "            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Side View\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Side View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|side\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n"
		+ "            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n"
		+ "            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n"
		+ "            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Front View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Front View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|front\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n"
		+ "            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n"
		+ "            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n"
		+ "            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Persp View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Persp View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n"
		+ "            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n"
		+ "            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n"
		+ "            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1276\n            -height 1098\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"ToggledOutliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"ToggledOutliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n"
		+ "            -showReferenceNodes 1\n            -showReferenceMembers 1\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n"
		+ "            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -selectCommand \"print(\\\"\\\")\" \n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            -ufeFilter \"USD\" \"InactivePrims\" -ufeFilterValue 1\n            $editorName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n"
		+ "            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n"
		+ "            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -ufeFilter \"USD\" \"InactivePrims\" -ufeFilterValue 1\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"graphEditor\" (localizedPanelLabel(\"Graph Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n"
		+ "                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 1\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 1\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -showUfeItems 1\n                -displayMode \"DAG\" \n"
		+ "                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 1\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n            animCurveEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showPlayRangeShades \"on\" \n                -lockPlayRangeShades \"off\" \n                -smoothness \"fine\" \n"
		+ "                -resultSamples 1\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                -showUpstreamCurves 1\n                -keyMinScale 1\n                -stackedCurvesMin -1\n                -stackedCurvesMax 1\n                -stackedCurvesSpace 0.2\n                -preSelectionHighlight 0\n                -limitToSelectedCurves 0\n                -constrainDrag 0\n                -valueLinesToggle 0\n                -outliner \"graphEditor1OutlineEd\" \n                -highlightAffectedCurves 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dopeSheetPanel\" (localizedPanelLabel(\"Dope Sheet\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n"
		+ "                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 0\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n"
		+ "                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 1\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -showUfeItems 1\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 0\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n"
		+ "            dopeSheetEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -hierarchyBelow 0\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"timeEditorPanel\" (localizedPanelLabel(\"Time Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Time Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"clipEditorPanel\" (localizedPanelLabel(\"Trax Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n"
		+ "            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"sequenceEditorPanel\" (localizedPanelLabel(\"Camera Sequencer\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Camera Sequencer\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = sequenceEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 1 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperGraphPanel\" (localizedPanelLabel(\"Hypergraph Hierarchy\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypergraph Hierarchy\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"HyperGraphEd\");\n            hyperGraph -e \n                -graphLayoutStyle \"hierarchicalLayout\" \n                -orientation \"horiz\" \n                -mergeConnections 0\n                -zoom 1\n                -animateTransition 0\n                -showRelationships 1\n                -showShapes 0\n                -showDeformers 0\n                -showExpressions 0\n                -showConstraints 0\n                -showConnectionFromSelected 0\n                -showConnectionToSelected 0\n                -showConstraintLabels 0\n                -showUnderworld 0\n                -showInvisible 0\n                -transitionFrames 1\n                -opaqueContainers 0\n                -freeform 0\n                -imagePosition 0 0 \n                -imageScale 1\n                -imageEnabled 0\n                -graphType \"DAG\" \n"
		+ "                -heatMapDisplay 0\n                -updateSelection 1\n                -updateNodeAdded 1\n                -useDrawOverrideColor 0\n                -limitGraphTraversal -1\n                -range 0 0 \n                -iconSize \"smallIcons\" \n                -showCachedConnections 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperShadePanel\" (localizedPanelLabel(\"Hypershade\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypershade\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"visorPanel\" (localizedPanelLabel(\"Visor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Visor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"nodeEditorPanel\" (localizedPanelLabel(\"Node Editor\")) `;\n\tif ($nodeEditorPanelVisible || $nodeEditorWorkspaceControlOpen) {\n\t\tif (\"\" == $panelName) {\n\t\t\tif ($useSceneConfig) {\n\t\t\t\t$panelName = `scriptedPanel -unParent  -type \"nodeEditorPanel\" -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels `;\n\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -connectionMinSegment 0.03\n                -connectionOffset 0.03\n                -connectionRoundness 0.8\n                -connectionTension -100\n                -defaultPinnedState 0\n"
		+ "                -additiveGraphingMode 0\n                -connectedGraphingMode 1\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 0\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n                -showUnitConversions 0\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\t}\n\t\t} else {\n\t\t\t$label = `panel -q -label $panelName`;\n\t\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n"
		+ "                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -connectionMinSegment 0.03\n                -connectionOffset 0.03\n                -connectionRoundness 0.8\n                -connectionTension -100\n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -connectedGraphingMode 1\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 0\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n"
		+ "                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n                -showUnitConversions 0\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\tif (!$useSceneConfig) {\n\t\t\t\tpanel -e -l $label $panelName;\n\t\t\t}\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"createNodePanel\" (localizedPanelLabel(\"Create Node\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Create Node\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"polyTexturePlacementPanel\" (localizedPanelLabel(\"UV Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"UV Editor\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"renderWindowPanel\" (localizedPanelLabel(\"Render View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Render View\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"shapePanel\" (localizedPanelLabel(\"Shape Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tshapePanel -edit -l (localizedPanelLabel(\"Shape Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"posePanel\" (localizedPanelLabel(\"Pose Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tposePanel -edit -l (localizedPanelLabel(\"Pose Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynRelEdPanel\" (localizedPanelLabel(\"Dynamic Relationships\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dynamic Relationships\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"relationshipPanel\" (localizedPanelLabel(\"Relationship Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Relationship Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"referenceEditorPanel\" (localizedPanelLabel(\"Reference Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Reference Editor\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynPaintScriptedPanelType\" (localizedPanelLabel(\"Paint Effects\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Paint Effects\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"scriptEditorPanel\" (localizedPanelLabel(\"Script Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Script Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"profilerPanel\" (localizedPanelLabel(\"Profiler Tool\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Profiler Tool\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"contentBrowserPanel\" (localizedPanelLabel(\"Content Browser\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Content Browser\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|front\" \n            -useInteractiveMode 0\n            -displayLights \"all\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n"
		+ "            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 1\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n"
		+ "            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 0\n            -nurbsCurves 1\n            -nurbsSurfaces 0\n            -polymeshes 1\n            -subdivSurfaces 0\n            -planes 0\n            -lights 0\n            -cameras 1\n            -controlVertices 0\n            -hulls 0\n            -grid 1\n            -imagePlane 1\n            -joints 0\n            -ikHandles 0\n            -deformers 0\n            -dynamics 0\n            -particleInstancers 0\n            -fluids 0\n            -hairSystems 0\n            -follicles 0\n            -nCloths 0\n            -nParticles 0\n            -nRigids 0\n            -dynamicConstraints 0\n"
		+ "            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 0\n            -handles 0\n            -pivots 0\n            -textures 0\n            -strokes 0\n            -motionTrails 0\n            -clipGhosts 0\n            -bluePencil 0\n            -greasePencils 0\n            -shadows 1\n            -captureSequenceNumber -1\n            -width 1273\n            -height 1314\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"Stereo\" (localizedPanelLabel(\"Stereo\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Stereo\")) -mbv $menusOkayInPanels  $panelName;\n{ string $editorName = ($panelName+\"Editor\");\n            stereoCameraView -e \n                -camera \"|persp\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n"
		+ "                -displayAppearance \"wireframe\" \n                -activeOnly 0\n                -ignorePanZoom 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -holdOuts 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 32768\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -depthOfFieldPreview 1\n"
		+ "                -maxConstantTransparency 1\n                -objectFilterShowInHUD 1\n                -isFiltered 0\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -controllers 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n"
		+ "                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -imagePlane 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -particleInstancers 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nParticles 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -pluginShapes 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -motionTrails 1\n                -clipGhosts 1\n                -bluePencil 1\n                -greasePencils 0\n                -shadows 0\n                -captureSequenceNumber -1\n                -width 0\n                -height 0\n                -sceneRenderFilter 0\n                -displayMode \"centerEye\" \n"
		+ "                -viewColor 0 0 0 1 \n                -useCustomBackground 1\n                $editorName;\n            stereoCameraView -e -viewSelected 0 $editorName; };\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\tif ($useSceneConfig) {\n        string $configName = `getPanel -cwl (localizedPanelLabel(\"Current Layout\"))`;\n        if (\"\" != $configName) {\n\t\t\tpanelConfiguration -edit -label (localizedPanelLabel(\"Current Layout\")) \n\t\t\t\t-userCreated false\n\t\t\t\t-defaultImage \"vacantCell.xP:/\"\n\t\t\t\t-image \"\"\n\t\t\t\t-sc false\n\t\t\t\t-configString \"global string $gMainPane; paneLayout -e -cn \\\"single\\\" -ps 1 100 100 $gMainPane;\"\n\t\t\t\t-removeAllPanels\n\t\t\t\t-ap false\n\t\t\t\t\t(localizedPanelLabel(\"Persp View\")) \n\t\t\t\t\t\"modelPanel\"\n"
		+ "\t\t\t\t\t\"$panelName = `modelPanel -unParent -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels `;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 32768\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -bluePencil 1\\n    -greasePencils 0\\n    -excludeObjectPreset \\\"All\\\" \\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1276\\n    -height 1098\\n    -sceneRenderFilter 0\\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName\"\n"
		+ "\t\t\t\t\t\"modelPanel -edit -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels  $panelName;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 32768\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -bluePencil 1\\n    -greasePencils 0\\n    -excludeObjectPreset \\\"All\\\" \\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1276\\n    -height 1098\\n    -sceneRenderFilter 0\\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName\"\n"
		+ "\t\t\t\t$configName;\n\n            setNamedPanelLayout (localizedPanelLabel(\"Current Layout\"));\n        }\n\n        panelHistory -e -clear mainPanelHistory;\n        sceneUIReplacement -clear;\n\t}\n\n\ngrid -spacing 5 -size 12 -divisions 5 -displayAxes yes -displayGridLines yes -displayDivisionLines yes -displayPerspectiveLabels no -displayOrthographicLabels no -displayAxesBold yes -perspectiveLabelPosition axis -orthographicLabelPosition edge;\nviewManip -drawCompass 0 -compassAngle 0 -frontParameters \"\" -homeParameters \"\" -selectionLockParameters \"\";\n}\n");
	setAttr ".st" 3;
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "4709DC55-4F48-E4E8-EA0A-33A234FC99FB";
	setAttr ".b" -type "string" "playbackOptions -min 207 -max 208 -ast 207 -aet 208 ";
	setAttr ".st" 6;
createNode makeNurbCircle -n "makeNurbCircle1";
	rename -uid "1F00EF79-4342-92D6-4B5D-D98260970811";
	setAttr ".nr" -type "double3" 0 0 0 ;
	setAttr ".d" 1;
	setAttr ".s" 4;
createNode nodeGraphEditorInfo -n "MayaNodeEditorSavedTabsInfo";
	rename -uid "105B5642-4E92-9307-0808-93BA1D8B8485";
	setAttr -s 2 ".tgi";
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -371.7787028791264 -578.0812156799833 ;
	setAttr ".tgi[0].vh" -type "double2" 688.72546905520505 489.98598125229512 ;
	setAttr ".tgi[1].tn" -type "string" "horizontal Cam";
	setAttr ".tgi[1].vl" -type "double2" -1195.1530035055509 -473.85605375555627 ;
	setAttr ".tgi[1].vh" -type "double2" 598.05764061212574 1332.1429388542435 ;
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
	setAttr ".pa" 1;
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
connectAttr "ctrl_general.globalScale" "ctrl_general.sx" -l on;
connectAttr "ctrl_general.globalScale" "ctrl_general.sy" -l on;
connectAttr "ctrl_general.globalScale" "ctrl_general.sz" -l on;
connectAttr "ctrl_general.offset" "ctrl_general_offsetShape.lodv";
connectAttr "ctrl_root.offset" "ctrl_root_offsetShape.lodv";
connectAttr "ctrl_shake.offset" "ctrl_shake_offsetShape.lodv";
connectAttr "ctrl_cam_HOOK_pCon.ctx" "ctrl_cam_HOOK.tx";
connectAttr "ctrl_cam_HOOK_pCon.cty" "ctrl_cam_HOOK.ty";
connectAttr "ctrl_cam_HOOK_pCon.ctz" "ctrl_cam_HOOK.tz";
connectAttr "ctrl_cam_HOOK_pCon.crx" "ctrl_cam_HOOK.rx";
connectAttr "ctrl_cam_HOOK_pCon.cry" "ctrl_cam_HOOK.ry";
connectAttr "ctrl_cam_HOOK_pCon.crz" "ctrl_cam_HOOK.rz";
connectAttr "ctrl_general.s" "ctrl_cam.s";
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
connectAttr "ctrl_general.s" "ctrl_aim.s";
connectAttr "ctrl_aim.offset" "ctrl_aim_offset.lodv";
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
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
// End of camRig_002.ma
