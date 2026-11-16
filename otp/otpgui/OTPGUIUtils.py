from typing import Tuple

from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.interval.IntervalGlobal import *
from panda3d.core import Vec3, Vec4, VBase4

from toontown.toonbase import ClientSettings


def getImageScale(imageWidth: int, imageHeight: int, scale: float = 1.0) -> Tuple[float, float, float]:
    return (imageWidth / imageHeight) * scale, 1, scale


class Animations:
    @staticmethod
    def staggeredMoveDown(items, delay = 0.05, *ignoreList):
        """
        Move and Fade all items with a slight delay
        :param items: List of all gui objects
        :param delay: The delay between the starting point of each object
        :param ignoreList: Any items to not animate
        """
        if not ClientSettings.GUIAnimations.get():
            return
        seq = Sequence()
        for i in items:
            if i not in ignoreList:
                i.setTransparency(1)
                finalPos = i.getPos()
                i.setColorScale(1.0, 1.0, 1.0, 0.0)
                fadeIn = Parallel(
                        i.posInterval(0.2, finalPos, i.getPos() - Vec3(0, 0, -0.1), blendType = 'easeOut'),
                        LerpColorScaleInterval(i, 0.2, Vec4(1.0), Vec4(1.0, 1.0, 1.0, 0.0), blendType = 'easeOut')
                )
                seq.append(Func(fadeIn.start))
                seq.append(Wait(delay))
        seq.start()

    @staticmethod
    def staggeredMoveUp(items, delay = 0.05, *ignoreList):
        """
        Move and Fade all items with a slight delay
        :param items: List of all gui objects
        :param delay: The delay between the starting point of each object
        :param ignoreList: Any items to not animate
        """
        if not ClientSettings.GUIAnimations.get():
            return
        seq = Sequence()
        for i in items:
            if i not in ignoreList:
                i.setTransparency(1)
                finalPos = i.getPos()
                i.setColorScale(1.0, 1.0, 1.0, 0.0)
                fadeIn = Parallel(
                        i.posInterval(0.2, finalPos, i.getPos() - Vec3(0, 0, 0.1), blendType = 'easeOut'),
                        LerpColorScaleInterval(i, 0.2, Vec4(1.0), Vec4(1.0, 1.0, 1.0, 0.0), blendType = 'easeOut')
                )
                seq.append(Func(fadeIn.start))
                seq.append(Wait(delay))
        seq.start()

    @staticmethod
    def staggeredPopUp(items, delay = 0.05, *ignoreList):
        """
        Pop and Fade all items with a slight delay
        :param items: List of all gui objects
        :param delay: The delay between the starting point of each object
        :param ignoreList: Any items to not animate
        """
        if not ClientSettings.GUIAnimations.get():
            return
        seq = Sequence()
        for i in items:
            if i not in ignoreList:
                i.setTransparency(1)
                finalScale = i.getScale()
                i.setScale(finalScale * 0.5)
                i.setColorScale(1.0, 1.0, 1.0, 0.0)
                par = Parallel(
                        Sequence(i.scaleInterval(.2, Vec3(finalScale * 1.1), blendType = 'easeInOut'),
                                 i.scaleInterval(.1, Vec3(finalScale), blendType = 'easeInOut')),
                        LerpColorScaleInterval(i, .2, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0), blendType = 'easeInOut')
                )
                seq.append(Func(par.start))
                seq.append(Wait(delay))
        seq.start()

    @staticmethod
    def popup(element: DirectGuiWidget, finalScale: float = 1.0) -> Sequence:
        return Sequence(
                LerpScaleInterval(element, 0.15, finalScale * 1.1, 0.01, blendType = 'easeInOut'),
                LerpScaleInterval(element, 0.08, finalScale * 0.9, blendType = 'easeInOut'),
                LerpScaleInterval(element, 0.1, finalScale * 1.05, blendType = 'easeInOut'),
                LerpScaleInterval(element, 0.12, finalScale * 0.95, blendType = 'easeInOut'),
                LerpScaleInterval(element, 0.14, finalScale * 1.0, blendType = 'easeInOut'),
                name = f'element{element.getName()}.popup'
        )

    @staticmethod
    def slideUp(element: DirectGuiWidget, finalZ: float, startZ: float = 0.0, intensity: float = 1) -> Sequence:
        x: float = element.getX()
        return Sequence(
                Parallel(
                        LerpColorScaleInterval(element, 0.15, VBase4(1.0, 1.0, 1.0, 1.0), VBase4(1.0, 1.0, 1.0, 0.0),
                                               blendType = 'easeInOut'),
                        LerpPosInterval(element, 0.15, pos = (x, 0.0, finalZ + (.05 * intensity)),
                                        startPos = (x, 0, startZ), blendType = 'easeInOut'),
                ),
                LerpPosInterval(element, 0.08, pos = (x, 0.0, finalZ - (.05 * intensity)), blendType = 'easeInOut'),
                LerpPosInterval(element, 0.10, pos = (x, 0.0, finalZ + (.025 * intensity)), blendType = 'easeInOut'),
                LerpPosInterval(element, 0.12, pos = (x, 0.0, finalZ - (.025 * intensity)), blendType = 'easeInOut'),
                LerpPosInterval(element, 0.14, pos = (x, 0.0, finalZ), blendType = 'easeInOut'),
                name = f'element{element.getName()}.slideUp'
        )

    @staticmethod
    def slideDown(element: DirectGuiWidget, finalZ: float, startZ: float = 0.0, intensity: float = 1) -> Sequence:
        x: float = element.getX()
        return Sequence(
                Parallel(
                        LerpColorScaleInterval(element, 0.15, VBase4(1.0, 1.0, 1.0, 1.0), VBase4(1.0, 1.0, 1.0, 0.0),
                                               blendType = 'easeInOut'),
                        LerpPosInterval(element, 0.15, pos = (x, 0.0, finalZ - (.05 * intensity)),
                                        startPos = (x, 0, startZ), blendType = 'easeInOut'),
                ),
                LerpPosInterval(element, 0.08, pos = (x, 0.0, finalZ + (.05 * intensity)), blendType = 'easeInOut'),
                LerpPosInterval(element, 0.10, pos = (x, 0.0, finalZ - (.025 * intensity)), blendType = 'easeInOut'),
                LerpPosInterval(element, 0.12, pos = (x, 0.0, finalZ + (.025 * intensity)), blendType = 'easeInOut'),
                LerpPosInterval(element, 0.14, pos = (x, 0.0, finalZ), blendType = 'easeInOut'),
                name = f'element{element.getName()}.slideUp'
        )

    @staticmethod
    def pulse(element: DirectGuiWidget, halfDuration: float, intensity: float = 0.95, loopDelay: float = 0):
        scale: Vec3 = element.getScale()
        seq = Sequence(
            LerpScaleInterval(element, halfDuration, scale * intensity, blendType = 'easeIn'),
            LerpScaleInterval(element, halfDuration, scale, blendType = 'easeOut')
        )
        if loopDelay:
            seq.append(Wait(loopDelay))
        return seq
