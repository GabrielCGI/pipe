//Maya ASCII 2025ff03 scene
//Name: camRig.ma
//Last modified: Fri, Feb 07, 2025 04:21:09 PM
//Codeset: 1252
requires maya "2025ff03";
requires "stereoCamera" "10.0";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t pal;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
fileInfo "cutIdentifier" "202407121012-8ed02f4c99";
fileInfo "osv" "Windows 10 Pro v2009 (Build: 19045)";
fileInfo "UUID" "F84E69C8-4FBF-41FC-DE13-4AA3FC87E82C";
createNode transform -s -n "persp";
	rename -uid "441DD6C9-4855-F603-2BD2-B6BD7F6BB9FA";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 4.8308747982947589 30.728291712681507 -25.577022909220986 ;
	setAttr ".r" -type "double3" -53.40000000000019 -181.99999999998903 0 ;
	setAttr ".rp" -type "double3" -3.5527136788005009e-15 4.4408920985006262e-16 -1.4210854715202004e-14 ;
	setAttr ".rpt" -type "double3" 1.3696082108250003e-15 -8.4380510620149564e-15 2.3867373572590794e-14 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "42095434-4E1D-76DD-8214-1BBE9088A2FB";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".fl" 34.999999999999979;
	setAttr ".coi" 33.59999985953349;
	setAttr ".ow" 357.2483710893066;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 0 0.81025422067531205 -12 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -n "camRig";
	rename -uid "5E4C28E3-48C8-06E0-075C-479A305F5D29";
createNode transform -n "camera" -p "camRig";
	rename -uid "AF15FE46-4017-B466-04E8-80908B9D4C2B";
createNode transform -n "shotCam" -p "camera";
	rename -uid "64EF9BBD-4B6B-6680-8B83-98A224308128";
	setAttr -l on ".v";
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
	rename -uid "59980009-42AB-AD9C-51EA-2ABBB03B2C9B";
	setAttr -k off ".v";
	setAttr -av ".ovr" 1.3;
	setAttr ".ncp" 1;
	setAttr ".coi" 0.51202404210276575;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".hc" -type "string" "viewSet -p %camera";
	setAttr ".dgo" 1;
	setAttr ".dr" yes;
	setAttr ".dgc" -type "float3" 0 0 0 ;
createNode transform -n "refs" -p "camRig";
	rename -uid "6B59CF63-4E0C-636E-476F-B7B922432F5B";
createNode transform -n "imagePlane_refs_MOVE" -p "refs";
	rename -uid "D7135A58-4FAE-C2D9-E529-4BB65B842266";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "imagePlane_ref_01" -p "imagePlane_refs_MOVE";
	rename -uid "6531A9C0-4AF5-801E-C70A-9E80CF9A18A3";
createNode imagePlane -n "imagePlane_ref_Shape1" -p "imagePlane_ref_01";
	rename -uid "F67A7E6C-440B-4DB0-EF26-3A8DB911752F";
	setAttr -k off ".v";
	setAttr ".fc" 202;
	setAttr ".dlc" no;
	setAttr ".w" 10;
	setAttr ".h" 10;
	setAttr ".cs" -type "string" "ACES - ACES2065-1";
createNode parentConstraint -n "imagePlane_refs_MOVE_parentConstraint1" -p "imagePlane_refs_MOVE";
	rename -uid "5CAD4394-4A4B-064F-5631-AABD4C2FF005";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_generalW0" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_rootW1" -dv 1 -min 0 -at "double";
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
createNode transform -n "rig" -p "camRig";
	rename -uid "EF140E9A-43A3-E4A8-49D2-66914F6392F2";
createNode transform -n "controls" -p "rig";
	rename -uid "1A84599B-41DC-7945-67EA-5E8CA12B7498";
createNode transform -n "ctrl_general" -p "controls";
	rename -uid "53283ABF-433D-7545-125A-929311F33558";
	addAttr -ci true -sn "divider_aimTarget" -ln "divider_aimTarget" -nn " " -min 0 
		-max 0 -en "------" -at "enum";
	addAttr -ci true -sn "Aim" -ln "Aim" -nn "Aim Constraint" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "horizontalCam" -ln "horizontalCam" -nn "Horizontal Cam" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -sn "aimParent" -ln "aimParent" -nn "Aim Control Parent" -min 0 
		-max 3 -en "World:General:Root" -at "enum";
	addAttr -ci true -sn "divider_imagePlanes" -ln "divider_imagePlanes" -nn " " -min 
		0 -max 0 -en "------" -at "enum";
	addAttr -ci true -sn "refVisibility" -ln "refVisibility" -nn "References" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -sn "refParent" -ln "refParent" -nn "Image Plane Parent" -min 0 
		-max 2 -en "World:General:Root" -at "enum";
	addAttr -ci true -sn "divider_visibility" -ln "divider_visibility" -nn " " -min 
		0 -max 0 -en "------" -at "enum";
	addAttr -ci true -sn "camShape" -ln "camShape" -nn "Maya Camera Visibility" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -sn "controls" -ln "controls" -nn "Control Visibility" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "divider_breathingCam" -ln "divider_breathingCam" -nn " " -min 
		0 -max 0 -en "------" -at "enum";
	addAttr -ci true -sn "breathingCam" -ln "breathingCam" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "breathingCamIntensity" -ln "breathingCamIntensity" -dv 1 -min 
		0 -max 1 -at "double";
	setAttr -l on -k off ".v";
	setAttr -k off ".sx";
	setAttr -k off ".sz";
	setAttr ".mnsl" -type "double3" 0.1 0.1 0.1 ;
	setAttr ".mxsl" -type "double3" 10 10 10 ;
	setAttr ".msxe" yes;
	setAttr ".msye" yes;
	setAttr ".msze" yes;
	setAttr -cb on ".divider_aimTarget";
	setAttr -k on ".Aim";
	setAttr -k on ".horizontalCam";
	setAttr -k on ".aimParent";
	setAttr -cb on ".divider_imagePlanes";
	setAttr -k on ".refVisibility";
	setAttr -k on ".refParent" 2;
	setAttr -cb on ".divider_visibility";
	setAttr -k on ".camShape";
	setAttr -k on ".controls" yes;
	setAttr -cb on ".divider_breathingCam";
	setAttr -k on ".breathingCam";
	setAttr -k on ".breathingCamIntensity";
createNode nurbsCurve -n "ctrl_generalShape" -p "ctrl_general";
	rename -uid "8263B913-42FF-E526-5DEF-238E2DD291AD";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.56099999 0.56099999 0.56099999 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		0 12.021105646142942 -1.1677919176935021e-15
		12.021105646142939 0 0
		0 -12.021105646142942 1.1677919176935021e-15
		-12.021105646142939 0 0
		0 12.021105646142942 -1.1677919176935021e-15
		;
createNode transform -n "ctrl_root_OFFSET" -p "ctrl_general";
	rename -uid "0030A882-4377-6DB4-8604-E5A1AE0E960E";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.92648757 0.46801287 0.66785794 ;
createNode transform -n "ctrl_root_HOOK" -p "ctrl_root_OFFSET";
	rename -uid "7F5E0F56-4CCE-FC6F-F088-DB9C102B2E8B";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_root_MOVE" -p "ctrl_root_HOOK";
	rename -uid "4FECA94E-48A4-5DCD-55A4-D8999B2D9639";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_root" -p "ctrl_root_MOVE";
	rename -uid "293F0F62-4769-78CA-09A9-B5A0EB8F9382";
	setAttr -k off ".v";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_rootShape" -p "ctrl_root";
	rename -uid "5640D6C6-47EC-4E90-702A-918805CF76EA";
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
createNode transform -n "ctrl_shake_OFFSET" -p "ctrl_root";
	rename -uid "19012519-413E-0CD2-B3AB-F19FA39BBDFE";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.92648757 0.46801287 0.66785794 ;
createNode transform -n "ctrl_shake_HOOK" -p "ctrl_shake_OFFSET";
	rename -uid "F8E14C0D-44B9-B87B-37F0-D3836F95CF52";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_shake_MOVE" -p "ctrl_shake_HOOK";
	rename -uid "68B221D7-4B8F-E811-8692-C6BAEC179D9A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_shake" -p "ctrl_shake_MOVE";
	rename -uid "A399AAD1-47B3-77C9-5761-9DA50A143A64";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_shakeShape" -p "ctrl_shake";
	rename -uid "C256AE7F-4FD0-EA5B-BCE4-2A8AB1141C3D";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.40700001 0.28300002 0.83099997 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 8 0 no 3
		9 0 0.21505724700000001 0.89947866030000001 1.1476368939999999 1.7879380090000001
		 2.205490202 2.780111019 3.201068383 4
		9
		-1.3166558839527525 5.0032923590204827 -5.5489232492041489e-16
		1.3166558839527525 5.0032923590204827 -5.5489232492041489e-16
		5.0032923590204827 1.3166558839527525 6.9361540615051861e-17
		5.0032923590204827 -1.3166558839527525 -6.9361540615051861e-17
		1.3166558839527525 -5.0032923590204827 5.5489232492041489e-16
		-1.3166558839527525 -5.0032923590204827 5.5489232492041489e-16
		-5.0032923590204827 -1.3166558839527525 -6.9361540615051861e-17
		-5.0032923590204827 1.3166558839527525 6.9361540615051861e-17
		-1.3166558839527525 5.0032923590204827 -5.5489232492041489e-16
		;
createNode aimConstraint -n "ctrl_shake_MOVE_aimConstraint1" -p "ctrl_shake_MOVE";
	rename -uid "0B6D8D38-4C83-82BC-1512-BBB32428689C";
	addAttr -dcb 0 -ci true -sn "w0" -ln "ctrl_aimW0" -dv 1 -at "double";
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
createNode transform -n "ctrl_cam_HOOK" -p "controls";
	rename -uid "F629F9B7-41E2-B398-D1CD-F3B23D8B70AF";
	setAttr ".s" -type "double3" 15 15 15 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_cam_MOVE" -p "ctrl_cam_HOOK";
	rename -uid "A0628A68-4F6F-7277-67B3-F19F200CF25A";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_cam" -p "ctrl_cam_MOVE";
	rename -uid "4EFAB6B0-4C08-9759-42F5-18AD2A657C45";
	addAttr -ci true -sn "focalLength" -ln "focalLength" -dv 35 -min 12 -max 200 -at "double";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en "------" 
		-at "enum";
	addAttr -ci true -sn "dof" -ln "dof" -nn "Depth of Field" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "focusDistance" -ln "focusDistance" -min 0 -at "double";
	addAttr -ci true -sn "fStop" -ln "fStop" -min 0 -at "double";
	addAttr -ci true -sn "divider_02" -ln "divider_02" -nn " " -min 0 -max 0 -en "------" 
		-at "enum";
	addAttr -ci true -sn "gridType" -ln "gridType" -min 0 -max 3 -en "Scope:HD:Square:Square Illogic" 
		-at "enum";
	addAttr -ci true -sn "gridVisibility" -ln "gridVisibility" -nn "Grid Visibility" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_03" -ln "divider_03" -nn " " -min 0 -max 0 -en "------" 
		-at "enum";
	addAttr -ci true -sn "nearClipPlane" -ln "nearClipPlane" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "farClipPlane" -ln "farClipPlane" -dv 100000 -min 0 -at "double";
	addAttr -ci true -sn "distance" -ln "distance" -nn "Distance Tool" -min 0 -max 1 
		-at "bool";
	setAttr -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -k on ".focalLength";
	setAttr -cb on ".divider_01";
	setAttr -k on ".dof";
	setAttr -k on ".focusDistance" 5;
	setAttr -k on ".fStop" 5.6;
	setAttr -cb on ".divider_02";
	setAttr -k on ".gridType" 3;
	setAttr -k on ".gridVisibility" yes;
	setAttr -cb on ".divider_03";
	setAttr -cb on ".nearClipPlane";
	setAttr -cb on ".farClipPlane" 10000;
	setAttr -cb on ".distance";
