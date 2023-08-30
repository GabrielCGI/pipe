import pymel.core as pm
import math
class Zoetrop():
    def __init__(self,data):
        self.data = data
        self.loops = self.get_all_loops()

    def get_all_loops(self):

        loop_sets = [set_obj.name() for set_obj in pm.ls(type='objectSet') if set_obj.name().startswith('LP')]
        loops=[]
        for set in loop_sets:
            members = pm.sets(set, query=True)
            if members and len(members)==1:
                geo = members[0]
                loops.append(Loop(geo,self.data))
        return loops

    @staticmethod
    def read_loop_attributs_from_standIn(node):
        """
        Imports an Alembic into the Maya scene, reads specified attributes from the top parent, and deletes the Alembic.

        :param alembic_path: Path to the Alembic file.
        :param attributes_list: List of attributes to read from the top parent of the imported Alembic.
        :return: Dictionary containing attribute values. If an attribute does not exist, its value will be None.
        """
        loop_attributes_template = ['data_start_loop', 'data_end_loop', 'data_FPS_maya', 'data_FPS_loop', 'data_motion']
        if pm.nodeType(node) == 'transform':
            shapes = pm.listRelatives(node, shapes=True, type='aiStandIn')
            if not shapes:
                pm.warning("No standin found")
                raise ValueError(f"No aiStandIn shape found under transform: {node}")
            node = shapes[0]
        if pm.nodeType(node) != 'aiStandIn':
            pm.warning("No standin found")
            raise ValueError(f"Node {node} is not an aiStandIn object.")
        alembic_path = node.dso.get()
        print(alembic_path)
        # Import the Alembic into the Maya scene
        imported_nodes = pm.importFile(alembic_path, returnNewNodes=True)

        # Ensure we imported something
        if not imported_nodes:
            pm.warning("Failed to import Alembic.")
            return None

        # The top parent (usually the transform node) should be the first in the list
        top_parent = imported_nodes[0]

        # Read attributes from the provided list
        loop_attributes = {}
        for attr_name in loop_attributes_template:
            if pm.hasAttr(top_parent, attr_name):
                loop_attributes[attr_name] = pm.getAttr(top_parent + "." + attr_name)
            else:
                loop_attributes[attr_name] = None

        pm.delete(imported_nodes)
        return loop_attributes

    def create_loop_from_selection(self):
        selected = pm.selected()
        if not selected:
            pm.warning("Please select a geometry to duplicate.")
            return

        # Check if all selected objects have a parent
        for obj in selected:
            if not obj.getParent():
                pm.warning(f"{obj} does not have a parent. Aborting.")
                return

        try:
            pm.undoInfo(state=False)
            for geo in selected:
                new_loop = Loop(geo,self.data)
                new_loop.create_loop()

            pm.select(clear=True)

        except Exception as e:
            print("Exception occurred:", e)
            pm.warning("Something went wrong")
        finally:
            pm.undoInfo(state=True)
            self.loops = self.get_all_loops()

    @staticmethod

    def set_key(node, data):
        result = pm.confirmDialog(title='Confirm Action',
                                  message=f'Are you sure you want to set these keys on {node.name()}? \nThis will disconnect existing connections to rotateY.',
                                  button=['Yes', 'No'],
                                  defaultButton='Yes',
                                  cancelButton='No',
                                  dismissString='No')

        if result == 'No':
            pm.warning("Operation cancelled by user.")
            return
        pm.undoInfo(openChunk=True)
        loop = Loop(node, data)
        input_plug = pm.listConnections(node.rotateY, plugs=True, d=False, s=True)
        if input_plug:
            pm.disconnectAttr(input_plug[0], node.rotateY)

        for frame in range(0, 301):  # Including 300, hence 301 as the stop value
            rot_value = math.floor(frame / loop.modulo) * loop.angle
            node.rotateY.setKey(time=frame, value=rot_value)
            pm.keyTangent(node, edit=True, time=(frame,), attribute='rotateY', inTangentType='linear', outTangentType='linear')
        pm.undoInfo(closeChunk=True)

