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
        self.modes = ['Dark Imaging', 'Dark Spectroscopy', 'Imaging',
                      'Spectroscopy']
        self.filters = ['Y', 'J', 'H', 'K', 'J2', 'J3', 'NB']


    def set_mode(self, filter, mode):
        if not mode in self.modes:
            log.ERROR(f"Mode: {mode} is unknown")
        elif not filter in self.filters:
            log.ERROR(f"Filter: {filter} is unknown")
        else:
            log.info(f"Setting mode to {filter} {mode}")


    def quick_dark(self):
        log.info('Setting Quick Dark')


    def take_arcs(self, arc, band, arcexp, narcs):
        self.configure_for_arcs(arc)
        self.set_mode(band, 'Spectroscopy')
        log.info(f"Taking {narcs:d} x {arcexp:d}sec "\
                 f"{band}-band {arc} arcs")
        self.goi(arcexp, n=narcs)


    def take_arcs(self, config, band):
        for arc in ['Ne', 'Ar']:
            narcs = int(config[band][f"{arc}Count"])
            arcexp = int(config[band][f"{arc}Exp"])
            if narcs > 0:
                self.configure_for_arcs(arc)
                self.set_mode(band, 'Spectroscopy')
                log.info(f"Taking {narcs:d} x {arcexp:d}sec "\
                         f"{band}-band {arc} arcs")
                self.goi(arcexp, n=narcs)


    def take_flats(self, band, flatexp, nflats, lampsoff=True):
        log.info(f"Taking {nflats:d} x {flatexp:d}sec "\
                 f"{band}-band flats (LampsOff={lampsoff})")
        self.set_mode(band, 'Spectroscopy')
        self.goi(flatexp, n=nflats)
        if lampsoff is False:
            m.dome_lamps('off')
            self.goi(flatexp, n=nflats)


    def take_flats(self, config, band):
        nflats = int(config[band]['FlatCount'])
        if nflats > 0:
            flatexp = int(config[band]['FlatExp'])
            lampsoff = config[band]['LampsOff']
            log.info(f"Taking {nflats:d} x {flatexp:d}sec "\
                     f"{band}-band flats (LampsOff={lampsoff})")
            self.goi(flatexp, n=nflats)


    def configure_for_arcs(self, arc):
        log.info('Configuring for arcs')
        self.dome_lamps('off')
        self.arc_lamps(arc)
        log.info('  Closing hatch')


    def dome_lamps(self, state):
        assert state in ['on', 'off']
        log.info('  Turning {state} dome lamps')


    def arc_lamps(self, state):
        assert state in ['Ar', 'Ne', 'off']
        log.info('  Turning {state} arc lamps')


    def configure_for_flats(self):
        log.info('Configuring for flats')
        self.dome_lamps('on')
        self.arc_lamps('off')
        log.info('  Opening hatch')


    def get_hatchopen_state(self):
        log.debug('Getting hatch state')
        isopen = True
        state = {True: 'open', False: 'closed'}[isopen]
        log.debug(f"  Hatch is {state}")
        return isopen



calibration_config_comments = '''
# Calibration script configuration file format. This is a YAML formatted file.
# Each mask is an entry whose first line begins with "- " and contains several
# entries (one for each filter, plus a "maskname") which are formatted as 
# "  J:" (for the J filter in this example).  Each filter entry is either "null"
# (indicating no calibrations are needed for that filter+mask combination) or a
# dictionary containing several entries.  The dictionary looks like this:
# {ArCount: 0, ArExp: 2, FlatCount: 1, FlatExp: 10, Lamp: mos, LampsOff: 0, NeCount: 0,
#    NeExp: 2}
# It has the following key, value pairs:
#   ArCount: number of Ar exposures to acquire [int]
#   ArExp: exposures Time for Ar arcs [int]
#   FlatCount: number of Flats to acquire [int]
#   FlatExp: exposure Time for Flats [int]
#   Lamp: lamp to use for flats [str] (usually "mos")
#   LampsOff: flag indicating whether to acquire Lamps on/off pair [int 0 or 1]
#   NeCount: number of Ne exposures to acquire [int]
#   NeExp: exposures Time for Ne arcs [int]
'''

if __name__ == '__main__':
    main()
