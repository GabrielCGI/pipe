import pymel.core as pm

class Zoetrop():
    def __init__(self,data):
        self.data = data
        self.loops = self.get_all_loops()

    def get_all_loops(self):
        loops=[]
        loop_sets = self.loop_sets
        for set in loop_sets:
            members = pm.sets(set, query=True)
            geo = members[0]
            loops.append(Loop(geo,self.data))
        return loops

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
                self.add_loop(geo)
            pm.select(clear=True)

        except Exception as e:
            print("Exception occurred:", e)
            pm.warning("Something went wrong")
        finally:
            pm.undoInfo(state=True)

    def add_loop(self, geo):
        print (self.data)
        new_loop = Loop(geo,self.data)
        new_loop.create_loop()
        self.loops = self.get_all_loops()

    @property
    def loop_sets(self):
        return [set_obj.name() for set_obj in pm.ls(type='objectSet') if set_obj.name().startswith('LP')]

class Loop():
    def __init__(self,geo,data):
        self.start_loop = data[0]
        self.end_loop = data[1]
        self.FPS_maya = data[2]
        self.FPS_loop = data[3]
        self.geo = geo
        #self.samples_val = samples_val

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

    def update_data(self,data):
        self.start_loop = data[0]
        self.end_loop = data[1]
        self.FPS_maya = data[2]
        self.FPS_loop = data[3]

    def create_loop(self):
        # Check if all selected objects have a parent
        self._print_duplication_start_info()
        self.loop_group = self._create_or_replace_group()
        self._apply_rotation_expression(self.loop_group)
        self._generate_frames()
        self._create_loop_set()

    def _create_or_replace_group(self):
        """Creates a new group or replaces if it exists."""

        if pm.objExists(self.loop_group_name):
            pm.delete(self.loop_group_name)

        return pm.group(em=True, name=self.loop_group_name)

    def _apply_rotation_expression(self, group):
        """Applies rotation expression to the given group."""
        rotation_expression = f"{group.name()}.rotateY = floor(frame / {self.modulo}) * {self.angle};"
        pm.expression(s=rotation_expression)

    def _print_duplication_start_info(self):
        """Prints the starting information of the duplication process."""
        print("------ Begins ------")
        print(f"Generating {self.samples} samples")
        print(f"Speed Angle: {self.angle}\n")

    def _generate_frames(self):
        """Duplicates the given object for specified frames and groups them."""
        for frame in range(self.start_loop, self.end_loop):
            if frame % self.modulo == 0:
                pm.currentTime(frame)
                copy_geo = pm.duplicate(self.geo, name=f"frame_{frame}")[0]
                rot_group = pm.group(em=True, name=f"{copy_geo.name()}_rot")

                pm.parent(rot_group, self.loop_group)
                pm.parent(copy_geo , rot_group)
                self.force_visibility_on_children(rot_group)
                #self.hide_frame_over_rig(rot_group,frame,self.modulo)
                print(f"Succes on time: {frame}")

    def rig_visibility(self,state):
        parent = self.geo.getParent()
        try:
            parent.visibility.set(state)
        except Exception as e:
            pm.warning(f"Fail to set visibility to {state} on {parent.name()}")
            print (e)

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

    def _create_loop_set(self):
        if pm.objExists(self.loop_set_name):
            pm.delete(self.loop_set_name)
        loop_set = pm.sets(name=self.loop_set_name, empty=True)
        loop_set.addMember(self.geo)
        self.loop_set=loop_set

    def delete_loop(self):
        try:
            pm.delete(self.loop_group_name)
        except Exception as e:
            pm.warning(f"Delete loop fail {self.loop_group_name}")
            print (e)

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
