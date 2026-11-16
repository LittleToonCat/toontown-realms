import colorsys

from panda3d.core import Vec4, Vec3


def hsvToRgb(h, s, v, a = 1.0):
    """ Static convenience function to turn hsv into a vbase4 rgba - hsv_to_rgb only does rgb """
    rgb = colorsys.hsv_to_rgb(h, s, v)
    return Vec4(rgb[0], rgb[1], rgb[2], a)


def rgbToHsv(r, g, b, a = 1):
    """ Static convenience function to turn rgb(a) into hsv """
    hsv = colorsys.rgb_to_hsv(r, g, b)
    return Vec3(hsv[0], hsv[1], hsv[2])


def hsvFloatToInt(hue, saturation, value, alpha):
    return [int(hue * 360), int(saturation * 100), int(value * 100), int(alpha * 100)]


def hsvIntToFloat(hue, saturation, value, alpha):
    return [hue / 360., saturation / 100., value / 100., alpha / 100.]