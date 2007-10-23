from ctypes import *
import os

RR_ROTATE_0 = 1
RR_ROTATE_90 = 2
RR_ROTATE_180 = 4
RR_ROTATE_270 = 8

RR_REFLECT_X = 16
RR_REFLECT_Y = 32

# some fundamental datatypes 
RRCrtc = c_long
RROutput = c_long
RRMode = c_long
Connection = c_ushort
SubpixelOrder = c_ushort
Time = c_ulong
Rotation = c_ushort
Status = c_int

# load the libs
xlib = cdll.LoadLibrary("libX11.so")
rr = cdll.LoadLibrary("libXrandr.so")

# query resources
class _XRRModeInfo(Structure):
    _fields_ = [
        ("id", RRMode), # XID is c_long
        ("width", c_int),
        ("height", c_int),
        ("dotClock", c_long),
        ("hSyncStart", c_int),
        ("hSyncEnd", c_int),
        ("hTotal", c_int),
        ("hSkew", c_int),
        ("vSyncStart", c_int),
        ("vSyncEnd", c_int),
        ("vTotal", c_int),
        ("name", c_char_p),
        ("nameLength", c_int),
        ("modeFlags", c_long),
        ]

class _XRRScreenSize(Structure):
    _fields_ = [
        ("width", c_int),
        ("height", c_int),
        ("mwidth", c_int),
        ("mheight", c_int)
        ]

class _XRRCrtcInfo(Structure):
    _fields_ = [
        ("timestamp", Time),
        ("x", c_int),
        ("y", c_int),
        ("width", c_int),
        ("height", c_int),
        ("mode", POINTER(RRMode*100)),
        ("rotation", c_int),
        ("noutput", c_int),
        ("outputs", POINTER(RROutput*100)),
        ("rotations", POINTER(Rotation*100)),
        ("npossible", c_int),
        ("possible", POINTER(RROutput*100)),
        ]
    
class _XRRScreenResources(Structure):
    _fields_ = [
        ("timestamp", Time),
        ("configTimestamp", Time),
        ("ncrtc", c_int),
        ("crtcs", POINTER(RRCrtc*100)),
        ("noutput", c_int),
        ("outputs", POINTER(RROutput*100)),
        ("nmode", c_int),
        ("modes", POINTER(_XRRModeInfo*100)), # number needs just to be big
        ]

class ExtensionMissingException(Exception):
    pass
class UnsupportedException(Exception):
    pass

# XRRGetOutputInfo
class _XRROutputInfo(Structure):
    _fields_ = [
        ("timestamp", Time),
        ("crtc", c_int),
        ("name", c_char_p),
        ("nameLen", c_int),
        ("mm_width", c_ulong),
        ("mm_height", c_ulong),
        ("connection", Connection),
        ("subpixel_order", SubpixelOrder),
        ("ncrtc", c_int),
        ("crtcs", POINTER(RRCrtc*100)),
        ("nclone", c_int),
        ("clones", POINTER(RROutput*100)),
        ("nmode", c_int),
        ("npreferred", c_int),
        ("modes", POINTER(RRMode*100))
        ]

class _XRRCrtcGamma(Structure):
    _fields_ = [
        ('size', c_int),
        ('red', POINTER(c_ushort)),
        ('green', POINTER(c_ushort)),
        ('blue', POINTER(c_ushort)),
        ]

def _array_conv(array, type, conv = lambda x:x):
    res = type * len(array)
    for i in array:
        res[i] = conv(array[i])
    return res

class Output:
    def __init__(self, info, screen):
        self._info = info
        self._screen = screen
    def __del__(self):
        rr.XRRFreeOutputInfo(self._info)
    def get_physical_width(self):
        return self._info.contents.mm_width
    def get_physical_height(self):
        return self._info.contents.mm_height
    def get_crtc(self):
        return self._info.contents.crtc
    def get_available_rotations(self):
        if self.is_active():
            crtc = self._screen.get_crtc_by_xid(self._info.contents.crtc)
            return crtc.get_available_rotations()
        else:
            return None
    def get_available_modes(self):
        modes = []
        for m in range(self._info.contents.nmode):
            output_mode = self._info.contents.modes.contents[m]
            for s in range(self._screen._resources.contents.nmode):
                screen_mode = self._screen._resources.contents.modes.contents[s]
                if screen_mode.id == output_mode:
                    modes.append(screen_mode)
        return modes
    def get_preferred_mode(self):
        return self._info.contents.npreferred
    def is_active(self):
        return self._info.contents.crtc != 0

