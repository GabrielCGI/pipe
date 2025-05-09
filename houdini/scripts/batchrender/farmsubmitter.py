import sys
import PrismInit

USD_PLUGIN = PrismInit.pcore.getPlugin('USD')
LOP_RENDER = USD_PLUGIN.api.lopRender

loprender_module = sys.modules[LOP_RENDER.__module__]

class Farm_Submitter(loprender_module.Farm_Submitter):
    
    def __init__(self, origin, states, kwargs):
        super().__init__(origin, states[0], kwargs)
        self.states = states
    
    def set_states(self):
        state = self.state
        priority = state.ui.sp_rjPrio.text()
        frame_per_task = state.ui.sp_rjFramesPerTask.text()
        task_timeout = state.ui.sp_rjTimeout.text()
        submit_suspended = state.ui.chb_rjSuspended.isChecked()
        submit_cleanup_job = state.ui.chb_cleanup.isChecked()
        concurrent_tasks = state.ui.sp_dlConcurrentTasks.text()
        machine_limit = state.ui.sp_machineLimit.text()
        pool_preset = state.ui.cb_dlPreset.currentText()
        submit_high_prio_job = state.ui.gb_prioJob.isChecked()
        high_prio_job_priority = state.ui.sp_highPrio.text()
        high_prio_job_frames = state.ui.e_highPrioFrames.text()
        
        for state in self.states:
            state.ui.sp_rjPrio.setValue(int(priority))
            state.ui.sp_rjFramesPerTask.setValue(int(frame_per_task))
            state.ui.sp_rjTimeout.setValue(int(task_timeout))
            state.ui.chb_rjSuspended.setChecked(submit_suspended)
            state.ui.chb_cleanup.setChecked(submit_cleanup_job)
            state.ui.sp_dlConcurrentTasks.setValue(int(concurrent_tasks))
            state.ui.sp_machineLimit.setValue(int(machine_limit))
            state.ui.cb_dlPreset.setCurrentText(pool_preset)
            state.ui.gb_prioJob.setChecked(submit_high_prio_job)
            state.ui.sp_highPrio.setValue(int(high_prio_job_priority))
            state.ui.e_highPrioFrames.setText(high_prio_job_frames)
            
    
    def submit(self):
        self.hide()
        self.state.ui.gb_submit.setCheckable(True)
        self.state.ui.gb_submit.setChecked(True)
        
        self.set_states()

        sanityChecks = bool(self.kwargs["node"].parm("sanityChecks").eval())
        version = 'next'
        saveScene = bool(self.kwargs["node"].parm("saveScene").eval())
        incrementScene = saveScene and bool(
            self.kwargs["node"].parm("incrementScene").eval()
        )

        sm = self.core.getStateManager()
        
        result = sm.publish(
            successPopup=False,
            executeState=True,
            states=self.states,
            useVersion=version,
            saveScene=saveScene,
            incrementScene=incrementScene,
            sanityChecks=sanityChecks,
            versionWarning=False,
        )
        
        if result:
            msg = "Job submitted successfully."
            self.core.popup(msg, severity="info")

        self.close()