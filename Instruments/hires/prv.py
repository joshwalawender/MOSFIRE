from .core import *
from .cals import *
from .detector import *
from .dewar import *
from .expo import *
from .iodine import *
from .mechs import *


# -----------------------------------------------------------------------------
# Afternoon Setup for PRV
# -----------------------------------------------------------------------------
def PRV_afternoon_setup(check_iodine=True, fnroot=None):
    """Configure the instrument for afternoon setup (PRV mode).
    """
    # Check that lights are off in the HIRES enclosure
    if lights_are_on() is True:
        log.error('Lights in HIRES enclosure are on!')
        log.error('Enclosure may be occupied, halting script.')
        return False
    # Check dewar level, if below threshold, fill
    if get_DWRN2LV() < 30:
        log.info(f'Dewar level at {getDWRN2LV():.1f} %. Initiating dewar fill.')
        fill_dewar()
    # Start iodine cell
    iodine_start()
    # Open covers
    open_covers()
    # Set filename root
    now = dt.utcnow()
    if fnroot is None:
        fnroot = now.strftime('%Y%m%d_')
    set('hiccd', 'OUTFILE', fnroot)
    # Set binning to 3x1
    set_binning('3x1')
    # --> Set full frame (not possible?)
    # Confirm gain=low
    assert get_gain() == 'low'
    # Confirm Speed = fast
    assert get_ccdspeed() == 'fast'
    # m slitname=opened
    open_slit()
    # m fil1name=clear
    # m fil2name=clear
    set_filters('clear', 'clear')
    # Confirm collimator = red
    assert get_collimator() == 'red'
    # m cofraw = +70000
    set_cofraw(70000)
    # m cafraw=0
    set_cafraw(0)
    # --> set ECHANG
#     set('hires', 'ECHANG', 0, wait=True)
    # --> set XDANG
#     set('hires', 'XDANG', 0, wait=True)
    # --> tvfilter to BG38
    set_tvfilter('bg38')  # check that tvfocus is set properly
    # Confirm tempiod1 and tempiod2
    if check_iodine is True:
        while check_iodine_temps() is not True:
            log.info('Iodine cell not at temperature.')
            tempiod1, tempiod2 = get_iodine_temps()
            log.info(f'  tempiod1 = {tempiod1:.1f} C')
            log.info(f'  tempiod2 = {tempiod2:.1f} C')
            log.info(f'  waiting 5 minutes before checking again (or CTRL-c to exit)')
            sleep(300)
    if check_iodine_temps() is True:
        log.info('Iodine cell at temperature:')
    else:
        log.info('Iodine cell is not at recommended temperature:')
        tempiod1, tempiod2 = get_iodine_temps()
        log.info(f'  tempiod1 = {tempiod1:.1f} C')
        log.info(f'  tempiod2 = {tempiod2:.1f} C')

    # Obstype = object
    set_obstype('Object')

    # Focus
    # - Exposure meter off
    expo_off()
    # - ThAr2 on
    set_lamp('ThAr2')
    # - Lamp filter=ng3
    set_lamp_filter('ng3')
    # - m deckname=D5
    set_decker('D5')
    # - iodine out
    iodine_out()
    # - texp = 10 seconds
    set_itime(10)
    # - expose
    take_exposure(n=1)
    
    # - -> run IDL focus routine and iterate as needed
    foc_instructions = f"""
You must now accurately position the echelle and cross disperser angles to
place particular arc lines on particular destination pixels.  This is done via
an IDL routine written by the CPS team. This routine will launch momentarily in
a new xterm.

Begin by calling the foc script on your first file:
    IDL> foc, /plt, inpfile='{lastfile}'
When a new image is called for by the foc script, just use the HIRES dashboard
GUI to take a new image.

After a new image is taken, analyze it by calling the script again using:
    IDL> foc, /plt, inpfile='[insert path to new file here]'
If you would like more details on the IDL foc routine, you can view the code
and docstring on github: 
https://github.com/Caltech-IPAC/hires-pipeline/blob/master/focus/foc.pro
For additional instructions, see: 
https://caltech-ipac.github.io/hiresprv/setup.html#spectrograph-alignment-and-focus
"""
    print(foc_instructions)
    subprocess.call(['/home/hireseng/bin/focusPRV'])