createNode nurbsCurve -n "ctrl_camShape" -p "ctrl_cam";
	rename -uid "38BF5356-4D3E-7380-76D9-D2944178FA95";
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
		7.6788046607108406e-10 -0.077707169746137117 0.055951652732291558
		-0.054947267007280726 -0.054947267775161228 0.055951652732291558
		-0.078082197603200856 -0.078082197603200856 1.1477149665597347e-09
		-0.054947265906427206 -0.054947266674307695 0.055951652732291558
		-0.077707165330704375 -1.0686969158680334e-17 0.055951652732291544
		-0.11042489543469657 -5.5446084496328846e-18 1.1477149665597347e-09
		-0.077707165330704375 -1.0686969158680334e-17 0.055951652732291544
		-0.054947267007280726 0.054947267775161228 0.055951652732291544
		-0.078082197603200856 0.078082197603200856 1.1477149665597347e-09
		-0.054947265906427213 0.054947266674307653 0.055951652732291544
		7.6788042229489841e-10 0.077707166098584704 0.055951652732291544
		-5.5446084496328846e-18 0.11042489543469657 1.1477149665597347e-09
		7.6788041988897845e-10 0.077707169746137117 0.055951652732291544
		0.054947268543041737 0.054947267775161228 0.055951652732291544
		0.078082197603200856 0.078082197603200856 1.1477149665597347e-09
		0.054947267442188169 0.05494726667430775 0.055951652732291544
		0.07770716686646513 5.1741823993608847e-17 0.055951652732291544
		0.11042489543469657 5.5446084496328846e-18 1.1477149665597347e-09
		0.077707170514017723 5.3638195238746238e-17 0.055951652732291544
		0.054947268543041737 -0.054947267775161228 0.055951652732291558
		0.078082197603200856 -0.078082197603200856 1.1477149860229328e-09
		0.054947267442188273 -0.054947266674307653 0.055951652732291558
		7.6788046911649176e-10 -0.077707166098584704 0.055951652732291558
		5.5446084496328846e-18 -0.11042489543469657 1.1477149665597347e-09
		7.678805350889169e-10 -0.077707169746137145 0.055951652732291558
		;
createNode nurbsCurve -n "ctrl_camShape1" -p "ctrl_cam";
	rename -uid "8F29BED2-4851-26D7-8D98-EC8803927893";
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
		6.7615750544004992e-18 -0.11042490061800968 3.5983439005711089e-09
		-0.078082196038845281 -0.078082196038845281 3.5983439005711089e-09
		-0.11042490061800968 -6.7615750544004992e-18 3.5983438811079056e-09
		-0.078082196038845281 0.078082196038845281 3.5983438616447089e-09
		-6.7615750544004992e-18 0.11042490061800968 3.5983438616447089e-09
		0.078082196038845281 0.078082196038845281 3.5983438616447089e-09
		0.11042490061800968 6.7615750544004992e-18 3.5983438811079056e-09
		0.078082196038845281 -0.078082196038845281 3.5983439005711089e-09
		6.7615750544004992e-18 -0.11042490061800968 3.5983439005711089e-09
		;
createNode nurbsCurve -n "curveShape1" -p "ctrl_cam";
	rename -uid "1A7B83F8-4077-59DD-B338-38B04C15F042";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.56099999 0.56099999 0.56099999 ;
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		1 12 0 no 3
		13 0 1 2 3 4 5 6 7 8 9 10 11 12
		13
		0.13529587670856655 -0.13529587315521796 0.055951652732291517
		0.13529587402124668 -0.13529587757459555 0.20350158432590842
		0.13529587670856655 -0.13529587315521796 0.055951652732291517
		-0.13529587670856655 -0.13529587315521796 0.055951652732291517
		-0.13529587402124668 -0.13529587757459555 0.20350185360879183
		-0.13529587670856655 -0.13529587315521796 0.055951652732291517
		-0.13529587670856655 0.13529587315521796 0.055951652732291579
		-0.13529587402124668 0.13529587757459555 0.20350177558336494
		-0.13529587670856655 0.13529587315521796 0.055951652732291579
		0.13529587670856655 0.13529587315521796 0.055951652732291579
		0.13529587402124668 0.13529587757459555 0.20350143277339519
		0.13529587670856655 0.13529587315521796 0.055951652732291579
		0.13529587670856655 -0.13529587315521796 0.055951652732291517
		;
createNode transform -n "geo_grid_MOVE" -p "ctrl_cam";
	rename -uid "8798EE89-472C-07EA-CCDC-879828452AAB";
	setAttr ".rp" -type "double3" 0 0 -0.11619899900569387 ;
	setAttr ".sp" -type "double3" 0 0 -0.11619899900569387 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "geo_grid_scope" -p "geo_grid_MOVE";
	rename -uid "409DD95E-48BB-014D-339D-B39E147C2C74";
	setAttr -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".rp" -type "double3" 0 0 -0.11619899900569386 ;
	setAttr ".sp" -type "double3" 0 0 -0.11619899900569386 ;
createNode mesh -n "geo_grid_scopeShape" -p "geo_grid_scope";
	rename -uid "4CCD02B8-455F-3291-07D2-3487D6AD497E";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr -s 5 ".gtag";
	setAttr ".gtag[0].gtagnm" -type "string" "back";
	setAttr ".gtag[0].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[1].gtagnm" -type "string" "front";
	setAttr ".gtag[1].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[2].gtagnm" -type "string" "left";
	setAttr ".gtag[2].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[3].gtagnm" -type "string" "right";
	setAttr ".gtag[3].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[4].gtagnm" -type "string" "rim";
	setAttr ".gtag[4].gtagcmp" -type "componentList" 0;
	setAttr ".pv" -type "double2" 0.5 0.5 ;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 40 ".uvst[0].uvsp[0:39]" -type "float2" 0.24948356 1.2223609e-09
		 0.25104994 0.2487645 0.25104997 0.25249982 0.24948354 0.25249979 1.8946402e-08 0.25249976
		 0.25104994 0.74750024 0.25104994 0.75123554 0.25104994 1 0.24948354 0.75123549 1.8513164e-08
		 0.75123549 0.74895006 1.9128645e-08 0.75051647 0.2487645 1 0.2487645 0.75051647 0.25249976
		 0.74895006 0.25249976 0.75051647 0.74750024 1 0.74750024 0.75051647 0.75123549 0.75051647
		 1 0.74895006 0.75123549 0.24948354 1 0.74895 0.99999994 0.24948354 0.5 0.74895006
		 0.5 0.5 0.25249976 0.5 0.75123549 0.99999994 0.25249976 1 0.75123549 0.24948354 0.2487645
		 2.2273651e-08 0.2487645 0.25104994 2.2266065e-08 0.74895006 0.24876449 0.5 0.24876451
		 0.75051647 2.2266066e-08 0.24948356 0.74750024 2.2239819e-08 0.74750018 0.25104994
		 0.5 0.74895006 0.74750024 0.5 0.74750024 0.75051647 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 40 ".pt[0:39]" -type "float3"  0.10690858 -0.073008798 -0.6161989 
		0.10781036 -0.073008798 -0.6161989 0.10690858 -0.023907516 -0.27992934 0.10781036 
		-0.023907516 -0.27992934 0.10781036 -0.024390448 -0.28323668 0.10690858 -0.024390448 
		-0.28323668 0.10690858 -3.0920435e-23 -0.116199 0.10781036 -3.0920435e-23 -0.116199 
		0.10690858 0.024390448 0.050838698 0.10781036 0.024390448 0.050838698 0.10781036 
		0.023907516 0.047531355 0.10690858 0.023907516 0.047531355 -0.10781036 -0.073008798 
		-0.6161989 -0.10690858 -0.073008798 -0.6161989 -0.10781036 -0.023907516 -0.27992934 
		-0.10690858 -0.023907516 -0.27992934 -0.10690858 -0.024390448 -0.28323668 -0.10781036 
		-0.024390448 -0.28323668 -0.10781036 -3.0920435e-23 -0.116199 -0.10690858 -3.0920435e-23 
		-0.116199 -0.10781036 0.024390448 0.050838698 -0.10690858 0.024390448 0.050838698 
		-0.10690858 0.023907516 0.047531355 -0.10781036 0.023907516 0.047531355 0.32561842 
		-0.024390448 -0.28323668 0.32561842 -0.023907516 -0.27992934 0 -0.023907516 -0.27992934 
		0 -0.024390448 -0.28323668 -0.32561842 -0.023907516 -0.27992934 -0.32561842 -0.024390448 
		-0.28323668 0.10781036 0.073008798 0.38380092 0.10690858 0.073008798 0.38380092 -0.10690858 
		0.073008798 0.38380092 -0.10781036 0.073008798 0.38380092 0.32561842 0.023907516 
		0.047531355 0.32561842 0.024390448 0.050838698 0 0.024390448 0.050838698 0 0.023907516 
		0.047531355 -0.32561842 0.024390448 0.050838698 -0.32561842 0.023907516 0.047531355;
	setAttr -s 40 ".vt[0:39]"  -0.16416235 0 0.49999991 -0.16554706 0 0.49999991
		 -0.16416235 0 0.16373035 -0.16554706 0 0.16373035 -0.16554706 0 0.1670377 -0.16416235 0 0.1670377
		 -0.16416235 0 2.1175824e-22 -0.16554706 0 2.1175824e-22 -0.16416235 0 -0.1670377
		 -0.16554706 0 -0.1670377 -0.16554706 0 -0.16373035 -0.16416235 0 -0.16373035 0.16554706 0 0.49999991
		 0.16416235 0 0.49999991 0.16554706 0 0.16373035 0.16416235 0 0.16373035 0.16416235 0 0.1670377
		 0.16554706 0 0.1670377 0.16554706 0 2.1175824e-22 0.16416235 0 2.1175824e-22 0.16554706 0 -0.1670377
		 0.16416235 0 -0.1670377 0.16416235 0 -0.16373035 0.16554706 0 -0.16373035 -0.49999994 0 0.1670377
		 -0.49999994 0 0.16373035 0 0 0.16373035 0 0 0.1670377 0.49999994 0 0.16373035 0.49999994 0 0.1670377
		 -0.16554706 0 -0.49999991 -0.16416235 0 -0.49999991 0.16416235 0 -0.49999991 0.16554706 0 -0.49999991
		 -0.49999994 0 -0.16373035 -0.49999994 0 -0.1670377 0 0 -0.1670377 0 0 -0.16373035
		 0.49999994 0 -0.1670377 0.49999994 0 -0.16373035;
	setAttr -s 60 ".ed[0:59]"  1 0 0 0 5 1 5 4 1 4 1 1 2 5 1 5 27 1 27 26 1
		 26 2 1 3 2 1 2 6 1 6 7 1 7 3 1 4 3 1 3 25 1 25 24 0 24 4 1 6 11 1 11 10 1 10 7 1
		 8 11 1 11 37 1 37 36 1 36 8 1 9 8 1 8 31 1 31 30 0 30 9 1 10 9 1 9 35 1 35 34 0 34 10 1
		 13 12 0 12 17 1 17 16 1 16 13 1 14 17 1 17 29 1 29 28 0 28 14 1 15 14 1 14 18 1 18 19 1
		 19 15 1 16 15 1 15 26 1 27 16 1 18 23 1 23 22 1 22 19 1 20 23 1 23 39 1 39 38 0 38 20 1
		 21 20 1 20 33 1 33 32 0 32 21 1 22 21 1 21 36 1 37 22 1;
	setAttr -s 20 -ch 80 ".fc[0:19]" -type "polyFaces" 
		f 4 0 1 2 3
		mu 0 4 0 30 1 28
		f 4 4 5 6 7
		mu 0 4 2 1 32 24
		f 4 8 9 10 11
		mu 0 4 3 2 36 22
		f 4 12 13 14 15
		mu 0 4 28 3 4 29
		f 4 -11 16 17 18
		mu 0 4 22 36 5 34
		f 4 19 20 21 22
		mu 0 4 6 5 38 25
		f 4 23 24 25 26
		mu 0 4 8 6 7 20
		f 4 27 28 29 30
		mu 0 4 34 8 9 35
		f 4 31 32 33 34
		mu 0 4 10 33 11 31
		f 4 35 36 37 38
		mu 0 4 13 11 12 26
		f 4 39 40 41 42
		mu 0 4 14 13 39 23
		f 4 43 44 -7 45
		mu 0 4 31 14 24 32
		f 4 -42 46 47 48
		mu 0 4 23 39 15 37
		f 4 49 50 51 52
		mu 0 4 17 15 16 27
		f 4 53 54 55 56
		mu 0 4 19 17 18 21
		f 4 57 58 -22 59
		mu 0 4 37 19 25 38
		f 4 -9 -13 -3 -5
		mu 0 4 2 3 28 1
		f 4 -24 -28 -18 -20
		mu 0 4 6 8 34 5
		f 4 -40 -44 -34 -36
		mu 0 4 13 14 31 11
		f 4 -54 -58 -48 -50
		mu 0 4 17 19 37 15;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "geo_grid_HD" -p "geo_grid_MOVE";
	rename -uid "F83610B2-40C9-3DC5-E232-75A496EDC603";
	setAttr -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".rp" -type "double3" 0 0 -0.11619899900569386 ;
	setAttr ".sp" -type "double3" 0 0 -0.11619899900569386 ;
