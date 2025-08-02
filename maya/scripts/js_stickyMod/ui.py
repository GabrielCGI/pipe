'''

Written by Josh Sobel
joshsobel89@gmail.com
http://www.friggingawesome.com

Run with:

import js_stickyMod.ui
js_stickyMod.ui.ui ()

'''



from __future__ import absolute_import

import maya.cmds as cmds
import maya.mel as mel
import sys
import os
import js_stickyMod.stickyMod_funcs as funcs



def ui ():

	version = 'v1.05'

	# Define

	win = 'stickyMod_win'
	width = 300
	height = 10
	bWidth = width - 35
	bWidth2 = bWidth * .494
	bHeight = 35
	bHeight2 = bHeight * .6
	bColor_green = [0.670,0.736,0.602]
	bColor_blue = [0.571,0.676,0.778]
	bColor_purple = [0.691,0.604,0.756]
	bColor_red = [0.765,0.525,0.549]
	bColor_brown = [0.804,0.732,0.646]

	if (cmds.window (win, exists = 1)):
		cmds.deleteUI (win)

	cmds.window (win, rtf = 1, t = 'Sticky Mod', s = 1, w = width)
	cmds.columnLayout (adj = 1, rs = 3, w = width)

	# Contents

	cmds.frameLayout ('jssm_stickyMod_fl', l = '                                 Sticky Mod {}'.format (version), cll = 0, mh = 8, mw = 15, w = width, ann = "Ride-along manipulator with adjustable falloff and placement for quick mesh adjustments.\nThis tool uses Handles and Nurbs Curves, which are turned on automatically if 'Force Display' is on.")
	cmds.columnLayout (adj = 0, rs = 3)

	cmds.text (l = "Select 1 vertex to run, or multiple vertices to ignore interactive falloff and auto-flood/smooth the map.", ww = 1, w = bWidth)
	cmds.separator (h = 1, style = 'none')
	cmds.text (l = "When running on multiple, the rivet will be built on the last vert in the selection.", ww = 1, w = bWidth)
	cmds.separator (h = 1, style = 'none')
	cmds.text (l = "This tool uses Handles and Nurbs Curves, which are turned on automatically if 'Force Display' is on.", ww = 1, w = bWidth)

	cmds.separator (h = 6, style = 'none')

	cmds.iconTextButton (l = '                Create Sticky Mod', i = 'softMod.png', bgc = bColor_green, ann = "Creates a ride-along manipulator with adjustable falloff for quick mesh adjustments.\n* Select 1 vertex to run, or multiple vertices to ignore interactive falloff and auto-flood/smooth the map. When running on multiple, the rivet will be built on the last vert in the selection.\nThis tool uses Handles and Nurbs Curves, which are turned on automatically if 'Force Display' is on.", st = 'iconAndTextHorizontal', w = bWidth, h = bHeight, c = 'import js_stickyMod.ui as ui ; ui.sm_create ()')
	cmds.rowColumnLayout (nc = 2, rs = [2,3], cs = [2,3])
	cmds.button (l = 'Add Geo', bgc = bColor_brown, ann = 'Add selected geo to selected sticky mod.', w = bWidth2, h = bHeight2, c = 'import js_stickyMod.stickyMod_funcs as funcs ; funcs.addGeo_sel ()')
	cmds.button (l = 'Remove Geo', bgc = bColor_brown, ann = 'Remove selected geo from selected sticky mod.', w = bWidth2, h = bHeight2, c = 'import js_stickyMod.stickyMod_funcs as funcs ; funcs.removeGeo_sel ()')
	cmds.button (l = 'Ori To World', bgc = bColor_brown, ann = 'Orient selected sticky mod to the world.', w = bWidth2, h = bHeight2, c = 'import js_stickyMod.stickyMod_funcs as funcs ; funcs.oriToWorld_sel ()')
	cmds.button (l = 'Aim At Sel', bgc = bColor_brown, ann = "Select an object and a sticky mod to aim the sticky mod's null at the object.", w = bWidth2, h = bHeight2, c = 'import js_stickyMod.stickyMod_funcs as funcs ; funcs.aimAtObj_sel ()')
	cmds.setParent ('..')
	cmds.button (l = 'Break Rivet Rotation', bgc = bColor_brown, ann = 'Break rotation follow on the null of the selected sticky mod.', h = bHeight2, w = bWidth, c = 'import js_stickyMod.stickyMod_funcs as funcs ; funcs.breakRot_sel ()')
	
	cmds.separator (h = 4, style = 'none')

	cmds.rowColumnLayout (nc = 5, rs = [3,3], cs = [3,3])
	cmds.text (l = '   Falloff Radius:  ', ann = 'Default value for Falloff Radius.')
	cmds.floatField ('jssm_sm_falloff_ff', v = 1, pre = 2, w = 40, ann = 'Default value for Falloff Radius.')
	cmds.text (l = '  Smooth Map:  ', ann = "If running on multiple verts for auto-flooding, the map will be smoothed this number of times.")
	cmds.intField ('jssm_sm_smooth_if', v = 3, min = 0, w = 40, ann = "If running on multiple verts for auto-flooding, the map will be smoothed this number of times.")
	cmds.setParent ('..')
	cmds.separator (h = 1, style = 'none')
	cmds.rowColumnLayout (nc = 4, cs = ([2,3],[3,3],[4,3]))
	cmds.optionMenu ('jssm_sm_vis_om', l = '      Mode:', w = 139, ann = 'Choose whether default visualization mode is a Nurbs Curve or a Handle. Set your viewport display options accordingly.')
	cmds.menuItem ('jssm_sm_vis1_mi', l = 'Handle')
	cmds.menuItem ('jssm_sm_vis2_mi', l = 'Nurbs Crv')
	cmds.text (l = '  Crv Scale: ', ann = 'Size the nurbs curve control is built at. Ignore if you prefer Handle mode.')
	cmds.floatField ('jssm_sm_scale_ff', v = 1, pre = 2, min = .001, w = 40, ann = 'Size the nurbs curve control is built at. Ignore if you prefer Handle mode.')
	cmds.setParent ('..')
	cmds.separator (h = 1, style = 'none')
	cmds.rowColumnLayout (nc = 4, cs = ([2,3],[3,3],[4,3]))
	cmds.text (l = '      ')
	cmds.checkBox ('jssm_sm_sphere_cb', l = 'Sphere   ', v = 1, ann = 'Radius display spheres will be turned off by default.')
	cmds.checkBox ('jssm_sm_lra_cb', l = 'Axis   ', v = 0, ann = 'Local Rotation Axes will be turned on be default.')
	cmds.checkBox ('jssm_sm_forceDisplay_cb', l = 'Force Display', v = 1, ann = 'Turns on viewport display for relevant object types on creation.')
	cmds.setParent ('..')
	cmds.setParent ('..')

	cmds.columnLayout (adj = 1, rs = 3)
	cmds.button (l = "Create Rivet", bgc = bColor_blue, w = bWidth2, h = bHeight2, ann = "Select a vertex and run.", c = "import js_stickyMod.stickyMod_funcs as stickyMod_funcs ; stickyMod_funcs.rivet_sel (loc = 1)")
	cmds.button (l = "Download 'AnimPolish' For More Finaling Tools", bgc = bColor_blue, w = bWidth2, h = bHeight2, c = "import webbrowser ; webbrowser.open('http://joshsobelrigs.com/animpolish')")
	cmds.setParent ('..')
	
	# Launch
	cmds.showWindow (win)
	cmds.window (win, e = 1, w = width, h = height)



