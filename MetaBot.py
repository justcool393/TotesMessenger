import logging, os, praw, re, time, traceback, sys, urllib2;

linked = [];
linkedsrc = [];
skipped = [];
skippedsrc = [];

ARCHIVE_TIME = 15778463; # currently 6 months (in seconds)
CJ_HEADER = u"""This dank meme has been linked to from another place on le reddit.""";
HEADER = u"""This thread has been linked to from another place on reddit.""";
FOOTER = u"""[](#footer)*^If ^you ^follow ^any ^of ^the ^above ^links, ^respect ^the ^rules ^of ^reddit ^and ^don't ^vote. ^\([Info](/r/TotesMessenger/wiki/) ^/ ^[Contact](/message/compose/?to=\/r\/TotesMessenger))* [](#bot)""";

user = os.environ['REDDIT_USER'];
blacklist = ["anime", "asianamerican", "askhistorians", "askscience", "aww", "benfrick", "bmw", "chicagosuburbs",
             "cosplay", "cumberbitches", "d3gf", "deer", "depression", "depthhub", "drinkingdollars",
             "forwardsfromgrandma", "futurology", "geckos", "giraffes", "graphical_design", "grindsmygears",
             "indianfetish", "misc", "mixedbreeds", "news", "newtotf2", "omaha", "petstacking", "pigs",
             "politicaldiscussion", "programmingcirclejerk", "raerthdev", "rants", "salvia", "science",
             "seiko", "shoplifting", "sketches", "sociopath", "suicidewatch", "talesfromtechsupport", "unitedkingdom"];
# Do not edit

srcblacklist = ["depression", "lifeafternarcissists", "managedbynarcissists", "moderationlog", "raisedbynarcissists",
                "rbnathome", "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames", "rbnlifeskills", "rbnmovienight",
                "rbnrelationships", "rbnspouses", "suicidewatch", "switcharoo", "switcheroo", "trolledbynarcissists",
                "unremovable", "politic", "mlplite", "risingthreads", "uncensorship", "leagueofriot", "benlargefanclub",
                "fitnesscirclejerk", "taiwancirclejerk"];

banned = ["reddit.com", "minecraft", "adviceanimals", "askreddit", "worldnews", "femradebates", "pcmasterrace",
          "purplepilldebate", "slrep", "funny", "theredpill", "personalfinance", "india", "lifehacks", "kotakuinaction",
          "askmen", "smashbros", "android", "neutralpolitics", "dota2", "wet_shavers", "dogecoin", "askphilosophy",
          "suits", "japanlife", "photography", "hiphopheads", "apple", "lifeprotips", "nba"];

blockedusers = ["amprobablypooping", "evilrising", "frontpagewatch", "frontpagewatchmirror", "moon-done", "politicbot",
                "rising_threads_bot", "removal_rover", "know_your_shit", "drugtaker", "nedsc"];

# metabots = [user, "totesmessenger", "totes_meta_bot", "meta_bot", "meta_bot2", "originallinkbot"];

# Ban list:
# drugtaker - Meta bot NSFW marking evasion
# NedSc     - By request

nsfwreddits = ["srsshillwatch", "srsshillswatch", "srshillswatch", "srshillwatch", "gonewild"];

test_reddits = ["justcool393", "tmtest", "totesmessenger"];



def main():
    global linked;
    global linkedsrc;
    global skipped;
    global skippedsrc;
    create_files();

    linked = load_list("linked.lst");
    linkedsrc = load_list("linkedsrc.lst");
    skipped = load_list("skipped.lst");
    skippedsrc = load_list("skippedsrc.lst");

    add_linkedsrc();

    r = praw.Reddit("Links to reddit posts from other places in reddit", domain="api.reddit.com", log_requests=0);
    r.login(user, os.environ['REDDIT_PASS']);
    logging.info("Logged in to reddit...");

    check_at = 3600;
    save_at = 60;
    last_logged = 0;
    last_saved = 0;
    times_zero = 1;

    count = link_subs(r, 100, 120); # Check the last 100 posts on startup
    while True:
        if time.time() >= (last_saved + save_at):
            last_saved = time.time();
            save_list("linked.lst", linked);
            save_list("linkedsrc.lst", linkedsrc);
            save_list("skipped.lst", skipped);
            save_list("skippedsrc.lst", skippedsrc);

        if time.time() >= (last_logged + check_at):

            last_logged = time.time();
            if count == 0:
                times_zero += 1;
            else:
                logging.info("Linked " + str(count) + " in the last " + str((check_at * times_zero) / 60 / 60) + " hour(s)");
                count = 0;
                times_zero = 1;
        count += link_subs(r, 25, 60);