# -----------------------------------------------------------------------------
# PRV Calibrations
# -----------------------------------------------------------------------------
def PRV_calibrations():
    print('Running PRV afternoon calibrations.  Before running this, the '
          'instrument should already be configured for PRV observations.')
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.info('Exiting calibrations script.')
        return False

    # Check that lights are off in the HIRES enclosure
    if lights_are_on() is True:
        log.error('Lights in HIRES enclosure are on!')
        log.error('Enclosure may be occupied, halting script.')
        return False
    # Check dewar level, if below threshold, fill
    if get_DWRN2LV() < 30:
        log.info(f'Dewar level at {getDWRN2LV():.1f} %. Initiating dewar fill.')
        fill_dewar()

    # THORIUM Exposures w/ B5
    # - Exposure meter off
    expo_off()
    # - ThAr2 on
    set_lamp('ThAr2')
    # - lamp filter = ng3
    set_lamp_filter('ng3')
    # - m deckname=B5
    set_decker('B5')
    # - iodine out
    iodine_out()
    # - texp=1 second
    set_itime(1)
    # - two exposures
    take_exposure(n=2)

    # THORIUM Exposure w/ B1
    # - Exposure meter off
    # - ThAr2 on
    # - lamp filter = ng3
    # - m deckname=B1
    set_decker('B1')
    # - iodine out
    # - texp=3 second
    set_itime(3)
    # - one exposure
    take_exposure(n=1)
    # - -> check saturation: < 20,000 counts on middle chip?
    # - -> Check I2 line depth. In center of chip, it should be ~30%
    print('IMPORTANT:')
    print('Check saturation: < 20,000 counts on middle chip?')
    print('Check I2 line depth. In center of chip, it should be ~30%')
    print()
    print('If you are not happy with the exposure, adjust the exposure time')
    print('in the HIRES dashboard and take a new exposure.  Continute until')
    print('you have an exposure which satisfies the above checks.')
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.error('Exiting calibrations script.')
        return False

    # Iodine Cell Calibrations B5
    # - Make sure cell is fully warmed up before taking these
    check_iodine_temps()
    # - Exposure meter off
    # - Quartz2 on
    set_lamp('quartz2')
    # - Lamp filter=ng3
    # - m deckname=B5
    set_decker('B5')
    # - iodine in
    iodine_in()
    # - texp=2 second
    set_itime(2)
    # - one exposure
    take_exposure(n=1)
    # - -> check saturation: < 20,000 counts on middle chip?
    # - -> Check I2 line depth. In center of chip, it should be ~30%
    print('IMPORTANT:')
    print('Check saturation: < 20,000 counts on middle chip?')
    print('Check I2 line depth. In center of chip, it should be ~30%')
    print()
    print('If you are not happy with the exposure, adjust the exposure time')
    print('in the HIRES dashboard and take a new exposure.  Continute until')
    print('you have an exposure which satisfies the above checks.')
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.error('Exiting calibrations script.')
        return False

    # Wide Flat Fields
    # - Exposure meter off
    # - Quartz2 on
    # - Lamp filter=ng3
    # - m deckname=C1
    set_decker('C1')
    # - iodine out
    iodine_out()
    # - texp=1 second
    set_itime(1)
    # - Take 1 exposures
    take_exposure(n=1)
    # - -> Check one test exp for saturation (<20k counts)
    print('IMPORTANT:')
    print('Check saturation: middle chip should have 10,000 < counts < 20,000')
    print()
    print('If you are not happy with the exposure, adjust the exposure time')
    print('in the HIRES dashboard and take a new exposure.  Continute until')
    print('you have an exposure which satisfies the above checks.')
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        new_exp_time = input('New Exposure Time (s)? ')
        try:
            new_exp_time = int(new_exp_time)
        except ValueError:
            print('New exposure time must be an integer.')
            new_exp_time = input('New Exposure Time (s)? ')
            new_exp_time = int(new_exp_time)
        set_itime(new_exp_time)
    # - Take 49 exposures
    log.info('Taking 49 additional flats.  This will take some time ...')
    take_exposure(n=49)
    # - m lampname=none
    set_lamp('none')
    # - m deckname=C2
    set_decker('C2')
    # - Check dewar level, if below threshold, fill
    if estimate_dewar_time() < 12:
        fill_dewar()

