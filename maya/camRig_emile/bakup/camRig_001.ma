//Maya ASCII 2024 scene
//Name: camRig_001.ma
//Last modified: Sun, Oct 06, 2024 02:16:56 PM
//Codeset: 1252
requires maya "2024";
requires "stereoCamera" "10.0";
requires -nodeType "mayaUsdLayerManager" -dataType "pxrUsdStageData" "mayaUsdPlugin" "0.25.0";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2024";
fileInfo "version" "2024";
fileInfo "cutIdentifier" "202310181224-69282f2959";
fileInfo "osv" "Windows 10 Home v2009 (Build: 19045)";
fileInfo "UUID" "197C8F62-4D6B-615D-54DF-1E98FF966ECA";
createNode transform -s -n "persp";
	rename -uid "441DD6C9-4855-F603-2BD2-B6BD7F6BB9FA";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 134.33023331335772 77.594362825740532 -258.98569306171385 ;
	setAttr ".r" -type "double3" 345.86164720319232 -2727.7999999997769 0 ;
	setAttr ".rp" -type "double3" 2.7533531010703882e-14 -2.1552204465535851e-14 0 ;
	setAttr ".rpt" -type "double3" -3.7580368978924766e-14 1.9153958786610848e-15 -2.713023484241178e-14 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "42095434-4E1D-76DD-8214-1BBE9088A2FB";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".fl" 34.999999999999979;
	setAttr ".coi" 361.92722912728448;
	setAttr ".ow" 357.2483710893066;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
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
	setAttr ".fcp" 100000;
	setAttr ".coi" 0.51202404210276575;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".hc" -type "string" "viewSet -p %camera";
	setAttr ".dgo" 1;
	setAttr ".dr" yes;
	setAttr ".dgc" -type "float3" 0 0 0 ;
createNode parentConstraint -n "camera_parentConstraint1" -p "camera";
	rename -uid "A022A055-4B32-EBAA-9E9F-CCADBB4577EB";
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
		-max 0 -en "AIM" -at "enum";
	addAttr -ci true -sn "Aim" -ln "Aim" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "horizontalCam" -ln "horizontalCam" -nn "Horizontal Cam" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -sn "aimParent" -ln "aimParent" -min 0 -max 3 -en "World:General:Root:Shake" 
		-at "enum";
	addAttr -ci true -sn "horizontalParent" -ln "horizontalParent" -min 0 -max 1 -en 
		"Root:Shake" -at "enum";
	addAttr -ci true -sn "divider_imagePlanes" -ln "divider_imagePlanes" -nn " " -min 
		0 -max 0 -en "Reference" -at "enum";
	addAttr -ci true -sn "refVisibility" -ln "refVisibility" -nn "Image Planes" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -sn "refParent" -ln "refParent" -nn "Image Plane Parent" -min 0 
		-max 2 -en "World:General:Root" -at "enum";
	addAttr -ci true -sn "divider_visibility" -ln "divider_visibility" -nn " " -min 
		0 -max 0 -en "Visibility" -at "enum";
	addAttr -ci true -sn "camShape" -ln "camShape" -nn "Camera" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "controls" -ln "controls" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_breathingCam" -ln "divider_breathingCam" -nn " " -min 
		0 -max 0 -en "Breathing" -at "enum";
	addAttr -ci true -sn "breathingCam" -ln "breathingCam" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "breathingCamIntensity" -ln "breathingCamIntensity" -dv 1 -min 
		0 -max 1 -at "double";
	setAttr -l on -k off ".v";
	setAttr ".mnsl" -type "double3" 0.1 0.1 0.1 ;
	setAttr ".mxsl" -type "double3" 10 10 10 ;
	setAttr ".msxe" yes;
	setAttr ".msye" yes;
	setAttr ".msze" yes;
	setAttr -cb on ".divider_aimTarget";
	setAttr -k on ".Aim";
	setAttr -k on ".horizontalCam";
	setAttr -k on ".aimParent" 2;
	setAttr -k on ".horizontalParent" 1;
	setAttr -cb on ".divider_imagePlanes";
	setAttr -k on ".refVisibility";
	setAttr -k on ".refParent" 2;
	setAttr -cb on ".divider_visibility";
	setAttr -k on ".camShape";
	setAttr -k on ".controls" yes;
	setAttr -cb on ".divider_breathingCam";
	setAttr -k on ".breathingCam" yes;
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
		0 68.570991463064004 -6.6613381477509392e-15
		68.57099146306399 0 0
		0 -68.570991463064004 6.6613381477509392e-15
		-68.57099146306399 0 0
		0 68.570991463064004 -6.6613381477509392e-15
		;