def add_linkedsrc():
    for c in r.get_redditor(user).get_comments(sort='new'):
        parent = parent_obj(c);
        if parent is None:
            return;
        linkedsrc.append(parent.id);
        pass;

def parent_obj(obj):
    assert type(obj) == praw.objects.Comment;
    if obj.is_root:
        return obj.submission;
    return self.rh.get_info(thing_id=obj.parent_id);

def create_files():
    f = open("linked.lst", "a");
    f.close();
    f = open("linkedsrc.lst", "a");
    f.close();
    f = open("skipped.lst", "a");
    f.close();
    f = open("skippedsrc.lst", "a");
    f.close();

def link_subs(r, count, delay):
    linked_count = 0;
    for submission in r.get_domain_listing('reddit.com', sort='new', limit=count):

        #if submission.subreddit.display_name.lower() not in test_reddits:  # For testing things
        #    continue;

        try:
            if link_submission(r, submission):
                linked_count += 1;
        except Exception:
            logging.error(exi());
        time.sleep(3);

    time.sleep(delay);
    return linked_count;


def link_submission(r, submission):
    url = submission.url;
    if not is_comment(url):
        return;
    linkedp = None;
    try:
        linkedp = get_object(r, url);
    except praw.errors.ClientException as e:
        logging.error("Link is not a reddit post (id: " + submission.id + ")");
        logging.error(exi());
        return;
    except Exception:
        logging.error("Could not get comment!");
        logging.error(exi());

    if linkedp is None:
        return;

    lid = linkedp.id;
    sid = submission.id;

    # Skip conditions: Already deleted, undelete/scraper/mod log bots, blacklisted, banned/archived,
    # archived, in source blacklist

    if linkedp is None or linkedp.subreddit is None:
        skipped.append(lid);
        return False;

    srlower = linkedp.subreddit.display_name.lower();

    if linkedp.author is None or srlower in blacklist or srlower in banned or linkedp.created < (time.time() - ARCHIVE_TIME):
        skipped.append(lid);
        return False;

    if submission.subreddit.display_name.lower() in srcblacklist or submission.author is None:
        skippedsrc.append(sid);
        return False;

    if submission.author.name.lower() in blockedusers:
        skippedsrc.append(sid);

    if lid in skipped or sid in skippedsrc:
        return False;

    if sid in linkedsrc:
        return False;


    if lid in linked or check_commmented(linkedp) or get_bot_comment(linkedp) is not None:
        success = edit_post(get_bot_comment(linkedp), submission);
        linkedsrc.append(sid);
        if not lid in linked:
            linked.append(lid);
        return success;

    if isinstance(linkedp, praw.objects.Comment):
        linked.append(lid);
        linkedsrc.append(sid);
        comment(linkedp, submission, srlower == "circlejerk");
    elif isinstance(linkedp, praw.objects.Submission):
        post(linkedp, submission, srlower == "circlejerk");
    else:
        logging.error("Not a Comment or Submission! (ID: " + id + ")");
        return False;

    linked.append(lid);
    linkedsrc.append(sid);
    return True;


def edit_post(totessubmission, original):
    if totessubmission is None:
        return False;
    text = re.sub("\[\]\(#footer\).{1,}", "", totessubmission.body); # sub. invisible link for easier footer changes
    text = re.sub("\*\^If.{1,}", "", text);
    text = re.sub("\^Please.{1,}", "", text); # substitute old footer as well
    text = re.sub("Do not vote.{1,}", "", text); # substitute original footer as well
    text = text + format_link(original) + u"""


""" + FOOTER;
    totessubmission.edit(text);
    return True;


def get_comment(r, s):
    return get_linked(r, s).comments[0];


def get_linked(r, link):
    return r.get_submission(link);


