from datetime import datetime as dt

# Wrap ktl import in try/except so that we can maintain test case or simulator
# version of functions.
try:
    import ktl
    from ktl import Exceptions as ktlExceptions
except ModuleNotFoundError:
    ktl = None

from Keck.Instruments import AbstractInstrument


# -----------------------------------------------------------------------------
# LRIS Blue
# -----------------------------------------------------------------------------
class LRISb(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'LRIS Blue'
        self.optical = True
        self.allowed_sampmodes = [1]
        self.scripts = ["stare"]
        self.binnings = ["1x1", "1x2", "2x2"]
        self.basename = f"b{dt.utcnow().strftime('%Y%m%d')}_"


# -----------------------------------------------------------------------------
# LRIS Red
# -----------------------------------------------------------------------------
class LRISr(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'LRIS Red'
        self.optical = True
        self.allowed_sampmodes = [1]
        self.scripts = ["stare"]
        self.binnings = ["1x1", "1x2", "2x1", "2x2"]
        self.basename = f"r{dt.utcnow().strftime('%Y%m%d')}_"