class Loop():
    def __init__(self,geo,data):
        self.update_data(data)
        self.geo = geo
        self.pretty_name = "pretty_name"

    @property
    def modulo(self):
        return self.FPS_maya / self.FPS_loop

    @property
    def duration(self):
        return self.end_loop- self.start_loop

    @property
    def samples(self):
        return self.FPS_loop * (self.duration / self.FPS_maya)

    @property
    def loop_group_name(self):
        parent_name = self.geo.getParent().replace(':',"NS")
        loop_group_name = f"LOOP_{parent_name}"
        return loop_group_name

    @property
    def angle(self):
        return 360 / self.samples

    @property
    def loop_set_name(self):
        parent_name = self.geo.getParent().replace(':',"NS")
        return f"LP_{parent_name}"

    @property
    def is_aiStandIn(self):
        if not pm.objExists(self.geo):
            return False

        # If the given node is a transform, get its shape children.
        if pm.nodeType(self.geo) == "transform":
            shape_nodes = pm.listRelatives(self.geo, shapes=True)
            if shape_nodes:
                return pm.nodeType(shape_nodes[0]) == 'aiStandIn'

        return False



    # Fetch and print the attribute values

    @staticmethod
    def safe_get_standIn_shape(node):
        if pm.nodeType(node) == 'transform':
            shapes = pm.listRelatives(node, shapes=True, type='aiStandIn')
            if not shapes:
                raise ValueError(f"No aiStandIn shape found under transform: {node}")
            node = shapes[0]
        if pm.nodeType(node) != 'aiStandIn':
            raise ValueError(f"Node {node} is not an aiStandIn object.")
        return node

    @staticmethod
    def freezeStandin(node,frame):
        node = Loop.safe_get_standIn_shape(node)
        connected_exprs = pm.listConnections(node.frameNumber, type='expression')
        if connected_exprs:
            print("exp delete")
            for expr in connected_exprs:
                pm.delete(expr)
        node.frameNumber.set(frame)
        # Set useFrameExtension to 0.
        node.useFrameExtension.set(0)

    @staticmethod
    def force_visibility_on_children(target):
        # Define a helper function to force set visibility
        def force_visibility(node):
            if node.hasAttr('visibility'):
                # If there's a connection, disconnect it
                if node.visibility.isDestination():
                    pm.disconnectAttr(node.visibility.listConnections(s=True, d=False, p=True)[0], node.visibility)
                    pm.warning(f"Disconnected existing visibility connection on: {node}")

                # Unlock if it's locked
                if node.visibility.isLocked():
                    node.visibility.unlock()
                    pm.warning(f"Unlocked visibility attribute on: {node}")

                # Set the visibility
                node.visibility.set(1)

        # Forcefully set visibility for the main target
        force_visibility(target)

        # Get the immediate children of the object
        children = target.getChildren(noIntermediate=True, fullPath=True)  # Fetch immediate children. Add other flags if needed.

        for child in children:
            force_visibility(child)
            # If you want to handle nested children, you can recursively call this function:
            # force_visibility_on_children(child)

    ### DATA MANAGEMENT ###
    def update_data(self,data):
        self.start_loop = data[0]
        self.end_loop = data[1]
        self.FPS_maya = data[2]
        self.FPS_loop = data[3]
        self.motion = data[4]

    def write_data_attributs(self):
        """Adds custom data attributes to self.geo."""

        # Ensure the node exists.
        if not pm.objExists(self.geo):
            pm.warning(f"Node {self.geo} does not exist. Cannot add attributes.")
            return

        # Define the attributes and their types to add.
        attributes = {
            'data_start_loop': 'double',
            'data_end_loop': 'double',
            'data_FPS_maya': 'double',
            'data_FPS_loop': 'double',
            'data_motion' : 'double'
        }
        # Add each attribute if it doesn't exist and set its value.
        for attr_name, attr_type in attributes.items():
            if not pm.attributeQuery(attr_name, node=self.geo, exists=True):
                pm.addAttr(self.geo, longName=attr_name, attributeType=attr_type, keyable=True)

            pm.setAttr(f"{self.geo}.{attr_name}", getattr(self, attr_name[len("data_"):])) #remove "data_" prefix and map maya attribut to class attribut


        pm.warning(f"Data attributes added to {self.geo}.")


    def read_data_attributs(self):
        if not pm.objExists(self.geo):
            pm.warning(f"Node {self.geo} does not exist. Cannot read attributes.")
            return None

        attributes = ['data_start_loop', 'data_end_loop', 'data_FPS_maya', 'data_FPS_loop','data_motion']

        attribute_values = []

        for attr_name in attributes:
            if pm.attributeQuery(attr_name, node=self.geo, exists=True):
                attribute_values.append(pm.getAttr(f"{self.geo}.{attr_name}"))
            else:
                pm.warning(f"Attribute {attr_name} does not exist on node {self.geo}.")
                return None
        pm.warning(f"Data attributes read from {self.geo}.")
        return attribute_values

    def check_data_difference(self, new_data):
        """Checks if provided data matches existing data attributes on the node."""
        existing_data = self.read_data_attributs()
        # If there's no existing data or data doesn't match
        if not existing_data or existing_data != new_data:
            # Perform any actions or return a value indicating a difference
            # For example, you can raise an exception or return a boolean indicating difference
            self.prompt_user_select_data(new_data, existing_data)
        # If data matches, return True or perform other desired operations
        return True

    def prompt_user_select_data(self, new_data, existing_data):
        """Prompts user whether to keep the existing data or update with new data."""
        import pymel.core as pm

        attributes_list = ['start_loop', 'end_loop', 'FPS_maya', 'FPS_loop','motion']

        # Building the message string
        message_lines = [f"Loop parameters are different for {self.pretty_name} \n"]
        try:
            for attr, old_val, new_val in zip(attributes_list, existing_data, new_data):
                if old_val != new_val:
                    message_lines.append(f"{attr}:\tOld: {old_val}\tNew: {new_val}")
        except Exception as e:
            pm.warning("Fail to compare data")
            print (e)
        # If there are no differences, exit the function
        if len(message_lines) == 1:
            print("No differences found between new and existing data.")
            return

        message = "\n".join(message_lines)

        result = pm.confirmDialog(
            title='Data Difference Detected',
            message=message,
            button=['Keep', 'Replace'],
            defaultButton='Keep',
            cancelButton='Keep',
            dismissString='Keep'
        )

        if result == 'Replace':
            # Here you can update the data attributes with new data
            self.update_data(new_data)
            self.write_data_attributs()
            pm.warning("Data attributes updated.")
        else:
            self.update_data(existing_data)
            pm.warning("Retained existing data attributes.")

    ### LOOP OPERATIONS ###
    def create_loop(self):
        # Check if all selected objects have a parent
        current_frame = pm.currentTime(query=True)
        self._print_duplication_start_info()
        self._create_or_replace_group()
        self._apply_rotation_expression()
        self._generate_frames()
        self._create_loop_set()
        self.write_data_attributs()
        pm.currentTime(current_frame)
        self._restore_parent()

    def delete_loop(self):
        try:
            pm.delete(self.loop_group_name)
        except Exception as e:
            pm.warning(f"Delete loop fail {self.loop_group_name}")
            print (e)

    ### INTERNAL UTILITIES ###
    def _generate_frames(self):
        """Duplicates the given object for specified frames and groups them."""
        counter = 0
        new_end_loop= int(self.end_loop + ((self.motion*-1)*self.modulo))
        parent = self.geo.getParent()
        parent_visibility_state= parent.visibility.get()
        try:
            parent.visibility.set(1)
        except:
            pm.warning("fail to set visibility on parent:"+parent.name())
        for frame in range(self.start_loop, new_end_loop):

            if frame % self.modulo == 0:
                pm.currentTime(frame)
                frame_name = f"frame_{self.pretty_name}_{frame}"
                if self.is_aiStandIn:
                    copy_geo = pm.duplicate(self.geo,  name=frame_name , rr=True, ic=True)[0]
                    print(copy_geo)
                    self.freezeStandin(copy_geo,frame)
                else:
                    copy_geo = pm.duplicate(self.geo, name=frame_name)[0]

                rot_group = pm.group(em=True, name=f"{copy_geo.name()}_rot")
                extra_rot =0


                counter +=1
                pm.parent(rot_group, self.loop_group)
                pm.parent(copy_geo , rot_group)


                self.force_visibility_on_children(rot_group)
                #self.hide_frame_over_rig(rot_group,frame,self.modulo)
                print(f"Succes on time: {frame}")
        #restore visibility rig
        try:
            parent.visibility.set(parent_visibility_state)
        except:
            pm.warning("fail to set visibility on parent:"+parent.name())
    def _create_or_replace_group(self):
        """Creates a new group or replaces it if it exists, while preserving the original parent."""

        self.parent_loop_group = None
        if pm.objExists(self.loop_group_name):
            # Store the parent of the group if it exists before deletion
            self.parent_loop_group = pm.listRelatives(self.loop_group_name, parent=True)
            pm.delete(self.loop_group_name)
        # Create a new group
        self.loop_group = pm.group(em=True, name=self.loop_group_name)

    def _apply_rotation_expression(self):
        """Applies rotation expression to the given group."""
        rotation_expression = f"{self.loop_group.name()}.rotateY = floor(frame / {self.modulo}) * {self.angle};"
        pm.expression(s=rotation_expression)

    def _restore_parent(self):
        if self.parent_loop_group:
            pm.parent(self.loop_group,self.parent_loop_group)

    def _print_duplication_start_info(self):
        """Prints the starting information of the duplication process."""
        print("------ Begins ------")
        print(f"Generating {self.samples} samples")
        print(f"Speed Angle: {self.angle}\n")

    def rig_visibility(self,state):
        parent = self.geo.getParent()
        try:
            parent.visibility.set(state)
        except Exception as e:
            pm.warning(f"Fail to set visibility to {state} on {parent.name()}")
            print (e)

    def _create_loop_set(self):
        if pm.objExists(self.loop_set_name):
            pm.delete(self.loop_set_name)
        loop_set = pm.sets(name=self.loop_set_name, empty=True)
        loop_set.addMember(self.geo)
        self.loop_set=loop_set


