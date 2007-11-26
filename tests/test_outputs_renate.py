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

    output = screen.outputs["VGA"]
    print "output: ", output.id
    print "active: ", output.is_active()
    print "ctrc: ", output.get_crtc()
    print "ctrcs: ", output.get_crtcs()

    # pick a random mode
    modes = screen._resources.contents.modes
    mode = modes[0]
    print "Setting: ", mode.width, mode.height

    # find output that is connected to crtc
    # 
    # (why can't I just get from xrandr what output is connected to 
    # what crtc?!?)
    #for crtc in output.get_crtcs():
    #    if check_crtc_for_output(screen, crtc):
    #        print "activating output %s" % output.id
    #        crtc.set_config(0,0, mode, [output])
    #sys.exit(0)

    # diabling works too
    #screen.get_crtc_by_xid(output.get_crtc()).disable()
    

    # enlarge screen (VGA-0 starts where DVI-0 ends (right-of))
    # so that 2x1280 resolution is used
    # (this needs the "virtual" keyword in xorg.conf)
    new_res_x = 2*1024
    new_res_y = 768
    fb_width_mm = screen.get_output_by_name("VGA").get_physical_width() + screen.get_output_by_name("LVDS").get_physical_width()
    fb_height_mm = min(screen.get_output_by_name("VGA").get_physical_height(),screen.get_output_by_name("LVDS").get_physical_height())
    screen.set_size(new_res_x, new_res_y, fb_width_mm, fb_height_mm)
    new_output_x = new_res_x/2
    new_output_y = 0
    # normalize so that top-left is (0,0) (see xrandr.c:set_position)
    # ...
    for crtc in output.get_crtcs():
        if check_crtc_for_output(screen, crtc):
            print "enlarging output %s" % output.id
            crtc.set_config(new_output_x, new_output_y, mode, [output])
    
