import ftplib, logging, os, praw, re, time, traceback, sys, requests.exceptions
import datetime, random  # for science. (apr 1st stuff)

linked = []
linkedsrc = []
skipped = []
skippedsrc = []
linkedcount = 0
errorcount = 0

TESTING = False
ARCHIVE_TIME = 15778463  # currently 6 months (in seconds)
CRASH_TIMER = 60
CJ_HEADER = u"This dank meme has been linked to from another place on le reddit."
HEADER = u"This thread has been linked to from another place on reddit."
FOOTER = u"[](#footer)*^If ^you ^follow ^any ^of ^the ^above ^links, ^respect ^the ^rules ^of ^reddit ^and ^don't ^vote. ^\([Info](/r/TotesMessenger/wiki/) ^/ ^[Contact](/message/compose/?to=\/r\/TotesMessenger))* [](#bot)"

user = os.environ['REDDIT_USER']
blacklist = ["anime", "asianamerican", "askhistorians", "askscience", "aww", "benfrick", "bmw", "chicagosuburbs",
             "cosplay", "cumberbitches", "d3gf", "deer", "depression", "depthhub", "drinkingdollars",
             "forwardsfromgrandma", "futurology", "geckos", "giraffes", "graphical_design", "grindsmygears",
             "indianfetish", "misc", "mixedbreeds", "news", "newtotf2", "omaha", "petstacking", "pigs",
             "politicaldiscussion", "programmingcirclejerk", "raerthdev", "rants", "salvia", "science",
             "seiko", "shoplifting", "sketches", "sociopath", "suicidewatch", "talesfromtechsupport", "unitedkingdom"]
# Do not edit

srcblacklist = ["depression", "lifeafternarcissists", "managedbynarcissists", "moderationlog", "raisedbynarcissists",
                "rbnathome", "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames", "rbnlifeskills", "rbnmovienight",
                "rbnrelationships", "rbnspouses", "suicidewatch", "switcharoo", "switcheroo", "trolledbynarcissists",
                "unremovable", "politic", "mlplite", "risingthreads", "uncensorship", "leagueofriot", "benlargefanclub",
                "fitnesscirclejerk", "taiwancirclejerk", "requestedtweaks", "jaxbrew", "floridabrew", "aggregat0r",
                "gamecollectingjerk", "technews2015", "runningcirclejerk", "nosillysuffix", "leoduhvinci",
                "slowplounge", "listentoremoved", "removalseuropean", "programmingcirclejerk"]

banned = ["reddit.com", "minecraft", "adviceanimals", "askreddit", "worldnews", "femradebates", "pcmasterrace",
          "purplepilldebate", "slrep", "funny", "theredpill", "personalfinance", "india", "lifehacks", "kotakuinaction",
          "askmen", "smashbros", "android", "neutralpolitics", "dota2", "wet_shavers", "dogecoin", "askphilosophy",
          "suits", "japanlife", "photography", "hiphopheads", "apple", "lifeprotips", "nba", "dbz", "gender_critical",
          "movies", "gendercritical"]

blockedusers = ["amprobablypooping", "evilrising", "frontpagewatch", "frontpagewatchmirror", "moon-done", "politicbot",
                "rising_threads_bot", "removal_rover", "know_your_shit", "drugtaker", "nedsc", "illusionbot",
                "multifunctionbot"]

# Ban list:
# drugtaker        - Meta bot NSFW marking evasion
# NedSc            - By request
# IllusionBot      - Bot (by request)
# MultiFunctionBot - Bot (by request of EP mods)

nsfwreddits = ["srsshillwatch", "srsshillswatch", "srshillswatch", "srshillwatch", "gonewild"]

test_reddits = ["justcool393", "tmtest", "totesmessenger"]


