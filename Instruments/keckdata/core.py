#!/usr/env/python

## Import General Tools
from pathlib import Path, PosixPath

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.nddata import NDData, StdDevUncertainty, CCDData
from astropy.table import Table


##-------------------------------------------------------------------------
## KeckData Exceptions
##-------------------------------------------------------------------------
class KeckDataError(Exception):
    """Base class for exceptions in this module."""
    pass


class IncompatiblePixelData(KeckDataError):
    """Raise when trying to operate on multiple KeckData
    objects which have incompatible pixeldata.
    """
    def __init__(self, message):
        super().__init__(f"KeckData objects have incompatible pixeldata. {message}")


class IncorrectNumberOfExtensions(KeckDataError):
    """Raise when verify method fails for a specific instrument.
    """
    def __init__(self, datatype, expected, kd):
        msg = f"Incorrect number of {datatype} entries.  Expected {expected} for {type(kd)}"
        print(msg)
        super().__init__(msg)


class UnableToParseInstrument(KeckDataError):
    """Raise when failing to parse INSTRUME header keyword.
    """
    def __init__(self, message):
        super().__init__(f"Unable to determine instrument. {message}")


##-------------------------------------------------------------------------
## KeckData Classes
##-------------------------------------------------------------------------
class KeckData(object):
    """Our data model.
    
    Attributes:
    pixeldata -- a list of CCDData objects containing pixel values.
    tabledata -- a list of astropy.table.Table objects
    headers -- a list of astropy.io.fits.Header objects
    """
    def __init__(self, *args, **kwargs):
        self.pixeldata = []
        self.tabledata = []
        self.headers = []
        self.instrument = None

    def verify(self):
        """Method to check the data against expectations. For the 
        KeckData class this simply passes and does nothing, but
        subclasses for specific instruments can populate this
        with appropriate tests.
        """
        pass

    def add(self, kd2):
        """Method to add another KeckData object to this one and return
        the result.  This uses the CCDData object's add method and
        simply loops over all elements of the pixeldata list.
        """
        if len(self.pixeldata) != len(kd2.pixeldata):
            raise IncompatiblePixelData
        for i,pd in enumerate(self.pixeldata):
            self.pixeldata[i] = pd.add(kd2.pixeldata[i])
        return self

    def subtract(self, kd2):
        """Method to subtract another KeckData object to this one
        and return the result.  This uses the CCDData object's
        subtract method and simply loops over all elements of
        the pixeldata list.
        """
        if len(self.pixeldata) != len(kd2.pixeldata):
            raise IncompatiblePixelData
        for i,pd in enumerate(self.pixeldata):
            self.pixeldata[i] = pd.subtract(kd2.pixeldata[i])
        return self

    def multiply(self, kd2):
        """Method to multiply another KeckData object by this one
        and return the result.  This uses the CCDData object's
        multiply method and simply loops over all elements of
        the pixeldata list.
        """
        if len(self.pixeldata) != len(kd2.pixeldata):
            raise IncompatiblePixelData
        for i,pd in enumerate(self.pixeldata):
            self.pixeldata[i] = pd.multiply(kd2.pixeldata[i])
        return self

    def get(self, kw):
        """Method to loop over all headers and get the specified keyword value.
        Returns the first result it finds and doe not check for duplicate
        instances of the keyword in subsequent headers.
        """
        for hdr in self.headers:
            val = hdr.get(kw, None)
            if val is not None:
                return val

    def type(self):
        """Return the image type.
        """
        return None


##-------------------------------------------------------------------------
## Get HDU Type
##-------------------------------------------------------------------------
def get_hdu_type(hdu):
    """Function to examine a FITS HDU object and determine its type.  Returns
    one of the following strings:
    
    'header' -- This is a PrimaryHDU or ImageHDU with no pixel data.
    'pixeldata' -- This is a PrimaryHDU or ImageHDU containing pixel data.
    'uncertainty' -- This is a pixeldata HDU which is associated with the
                     uncertainty data written by either CCDData or KeckData.
    'mask' -- This is a pixeldata HDU which is associated with the mask
              data written by either CCDData or KeckData.
    'tabledata' -- This is a TableHDU type HDU.
    """
    if type(hdu) in [fits.PrimaryHDU, fits.ImageHDU] and hdu.data is None:
        # This is a header only HDU
        return 'header'
    elif type(hdu) in [fits.PrimaryHDU, fits.ImageHDU] and hdu.data is not None:
        # This is a pixel data HDU
        extname = hdu.header.get('EXTNAME', '').strip()
        if extname == 'MASK':
            # This is a mask HDU
            return 'mask'
        elif extname == 'UNCERT':
            # This is an uncertainty HDU
            return 'uncertainty'
        else:
            # This must be pixel data
            return 'pixeldata'
    elif type(hdu) == fits.TableHDU:
            # This is table data
            return 'tabledata'


