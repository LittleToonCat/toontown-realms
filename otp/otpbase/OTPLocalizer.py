from direct.showbase import DConfig

try:
    language = DConfig.GetString('language', 'english')
    checkLanguage = DConfig.GetBool('check-language', 0)
except:
    language = simbase.config.GetString('language', 'english')
    checkLanguage = simbase.config.GetBool('check-language', 0)

def getLanguage():
    return language


print('OTPLocalizer: Running in language: %s' % language)
if language == 'english':
    _languageModule = 'otp.otpbase.OTPLocalizer' + language.capitalize()
else:
    checkLanguage = 1
    _languageModule = 'otp.otpbase.OTPLocalizer_' + language
from otp.otpbase.OTPLocalizerEnglish import *
if checkLanguage:
    l = {}
    g = {}
    try:
        # For Pypperoni
        import localizer_index
        englishModule = localizer_index.get_otplocalizer('otp.otpbase.OTPLocalizerEnglish')
        foreignModule = localizer_index.get_otplocalizer(_languageModule)
    except ModuleNotFoundError:
        englishModule = __import__('otp.otpbase.OTPLocalizerEnglish', g, l)
        foreignModule = __import__(_languageModule, g, l)
    for key, val in list(englishModule.__dict__.items()):
        if key not in foreignModule.__dict__:
            print('WARNING: Foreign module: %s missing key: %s' % (_languageModule, key))
            locals()[key] = val
        elif isinstance(val, dict):
            fval = foreignModule.__dict__.get(key)
            for dkey, dval in list(val.items()):
                if dkey not in fval:
                    print('WARNING: Foreign module: %s missing key: %s.%s' % (_languageModule, key, dkey))
                    fval[dkey] = dval

            for dkey in list(fval.keys()):
                if dkey not in val:
                    print('WARNING: Foreign module: %s extra key: %s.%s' % (_languageModule, key, dkey))

    for key in list(foreignModule.__dict__.keys()):
        if key not in englishModule.__dict__:
            print('WARNING: Foreign module: %s extra key: %s' % (_languageModule, key))

if __debug__:
    def getLanguageModule():
        langModule = __import__(_languageModule)
        return langModule
