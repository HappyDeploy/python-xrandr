#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Python-XRandR provides a high level API for the XRandR extension of the
# X.org server. XRandR allows to configure resolution, refresh rate, rotation 
# of the screen and multiple outputs of graphics cards.
#
# This module provides a command line interface tool to access the
# features of XRandR.
#
# In many aspects it follows the design of the xrand tool written by
# Keith Packard.
#
# Copyright 2007 © Sebastian Heinlein <sebastian.heinlein@web.de>
# Copyright 2007 © Michael Vogt <mvo@ubuntu.com>
# Copyright 2007 © Canonical Ltd.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from gettext import gettext as _
import gettext
gettext.textdomain("python-xrandr")

from optparse import OptionParser

import xrandr

__version__ = "0.0.x(development)"

def main():
    parser = OptionParser(version=__version__)
    parser.add_option("--verbose", "-v",
                      action="store_true", dest="verbose",
                      default=False,
                      #TRANSLATORS: command line option
                      help=_("show additional information"))
    parser.add_option("-s", "--size",
                      default=None,
                      action="store", type="int", dest="size",
                      #TRANSLATORS: command line option
                      help=_("set the screen reolsution to the given size id"))
    parser.add_option("-r", "--rate",
                      default=None,
                      action="store", type="int", dest="rate",
                      #TRANSLATORS: command line option
                      help=_("set the given refresh rate"))
    parser.add_option("-o", "--rotate",
                      default=None,
                      action="store", type="string", dest="rotate",
                      #TRANSLATORS: command line option
                      help=_("rotate the screen. supported values are "
                             "normal, left, inverted, right or 0, 90, 180, "
                             "270"))
    parser.add_option("--output", "",
                      default=None,
                      action="store", type="string", dest="output",
                      #TRANSLATORS: command line option
                      help=_("select an available output"))
    parser.add_option("--disable", "",
                      action="store_true", dest="output_disable",
                      #TRANSLATORS: command line option
                      help=_("disable the selected output"))
    (options, args) = parser.parse_args()

    if xrandr.has_extension():
        print _("XRandR %s.%s") % xrandr.XRANDR_VERSION
    else:
        print _("The XRandR extension is not available")
        sys.exit(1)

    changed_1_0 = False

    screen = xrandr.get_current_screen()

    if options.size != None:
        screen.set_size_index(options.size)
        changed_1_0 = True
    if options.rate:
        screen.set_refresh_rate(options.rate)
        changed_1_0 = True
    if options.rotate:
        if options.rotate in [_("normal"), "0"]:
            rotation = xrandr.RR_ROTATE_0
        elif options.rotate in [_("right"), "90"]:
            rotation = xrandr.RR_ROTATE_90
        elif options.rotate in [_("inverted"), "180"]:
            rotation = xrandr.RR_ROTATE_180
        elif options.rotate in [_("left"), "270"]:
            rotation = xrandr.RR_ROTATE_270
        else:
            print _("Invalid orientation")
            sys.exit(1)
        screen.set_rotation(rotation)
        changed_1_0 = True
    if changed_1_0:
        screen.apply_config()
    elif options.output:
        output = screen.get_output_by_name(options.output)
        if not output:
            print _("Output does not exist")
            sys.exit(1)
        if options.output_disable:
            output.disable()
    else:
        screen.print_info(options.verbose)

if __name__ == "__main__":
    main()

# vim:ts=4:sw=4:et
