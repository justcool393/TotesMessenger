import logging, os, praw, re, time, sys;

linked = [];
user = os.environ['REDDIT_USER'];
test_reddits = ["TMTest", "Test", "justcool393"];
blacklist = ["anime", "asianamerican", "askhistorians", "askscience", "askreddit", "aww", "chicagosuburbs", "Bitcoin",
             "benfrick", "bmw", "cosplay", "cumberbitches", "d3gf", "deer", "depression", "depthhub", "drinkingdollars",
             "forwardsfromgrandma", "futurology", "geckos", "giraffes", "graphical_design", "grindsmygears",
             "indianfetish", "misc", "mixedbreeds", "news", "newtotf2", "omaha", "petstacking", "pigs",
             "politicaldiscussion", "politics", "programmingcirclejerk", "raerthdev", "rants", "salvia", "science",
             "seiko", "shoplifting", "sketches", "sociopath", "suicidewatch", "talesfromtechsupport", "unitedkingdom"];


def main():
    r = praw.Reddit("Links to reddit posts from other places in reddit", domain="api.reddit.com");
    r.login(user, os.environ['REDDIT_PASS']);
    logging.info("Logged in and started linking");

    check_at = 300;
    last_checked = 0;
    times_zero = 1;

    count = link_subs(r, 100, 15);
    # Check the last 100 posts on startup
    while True:
        if time.time() - last_checked > check_at:
            last_checked = time.time();
            if count == 99999: # Testing
                pass;
            else:
                logging.info("Linked " + str(count) + " in the last " + str((check_at * times_zero) / 60) + " minutes");
                count = 0;
                times_zero = 1;

        count += link_subs(r, 50, 45);


def link_subs(r, count, delay):
    linked_count = 0;
    for submission in r.get_domain_listing('reddit.com', sort='new', limit=count):

        # if submission.subreddit not in test_reddits:  # For testing things
        #     continue;
        #logging.info("Found submission to link (ID: " + submission.id + ")");

        if not is_comment(submission.url):
            continue;

        try:
            linkedp = get_linked(r, submission.url);
        except praw.errors.ClientException:
            logging.error("Link is not a reddit post! (ID: " + submission.id + ")");
            continue;

        if linkedp.id in linked:
            continue;

        if linkedp.subreddit.display_name in blacklist:
            linked.append(linkedp);
            continue;  # Do not comment in blacklisted subreddits (reddit rules)

        linkedp.replace_more_comments(limit=None, threshold=0);
        # TODO: Make the bot edit it's comment on other links.
        commented = check_commented(linkedp);

        if commented:
            linked.append(linkedp);
            continue;

        # End to do
        post(r, linkedp, submission);  # Hope it works
        linked_count += 1;

    time.sleep(delay);
    return linked_count;


def get_linked(r, link):
    return r.get_submission(link);


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


def post(r, s, post):
    comment = u"""
This post has been linked to from another place on reddit. ([Info](/r/TotesMessenger/wiki/))

{link}""";
    try:
        s.add_comment(comment.format(link=format_link(post)));
    except praw.errors.RateLimitExceeded:
        logging.debug("Cannot comment on post (comment karma is too low)");
    except Exception as e:
        logging.error("Exception on comment add! (Submission ID: " + str(s.id) + ")");
        logging.error(str(e));


def format_link(post):
    link = post.url;
    return u"- [" + post.subreddit.url + "] " + u"[" + post.title + "](" + np(link) + ")\n";


def np(link):
    return re.sub(r"//[a-z]{0,3}\.?reddit", "//np.reddit", link);


def is_comment(link):
    a = re.compile("http[s]?://[a-z]{0,3}\.?reddit\.com/r/.{1,20}/comments/.*");
    return a.match(link);


def log_crash(e):
    logging.error("Error occurred in the bot; restarting in 15 seconds...");
    logging.error("Details: " + str(e));
    time.sleep(15);
    sys.exit(1);  # Signal to the host that we crashed


def setup_logging():
    root = logging.getLogger();
    root.setLevel(logging.INFO);

    ch = logging.StreamHandler(sys.stdout);
    ch.setLevel(logging.INFO);

    root.addHandler(ch);


try:
    setup_logging();
    main();
except (NameError, SyntaxError) as e:
    logging.error(str(e));
    time.sleep(86400);  # Sleep for 1 day so we don't restart.
except Exception as e:
    log_crash(e);