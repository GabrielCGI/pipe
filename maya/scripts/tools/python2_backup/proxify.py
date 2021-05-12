#EXPORT STAND IN & LOW POLY NEXT TO THE CURRENT SCENE
# 1) Select highpoly first and LAST the lowpoly
# 2) Set name
import sys
import os
import maya.cmds as cmds

def proxify():
	path = cmds.file(q=True, sn=True)
	proxName= os.path.basename(path).split(".")[0]
	result = cmds.promptDialog(
			title='Proxy name',
			message='Rename:',
			button=[proxName, 'Rename'],
			defaultButton=proxName,
			cancelButton='Rename',
			dismissString='Cancel')

	if result == proxName and proxName:
		name = proxName
		print proxName

	elif result == 'Rename':
		rename = cmds.promptDialog(query=True, text=True)
		if rename:
			name = rename
		else:
			cmds.warning( "Name is empty" )
			sys.exit()
	else:
		sys.exit()


	proxyName="/"+name+"_proxy.mb"
	assName="/"+name+".ass"
	sel = cmds.ls(selection=True)
	proxy  = sel[-1]
	sel.pop(-1)
	cmds.select(sel)

	dirPath= os.path.dirname(path)
	baseName=os.path.basename(path)

	standinPath = dirPath+assName
	lowPolyPath = dirPath+proxyName

	#Export assa
	cmds.file(standinPath,force=True,options="-shadowLinks 0;-mask 24;-lightLinks 0;-boundingBox;-fullPath", type="ASS Export", exportSelected=True)

	standIn = cmds.createNode("aiStandIn", n=name+"standInShape")

	cmds.setAttr (standIn+".ignoreGroupNodes",1)
	cmds.setAttr(standIn+".dso",standinPath,type="string")

	cmds.select(proxy)
	cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
	cmds.xform(proxy,piv=[0, 0, 0])
	cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
	cmds.delete(ch=True)

	cmds.parent(proxy,standIn)

	cmds.setAttr (proxy+".tx",lock=True)
	cmds.setAttr (proxy+".ty",lock=True)
	cmds.setAttr (proxy+".tz",lock=True)
	cmds.setAttr (proxy+".rx",lock=True)
	cmds.setAttr (proxy+".ry",lock=True)
	cmds.setAttr (proxy+".rz",lock=True)
	cmds.setAttr (proxy+".sx",lock=True)
	cmds.setAttr (proxy+".sy",lock=True)
	cmds.setAttr (proxy+".sz",lock=True)

	cmds.select(standIn,proxy)


	cmds.file(lowPolyPath,force=True, options="v=0;", type="mayaBinary", pr=True, es=True)