def main():
    global linked
    global linkedsrc
    global skipped
    global skippedsrc
    global linkedcount
    global errorcount

    create_files()

    linked = load_list("linked.lst")
    linkedsrc = load_list("linkedsrc.lst")
    skipped = load_list("skipped.lst")
    skippedsrc = load_list("skippedsrc.lst")

    r = praw.Reddit("Links to reddit posts from other places in reddit", domain="api.reddit.com", log_requests=0)
    r.login(user, os.environ['REDDIT_PASS'])
    logging.info("Logged in to reddit...")

    add_linked(r)
    logging.info(
        "L: " + str(len(linked)) + ", LS: " + str(len(linkedsrc)) + ", S:" + str(len(skipped)) + ", SS: " +
        str(len(skippedsrc)))

    check_at = 3600.0
    save_at = 1800.0
    last_logged = 0.0
    last_saved = 0.0
    times_zero = 1

    link_subs(r, 100, 0)  # Check the last 100 posts on startup
    while True:

        if time.time() - last_saved >= save_at:
            logging.info("Saving list data, expect short delay...")
            last_saved = time.time()
            save_lists(["linked.lst", "linkedsrc.lst", "skipped.lst", "skippedsrc.lst"],
                       [linked, linkedsrc, skipped, skippedsrc])

        if time.time() - last_logged >= check_at:
            last_logged = time.time()
            if linkedcount == 0:
                times_zero += 1
            else:
                logging.info(
                    "Last " + str((int(check_at) * times_zero) / 60 / 60) + " hr(s): Linked " + str(linkedcount)
                    + ", " + str(errorcount) + " failed.")
                linkedcount = 0
                errorcount = 0
                times_zero = 1

        link_subs(r, 25, 30)
        ex_post(r)  # ### Code for April Fool's Prank ### #


def add_linked(r):
    for c in r.user.get_comments(sort='new', limit=None):
        pid = c.parent_id
        if pid is None:
            continue
        if pid not in linked:
            linked.append(pid)
        # Add linkedsrc one in to one method.
        posts = re.findall("http://np.reddit.com/r/.{1,20}/comments/.{1,8}/", c.body)
        for p in posts:
            pid = re.sub("http://np.reddit.com/r/.{1,20}/comments/", "", p)[:-1]
            if pid not in linkedsrc:
                linkedsrc.append(pid)


def link_subs(r, count, delay):
    for submission in r.get_domain_listing('reddit.com', sort='new', limit=count):

        if TESTING and submission.subreddit.display_name.lower() not in test_reddits:
            continue

        try:
            if link_submission(r, submission):
                time.sleep(2)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
            handle_http_error(ex)

    time.sleep(delay)


def link_submission(r, submission):
    global linkedcount
    global errorcount
    url = re.sub("(\#|\?).{1,}", "", submission.url)
    if not is_comment(url):
        return False

    linkedp = None

    try:
        linkedp = get_object(r, url)
    except praw.errors.ClientException:
        logging.error("Link is not a reddit post (id: " + submission.id + ")")
        logging.error(exi())
        return False
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
        handle_http_error(ex)
        return False
    except Exception:
        logging.error("Could not get comment!")
        logging.error(exi())
        return False

    if linkedp is None:
        return False

    lid = linkedp.id
    sid = submission.id

    # Skip conditions: Already deleted, undelete/scraper/mod log bots, blacklisted, banned/archived,
    # archived, in source blacklist

    if linkedp.subreddit is None or linkedp.author is None:
        skipped.append(lid)
        return False

    srlower = linkedp.subreddit.display_name.lower()

    if srlower in blacklist or srlower in banned or linkedp.created < (time.time() - ARCHIVE_TIME):
        skipped.append(lid)
        return False

    if linkedp.subreddit.user_is_banned:
        banned.append(srlower)
        skipped.append(lid)
        return False

    if submission.subreddit.display_name.lower() in srcblacklist or submission.author is None:
        skippedsrc.append(sid)
        return False

    if submission.author.name.lower() in blockedusers:
        skippedsrc.append(sid)
        return False

    if lid in skipped or sid in skippedsrc:
        return False

    if sid in linkedsrc:
        return False

    if lid in linked or check_commmented(linkedp) or get_bot_comment(linkedp) is not None:
        success = edit_post(get_bot_comment(linkedp), submission)
        if success:
            linkedsrc.append(sid)
            if lid not in linked:
                linked.append(lid)
        else:
            errorcount += 1
        return success

    cj = srlower == "circlejerk"  # check if our subreddit is /r/circlejerk so we can user our specialized msg for it

    if isinstance(linkedp, praw.objects.Comment):
        success = comment(linkedp, submission, cj)
    elif isinstance(linkedp, praw.objects.Submission):
        success = post(linkedp, submission, cj)
    else:
        logging.error("Not a Comment or Submission! (ID: " + lid + ")")
        errorcount += 1
        return False

    if success:
        linked.append(lid)
        linkedsrc.append(sid)
        linkedcount += 1
    return success


