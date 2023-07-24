import importlib
from common import utils

utils.unload_packages(silent=True, package="renderer_diagnosis")
importlib.import_module("renderer_diagnosis")
from renderer_diagnosis.RendererDiagnosis import RendererDiagnosis
try:
    rend_diagnos.close()
except:
    pass
rend_diagnos = RendererDiagnosis()
rend_diagnos.show()