createNode transform -n "ctrl_root_OFFSET" -p "ctrl_general";
	rename -uid "0030A882-4377-6DB4-8604-E5A1AE0E960E";
	setAttr ".s" -type "double3" 15 15 15 ;
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
		-1 2 -3.3306690738754696e-16
		-0.99999999999999978 2.5982347560814332 0
		-1.4000000000000004 2.5982347560814332 0
		0 4 -6.6613381477509392e-16
		1.3999999999999997 2.5982347560814332 0
		1 2.5982347560814332 0
		1 2 -3.3306690738754696e-16
		2 1 -1.6653345369377348e-16
		2.5982347560814332 1 5.5511151231257827e-17
		2.5982347560814332 1.3999999999999997 1.1102230246251565e-16
		4 0 0
		2.5982347560814332 -1.3999999999999995 -5.5511151231257827e-17
		2.5982347560814332 -1 1.6653345369377348e-16
		2 -1 1.6653345369377348e-16
		1 -2 3.3306690738754696e-16
		1 -2.5982347560814332 0
		1.3999999999999999 -2.5982347560814332 0
		0 -4 6.6613381477509392e-16
		-1.3999999999999999 -2.5982347560814332 0
		-1 -2.5982347560814332 0
		-1 -2 3.3306690738754696e-16
		-2 -1 1.6653345369377348e-16
		-2.5982347560814332 -1 1.6653345369377348e-16
		-2.5982347560814332 -1.3999999999999995 -5.5511151231257827e-17
		-4 0 0
		-2.5982347560814332 1.3999999999999997 1.1102230246251565e-16
		-2.5982347560814332 1 5.5511151231257827e-17
		-2 1 -1.6653345369377348e-16
		-1 2 -3.3306690738754696e-16
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
		-0.52687038988408852 2.0021074815595363 -2.2204460492503131e-16
		0.52687038988408852 2.0021074815595363 -2.2204460492503131e-16
		2.0021074815595363 0.52687038988408841 2.7755575615628914e-17
		2.0021074815595363 -0.52687038988408852 -2.7755575615628914e-17
		0.52687038988408841 -2.0021074815595363 2.2204460492503131e-16
		-0.52687038988408841 -2.0021074815595363 2.2204460492503131e-16
		-2.0021074815595363 -0.52687038988408852 -2.7755575615628914e-17
		-2.0021074815595363 0.52687038988408852 2.7755575615628914e-17
		-0.52687038988408852 2.0021074815595363 -2.2204460492503131e-16
		;
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
	addAttr -ci true -sn "divider_01" -ln "divider_01" -nn " " -min 0 -max 0 -en "DOF" 
		-at "enum";
	addAttr -ci true -sn "dof" -ln "dof" -nn "Depth of Field" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "focusDistance" -ln "focusDistance" -min 0 -at "double";
	addAttr -ci true -sn "fStop" -ln "fStop" -min 0 -at "double";
	addAttr -ci true -sn "divider_02" -ln "divider_02" -nn " " -min 0 -max 0 -en "Grid" 
		-at "enum";
	addAttr -ci true -sn "gridType" -ln "gridType" -min 0 -max 1 -en "Scope:HD" -at "enum";
	addAttr -ci true -sn "gridVisibility" -ln "gridVisibility" -nn "Grid Visibility" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -sn "divider_03" -ln "divider_03" -nn " " -min 0 -max 0 -en "Clip Plane" 
		-at "enum";
	addAttr -ci true -sn "Near" -ln "Near" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "Far" -ln "Far" -dv 100000 -min 0 -at "double";
	addAttr -ci true -sn "distance" -ln "distance" -min 0 -max 1 -at "bool";
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
	setAttr -k on ".focalLength";
	setAttr -cb on ".divider_01";
	setAttr -k on ".dof";
	setAttr -k on ".focusDistance" 5;
	setAttr -k on ".fStop" 5.6;
	setAttr -cb on ".divider_02";
	setAttr -k on ".gridType" 1;
	setAttr -k on ".gridVisibility" yes;
	setAttr -cb on ".divider_03";
	setAttr -k on ".Near";
	setAttr -k on ".Far";
	setAttr -k on ".distance";
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
		4.3801565707484174e-09 -0.44325853462496628 0.31916035136762189
		-0.31343111755147651 -0.31343112193163292 0.31916035136762189
		-0.44539777478657128 -0.44539777478657128 6.5468148680025706e-09
		-0.31343111127196926 -0.31343111565212578 0.31916035136762189
		-0.44325850943838152 -6.0960787844088692e-17 0.31916035136762166
		-0.62988753156759869 -3.1627648059793762e-17 6.5468148680025706e-09
		-0.44325850943838152 -6.0960787844088692e-17 0.31916035136762166
		-0.31343111755147651 0.31343112193163292 0.31916035136762166
		-0.44539777478657128 0.44539777478657128 6.5468148680025706e-09
		-0.31343111127196949 0.31343111565212561 0.31916035136762166
		4.3801563210395576e-09 0.44325851381853765 0.31916035136762166
		-3.1627648059793762e-17 0.62988753156759869 6.5468148680025706e-09
		4.3801563073156742e-09 0.44325853462496639 0.31916035136762166
		0.3134311263117896 0.31343112193163292 0.31916035136762166
		0.44539777478657128 0.44539777478657128 6.5468148680025706e-09
		0.31343112003228213 0.313431115652126 0.31916035136762166
		0.44325851819869427 2.9514657601295662e-16 0.31916035136762178
		0.62988753156759869 3.1627648059793762e-17 6.5468148680025706e-09
		0.44325853900512308 3.0596388852054944e-16 0.31916035136762178
		0.3134311263117896 -0.31343112193163292 0.31916035136762189
		0.44539777478657128 -0.44539777478657128 6.5468149790248731e-09
		0.31343112003228263 -0.31343111565212561 0.31916035136762189
		4.3801565881200805e-09 -0.44325851381853765 0.31916035136762189
		3.1627648059793762e-17 -0.62988753156759869 6.5468148680025706e-09
		4.3801569644410827e-09 -0.44325853462496645 0.31916035136762189
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
		3.8569489278295129e-17 -0.6298875611343403 2.0525733335219343e-08
		-0.44539776586314805 -0.44539776586314805 2.0525733335219343e-08
		-0.62988756113434041 -3.8569489278295135e-17 2.052573322419704e-08
		-0.44539776586314811 0.44539776586314811 2.0525733113174738e-08
		-3.8569489278295135e-17 0.62988756113434041 2.0525733113174738e-08
		0.44539776586314811 0.44539776586314811 2.0525733113174738e-08
		0.62988756113434041 3.8569489278295135e-17 2.052573322419704e-08
		0.44539776586314811 -0.44539776586314811 2.0525733335219343e-08
		3.8569489278295135e-17 -0.62988756113434041 2.0525733335219343e-08
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
		0.77175699805513198 -0.77175697778606112 0.31916035136762133
		0.77175698272607696 -0.7717570029951486 1.1608171338223954
		0.77175699805513198 -0.77175697778606112 0.31916035136762133
		-0.77175699805513198 -0.77175697778606112 0.31916035136762133
		-0.77175698272607696 -0.7717570029951486 1.1608186698703129
		-0.77175699805513198 -0.77175697778606112 0.31916035136762133
		-0.77175699805513198 0.77175697778606112 0.31916035136762222
		-0.77175698272607696 0.7717570029951486 1.1608182247963719
		-0.77175699805513198 0.77175697778606112 0.31916035136762222
		0.77175699805513198 0.77175697778606112 0.31916035136762222
		0.77175698272607696 0.7717570029951486 1.1608162693340192
		0.77175699805513198 0.77175697778606112 0.31916035136762222
		0.77175699805513198 -0.77175697778606112 0.31916035136762133
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
createNode aimConstraint -n "ctrl_cam_MOVE_aimConstraint1" -p "ctrl_cam_MOVE";
	rename -uid "B614C0C2-47DE-85FB-3F18-C1B48D17F054";
	addAttr -dcb 0 -ci true -sn "w0" -ln "ctrl_aimW0" -dv 1 -at "double";
	addAttr -dcb 0 -ci true -sn "w1" -ln "ctrl_upW1" -dv 1 -at "double";
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
	setAttr ".a" -type "double3" 0 0 1 ;
	setAttr ".wut" 0;
	setAttr ".o" -type "double3" 0 540 0 ;
	setAttr ".rsrr" -type "double3" 0 720 0 ;
	setAttr -k on ".w0";
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
	setAttr ".t" -type "double3" 0 0 -1 ;
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
	setAttr ".rp" -type "double3" 0 0 -1 ;
	setAttr ".sp" -type "double3" 0 0 -1 ;
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
		0.16480994269726534 0.16480994269726534 -1
		-0.16480994269726534 0.16480994269726534 -1
		-0.16480994269726534 -0.16480994269726534 -0.99999999999999989
		0.16480994269726534 -0.16480994269726534 -0.99999999999999989
		0.16480994269726534 0.16480994269726534 -1
		0 -1.7156390688685607e-16 -1.3340476883950181
		-0.16480994269726534 0.16480994269726534 -1
		-0.16480994269726534 -0.16480994269726534 -0.99999999999999989
		0 -1.7156390688685607e-16 -1.3340476883950181
		0.16480994269726534 -0.16480994269726534 -0.99999999999999989
		0.16480994269726534 0.16480994269726534 -1
		0 -1.7156390688685607e-16 -1.3340476883950181
		-0.16480994269726534 0.16480994269726534 -1
		;
