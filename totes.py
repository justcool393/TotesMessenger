import ftplib
import logging
import praw
import os
import re
import sys
import sqlite3
import time
import traceback

# Requests' exceptions live in .exceptions and are called errors.
from requests.exceptions import ConnectionError, HTTPError
# Praw's exceptions live in .errors and are called exceptions.
from praw.errors import APIException, ClientException, RateLimitExceeded

# Internationalization stuff
from i18n import TranslationException, Translation, I18n, DEFAULT_LANG

from urllib.parse import urlparse
from datetime import datetime, timezone

# Settings
from settings import *

USER_AGENT = 'TotesMessenger v0.5 by /u/justcool393 and /u/cmd-t'
DOMAIN = 'api.reddit.com'

loglevel = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(level=loglevel,
                    format='[%(asctime)s] [%(levelname)s] %(message)s')

log = logging.getLogger('totes')
logging.getLogger('requests').setLevel(loglevel)


db = sqlite3.connect("totes.sqlite3")
cur = db.cursor()

r = praw.Reddit(USER_AGENT, domain=DOMAIN)

i18n = I18n()

PATH_REGEX = re.compile(r'^/r/([^/]+)/comments/([a-z0-9]{6,8})(/[^/]+/([a-z0-9]{6,8}))?')


def log_error(e):
    log.error("Unexpected {}:\n{}".format(e.__class__.__name__,
                                          traceback.format_exc()))


def np(url):
    """
    Transforms a reddit link into a no participation URL (which in some
    subreddits hides voting arrows, to help prevent administrator shadowbans.
    :param url: URL to transform
    :return: A no participation (NP) link
    """
    url = urlparse(url)
    return "https://np.reddit.com{}".format(url.path)


def escape_title(title):
    """
    Escapes special characters in titles. Markdown uses some characters like
    * and _ for things such as links to make sure people can't bold titles
    and such.
    :param title: Title to escape
    :return: A escaped title
    """
    escaped = "\\*[]^`_~/"
    for s in escaped:
        title = title.replace(s, "\\" + s)
    return title


def source_exists(id):
    cur.execute("SELECT 1 FROM sources WHERE id=? LIMIT 1", (id,))
    return True if cur.fetchone() else False


def link_exists(id):
    cur.execute("SELECT 1 FROM links WHERE id=? LIMIT 1", (id,))
    return True if cur.fetchone() else False


class RecoverableException(Exception):
    pass


class SubmissionNotFound(RecoverableException):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "Could not find submission {}".format(id)


class NotAComment(RecoverableException):
    pass


RECOVERABLE_EXC = (RecoverableException,
                   ConnectionError,
                   HTTPError,
                   APIException,
                   ClientException,
                   RateLimitExceeded)