createNode mesh -n "geo_grid_HDShape" -p "geo_grid_HD";
	rename -uid "1C7F6A2C-4000-045D-D796-C4829D485333";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr -s 5 ".gtag";
	setAttr ".gtag[0].gtagnm" -type "string" "back";
	setAttr ".gtag[0].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[1].gtagnm" -type "string" "front";
	setAttr ".gtag[1].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[2].gtagnm" -type "string" "left";
	setAttr ".gtag[2].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[3].gtagnm" -type "string" "right";
	setAttr ".gtag[3].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[4].gtagnm" -type "string" "rim";
	setAttr ".gtag[4].gtagcmp" -type "componentList" 0;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 32 ".uvst[0].uvsp[0:31]" -type "float2" 0.66760027 1 0.99999994
		 0.6650002 0.66573298 0.66833317 0.66573304 0.66500026 0.33426699 1 0.33426696 0.66833317
		 0.3323997 0.66833317 2.5145713e-08 0.66833317 0.3323997 0.66500026 0.33239961 -3.4924601e-09
		 0.3323997 0.33499986 2.5145713e-08 0.33499986 0.33426693 0.33166686 0.66573298 0.33499986
		 0.66573292 -3.4924601e-09 0.66573298 0.33166689 0.66760021 0.33166686 1 0.33166689
		 0.66760027 0.66833317 0.99999994 0.66833317 0.66573304 1 0.3323997 1 0.33239967 0.33166689
		 2.9860519e-08 0.33166686 0.33426696 -7.5281914e-09 0.66760027 -7.3729711e-09 2.9860537e-08
		 0.6650002 0.33426696 0.33499986 0.33426696 0.6650002 0.66760027 0.33499986 0.99999994
		 0.33499986 0.66760027 0.6650002;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 32 ".vt[0:31]"  0.057737537 0.097586267 -0.116199 0.058388054 0.097586267 -0.116199
		 0.058388054 0.032854013 -0.116199 0.057737537 0.032854013 -0.116199 0.057737537 0.032203507 -0.116199
		 0.058388054 0.032203507 -0.116199 -0.058388073 0.097586267 -0.116199 -0.057737559 0.097586267 -0.116199
		 -0.057737559 0.032854013 -0.116199 -0.058388073 0.032854013 -0.116199 -0.058388073 0.032203507 -0.116199
		 -0.057737559 0.032203507 -0.116199 -0.057737559 -0.097586267 -0.116199 -0.058388073 -0.097586267 -0.116199
		 -0.058388073 -0.032203496 -0.116199 -0.058388073 -0.032854002 -0.116199 -0.057737559 -0.032854002 -0.116199
		 -0.057737559 -0.032203496 -0.116199 -0.17418842 -0.032854002 -0.116199 -0.17418842 -0.032203496 -0.116199
		 0.058388054 -0.097586267 -0.116199 0.057737537 -0.097586267 -0.116199 0.057737537 -0.032203496 -0.116199
		 0.057737537 -0.032854002 -0.116199 0.058388054 -0.032854002 -0.116199 0.058388054 -0.032203496 -0.116199
		 0.17418842 -0.032203496 -0.116199 0.17418842 -0.032854002 -0.116199 -0.17418842 0.032203507 -0.116199
		 -0.17418842 0.032854013 -0.116199 0.17418842 0.032854013 -0.116199 0.17418842 0.032203507 -0.116199;
	setAttr -s 48 ".ed[0:47]"  1 0 0 0 3 1 3 2 1 2 1 1 2 5 1 5 31 1 31 30 0
		 30 2 1 4 3 1 3 8 1 8 11 1 11 4 1 5 4 1 4 22 1 22 25 1 25 5 1 7 6 0 6 9 1 9 8 1 8 7 1
		 10 9 1 9 29 1 29 28 0 28 10 1 11 10 1 10 14 1 14 17 1 17 11 1 13 12 0 12 16 1 16 15 1
		 15 13 1 15 14 1 14 19 1 19 18 0 18 15 1 17 16 1 16 23 1 23 22 1 22 17 1 21 20 0 20 24 1
		 24 23 1 23 21 1 25 24 1 24 27 1 27 26 0 26 25 1;
	setAttr -s 16 -ch 64 ".fc[0:15]" -type "polyFaces" 
		f 4 0 1 2 3
		mu 0 4 0 20 2 18
		f 4 4 5 6 7
		mu 0 4 18 31 1 19
		f 4 8 9 10 11
		mu 0 4 3 2 5 28
		f 4 12 13 14 15
		mu 0 4 31 3 13 29
		f 4 16 17 18 19
		mu 0 4 4 21 6 5
		f 4 20 21 22 23
		mu 0 4 8 6 7 26
		f 4 24 25 26 27
		mu 0 4 28 8 10 27
		f 4 28 29 30 31
		mu 0 4 9 24 12 22
		f 4 32 33 34 35
		mu 0 4 22 10 11 23
		f 4 36 37 38 39
		mu 0 4 27 12 15 13
		f 4 40 41 42 43
		mu 0 4 14 25 16 15
		f 4 44 45 46 47
		mu 0 4 29 16 17 30
		f 4 -3 -9 -13 -5
		mu 0 4 18 2 3 31
		f 4 -19 -21 -25 -11
		mu 0 4 5 6 8 28
		f 4 -33 -31 -37 -27
		mu 0 4 10 22 12 27
		f 4 -39 -43 -45 -15
		mu 0 4 13 15 16 29;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "geo_grid_square" -p "geo_grid_MOVE";
	rename -uid "FFCFDE16-45EF-1673-C376-18B1793424A8";
	setAttr -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".rp" -type "double3" 0 0 -0.11619899900569386 ;
	setAttr ".sp" -type "double3" 0 0 -0.11619899900569386 ;
createNode mesh -n "geo_grid_squareShape" -p "geo_grid_square";
	rename -uid "6BAF038C-42C2-2BFF-5507-CCAEA6063494";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr -s 5 ".gtag";
	setAttr ".gtag[0].gtagnm" -type "string" "back";
	setAttr ".gtag[0].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[1].gtagnm" -type "string" "front";
	setAttr ".gtag[1].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[2].gtagnm" -type "string" "left";
	setAttr ".gtag[2].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[3].gtagnm" -type "string" "right";
	setAttr ".gtag[3].gtagcmp" -type "componentList" 0;
	setAttr ".gtag[4].gtagnm" -type "string" "rim";
	setAttr ".gtag[4].gtagcmp" -type "componentList" 0;
	setAttr ".pv" -type "double2" 0.50000001257285653 0.4999999962359043 ;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 32 ".uvst[0].uvsp[0:31]" -type "float2" 0.66760027 1 0.99999994
		 0.6650002 0.66573298 0.66833317 0.66573304 0.66500026 0.33426699 1 0.33426696 0.66833317
		 0.3323997 0.66833317 2.5145713e-08 0.66833317 0.3323997 0.66500026 0.33239961 -3.4924601e-09
		 0.3323997 0.33499986 2.5145713e-08 0.33499986 0.33426693 0.33166686 0.66573298 0.33499986
		 0.66573292 -3.4924601e-09 0.66573298 0.33166689 0.66760021 0.33166686 1 0.33166689
		 0.66760027 0.66833317 0.99999994 0.66833317 0.66573304 1 0.3323997 1 0.33239967 0.33166689
		 2.9860519e-08 0.33166686 0.33426696 -7.5281914e-09 0.66760027 -7.3729711e-09 2.9860537e-08
		 0.6650002 0.33426696 0.33499986 0.33426696 0.6650002 0.66760027 0.33499986 0.99999994
		 0.33499986 0.66760027 0.6650002;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 32 ".pt[0:31]" -type "float3"  0.00022112767 0.076377451 
		0 0.00029288721 0.076377451 0 0.00029288721 0.025985213 0 0.00022112767 0.025985213 
		0 0.00022112767 0.025913469 0 0.00029288721 0.025913469 0 -0.00029288846 0.076377451 
		0 -0.00022112983 0.076377451 0 -0.00022112983 0.025985213 0 -0.00029288846 0.025985213 
		0 -0.00029288846 0.025913469 0 -0.00022112983 0.025913469 0 -0.00022112983 -0.076377481 
		0 -0.00029288846 -0.076377481 0 -0.00029288846 -0.025913469 0 -0.00029288846 -0.025985213 
		0 -0.00022112983 -0.025985213 0 -0.00022112983 -0.025913469 0 -0.00094907731 -0.025985213 
		0 -0.00094907731 -0.025913469 0 0.00029288721 -0.076377481 0 0.00022112767 -0.076377481 
		0 0.00022112767 -0.025913469 0 0.00022112767 -0.025985213 0 0.00029288721 -0.025985213 
		0 0.00029288721 -0.025913469 0 0.00094907731 -0.025913469 0 0.00094907731 -0.025985213 
		0 -0.00094907731 0.025913469 0 -0.00094907731 0.025985213 0 0.00094907731 0.025985213 
		0 0.00094907731 0.025913469 0;
	setAttr -s 32 ".vt[0:31]"  0.057737537 0.097586267 -0.116199 0.058388054 0.097586267 -0.116199
		 0.058388054 0.032854013 -0.116199 0.057737537 0.032854013 -0.116199 0.057737537 0.032203507 -0.116199
		 0.058388054 0.032203507 -0.116199 -0.058388073 0.097586267 -0.116199 -0.057737559 0.097586267 -0.116199
		 -0.057737559 0.032854013 -0.116199 -0.058388073 0.032854013 -0.116199 -0.058388073 0.032203507 -0.116199
		 -0.057737559 0.032203507 -0.116199 -0.057737559 -0.097586267 -0.116199 -0.058388073 -0.097586267 -0.116199
		 -0.058388073 -0.032203496 -0.116199 -0.058388073 -0.032854002 -0.116199 -0.057737559 -0.032854002 -0.116199
		 -0.057737559 -0.032203496 -0.116199 -0.17418842 -0.032854002 -0.116199 -0.17418842 -0.032203496 -0.116199
		 0.058388054 -0.097586267 -0.116199 0.057737537 -0.097586267 -0.116199 0.057737537 -0.032203496 -0.116199
		 0.057737537 -0.032854002 -0.116199 0.058388054 -0.032854002 -0.116199 0.058388054 -0.032203496 -0.116199
		 0.17418842 -0.032203496 -0.116199 0.17418842 -0.032854002 -0.116199 -0.17418842 0.032203507 -0.116199
		 -0.17418842 0.032854013 -0.116199 0.17418842 0.032854013 -0.116199 0.17418842 0.032203507 -0.116199;
	setAttr -s 48 ".ed[0:47]"  1 0 0 0 3 0 3 2 1 2 1 0 2 5 1 5 31 0 31 30 0
		 30 2 0 4 3 1 3 8 0 8 11 1 11 4 0 5 4 1 4 22 0 22 25 1 25 5 0 7 6 0 6 9 0 9 8 1 8 7 0
		 10 9 1 9 29 0 29 28 0 28 10 0 11 10 1 10 14 0 14 17 1 17 11 0 13 12 0 12 16 0 16 15 1
		 15 13 0 15 14 1 14 19 0 19 18 0 18 15 0 17 16 1 16 23 0 23 22 1 22 17 0 21 20 0 20 24 0
		 24 23 1 23 21 0 25 24 1 24 27 0 27 26 0 26 25 0;
	setAttr -s 16 -ch 64 ".fc[0:15]" -type "polyFaces" 
		f 4 0 1 2 3
		mu 0 4 0 20 2 18
		f 4 4 5 6 7
		mu 0 4 18 31 1 19
		f 4 8 9 10 11
		mu 0 4 3 2 5 28
		f 4 12 13 14 15
		mu 0 4 31 3 13 29
		f 4 16 17 18 19
		mu 0 4 4 21 6 5
		f 4 20 21 22 23
		mu 0 4 8 6 7 26
		f 4 24 25 26 27
		mu 0 4 28 8 10 27
		f 4 28 29 30 31
		mu 0 4 9 24 12 22
		f 4 32 33 34 35
		mu 0 4 22 10 11 23
		f 4 36 37 38 39
		mu 0 4 27 12 15 13
		f 4 40 41 42 43
		mu 0 4 14 25 16 15
		f 4 44 45 46 47
		mu 0 4 29 16 17 30
		f 4 -3 -9 -13 -5
		mu 0 4 18 2 3 31
		f 4 -19 -21 -25 -11
		mu 0 4 5 6 8 28
		f 4 -33 -31 -37 -27
		mu 0 4 10 22 12 27
		f 4 -39 -43 -45 -15
		mu 0 4 13 15 16 29;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "imagePlane_squareIllogic" -p "geo_grid_MOVE";
	rename -uid "C910B3D2-45C0-A663-6159-18AB179FF972";
	setAttr ".t" -type "double3" 0 0 -0.11619899900569386 ;
	setAttr ".s" -type "double3" 0.027961862889452488 0.027961862889452488 0.027961862889452488 ;
