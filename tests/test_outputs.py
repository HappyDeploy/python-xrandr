#!/usr/bin/python

import sys
sys.path.insert(0,"../")
from xrandr import xrandr


screen = xrandr.get_current_screen()

output = screen.outputs["VGA-0"]
print "output: ", output.id
print "active: ", output.is_active()
print "ctrc: ", output.get_crtc()
print "ctrcs: ", output.get_crtcs()

# pick a random mode
mode = screen._resources.contents.modes.contents[0]
print "Setting: ", mode.width, mode.height

# find output that is connected to crtc
for crtc in output.get_crtcs():
    # check if this is in use by some other output and ignore it then
    for other in screen.outputs.values():
        if other.id == output.id:
            continue
        if other.get_crtc == crtc:
            continue
    print "activating output %s" % output.id
    crtc.set_config(0,0, mode, [output])
    break


# diabling works too
#for crtc in screen.crtcs:
#    for crtc_output in crtc.outputs:
#        if crtc_output == output:
#            print "disabling: %s" % output.id
#            crtc.disable()
