import hou

def create_domelight():
    node = hou.selectedNodes()
    i = 1
    for n in node:

        node_name = n.name()   
        parent = n.parent()   
        parent_name = parent.name()
        
        stage = parent.parent()
        stage_name = stage.name()

        light = stage.createNode('domelight::3.0', 'L_'+node_name)
        light.parm('xn__inputstexturefile_r3ah').set('op:/'+stage_name+'/'+parent_name+'/'+node_name)
        light.setCurrent('on')

        light.setPosition(parent.position()+hou.Vector2(0, -2*i))
        i +=1