createNode imagePlane -n "imagePlane_squareIllogicShape" -p "imagePlane_squareIllogic";
	rename -uid "E7B6BD77-43FB-445B-C680-23B731BC5AD7";
	setAttr -k off ".v";
	setAttr ".fc" 152;
	setAttr ".imn" -type "string" "R:/pipeline/pipe/maya/camRig_emile/imagePlanes/square_noCross.png";
	setAttr ".cov" -type "short2" 1280 1280 ;
	setAttr ".dic" yes;
	setAttr ".ag" 0.5;
	setAttr ".dlc" no;
	setAttr ".w" 12.48;
	setAttr ".h" 12.48;
	setAttr ".cs" -type "string" "sRGB - Texture";
createNode aimConstraint -n "ctrl_cam_MOVE_aimConstraint1" -p "ctrl_cam_MOVE";
	rename -uid "EE18E323-4D52-4A3F-6E71-FEAFA5054331";
	addAttr -dcb 0 -ci true -sn "w0" -ln "ctrl_aimW0" -dv 1 -at "double";
	addAttr -dcb 0 -ci true -sn "w1" -ln "ctrl_horizontalCam_upW1" -dv 1 -at "double";
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
	setAttr ".a" -type "double3" 0 0 -1 ;
	setAttr ".wut" 0;
	setAttr -k on ".w0" 0;
	setAttr -k on ".w1";
createNode parentConstraint -n "pCon_ctrl_cam_HOOK" -p "ctrl_cam_HOOK";
	rename -uid "6413BDFD-4DF1-DAD1-E1CA-BFB80CB0751B";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_shakeW0" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_breathingCamW1" -dv 1 -min 0 
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
	setAttr -s 2 ".tg";
	setAttr -k on ".w0";
	setAttr -k on ".w1";
createNode transform -n "ctrl_aim_OFFSET" -p "controls";
	rename -uid "8BEE8E0C-4C6F-AB23-27F8-CFB9CC01FCE5";
	setAttr ".t" -type "double3" 0 0 -12 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.92648757 0.46801287 0.66785794 ;
createNode transform -n "ctrl_aim_HOOK" -p "ctrl_aim_OFFSET";
	rename -uid "635C08F5-45A5-F3F1-7B52-D1A3F590C297";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_aim_MOVE" -p "ctrl_aim_HOOK";
	rename -uid "FFA4C963-4F23-8F99-98A6-00BDA702B889";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_aim" -p "ctrl_aim_MOVE";
	rename -uid "4ED64E47-4C8A-38DA-C4B8-B998092F860E";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en "------" 
		-at "enum";
	addAttr -ci true -sn "aimUpVector" -ln "aimUpVector" -nn "Up Vector" -min 0 -max 
		4 -en "Scene Up:Object Up:Object Rotation Up:Vector:None" -at "enum";
	addAttr -ci true -sn "divider_02" -ln "divider_02" -nn " " -min 0 -max 0 -en "------" 
		-at "enum";
	addAttr -ci true -sn "worldUpVectorX" -ln "worldUpVectorX" -min -1 -max 1 -at "double";
	addAttr -ci true -sn "worldUpVectorY" -ln "worldUpVectorY" -dv 1 -min -1 -max 1 
		-at "double";
	addAttr -ci true -sn "worldUpVectorZ" -ln "worldUpVectorZ" -min -1 -max 1 -at "double";
	setAttr -k off ".v";
	setAttr -k off ".sy";
	setAttr -k off ".sx";
	setAttr -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -k on ".aimUpVector";
	setAttr -cb on ".divider_02";
	setAttr -k on ".worldUpVectorX";
	setAttr -k on ".worldUpVectorY";
	setAttr -k on ".worldUpVectorZ";
createNode nurbsCurve -n "ctrl_aimShape" -p "ctrl_aim";
	rename -uid "1C75BF2E-46E2-E0BA-A56E-30BF112918FD";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 12 0 no 3
		13 0 4 8 12 16 24.485281000000001 32.970562999999999 36.970562999999999 45.455843999999999
		 53.941125 57.941125 66.426406999999998 74.911687999999998
		13
		0.7915218706819378 0.7915218706819378 4.4408920985006262e-16
		-0.7915218706819378 0.7915218706819378 4.4408920985006262e-16
		-0.7915218706819378 -0.7915218706819378 1.7763568394002505e-15
		0.7915218706819378 -0.7915218706819378 1.7763568394002505e-15
		0.7915218706819378 0.7915218706819378 4.4408920985006262e-16
		0 -8.2395869022311799e-16 -1.642012982915154
		-0.7915218706819378 0.7915218706819378 4.4408920985006262e-16
		-0.7915218706819378 -0.7915218706819378 1.7763568394002505e-15
		0 -8.2395869022311799e-16 -1.642012982915154
		0.7915218706819378 -0.7915218706819378 1.7763568394002505e-15
		0.7915218706819378 0.7915218706819378 4.4408920985006262e-16
		0 -8.2395869022311799e-16 -1.642012982915154
		-0.7915218706819378 0.7915218706819378 4.4408920985006262e-16
		;
createNode parentConstraint -n "ctrl_aim_MOVE_parentConstraint1" -p "ctrl_aim_MOVE";
	rename -uid "4BF4557F-43EA-C1E5-0BE5-AAB6152F87C7";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_rootW0" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_generalW1" -dv 1 -min 0 -at "double";
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
	setAttr ".tg[0].tot" -type "double3" 0 0 -1 ;
	setAttr ".tg[1].tot" -type "double3" 0 0 -15 ;
	setAttr -k on ".w0";
	setAttr -k on ".w1";
createNode transform -n "ctrl_aim_objectUp_OFFSET" -p "controls";
	rename -uid "578D3F47-4395-A09D-B680-01B028044926";
	setAttr ".t" -type "double3" 0 0 -16 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_aim_objectUp_HOOK" -p "ctrl_aim_objectUp_OFFSET";
	rename -uid "EE7A02D5-465F-D7A9-D4B0-1CAF40240D8C";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.60000002 0.1 ;
createNode transform -n "ctrl_aim_objectUp_MOVE" -p "ctrl_aim_objectUp_HOOK";
	rename -uid "EB0EA3F8-4FAE-A2C1-44E0-B1A5610E7A5B";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_aim_objectUp" -p "ctrl_aim_objectUp_MOVE";
	rename -uid "D3EB0C96-403F-751E-6AF9-29AE87D64DF9";
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en "------" 
		-at "enum";
	addAttr -ci true -sn "objectUpParent" -ln "objectUpParent" -nn "Object Parent" -min 
		0 -max 2 -en "World:Aim:Root" -at "enum";
	setAttr -k off ".v";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -cb on ".divider_01";
	setAttr -k on ".objectUpParent" 1;
createNode nurbsCurve -n "ctrl_aim_objectUpShape" -p "ctrl_aim_objectUp";
	rename -uid "9793B113-4866-F3CA-2014-2592B54130BF";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 0.19499999 0.024999976 ;
	setAttr ".ls" 4;
	setAttr ".cc" -type "nurbsCurve" 
		1 34 0 no 3
		35 1 5 9 10 11 15 19 20 21 25 29 30 31 35 39 40 41 42 43 44 45 46 47 48 49
		 50 51 52 53 54 55 56 57 58 59
		35
		0 0 -1.6190145701821863
		0 0 -1.6190145701821863
		0 0 -1.6190145701821863
		0 0 0
		0 0 1.6190145701821863
		0 0 1.6190145701821863
		0 0 1.6190145701821863
		0 0 0
		0.77827225548927093 0 0
		0.77827225548927093 0 0
		0.77827225548927093 0 0
		0 0 0
		-0.77827225548927093 0 0
		-0.77827225548927093 0 0
		-0.77827225548927093 0 0
		0 0 0
		0 1.5200039871611073 0
		-0.65090342741383034 1.5200020069296953 0
		0 2.677104111424728 0
		0.65090342741383034 1.5200020069296953 0
		0 1.5200039871611073 0
		0 1.5200020069296953 0.65090342741383034
		0 2.677104111424728 0
		0 1.5200020069296953 -0.65090342741383034
		0 1.5200039871611073 0
		0 0 0
		0 -1.6190145948194801 0
		-0.29891888189796367 -1.8626388944063548 0
		0 -1.6190251757146228 0
		0.29891888189796367 -1.8626388944063548 0
		0 -1.6190145948194801 0
		0 -1.8626388944063548 -0.29891888189796367
		0 -1.6190251757146228 0
		0 -1.8626388944063548 0.29891888189796367
		0 -1.6190145948194801 0
		;
createNode parentConstraint -n "ctrl_aim_objectUp_HOOK_parentConstraint1" -p "ctrl_aim_objectUp_HOOK";
	rename -uid "659A0062-482A-9128-B3AB-A6BD45E9FA02";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_aimW0" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_rootW1" -dv 1 -min 0 -at "double";
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
	setAttr ".tg[1].tot" -type "double3" 0 0 -1.0666666666666667 ;
	setAttr -k on ".w0";
	setAttr -k on ".w1";
createNode transform -n "ctrl_horizontalCam_up_OFFSET" -p "controls";
	rename -uid "AF1A3585-42B1-C8B2-0B2F-3CAB8455204C";
	setAttr ".t" -type "double3" 0 0 -20 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_horizontalCam_up_MOVE" -p "ctrl_horizontalCam_up_OFFSET";
	rename -uid "72308D35-4D77-EB01-7552-CA97ACDF1D73";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_horizontalCam_up" -p "ctrl_horizontalCam_up_MOVE";
	rename -uid "44C07AD2-4533-AF4A-C2EA-1BA9F515CD15";
