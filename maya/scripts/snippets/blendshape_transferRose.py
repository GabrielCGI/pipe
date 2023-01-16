import pymel.core as pm

#Create empty group
bsGRP = pm.group(empty=True, name='bsGRP')

# Select the blendshape node
blendshape_node =pm.ls("asFaceBS")[0]

# Select body (body new is already wrapped over body)
body =pm.ls("Joan_Body_old")[0]
body_new = pm.ls("Joan_Body")[0]

# Get the weights
weights = blendshape_node.weight

for i, weight in enumerate(weights):
    print('Blendshape target %s: %s' % (i, weight))

    blendshape_node.setWeight(i, 1)
    name = pm.listAttr(weight)[0]

    duplicate_body = pm.duplicate(body_new)
    pm.parent(duplicate_body,bsGRP)

    pm.rename(duplicate_body,name)
    blendshape_node.setWeight(i, 0)