class Source:
    """
    Comment or thread that has been linked to from somewhere else on reddit.
    """
    def __init__(self, url):
        self.path = urlparse(url.lower()).path
        self.id, self.subreddit = self._parse_path()

        self._submission = None
        self.author = None
        self.title = None
        self.reply = None
        self.skip = False
        self.is_new = True

    def __eq__(self, other):
        if isinstance(other, Source):
            return self.id == other.id

        return False

    def __hash__(self):
        return hash(self.id)

    @property
    def submission(self):
        if self._submission:
            return self._submission

        self._submission = r.get_info(thing_id=self.id)

        if not self._submission:
            raise SubmissionNotFound(self.id)

        return self._submission

    @property
    def is_comment(self):
        return self.id.startswith('t1')

    @property
    def is_post(self):
        return self.id.startswith('t3')

    def check_skip(self):
        if self.skip:
            return True

        cur.execute(
            "SELECT * FROM users WHERE name = ? AND skip_source = ? LIMIT 1",
            (self.author, True))

        if cur.fetchone():
            self.skip = True
            return True

        cur.execute(
            "SELECT * FROM subreddits WHERE name = ? AND skip_source = ? LIMIT 1",
            (self.subreddit, True))

        if cur.fetchone():
            self.skip = True
            return True

        if self.submission.archived:  # skip if source is archived
            self.skip = True
            return True

        return False

    def save(self):
        if source_exists(self.id):
            cur.execute("""
            UPDATE sources SET
            reply=?,
            subreddit=?,
            author=?,
            title=?,
            skip=?
            WHERE id=?
            """, (self.reply, self.subreddit, self.author, self.title,
                  self.skip, self.id))
        else:
            cur.execute("""
            INSERT INTO sources (id, reply, subreddit, author, title, skip)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (self.id, self.reply, self.subreddit, self.author, self.title,
                  self.skip))

        # Maybe commit?
        db.commit()

    def load(self):
        """
        Populate attributes from database and fetch corresponding submission.
        """
        cur.execute("""
        SELECT id, reply, subreddit, author, title, skip FROM sources
        WHERE id=? LIMIT 1
        """, (self.id,))

        source = cur.fetchone()

        if source:
            self.id, self.reply, self.subreddit, self.author, self.title, self.skip = source
            self.is_new = False
            return  # Return early cuz we don't need to perform an api call.

        if not self.author and self.submission.author:
            self.author = self.submission.author.name.lower()
        else:
            self.author = '[deleted]'

        if hasattr(self.submission, 'title'):
            self.title = self.submission.title
        else:
            self.title = '[comment]'

    def _parse_path(self):
        # Comments have path /r/sub/comments/xxx/title/xxx/
        # Posts have path /r/sub/comments/xxx/title/
        # TODO: Link when "/r/sub/" is not included in path
        match = PATH_REGEX.match(self.path)

        if match:
            subreddit, post, _, comment = match.groups()
        else:
            raise NotAComment("Source {} is not a comment or post.".format(self.path))

        if comment:
            id = "t1_{}".format(comment)
        else:
            id = "t3_{}".format(post)

        return id, subreddit


class Link:
    """
    Thread that links to another place on reddit
    """
    def __init__(self, submission, source):
        self.submission = submission
        self.id = submission.name
        # self.subreddit = submission.subreddit.display_name
        # TODO: Change to subreddit.display_name
        self.subreddit = submission.subreddit.display_name.lower()
        self.skip = False

        if submission.author:
            self.author = submission.author.name.lower()
        else:
            self.author = '[deleted]'
            self.skip = True  # skip the link if the user has deleted it

        self.title = submission.title
        self.permalink = submission.permalink
        self.source = source
        self.is_new = True

    def check_skip(self):
        """
        Checks whether we should skip this link. This uses an all-lowercase
        version of the subreddit name, which is different than what is used
        in the post (the mixed case name). For example, in the database,
        the name would be "TotesMessenger", but the subreddits database table
        uses the lowercase name, so that is what will be used.

        The username will also be converted to lowercase and stored as such
        as this is only used internally.
        :return: A boolean value indicating whether we should skip this link
        """
        if self.skip:
            return True

        if self.source.subreddit == "subredditsimulator":
            if self.subreddit != "subredditsimmeta":
                self.skip = True
                return True

        cur.execute(
            "SELECT * FROM users WHERE name = ? AND skip_link = ? LIMIT 1",
            (self.author, True))

        if cur.fetchone():
            self.skip = True
            return True

        # TODO: convert database

        cur.execute(
            "SELECT * FROM subreddits WHERE name = ? AND skip_link = ? LIMIT 1",
            (self.subreddit.lower(), True))

        if cur.fetchone():
            self.skip = True
            return True

        return False

    def save(self):
        if link_exists(self.id):
            cur.execute("""
            UPDATE links SET
            source=?,
            permalink=?,
            subreddit=?,
            skip=?,
            author=?,
            title=?
            WHERE id=?
            """, (self.source, self.permalink, self.subreddit, self.skip,
                  self.author, self.title, self.id))
        else:
            cur.execute("""
            INSERT INTO links (id, source, permalink, subreddit, skip, author, title)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.id, self.source, self.permalink, self.subreddit,
                  self.skip, self.author, self.title))

        # Maybe commit less often?
        db.commit()

    def load(self):
        """
        Populate attributes from database and fetch corresponding submission.
        """
        cur.execute("""
        SELECT id, source, permalink, subreddit, skip, author, title FROM links
        WHERE id=? LIMIT 1
        """, (self.id,))

        link = cur.fetchone()

        if link:
            self.id, self.source, self.permalink, self.subreddit, self.skip, self.author, self.title = link
            self.is_new = False


