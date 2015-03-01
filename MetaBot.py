import logging, os, praw, re, time, traceback, sys, urllib2;

linked = [];
linkedsrc = [];

brigademsg = u"""^Do ^not ^vote ^or ^comment ^in ^linked ^threads. ^\([Info](/r/TotesMessenger/wiki/) ^| ^[Contact](/message/compose/?to=\/r\/TMTest))""";

user = os.environ['REDDIT_USER'];
blacklist = ["anime", "asianamerican", "askhistorians", "askscience", "aww", "benfrick", "bmw", "chicagosuburbs",
             "cosplay", "cumberbitches", "d3gf", "deer", "depression", "depthhub", "drinkingdollars",
             "forwardsfromgrandma", "futurology", "geckos", "giraffes", "graphical_design", "grindsmygears",
             "indianfetish", "misc", "mixedbreeds", "news", "newtotf2", "omaha", "petstacking", "pigs",
             "politicaldiscussion", "politics", "programmingcirclejerk", "raerthdev", "rants", "salvia", "science",
             "seiko", "shoplifting", "sketches", "sociopath", "suicidewatch", "talesfromtechsupport", "unitedkingdom"];
# Do not edit

srcblacklist = ["depression", "lifeafternarcissists", "managedbynarcissists", "moderationlog", "raisedbynarcissists",
                "rbnathome", "rbnbookclub", "rbnchildcare", "rbnfavors", "rbngames", "rbnlifeskills", "rbnmovienight",
                "rbnrelationships", "rbnspouses", "suicidewatch", "switcharoo", "trolledbynarcissists", "unremovable",
                "politic", "mlplite", "risingthreads", "uncensorship"];

banned = ["reddit.com", "minecraft", "adviceanimals", "askreddit", "worldnews", "femradebates", "pcmasterrace",
          "purplepilldebate", "slrep"];

blockedusers = ["amprobablypooping", "evilrising", "frontpagewatch", "frontpagewatchmirror", "moon-done", "politicbot",
                "rising_threads_bot", "removal_rover"];
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

        if submission.subreddit.display_name.lower() not in test_reddits:  # For testing things
            continue;

        try:
            link_submission(r, submission);
        except Exception as e:
            logging.error(exi(e));
        linked_count += 1;
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

        logging.error(exi(e));
        return;
    except Exception as e:
        logging.error("Could not get comment!");
        logging.error(exi(e));

    lid = linkedp.id;

    if submission.author is None:
        linked.append(lid);  # This is already deleted. Don't reply.
        return;

    if submission.author.name.lower() in blockedusers:
        linked.append(lid);  # Block undelete, mod log and scraper bots.
        return;

    if linkedp.subreddit.display_name.lower() in blacklist:
        linked.append(lid);  # Do not comment in blacklisted subreddits (reddit rules)
        return;

    if linkedp.subreddit.display_name.lower() in banned:
        linked.append(lid);  # Do not attempt to comment in banned/archived subreddits
        return;

    if submission.subreddit.display_name.lower() in srcblacklist:
        linked.append(lid);  # Do not comment if it comes from blocked sources (NBD, SW, etc..)
        return;

    if lid in linked:
        if submission.id not in linkedsrc:
            success = edit_post(get_bot_comment(linkedp), submission);
            if success:
                linkedsrc.append(submission.id);
                return;
            else:
                return;

        if isinstance(linkedp, praw.objects.Comment):
            if check_commment_replies(linkedp):
                linked.append(lid);
                linkedsrc.append(submission.id);
                return;
            else:
                comment(linkedp, submission);
        elif isinstance(linkedp, praw.objects.Submission):
            linkedp.replace_more_comments(limit=None, threshold=0);
            if check_commented(linkedp):
                linkedsrc.append(submission.id);
                linked.append(lid);
                return;
            else:
                post(linkedp, submission);
        else:
            logging.error("Not a Comment or Submission! (ID: " + id + ")");

        linked.append(lid);


def edit_post(totessubmission, original):
    if totessubmission is None:
        return False;
    text = re.sub("\^Do.{1,}", "", totessubmission.body);
    text = text + format_link(original) + u"""


    """ + brigademsg;
    totessubmission.edit(text);
    return True;


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


def get_bot_comment(s):
    if isinstance(s, praw.objects.Comment):
        for c in s.replies:
            if c.author is None:
                continue;
            if c.author.name == user:
                return c;
    else:
        flat_comments = praw.helpers.flatten_tree(s.comments);
        for c in flat_comments:
            if c.author is None:
                continue;
            if c.author.name == user:
                return c;
    return None;


def format_comment(original):
    cmt = u"""
This thread has been linked to from another place on reddit.

{link}

""" + brigademsg;
    return cmt.format(link=format_link(original));


def post(s, original):
    try:
        s.add_comment(format_comment(original));
    except praw.errors.RateLimitExceeded:
        logging.debug("Cannot comment on post (comment karma is too low)");
    except praw.errors.APIException as e:
        logging.warning(str(e));
    except Exception as e:
        logging.error("Exception on comment add! (Submission ID: " + str(s.id) + ")");
        logging.error(exi(e));


def comment(c, original):
    try:
        c.reply(format_comment(original));
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

        return o;  # Get the comment (and hopefully not the link)
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
except (AttributeError, NameError, SyntaxError, TypeError) as e:
    logging.error(exi(e));
    time.sleep(86400);  # Sleep for 1 day so we don't restart.
    # except Exception as e:
    #	log_crash(e);