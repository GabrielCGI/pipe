import pymel.core as pm
import pymel.core.datatypes as dt
from gf_animtools.rig.at_base_objects import ModGroup, RigControl


class LimbsGroup(ModGroup):
    NODE_TYPE = 'modLimbs'

    def __init__(self, node_name):
        super(LimbsGroup, self).__init__(node_name=node_name)

    @property
    def typeId(self):
        """
        0 = Arm
        1 = Leg
        """
        return self.node.param_limbType.get()

    @property
    def jointsName(self):
        return (['ArmClav', 'Shoulder', 'Elbow', 'Hand'], ['HipClav', 'Hip', 'Knee', 'Foot'])[self.typeId]

    @property
    def typeName(self):
        return ['Arm', 'Leg'][self.typeId]

    @property
    def clavicle(self):
        return self.node.param_clavicle.get()

    def getCtrNames(self):
        userAttributes = self.getUserAttr()
        jNames = self.jointsName
        sfx = self.mod_suffix
        name = self.mod_name
        xNme = userAttributes.get('extraName', '')

        # # ----- Compute Names ----- #
        # dic = {'fk_shoulder':'Fk' + jNames[1] + xNme + sfx,
        #        'fk_elbow': 'Fk' + jNames[2] + xNme + sfx,
        #        'fk_hand': 'Fk' + jNames[3] + xNme + sfx,
        #        'pole_vector': 'Pv' + jNames[2] + xNme + sfx,
        #        'ik_hand': jNames[3] + xNme + sfx,
        #        'limb_options': name + 'Options' + xNme + sfx,
        #        'bend_shoulder': 'Bend' + jNames[1] + xNme + sfx,
        #        'bend_elbow': 'Bend' + jNames[2] + xNme + sfx,
        #        'bend_hand': 'Bend' + jNames[3] + xNme + sfx}

        dic = self.rig.namingConvention.getLimbsCtrNames(self.typeId, name, xNme)
        dic = {k: v + sfx for k, v in dic.items()}
        if not self.clavicle:
            del dic['clav']

        return dic

    def getJntNames(self):
        userAttributes = self.getUserAttr()
        jNames = self.jointsName
        sfx = self.mod_suffix
        xNme = userAttributes.get('extraName', '')
        ns = self.namespace()

        # ----- Compute Names ----- #
        dic = {'shoulder': ns + ':' + jNames[1] + xNme + '_Sk' + sfx,
               'elbow': ns + ':' + jNames[2] + xNme + '_Sk' + sfx,
               'wrist': ns + ':' + jNames[3] + xNme + '_Sk' + sfx}

        if self.clavicle:
            dic['clav'] = ns + ':' + jNames[0] + xNme + '_Sk' + sfx

        return dic

    @property
    def joints(self):
        result = {}
        for k, v in self.getJntNames().items():
            result[k] = pm.PyNode(v)
        return result

    def ikFkSwitch(self):
        ctrNames = self.getCtrNames()
        controllers = self.controllers
        joints = self.joints

        if self.clavicle:
            clavicle = RigControl.findFromName(ctrNames['clav'], controllers)
        fk_shoulder = RigControl.findFromName(ctrNames['fk_shoulder'], controllers)
        fk_elbow = RigControl.findFromName(ctrNames['fk_elbow'], controllers)
        fk_hand = RigControl.findFromName(ctrNames['fk_hand'], controllers)
        ik_hand = RigControl.findFromName(ctrNames['ik_hand'], controllers)
        pole_vector = RigControl.findFromName(ctrNames['pole_vector'], controllers)
        limb_options = RigControl.findFromName(ctrNames['limb_options'], controllers)

        jnt_shoulder = joints['shoulder']
        jnt_elbow = joints['elbow']
        gp_hand = self.extremityGp.get()

        if self.clavicle:
            jnt_clavicle = joints['clav']
            clavMtx = clavicle.worldMatrix.get()

        if limb_options.IKFK.get():     # FK to IK
            print('FK to IK')
            ik_hand.setMatrix(gp_hand.worldMatrix.get(), worldSpace=True)
            pole_vector.setMatrix(jnt_elbow.worldMatrix.get(), worldSpace=True)
            limb_options.IKFK.set(0)
            if self.clavicle:
                clavicle.setMatrix(clavMtx, worldSpace=True)

        else:
            ref_before = {
                "shoulder": jnt_shoulder.worldMatrix.get(),
                "elbow": jnt_elbow.worldMatrix.get(),
                "hand": gp_hand.worldMatrix.get(),
            }
            if self.clavicle:
                ref_before['clav'] = jnt_clavicle.worldMatrix.get()

            # switch to FK here
            limb_options.IKFK.set(1)

            # --- AFTER SWITCH (FK) ---
            if self.clavicle:
                apply_fk_from_refs(ref_before["clav"], jnt_clavicle, clavicle)
            apply_fk_from_refs(ref_before["shoulder"], jnt_shoulder, fk_shoulder)
            apply_fk_from_refs(ref_before["elbow"], jnt_elbow, fk_elbow)
            apply_fk_from_refs(ref_before["hand"], gp_hand, fk_hand)


