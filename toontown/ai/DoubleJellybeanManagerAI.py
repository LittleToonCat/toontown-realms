# TODO: maybe do something more here
from direct.directnotify.DirectNotifyGlobal import directNotify

from toontown.ai.HolidayBaseAI import HolidayBaseAI


class _DoubleJellybeanBase(HolidayBaseAI):
    notify = directNotify.newCategory('DoubleJellybeanBase')

    def start(self):
        if self.__class__.__name__ == '_DoubleJellybeanBase':
            raise Exception('Directly using base class. Gustavo says no!')
        self.notify.debug('Started double jellybean holiday for {}'.format(self.__class__.__name__))

    def stop(self):
        if self.__class__.__name__ == '_DoubleJellybeanBase':
            raise Exception('Directly using base class. Gustavo says no!')
        self.notify.debug('Stopped double jellybean holiday for {}'.format(self.__class__.__name__))


class DoubleJellybeanTrolleyAI(_DoubleJellybeanBase):
    notify = directNotify.newCategory('DoubleJellybeanTrolleyAI')


class DoubleJellybeanFishingAI(_DoubleJellybeanBase):
    notify = directNotify.newCategory('DoubleJellybeanFishingAI')


class DoubleJellybeanPartyAI(_DoubleJellybeanBase):
    notify = directNotify.newCategory('DoubleJellybeanPartyAI')