def check_commmented(c):
    if isinstance(c, praw.objects.Comment):
        comments = c.replies;
    elif isinstance(c, praw.objects.Submission):
        c.replace_more_comments(limit=None, threshold=0);
        comments = praw.helpers.flatten_tree(c.comments);

    for co in comments:
        if co.author is None:
            continue;
        if co.author.name.lower() == user.lower():
            return True;
    return False;


def get_bot_comment(s):
    if isinstance(s, praw.objects.Comment):
        for c in s.replies:
            if c.author is None:
                continue;
            if c.author.name.lower() == user.lower():
                return c;
    else:
        s.replace_more_comments(limit=None, threshold=0);
        flat_comments = praw.helpers.flatten_tree(s.comments);
        for c in flat_comments:
            if c.author is None:
                continue;
            if c.author.name.lower() == user.lower():
                return c;
    return None;


def format_comment(original, isrcirclejerk):
    if isrcirclejerk:
        cmt = CJ_HEADER;
    else:
        cmt = HEADER;
    cmt = cmt + u"""

{link}

""" + FOOTER;

    return cmt.format(link=format_link(original));


def post(s, original, isrcirclejerk):
    try:
        s.add_comment(format_comment(original, isrcirclejerk));
    except praw.errors.RateLimitExceeded:
        logging.debug("Can't comment (comment karma is too low)");
    except praw.errors.APIException as e:
        logging.warning(str(e));
    except Exception:
        logging.error("Error adding comment (SID: " + str(s.id) + ")");
        logging.error(exi());


def comment(c, original, isrcirclejerk):
    try:
        c.reply(format_comment(original, isrcirclejerk));
    except praw.errors.RateLimitExceeded:
        logging.debug("Can't comment (comment karma is too low)");
    except praw.errors.APIException as e:
        logging.warning(str(e));
    except Exception:
        logging.error("Error adding comment (CID: " + str(c.id) + ")");
        logging.error(str(e));


def format_link(post):
    srurl = post.subreddit.url;
    nsfw = post.subreddit.name.lower() in nsfwreddits or post.subreddit.over18 or post.over_18;
    text = u"- [" + srurl[:-1] + "] ";
    if nsfw:
        text = text + u"[NSFW] ";
    return text + u"[" + post.title + "](" + np(post.permalink) + ")\n";

def changesubdomain(link, sub):
    l = re.sub(r"http[s]?://[a-z]{0,3}\.?reddit\.com", "", link);
    return "http://" + sub + ".reddit.com" + l;

def unnp(link):
    return changesubdomain(link, "www");


def np(link):
    return changesubdomain(link, "np");


def get_cid(url):
    l = re.sub(r"http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.{6,8}/.*/", "", url);
    l = re.sub(r"\?.*", "", l);
    l = re.sub(r"\..*", "", l);
    return "t1_" + l;


def get_object(r, url):
    obj = praw.objects.Submission.from_url(r, unnp(url));
    a = re.compile("http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.{6,8}/.*/.{6,8}");

    if a.match(url):
        url = unnp(url);
        o = r.get_info(thing_id=get_cid(url));
        if o is None:
            raise Exception("Comment is none! (URL: " + url + ")");

        return o;
    else:
        return obj;


def is_comment(link):
    a = re.compile("http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.*");
    return a.match(link);


def load_list(file):
    f = open(file, "r");
    data = f.read();
    f.close();
    return data.split();

def save_list(file, list):
    f = open(file, "wb");
    str = "";
    for s in list:
        str = str + s + " ";
    f.write(str);
    f.close();


def log_crash():
    logging.error("Error occurred in the bot; restarting in 15 seconds...");
    logging.error("Details: ");
    logging.error(exi());
    time.sleep(15);
    sys.exit(1);


def exi():
    return traceback.format_exc();


def setup_logging():
    root = logging.getLogger();
    root.setLevel(logging.INFO);
    logging.getLogger("requests").setLevel(logging.WARNING);
    ch = logging.StreamHandler(sys.stdout);
    ch.setLevel(logging.INFO);

    root.addHandler(ch);


try:
    setup_logging();
    time.sleep(15*60); # sleep for 15 minutes because I don't trust my bot
    main();
except (AttributeError, NameError, SyntaxError, TypeError) as e:
    logging.error(exi());
    time.sleep(86400);  # Sleep for 1 day so we don't restart.
except Exception:
    log_crash();