createNode parentConstraint -n "ctrl_aim_HOOK_parentConstraint1" -p "ctrl_aim_HOOK";
	rename -uid "497AD52C-4089-2707-8A92-FD88FBF67B7F";
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
	setAttr ".tg[0].tot" -type "double3" 0 0 -1 ;
	setAttr ".tg[1].tot" -type "double3" 0 0 -1 ;
	setAttr ".tg[2].tot" -type "double3" 0 0 -1 ;
	setAttr -k on ".w0";
	setAttr -k on ".w1";
	setAttr -k on ".w2";
createNode transform -n "ctrl_up_OFFSET" -p "controls";
	rename -uid "E15D8C04-4FEF-7CCB-FD94-24BF04D5B444";
	setAttr ".t" -type "double3" 0 0 -16 ;
	setAttr ".r" -type "double3" -90.000000000000028 0 0 ;
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.89999998 0.30000001 0.60000002 ;
createNode transform -n "ctrl_up_MOVE" -p "ctrl_up_OFFSET";
	rename -uid "1097258D-4EAF-CED8-02FB-E88FCB8D1E20";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.69999999 0.60000002 1 ;
createNode transform -n "ctrl_up" -p "ctrl_up_MOVE";
	rename -uid "0B47ECAD-46A0-1BD5-7503-9A9EED60849C";
createNode nurbsCurve -n "ctrl_upShape" -p "ctrl_up";
	rename -uid "5412C716-4D4C-A89F-F256-F68612B4E086";
	setAttr -k off ".v";
	setAttr ".lodv" no;
	setAttr ".tw" yes;
createNode parentConstraint -n "ctrl_up_MOVE_parentConstraint1" -p "ctrl_up_MOVE";
	rename -uid "0DBA6667-47FD-4543-5F3A-FFAFCE9B0E62";
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
	setAttr ".tg[0].tot" -type "double3" 0 0 -1.0666666666666667 ;
	setAttr ".tg[0].tor" -type "double3" -90.000000000000028 0 0 ;
	setAttr ".tg[1].tot" -type "double3" 0 0 -1.0666666666666667 ;
	setAttr ".tg[1].tor" -type "double3" -90.000000000000028 0 0 ;
	setAttr -k on ".w0";
	setAttr -k on ".w1";
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
createNode condition -n "cond_grid_geoSwitch";
	rename -uid "AE0DCAEE-4601-5784-D33E-3287B80484C0";
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
createNode condition -n "cond_aimParent_general";
	rename -uid "3D68458A-46A8-CFB7-C475-559EEDECC5FB";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimParent_root";
	rename -uid "ED929928-4301-996A-146E-64AC22D5C4DD";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_aimParent_shake";
	rename -uid "65A6373D-469E-781B-5BC0-0489AFC79983";
	setAttr ".st" 3;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode makeNurbCircle -n "makeNurbCircle1";
	rename -uid "BF2ED297-4F33-E099-C6D6-39AA08473295";
	setAttr ".nr" -type "double3" 0 1 0 ;
