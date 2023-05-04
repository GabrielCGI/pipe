from abc import ABCMeta, abstractmethod


class ShuffleMode:
    __metaclass__ = ABCMeta
    @abstractmethod
    def run(self):
        pass


class MergeShuffleMode(ShuffleMode):
    def run(self):
        # TODO
        print("SHUFFLE")
