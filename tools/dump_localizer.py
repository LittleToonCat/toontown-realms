from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer

with open('ttlocalizer.txt', 'w') as ttl:
    for key, val in TTLocalizer.__dict__.items():
        if isinstance(val, str):
            ttl.write(f'#{key} = {repr(val)}\n')
with open('otplocalizer.txt', 'w') as otpl:
    for key, val in OTPLocalizer.__dict__.items():
        if isinstance(val, str):
            otpl.write(f'#{key} = {repr(val)}\n')