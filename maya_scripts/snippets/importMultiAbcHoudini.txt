

import hou
import glob
path = r"D:\Teaser\shots\shot_250\abc\side"
files = glob.glob(path+"\\*.abc")

for file in files:
	geo = hou.node('/obj').createNode('geo',file.split("\\")[-1])
	read = geo.createNode('alembic')
	param = read.parm('fileName')
	param.set(file)