createNode condition -n "cond_horizontalParent_shake";
	rename -uid "5F83151E-4460-396C-33A0-D299A4674A6E";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
createNode condition -n "cond_horizontalParent_root";
	rename -uid "F27869BA-446A-CDBD-1149-6493CAA5206D";
	setAttr ".ct" -type "float3" 1 0 0 ;
	setAttr ".cf" -type "float3" 0 1 1 ;
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
	setAttr -s 9 ".ktv[0:8]"  1001 0 1050 -0.49972949895265623 1100 0
		 1150 -0.33647694133196432 1200 0 1250 0.12450560958020782 1300 0 1350 0.23856600193368582
		 1400 0;
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
	setAttr -s 5 ".ktv[0:4]"  1001 0 1100 0.48648663405050058 1200 0 1300 0.48648663405050058
		 1400 0;
	setAttr ".pre" 3;
	setAttr ".pst" 3;
createNode animCurveTL -n "ctrl_breathingCam_translateZ";
	rename -uid "36204D5F-4903-ED7E-E20E-3982198C46E3";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 8 ".ktv[0:7]"  1001 0.083164444013954841 1050 0.072756498100408643
		 1150 0.09357238992750104 1200 0.083164444013954841 1250 0.072756498100408643 1300 0.083164444013954869
		 1350 0.09357238992750104 1400 0.083164444013954841;
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
createNode lightLinker -s -n "lightLinker1";
	rename -uid "841C6BA5-4FCD-540A-3705-C681BB8EC307";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "2597CE63-4C6E-C22A-53D2-67BC377D71D0";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "8249074F-4526-38C1-FE19-C5B9DB97AB41";
createNode displayLayerManager -n "layerManager";
	rename -uid "6AD1C251-4AB9-22F7-18D8-48B96BE20010";
