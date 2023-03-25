import importlib
import maya.mel as mel
from pymel.core import *
import replace_by_tx
import CollectorCopier
from CollectorCopier import *


def run(force_override_ass_paths_files):
    answer_delete = confirmDialog(
        title='Confirm Submit to Deadline Ranch',
        icon="question",
        message="Do you really want to send all the data from this scene "
                "to the RANCH server and start sending a new job to the Illogic farm ?",
        button=['Yes', 'No'],
        defaultButton='Yes',
        dismissString='No')
    if answer_delete == "Yes":
        setAttr("defaultArnoldRenderOptions.procedural_searchpath", "X:/;Y:/;Z:/;I:/;B:/;R:/")
        setAttr("defaultArnoldRenderOptions.texture_searchpath", "X:;Y:;Z:;I:;B:;R:")
        setAttr("defaultArnoldRenderOptions.absoluteTexturePaths", False)
        setAttr("defaultArnoldRenderOptions.absoluteProceduralPaths", False)

        print ("Start replacing by tx")
        replace_by_tx.replace_by_tx()

        # Increment and save
        mel.eval('incrementAndSaveScene 0;')

        # Collect all the paths in the scene and copy them to RANCH
        collector_copier = CollectorCopier(force_override_ass_paths_files)
        collector_copier.run_collect()

        # Run modified submit to deadline
        mel.eval('source "R:/deadline/submission/Maya/Main/SubmitMayaToDeadlineRanch.mel";SubmitMayaToDeadlineRanch;')