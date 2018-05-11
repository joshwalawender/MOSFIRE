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
# NIRES Spectrograph
# -----------------------------------------------------------------------------
class NIRES(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'NIRES'
        self.optical = False
        self.allowed_sampmodes = [2, 3]
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
        self.basename = f"n{dt.utcnow().strftime('%Y%m%d')}_"
        self.sampmode = 2

    def set_bright(self):
        print("Setting bright object parameters")
        self.set_itime(2)
        self.set_sampmode(2)
        self.set_coadds(1)

    def set_faint(self):
        print("Setting faint object parameters")
        self.set_itime(120)
        self.set_sampmode(3)
        self.set_coadds(3)


# -----------------------------------------------------------------------------
# NIRES Imager
# -----------------------------------------------------------------------------
class NIRESim(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'NIRES Slit Viewing Camera'
        self.optical = False
        self.allowed_sampmodes = [2, 3]
        self.scripts = ["stare", "box5", "box9"]
        self.basename = f"ns{dt.utcnow().strftime('%Y%m%d')}_"
        self.sampmode = 2

    def set_bright(self):
        print("Setting bright object parameters")
        self.set_itime(2)
        self.set_sampmode(2)
        self.set_coadds(1)

    def set_faint(self):
        print("Setting faint object parameters")
        self.set_itime(120)
        self.set_sampmode(3)
        self.set_coadds(3)
