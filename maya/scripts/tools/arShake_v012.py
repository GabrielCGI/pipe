################################################################################################
################################################################################################
###                                   Animation Shake Tool                                   ###
###                                  By Alastair Richardson                                  ###
###                                        April, 2014                                       ###
###          Use:                                                                            ###
###             windows:                                                                     ###
###                 Place .py file in Documents/Maya/Scripts folder                          ###
###                                                                                          ###
###             Maya shelf script:                                                           ###
###                 import arShake_v012                                                      ###
###                 reload(arShake_v012)                                                     ###
###                 arShake_v012.GUI()                                                       ###
###                                                                                          ###
###                                                                                          ###
###          More at www.alrichardson.com                                                    ###
###                                                                                          ###
################################################################################################
################################################################################################

import maya.cmds as cmds, maya.OpenMaya as om
import random
from functools import partial

########################## Main Shake function ##########################
def runShake():
	# query time slider range for shake to be applied to
	sliderStart = cmds.playbackOptions( query = True, min = True )
	sliderEnd = cmds.playbackOptions( query = True, max = True )
	
	# set current time to start of time slider
	cmds.currentTime( int(sliderStart) )
	
	# query text field to find frequency of shake application to frames
	everyFrame = cmds.textField( 'everyFrame', query = True, text = True )
	if (float(everyFrame) < 1):
		return om.MGlobal.displayWarning( 'Please set Per Frame to equal or greater than 1' )
	
	# creat seelction variable of object to have shake applied to
	selection = cmds.ls(sl=True)
	if len( selection ) == 0:
		return om.MGlobal.displayWarning( 'Please select and object with translates to add shake to' )
	
	# start the main for loop for shake
	for i in selection:
		cmds.select( i )
		trg = i
		# query global keyframe interpolation settings and set them to linear
		# this is to optemise the results produced by arShake
		currentInKey = cmds.keyTangent( query = True, g=True )
		currentOutKey = cmds.keyTangent( query = True, g=True )
		cmds.keyTangent( g=True, inTangentType = 'linear' )
		cmds.keyTangent( g=True, outTangentType = 'linear' )
		time = cmds.currentTime(query = True)
		
		# query if the shake anim layer exists, if not then create it
		animLayerExists = cmds.animLayer( i + '_ShakeLayer', query = True, exists = True )
		if animLayerExists:
			om.MGlobal.displayInfo( 'shake layer already exists, running now' )
		else:
			cmds.animLayer( i + '_ShakeLayer', attribute = ( i + '.translate', i + '.rotate', i + '.scale' )  )
			
		# find the number of frames in range of effect
		totalSliderTime = int(sliderEnd) - time
		
		# make the available time a factor of 1
		divTime = 1 / totalSliderTime
		newDivTime = 0
		
		# query main chack box for translate shake
		translateShake = cmds.checkBox( 'translateShake', query = True, value = True )
		
		if translateShake == False:
			# query individual chack boxes for translate shake
			tX = cmds.checkBox( 'tX', query = True, value = True )
			tY = cmds.checkBox( 'tY', query = True, value = True )
			tZ = cmds.checkBox( 'tZ', query = True, value = True )
		
		else:
			tX = False
			tY = False
			tZ = False
		translateShakeAmount = cmds.textField( 'translateShakeAmount', query = True, text = True )
		
		# query main chack box for rotate shake
		rotateShake = cmds.checkBox( 'rotateShake', query = True, value = True )
		
		if rotateShake == False:
			# query individual chack boxes for translate shake
			rX = cmds.checkBox( 'rX', query = True, value = True )
			rY = cmds.checkBox( 'rY', query = True, value = True )
			rZ = cmds.checkBox( 'rZ', query = True, value = True )
		
		else:
			rX = False
			rY = False
			rZ = False
		rotateShiveAmount = cmds.textField( 'rotateShiveAmount', query = True, text = True )
		
		# This for loop calcuates the shake amount to be applied based on current time and the value of the falloff curve used.
		for i in range(int(time),int(sliderEnd) + 1):
			newDivTime+= divTime
			gradiantValue = cmds.gradientControlNoAttr( 'falloffCurve', query = True, valueAtPoint = newDivTime )
			useCurveTick = cmds.checkBox( 'useCurve', query = True, value = True )
			if useCurveTick:
				gradiantMultipler = gradiantValue
			else:
				gradiantMultipler = 1
			timePlus = cmds.currentTime(query = True)
			if timePlus <= int(sliderEnd):
				cmds.animLayer( trg + '_ShakeLayer', edit = True, mute = True )
				# translate shake starts here
				# make some nice random variables for the shaking!
				translateXRandom = (random.random() - 0.5 )
				translateYRandom = (random.random() - 0.5 )
				translateZRandom = (random.random() - 0.5 )
				# query the current translate values of the object
				currentTranslateX = cmds.getAttr( trg + '.translateX' )
				currentTranslateY = cmds.getAttr( trg + '.translateY' )
				currentTranslateZ = cmds.getAttr( trg + '.translateZ' )
				cmds.animLayer( trg + '_ShakeLayer', edit = True, mute = False )
				# based on the state of the check boxes, apply translate shake
				if tX or translateShake:
					cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
					value = currentTranslateX + ((translateXRandom * float(translateShakeAmount)) * gradiantMultipler), 
					attribute = 'translateX' )
				else:
					tXdone = False
				if tY or translateShake:
					cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
					value = currentTranslateY + ((translateYRandom * float(translateShakeAmount)) * gradiantMultipler), 
					attribute = 'translateY' )
				else:
					tYdone = False
				if tZ or translateShake:
					cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
					value = currentTranslateZ + ((translateZRandom * float(translateShakeAmount)) * gradiantMultipler), 
					attribute = 'translateZ' )
				else:
					tZdone = False
				cmds.animLayer( trg + '_ShakeLayer', edit = True, mute = True )
				# rotate shake starts here
				# make some more random variables for the shaking!
				rotateRandomX = (random.random() -.5 )
				rotateRandomY = (random.random() -.5 )
				rotateRandomZ = (random.random() -.5 )
				currentRotateX = cmds.getAttr( trg + '.rotateX' )
				currentRotateY = cmds.getAttr( trg + '.rotateY' )
				currentRotateZ = cmds.getAttr( trg + '.rotateZ' )
				cmds.animLayer( trg + '_ShakeLayer', edit = True, mute = False )
				# based on the state of the check boxes, apply rotate shake
				# I found that if the current rotate value of the object were 0, it threw out he script
				if currentRotateX > 0.000001:
					if rX or rotateShake:
						cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
						value = currentRotateX + ((rotateRandomX * float(rotateShiveAmount)) * gradiantMultipler ), 
						attribute = 'rotateX' )
					else:
						rXdone = False
				if currentRotateX < 0.000001:
					if rX or rotateShake:
						cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
						value = currentRotateX - ((rotateRandomX * float(rotateShiveAmount)) * gradiantMultipler ), 
						attribute = 'rotateX' )
					else:
						rXdone = False
				if currentRotateY > 0.000001:
					if rY or rotateShake:
						cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
						value = currentRotateY + ((rotateRandomY * float(rotateShiveAmount)) * gradiantMultipler ), 
						attribute = 'rotateY' )
					else:
						rYdone = False
				if currentRotateY < 0.000001:
					if rY or rotateShake:
						cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
						value = currentRotateY - ((rotateRandomY * float(rotateShiveAmount)) * gradiantMultipler ), 
						attribute = 'rotateY' )
					else:
						rYdone = False
				if currentRotateZ > 0.000001:
					if rZ or rotateShake:
						cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
						value = currentRotateZ + ((rotateRandomZ * float(rotateShiveAmount)) * gradiantMultipler ), 
						attribute = 'rotateZ' )
					else:
						rZdone = False
				if currentRotateZ < 0.000001:
					if rZ or rotateShake:
						cmds.setKeyframe( animLayer = trg + '_ShakeLayer', 
						value = currentRotateZ + ((rotateRandomZ * float(rotateShiveAmount)) * gradiantMultipler ), 
						attribute = 'rotateZ' )
					else:
						rZdone = False
			else:
				om.MGlobal.displayInfo( 'reached end of loop' )
			#advance current time by amount specified in by frame text field
			cmds.currentTime( timePlus + int(everyFrame) )
		# once the loop has finished, reset the global keyframe interpolation to its original setting.
		cmds.keyTangent( g=True, inTangentType = currentInKey[0] )
		cmds.keyTangent( g=True, outTangentType = currentOutKey[1] )
		# set the current time back to the start time.
		cmds.currentTime( time )



