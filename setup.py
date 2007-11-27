#!/usr/bin/env python
from distutils.core import setup

setup(name="python-xrandr",
      version="0.0.1",
      description="Python bindings for XRandR",
      author="Michael Vogt, Sebastian Heinlein",
      packages=['xrandr'],
      scripts=['pyxrandr'],
      license = 'GNU LGPL',
      platforms = 'posix')

