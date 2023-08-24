import pymel.core as pm

def convert_single_joint_skin_to_parent_constraint():
    # Get all skin clusters in the scene
    skin_clusters = pm.ls(type="skinCluster")

    for skin_cluster in skin_clusters:
        # Get the influence objects (joints) for each skin cluster
        influences = skin_cluster.getInfluence()


        # If there's only one influence object
        if len(influences) == 1:
            # Get the geometry associated with the skin cluster
            geometry = skin_cluster.getGeometry()[0]
            geo_transform = geometry.getTransform()


            # Unlock the necessary attributes on the geometry's transform
            attrs_to_unlock = ['translateX', 'translateY', 'translateZ',
                               'rotateX', 'rotateY', 'rotateZ',
                               'scaleX', 'scaleY', 'scaleZ']
            for attr in attrs_to_unlock:
                pm.setAttr(f"{geo_transform}.{attr}", lock=False)

            # Create a parent constraint from the joint to the geometry
            pm.parentConstraint(influences[0], geo_transform, maintainOffset=True)

            # Create a scale constraint from the joint to the geometry
            pm.scaleConstraint(influences[0], geo_transform, maintainOffset=True)
            print(f"Skin {skin_cluster} replaced on {geo_transform.name()}")
            # Delete the skin cluster
            pm.delete(skin_cluster)
    print("done !")
convert_single_joint_skin_to_parent_constraint()