class Notification:
    def __init__(self, source):
        self.source = source
        self.id = source.id
        self.reply = source.reply
        self.links = []

    def set_language(self):
        source_subreddit = self.source.subreddit.lower()

        query = cur.execute(
            "SELECT language FROM subreddits WHERE name = ?",
            (source_subreddit,))
        lang = query.fetchone()
        if lang is None:
            try:
                lang = [r.get_subreddit(source_subreddit).lang]
            except RECOVERABLE_EXC as e:
                log_error(e)
                lang = [DEFAULT_LANG]  # use default if reddit fails

        try:
            i18n.setlang(lang[0])
        except TranslationException:
            i18n.setlang(DEFAULT_LANG)

    def should_notify(self):
        query = cur.execute("""
        SELECT subreddit, title, permalink FROM links
        WHERE source=? AND skip=?
        ORDER BY subreddit ASC, title ASC
        """, (self.id, False))

        for row in query:
            self.links.append(row)

        return any(self.links)

    def post_reply(self):
        # Render body.
        body = self._render_comment()

        if TEST:
            log.debug("""
========== COMMENT ============
Source: {}
{}
========== /COMMENT ===========
""".format(self.source.path, body))
            return True

        if self.reply:
            reply = r.get_info(thing_id=self.reply)
            reply.edit(body)
            return True

        if self.source.is_comment:
            reply = self.source.submission.reply(body)
            self.reply = reply.name

        elif self.source.is_post:
            reply = self.source.submission.add_comment(body)
            self.reply = reply.name

        self.source.reply = self.reply
        self.source.save()

        return True

    def _render_comment(self):
        self.set_language()

        translation_link = TRANSLATION_ERROR_LINK.format(language=i18n.name)
        translation_link = translation_link.replace(" ", "%20")

        footer_links = i18n.get("infolink").format(info=INFO_LINK,
                                                   contact=CONTACT_LINK,
                                                   translation=translation_link,
                                                   language=i18n.name)
        parts = []

        parts.append(i18n.get("linkingnotification"))

        cutoff_title = len(self.links) > LINKS_BEFORE_TITLE_CUTOFF

        for subreddit, title, permalink in self.links:
            if cutoff_title and len(title) > TITLE_LIMIT:
                title = title[:TITLE_LIMIT] + "..."
            parts.append("- [/r/{}] [{}]({})".format(subreddit,
                                                     escape_title(title),
                                                     np(permalink)))

        parts.append("[](#footer)*^({}) {}*".format(i18n.get("votingwarning"),
                                                    footer_links))
        parts.append("[](#bot)")

        return "\n\n".join(parts)



class Totes:

    def __init__(self, username, password, limit=25):
        self.username = username
        self.password = password
        self.limit = limit

        self._setup = False

    def run(self):
        """
        Comment replies notifying posts and comments that they have been linked
        to from somewhere else on reddit.
        """
        if not self._setup:
            raise Exception("Totes not ready yet!!!")

        log.info("Running.")

        sources = set()

        submissions = r.get_domain_listing('reddit.com', sort='new',
                                           limit=self.limit)

        for submission in submissions:
            now = datetime.now(timezone.utc).timestamp()

            if now - submission.created_utc < POST_TIME:
                continue  # skip if our post is less than POST_TIME (2 min) old

            try:
                source = Source(submission.url)
                source.load()
            except RECOVERABLE_EXC as e:
                if DEBUG:  # give a stacktrace only if debugging
                    log_error(e)
                else:
                    log.error(str(e))
                db.rollback()
                log.debug("Something wrong with source: {}".format(
                    submission.name))
                continue

            log.debug("Got source: {}".format(submission.name))

            source.check_skip()
            source.save()

            try:
                link = Link(submission, source.id)
                link.load()
            except RECOVERABLE_EXC as e:
                log_error(e)
                db.rollback()
                log.debug("Something wrong with link: {}".format(
                    submission.name))
                continue

            log.debug("Got link: {}".format(submission.name))

            link.check_skip()
            link.save()

            skip_any = source.skip or link.skip
            any_new = source.is_new or link.is_new

            log.debug("Skip any: {}".format(skip_any))
            log.debug("Any new: {}".format(any_new))

            if any_new and not skip_any:
                sources.add(source)

        for source in sources:
            notification = Notification(source)

            if notification.should_notify():
                try:
                    notification.post_reply()
                except RECOVERABLE_EXC as e:
                    log_error(e)
                    db.rollback()
                    continue

        log.info("Done.")

    def setup(self):
        """
        Load settings and perform setup.
        """
        self._login()

        self._setup = True
        log.info("Totes set up.")

    def quit(self):
        """
        Teardown.
        """
        log.info("Totes goodbye!")

    def _login(self):
        """
        Create reddit session.
        """
        r.login(self.username, self.password)
        log.info("Logged in to reddit.")

if __name__ == "__main__":

    username = os.environ.get("REDDIT_USERNAME")
    password = os.environ.get("REDDIT_PASSWORD")

    totes = Totes(username, password, LIMIT)
    totes.setup()

    try:
        while True:
            try:
                totes.run()
            except RECOVERABLE_EXC as e:
                log_error(e)
                db.rollback()
            time.sleep(WAIT)
    except KeyboardInterrupt:
        pass

    totes.quit()
    db.close()
    exit(0)

