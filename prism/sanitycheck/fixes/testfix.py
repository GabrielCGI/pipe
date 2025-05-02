from . import fix

class TestFix(fix.Fix):
      
    def __init__(self):
        super().__init__(
            name='test_fix',
            label='Test Fix')
    
    def run(self):
        print('Test Fix')