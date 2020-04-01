## Import General Tools
import inspect
from datetime import datetime as dt
from datetime import timedelta as tdelta
from time import sleep

from pathlib import Path
import random
import xml.etree.ElementTree as ET
import numpy as np

from astropy.table import Table, Column
from astropy import coordinates as c
from astropy import units as u
from astropy.time import Time
# from astroplan import FixedTarget, Observer

from .core import log


##-------------------------------------------------------------------------
## Define Mask Object
##-------------------------------------------------------------------------
class Mask(object):
    '''An object to represent a MOSFIRE MOS mask.'''

    def __init__(self, input):
        '''The input to the __init__ method is parsed to determine what type of
        mask object to build.  Can be used to read in a mask XML file generated
        by MAGMA, build a simple long slit, build an open mask, or generate a
        set of random slits.
        '''
        self.slitpos = None
        self.alignmentStars = None
        self.scienceTargets = None
        self.xmlroot = None
        # from maskDescription
        self.name = None
        self.priority = None
        self.center_str = None
        self.center = None
        self.PA = None
        self.mascgenArguments = None

        try_input_as_path = Path(input).expanduser()
        if input is None:
            pass
        if try_input_as_path.exists():
            log.debug(f'Found mask file "{try_input_as_path}" on disk')
            self.read_xml(try_input_as_path)
        elif isinstance(input, Path):
            input = input.expanduser()
            if input.exists() is True:
                log.debug(f'Found mask file "{input}" on disk')
                self.read_xml(input)
            else:
                log.error(f'Failed to find "{input}" on disk')
                return None
        elif isinstance(input, str):
            if input.upper() in ['OPEN', 'OPEN MASK']:
                log.debug(f'"{input}" interpreted as OPEN')
                self.build_open_mask()
            elif input.upper() in ['RAND', 'RANDOM']:
                log.debug(f'"{input}" interpreted as RANDOM')
                self.build_random_mask()
            else:
                try:
                    width, length = input.split('x')
                    width = float(width)
                    length = int(length)
                    assert length <= 46
                    assert width > 0
                    self.build_longslit(input)
                except:
                    log.debug(f'Unable to parse "{input}" as long slit')
                    log.error(f'Unable to parse "{input}"')
                    raise ValueError(f'Unable to parse "{input}"')
        else:
            raise ValueError(f'Unable to parse "{input}"')


    def find_bad_angles(self, night='2020-02-25', nhours=6, plot=False):
        log.info(f'Checking for bad angles for mask "{self.name}" on {night}')
        if self.PA is None:
            log.error("No PA defined for this mask.")
            return None
        if not isinstance(self.center, c.SkyCoord):
            log.error("No central coordinate defined for this mask")
            return None

        keck = c.EarthLocation.of_site('keck')
        time = Time(f'{night}T10:00:00', format='isot', scale='utc', location=keck) + np.arange(-nhours, nhours, 1/60)*u.hour
        HA = time.sidereal_time('apparent') - self.center.ra.hourangle*u.hourangle

        # calculate parallactic angle from HA, dec, latitude
        # from https://en.wikipedia.org/wiki/Parallactic_angle
        # P = arctan( sin(HA) / (cos(dec)*tan(lat) - sin(dec)*cos(HA)) )
        tan_p_angles = np.sin(HA.to(u.radian))
        tan_p_angles /= np.cos(self.center.dec.radian)*np.tan(keck.lat.radian)\
                      - np.sin(self.center.dec.radian)*np.cos(HA.to(u.radian))
        p_angles = c.Angle(np.arctan(tan_p_angles)) - 180*u.deg

        predicted_rotpposn = c.Angle(45*u.deg) - p_angles
        predicted_rotpposn = predicted_rotpposn.wrap_at(360*u.deg)

        result = []
        danger_times = []
        danger_angles = []
        last_point_bad = False
        for t,p in zip(time, predicted_rotpposn):
            if abs(p.value-180) < 10 or abs(p.value-0) < 10:
                if last_point_bad is False:
                    result.append( [t, None] )
                last_point_bad = True
                danger_times.append(t)
                danger_angles.append(p)
            else:
                if last_point_bad is True:
                    result[-1][1] = t
                    bad_start = result[-1][0].datetime
                    bad_end = result[-1][1].datetime
                    msg = (f'  Bad rotator angle for "{self.name}" from '
                           f'{bad_start.strftime("%H:%M UT")} to '
                           f'{bad_end.strftime("%H:%M UT")} '
                           f'({(bad_start-tdelta(hours=10)).strftime("%H:%M HST")} to '
                           f'{(bad_end-tdelta(hours=10)).strftime("%H:%M HST")})')
                    log.info(msg)
                last_point_bad = False
        danger_times = Time(danger_times)
        danger_angles = c.Angle(danger_angles)
    
        if plot is True:
            from matplotlib import pyplot as plt
            from matplotlib import dates

            plt.figure(figsize=(18,6))

            plt.title(msg)
            plt.fill_between(danger_times.plot_date, -10, 370, color='red', alpha=0.2)

            # plt.plot_date(UTs.plot_date, ROTPPOSNs, 'go')
            plt.plot_date(time.plot_date, predicted_rotpposn.to(u.deg), 'b-')
            plt.plot_date(danger_times.plot_date, danger_angles.to(u.deg), 'r-', lw=8)

            # Format the time axis
            date_formatter = dates.DateFormatter('%H:%M')
            plt.gca().xaxis.set_major_formatter(date_formatter)
            # Set labels.
            plt.yticks(np.arange(0,390,180))
            plt.ylabel("Physical Drive Angle (degrees)")
            plt.xlabel("HST Time on {0}".format(min(time).datetime.date()))
            plt.grid()
            plt.show()
        
        return result
        
        
    def slit_corners(self, scienceslitno):
        '''Return the 4 corners of the science slit in RA and Dec.
        '''
        slit = dict(self.scienceTargets[scienceslitno])
        ra_str = f"{slit['slitRaH']}h{slit['slitRaM']}m{slit['slitRaS']}s"
        dec_str = f"{slit['slitDecD']}d{slit['slitDecM']}m{slit['slitDecS']}s"
        slit_center = c.SkyCoord(f"{ra_str} {dec_str}")
        slitL = float(slit['slitLengthArcsec'])
        slitW = float(slit['slitWidthArcsec'])
        c1 = slit_center.directional_offset_by(m.PA*u.deg + (np.tan(slitW/slitL)*u.radian).to(u.deg),
                                               ((slitL/2)**2 + (slitW/2)**2)**0.5*u.arcsec )
        c2 = slit_center.directional_offset_by(m.PA*u.deg - (np.tan(slitW/slitL)*u.radian).to(u.deg),
                                               ((slitL/2)**2 + (slitW/2)**2)**0.5*u.arcsec )
        c3 = slit_center.directional_offset_by(m.PA*u.deg + (np.tan(slitW/slitL)*u.radian).to(u.deg) + 180*u.deg,
                                               ((slitL/2)**2 + (slitW/2)**2)**0.5*u.arcsec )
        c4 = slit_center.directional_offset_by(m.PA*u.deg - (np.tan(slitW/slitL)*u.radian).to(u.deg) + 180*u.deg,
                                               ((slitL/2)**2 + (slitW/2)**2)**0.5*u.arcsec )
        return (c1, c2, c3, c4)


    def read_xml(self, xml):
        '''Read an XML mask file generated by MAGMA.
        '''
        xmlfile = Path(xml)
        if xmlfile.exists():
            tree = ET.parse(xmlfile)
            self.xmlroot = tree.getroot()
        else:
            try:
                self.xmlroot = ET.fromstring(xml)
            except:
                log.error(f'Could not parse {xml} as file or XML string')
                raise
        # Parse XML root
        for child in self.xmlroot:
            if child.tag == 'maskDescription':
                self.name = child.attrib.get('maskName')
                self.priority = float(child.attrib.get('totalPriority'))
                self.PA = float(child.attrib.get('maskPA'))
                self.center_str = f"{child.attrib.get('centerRaH')}:"\
                                  f"{child.attrib.get('centerRaM')}:"\
                                  f"{child.attrib.get('centerRaS')} "\
                                  f"{child.attrib.get('centerDecD')}:"\
                                  f"{child.attrib.get('centerDecM')}:"\
                                  f"{child.attrib.get('centerDecS')}"
                self.center = c.SkyCoord(self.center_str, unit=(u.hourangle, u.deg))
            elif child.tag == 'mascgenArguments':
                self.mascgenArguments = {}
                for el in child:
                    if el.attrib == {}:
                        self.mascgenArguments[el.tag] = (el.text).strip()
                    else:
                        self.mascgenArguments[el.tag] = el.attrib
            elif child.tag == 'mechanicalSlitConfig':
                data = [el.attrib for el in child.getchildren()]
                self.slitpos = Table(data)
            elif child.tag == 'scienceSlitConfig':
                data = [el.attrib for el in child.getchildren()]
                self.scienceTargets = Table(data)
                ra = [f"{star['targetRaH']}:{star['targetRaM']}:{star['targetRaS']}"
                      for star in self.scienceTargets]
                dec = [f"{star['targetDecD']}:{star['targetDecM']}:{star['targetDecS']}"
                       for star in self.scienceTargets]
                self.scienceTargets.add_columns([Column(ra, name='RA'),
                                                 Column(dec, name='DEC')])
            elif child.tag == 'alignment':
                data = [el.attrib for el in child.getchildren()]
                self.alignmentStars = Table(data)
                ra = [f"{star['targetRaH']}:{star['targetRaM']}:{star['targetRaS']}"
                      for star in self.alignmentStars]
                dec = [f"{star['targetDecD']}:{star['targetDecM']}:{star['targetDecS']}"
                       for star in self.alignmentStars]
                self.alignmentStars.add_columns([Column(ra, name='RA'),
                                                 Column(dec, name='DEC')])
            else:
                mask[child.tag] = [el.attrib for el in child.getchildren()]


    def build_longslit(self, input):
        '''Build a longslit mask
        '''
        # parse input string assuming format similar to 0.7x46
        width, length = input.split('x')
        width = float(width)
        length = int(length)
        assert length <= 46
        self.name = f'LONGSLIT-{input}'
        slits_list = []
        # []
        # scale = 0.7 arcsec / 0.507 mm
        for i in range(length):
            # Convert index iteration to slit number
            # Start with slit number 23 (middle of CSU) and grow it by adding
            # a bar first on one side, then the other
            slitno = int( {0: -1, -1:1}[-1*(i%2)] * (i+(i+1)%2)/2 + 24 )
            leftbar = slitno*2
            leftmm = 145.82707536231888 + -0.17768476719087264*leftbar + (width-0.7)/2*0.507/0.7
            rightbar = slitno*2-1
            rightmm = leftmm - width*0.507/0.7
            slitcent = (slitno-23) * .490454545
            slits_list.append( {'centerPositionArcsec': slitcent,
                                'leftBarNumber': leftbar,
                                'leftBarPositionMM': leftmm,
                                'rightBarNumber': rightbar,
                                'rightBarPositionMM': rightmm,
                                'slitNumber': slitno,
                                'slitWidthArcsec': width,
                                'target': ''} )
        self.slitpos = Table(slits_list)
        self.slitpos.sort('slitNumber')

        # Alignment Box
        slit23 = self.slitpos[self.slitpos['slitNumber'] == 23][0]
        leftmm = slit23['leftBarPositionMM'] - 1.65*0.507/0.7
        rightmm = slit23['rightBarPositionMM'] + 1.65*0.507/0.7
        as_dict = {'centerPositionArcsec': 0.0,
                   'leftBarNumber': 46,
                   'leftBarPositionMM': leftmm,
                   'mechSlitNumber': 23,
                   'rightBarNumber': 45,
                   'rightBarPositionMM': rightmm,
                   'slitWidthArcsec': 4.0,
                   'targetCenterDistance': 0,
                   }
        self.alignmentStars = Table([as_dict])


    def build_open_mask(self):
        '''Build OPEN mask
        '''
        self.name = 'OPEN'
        slits_list = []
        for i in range(46):
            slitno = i+1
            leftbar = slitno*2
            leftmm = 270.400
            rightbar = slitno*2-1
            rightmm = 4.000
            slitcent = 0
            width  = (leftmm-rightmm) * 0.7/0.507
            slits_list.append( {'centerPositionArcsec': slitcent,
                                'leftBarNumber': leftbar,
                                'leftBarPositionMM': leftmm,
                                'rightBarNumber': rightbar,
                                'rightBarPositionMM': rightmm,
                                'slitNumber': slitno,
                                'slitWidthArcsec': width,
                                'target': ''} )
        self.slitpos = Table(slits_list)


    def build_random_mask(self, slitwidth=0.7):
        '''Build a Mask with randomly placed, non contiguous slits
        '''
        self.name = 'RANDOM'
        slits_list = []
        for i in range(46):
            slitno = i+1
            cent = random.randrange(54,220)
            # check if it is the same as the previous slit
            if i > 0:
                while cent == slits_list[i-1]['centerPositionArcsec']:
                    cent = random.randrange(54,220)
            leftbar = slitno*2
            leftmm = cent + slitwidth*0.507/0.7
            rightbar = slitno*2-1
            rightmm = cent - slitwidth*0.507/0.7
            width  = (leftmm-rightmm) * 0.7/0.507
            slits_list.append( {'centerPositionArcsec': cent,
                                'leftBarNumber': leftbar,
                                'leftBarPositionMM': leftmm,
                                'rightBarNumber': rightbar,
                                'rightBarPositionMM': rightmm,
                                'slitNumber': slitno,
                                'slitWidthArcsec': width,
                                'target': ''} )
        self.slitpos = Table(slits_list)
        