########################## GUI function ##########################
def GUI():
	
	# callbacks for editing check boxes
	def translateOnCallBack():
		cmds.checkBox( 'tX', edit = True, value = False )
		cmds.checkBox( 'tY', edit = True, value = False )
		cmds.checkBox( 'tZ', edit = True, value = False )
	
	def translateOffCallBack():
		cmds.checkBox( 'translateShake', edit = True, value = False )
	
	def rotateOnCallBack():
		cmds.checkBox( 'rX', edit = True, value = False )
		cmds.checkBox( 'rY', edit = True, value = False )
		cmds.checkBox( 'rZ', edit = True, value = False )
	
	def rotateOffCallBack():
		cmds.checkBox( 'rotateShake', edit = True, value = False )
	
	#GUI window and layout
	if (cmds.window( 'arShake', exists = True )):
		cmds.deleteUI( 'arShake', window = True )
	cmds.window( 'arShake', title = 'arShake', width = 200, height = 190, sizeable = False )
	cmds.frameLayout( label='Frame range and shake values:', labelAlign='bottom', borderStyle='etchedOut' )
	
	# top group of text fields
	cmds.rowColumnLayout( numberOfColumns =2 ) # text fields
	cmds.text( label = 'Per frame:', align = 'right', width = 100)
	cmds.textField( 'everyFrame', text = int(1), width = 80 )
	cmds.text( label = 'Translate amount:', align = 'right', width = 100)
	cmds.textField( 'translateShakeAmount', text = int(10), width = 80 )
	cmds.text( label = 'Rotate amount:', align = 'right', width = 100)
	cmds.textField( 'rotateShiveAmount', text = int(10), width = 80 )
	cmds.setParent( '..' )
	
	# translate check boxes
	cmds.frameLayout( label='Attributes to add shake to:', labelAlign='bottom', borderStyle='etchedOut' )
	cmds.rowColumnLayout( numberOfRows = 3 )
	cmds.rowColumnLayout( numberOfColumns = 3 )
	cmds.checkBox( 'translateShake', label = 'Translate', value = True, changeCommand = lambda arg : translateOnCallBack() )
	cmds.text( label = '')
	cmds.text( label = '')
	cmds.checkBox( 'tX', label = 'X', value = False, width = 100, changeCommand = lambda arg : translateOffCallBack() )
	cmds.checkBox( 'tY', label = 'Y', value = False, width = 80, changeCommand = lambda arg : translateOffCallBack( ) )
	cmds.checkBox( 'tZ', label = 'Z', value = False, width = 70, changeCommand = lambda arg : translateOffCallBack( ) )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	
	# rotate check boxes
	cmds.rowColumnLayout( numberOfRows = 3 )
	cmds.rowColumnLayout( numberOfColumns = 3 ) 
	cmds.checkBox( 'rotateShake', label = 'Rotate', value = True, changeCommand = lambda arg : rotateOnCallBack() )
	cmds.text( label = '')
	cmds.text( label = '')
	cmds.checkBox( 'rX', label = 'X', value = False, width = 100, changeCommand = lambda arg : rotateOffCallBack() )
	cmds.checkBox( 'rY', label = 'Y', value = False, width = 80, changeCommand = lambda arg : rotateOffCallBack() )
	cmds.checkBox( 'rZ', label = 'Z', value = False, width = 70, changeCommand = lambda arg : rotateOffCallBack() )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	
	# layout for gradient to control easing of shake
	cmds.rowColumnLayout()
	cmds.frameLayout( label='Easing in and out of shake over frame range:', labelAlign='bottom', borderStyle='etchedOut' )
	cmds.checkBox( 'useCurve', label = 'Use curve', value = True )
	cmds.columnLayout()
	interp0 = 1
	interp1 = 2
	interp2 = 0
	cmds.gradientControlNoAttr( 'falloffCurve', height=90, width = 250, 
	asString = '0, 0, ' + str(interp0) + ', 1, 0.5, ' + str(interp0) + ', 0, 1, ' + str(interp0) )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	
	# layout for button to startshake
	cmds.frameLayout( label='Run shake!', labelAlign='bottom', borderStyle='etchedOut' )
	cmds.button( 'sivernator', label = 'Shake it up', width = 250, height = 30, command = lambda arg: runShake() )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	cmds.setParent( '..' )
	cmds.showWindow()
	
	# Thanks for reading this far, I hope you found something usefull!