def sm_create ():

	sphVis = cmds.checkBox ('jssm_sm_sphere_cb', q = 1, v = 1)
	lra = cmds.checkBox ('jssm_sm_lra_cb', q = 1, v = 1)
	falloff = cmds.floatField ('jssm_sm_falloff_ff', q = 1, v = 1)
	smooth = cmds.intField ('jssm_sm_smooth_if', q = 1, v = 1)
	mode = cmds.optionMenu ('jssm_sm_vis_om', q = 1, sl = 1)
	scale = cmds.floatField ('jssm_sm_scale_ff', q = 1, v = 1)
	display = cmds.checkBox ('jssm_sm_forceDisplay_cb', q = 1, v = 1)
	funcs.run_sel (falloff = falloff, sphVis = sphVis, smooth = smooth, lra = lra, mode = mode, scale = scale)
	if display == 1:
		try:
			panel = cmds.getPanel (wf = 1)
			cmds.modelEditor (panel, e = 1, nurbsCurves = 1)
			if mode == 1 or lra == 1:
				cmds.modelEditor (panel, e = 1, handles = 1)
		except:
			try:
				cmds.modelEditor ('modelPanel4', e = 1, nurbsCurves = 1)
				if mode == 1 or lra == 1:
					cmds.modelEditor ('modelPanel4', e = 1, handles = 1)
			except:
				sys.stdout.write ("Sticky Mod created! However, relevant viewport display options were not enabled because a viewport was not found.")
