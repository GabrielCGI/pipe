import os
import ranchExporter as rex
import unittest

TEST_RESSOURCE_DIR = 'R:/pipeline/pipe/prism/ranch_cache_scripts/unittest_ranchExporter_ressources'

class TestRanchExporter(unittest.TestCase):
    
    def test_log(self):
        import hou
        hip_test = os.path.join(TEST_RESSOURCE_DIR, 'Lighting/prism_filecache.hipnc')
        hou.hipFile.load(hip_test)
        
        import PrismInit
        core = PrismInit.pcore
        sm = core.getStateManager()
        file_cache_state = sm.states[1].ui
        self.assertTrue(True)
        
        
    
    def test_is_list_cache(self):
        import hou
        hip_test = os.path.join(TEST_RESSOURCE_DIR, 'Lighting/prism_filecache.hipnc')
        hou.hipFile.load(hip_test)
        
        import PrismInit
        core = PrismInit.pcore
        sm = core.getStateManager()
        file_cache_state = sm.states[1].ui
        file_cache_node = file_cache_state.node
        render_state = sm.states[3].ui
        kwargs = {
            'state': file_cache_state,
            'scenefile': hou.hipFile.name()
        }
        kwargs_render_node = {
            'state': render_state,
            'scenefile': hou.hipFile.name()
        }
        
        self.assertTrue(rex.is_light_cache(kwargs))
        file_cache_node.parm('depFromScenefile').set(1)
        self.assertTrue(rex.is_light_cache(kwargs))
        file_cache_node.parm("saveMode").set(0)
        self.assertFalse(rex.is_light_cache(kwargs))
        self.assertFalse(rex.is_light_cache(kwargs_render_node))
        
        
    
if __name__ == '__main__':    
    unittest.main()