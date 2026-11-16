import random

from otp.otpbase import OTPLocalizer as OL

# EPISODE GUI
EpisodePlay = 'Play'
EpisodeDisabled = 'Unavailable'

# EPISODE NAMES
EpisodeComingSoon = 'Coming Soon!'
EpisodeTestingGrounds = 'Testing Grounds'
EpisodePrologue = 'The Prologue'
EpisodeCogHighrise = 'Short Work'
EpisodeStormSellbot = 'Operation Storm Sellbot'
EpisodeSquirtingFlower = '? ? ? ? ?'
EpisodeATWSos = "Operation: Seek Out Scrooge Part 1"

# EPISODE DESCRIPTIONS
EpisodeTestingGroundsDesc = 'Developer testing grounds. This is a free zone to test with as you please.\n\nWith how ' \
                            'the Episode system is set up, this is pretty convenient.'
EpisodePrologueDesc = 'Experience the creation of the Cogs, playing as Scrooge McDuck!\n\nAs seen in Toontown ' \
                      'Online\'s 2003 Installation Video.'
EpisodeCogHighriseDesc = 'Ever wonder what it\'s like to live life as a Cog? Well now you can!\n\nVenture the ' \
                         'hallways of a Cog High Rise as a Level 1 Short Change!'
EpisodeStormSellbotDesc = 'How did Operation: Storm Sellbot occur? What caused the power surge in Sellbot ' \
                          'Headquarters? Find out in this Great Moment in Toontown History'
EpisodeSquirtingFlowerDesc = '? ? ? ? ?'
EpisodeATWSosDesc = "Join Flippy in the hunt for Scrooge."

''' ==== Episode 1 ==== '''
PrologueIntro = 'Some time ago...'
PrologueIntroDialogue = (
    'Ah, what a sunny day in Duckburg!',
    "Mayhaps I should go and see what my good ol' friend Gyro has been up to!",
    'What was that lad working on again? Some robot whatchamacallit?',
    "Launchpad McQuack, fire her engines up! We're headed to Toontown!",
    'Yes sir, Mr. McDuck! Setting course to Daisy Gardens!'
)
PrologueIntroCard = (
    "Our story begins on\nthe outskirts of\nthe place cartoon\ncharacters call 'home.'",
    'On this day, world-famous\nbillionaire Scrooge McDuck\ndecides to pay a visit to his\nfavorite '
    'employee, eccentric\ninventor Gyro Gearloose...'
)
PrologueLaunchpadMcQuack = 'Launchpad McQuack'
PrologueOakStreetDialogue = (
    "Well, here we are Mr. McDuck! Gyro's Laboratory in Toontown!",
    "Thank you Launchpad. I'll send Gyro your regards.",
    "Tell that lump of feathers that he needs to come back to Duckburg once in a while!",
    "Give me a call when you're done sir!"
)
PrologueLabDialogue = (
    'Gyro?',
    'I wonder where Gyro could be?',
    "Sufferin' catfish! A g-g-giant robot!",
    'Hmm... a giant robot...',
    'Perfect!',
    'Why, a thing like this could be a really big help to the citizens of Toontown...',
    '....and make ME a big pile of money!',  # extra . to account for displayTalk eating the first .
    "\"Do not touch!\"",
    'PHOOEY!',
    "That can't mean me! After all, I paid for it.",
    "Let's get my investment up and running!",
    'Maybe if I connect the blue one to the red one...',
    'ALL SYSTEMS READY',
    'Great heavens to Betsy! What have I done?',
    'GO!',
    'No.',
    'Oh my heavenly days!',
    "This can't be good..."
)
PrologueOutro = "Gyro's invention is running amok!\nScrooge has placed himself and\nall of Toontown in danger! " \
                "Can\nanyone stop this army of robots?\nToontown needs your help now!"

''' ==== Episode 2 ==== '''
ShortChangeOfficeDialogue = (
    'This will be a short-term assignment.', 'Hmmph? It appears to be my lunch break.',
    "About time. I've needed an oil change all day.", "Let's make this a short stop."
)
ShortChangeBathroomDialogue = (
    "I believe you're in the wrong office.", 'Yikes! A Cog!',
    "You won't be getting past me.",
    "I believe a promotion is in order.", 'What a relaxing oil cleaning that was.'
)
ShortWorkBathroomBattleChooseAttack = 'Choose An Attack'
ShortWorkBathroomBattleAttackLbl = 'Accuracy: {0}\nDamage: {1}\n{2}\nCogbucks: 1'
ShortWorkBathroomBattleDefaultCogbuckAmt = '39/40 '
ShortWorkBathroomBattleLevelLbl = 'Level 1'
ShortChangeBarDialogue = 'I need to see a Bossbot regarding my promotion.'
ShortWorkIntroCard = (
    "This story begins in one\nof the Cog Headquarters,\nA place ridden with trains\nand greasy 'Cashbots'.",
    "A Level 1 Short Change\nhad just finished up a\nhard days work in a\nCashbot Cog High Rise.",
    "What did this day\nhave in store for our\nLevel 1 Short Change?\nLet's find out...")
