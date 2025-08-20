# This file has intentional violations for pylint testing

import os,sys    # Violation: imports on one line
from typing import *  # Violation: import *

# Violation: Missing module docstring

class badClass:  # Violation: class name is not PascalCase
    def __init__(self):
        self.someVar = None  # Violation: Variable name is not snake_case
        
    def badMethod(self, reallyReallyLongParameterNameThatViolatesGoogleStyleGuideRules):  # Violation: very long line
        pass  # Violation: method without docstring

def bad_function():  # Violation: function without docstring
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24+25  # Violation: long line
    return x

# Violation: code at the end without if __name__ == "__main__"
bad_function()