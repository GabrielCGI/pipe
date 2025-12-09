import importlib
from . import AutoComp
from . import AutoCompFactory
from . import LayoutManager
from . import ShuffleMode
from . import RuleSet


def main(reload=False):
    if reload:
        importlib.reload(AutoComp)
        importlib.reload(AutoCompFactory)
        importlib.reload(LayoutManager)
        importlib.reload(ShuffleMode)
        importlib.reload(RuleSet)
    return AutoComp.AutoComp