createNode displayLayer -n "defaultLayer";
	rename -uid "E9DC7FDF-4D02-5EE6-6F33-9492AB9AFE58";
	setAttr ".ufem" -type "stringArray" 0  ;
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "724521CF-4600-10D8-F3E4-15BC63D60A45";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "71DB50E7-4133-F93A-03D2-0FA29B0AED36";
	setAttr ".g" yes;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "E32D5C55-466E-6D1B-6042-18A5A8154BFF";
	setAttr ".b" -type "string" (
		"// Maya Mel UI Configuration File.\n//\n//  This script is machine generated.  Edit at your own risk.\n//\n//\n\nglobal string $gMainPane;\nif (`paneLayout -exists $gMainPane`) {\n\n\tglobal int $gUseScenePanelConfig;\n\tint    $useSceneConfig = $gUseScenePanelConfig;\n\tint    $nodeEditorPanelVisible = stringArrayContains(\"nodeEditorPanel1\", `getPanel -vis`);\n\tint    $nodeEditorWorkspaceControlOpen = (`workspaceControl -exists nodeEditorPanel1Window` && `workspaceControl -q -visible nodeEditorPanel1Window`);\n\tint    $menusOkayInPanels = `optionVar -q allowMenusInPanels`;\n\tint    $nVisPanes = `paneLayout -q -nvp $gMainPane`;\n\tint    $nPanes = 0;\n\tstring $editorName;\n\tstring $panelName;\n\tstring $itemFilterName;\n\tstring $panelConfig;\n\n\t//\n\t//  get current state of the UI\n\t//\n\tsceneUIReplacement -update $gMainPane;\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Top View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Top View\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        modelEditor -e \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n"
		+ "            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n"
		+ "            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Side View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Side View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n"
		+ "            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n"
		+ "            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n"
		+ "            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Front View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Front View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n"
		+ "            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n"
		+ "            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n"
		+ "            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Persp View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Persp View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n"
		+ "            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n"
		+ "            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n"
		+ "            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -excludeObjectPreset \"All\" \n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1319\n            -height 696\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"ToggledOutliner\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"ToggledOutliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 1\n            -showReferenceMembers 1\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -autoExpandAllAnimatedShapes 1\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n"
		+ "            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -selectCommand \"print(\\\"\\\")\" \n"
		+ "            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n"
		+ "            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -autoExpandAllAnimatedShapes 1\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n"
		+ "            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -ufeFilter \"USD\" \"InactivePrims\" -ufeFilterValue 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"graphEditor\" (localizedPanelLabel(\"Graph Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n"
		+ "            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 1\n                -autoExpandAllAnimatedShapes 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 1\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n"
		+ "                -highlightActive 0\n                -autoSelectNewObjects 1\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -showUfeItems 1\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 1\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n"
		+ "                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n            animCurveEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showPlayRangeShades \"on\" \n                -lockPlayRangeShades \"off\" \n                -smoothness \"fine\" \n                -resultSamples 1\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                -showUpstreamCurves 1\n                -keyMinScale 1\n                -stackedCurvesMin -1\n                -stackedCurvesMax 1\n                -stackedCurvesSpace 0.2\n                -preSelectionHighlight 1\n                -limitToSelectedCurves 0\n                -constrainDrag 0\n                -valueLinesToggle 0\n                -outliner \"graphEditor1OutlineEd\" \n                -highlightAffectedCurves 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dopeSheetPanel\" (localizedPanelLabel(\"Dope Sheet\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 0\n                -autoExpandAllAnimatedShapes 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n"
		+ "                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 0\n                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -showUfeItems 1\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n"
		+ "                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 0\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n            dopeSheetEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -showSummary 1\n                -showScene 0\n                -hierarchyBelow 0\n                -showTicks 1\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"timeEditorPanel\" (localizedPanelLabel(\"Time Editor\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Time Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"clipEditorPanel\" (localizedPanelLabel(\"Trax Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"sequenceEditorPanel\" (localizedPanelLabel(\"Camera Sequencer\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n"
		+ "\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Camera Sequencer\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = sequenceEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 1 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperGraphPanel\" (localizedPanelLabel(\"Hypergraph Hierarchy\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypergraph Hierarchy\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"HyperGraphEd\");\n            hyperGraph -e \n                -graphLayoutStyle \"hierarchicalLayout\" \n                -orientation \"horiz\" \n                -mergeConnections 0\n                -zoom 1\n                -animateTransition 0\n                -showRelationships 1\n"
		+ "                -showShapes 0\n                -showDeformers 0\n                -showExpressions 0\n                -showConstraints 0\n                -showConnectionFromSelected 0\n                -showConnectionToSelected 0\n                -showConstraintLabels 0\n                -showUnderworld 0\n                -showInvisible 0\n                -transitionFrames 1\n                -opaqueContainers 0\n                -freeform 0\n                -imagePosition 0 0 \n                -imageScale 1\n                -imageEnabled 0\n                -graphType \"DAG\" \n                -heatMapDisplay 0\n                -updateSelection 1\n                -updateNodeAdded 1\n                -useDrawOverrideColor 0\n                -limitGraphTraversal -1\n                -range 0 0 \n                -iconSize \"smallIcons\" \n                -showCachedConnections 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperShadePanel\" (localizedPanelLabel(\"Hypershade\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypershade\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"visorPanel\" (localizedPanelLabel(\"Visor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Visor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"nodeEditorPanel\" (localizedPanelLabel(\"Node Editor\")) `;\n\tif ($nodeEditorPanelVisible || $nodeEditorWorkspaceControlOpen) {\n\t\tif (\"\" == $panelName) {\n\t\t\tif ($useSceneConfig) {\n\t\t\t\t$panelName = `scriptedPanel -unParent  -type \"nodeEditorPanel\" -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels `;\n\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n"
		+ "                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -connectedGraphingMode 1\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 1\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n"
		+ "                -showUnitConversions 0\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\t}\n\t\t} else {\n\t\t\t$label = `panel -q -label $panelName`;\n\t\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -connectedGraphingMode 1\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n"
		+ "                -gridSnap 1\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n                -showUnitConversions 0\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\tif (!$useSceneConfig) {\n\t\t\t\tpanel -e -l $label $panelName;\n\t\t\t}\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"createNodePanel\" (localizedPanelLabel(\"Create Node\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Create Node\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"polyTexturePlacementPanel\" (localizedPanelLabel(\"UV Editor\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"UV Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"renderWindowPanel\" (localizedPanelLabel(\"Render View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Render View\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"shapePanel\" (localizedPanelLabel(\"Shape Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tshapePanel -edit -l (localizedPanelLabel(\"Shape Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"posePanel\" (localizedPanelLabel(\"Pose Editor\")) `;\n\tif (\"\" != $panelName) {\n"
		+ "\t\t$label = `panel -q -label $panelName`;\n\t\tposePanel -edit -l (localizedPanelLabel(\"Pose Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynRelEdPanel\" (localizedPanelLabel(\"Dynamic Relationships\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dynamic Relationships\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"relationshipPanel\" (localizedPanelLabel(\"Relationship Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Relationship Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"referenceEditorPanel\" (localizedPanelLabel(\"Reference Editor\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Reference Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynPaintScriptedPanelType\" (localizedPanelLabel(\"Paint Effects\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Paint Effects\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"scriptEditorPanel\" (localizedPanelLabel(\"Script Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Script Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"profilerPanel\" (localizedPanelLabel(\"Profiler Tool\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Profiler Tool\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"contentBrowserPanel\" (localizedPanelLabel(\"Content Browser\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Content Browser\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"Stereo\" (localizedPanelLabel(\"Stereo\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Stereo\")) -mbv $menusOkayInPanels  $panelName;\n{ string $editorName = ($panelName+\"Editor\");\n            stereoCameraView -e \n                -camera \"|persp\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n"
		+ "                -displayAppearance \"wireframe\" \n                -activeOnly 0\n                -ignorePanZoom 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -holdOuts 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 1\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 32768\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -depthOfFieldPreview 1\n"
		+ "                -maxConstantTransparency 1\n                -objectFilterShowInHUD 1\n                -isFiltered 0\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -controllers 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n"
		+ "                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -imagePlane 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -particleInstancers 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nParticles 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -pluginShapes 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -motionTrails 1\n                -clipGhosts 1\n                -bluePencil 1\n                -greasePencils 0\n                -shadows 0\n                -captureSequenceNumber -1\n                -width 0\n                -height 0\n                -sceneRenderFilter 0\n                -displayMode \"centerEye\" \n"
		+ "                -viewColor 0 0 0 1 \n                -useCustomBackground 1\n                $editorName;\n            stereoCameraView -e -viewSelected 0 $editorName;\n            stereoCameraView -e \n                -pluginObjects \"gpuCacheDisplayFilter\" 1 \n                $editorName; };\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Model Panel5\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Model Panel5\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -camera \"|camRig|camera|shotCam\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n"
		+ "            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n"
		+ "            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n"
		+ "            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1319\n            -height 640\n            -sceneRenderFilter 0\n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\tif ($useSceneConfig) {\n        string $configName = `getPanel -cwl (localizedPanelLabel(\"Current Layout\"))`;\n        if (\"\" != $configName) {\n\t\t\tpanelConfiguration -edit -label (localizedPanelLabel(\"Current Layout\")) \n\t\t\t\t-userCreated false\n\t\t\t\t-defaultImage \"vacantCell.xP:/\"\n\t\t\t\t-image \"\"\n\t\t\t\t-sc false\n\t\t\t\t-configString \"global string $gMainPane; paneLayout -e -cn \\\"single\\\" -ps 1 100 100 $gMainPane;\"\n"
		+ "\t\t\t\t-removeAllPanels\n\t\t\t\t-ap false\n\t\t\t\t\t(localizedPanelLabel(\"Persp View\")) \n\t\t\t\t\t\"modelPanel\"\n"
		+ "\t\t\t\t\t\"$panelName = `modelPanel -unParent -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels `;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 32768\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -bluePencil 1\\n    -greasePencils 0\\n    -excludeObjectPreset \\\"All\\\" \\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1319\\n    -height 696\\n    -sceneRenderFilter 0\\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t\t\"modelPanel -edit -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels  $panelName;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 32768\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -bluePencil 1\\n    -greasePencils 0\\n    -excludeObjectPreset \\\"All\\\" \\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1319\\n    -height 696\\n    -sceneRenderFilter 0\\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t$configName;\n\n            setNamedPanelLayout (localizedPanelLabel(\"Current Layout\"));\n        }\n\n        panelHistory -e -clear mainPanelHistory;\n        sceneUIReplacement -clear;\n\t}\n\n\ngrid -spacing 5 -size 12 -divisions 5 -displayAxes yes -displayGridLines yes -displayDivisionLines yes -displayPerspectiveLabels no -displayOrthographicLabels no -displayAxesBold yes -perspectiveLabelPosition axis -orthographicLabelPosition edge;\nviewManip -drawCompass 0 -compassAngle 0 -frontParameters \"\" -homeParameters \"\" -selectionLockParameters \"\";\n}\n");
	setAttr ".st" 3;
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "EC7F7A0C-43D9-5EC1-6E14-B6866E30DDBE";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
	setAttr ".st" 6;
