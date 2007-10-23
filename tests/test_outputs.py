#!/usr/bin/python

import sys
sys.path.insert(0,"../")
from xrandr import xrandr

def check_crtc_for_output(screen, crtc):
    # FIXME: port the rest of check_crtc_for_output from xrandr.c
    # check if this is in use by some other output and ignore it then
    for other in screen.outputs.values():
        if other.id == output.id:
            continue
        if other.get_crtc() == crtc.xid:
            return False
    return True

if __name__ == "__main__":

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
        if check_crtc_for_output(screen, crtc):
            print "activating output %s" % output.id
            crtc.set_config(0,0, mode, [output])

# diabling works too
#screen.get_crtc_by_xid(output.get_crtc()).disable()
