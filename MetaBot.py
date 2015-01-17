import logging, os, praw, re, time, traceback, sys;

linked = [];

user = os.environ['REDDIT_USER'];
blacklist = ["anime", "asianamerican", "askhistorians", "askscience", "aww", "benfrick", "bmw", "chicagosuburbs",
             "cosplay", "cumberbitches", "d3gf", "deer", "depression", "depthhub", "drinkingdollars",
             "forwardsfromgrandma", "futurology", "geckos", "giraffes", "graphical_design", "grindsmygears",
             "indianfetish", "lifeafternarcissists", "managedbynarcissists", "misc", "mixedbreeds", "news", "newtotf2",
             "omaha", "petstacking", "pigs", "politicaldiscussion", "politics", "programmingcirclejerk", "raerthdev",
             "raisedbynarcissists", "rants", "rbnathome", "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames",
             "rbnlifeskills", "rbnmovienight", "rbnrelationships", "rbnspouses", "salvia", "science", "seiko",
             "shoplifting", "sketches", "sociopath", "suicidewatch", "talesfromtechsupport", "trolledbynarcissists",
             "unitedkingdom"];

srcblacklist = ["depression", "lifeafternarcissists", "managedbynarcissists", "moderationlog", "raisedbynarcissists",
                "rbnathome", "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames", "rbnlifeskills", "rbnmovienight",
                "rbnrelationships", "rbnspouses", "suicidewatch", "trolledbynarcissists", "unremovable", "politic",
                "mlplite"];

banned = ["reddit.com", "minecraft", "adviceanimals", "askreddit", "worldnews", "femradebates"];

blockedusers = ["amprobablypooping", "evilrising", "frontpagewatch", "frontpagewatchmirror", "moon-done", "politicbot",
                "removal_rover"];
# Scraper and undelete are blocked from triggering the meta bot.

test_reddits = ["justcool393", "tmtest", "totesmessenger"];


def main():
    r = praw.Reddit("Links to reddit posts from other places in reddit", domain="api.reddit.com", log_requests=0);
    r.login(user, os.environ['REDDIT_PASS']);
    logging.info("Logged in and started linking");

    check_at = 3600;
    last_checked = 0;
    times_zero = 1;

    count = link_subs(r, 100, 60);
    # Check the last 100 posts on startup
    while True:
        if time.time() - last_checked > check_at:
            last_checked = time.time();
            if count == 0:
                times_zero += 1;
            else:
                logging.info("Linked " + str(count) + " in the last " + str((check_at * times_zero) / 60) + " minutes");
                count = 0;
                times_zero = 1;

        count += link_subs(r, 25, 60);


def link_subs(r, count, delay):
    linked_count = 0;
    for submission in r.get_domain_listing('reddit.com', sort='new', limit=count):

        # if submission.subreddit.display_name.lower() not in test_reddits:  # For testing things
        #     continue;

        url = submission.url;
        if not is_comment(url):
            continue;

        try:
            linkedp = get_object(r, url);
        except praw.errors.ClientException as e:
            logging.error("Link is not a reddit post (id: " + submission.id + ")");
            logging.error(exi(e));
            continue;
        lid = linkedp.id;

        if submission.author is None:
            linked.append(lid); # This is already deleted. Don't reply.
            continue;

        if submission.author.name.lower() in blockedusers:
            linked.append(lid); # Block undelete, mod log and scraper bots.
            continue;

        if linkedp.subreddit.display_name.lower() in blacklist:
            linked.append(lid); # Do not comment in blacklisted subreddits (reddit rules)
            continue;

        if linkedp.subreddit.display_name.lower() in banned:
            linked.append(lid); # Do not attempt to comment in banned/archived subreddits
            continue;

        if submission.subreddit.display_name.lower() in srcblacklist:
            linked.append(lid); # Do not comment if it comes from blocked sources (NBD, SW, etc..)
            continue;

        if lid in linked:
            continue;

        # TODO: Make the bot edit it's comment on other links.

        if isinstance(linkedp, praw.objects.Comment):
            if not check_commment_replies(linkedp):
                comment(r, linkedp, submission);
        elif isinstance(linkedp, praw.objects.Submission):
            linkedp.replace_more_comments(limit=None, threshold=0);
            commented = check_commented(linkedp);
            if not commented:
                post(r, linkedp, submission);
        else:
            logging.error("Not a Comment or Submission! (ID: " + id + ")");

        linked.append(lid);
        linked_count += 1;
        time.sleep(10);

    time.sleep(delay);
    return linked_count;