def edit_post(totessubmission, original):
    if totessubmission is None:
        return False
    text = re.sub("\[\]\(#footer\).{1,}", "", totessubmission.body)  # sub. invisible link for easier footer changes
    text = re.sub("\*\^If.{1,}", "", text)
    text = re.sub("\^Please.{1,}", "", text)  # substitute old footer as well
    text = re.sub("Do not vote.{1,}", "", text)  # substitute original footer as well
    text = text + format_link(original) + u"""


""" + FOOTER
    totessubmission.edit(text)
    return True


def check_commmented(c):
    if isinstance(c, praw.objects.Comment):
        comments = c.replies
    elif isinstance(c, praw.objects.Submission):
        c.replace_more_comments(limit=None, threshold=0)
        comments = praw.helpers.flatten_tree(c.comments)

    for co in comments:
        if co.author is None:
            continue
        if co.author.name.lower() == user.lower():
            return True
    return False


def get_bot_comment(s):
    if isinstance(s, praw.objects.Comment):
        for c in s.replies:
            if c.author is None:
                continue
            if c.author.name.lower() == user.lower():
                return c
    else:
        s.replace_more_comments(limit=None, threshold=0)
        flat_comments = praw.helpers.flatten_tree(s.comments)
        for c in flat_comments:
            if c.author is None:
                continue
            if c.author.name.lower() == user.lower():
                return c
    return None


def format_comment(original, isrcirclejerk):
    if isrcirclejerk:
        cmt = CJ_HEADER
    else:
        cmt = HEADER
    cmt = cmt + u"""

{link}

""" + FOOTER

    return cmt.format(link=format_link(original))


def post(s, original, isrcirclejerk):
    try:
        s.add_comment(format_comment(original, isrcirclejerk))
        return True
    except praw.errors.RateLimitExceeded:
        logging.debug("Can't comment (comment karma is too low)")
    except praw.errors.APIException as e:
        logging.warning(str(e))
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
        handle_http_error(ex)
    except Exception:
        logging.error("Error adding comment (SID: " + str(s.id) + ")")
        logging.error(exi())
    return False


def comment(c, original, isrcirclejerk):
    try:
        c.reply(format_comment(original, isrcirclejerk))
        return True
    except praw.errors.RateLimitExceeded:
        logging.debug("Can't comment (comment karma is too low)")
    except praw.errors.APIException as ex:
        logging.warning(str(ex))
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
        handle_http_error(ex)
    except Exception as ex:
        logging.error("Error adding comment (CID: " + str(c.id) + ")")
        logging.error(str(ex))
    return False


def format_link(post):
    srurl = post.subreddit.url
    nsfw = post.subreddit.name.lower() in nsfwreddits or post.subreddit.over18 or post.over_18
    text = u"- [" + srurl[:-1] + "] "
    if nsfw:
        text = text + u"[NSFW] "
    return text + u"[" + post.title + "](" + np(post.permalink) + ")\n"


def changesubdomain(link, sub):
    l = re.sub(r"http[s]?://[a-z]{0,3}\.?[a-z]{0,2}\.?reddit\.com", "", link)
    return "http://" + sub + ".reddit.com" + l


def unnp(link):
    return changesubdomain(link, "www")


def np(link):
    return changesubdomain(link, "np")


def get_cid(url):
    l = re.sub(r"http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.{6,8}/.*/", "", url)
    l = re.sub(r"\?.*", "", l)
    l = re.sub(r"\..*", "", l)
    return "t1_" + l