##-------------------------------------------------------------------------
## KeckData Reader
##-------------------------------------------------------------------------
def fits_reader(file, defaultunit='adu', datatype=None, verbose=False):
    """A reader for KeckData objects.
    
    Currently this is a separate function, but should probably be
    registered as a reader similar to fits_ccddata_reader.
    
    Arguments:
    file -- The filename (or pathlib.Path) of the FITS file to open.

    Keyword arguments:
    defaultunit -- If the BUNIT keyword is unable to be located or
                   parsed, the reader will assume this unit.  Defaults
                   to "adu".
    datatype -- The output datatype.  Defaults to KeckData, but could
                be a subclass such as MOSFIREData.  The main effect of
                this is that it runs the appropriate verify method on
                the data.
    """
    if type(file) is not Path:
        file = Path(file).expanduser()

    try:
        hdul = fits.open(file, 'readonly')
    except FileNotFoundError as e:
        print(e.msg)
        raise e
    except OSError as e:
        print(e.msg)
        raise e
    # Determine instrument
    if datatype is None:
        instrument = None
        while instrument is None:
            for hdu in hdul:
                if hdu.header.get('INSTRUME') is not None:
                    instrument = hdu.header.get('INSTRUME')
        if instrument is None:
            raise UnableToParseInstrument

        if instrument[:5] == 'HIRES':
            from .hires import HIRESData
            datatype = HIRESData
        elif instrument == 'MOSFIRE':
            from .mosfire import MOSFIREData
            datatype = MOSFIREData
        else:
            datatype = KeckData

    # Loop though HDUs and read them in as pixel data or table data
    kd = datatype()
    while len(hdul) > 0:
        if verbose: print('Extracting HDU')
        hdu = hdul.pop(0)
        kd.headers.append(hdu.header)
        hdu_type = get_hdu_type(hdu)
        if verbose: print(f'  Got HDU type = {hdu_type}')
        if hdu_type == 'header':
            pass
        elif hdu_type == 'tabledata':
            kd.tabledata.append(Table(hdu.data))
        elif hdu_type == 'pixeldata':
            # Check the next HDU
            mask = None
            uncertainty = None
            if len(hdul) > 0:
                next_type = get_hdu_type(hdul[0])
                if next_type == 'mask':
                    mask = hdul[0].data
                elif next_type == 'uncertainty':
                    uncertainty = hdul[0].data
            if len(hdul) > 1:
                next_type2 = get_hdu_type(hdul[1])
                if next_type2 == 'mask':
                    mask = hdul[1].data
                elif next_type2 == 'uncertainty':
                    uncertainty = hdul[1].data               
            # Sanitize "ADU per coadd" BUNIT value
            if hdu.header.get('BUNIT') == "ADU per coadd":
                hdu.header.set('BUNIT', 'adu')
            # Populate the CCDData object
            c = CCDData(hdu.data, mask=mask, uncertainty=uncertainty,
                        meta=hdu.header,
                        unit=hdu.header.get('BUNIT', defaultunit),
                       )
            kd.pixeldata.append(c)
    if verbose: print(f'Read in {len(kd.headers)} headers, '
                      f'{len(kd.pixeldata)} sets of pixel data, '
                      f'and {len(kd.tabledata)} tables')
    kd.verify()
    return kd


class KeckDataList(object):
    def __init__(self, input):
        assert type(input) == list
        self.kds = []
        for item in input:
            if type(item) == str:
                p = Path(str)
                if p.exists():
                    try:
                        kd = fits_reader(p)
                        self.kds.append(kd)
                    except:
                        pass
            elif type(item) in [Path, PosixPath]:
                if item.exists():
                    try:
                        kd = fits_reader(item)
                        self.kds.append(kd)
                    except:
                        pass
            elif issubclass(type(item), KeckData):
                self.kds.append(item)

        self.len = len(self.kds)

        # Verify all input object have the same number of pixeldata arrays
        pixeldata_lengths = set([len(kd.pixeldata) for kd in self.kds])
        if len(pixeldata_lengths) > 1:
            print(pixeldata_lengths)
            raise IncompatiblePixelData(
                  'Input files have insconsistent pixel data ')

        # Determine which KeckData type this is
        kdtypes = set([type(kd) for kd in self.kds])
        if len(kdtypes) > 1:
            print(kdtypes)
            raise IncompatiblePixelData(
                  'Input KeckData objects are not all of the same type')
        self.kdtype = kdtypes.pop()

    def pop(self):
        self.len -= 1
        return self.kds.pop()
        
