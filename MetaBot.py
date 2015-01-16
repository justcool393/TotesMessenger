import logging, os, praw, re, time, sys;

archived = [];
user = os.environ['REDDIT_USER'];


def main():
    r = praw.Reddit("Links to reddit posts from other places in reddit", domain="api.reddit.com");
    r.login(user, os.environ['REDDIT_PASS']);
    logging.info("Logged in and started post archiving.");
    s = r.get_subreddit('justcool393');

    check_at = 3600;
    last_checked = 0;
    times_zero = 1;

    linked = archive_submissions(r, s, 100, 15);
    # Check the last 100 posts on startup
    while True:
        if time.time() - last_checked > check_at:
            last_checked = time.time();
            if linked == 0:
                pass;
            else:
                logging.info("Linked " + str(linked) + " in the last " + str((check_at * times_zero) / 60) + " minutes");
                linked = 0;
                times_zero = 1;

        linked += archive_submissions(r, s, 50, 120);


def archive_submissions(r, s, count, delay):
    archived_posts = 0;
    for submission in s.get_new(limit=count):

        submission.replace_more_comments(limit=None, threshold=0);

        if submission.id in archived:
            continue;

        commented = check_commented(submission);

        if commented:
            archived.append(submission.id);
            continue;

        try:
            archive_and_post(r, submission);
            archived_posts += 1;
        except UnicodeEncodeError:
            logging.error("Unable to archive post (UnicodeEncodeError, Submission ID: " + submission.id + ")");

    time.sleep(delay);
    return archived_posts;

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

def archive_and_post(r, s):
    post(r, s, arch_post);


def post(r, s, link):
    comment = """
This post has been linked to from another place on reddit. ([Info](/r/)

{{link}}""";
    try:
        s.add_comment(comment.format(link=''));
    except Exception as e:
        logging.error("Exception on comment add! (Submission ID: " + str(s.id) + ")");
        logging.error(str(e));
        pass;

def format_link(post):
    link = post.url;
    return "- [" + get_subreddit(link) + "] " + "[" + post.title + "](" + np(link) + ")\n";

def np(link):
    return re.sub(r"//[a-z]{0,3}\.?reddit", "//np.reddit", link);

def get_subreddit(link):
    reg = re.sub("http[s]?://.{0,}reddit.com", "", link);
    return re.sub("\/c.*", "", reg);

def log_crash(e):
    logging.error("Error occurred in the bot; restarting in 15 seconds...");
    logging.error("Details: " + str(e));
    time.sleep(15);
    sys.exit(1); # Signal to the host that we crashed


try:
    main();
except (NameError, SyntaxError) as e:
    logging.error(str(e));
    time.sleep(86400); # Sleep for 1 day so we don't restart.
except Exception as e:
    log_crash(e);