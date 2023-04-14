import importlib
import maya.mel as mel
import pymel.core as pm
from standin_utils import *
import replace_by_tx
import CollectorCopier
from CollectorCopier import *


def get_out_of_date_standins():
    standins = pm.ls(type="aiStandIn")
    out_of_date_standins = []
    for standin in standins:
        parsed_standin = parse_standin(standin)
        if parsed_standin["valid"]:
            object_name = parsed_standin["object_name"]
            active_variant = parsed_standin["active_variant"]
            standin_versions = parsed_standin["standin_versions"]
            active_version = parsed_standin["active_version"]
            last_version = standin_versions[active_variant][0][0]
            if active_version != last_version:
                out_of_date_standins.append((object_name, active_version, last_version))
    return out_of_date_standins


def run(force_override_ass_paths_files):
    out_of_date_standins = get_out_of_date_standins()
    if len(out_of_date_standins) > 0:
        max_display_standins = 15
        msg = "You have out of date Standin(s) :\n\n"
        for index, standin_data in enumerate(out_of_date_standins):
            if index == max_display_standins:
                nb_remaining = len(out_of_date_standins) - max_display_standins
                msg += "\n" + str(nb_remaining) + " other(s) standins ...\n"
                break
            msg += str(standin_data[0]) + " : \n        actual : " + str(standin_data[1]) + \
                "\n        latest : " + str(standin_data[2]) + "\n"
        msg += "\nYou should update them with the Asset Loader.\nDo you want to continue ?"
        answer_out_of_date_standins = confirmDialog(
            title='Out of date StandIn(s)',
            icon="question",
            message=msg,
            button=['Continue', 'Cancel'],
            defaultButton='Continue',
            dismissString='Cancel',
            cancelButton='Cancel')
        if answer_out_of_date_standins != "Continue":
            return

    answer_submit = confirmDialog(
        title='Confirm Submit to Deadline Ranch',
        icon="question",
        message="How do you want to save the scene before submitting the job ?",
        button=['Increment and Save', 'Skip', 'Cancel'],
        defaultButton='Skip',
        dismissString='Cancel')
    skip = answer_submit == "Skip"
    increment_and_save = answer_submit == "Increment and Save"
    if skip or increment_and_save:
        pm.setAttr("defaultArnoldRenderOptions.procedural_searchpath", "X:/;Y:/;Z:/;I:/;B:/;R:/")
        pm.setAttr("defaultArnoldRenderOptions.texture_searchpath", "X:;Y:;Z:;I:;B:")
        pm.setAttr("defaultArnoldRenderOptions.absoluteTexturePaths", False)
        pm.setAttr("defaultArnoldRenderOptions.absoluteProceduralPaths", False)

        print("Start replacing by tx")
        replace_by_tx.replace_by_tx()

        # Increment and save
        if increment_and_save:
            pm.mel.eval('incrementAndSaveScene 0;')

        # Collect all the paths in the scene and copy them to RANCH
        collector_copier = CollectorCopier(force_override_ass_paths_files)
        collector_copier.run_collect()

        # Run modified submit to deadline
        pm.mel.eval('source "R:/deadline/submission/Maya/Main/SubmitMayaToDeadlineRanch.mel";SubmitMayaToDeadlineRanch;')