createNode nurbsCurve -n "ctrl_horizontalCam_upShape" -p "ctrl_horizontalCam_up";
	rename -uid "4085EE5B-4B44-EDC9-1C2D-E2B71FDB22C5";
	setAttr -k off ".v";
	setAttr ".lodv" no;
	setAttr ".tw" yes;
	setAttr -s 11 ".cp[1:10]" -type "double3" 0 1.1398097076581033 0 0 
		0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
createNode parentConstraint -n "ctrl_horizontalCam_up_MOVE_parentConstraint1" -p "ctrl_horizontalCam_up_MOVE";
	rename -uid "52D43C85-4084-629F-C936-14A7E6A3D198";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_shakeW0" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_rootW1" -dv 1 -min 0 -at "double";
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
	setAttr ".tg[0].tot" -type "double3" 0 0 -1.3333333333333333 ;
	setAttr ".tg[1].tot" -type "double3" 0 0 -1.3333333333333333 ;
	setAttr -k on ".w0";
	setAttr -k on ".w1" 0;
createNode transform -n "ctrl_distance_OFFSET" -p "controls";
	rename -uid "5DD88FB6-454A-E5C9-BF61-E69FBF7ED587";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_distance_MOVE" -p "ctrl_distance_OFFSET";
	rename -uid "50914E0C-444B-D9B1-2F58-C29A7C2A5E19";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_distance" -p "ctrl_distance_MOVE";
	rename -uid "303D5529-49EB-8E7F-E19C-B1BD407D775E";
	addAttr -ci true -sn "distanceToCam" -ln "distanceToCam" -nn "Distance" -at "double";
	addAttr -ci true -sn "parent" -ln "parent" -min 0 -max 2 -en "General:Root:Shake" 
		-at "enum";
	setAttr -k off ".v";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -k on ".distanceToCam";
	setAttr -k on ".parent";
createNode nurbsCurve -n "ctrl_distanceShape" -p "ctrl_distance";
	rename -uid "A92DF2AD-4DE1-51A6-71A9-589779940925";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 1 0.125 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 59 0 no 3
		60 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54
		 55 56 57 58 59
		60
		0.36544599999999999 0 -1.7372460000000001
		0 0 -1.979341
		-0.36544599999999999 0 -1.7372460000000001
		0 0 -3.2729180000000002
		0.36544599999999999 0 -1.7372460000000001
		0 0 -1.979341
		0 0.36544599999999999 -1.7372460000000001
		0 0 -3.2729180000000002
		0 -0.36544599999999999 -1.7372460000000001
		0 0 -1.979341
		0 0 0
		0 0 1.979341
		-0.36544599999999999 0 1.7372460000000001
		0 0 3.2729180000000002
		0.36544599999999999 0 1.7372460000000001
		0 0 1.979341
		0 -0.36544599999999999 1.7372460000000001
		0 0 3.2729180000000002
		0 0.36544599999999999 1.7372460000000001
		0 0 1.979341
		0 0 0
		1.979341 0 0
		1.7372460000000001 0 0.36544599999999999
		3.2729180000000002 0 0
		1.7372460000000001 0 -0.36544599999999999
		1.979341 0 0
		1.7372460000000001 0.36544599999999999 0
		3.2729180000000002 0 0
		1.7372460000000001 -0.36544599999999999 0
		1.979341 0 0
		0 0 0
		-1.979341 0 0
		-1.7372460000000001 0 0.36544599999999999
		-3.2729180000000002 0 0
		-1.7372460000000001 0 -0.36544599999999999
		-1.979341 0 0
		-1.7372460000000001 0.36544599999999999 0
		-3.2729180000000002 0 0
		-1.7372460000000001 -0.36544599999999999 0
		-1.979341 0 0
		0 0 0
		0 1.979341 0
		-0.36544599999999999 1.7372460000000001 0
		0 3.2729180000000002 0
		0.36544599999999999 1.7372460000000001 0
		0 1.979341 0
		0 1.7372460000000001 0.36544599999999999
		0 3.2729180000000002 0
		0 1.7372460000000001 -0.36544599999999999
		0 1.979341 0
		0 0 0
		0 -1.979341 0
		-0.36544599999999999 -1.7372460000000001 0
		0 -3.2729180000000002 0
		0.36544599999999999 -1.7372460000000001 0
		0 -1.979341 0
		0 -1.7372460000000001 -0.36544599999999999
		0 -3.2729180000000002 0
		0 -1.7372460000000001 0.36544599999999999
		0 -1.979341 0
		;
createNode parentConstraint -n "ctrl_distance_OFFSET_parentConstraint1" -p "ctrl_distance_OFFSET";
	rename -uid "0723BB4A-4AA7-4A68-0B3A-B0912BE1BCEE";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_generalW0" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w1" -ln "ctrl_rootW1" -dv 1 -min 0 -at "double";
	addAttr -dcb 0 -ci true -k true -sn "w2" -ln "ctrl_shakeW2" -dv 1 -min 0 -at "double";
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
createNode transform -n "ctrl_breathingCam_MOVE" -p "controls";
	rename -uid "F87F8FC1-4E2D-60F3-D323-25932CB894B5";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_breathingCam" -p "ctrl_breathingCam_MOVE";
	rename -uid "3FC229A8-43C9-6DD7-8CB9-45B8AF40BE0A";
	setAttr -k off ".v";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode nurbsCurve -n "ctrl_breathingCamShape" -p "ctrl_breathingCam";
	rename -uid "8E715C55-4FA5-8D9B-EBC5-83960632068E";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.5 0.5 0.5 ;
	setAttr ".tw" yes;
	setAttr -s 11 ".cp[0:10]" -type "double3" 7.616276428252502 7.6162764282525046 
		0 6.5953606990088789e-16 10.771041419617205 0 -7.616276428252502 7.6162764282525028 
		0 -10.771041419617207 4.0114160832490064e-15 0 -7.616276428252502 -7.616276428252502 
		0 -1.0789425856555902e-15 -10.771041419617209 0 7.616276428252502 -7.6162764282525028 
		0 10.771041419617207 1.9842002786553737e-15 0 0 0 0 0 0 0 0 0 0;
createNode parentConstraint -n "ctrl_breathingCam_MOVE_parentConstraint1" -p "ctrl_breathingCam_MOVE";
	rename -uid "3657E12C-45D1-BF3F-B3FC-8D95B2A60990";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_shakeW0" -dv 1 -min 0 -at "double";
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
createNode transform -n "constraints" -p "rig";
	rename -uid "0E9B1CC4-4E7D-861C-2F47-FA82668CD058";
createNode parentConstraint -n "camera_pConstraint" -p "constraints";
	rename -uid "A022A055-4B32-EBAA-9E9F-CCADBB4577EB";
	addAttr -dcb 0 -ci true -k true -sn "w0" -ln "ctrl_camW0" -dv 1 -min 0 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr ".t" -type "double3" 0 0 0.083164444013954841 ;
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
createNode condition -n "cond_refsMOVE_general";
	rename -uid "8E7F8FF9-46C1-A1C6-35C9-E0BAA43DEDBE";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_refsMOVE_root";
	rename -uid "13B98163-4689-87A9-4BD7-A19F5B56252B";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode remapValue -n "remapVal_viewGrid_tZ";
	rename -uid "C8996764-41B3-68A0-898C-A5A6BE072F52";
	setAttr ".imn" 12;
	setAttr ".imx" 200;
	setAttr ".omx" -1.8250000476837158;
	setAttr -s 2 ".vl[0:1]"  0 0 1 1 1 1;
	setAttr -s 2 ".cl";
	setAttr ".cl[0].clp" 0;
	setAttr ".cl[0].clc" -type "float3" 0 0 0 ;
	setAttr ".cl[0].cli" 1;
	setAttr ".cl[1].clp" 1;
	setAttr ".cl[1].clc" -type "float3" 1 1 1 ;
	setAttr ".cl[1].cli" 1;
createNode condition -n "cond_grid_scope";
	rename -uid "AE0DCAEE-4601-5784-D33E-3287B80484C0";
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_grid_HD";
	rename -uid "C34BEDE6-4008-C369-5E39-A790DDDC9A94";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_grid_square";
	rename -uid "852A311E-450A-4BAC-29D0-2C82A9607F58";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_grid_squareIllogic";
	rename -uid "0204498F-4591-B144-C0BE-27A55802A33C";
	setAttr ".st" 3;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_horizontal_bool";
	rename -uid "A5EAC3E7-4D5D-E07D-AD16-088C284B4D7E";
	setAttr ".op" 3;
createNode condition -n "cond_aim_bool";
	rename -uid "1DE8A127-40DD-8275-3AF3-01BBCA88D2B6";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode plusMinusAverage -n "PMA_breathingCam_intensityValueBalance_pConShake";
	rename -uid "F6854650-46AB-287E-5231-5FB77C6167BD";
	setAttr -s 2 ".i1";
	setAttr -s 2 ".i1";
createNode condition -n "cond_brethingCam_onOFF";
	rename -uid "484455D5-4295-068C-C36C-F6B5B637C2F9";
	setAttr ".cf" -type "float3" 1 0 1 ;
createNode reverse -n "rev_breathingCam_intensity";
	rename -uid "4C249A9E-4891-9635-4C38-73B1C65E1B1C";
createNode multiplyDivide -n "multDiv_breathingCam_onOFF";
	rename -uid "E6B365F5-4495-1A26-2472-13951480816D";
createNode condition -n "cond_aimParent_root";
	rename -uid "65A6373D-469E-781B-5BC0-0489AFC79983";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimParent_general";
	rename -uid "12772F9E-4342-F47E-08D5-1B9C7B2A057A";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode plusMinusAverage -n "PMA_objectUp_visibility_logicGate";
	rename -uid "56C54E56-4082-B181-9C8F-BF8C112D5AE9";
	setAttr -s 2 ".i1";
	setAttr -s 2 ".i1";
createNode condition -n "cond_objectUp_ctrl_visibility";
	rename -uid "EDF83EB8-474A-1509-5EA0-7F852269EC81";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_objectUpRoation_ctrl_visibility";
	rename -uid "19FAEAF2-46A9-6930-2B24-A7B2A10FE9B1";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_objectUp_parent_aim";
	rename -uid "5B79A60A-491A-2A88-DE85-B789AC11B3A4";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_objectUp_parent_root";
	rename -uid "E0F02EB3-404A-683D-BD1F-D99506A3487E";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode makeNurbCircle -n "makeNurbCircle3";
	rename -uid "EBC093A8-4DFE-BDBB-7A1B-B1BE690653EC";
	setAttr ".nr" -type "double3" 0 0 0 ;
createNode distanceBetween -n "distanceBetween1";
	rename -uid "8CC6CCE6-4803-C378-064D-FFA008C3963D";
createNode condition -n "cond_distanceGeneral_dist";
	rename -uid "2796DB0C-4F13-F764-8C44-FEAAD93C8DA6";
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_distanceRoot_dist";
	rename -uid "836231DE-40D0-C7E0-3895-B9B15CE1DD58";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_distanceShake_dist";
	rename -uid "5D3C61F4-4104-33B2-CB70-6DAE16859076";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode animCurveTL -n "ctrl_breathingCam_translateX";
	rename -uid "5E5E672D-43E3-0442-DD5D-7D80DFF802C1";
	setAttr ".tan" 1;
	setAttr ".wgt" no;
	setAttr -s 9 ".ktv[0:8]"  1042.7083333333333 0 1093.75 -0.49972949895265623
		 1145.8333333333333 0 1197.9166666666667 -0.33647694133196432 1250 0 1302.0833333333333 0.12450560958020782
		 1354.1666666666667 0 1406.25 0.23856600193368582 1458.3333333333333 0;
	setAttr -s 9 ".kit[1:8]"  18 1 18 1 1 1 18 1;
	setAttr -s 9 ".kot[1:8]"  18 1 18 1 1 1 18 1;
	setAttr -s 9 ".kix[0:8]"  0.98028547888264805 1 0.98005821195681075 
		1 0.9796455541214546 0.99379214572437091 0.99359407167096125 1 0.97488076050086581;
	setAttr -s 9 ".kiy[0:8]"  -0.19758638589694782 0 0.19871059653682069 
		0 -0.20073511972265398 0.11125273523177165 -0.11300805608592986 0 -0.22272741817130115;
	setAttr -s 9 ".kox[0:8]"  0.98028549451515201 1 0.98005821723136333 
		1 0.97964554468693499 0.99379214689793538 0.99359407278663758 1 0.97488074062149366;
	setAttr -s 9 ".koy[0:8]"  -0.19758630833937862 0 0.1987105705222596 
		0 -0.20073516576583822 0.11125272474862194 -0.1130080462766348 0 -0.22272750518354925;
	setAttr ".pre" 3;
	setAttr ".pst" 3;
