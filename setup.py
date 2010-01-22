#!/usr/bin/env python
from distutils.core import setup, Extension
from vnc2flv import __version__

setup(
  name='vnc2flv',
  version=__version__,
  description='Screen recording tool that captures a VNC session and saves as FLV',
  long_description='Vnc2flv is a screen recorder. It captures a VNC desktop session '
  'and saves it as a Flash Video (FLV) file.',
  license='MIT/X',
  author='Yusuke Shinyama',
  author_email='yusuke at cs dot nyu dot edu',
  url='http://www.unixuser.org/~euske/python/vnc2flv/index.html',
  packages=[
    'vnc2flv'
    ],
  scripts=[
    'tools/flvrec.py',
    'tools/flvcat.py',
    'tools/flvdump.py',
    'tools/flvaddmp3.py',
    'tools/flvsplit.py',
    'tools/recordwin.sh'
    ],
  keywords=['vnc', 'flv', 'video', 'screen recorder'],
  classifiers=[
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
  ],
  ext_modules=[Extension('flvscreen',
                         ['flvscreen/flvscreen.c'],
                         #define_macros=[],
                         #include_dirs=[],
                         #library_dirs=[],
                         #libraries=[],
                         )],
  )