### OLD ####### OLD ####### OLD ####### OLD ####### OLD ####### OLD ####### OLD ####
    @staticmethod
    def hide_frame_over_rig(frame, start_range, loop_modulo):
        self.force_visibility_on_children(frame)
        expression_name = f"{frame.name()}_visExpression"
        end_range = start_range + loop_modulo - 1
        expression_str = f"""
        if (frame >= {start_range} && frame <= {end_range})
            {frame.nodeName()}.visibility = 0;
        else
            {frame.nodeName()}.visibility  = 1;
        """
        if pm.objExists(expression_name):
            pm.expression(expression_name, edit=True, s=expression_str)
        else:
            pm.expression(name=expression_name, s=expression_str)

    def setup_visibility(self, obj, loop):
        """Configures visibility settings for the given object."""

        target = obj.getParent().visibility

        expression_name = f"{target}_visExpression".replace(".","_")
        expression_str = f"""

        if (frame >= {loop.end_loop})
            {target} = 0;
        else
            {target} = 1;
        """

        if pm.objExists(expression_name):
            pm.expression(expression_name, edit=True, s=expression_str)
        else:
            if target.isDestination():
                source_attr = target.getInput(p=True)
                if source_attr:
                    print("disconet")
                    pm.disconnectAttr(source_attr, target)
            pm.expression(name=expression_name, s=expression_str)
        print (f"Visibility set on {target}")