createNode mayaUsdLayerManager -n "mayaUsdLayerManager1";
	rename -uid "9D222398-4D8C-6459-2D72-33BFC5CA4A9E";
	setAttr ".sst" -type "string" "";
select -ne :time1;
	setAttr ".o" 1400;
	setAttr ".unw" 1400;
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
	setAttr -s 19 ".u";
select -ne :defaultRenderingList1;
select -ne :standardSurface1;
	setAttr ".bc" -type "float3" 0.40000001 0.40000001 0.40000001 ;
	setAttr ".sr" 0.40000000596046448;
select -ne :initialShadingGroup;
	setAttr -s 2 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr ".imfkey" -type "string" "exr";
	setAttr ".dss" -type "string" "lambert1";
select -ne :defaultResolution;
	setAttr ".w" 1920;
	setAttr ".h" 1080;
	setAttr ".pa" 1;
	setAttr ".dar" 1.7777777910232544;
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "<MAYA_RESOURCES>/OCIO-configs/Maya2022-default/config.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".vn" -type "string" "ACES 1.0 SDR-video";
	setAttr ".dn" -type "string" "sRGB";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".potn" -type "string" "ACES 1.0 SDR-video (sRGB)";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
select -ne :ikSystem;
	setAttr -s 4 ".sol";
