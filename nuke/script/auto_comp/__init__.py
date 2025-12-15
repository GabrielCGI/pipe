import importlib
from . import AutoComp
from . import AutoCompFactory
from . import LayoutManager
from . import ShuffleMode
from . import RuleSet
from . import performance_profiler

def main(reload=False):
    if reload:
        importlib.reload(AutoComp)
        importlib.reload(AutoCompFactory)
        importlib.reload(LayoutManager)
        importlib.reload(ShuffleMode)
        importlib.reload(RuleSet)
        importlib.reload(performance_profiler)
    return AutoComp.AutoComp