createNode animCurveTL -n "ctrl_breathingCam_translateY";
	rename -uid "D739112A-4C09-B4D4-3F3D-24B5334927F8";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 5 ".ktv[0:4]"  1042.7083333333333 0 1145.8333333333333 0.48648663405050058
		 1250 0 1354.1666666666667 0.48648663405050058 1458.3333333333333 0;
	setAttr ".pre" 3;
	setAttr ".pst" 3;
createNode animCurveTL -n "ctrl_breathingCam_translateZ";
	rename -uid "36204D5F-4903-ED7E-E20E-3982198C46E3";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 8 ".ktv[0:7]"  1042.7083333333333 0.083164444013954841
		 1093.75 0.072756498100408643 1197.9166666666667 0.09357238992750104 1250 0.083164444013954841
		 1302.0833333333333 0.072756498100408643 1354.1666666666667 0.083164444013954869 1406.25 0.09357238992750104
		 1458.3333333333333 0.083164444013954841;
	setAttr -s 8 ".kit[0:7]"  1 18 18 1 18 18 18 18;
	setAttr -s 8 ".kot[0:7]"  1 18 18 1 18 18 18 18;
	setAttr -s 8 ".kix[0:7]"  0.99997430355709682 1 1 0.99997484345183951 
		1 0.99998752115463263 1 1;
	setAttr -s 8 ".kiy[0:7]"  -0.0071688371092721035 0 0 -0.0070931279044777907 
		0 0.0049957516965113075 0 0;
	setAttr -s 8 ".kox[0:7]"  0.99997430355799199 1 1 0.9999748434549649 
		1 0.99998752115463263 1 1;
	setAttr -s 8 ".koy[0:7]"  -0.0071688369843920571 0 0 -0.007093127463840835 
		0 0.0049957516965113075 0 0;
	setAttr ".pre" 3;
	setAttr ".pst" 3;
createNode makeNurbCircle -n "makeNurbCircle2";
	rename -uid "CDCD38FB-4C04-CA5A-1127-55B18F30F572";
	setAttr ".nr" -type "double3" 0 0 0 ;
	setAttr ".r" 10;
select -ne :time1;
	setAttr ".o" 1;
	setAttr ".unw" 1;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".aoon" yes;
	setAttr ".msaa" yes;
	setAttr ".dli" 1;
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
	setAttr -s 25 ".u";
select -ne :defaultRenderingList1;
select -ne :standardSurface1;
	setAttr ".bc" -type "float3" 0.40000001 0.40000001 0.40000001 ;
	setAttr ".sr" 0.40000000596046448;
select -ne :initialShadingGroup;
	setAttr -s 3 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr ".imfkey" -type "string" "exr";
	setAttr ".dss" -type "string" "lambert1";
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
connectAttr "ctrl_general.camShape" "shotCam.lodv";
connectAttr "ctrl_cam.focalLength" "shotCamShape.fl";
connectAttr "ctrl_cam.fStop" "shotCamShape.fs";
connectAttr "ctrl_cam.focusDistance" "shotCamShape.fd";
connectAttr "ctrl_cam.dof" "shotCamShape.dof";
connectAttr "ctrl_cam.farClipPlane" "shotCamShape.fcp";
connectAttr "ctrl_cam.nearClipPlane" "shotCamShape.ncp";
connectAttr "ctrl_general.refVisibility" "refs.v";
connectAttr "imagePlane_refs_MOVE_parentConstraint1.ctx" "imagePlane_refs_MOVE.tx"
		;
connectAttr "imagePlane_refs_MOVE_parentConstraint1.cty" "imagePlane_refs_MOVE.ty"
		;
connectAttr "imagePlane_refs_MOVE_parentConstraint1.ctz" "imagePlane_refs_MOVE.tz"
		;
connectAttr "imagePlane_refs_MOVE_parentConstraint1.crx" "imagePlane_refs_MOVE.rx"
		;
connectAttr "imagePlane_refs_MOVE_parentConstraint1.cry" "imagePlane_refs_MOVE.ry"
		;
connectAttr "imagePlane_refs_MOVE_parentConstraint1.crz" "imagePlane_refs_MOVE.rz"
		;
connectAttr ":defaultColorMgtGlobals.cme" "imagePlane_ref_Shape1.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "imagePlane_ref_Shape1.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "imagePlane_ref_Shape1.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "imagePlane_ref_Shape1.ws";
connectAttr ":perspShape.msg" "imagePlane_ref_Shape1.ltc";
connectAttr "imagePlane_refs_MOVE.ro" "imagePlane_refs_MOVE_parentConstraint1.cro"
		;
connectAttr "imagePlane_refs_MOVE.pim" "imagePlane_refs_MOVE_parentConstraint1.cpim"
		;
connectAttr "imagePlane_refs_MOVE.rp" "imagePlane_refs_MOVE_parentConstraint1.crp"
		;
connectAttr "imagePlane_refs_MOVE.rpt" "imagePlane_refs_MOVE_parentConstraint1.crt"
		;
connectAttr "ctrl_general.t" "imagePlane_refs_MOVE_parentConstraint1.tg[0].tt";
connectAttr "ctrl_general.rp" "imagePlane_refs_MOVE_parentConstraint1.tg[0].trp"
		;
connectAttr "ctrl_general.rpt" "imagePlane_refs_MOVE_parentConstraint1.tg[0].trt"
		;
connectAttr "ctrl_general.r" "imagePlane_refs_MOVE_parentConstraint1.tg[0].tr";
connectAttr "ctrl_general.ro" "imagePlane_refs_MOVE_parentConstraint1.tg[0].tro"
		;
connectAttr "ctrl_general.s" "imagePlane_refs_MOVE_parentConstraint1.tg[0].ts";
connectAttr "ctrl_general.pm" "imagePlane_refs_MOVE_parentConstraint1.tg[0].tpm"
		;
connectAttr "imagePlane_refs_MOVE_parentConstraint1.w0" "imagePlane_refs_MOVE_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_root.t" "imagePlane_refs_MOVE_parentConstraint1.tg[1].tt";
connectAttr "ctrl_root.rp" "imagePlane_refs_MOVE_parentConstraint1.tg[1].trp";
connectAttr "ctrl_root.rpt" "imagePlane_refs_MOVE_parentConstraint1.tg[1].trt";
connectAttr "ctrl_root.r" "imagePlane_refs_MOVE_parentConstraint1.tg[1].tr";
connectAttr "ctrl_root.ro" "imagePlane_refs_MOVE_parentConstraint1.tg[1].tro";
connectAttr "ctrl_root.s" "imagePlane_refs_MOVE_parentConstraint1.tg[1].ts";
connectAttr "ctrl_root.pm" "imagePlane_refs_MOVE_parentConstraint1.tg[1].tpm";
connectAttr "imagePlane_refs_MOVE_parentConstraint1.w1" "imagePlane_refs_MOVE_parentConstraint1.tg[1].tw"
		;
connectAttr "cond_refsMOVE_general.ocr" "imagePlane_refs_MOVE_parentConstraint1.w0"
		;
connectAttr "cond_refsMOVE_root.ocr" "imagePlane_refs_MOVE_parentConstraint1.w1"
		;
connectAttr "ctrl_general.sy" "ctrl_general.sx" -l on;
connectAttr "ctrl_general.sy" "ctrl_general.sz" -l on;
connectAttr "ctrl_general.controls" "ctrl_root.v";
connectAttr "ctrl_shake_MOVE_aimConstraint1.crx" "ctrl_shake_MOVE.rx";
connectAttr "ctrl_shake_MOVE_aimConstraint1.cry" "ctrl_shake_MOVE.ry";
connectAttr "ctrl_shake_MOVE_aimConstraint1.crz" "ctrl_shake_MOVE.rz";
connectAttr "ctrl_general.Aim" "ctrl_shake_MOVE_aimConstraint1.w0";
connectAttr "ctrl_shake_MOVE.pim" "ctrl_shake_MOVE_aimConstraint1.cpim";
connectAttr "ctrl_shake_MOVE.t" "ctrl_shake_MOVE_aimConstraint1.ct";
connectAttr "ctrl_shake_MOVE.rp" "ctrl_shake_MOVE_aimConstraint1.crp";
connectAttr "ctrl_shake_MOVE.rpt" "ctrl_shake_MOVE_aimConstraint1.crt";
connectAttr "ctrl_shake_MOVE.ro" "ctrl_shake_MOVE_aimConstraint1.cro";
connectAttr "ctrl_aim.t" "ctrl_shake_MOVE_aimConstraint1.tg[0].tt";
connectAttr "ctrl_aim.rp" "ctrl_shake_MOVE_aimConstraint1.tg[0].trp";
connectAttr "ctrl_aim.rpt" "ctrl_shake_MOVE_aimConstraint1.tg[0].trt";
connectAttr "ctrl_aim.pm" "ctrl_shake_MOVE_aimConstraint1.tg[0].tpm";
connectAttr "ctrl_shake_MOVE_aimConstraint1.w0" "ctrl_shake_MOVE_aimConstraint1.tg[0].tw"
		;
connectAttr "ctrl_aim_objectUp.wm" "ctrl_shake_MOVE_aimConstraint1.wum";
connectAttr "ctrl_aim.worldUpVectorX" "ctrl_shake_MOVE_aimConstraint1.wux";
connectAttr "ctrl_aim.worldUpVectorY" "ctrl_shake_MOVE_aimConstraint1.wuy";
connectAttr "ctrl_aim.worldUpVectorZ" "ctrl_shake_MOVE_aimConstraint1.wuz";
connectAttr "ctrl_aim.aimUpVector" "ctrl_shake_MOVE_aimConstraint1.wut";
connectAttr "pCon_ctrl_cam_HOOK.ctx" "ctrl_cam_HOOK.tx";
connectAttr "pCon_ctrl_cam_HOOK.cty" "ctrl_cam_HOOK.ty";
connectAttr "pCon_ctrl_cam_HOOK.ctz" "ctrl_cam_HOOK.tz";
connectAttr "pCon_ctrl_cam_HOOK.crx" "ctrl_cam_HOOK.rx";
connectAttr "pCon_ctrl_cam_HOOK.cry" "ctrl_cam_HOOK.ry";
connectAttr "pCon_ctrl_cam_HOOK.crz" "ctrl_cam_HOOK.rz";
connectAttr "ctrl_cam_MOVE_aimConstraint1.crx" "ctrl_cam_MOVE.rx";
connectAttr "ctrl_cam_MOVE_aimConstraint1.cry" "ctrl_cam_MOVE.ry";
connectAttr "ctrl_cam_MOVE_aimConstraint1.crz" "ctrl_cam_MOVE.rz";
connectAttr "ctrl_general.controls" "ctrl_cam.v" -l on;
connectAttr "ctrl_general.s" "ctrl_cam.s";
connectAttr "remapVal_viewGrid_tZ.ov" "geo_grid_MOVE.tz";
connectAttr "ctrl_cam.gridVisibility" "geo_grid_MOVE.v";
connectAttr "cond_grid_scope.ocr" "geo_grid_scope.v";
connectAttr "cond_grid_HD.ocr" "geo_grid_HD.v";
connectAttr "cond_grid_square.ocr" "geo_grid_square.v";
connectAttr "cond_grid_squareIllogic.ocr" "imagePlane_squareIllogic.v";
connectAttr ":defaultColorMgtGlobals.cme" "imagePlane_squareIllogicShape.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "imagePlane_squareIllogicShape.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "imagePlane_squareIllogicShape.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "imagePlane_squareIllogicShape.ws";
connectAttr "shotCamShape.msg" "imagePlane_squareIllogicShape.ltc";
connectAttr "cond_horizontal_bool.ocr" "ctrl_cam_MOVE_aimConstraint1.w1";
connectAttr "ctrl_cam_MOVE.pim" "ctrl_cam_MOVE_aimConstraint1.cpim";
connectAttr "ctrl_cam_MOVE.t" "ctrl_cam_MOVE_aimConstraint1.ct";
connectAttr "ctrl_cam_MOVE.rp" "ctrl_cam_MOVE_aimConstraint1.crp";
connectAttr "ctrl_cam_MOVE.rpt" "ctrl_cam_MOVE_aimConstraint1.crt";
connectAttr "ctrl_cam_MOVE.ro" "ctrl_cam_MOVE_aimConstraint1.cro";
connectAttr "ctrl_aim.t" "ctrl_cam_MOVE_aimConstraint1.tg[0].tt";
connectAttr "ctrl_aim.rp" "ctrl_cam_MOVE_aimConstraint1.tg[0].trp";
connectAttr "ctrl_aim.rpt" "ctrl_cam_MOVE_aimConstraint1.tg[0].trt";
connectAttr "ctrl_aim.pm" "ctrl_cam_MOVE_aimConstraint1.tg[0].tpm";
connectAttr "ctrl_cam_MOVE_aimConstraint1.w0" "ctrl_cam_MOVE_aimConstraint1.tg[0].tw"
		;