connectAttr "camera_parentConstraint1.ctx" "camera.tx";
connectAttr "camera_parentConstraint1.cty" "camera.ty";
connectAttr "camera_parentConstraint1.ctz" "camera.tz";
connectAttr "camera_parentConstraint1.crx" "camera.rx";
connectAttr "camera_parentConstraint1.cry" "camera.ry";
connectAttr "camera_parentConstraint1.crz" "camera.rz";
connectAttr "ctrl_general.camShape" "shotCam.lodv";
connectAttr "ctrl_cam.focalLength" "shotCamShape.fl";
connectAttr "ctrl_cam.fStop" "shotCamShape.fs";
connectAttr "ctrl_cam.focusDistance" "shotCamShape.fd";
connectAttr "ctrl_cam.dof" "shotCamShape.dof";
connectAttr "ctrl_cam.Far" "shotCamShape.fcp";
connectAttr "ctrl_cam.Near" "shotCamShape.ncp";
connectAttr "camera.ro" "camera_parentConstraint1.cro";
connectAttr "camera.pim" "camera_parentConstraint1.cpim";
connectAttr "camera.rp" "camera_parentConstraint1.crp";
connectAttr "camera.rpt" "camera_parentConstraint1.crt";
connectAttr "ctrl_cam.t" "camera_parentConstraint1.tg[0].tt";
connectAttr "ctrl_cam.rp" "camera_parentConstraint1.tg[0].trp";
connectAttr "ctrl_cam.rpt" "camera_parentConstraint1.tg[0].trt";
connectAttr "ctrl_cam.r" "camera_parentConstraint1.tg[0].tr";
connectAttr "ctrl_cam.ro" "camera_parentConstraint1.tg[0].tro";
connectAttr "ctrl_cam.s" "camera_parentConstraint1.tg[0].ts";
connectAttr "ctrl_cam.pm" "camera_parentConstraint1.tg[0].tpm";
connectAttr "camera_parentConstraint1.w0" "camera_parentConstraint1.tg[0].tw";
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
connectAttr "ctrl_general.controls" "ctrl_root.v";
connectAttr "pCon_ctrl_cam_HOOK.ctx" "ctrl_cam_HOOK.tx";
connectAttr "pCon_ctrl_cam_HOOK.cty" "ctrl_cam_HOOK.ty";
connectAttr "pCon_ctrl_cam_HOOK.ctz" "ctrl_cam_HOOK.tz";
connectAttr "pCon_ctrl_cam_HOOK.crx" "ctrl_cam_HOOK.rx";
connectAttr "pCon_ctrl_cam_HOOK.cry" "ctrl_cam_HOOK.ry";
connectAttr "pCon_ctrl_cam_HOOK.crz" "ctrl_cam_HOOK.rz";
connectAttr "ctrl_cam_MOVE_aimConstraint1.crx" "ctrl_cam_MOVE.rx";
connectAttr "ctrl_cam_MOVE_aimConstraint1.cry" "ctrl_cam_MOVE.ry";
connectAttr "ctrl_cam_MOVE_aimConstraint1.crz" "ctrl_cam_MOVE.rz";
connectAttr "ctrl_general.s" "ctrl_cam.s";
connectAttr "remapVal_viewGrid_tZ.ov" "geo_grid_MOVE.tz";
connectAttr "ctrl_cam.gridVisibility" "geo_grid_MOVE.v";
connectAttr "cond_grid_geoSwitch.ocr" "geo_grid_scope.v";
connectAttr "cond_grid_geoSwitch.ocg" "geo_grid_HD.v";
connectAttr "ctrl_general.Aim" "ctrl_cam_MOVE_aimConstraint1.w0";
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
connectAttr "ctrl_up.t" "ctrl_cam_MOVE_aimConstraint1.tg[1].tt";
connectAttr "ctrl_up.rp" "ctrl_cam_MOVE_aimConstraint1.tg[1].trp";
connectAttr "ctrl_up.rpt" "ctrl_cam_MOVE_aimConstraint1.tg[1].trt";
connectAttr "ctrl_up.pm" "ctrl_cam_MOVE_aimConstraint1.tg[1].tpm";
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
connectAttr "ctrl_aim_HOOK_parentConstraint1.ctx" "ctrl_aim_HOOK.tx";
connectAttr "ctrl_aim_HOOK_parentConstraint1.cty" "ctrl_aim_HOOK.ty";
connectAttr "ctrl_aim_HOOK_parentConstraint1.ctz" "ctrl_aim_HOOK.tz";
connectAttr "ctrl_aim_HOOK_parentConstraint1.crx" "ctrl_aim_HOOK.rx";
connectAttr "ctrl_aim_HOOK_parentConstraint1.cry" "ctrl_aim_HOOK.ry";
connectAttr "ctrl_aim_HOOK_parentConstraint1.crz" "ctrl_aim_HOOK.rz";
connectAttr "ctrl_general.Aim" "ctrl_aim.v";
connectAttr "ctrl_aim_HOOK.ro" "ctrl_aim_HOOK_parentConstraint1.cro";
connectAttr "ctrl_aim_HOOK.pim" "ctrl_aim_HOOK_parentConstraint1.cpim";
connectAttr "ctrl_aim_HOOK.rp" "ctrl_aim_HOOK_parentConstraint1.crp";
connectAttr "ctrl_aim_HOOK.rpt" "ctrl_aim_HOOK_parentConstraint1.crt";
connectAttr "ctrl_general.t" "ctrl_aim_HOOK_parentConstraint1.tg[0].tt";
connectAttr "ctrl_general.rp" "ctrl_aim_HOOK_parentConstraint1.tg[0].trp";
connectAttr "ctrl_general.rpt" "ctrl_aim_HOOK_parentConstraint1.tg[0].trt";
connectAttr "ctrl_general.r" "ctrl_aim_HOOK_parentConstraint1.tg[0].tr";
connectAttr "ctrl_general.ro" "ctrl_aim_HOOK_parentConstraint1.tg[0].tro";
connectAttr "ctrl_general.s" "ctrl_aim_HOOK_parentConstraint1.tg[0].ts";
connectAttr "ctrl_general.pm" "ctrl_aim_HOOK_parentConstraint1.tg[0].tpm";
connectAttr "ctrl_aim_HOOK_parentConstraint1.w0" "ctrl_aim_HOOK_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_root.t" "ctrl_aim_HOOK_parentConstraint1.tg[1].tt";
connectAttr "ctrl_root.rp" "ctrl_aim_HOOK_parentConstraint1.tg[1].trp";
connectAttr "ctrl_root.rpt" "ctrl_aim_HOOK_parentConstraint1.tg[1].trt";
connectAttr "ctrl_root.r" "ctrl_aim_HOOK_parentConstraint1.tg[1].tr";
connectAttr "ctrl_root.ro" "ctrl_aim_HOOK_parentConstraint1.tg[1].tro";
connectAttr "ctrl_root.s" "ctrl_aim_HOOK_parentConstraint1.tg[1].ts";
connectAttr "ctrl_root.pm" "ctrl_aim_HOOK_parentConstraint1.tg[1].tpm";
connectAttr "ctrl_aim_HOOK_parentConstraint1.w1" "ctrl_aim_HOOK_parentConstraint1.tg[1].tw"
		;
connectAttr "ctrl_shake.t" "ctrl_aim_HOOK_parentConstraint1.tg[2].tt";
connectAttr "ctrl_shake.rp" "ctrl_aim_HOOK_parentConstraint1.tg[2].trp";
connectAttr "ctrl_shake.rpt" "ctrl_aim_HOOK_parentConstraint1.tg[2].trt";
connectAttr "ctrl_shake.r" "ctrl_aim_HOOK_parentConstraint1.tg[2].tr";
connectAttr "ctrl_shake.ro" "ctrl_aim_HOOK_parentConstraint1.tg[2].tro";
connectAttr "ctrl_shake.s" "ctrl_aim_HOOK_parentConstraint1.tg[2].ts";
connectAttr "ctrl_shake.pm" "ctrl_aim_HOOK_parentConstraint1.tg[2].tpm";
connectAttr "ctrl_aim_HOOK_parentConstraint1.w2" "ctrl_aim_HOOK_parentConstraint1.tg[2].tw"
		;
