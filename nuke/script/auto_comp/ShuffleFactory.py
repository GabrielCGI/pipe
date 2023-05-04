from .ShuffleMode import MergeShuffleMode

_SHUFFLE_MODE_DATA = {
    "MergeShuffle": MergeShuffleMode
}


class ShuffleFactory:
    def get_shuffle_mode(self, id):
        if id in _SHUFFLE_MODE_DATA:
            return _SHUFFLE_MODE_DATA[id]()
        return None