class Crtc:
    def __init__(self, info, xid, screen):
        self._info = info
        self.xid = xid
        self._screen = screen
    def __del__(self):
        rr.XRRFreeCrtcConfigInfo(self._info)
    def get_xid(self):
        return self.xid
    def get_available_rotations(self):
        return self._info.contents.rotations
    def set_config(self, x, y, mode, outputs):
        rr.XRRSetCrtcConfig(self._screen._display,
                            self._screen._resources,
                            self.xid,
                            self._screen.get_timestamp(),
                            x, y,
                            mode._id,
                            _array_conv(outputs, _c.c_ulong, lambda x: x._id),
                            len(outputs))

    def get_gamma_size(self):
        return rr.XRRGetCrtcGammaSize(self._screen._display, self.id)
    def get_gamma(self):
        result = rr.XRRGetCrtcGamma(self._screen._display, self.id)
        return _from_gamma(result)
    def set_gamma(self, gamma):
        g = _to_gamma(gamma)
        rr.XRRSetCrtcGamma(self._screen._display, self.id, g)
        rr.XRRFreeGamma(g)
    gamma = property(get_gamma, set_gamma)

class Screen:
    def __init__(self, dpy):
        self.outputs = {}
        self.crtcs = []

        self._display = dpy
        self._screen = xlib.XDefaultScreen(self._display)
        self._root = xlib.XDefaultRootWindow(self._display, self._screen)
        self._id = rr.XRRRootToScreen(self._display, self._root)
        
        self._load_screen_size_range()
        self._load_resources()
        self._load_config()
        if XRANDR_VERSION >= (1,2):
            self._load_outputs()
            self._load_crtcs()

    def __del__(self):
        rr.XRRFreeScreenConfigInfo(self._config)

    def _load_config(self):
        class XRRScreenConfiguration(Structure):
            " private to Xrandr "
            pass
        gsi = rr.XRRGetScreenInfo
        gsi.restype = POINTER(XRRScreenConfiguration)
        self._config = gsi(self._display, self._root)
        
    def _load_screen_size_range(self):
        minWidth = c_int()
        minHeight = c_int()
        maxWidth = c_int()
        maxHeight = c_int()
        res = rr.XRRGetScreenSizeRange(self._display, self._root, 
                                       byref(minWidth), byref(minHeight),
                                       byref(maxWidth), byref(maxHeight))
        if res:
            self.max_width = maxWidth.value
            self.min_width = maxWidth.value
            self.max_height = maxHeight.value
            self.min_height = minHeight.value

    def _load_resources(self):
        gsr = rr.XRRGetScreenResources
        gsr.restype = POINTER(_XRRScreenResources)
        self._resources = gsr(self._display, self._root)

    def _load_crtcs(self):
        for i in range(self._resources.contents.ncrtc):
            gci = rr.XRRGetCrtcInfo
            gci.restype = POINTER(_XRRCrtcInfo)
            xrrcrtcinfo = gci(self._display, self._resources,
                              self._resources.contents.crtcs.contents[i])
            self.crtcs.append(Crtc(xrrcrtcinfo,
                              self._resources.contents.crtcs.contents[i],
                              self))

    def _load_outputs(self):
        for i in range(self._resources.contents.noutput):
            goi = rr.XRRGetOutputInfo
            goi.restype = POINTER(_XRROutputInfo)
            xrroutputinfo = goi(self._display, self._resources,
                                self._resources.contents.outputs.contents[i])
            self.outputs[xrroutputinfo.contents.name] = Output(xrroutputinfo,
                                                               self)
    def get_timestamp(self):
        config_timestamp = Time()
        rr.XRRTimes.restpye = c_ulong
        return rr.XRRTimes(self._display, self._id, byref(config_timestamp))

    def get_crtc_by_xid(self, xid):
        for crtc in self.crtcs:
            if crtc.xid == xid:
                return crtc
        return None

    def get_current_rate(self):
        _check_required_version((1,0))
        xccr = rr.XRRConfigCurrentRate
        xccr.restype = c_int
        return xccr(self._config)

    def get_available_rates_for_size_index(self, size_index):
        _check_required_version((1,0))
        rates = []
        nrates = c_int()
        rr.XRRConfigRates.restype = POINTER(c_ushort*100)
        _rates = rr.XRRConfigRates(self._config, size_index, byref(nrates))
        for r in range(nrates.value):
            rates.append(_rates.contents[r])
        return rates

    def get_current_rotation(self):
        _check_required_version((1,0))
        current = c_ushort()
        rotations = rr.XRRConfigRotations(self._config, byref(current))
        return current.value

    def get_available_rotations(self):
        _check_required_version((1,0))
        current = c_ushort()
        rotations = rr.XRRConfigRotations(self._config, byref(current))
        return rotations

    def get_current_size_index(self):
        _check_required_version((1,0))
        rotation = c_ushort()
        size = rr.XRRConfigCurrentConfiguration(self._config,
                                                byref(rotation))
        return size

    def get_available_sizes(self):
        _check_required_version((1,0))
        nsizes = c_int()
        xcs = rr.XRRConfigSizes
        xcs.restype = POINTER(_XRRScreenSize*100)
        core_sizes = xrs(self._config, byref(nsizes))
        return sizes

    def set_config(self, size_index, rotation, rate):
        _check_required_version((1,0))
        status = rr.XRRSetScreenConfigAndRate(self._display,
                                              self._config,
                                              self._root,
                                              size_index,
                                              rotation,
                                              rate,
                                              self.get_timestamp())

    def print_info(self):
        _check_required_version((1,0))
        print "Modes (%s):" % self._resources.contents.nmode
        for i in range(self._resources.contents.nmode):
            print "  %s - %s %s" % (
                self._resources.contents.modes.contents[i].name,                    
                self._resources.contents.modes.contents[i].width,
                self._resources.contents.modes.contents[i].height)
        print "Outputs:"
        for o in self.outputs.keys():
            output = self.outputs[o]
            print "  %s (%s mm x %s mm)" % (o,
                                            output.get_physical_width(),
                                            output.get_physical_height())
            if output.is_active():
                print "    Rotations %s" % output.get_available_rotations()
                modes = output.get_available_modes()
                print "    Modes:"
                for m in range(len(modes)):
                    mode = modes[m]
                    if m == output.get_preferred_mode():
                        preferred = " (preferred)"
                    else: 
                        preferred = ""
                    refresh = mode.dotClock / (mode.hTotal * mode.vTotal)
                    print "      %s x %s @ %s%s" % (mode.width, mode.height, 
                                                    refresh, preferred)
            #for (f,t) in output._info.contents._fields_:
            #    print "%s %s" % (f, getattr(output._info.contents, f))

    def get_outputs(self):
        _check_required_version((1,2))
        return self.outputs


