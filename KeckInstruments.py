from datetime import datetime as dt
from time import sleep

# Wrap ktl import in try/except so that we can maintain test case or simulator
# version of functions.
try:
    import ktl
    from ktl import Exceptions as ktlExceptions
except:
    ktl = None


# -----------------------------------------------------------------------------
# Abstract Instrument
# -----------------------------------------------------------------------------
class AbstractInstrument(object):
    def __init__(self, readonly=True):
        self.name = 'AbstractInstrument'
        self.readonly = readonly
        self.serviceNames = []
        self.services = {}
        self.frameno = 1
        self.basename = 'image'
        self.itime = 1
        self.object = 'objectname'
        self.binnings = ["1x1"]
        self.binning = (1,1)
        self.sampmodes = [1, 2, 3]
        self.sampmode = 1
        self.sampmode_trans = {1: 'CCD', 2: 'CDS', 3: 'MCDS16'}
        self.allowed_sampmodes = [1, 2, 3]
        self.coadds = 1
        self.script = 'stare'
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'", "box5", "box9"]
        self.repeats = 1


    def get_filename(self):
        return f'{self.basename}{self.frameno:04d}.fits'
    
    
    def set_object(self, object):
        self.object = object
        print(f'OBJECT set to "{self.object}"')
    
    
    def set_itime(self, itime):
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
            except:
                print(f"Could not interpret string {input} as a binning setting.")
        elif type(input) in [list, tuple]:
            try:
                binX, binY = input
            except:
                print(f"Could not interpret tuple/list {input} as a binning setting.")
        else:
            print(f"Could not interpret {type(input)} {input} as a binning setting.")

        if f"{binX:d}x{binY:d}" in self.binnings:
            self.binning = (binX, binY)
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
    
    


# -----------------------------------------------------------------------------
# HIRES
# -----------------------------------------------------------------------------
class HIRES(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'HIRES'
        self.optical = True
        self.allowed_sampmodes = [1]
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
        self.binnings = ["1x1", "1x2", "2x1", "2x2"]
        self.basename = f"h{dt.utcnow().strftime('%Y%m%d')}_"
        self.serviceNames = ["hires", "hiccd", "expo"]
        self.obstypes = ["object", "dark", "line", "intflat", "bias"]
    
    
    def connect(self):
        if ktl is not None:
            for service in self.serviceNames:
                try:
                    self.services[service] = ktl.Service(service)
                except ktlExceptions.ktlError:
                    print(f"Failed to connect to service {service}")
    
    
    def get_DWRN2LV(self):
        if ktl is not None:
            DWRN2LV = float(self.services['hiccd']['DWRN2LV'].read())
        else:
            print('Using simulated results')
            DWRN2LV = 100 - dt.now().minute/60*90 # mock up (100 to 10 each hour)
        return DWRN2LV
    
    
    def get_RESN2LV(self):
        if ktl is not None:
            RESN2LV = float(self.services['hiccd']['RESN2LV'].read())
        else:
            print('Using simulated results')
            RESN2LV = 100 - dt.now().weekday()/6*50 # mock up (100 to 50 each week)
        return RESN2LV
    
    
    def fill_dewar(self):
        print('Initiating camera dewar fill.')
        if ktl is not None:
            pass
    
    
    def take_exposure(self, obstype=None, exptime=None, nexp=1):
        if obstype is None:
            obstype = self.services['hiccd']['OBSTYPE'].read()

        if obstype.lower() not in self.obstypes:
            print(f'OBSTYPE "{obstype} not understood"')
            return

        if self.services['hiccd']['OBSERVIP'].read() == 'true':
            print('Waiting up to 300s for current observation to finish')
            if not ktl.waitFor('($hiccd.OBSERVIP == False )', timeout=300):
                raise Exception('Timed out waiting for OBSERVIP')

        if exptime is not None:
            self.services['hiccd']['TTIME'].write(int(exptime))

        if obstype.lower() in ["dark", "bias", "zero"]:
            self.services['hiccd']['AUTOSHUT'].write(False)
        else:
            self.services['hiccd']['AUTOSHUT'].write(True)

        for i in range(nexp):
            exptime = int(self.services['hiccd']['TTIME'].read())
            print(f"Taking exposure {i:d} of {nexp:d}")
            print(f"  Exposure Time = {exptime:d} s")
            self.services['hiccd']['EXPOSE'].write(True)
            exposing = ktl.Expression("($hiccd.OBSERVIP == True) and ($hiccd.EXPOSIP == True )")
            reading = ktl.Expression("($hiccd.OBSERVIP == True) and ($hiccd.WCRATE == True )")
            obsdone = ktl.Expression("($hiccd.OBSERVIP == False)")

            if not exposing.wait(timeout=30):
                raise Exception('Timed out waiting for EXPOSING state to start')
            print('  Exposing ...')

            if not reading.wait(timeout=exptime+30):
                raise Exception('Timed out waiting for READING state to start')
            print('  Reading out ...')

            if not obsdone.wait(timeout=90):
                raise Exception('Timed out waiting for READING state to finish')
            print('Done')


#     def expo_get_power_on(self):
#         return True
#     
#     
#     def expo_toggle_power(self):
#         new_state = not self.expo_get_power_on()
#         print(f'Setting power on exposure meter {{True: "ON", False: "OFF"}[new_state]}')
    
    
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


# -----------------------------------------------------------------------------
# ESI
# -----------------------------------------------------------------------------
class ESI(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'ESI'
        self.optical = True
        self.allowed_sampmodes = [1]
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
        self.binnings = ["1x1", "1x2", "2x1", "2x2"]
        self.basename = f"e{dt.utcnow().strftime('%Y%m%d')}_"


