from datetime import datetime as dt

# Wrap ktl import in try/except so that we can maintain test case or simulator
# version of functions.
try:
    import ktl
    from ktl import Exceptions as ktlExceptions
except ModuleNotFoundError:
    ktl = None

from .Instruments import AbstractInstrument


# -----------------------------------------------------------------------------
# MOSFIRE
# -----------------------------------------------------------------------------
class MOSFIRE(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'MOSFIRE'
        self.optical = False
        self.allowed_sampmodes = [2, 3]
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'", "box5", "box9"]
        self.basename = f"m{dt.utcnow().strftime('%Y%m%d')}_"
        self.sampmode = 2
        self.serviceNames = ["mosfire"]
