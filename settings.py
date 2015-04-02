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
# Do not edit

SKIP_LINK = set(["depression", "lifeafternarcissists", "managedbynarcissists",
                 "moderationlog", "raisedbynarcissists", "rbnathome",
                 "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames",
                 "rbnlifeskills", "rbnmovienight", "rbnrelationships",
                 "rbnspouses", "suicidewatch", "switcharoo", "switcheroo",
                 "trolledbynarcissists", "unremovable", "politic", "mlplite",
                 "risingthreads", "uncensorship", "leagueofriot",
                 "benlargefanclub", "fitnesscirclejerk", "taiwancirclejerk",
                 "requestedtweaks", "jaxbrew", "floridabrew", "aggregat0r",
                 "gamecollectingjerk", "technews2015"])

BANNED = set(["reddit.com", "minecraft", "adviceanimals", "askreddit",
              "worldnews", "femradebates", "pcmasterrace", "purplepilldebate",
              "slrep", "funny", "theredpill", "personalfinance", "india",
              "lifehacks", "kotakuinaction", "askmen", "smashbros", "android",
              "neutralpolitics", "dota2", "wet_shavers", "dogecoin",
              "askphilosophy", "suits", "japanlife", "photography",
              "hiphopheads", "apple", "lifeprotips", "nba", "dbz",
              "gender_critical", "movies"])

IGNORED_USERS = set(["amprobablypooping", "evilrising", "frontpagewatch",
                     "frontpagewatchmirror", "moon-done", "politicbot",
                     "rising_threads_bot", "removal_rover", "know_your_shit",
                     "drugtaker", "nedsc"])

IGNORED_SOURCES = (SKIP_SOURCE | BANNED) - SKIP_LINK
IGNORED_LINKS = SKIP_LINK - (SKIP_LINK | BANNED)
IGNORED_BOTH = (SKIP_SOURCE | BANNED) & SKIP_LINK