connectAttr "ctrl_horizontalCam_up.t" "ctrl_cam_MOVE_aimConstraint1.tg[1].tt";
connectAttr "ctrl_horizontalCam_up.rp" "ctrl_cam_MOVE_aimConstraint1.tg[1].trp";
connectAttr "ctrl_horizontalCam_up.rpt" "ctrl_cam_MOVE_aimConstraint1.tg[1].trt"
		;
connectAttr "ctrl_horizontalCam_up.pm" "ctrl_cam_MOVE_aimConstraint1.tg[1].tpm";
connectAttr "ctrl_cam_MOVE_aimConstraint1.w1" "ctrl_cam_MOVE_aimConstraint1.tg[1].tw"
		;
connectAttr "ctrl_cam_HOOK.ro" "pCon_ctrl_cam_HOOK.cro";
connectAttr "ctrl_cam_HOOK.pim" "pCon_ctrl_cam_HOOK.cpim";
connectAttr "ctrl_cam_HOOK.rp" "pCon_ctrl_cam_HOOK.crp";
connectAttr "ctrl_cam_HOOK.rpt" "pCon_ctrl_cam_HOOK.crt";
connectAttr "ctrl_shake.t" "pCon_ctrl_cam_HOOK.tg[0].tt";
connectAttr "ctrl_shake.rp" "pCon_ctrl_cam_HOOK.tg[0].trp";
connectAttr "ctrl_shake.rpt" "pCon_ctrl_cam_HOOK.tg[0].trt";
connectAttr "ctrl_shake.r" "pCon_ctrl_cam_HOOK.tg[0].tr";
connectAttr "ctrl_shake.ro" "pCon_ctrl_cam_HOOK.tg[0].tro";
connectAttr "ctrl_shake.s" "pCon_ctrl_cam_HOOK.tg[0].ts";
connectAttr "ctrl_shake.pm" "pCon_ctrl_cam_HOOK.tg[0].tpm";
connectAttr "pCon_ctrl_cam_HOOK.w0" "pCon_ctrl_cam_HOOK.tg[0].tw";
connectAttr "ctrl_breathingCam.t" "pCon_ctrl_cam_HOOK.tg[1].tt";
connectAttr "ctrl_breathingCam.rp" "pCon_ctrl_cam_HOOK.tg[1].trp";
connectAttr "ctrl_breathingCam.rpt" "pCon_ctrl_cam_HOOK.tg[1].trt";
connectAttr "ctrl_breathingCam.r" "pCon_ctrl_cam_HOOK.tg[1].tr";
connectAttr "ctrl_breathingCam.ro" "pCon_ctrl_cam_HOOK.tg[1].tro";
connectAttr "ctrl_breathingCam.s" "pCon_ctrl_cam_HOOK.tg[1].ts";
connectAttr "ctrl_breathingCam.pm" "pCon_ctrl_cam_HOOK.tg[1].tpm";
connectAttr "pCon_ctrl_cam_HOOK.w1" "pCon_ctrl_cam_HOOK.tg[1].tw";
connectAttr "PMA_breathingCam_intensityValueBalance_pConShake.o1" "pCon_ctrl_cam_HOOK.w0"
		;
connectAttr "multDiv_breathingCam_onOFF.ox" "pCon_ctrl_cam_HOOK.w1";
connectAttr "ctrl_aim_MOVE_parentConstraint1.ctx" "ctrl_aim_MOVE.tx";
connectAttr "ctrl_aim_MOVE_parentConstraint1.cty" "ctrl_aim_MOVE.ty";
connectAttr "ctrl_aim_MOVE_parentConstraint1.ctz" "ctrl_aim_MOVE.tz";
connectAttr "ctrl_aim_MOVE_parentConstraint1.crx" "ctrl_aim_MOVE.rx";
connectAttr "ctrl_aim_MOVE_parentConstraint1.cry" "ctrl_aim_MOVE.ry";
connectAttr "ctrl_aim_MOVE_parentConstraint1.crz" "ctrl_aim_MOVE.rz";
connectAttr "ctrl_general.Aim" "ctrl_aim.v" -l on;
connectAttr "ctrl_general.s" "ctrl_aim.s";
connectAttr "ctrl_general.sy" "ctrl_aim.sy" -l on;
connectAttr "ctrl_general.sy" "ctrl_aim.sx" -l on;
connectAttr "ctrl_general.sy" "ctrl_aim.sz" -l on;
connectAttr "ctrl_aim_MOVE.ro" "ctrl_aim_MOVE_parentConstraint1.cro";
connectAttr "ctrl_aim_MOVE.pim" "ctrl_aim_MOVE_parentConstraint1.cpim";
connectAttr "ctrl_aim_MOVE.rp" "ctrl_aim_MOVE_parentConstraint1.crp";
connectAttr "ctrl_aim_MOVE.rpt" "ctrl_aim_MOVE_parentConstraint1.crt";
connectAttr "ctrl_root.t" "ctrl_aim_MOVE_parentConstraint1.tg[0].tt";
connectAttr "ctrl_root.rp" "ctrl_aim_MOVE_parentConstraint1.tg[0].trp";
connectAttr "ctrl_root.rpt" "ctrl_aim_MOVE_parentConstraint1.tg[0].trt";
connectAttr "ctrl_root.r" "ctrl_aim_MOVE_parentConstraint1.tg[0].tr";
connectAttr "ctrl_root.ro" "ctrl_aim_MOVE_parentConstraint1.tg[0].tro";
connectAttr "ctrl_root.s" "ctrl_aim_MOVE_parentConstraint1.tg[0].ts";
connectAttr "ctrl_root.pm" "ctrl_aim_MOVE_parentConstraint1.tg[0].tpm";
connectAttr "ctrl_aim_MOVE_parentConstraint1.w0" "ctrl_aim_MOVE_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_general.t" "ctrl_aim_MOVE_parentConstraint1.tg[1].tt";
connectAttr "ctrl_general.rp" "ctrl_aim_MOVE_parentConstraint1.tg[1].trp";
connectAttr "ctrl_general.rpt" "ctrl_aim_MOVE_parentConstraint1.tg[1].trt";
connectAttr "ctrl_general.r" "ctrl_aim_MOVE_parentConstraint1.tg[1].tr";
connectAttr "ctrl_general.ro" "ctrl_aim_MOVE_parentConstraint1.tg[1].tro";
connectAttr "ctrl_general.s" "ctrl_aim_MOVE_parentConstraint1.tg[1].ts";
connectAttr "ctrl_general.pm" "ctrl_aim_MOVE_parentConstraint1.tg[1].tpm";
connectAttr "ctrl_aim_MOVE_parentConstraint1.w1" "ctrl_aim_MOVE_parentConstraint1.tg[1].tw"
		;
connectAttr "cond_aimParent_root.ocr" "ctrl_aim_MOVE_parentConstraint1.w0";
connectAttr "cond_aimParent_general.ocr" "ctrl_aim_MOVE_parentConstraint1.w1";
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.ctx" "ctrl_aim_objectUp_HOOK.tx"
		;
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.cty" "ctrl_aim_objectUp_HOOK.ty"
		;
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.ctz" "ctrl_aim_objectUp_HOOK.tz"
		;
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.crx" "ctrl_aim_objectUp_HOOK.rx"
		;
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.cry" "ctrl_aim_objectUp_HOOK.ry"
		;
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.crz" "ctrl_aim_objectUp_HOOK.rz"
		;
connectAttr "PMA_objectUp_visibility_logicGate.o1" "ctrl_aim_objectUp.v" -l on;
connectAttr "ctrl_general.s" "ctrl_aim_objectUp.s";
connectAttr "ctrl_aim_objectUp_HOOK.ro" "ctrl_aim_objectUp_HOOK_parentConstraint1.cro"
		;
connectAttr "ctrl_aim_objectUp_HOOK.pim" "ctrl_aim_objectUp_HOOK_parentConstraint1.cpim"
		;
connectAttr "ctrl_aim_objectUp_HOOK.rp" "ctrl_aim_objectUp_HOOK_parentConstraint1.crp"
		;
connectAttr "ctrl_aim_objectUp_HOOK.rpt" "ctrl_aim_objectUp_HOOK_parentConstraint1.crt"
		;
connectAttr "ctrl_aim.t" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].tt";
connectAttr "ctrl_aim.rp" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].trp";
connectAttr "ctrl_aim.rpt" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].trt";
connectAttr "ctrl_aim.r" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].tr";
connectAttr "ctrl_aim.ro" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].tro";
connectAttr "ctrl_aim.s" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].ts";
connectAttr "ctrl_aim.pm" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].tpm";
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.w0" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_root.t" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].tt";
connectAttr "ctrl_root.rp" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].trp";
connectAttr "ctrl_root.rpt" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].trt"
		;
connectAttr "ctrl_root.r" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].tr";
connectAttr "ctrl_root.ro" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].tro";
connectAttr "ctrl_root.s" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].ts";
connectAttr "ctrl_root.pm" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].tpm";
connectAttr "ctrl_aim_objectUp_HOOK_parentConstraint1.w1" "ctrl_aim_objectUp_HOOK_parentConstraint1.tg[1].tw"
		;
connectAttr "cond_objectUp_parent_aim.ocr" "ctrl_aim_objectUp_HOOK_parentConstraint1.w0"
		;
connectAttr "cond_objectUp_parent_root.ocr" "ctrl_aim_objectUp_HOOK_parentConstraint1.w1"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.ctx" "ctrl_horizontalCam_up_MOVE.tx"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.cty" "ctrl_horizontalCam_up_MOVE.ty"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.ctz" "ctrl_horizontalCam_up_MOVE.tz"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.crx" "ctrl_horizontalCam_up_MOVE.rx"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.cry" "ctrl_horizontalCam_up_MOVE.ry"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.crz" "ctrl_horizontalCam_up_MOVE.rz"
		;
connectAttr "makeNurbCircle3.oc" "ctrl_horizontalCam_upShape.cr";
connectAttr "ctrl_horizontalCam_up_MOVE.ro" "ctrl_horizontalCam_up_MOVE_parentConstraint1.cro"
		;