ShortWorkDefeatCard = (
    'And so, Professor Guffaw\n'
    'managed to defeat the\n'
    'Short Change with only\n'
    'a couple level one gags.',

    '\nThe\n'
    'End')
ShortWorkDemoteCard = (
    'And so, The Big Cheese\n'
    'demoted the Short Change\n'
    'right on the spot for\n'
    'his outrageous disturbance.',

    '\nThe\n'
    'End')
ShortWorkBarWaiterDialogue = (
    'Bean Counter, get me a %s!',
    'On it.',
    'Yes, Mr. Big Wig?',
    'Got it, sir.',
    'Here you are, sir.',
    "It's my job, sir.",
    'Hey, Mr. Bean Counter.',
    "I'll have a %s too. Put it on the C.J.'s tab.",
    'Thanks.'
)
ShortWorkBarRequestDialogue = (
    'triple double oil supreme',
    'Diet Petroleum'
)
ShortWorkCogGarble = (
    "Where's my drink!?",
    'Arrgh!',
    'Hmmmph.',
    'Bah.',
    'Garble.',
    'Bah bah bah bah-bah, bah bah-bah bah.',
    'My break is almost over!',
    'I have Toons to be saddening!',
    'Get over here!',
    'Service!'
)
ShortWorkRaiderDialogue = "You don't fit in around here, Short Change. Go bother some other Cog."
ShortWorkPromotionDialogue = (
    'Talk to my assistant.',
    'Ahem.',
    'What do you want, Short String?',
    'You need a... promotion?',
    "Leave cracking jokes to the Toons. It's short-sighted to lie to an executive.",
    'You have one? I was afraid you were stringing me along.',
    'Hmmm...')
ShortWorkPromotionSceneDialogue = (
    "It's not that often I see Short Changes flashing their promotions around.",
    'I hereby promote you to a Level 2 Short Cha-',
    'Excuse me, sir. I was sent on urgent business.',
    "You've pushed my buttons enough this month. What is it this time?",
    'The Boss has sent me to inform you about another company restructure.',
    'Our previous C.E.O. has been demoted once again.',
    'You are wanted in Cog Nation for immediate promotion.',
    "Very well. I will be departing on the next train to Cog Nation.",
    'See to it that this Short Change has his Promotion Papers completed.',
    'Right away, sir. I wish you all the best, Mr. C.E.O.'
)
ShortWorkDemotionDialogue = (
    'Talk to my assistant.',
    'Ahem.',
    'What do you want, Short String?',
    'A promotion? Hmmmph. Your name suits you well.',
    "Your short-temperedness can't escape even this fine establishment.",
    'I believe a demotion is in order- for disturbing your executive!'
)

''' ==== Episode 3 ==== '''
StormSellbotIntroCard = (
    "This Great Moment in\n"
    "Toontown history\n"
    "begins in\n"
    "Daisy Gardens Playground.",

    "As Toons are celebrating\n"
    "Victory Parties across\n"
    "Toontown, An unexpected\n"
    "event occurs at the pet shop.\n"
)


''' ==== Episode 4 ==== '''
SosFailDoorCard = (
    "Flippy failed to\n"
    "open the door.\n"
    "So he went sad.\n"
    "It's quite sad init."
)

Sos4ScroogeIntro = (
    "Hi.",
    "You found me.",
    "Excellent work.",
    "However...",
    "It took you much longer than I expected.",
    "I'm actually very disappointed.",
    "For a while I thought you were just ignoring the fact that I was missing.",
    "Ignore means refuse to take notice of or acknowledge; disregard intentionally.",
    "It bothers me.",
    "\x01white\x01\5thumbs_down\5\x02",
    "It's ok though.",
    "As you have sought out me.",
    "Enough of that though.",
    "Sir... Thank you.",
    "By the way I'm British now."
)