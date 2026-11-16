import random
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from otp.chat import ChatGarbler


class ToonChatGarbler(ChatGarbler.ChatGarbler):
    animalSounds = {'dog': TTLocalizer.ChatGarblerDog,
                    'cat': TTLocalizer.ChatGarblerCat,
                    'mouse': TTLocalizer.ChatGarblerMouse,
                    'horse': TTLocalizer.ChatGarblerHorse,
                    'rabbit': TTLocalizer.ChatGarblerRabbit,
                    'duck': TTLocalizer.ChatGarblerDuck,
                    'monkey': TTLocalizer.ChatGarblerMonkey,
                    'bear': TTLocalizer.ChatGarblerBear,
                    'pig': TTLocalizer.ChatGarblerPig,
                    'gyro': TTLocalizer.ChatGarblerChicken,
                    'scrooge': TTLocalizer.ChatGarblerScrooge,
                    'default': OTPLocalizer.ChatGarblerDefault}

    def __getGarbleList(self, animalType):
        return ToonChatGarbler.animalSounds.get(animalType, 'default')

    def garble(self, toon, message):
        newMessage = ''
        animalType = toon.getStyle().getType()
        wordlist = self.__getGarbleList(animalType)
        numWords = random.randint(1, 7)
        for i in range(1, numWords + 1):
            wordIndex = random.randint(0, len(wordlist) - 1)
            newMessage = newMessage + wordlist[wordIndex]
            if i < numWords:
                newMessage = newMessage + ' '

        return newMessage

    def garbleSingle(self, animalType, message):
        newMessage = ''
        wordlist = self.__getGarbleList(animalType)
        numWords = 1
        for i in range(1, numWords + 1):
            wordIndex = random.randint(0, len(wordlist) - 1)
            newMessage = newMessage + wordlist[wordIndex]
            if i < numWords:
                newMessage = newMessage + ' '

        return newMessage