class QLimbsGroup(LimbsGroup):
    NODE_TYPE = 'modQLimbs'

    @property
    def jointsName(self):
        return (['ArmClav', 'Shoulder', 'Elbow', 'Hand', 'Wrist'],
                ['HipClav', 'Hip', 'Knee', 'Foot', 'Ankle'])[self.typeId]

    def getCtrNames(self):
        dic = super(QLimbsGroup, self).getCtrNames()
        userAttributes = self.getUserAttr()
        jNames = self.jointsName
        sfx = self.mod_suffix
        xNme = userAttributes.get('extraName', '')

        # ----- Compute Names ----- #
        dic['fk_wrist'] = 'Fk' + jNames[4] + xNme + sfx
        dic['ik_wrist'] = jNames[4] + xNme + sfx

        return dic

    def getJntNames(self):
        dic = super(QLimbsGroup, self).getJntNames()
        userAttributes = self.getUserAttr()
        jNames = self.jointsName
        sfx = self.mod_suffix
        xNme = userAttributes.get('extraName', '')
        ns = self.namespace()

        # ----- Compute Names ----- #
        dic['wrist_root'] = ns + ':' + jNames[4] + 'Root' + xNme + '_Sk' + sfx
        dic['wrist_end'] = ns + ':' + jNames[4] + 'End' + xNme + '_Sk' + sfx

        return dic

    def ikFkSwitch(self):
        ctrNames = self.getCtrNames()
        controllers = self.controllers
        joints = self.joints

        if self.clavicle:
            clavicle = RigControl.findFromName(ctrNames['clav'], controllers)
        fk_shoulder = RigControl.findFromName(ctrNames['fk_shoulder'], controllers)
        fk_elbow = RigControl.findFromName(ctrNames['fk_elbow'], controllers)
        fk_hand = RigControl.findFromName(ctrNames['fk_hand'], controllers)
        fk_wrist = RigControl.findFromName(ctrNames['fk_wrist'], controllers)
        ik_hand = RigControl.findFromName(ctrNames['ik_hand'], controllers)
        ik_wrist = RigControl.findFromName(ctrNames['ik_wrist'], controllers)
        pole_vector = RigControl.findFromName(ctrNames['pole_vector'], controllers)
        limb_options = RigControl.findFromName(ctrNames['limb_options'], controllers)

        jnt_shoulder = joints['shoulder']
        jnt_elbow = joints['elbow']
        jnt_wrist_root = joints['wrist_root']
        jnt_wrist_end = joints['wrist_end']
        gp_hand = self.extremityGp.get()

        if self.clavicle:
            jnt_clavicle = joints['clav']
            clavMtx = clavicle.worldMatrix.get()

        if limb_options.IKFK.get():     # FK to IK
            elbow_mtx = jnt_elbow.worldMatrix.get()
            fk_wrist_root_mtx = jnt_wrist_root.worldMatrix.get()

            # build ik hand matrix
            ik_hand_mtx = dt.TransformationMatrix(gp_hand.worldMatrix.get())
            wrist_end_mtx = dt.TransformationMatrix(jnt_wrist_end.worldMatrix.get())
            ik_hand_mtx.setTranslation(wrist_end_mtx.getTranslation('world'), 'world')
            ik_hand_mtx = ik_hand_mtx.matrix

            ik_hand.setMatrix(ik_hand_mtx, worldSpace=True)
            limb_options.IKFK.set(0)

            # build ik wrist matrix
            ik_wrist_root_mtx = jnt_wrist_root.worldMatrix.get()
            wrist_ik_space = ik_wrist.worldMatrix.get() * ik_wrist_root_mtx.inverse()
            new_ik_wrist = wrist_ik_space * fk_wrist_root_mtx

            ik_wrist.setMatrix(new_ik_wrist, worldSpace=True)
            pole_vector.setMatrix(elbow_mtx, worldSpace=True)
            if self.clavicle:
                clavicle.setMatrix(clavMtx, worldSpace=True)

        else:       # IK to FK
            ref_before = {
                "shoulder": jnt_shoulder.worldMatrix.get(),
                "elbow": jnt_elbow.worldMatrix.get(),
                "hand": jnt_wrist_root.worldMatrix.get(),
                "wrist":gp_hand.worldMatrix.get(),
            }
            if self.clavicle:
                ref_before['clav'] = jnt_clavicle.worldMatrix.get()

            # switch to FK here
            limb_options.IKFK.set(1)

            # --- AFTER SWITCH (FK) ---
            if self.clavicle:
                apply_fk_from_refs(ref_before["clav"], jnt_clavicle, clavicle)
            apply_fk_from_refs(ref_before["shoulder"], jnt_shoulder, fk_shoulder)
            apply_fk_from_refs(ref_before["elbow"], jnt_elbow, fk_elbow)
            apply_fk_from_refs(ref_before["hand"], jnt_wrist_root, fk_hand)
            apply_fk_from_refs(ref_before["wrist"], gp_hand, fk_wrist)


def compute_fk_target_from_refs(ref_before_mtx, ref_after_node, control):
    """
    ref_before_mtx: pm.datatypes.Matrix stored in IK mode (ref world matrix BEFORE switch)
    ref_after_node: PyNode of the same reference object AFTER switch (now in FK mode)
    control:        PyNode of the FK control AFTER switch
    """

    # current matrices (after switch)
    ref_after_matrix = ref_after_node.worldMatrix.get()
    fk_world_mtx = control.worldMatrix.get()
    fk_parent = control.getParent().worldMatrix.get()

    # delta between CURRENT ref and CURRENT fk
    delta_mtx = fk_world_mtx * ref_after_matrix.inverse()

    # target world matrix for FK (delta applied to BEFORE ref)
    target_world_mtx = delta_mtx * ref_before_mtx

    # convert to FK local
    fk_local_mtx = target_world_mtx * fk_parent.inverse()

    return fk_local_mtx

def apply_fk_from_refs(ref_before_mtx, ref_after_node, control):
    fk_local_mtx = compute_fk_target_from_refs(ref_before_mtx, ref_after_node, control)
    control.setMatrix(fk_local_mtx, objectSpace=True)
