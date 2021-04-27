from setuptools import setup, find_packages

cl_scripts = ['take_exposure=mosfire.detector:take_exposure',
              'waitfor_exposure=mosfire.detector:waitfor_exposure',
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