def get_object(r, url):
    url = unnp(url)
    obj = praw.objects.Submission.from_url(r, url)
    a = re.compile("http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.{6,8}/.*/.{6,8}")

    if a.match(url):
        o = r.get_info(thing_id=get_cid(url))
        if o is None:
            logging.error("Not a comment! (URL: " + url + ")")

        return o
    else:
        return obj


def is_comment(link):
    a = re.compile("http[s]?://[a-z]{0,3}\.?[a-z]{0,2}\.?reddit\.com/r/.{1,20}/comments/.*")
    return a.match(link)


# Loading and saving to permanent storage #

def create_files():
    download_lists(["linked.lst", "linkedsrc.lst", "skipped.lst", "skippedsrc.lst"])


def load_list(file):
    f = open(file, "r")
    data = f.read()
    f.close()
    return data.split()


def save_lists(files, lists):
    i = 0
    for file in files:
        f = open(file, "wb")
        str = ""
        for s in lists[i]:
            str = str + s + " "
        f.write(str)
        f.close()
        i += 1
    upload_lists(files)


def upload_lists(files):
    session = ftplib.FTP(os.environ['FTP_SRV'], os.environ['FTP_USR'], os.environ['FTP_PASS'])
    session.cwd("htdocs")
    for file in files:
        f = open(file, 'rb')
        session.storbinary("STOR " + file, f)
        f.close()
    session.quit()
    logging.info("List saving and uploading completed resuming linking.")


def download_lists(files):
    session = ftplib.FTP(os.environ['FTP_SRV'], os.environ['FTP_USR'], os.environ['FTP_PASS'])
    session.cwd("htdocs")
    for file in files:
        session.retrbinary("RETR " + file, open(file, 'wb').write)
    session.quit()
    logging.info("List downloading completed.")


# End loading and saaving to permanent storage

def handle_http_error(ex):
    global errorcount
    errorcount += 1
    code = ex.response.status_code
    if 500 <= code < 600:  # Sleep for 5 seconds on HTTP 5xx errors.
        time.sleep(5)


def log_crash():
    logging.error("Details: ")
    logging.error(exi())
    logging.error("Unhandled exception. Restarting in " + str(CRASH_TIMER) + " seconds...")
    time.sleep(CRASH_TIMER)
    sys.exit(1)


def exi():
    return traceback.format_exc()


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    root.addHandler(ch)

# #### METHODS USED IN APR 1ST STUFF STARTS HERE #### #

TESTING_APR = False
MAX_TRIES = 5
MAX_POSTS = 20


def ex_post(r):
    now = datetime.datetime.now()
    if (now.day != 1 and now.month != 4) and not TESTING_APR:
        return

    if random.randint(0, 20) != 10 and not TESTING_APR:  # 1 in 50 chance.
        return

    c = get_post(r)
    replies = get_reply_count(c)

    count = 0
    while (c.id in linked or replies > 100) and not TESTING_APR:  # 3 - 100 comment replies seems like a good number.
        if count > MAX_TRIES:
            logging.error("Couldn't find a good post...giving up.")
            return  # give up after a few amount of posts
        c = get_post(r)
        replies = get_reply_count(c)
        count += 1

    linkedpost = get_subreddit_and_post(c.subreddit.display_name.lower())
    formattedpost = format_joke_post(linkedpost[0], linkedpost[1], c.subreddit.display_name.lower() == "circlejerk")
    try:
        c.reply(formattedpost)
        logging.info("Added a joke comment successfully")
    except praw.errors.RateLimitExceeded:
        logging.debug("Can't comment (comment karma is too low)")
    except praw.errors.APIException as e:
        logging.warning(str(e))
    except Exception as e:
        logging.error("Error adding joke comment (CID: " + str(c.id) + ")")
        logging.error(str(e))
    linked.append(linkedpost)  # add our post to the linked post stuff so we don't post to the same comment.


