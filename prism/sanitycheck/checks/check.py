

import abc
from enum import Enum

class Severity(Enum):
    WARNING = 7123
    ERROR = 7124


class Check(abc.ABC):
      
    def __init__(self, name, label, severity, have_fix):
        self.name = name
        self.label = label
        self.severity = severity
        self.have_fix = have_fix
        self.documentation = ''
        self.message = ''
        self.status = True
        
    @abc.abstractmethod
    def run(self, stateManager):
        return True
    
    @abc.abstractmethod
    def fix(self, stateManager):
        pass