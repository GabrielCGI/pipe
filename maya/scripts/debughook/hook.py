
import PrismInit

from . import debug


def main():
    debug.debug()
    debug.debugpy.breakpoint()

    core = PrismInit.pcore

    state_manager = core.getStateManager()
    states = state_manager.states
    
    pass