connectAttr "cond_aimParent_general.ocr" "ctrl_aim_HOOK_parentConstraint1.w0";
connectAttr "cond_aimParent_root.ocr" "ctrl_aim_HOOK_parentConstraint1.w1";
connectAttr "cond_aimParent_shake.ocr" "ctrl_aim_HOOK_parentConstraint1.w2";
connectAttr "ctrl_up_MOVE_parentConstraint1.ctx" "ctrl_up_MOVE.tx";
connectAttr "ctrl_up_MOVE_parentConstraint1.cty" "ctrl_up_MOVE.ty";
connectAttr "ctrl_up_MOVE_parentConstraint1.ctz" "ctrl_up_MOVE.tz";
connectAttr "ctrl_up_MOVE_parentConstraint1.crx" "ctrl_up_MOVE.rx";
connectAttr "ctrl_up_MOVE_parentConstraint1.cry" "ctrl_up_MOVE.ry";
connectAttr "ctrl_up_MOVE_parentConstraint1.crz" "ctrl_up_MOVE.rz";
connectAttr "makeNurbCircle1.oc" "ctrl_upShape.cr";
connectAttr "ctrl_up_MOVE.ro" "ctrl_up_MOVE_parentConstraint1.cro";
connectAttr "ctrl_up_MOVE.pim" "ctrl_up_MOVE_parentConstraint1.cpim";
connectAttr "ctrl_up_MOVE.rp" "ctrl_up_MOVE_parentConstraint1.crp";
connectAttr "ctrl_up_MOVE.rpt" "ctrl_up_MOVE_parentConstraint1.crt";
connectAttr "ctrl_shake.t" "ctrl_up_MOVE_parentConstraint1.tg[0].tt";
connectAttr "ctrl_shake.rp" "ctrl_up_MOVE_parentConstraint1.tg[0].trp";
connectAttr "ctrl_shake.rpt" "ctrl_up_MOVE_parentConstraint1.tg[0].trt";
connectAttr "ctrl_shake.r" "ctrl_up_MOVE_parentConstraint1.tg[0].tr";
connectAttr "ctrl_shake.ro" "ctrl_up_MOVE_parentConstraint1.tg[0].tro";
connectAttr "ctrl_shake.s" "ctrl_up_MOVE_parentConstraint1.tg[0].ts";
connectAttr "ctrl_shake.pm" "ctrl_up_MOVE_parentConstraint1.tg[0].tpm";
connectAttr "ctrl_up_MOVE_parentConstraint1.w0" "ctrl_up_MOVE_parentConstraint1.tg[0].tw"
		;
connectAttr "ctrl_root.t" "ctrl_up_MOVE_parentConstraint1.tg[1].tt";
connectAttr "ctrl_root.rp" "ctrl_up_MOVE_parentConstraint1.tg[1].trp";
connectAttr "ctrl_root.rpt" "ctrl_up_MOVE_parentConstraint1.tg[1].trt";
connectAttr "ctrl_root.r" "ctrl_up_MOVE_parentConstraint1.tg[1].tr";
connectAttr "ctrl_root.ro" "ctrl_up_MOVE_parentConstraint1.tg[1].tro";
connectAttr "ctrl_root.s" "ctrl_up_MOVE_parentConstraint1.tg[1].ts";
connectAttr "ctrl_root.pm" "ctrl_up_MOVE_parentConstraint1.tg[1].tpm";
connectAttr "ctrl_up_MOVE_parentConstraint1.w1" "ctrl_up_MOVE_parentConstraint1.tg[1].tw"
		;
connectAttr "cond_horizontalParent_shake.ocr" "ctrl_up_MOVE_parentConstraint1.w0"
		;
connectAttr "cond_horizontalParent_root.ocr" "ctrl_up_MOVE_parentConstraint1.w1"
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
connectAttr "ctrl_general.s" "ctrl_distance.s";
connectAttr "distanceBetween1.d" "ctrl_distance.distanceToCam";
connectAttr "ctrl_cam.distance" "ctrl_distance.v";
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
connectAttr "ctrl_general.refParent" "cond_refsMOVE_general.ft";
connectAttr "ctrl_general.refParent" "cond_refsMOVE_root.ft";
connectAttr "ctrl_cam.focalLength" "remapVal_viewGrid_tZ.i";
connectAttr "ctrl_cam.gridType" "cond_grid_geoSwitch.ft";
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
connectAttr "ctrl_general.aimParent" "cond_aimParent_general.ft";
connectAttr "ctrl_general.aimParent" "cond_aimParent_root.ft";
connectAttr "ctrl_general.aimParent" "cond_aimParent_shake.ft";
connectAttr "ctrl_general.horizontalParent" "cond_horizontalParent_shake.ft";
connectAttr "ctrl_general.horizontalParent" "cond_horizontalParent_root.ft";
connectAttr "shotCam.t" "distanceBetween1.p1";
connectAttr "ctrl_distance.t" "distanceBetween1.p2";
connectAttr "ctrl_distance.parent" "cond_distanceGeneral_dist.ft";
connectAttr "ctrl_distance.parent" "cond_distanceRoot_dist.ft";
connectAttr "ctrl_distance.parent" "cond_distanceShake_dist.ft";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "cond_aimParent_general.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_aimParent_root.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_aimParent_shake.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_refsMOVE_general.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_refsMOVE_root.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "remapVal_viewGrid_tZ.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_aim_bool.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_horizontal_bool.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_horizontalParent_root.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_horizontalParent_shake.msg" ":defaultRenderUtilityList1.u" -na
		;
connectAttr "distanceBetween1.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_distanceGeneral_dist.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_distanceRoot_dist.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_distanceShake_dist.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "rev_breathingCam_intensity.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "cond_brethingCam_onOFF.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "multDiv_breathingCam_onOFF.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "PMA_breathingCam_intensityValueBalance_pConShake.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "cond_grid_geoSwitch.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
connectAttr "geo_grid_scopeShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "geo_grid_HDShape.iog" ":initialShadingGroup.dsm" -na;
// End of camRig_001.ma