def get_post(r):
    # Subreddits to post to!
    subreddits = ["subredditdrama", "metasubredditdrama", "subredditdramadrama", "circlejerk", "buttcoin", "bestof",
                  "botsrights", "videos", "pics", "gamerghazi", "againstgamergate", "bitcoin", "undelete"]
    subreddit = r.get_subreddit(random.choice(subreddits))

    choice = MAX_POSTS
    for c in subreddit.get_comments(limit=MAX_POSTS):
        if random.randint(0, choice - 1) <= 0 or choice == 0:
            return c
        choice -= 1


def get_subreddit_and_post(tosubreddit):
    subs = []

    srctitles = ["Let's fight the cancer with this post.", "Mods still won't remove this post even when proven wrong",
                 "The cancer speaks!", "Ah, the tumor doesn't give up now?", "The cancer is giving up!",
                 "And if you ask me how I'm feeling, this is why reddit sucks."]
    conspiracytitles = ["In which we prove a govt. coverup is involved", "Reddit never says goodbye to shills",
                        "Don't tell me you're too blind to see"]
    bitcointitles = ["This is actually really good for the bitcoin market", "Could this be the game-changer?",
                     "Merchant adoption, here we come!"]
    srddtitles = ["I'm sure this thread will go well.", "We're no stranger to drama here"]
    mrtitles = ["We're no strangers to this. What if the genders were reversed?",
                "Gotta make you understand. This is not cool."]
    msrdtitles = ["The mods are giving up on this subreddit", "SRD, we know the game and we're going to play it."]

    kiatitles = ["And this is why ethics is important", "Never gonna say goodbye until this sub is fixed."]
    ghazititles = ["Ah, another day, another Gator'rade", "You wouldn't get this from any other guy"]

    subreddits = ["SubredditCancer", "conspiracy", "Bitcoin", "MensRights", "KotakuInAction", "GamerGhazi"]

    if tosubreddit.lower() == "subredditdrama":  # add MSRD and SRDD if the subreddit is SubredditDrama
        subreddits.extend(["MetaSubredditDrama", "SubredditDramaDrama"])

    for s in subreddits:
        if s.lower() == tosubreddit.lower():
            subreddits.remove(s)
            break

    choice = random.choice(subreddits)
    if choice == "KotakuInAction":
        subs.extend([choice, random.choice(kiatitles)])
    elif choice == "SubredditCancer":
        subs.extend([choice, random.choice(srctitles)])
    elif choice == "conspiracy":
        subs.extend([choice, random.choice(conspiracytitles)])
    elif choice == "Bitcoin":
        subs.extend([choice, random.choice(bitcointitles)])
    elif choice == "SubredditDramaDrama":
        subs.extend([choice, random.choice(srddtitles)])
    elif choice == "MetaSubredditDrama":
        subs.extend([choice, random.choice(msrdtitles)])
    elif choice == "MensRights":
        subs.extend([choice, random.choice(mrtitles)])
    elif choice == "GamerGhazi":
        subs.extend([choice, random.choice(ghazititles)])
    else:
        subs.extend(["error", "*Error getting post title*"])

    return subs


def get_reply_count(s):
    if isinstance(s, praw.objects.Comment):
        return len(s.replies)
    else:
        s.replace_more_comments(limit=None, threshold=0)
        flat_comments = praw.helpers.flatten_tree(s.comments)
        return len(flat_comments)
    return -1


def format_joke_post(subreddit, title, isrcirclejerk):
    if isrcirclejerk:
        cmt = CJ_HEADER
    else:
        cmt = HEADER
    cmt = cmt + u"""

{link}

""" + FOOTER
    return cmt.format(link=u"- [/r/" + subreddit + "] [" + title + "](http://bringvictory.com/)")

# #### METHODS USED IN APR 1ST STUFF END HERE #### #

try:
    setup_logging()
    main()
except (AttributeError, NameError, SyntaxError, TypeError, UnboundLocalError) as e:
    logging.error("Crash due to syntactical error!")
    logging.error(exi())
    time.sleep(86400)  # Sleep for 1 day so we don't restart.
except Exception:
    log_crash()