import maya.cmds as cmds
import maya.mel as mel

dirPath = "B:/nutro_1909/shots/seq03_s010/fur/01/"
range = "99 340"
sampleTimes = '"-0.15 0 0.15"'

#selection = [u'ch_butterfly_shading_lib_butterfly:yeti_butterfly']
'''
selection = [u'ch_vizsla_shading_lib_vizsla:Vizsla_v019:YetiBody',
u'ch_vizsla_shading_lib_vizsla:Vizsla_v019:YetiEars',
u'ch_vizsla_shading_lib_vizsla:Vizsla_v019:YetiHead',
u'ch_vizsla_shading_lib_vizsla:Vizsla_v019:YetiWhiskers']
'''

selection = [u'ch_vizslaHigh_shading_lib_00:Vizsla_v019:YetiBody',
u'ch_vizslaHigh_shading_lib_00:Vizsla_v019:YetiEars',
u'ch_vizslaHigh_shading_lib_00:Vizsla_v019:YetiWhiskers',
u'ch_vizslaHigh_shading_lib_00:Vizsla_v019:YetiHead' ]


path = dirPath + "<NAME>.%04d.fur"

for s in selection:
    if cmds.getAttr(s+".fileMode") == 1:
        cmds.setAttr(s+".fileMode", 0)

cmds.select(selection)
cmd = 'pgYetiCommand -writeCache "%s" -range %s -sampleTimes %s'%(path, range, sampleTimes)

mel.eval(cmd)
for sel in selection:
    name = sel.replace(":","_")

    pathYeti = dirPath + name + "Shape.%04d.fur"
    cmds.setAttr(sel+".fileMode", 1)
    cmds.setAttr(sel+".cacheFileName", pathYeti, type="string")
