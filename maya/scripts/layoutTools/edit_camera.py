import maya.cmds as cmds


def editCamGate(data):
    for cam in cmds.ls(typ=["camera"]):
        if "persp" in cam:
            continue
        if cmds.camera(cam, q=True, o=True):
            continue

        trySetAttr(f"{cam}.displayFilmGate", data[0])
        trySetAttr(f"{cam}.displayResolution", data[1])
        trySetAttr(f"{cam}.displayGateMask", data[2])
        trySetAttr(f"{cam}.overscan", data[3])
        trySetAttr(f"{cam}.filmFit", data[4])

        trySetAttr(f"{cam}.displayGateMaskOpacity", 0.945)
        try:
            cmds.setAttr(f"{cam}.displayGateMaskColor", 0, 0, 0, type="double3")
        except Exception:
            pass


def createFreeCamFromRig() -> None:
    sel_cam = _camSelected()
    if not sel_cam:
        return
    camera = sel_cam[0]
    grp_cam = cmds.listRelatives(camera, p=True) or []
    if not grp_cam:
        return
    if not cmds.listConnections(grp_cam[0] + ".offsetParentMatrix", s=True) or []:
        return
    grp_cam = grp_cam[0]

    new_cam = cmds.camera(n=f"{camera}_freeCam1")
    rig_origin = _findRigOrigine(camera)
    _createAttr(new_cam[0], "camOrig", camera)
    _createAttr(new_cam[0], "RigOrig", rig_origin)
    try:
        v = cmds.getAttr(camera + ".focusDistance")
        v = 0.000001 if v == 0 else v
        cmds.setAttr(new_cam[1] + ".focusDistance", v)

        v = cmds.getAttr(camera + ".centerOfInterest")
        cmds.setAttr(new_cam[1] + ".centerOfInterest", v)

        v = cmds.getAttr(camera + ".focalLength")
        cmds.setAttr(new_cam[1] + ".focalLength", v)

        v = cmds.getAttr(camera + ".fStop")
        cmds.setAttr(new_cam[1] + ".fStop", v)
    except Exception as e:
        cmds.warning(str(e))
        pass

    trySetAttr(f"{camera}.v", 0)
    trySetAttr(f"{rig_origin}.v", 0)

    cmds.matchTransform(new_cam[0], camera)
    if cmds.objExists("|cameras"):
        cmds.parent(new_cam[0], "|cameras")
    siwtchCamShot(camera, new_cam[0])

def freeCamtoRig(type_world: str) -> None:
    all_selection = cmds.ls(sl=True, typ=["transform"])
    sel_cam = _camSelected(no_freeCam=False)
    if not sel_cam:
        return
    camera = sel_cam[0]

    origin_cam = cmds.getAttr(f"{camera}.camOrig")
    World_Ctr = cmds.getAttr(f"{camera}.RigOrig")
    if not origin_cam or not World_Ctr:
        return

    loc = cmds.spaceLocator(n="tmp_loc_" + camera.replace(":", "_"))
    cmds.matchTransform(loc, camera)

    all_ctrl = cmds.listRelatives(World_Ctr, s=False, ad=True, typ=["transform"]) or []
    all_ctrl.append(World_Ctr)
    resetCtrl(all_ctrl)

    if type_world == "WORLD":
        matchWorld(all_ctrl, loc)
    elif type_world == "OBJECT":
        matchObject(World_Ctr, loc)
    elif type_world == "AIM" and len(all_selection) > 1:
        matchAim(all_ctrl, loc, all_selection[1])
    else:
        cmds.delete(loc)
        return

    trySetAttr(f"{origin_cam}.v", 1)
    trySetAttr(f"{World_Ctr}.v", 1)
    siwtchCamShot(camera, origin_cam)
    cmds.delete(camera)
    cmds.delete(loc)

def siwtchCamShot(old_cam, new_cam):
    all_shot = cmds.sequenceManager(lsh=True)
    for shot in all_shot:
        cam = cmds.shot(shot, q=True, cc=True)
        if cam == old_cam:
            cmds.shot(shot, e=True, cc=new_cam)
            break

def matchWorld(all_ctrl: str, camera: str):
    cmds.matchTransform(all_ctrl[-2], camera, pos=True)
    cmds.matchTransform(all_ctrl[-3], camera, pos=True, scale=True)
    cmds.matchTransform(all_ctrl[-4], camera, rot=True)

def matchObject(World_Ctr: str, camera: str):
    cmds.matchTransform(World_Ctr, camera, pos=True, rot=True, scale=True)

def matchAim(all_ctrl: str, camera: str, sel_cam):
    cmds.matchTransform(all_ctrl[-2], sel_cam, pos=True, rot=True)
    cmds.matchTransform(all_ctrl[-3], camera, pos=True, rot=True)
    cmds.matchTransform(all_ctrl[-4], camera, pos=True, rot=True)


# commun fonction
def _camSelected(no_freeCam=True) -> list[str]:
    all_cam = []
    sel_cam = cmds.ls(sl=True, typ=["transform"])
    if not sel_cam:
        return all_cam

    for cam_trs in sel_cam:
        if "_freeCam" in cam_trs and no_freeCam:
            continue

        child = cmds.listRelatives(cam_trs, s=True) or []
        if not child:
            continue

        if cmds.objectType(child[0]) == "camera":
            all_cam.append(cam_trs)

    return all_cam

def _findRigOrigine(cam) -> str:
    if "rig_origin" not in cmds.attributeInfo(cam, all=True):
        return ""

    rig = cmds.getAttr(f"{cam}.rig_origin")
    split_name = cam.split("|")[-1].split(":")
    if len(split_name) == 1:
        return rig
    else:
        return f"{split_name[0]}:{rig}"

def _createAttr(grp: str, name: str, value: str) -> None:
    if name not in cmds.attributeInfo(grp, all=True):
        cmds.addAttr(grp, longName=name, niceName=name, dataType="string")
    cmds.setAttr(grp + f".{name}", value, type="string")

def trySetAttr(attr: str, value: bool) -> None:
    if cmds.getAttr(attr, l=True) or cmds.listConnections(attr, s=True):
        return

    cmds.setAttr(attr, value)

def resetCtrl(ctrl: list[str]):
    for ctrl in ctrl:
        for attr, value in {
            "sx": 1,
            "sy": 1,
            "sz": 1,
            "rx": 0,
            "ry": 0,
            "rz": 0,
            "tx": 0,
            "ty": 0,
            "tz": 0,
        }.items():
            try:
                cmds.setAttr(f"{ctrl}.{attr}", value)
            except Exception:
                pass
