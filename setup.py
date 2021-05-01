from setuptools import setup, find_packages

cl_scripts = [# detector
              'take_exposure=mosfire.detector:take_exposure',
              'goi=mosfire.detector:take_exposure',
              'waitfor_exposure=mosfire.detector:waitfor_exposure',
              'wfgo=mosfire.detector:waitfor_exposure',
              'exptime=mosfire.detector:exptime_with_args',
              'coadds=mosfire.detector:coadds_with_args',
              'sampmode=mosfire.detector:sampmode_with_args',
              # dcs
              'markbase=mosfire.dcs:markbase',
              'gotobase=mosfire.dcs:gotobase',
              ]

setup(
    name = "mosfire",
    version='0.0.1',
    author='Josh Walawender',
    packages = find_packages(),
    include_package_data=True,
    entry_points = {'console_scripts': cl_scripts},
)