connectAttr "ctrl_horizontalCam_up_MOVE.pim" "ctrl_horizontalCam_up_MOVE_parentConstraint1.cpim"
		;
connectAttr "ctrl_horizontalCam_up_MOVE.rp" "ctrl_horizontalCam_up_MOVE_parentConstraint1.crp"
		;
connectAttr "ctrl_horizontalCam_up_MOVE.rpt" "ctrl_horizontalCam_up_MOVE_parentConstraint1.crt"
		;
connectAttr "ctrl_shake.t" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].tt"
		;
connectAttr "ctrl_shake.rp" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].trp"
		;
connectAttr "ctrl_shake.rpt" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].trt"
		;
connectAttr "ctrl_shake.r" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].tr"
		;
connectAttr "ctrl_shake.ro" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].tro"
		;
connectAttr "ctrl_shake.s" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].ts"
		;
connectAttr "ctrl_shake.pm" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].tpm"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.w0" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_root.t" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].tt"
		;
connectAttr "ctrl_root.rp" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].trp"
		;
connectAttr "ctrl_root.rpt" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].trt"
		;
connectAttr "ctrl_root.r" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].tr"
		;
connectAttr "ctrl_root.ro" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].tro"
		;
connectAttr "ctrl_root.s" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].ts"
		;
connectAttr "ctrl_root.pm" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].tpm"
		;
connectAttr "ctrl_horizontalCam_up_MOVE_parentConstraint1.w1" "ctrl_horizontalCam_up_MOVE_parentConstraint1.tg[1].tw"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.ctx" "ctrl_distance_OFFSET.tx"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.cty" "ctrl_distance_OFFSET.ty"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.ctz" "ctrl_distance_OFFSET.tz"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.crx" "ctrl_distance_OFFSET.rx"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.cry" "ctrl_distance_OFFSET.ry"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.crz" "ctrl_distance_OFFSET.rz"
		;
connectAttr "ctrl_cam.distance" "ctrl_distance.v";
connectAttr "ctrl_general.s" "ctrl_distance.s";
connectAttr "distanceBetween1.d" "ctrl_distance.distanceToCam";
connectAttr "ctrl_distance_OFFSET.ro" "ctrl_distance_OFFSET_parentConstraint1.cro"
		;
connectAttr "ctrl_distance_OFFSET.pim" "ctrl_distance_OFFSET_parentConstraint1.cpim"
		;
connectAttr "ctrl_distance_OFFSET.rp" "ctrl_distance_OFFSET_parentConstraint1.crp"
		;
connectAttr "ctrl_distance_OFFSET.rpt" "ctrl_distance_OFFSET_parentConstraint1.crt"
		;
connectAttr "ctrl_general.t" "ctrl_distance_OFFSET_parentConstraint1.tg[0].tt";
connectAttr "ctrl_general.rp" "ctrl_distance_OFFSET_parentConstraint1.tg[0].trp"
		;
connectAttr "ctrl_general.rpt" "ctrl_distance_OFFSET_parentConstraint1.tg[0].trt"
		;
connectAttr "ctrl_general.r" "ctrl_distance_OFFSET_parentConstraint1.tg[0].tr";
connectAttr "ctrl_general.ro" "ctrl_distance_OFFSET_parentConstraint1.tg[0].tro"
		;
connectAttr "ctrl_general.s" "ctrl_distance_OFFSET_parentConstraint1.tg[0].ts";
connectAttr "ctrl_general.pm" "ctrl_distance_OFFSET_parentConstraint1.tg[0].tpm"
		;
connectAttr "ctrl_distance_OFFSET_parentConstraint1.w0" "ctrl_distance_OFFSET_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_root.t" "ctrl_distance_OFFSET_parentConstraint1.tg[1].tt";
connectAttr "ctrl_root.rp" "ctrl_distance_OFFSET_parentConstraint1.tg[1].trp";
connectAttr "ctrl_root.rpt" "ctrl_distance_OFFSET_parentConstraint1.tg[1].trt";
connectAttr "ctrl_root.r" "ctrl_distance_OFFSET_parentConstraint1.tg[1].tr";
connectAttr "ctrl_root.ro" "ctrl_distance_OFFSET_parentConstraint1.tg[1].tro";
connectAttr "ctrl_root.s" "ctrl_distance_OFFSET_parentConstraint1.tg[1].ts";
connectAttr "ctrl_root.pm" "ctrl_distance_OFFSET_parentConstraint1.tg[1].tpm";
connectAttr "ctrl_distance_OFFSET_parentConstraint1.w1" "ctrl_distance_OFFSET_parentConstraint1.tg[1].tw"
		;
connectAttr "ctrl_shake.t" "ctrl_distance_OFFSET_parentConstraint1.tg[2].tt";
connectAttr "ctrl_shake.rp" "ctrl_distance_OFFSET_parentConstraint1.tg[2].trp";
connectAttr "ctrl_shake.rpt" "ctrl_distance_OFFSET_parentConstraint1.tg[2].trt";
connectAttr "ctrl_shake.r" "ctrl_distance_OFFSET_parentConstraint1.tg[2].tr";
connectAttr "ctrl_shake.ro" "ctrl_distance_OFFSET_parentConstraint1.tg[2].tro";
connectAttr "ctrl_shake.s" "ctrl_distance_OFFSET_parentConstraint1.tg[2].ts";
connectAttr "ctrl_shake.pm" "ctrl_distance_OFFSET_parentConstraint1.tg[2].tpm";
connectAttr "ctrl_distance_OFFSET_parentConstraint1.w2" "ctrl_distance_OFFSET_parentConstraint1.tg[2].tw"
		;
connectAttr "cond_distanceGeneral_dist.ocr" "ctrl_distance_OFFSET_parentConstraint1.w0"
		;
connectAttr "cond_distanceRoot_dist.ocr" "ctrl_distance_OFFSET_parentConstraint1.w1"
		;
connectAttr "cond_distanceShake_dist.ocr" "ctrl_distance_OFFSET_parentConstraint1.w2"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.ctx" "ctrl_breathingCam_MOVE.tx"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.cty" "ctrl_breathingCam_MOVE.ty"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.ctz" "ctrl_breathingCam_MOVE.tz"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.crx" "ctrl_breathingCam_MOVE.rx"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.cry" "ctrl_breathingCam_MOVE.ry"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.crz" "ctrl_breathingCam_MOVE.rz"
		;
connectAttr "ctrl_general.breathingCam" "ctrl_breathingCam.v" -l on;
connectAttr "ctrl_breathingCam_translateX.o" "ctrl_breathingCam.tx";
connectAttr "ctrl_breathingCam_translateY.o" "ctrl_breathingCam.ty";
connectAttr "ctrl_breathingCam_translateZ.o" "ctrl_breathingCam.tz";
connectAttr "makeNurbCircle2.oc" "ctrl_breathingCamShape.cr";
connectAttr "ctrl_breathingCam_MOVE.ro" "ctrl_breathingCam_MOVE_parentConstraint1.cro"
		;
connectAttr "ctrl_breathingCam_MOVE.pim" "ctrl_breathingCam_MOVE_parentConstraint1.cpim"
		;
connectAttr "ctrl_breathingCam_MOVE.rp" "ctrl_breathingCam_MOVE_parentConstraint1.crp"
		;
connectAttr "ctrl_breathingCam_MOVE.rpt" "ctrl_breathingCam_MOVE_parentConstraint1.crt"
		;
connectAttr "ctrl_shake.t" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].tt";
connectAttr "ctrl_shake.rp" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].trp"
		;
connectAttr "ctrl_shake.rpt" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].trt"
		;
connectAttr "ctrl_shake.r" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].tr";
connectAttr "ctrl_shake.ro" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].tro"
		;
connectAttr "ctrl_shake.s" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].ts";
connectAttr "ctrl_shake.pm" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].tpm"
		;
connectAttr "ctrl_breathingCam_MOVE_parentConstraint1.w0" "ctrl_breathingCam_MOVE_parentConstraint1.tg[0].tw"
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
connectAttr "ctrl_general.refParent" "cond_refsMOVE_general.ft";
connectAttr "ctrl_general.refParent" "cond_refsMOVE_root.ft";
connectAttr "ctrl_cam.focalLength" "remapVal_viewGrid_tZ.i";
connectAttr "ctrl_cam.gridType" "cond_grid_scope.ft";
connectAttr "ctrl_cam.gridType" "cond_grid_HD.ft";
connectAttr "ctrl_cam.gridType" "cond_grid_square.ft";
connectAttr "ctrl_cam.gridType" "cond_grid_squareIllogic.ft";
connectAttr "ctrl_general.horizontalCam" "cond_horizontal_bool.st";
connectAttr "cond_aim_bool.ocr" "cond_horizontal_bool.ft";
connectAttr "ctrl_general.Aim" "cond_aim_bool.ft";
connectAttr "cond_brethingCam_onOFF.ocg" "PMA_breathingCam_intensityValueBalance_pConShake.i1[0]"
		;
connectAttr "rev_breathingCam_intensity.oy" "PMA_breathingCam_intensityValueBalance_pConShake.i1[1]"
		;
connectAttr "ctrl_general.breathingCam" "cond_brethingCam_onOFF.ft";
connectAttr "ctrl_general.breathingCamIntensity" "cond_brethingCam_onOFF.ctg";
connectAttr "ctrl_general.breathingCamIntensity" "rev_breathingCam_intensity.iy"
		;
connectAttr "cond_brethingCam_onOFF.ocr" "multDiv_breathingCam_onOFF.i1x";
connectAttr "ctrl_general.breathingCamIntensity" "multDiv_breathingCam_onOFF.i2x"
		;
connectAttr "ctrl_general.aimParent" "cond_aimParent_root.ft";
connectAttr "ctrl_general.aimParent" "cond_aimParent_general.ft";
connectAttr "cond_objectUp_ctrl_visibility.ocr" "PMA_objectUp_visibility_logicGate.i1[0]"
		;
connectAttr "cond_objectUpRoation_ctrl_visibility.ocr" "PMA_objectUp_visibility_logicGate.i1[1]"
		;
connectAttr "ctrl_aim.aimUpVector" "cond_objectUp_ctrl_visibility.ft";
connectAttr "ctrl_aim.aimUpVector" "cond_objectUpRoation_ctrl_visibility.ft";
connectAttr "ctrl_aim_objectUp.objectUpParent" "cond_objectUp_parent_aim.ft";
connectAttr "ctrl_aim_objectUp.objectUpParent" "cond_objectUp_parent_root.ft";
connectAttr "shotCam.t" "distanceBetween1.p1";
connectAttr "ctrl_distance.t" "distanceBetween1.p2";
connectAttr "ctrl_distance.parent" "cond_distanceGeneral_dist.ft";
connectAttr "ctrl_distance.parent" "cond_distanceRoot_dist.ft";
connectAttr "ctrl_distance.parent" "cond_distanceShake_dist.ft";
connectAttr "cond_aimParent_root.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_refsMOVE_general.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_refsMOVE_root.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "remapVal_viewGrid_tZ.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_aim_bool.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_horizontal_bool.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "distanceBetween1.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_distanceGeneral_dist.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_distanceRoot_dist.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_distanceShake_dist.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "rev_breathingCam_intensity.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_brethingCam_onOFF.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "multDiv_breathingCam_onOFF.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "PMA_breathingCam_intensityValueBalance_pConShake.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_grid_scope.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_grid_HD.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_grid_square.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_aimParent_general.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_grid_squareIllogic.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_objectUp_parent_aim.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_objectUp_parent_root.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_objectUp_ctrl_visibility.msg" ":defaultRenderUtilityList1.u" -na
		;
connectAttr "cond_objectUpRoation_ctrl_visibility.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "PMA_objectUp_visibility_logicGate.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "geo_grid_scopeShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "geo_grid_HDShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "geo_grid_squareShape.iog" ":initialShadingGroup.dsm" -na;
// End of camRig.ma
