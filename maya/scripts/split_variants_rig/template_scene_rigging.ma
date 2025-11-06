//Maya ASCII 2025ff03 scene
//script generate by the script ILLOGIC : splits_variants_rig.py
//Name: __nameScene__.ma
//file -r -ns ":" -dr 1 -rfn "baseballBat_baseballBatA_v002RN" -op "v=0;" -typ "mayaAscii"
//		 "c:/your/path/file/scene.ma";
__insert__information__all_data__here__
requires maya "2025ff03";
requires "stereoCamera" "10.0";
requires -nodeType "aiOptions" -nodeType "aiAOVDriver" -nodeType "aiAOVFilter" -nodeType "aiImagerDenoiserOidn"
		 "mtoa" "5.4.3";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
fileInfo "cutIdentifier" "202407121012-8ed02f4c99";
fileInfo "osv" "Windows 10 Pro v2009 (Build: 19045)";
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "R:\\pipeline\\networkInstall\\OpenColorIO-Configs\\PRISM\\illogic_V01-cg-config-v1.0.0_aces-v1.3_ocio-v2.1.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 - SDR Video (sRGB - Display)";
	setAttr ".vn" -type "string" "ACES 1.0 - SDR Video";
	setAttr ".dn" -type "string" "sRGB - Display";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 - SDR Video (sRGB - Display)";
	setAttr ".potn" -type "string" "ACES 1.0 - SDR Video (sRGB - Display)";
// End of __nameScene__.ma