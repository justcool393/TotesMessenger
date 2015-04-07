# Links submitted in these subs that point to other posts and comments
# (sources) elsewhere on reddit are skipped:
SKIP_LINK = set(["depression", "lifeafternarcissists", "managedbynarcissists",
                   "moderationlog", "raisedbynarcissists", "rbnathome",
                   "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames",
                   "rbnlifeskills", "rbnmovienight", "rbnrelationships",
                   "rbnspouses", "suicidewatch", "switcharoo", "switcheroo",
                   "trolledbynarcissists", "unremovable", "politic", "mlplite",
                   "risingthreads", "uncensorship", "leagueofriot",
                   "benlargefanclub", "fitnesscirclejerk", "taiwancirclejerk",
                   "requestedtweaks", "jaxbrew", "floridabrew", "aggregat0r",
                   "gamecollectingjerk", "technews2015", "serendipity",
                   "removalseuropean"])

# Posts and comments (sources) in these subs that are linked to from elsewhere
# on reddit are ignored:
SKIP_SOURCE = set(["anime", "asianamerican", "askhistorians", "askscience",
                 "aww", "benfrick", "bmw", "chicagosuburbs", "cosplay",
                 "cumberbitches", "d3gf", "deer", "depression", "depthhub",
                 "drinkingdollars", "forwardsfromgrandma", "futurology",
                 "geckos", "giraffes", "graphical_design", "grindsmygears",
                 "indianfetish", "misc", "mixedbreeds", "news", "newtotf2",
                 "omaha", "petstacking", "pigs", "politicaldiscussion",
                 "programmingcirclejerk", "raerthdev", "rants", "salvia",
                 "science", "seiko", "shoplifting", "sketches", "sociopath",
                 "suicidewatch", "talesfromtechsupport", "unitedkingdom"])

# We can't post in these subs, so posts and comments (sources) in these subs
# don't get notified:
BANNED = set(["reddit.com", "minecraft", "adviceanimals", "askreddit",
              "worldnews", "femradebates", "pcmasterrace", "purplepilldebate",
              "slrep", "funny", "theredpill", "personalfinance", "india",
              "lifehacks", "kotakuinaction", "askmen", "smashbros", "android",
              "neutralpolitics", "dota2", "wet_shavers", "dogecoin",
              "askphilosophy", "suits", "japanlife", "photography",
              "hiphopheads", "apple", "lifeprotips", "nba", "dbz",
              "gender_critical", "movies", "food", "korean", "asktrp",
              "debatereligion", "beerporn", "trueatheism", "badphilosophy",
              "srswomen", "buildapc", "rddt6", "perfect_timing", "askuk",
              "gendercritical", "offbeat", "worldoftanks", "conspiracy",
              "cringpics", "books", "tagpro", "music", "fantasy",
              "marriedredpill", "gmonews", "citiesskylines",
              "trollxchromosones", "conservative", "plazaaragon", "modhelp",
              "jokes", "changetip", "guns", "trackers", "ottawa", "dogtraining",
              "fatpeoplehate", "netsec", "metal", "teslore",
              "mechanicalkeyboards", "gifs", "technology", "asatru", "vinyl",
              "againstthechimpire", "nazihunting", "europe", "paradoxplaza",
              "china", "ukpolitics", "beertrade", "litecoin", "snowboarding",
              "explainlikeimfive", "gaming", "interestingasfuck",
              "adventuretime"])

# Submissions by these users that link to other posts and comments are ignored:
IGNORED_USERS = set(["amprobablypooping", "evilrising", "frontpagewatch",
                     "frontpagewatchmirror", "moon-done", "politicbot",
                     "rising_threads_bot", "removal_rover", "know_your_shit",
                     "drugtaker", "nedsc", "serendipitybot"])

IGNORED_SOURCES = (SKIP_SOURCE | BANNED) - SKIP_LINK
IGNORED_LINKS = SKIP_LINK - (SKIP_SOURCE | BANNED)
IGNORED_BOTH = (SKIP_SOURCE | BANNED) & SKIP_LINK

