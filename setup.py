#!/usr/bin/env python
from setuptools import setup

setup(name='pyxsim',
      packages=['pyxsim'],
      version='1.2.0',
      description='Python package for simulating X-ray observations of astrophysical sources',
      author='John ZuHone',
      author_email='jzuhone@gmail.com',
      url='http://github.com/jzuhone/pyxsim',
      setup_requires=["numpy"],
      install_requires=["six","numpy","astropy","h5py","yt>=3.3.1","soxs>=0.5.0"],
      include_package_data=True,
      classifiers=[
          'Intended Audience :: Science/Research',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'Topic :: Scientific/Engineering :: Visualization',
      ],
      )