def get_current_display():
    display_url = os.getenv("DISPLAY")
    dpy = xlib.XOpenDisplay(display_url)
    return dpy

def get_current_screen():
    screen = Screen(get_current_display())
    return screen

def get_version():
    """ Returns a tuple containing the major and minor version of the xrandr
        extension """
    major = c_int()
    minor = c_int()
    res = rr.XRRQueryVersion(get_current_display(),
                             byref(major), byref(minor))
    if res:
        return (major.value, minor.value)
    return None

def has_extension():
    if XRANDR_VERSION:
        return True
    return False

def _to_gamma(gamma):
    g = rr.XRRAllocGamma(len(gamma[0]))
    for i in range(gamma[0]):
        g.red[i] = gamma[0][i]
        g.green[i] = gamma[1][i]
        g.blue[i] = gamma[2][i]
    return g

def _from_gamma(g):
    gamma = ([], [], [])
    for i in range(g.size):
        gamma[0].append(g.red[i])
        gamma[1].append(g.green[i])
        gamma[2].append(g.blue[i])
    rr.XRRFreeGamma(g)

def _check_required_version(version):
    if XRANDR_VERSION == None:
        raise ExtensionMissingException
    elif XRANDR_VERSION < version:
        raise UnsupportedException

XRANDR_VERSION = get_version()

"""

#FIXME: make this work somehow, the screen size changes
#       with the resolution
#print
#fb_width = 800
#fb_height = 600
#dpi = 25.4 * rr.XDisplayHeight (dpy, screen) / rr.XDisplayHeightMM(dpy, screen)
#fb_width_mm = 25.4 * fb_width / dpi
#fb_height_mm = 25.4 * fb_height /dpi
#print "dpi: ",dpi
#print "new width: ", fb_width
#print "new height: ", fb_height
#print "fb_width_mm: ",fb_width_mm
#print "fb_height_mm: ",fb_height_mm
#rr.XRRSetScreenSize(dpy, win, int(fb_width_mm), int(fb_height_mm))
"""
