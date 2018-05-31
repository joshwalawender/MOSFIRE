# Wrap ktl import in try/except so that we can maintain test case or simulator
# version of functions.
try:
    import ktl
    from ktl import Exceptions as ktlExceptions
except ModuleNotFoundError:
    ktl = None


# -----------------------------------------------------------------------------
# Abstract Instrument
# -----------------------------------------------------------------------------
class AbstractInstrument(object):
    def __init__(self, readonly=True):
        self.name = 'AbstractInstrument'
        self.readonly = readonly
        self.serviceNames = []
        self.services = None
        self.frameno = 1
        self.basename = 'image'
        self.itime = 1
        self.object = 'objectname'
        self.binnings = ["1x1"]
        self.binning = (1, 1)
        self.sampmodes = [1, 2, 3]
        self.sampmode = 1
        self.sampmode_trans = {1: 'CCD', 2: 'CDS', 3: 'MCDS16'}
        self.allowed_sampmodes = [1, 2, 3]
        self.coadds = 1
        self.script = 'stare'
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'", "box5", "box9"]
        self.repeats = 1

    def connect(self):
        if ktl is not None:
            self.services = {}
            for service in self.serviceNames:
                try:
                    self.services[service] = ktl.Service(service)
                except ktlExceptions.ktlError:
                    print(f"Failed to connect to service {service}")

    def get_filename(self):
        return f'{self.basename}{self.frameno:04d}.fits'

    def set_object(self, object):
        self.object = object
        print(f'OBJECT set to "{self.object}"')

    def set_itime(self, itime):
        self._set_itime(itime)
        self.itime = itime
        print(f'ITIME set to {self.itime:.1f} s')

    def binning_as_str(self):
        return f"{int(self.binning[0]):d}x{int(self.binning[1]):d}"

    def set_binning(self, input):
        if type(input) is str:
            try:
                binX, binY = input.lower().split('x')
                binX = int(binX)
                binY = int(binY)
            except AttributeError:
                print(f"Could not interpret {input} as a binning setting.")
        elif type(input) in [list, tuple]:
            try:
                binX, binY = input
            except TypeError:
                print(f"Could not interpret {input} as a binning setting.")
        else:
            print(f"Could not interpret {type(input)} {input} as a binning.")

        if f"{binX:d}x{binY:d}" in self.binnings:
            self._set_binning(binX, binY)
            print(f"Binning set to {self.binning_as_str()}")
        else:
            print(f"Binning {input} is not supported on this instrument.")

    def set_sampmode(self, sampmode):
        if sampmode in self.allowed_sampmodes:
            self.sampmode = sampmode
            sampmode_str = self.sampmode_trans[self.sampmode]
            print(f"Set sampling mode to {self.sampmode} ({sampmode_str})")

    def set_coadds(self, coadds):
        self.coadds = coadds
        print(f'COADDS set to {self.coadds:d}')

    def set_repeats(self, nrepeats):
        self.repeats = nrepeats
        print(f'Number of script repeats set to {self.repeats:d}')

    def start_exposure(self):
        print(f'Starting exposure.')
        print(f'  Done')
        print(f'  Writing to: {self.get_filename()}')
        self.frameno += 1

    def start_sequence(self):
        print(f"Starting observation sequence")
        for i in range(self.repeats):
            print(f'  Running {self.script} ({i+1:d} of {self.repeats:d})')
        print(f"Done.")

    def goi(self):
        self.take_exposure()

    def abort_exposure(self):
        print(f'Aborting exposure.')
        print(f'  Done')
        print(f'  Writing to: {self.get_filename()}')
        self.frameno += 1

    def abort_afterframe(self):
        print(f'Aborting after this frame.')

    def abort_afterrepeat(self):
        print(f'Aborting after this repeat.')

    def set_bright(self):
        print("Setting bright object parameters")
        self.set_itime(2)

    def set_faint(self):
        print("Setting faint object parameters")
        self.set_itime(120)

    # -------------------------------------------------------------------------
    # Move and Dither Commands
    def en(self):
        pass

    def xy(self):
        pass

    def sltmov(self):
        pass