def link_to_comment(r, url):
    logging.error("Not implemented!");
    return False;
    # c = get_comment(r, url);
    # if c.id in linked:
    #     linked.append(c);
    #     return False;
    # if c.subreddit.display_name.lower() in blacklist:
    #     linked.append(c);
    #     return False;
    # if c.subreddit.display_name.lower() in srcblacklist:
    #     linked.append(c);
    #     return False;


def get_comment(r, s):
    return get_linked(r, s).comments[0];


def get_linked(r, link):
    return r.get_submission(link);

def check_commment_replies(c):
    for co in c.replies:
        if co.author is None:
            continue;
        if co.author.name == user:
            return True;
        if co.author.name == "totes_meta_bot":
            return True;
    return False;

def check_commented(s):
    flat_comments = praw.helpers.flatten_tree(s.comments);
    for c in flat_comments:
        if c.author is None:
            continue;
        if c.author.name == user:
            return True;
        if c.author.name == "totes_meta_bot":
            return True;
    return False;

def format_comment(r, original):
    cmt = u"""
This thread has been linked to from another place on reddit.

{link}

^Do ^not ^vote ^or ^comment ^in ^linked ^threads. ^\([Info](/r/TotesMessenger/wiki/) ^| ^[Contact](/message/compose/?to=\/r\/TMTest))""";
    return cmt.format(link=format_link(original));


def post(r, s, original):
    try:
        s.add_comment(format_comment(r, original));
    except praw.errors.RateLimitExceeded:
        logging.debug("Cannot comment on post (comment karma is too low)");
    except Exception as e:
        logging.error("Exception on comment add! (Submission ID: " + str(s.id) + ")");
        logging.error(exi(e));


def comment(r, c, original):
    try:
        c.reply(format_comment(r, original));
    except praw.errors.RateLimitExceeded:
        logging.debug("Cannot comment (CK is too low)");
    except Exception as e:
        logging.error("Exception on comment add! (SID: " + str(c.id) + ")");
        logging.error(str(e));


def format_link(post):
    srurl = post.subreddit.url;
    return u"- [" + srurl[:-1] + "] " + u"[" + post.title + "](" + np(post.permalink) + ")\n";

def unnp(link):
    l = re.sub(r"http[s]?://[a-z]{0,3}\.?reddit\.com", "", link);
    return "http://www.reddit.com" + l;

def np(link):
    l = re.sub(r"http[s]?://[a-z]{0,3}\.?reddit\.com", "", link);
    return "http://np.reddit.com" + l;
    # return re.sub(r"//[a-z]{0,3}\.?reddit", "//np.reddit", link);

def get_object(r, url):
    obj = praw.objects.Submission.from_url(r, unnp(url));
    a = re.compile("http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.{6,8}/.*/.{6,8}");

    if a.match(url):
        return r.get_info(url)[1]; # Get the comment (and hopefully not the link)
    else:
        return obj;

def is_comment(link):
    a = re.compile("http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.*");
    return a.match(link);


def log_crash(e):
    logging.error("Error occurred in the bot; restarting in 15 seconds...");
    logging.error("Details: ");
    logging.error(exi(e));
    time.sleep(15);
    sys.exit(1);  # Signal to the host that we crashed

def exi(ex):
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
    main();
except (NameError, SyntaxError, TypeError) as e:
    logging.error(exi(e));
    time.sleep(86400);  # Sleep for 1 day so we don't restart.
#except Exception as e:
#    log_crash(e);