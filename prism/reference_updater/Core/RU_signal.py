



class Signal():
    def __init__(self):
        self.container = []

    def connect(self, connection):
        self.container.append(connection)

    def emits(self, info):
        for cd in self.container:
            cd(info)



signal = Signal()