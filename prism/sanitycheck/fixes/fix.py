
import abc

class Fix(abc.ABC):
      
    def __init__(self, name, label):
        self.name = name
        self.label = label
    
    @abc.abstractmethod
    def run(self):
        pass