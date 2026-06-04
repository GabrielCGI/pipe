import hou
import os
from pprint import pprint


DEBUG = True
def pdebug(msg):
    if DEBUG:
        print(msg)


def get_shot_input_nulls(root_node):
    result = []

    if not root_node:
        return result

    # Iterate through all descendants
    for node in root_node.allSubChildren():
        # Check node type is Null
        if node.type().name() != "null":
            continue

        # Check parameter exists
        parm = node.parm("shotinputnull")
        if parm is None:
            continue

        # Check value == 1
        if parm.eval() == 1:
            result.append(node)

    return result


def build_content(kwargs):
    node = kwargs['node'].node('edit')
    pdebug('Start building content')

    #---------------- GET SHOT LIST ----------------
    prismjob = hou.getenv('PRISM_JOB')
    prismsequence = hou.getenv('PRISM_SEQUENCE')

    if not prismjob:
        pdebug('Scene file must be saved as a shot.')

    sequencepath = os.path.join(prismjob, '03_Production', 'Shots', prismsequence)

    shots = os.listdir(sequencepath)
    if len(shots)<1:
        pdebug('No shot exists.')
        
    pdebug(sequencepath)
    pdebug(shots)

    #---------------- QUERRY SHOTS TO CREATE ---------------- 
    selected_shots_list = hou.ui.selectFromList(shots)
    print(selected_shots_list)
    selected_shots = []
    for i in selected_shots_list:
        selected_shots.append(shots[i])
    if len(selected_shots)<1:
        pdebug('No shot was selected')
        return

    children_names = [child.name() for child in node.children()]
    pdebug(children_names)
    for i in range(0, len(selected_shots)):
        shot = selected_shots[i]
        if f"{shot}_in" in children_names:
            pdebug('Shot already exists in the switch_by_shot.')
            return

    #---------------- BUILD CONTENTS ---------------- 
    pdebug('---------------- BUILD CONTENTS ---------------- ')
    inedit = node.node('IN_EDIT')
    if not node.node('fallBack_out'):
        fallback_out = inedit.createOutputNode('null', f"fallBack_out")
        fallback_out.setColor(hou.Color(1, 0, 0))
    else:
        fallback_out = node.node('fallBack_out')
    
    if not node.node('switch_shot'):
        switch = inedit.createOutputNode('switch', f"switch_shot")
        switch.setInput(0, fallback_out)
        output = node.node('output0')
        output.setInput(0, switch)  
    else:
        switch = node.node("switch_shot")
        output = node.node("output0")

    shotinputnull_list = get_shot_input_nulls(node)
    number_of_existing_shots = len(shotinputnull_list)

    origin_pos = inedit.position()
    offset = 10 
    working_gap = 10
    
    for i in range(0, len(selected_shots)):
        shot = selected_shots[i]

        shot_in_null = inedit.createOutputNode('null', f"{shot}_in")
        shotinputnull_parm = hou.IntParmTemplate(
            name="shotinputnull",
            label="Shot Input Null",
            num_components=1,
            default_value=(1,),
            is_hidden=True
        )

        # Add it as a spare parameter
        input_null_parm_group = node.parmTemplateGroup()
        input_null_parm_group.append(shotinputnull_parm)
        shot_in_null.setParmTemplateGroup(input_null_parm_group)
        print(2)

        prune_unused = shot_in_null.createOutputNode('prune', 'prune_unused')
        print(5)
        shot_out_null = prune_unused.createOutputNode('null', f"{shot}_out")
        print(4)
        try:
            switch.setInput(number_of_existing_shots+i+1, shot_out_null)
        except Exception as e:
            print(e)
        print(3)

        shot_in_null.setPosition(origin_pos+hou.Vector2(number_of_existing_shots*offset + i*offset, -5))
        prune_unused.setPosition(origin_pos+hou.Vector2(number_of_existing_shots*offset + i*offset, -7-working_gap))
        shot_out_null.setPosition(origin_pos+hou.Vector2(number_of_existing_shots*offset + i*offset, -9-working_gap))

    switch.setPosition(origin_pos+hou.Vector2(i*offset, -14-working_gap))
    fallback_out.setPosition(origin_pos+hou.Vector2(-offset, -12-working_gap))
    output.setPosition(switch.position()-hou.Vector2(0, 2))


    pdebug('Done building content')