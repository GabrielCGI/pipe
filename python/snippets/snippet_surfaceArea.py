import maya.cmds as cmds
sel = cmds.ls(selection=True)

baseNumFlower = 1800
baseNumGrass = 7000
baseNumeWeed = 300
baseNumWeed2 = 78
referenceSurfaceArea = 4000000

surfaceArea = cmds.polyEvaluate(sel[0], a=True)
print surfaceArea
coef =  surfaceArea / referenceSurfaceArea


flowerPoint = coef * baseNumFlower
grassPoint = coef * baseNumGrass
numWeed = coef * baseNumeWeed
numWeed2 = coef * baseNumWeed2

print "Flower point:" + str(round(flowerPoint))
print "Grass point:" + str(round(grassPoint))
print "Weed point:" + str(round(numWeed))
print "Weed2 point:" + str(round(numWeed2))

