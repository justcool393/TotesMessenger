import os
import sys

import psycopg2 as pg

from datetime import datetime, timedelta
from urllib.parse import urlparse

from settings import IGNORED_BOTH, IGNORED_LINKS, IGNORED_SOURCES, IGNORED_USERS

PRUNE_PERIOD = timedelta(2)  # Two days

# Database
db_url = urlparse(os.environ["DATABASE_URL"])

db = pg.connect(
    database=db_url.path[1:],
    user=db_url.username,
    password=db_url.password,
    host=db_url.hostname,
    port=db_url.port
)

#db = sqlite3.connect('totes.sqlite3')
cur = db.cursor()

def create_tables():
    """
    Create tables.
    """

    cur.execute("""
    CREATE TABLE subreddits (
        name         TEXT  PRIMARY KEY,
        skip_source  BOOLEAN      DEFAULT FALSE,
        skip_link    BOOLEAN      DEFAULT FALSE,
        t            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE users (
        name         TEXT  PRIMARY KEY,
        skip_source  BOOLEAN      DEFAULT FALSE,
        skip_link    BOOLEAN      DEFAULT FALSE,
        t            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE sources (
        id         TEXT  PRIMARY KEY,
        reply      TEXT  UNIQUE,
        subreddit  TEXT,
        author     TEXT,
        title      TEXT,
        skip       BOOLEAN      DEFAULT FALSE,
        t          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE links (
        id         TEXT   PRIMARY KEY,
        source     TEXT,
        subreddit  TEXT,
        author     TEXT,
        title      TEXT,
        permalink  TEXT,
        skip       BOOLEAN       DEFAULT FALSE,
        t          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE INDEX ON links (source)
    """)

    db.commit()
    print("Tables ready.")

def sub_exists(sub):
    cur.execute("SELECT 1 FROM subreddits WHERE name=%s LIMIT 1", (sub,))
    return True if cur.fetchone() else False

def user_exists(user):
    cur.execute("SELECT 1 FROM users WHERE name=%s LIMIT 1", (user,))
    return True if cur.fetchone() else False

def populate_db():
    for sub in IGNORED_SOURCES:
        if sub_exists(sub):
            print("Updating {}".format(sub))
            cur.execute("""
            UPDATE subreddits SET skip_source=%s
            WHERE name=%s
            """, (True, sub))
        else:
            print("Inserting {}".format(sub))
            cur.execute("""
            INSERT INTO subreddits (name, skip_source)
            VALUES (%s, %s)
            """, (sub, True))

    for sub in IGNORED_BOTH:
        if sub_exists(sub):
            print("Updating {}".format(sub))
            cur.execute("""
            UPDATE subreddits SET skip_source=%s, skip_link=%s
            WHERE name=%s
            """, (True, True, sub))
        else:
            print("Inserting {}".format(sub))
            cur.execute("""
            INSERT INTO subreddits (name, skip_source, skip_link)
            VALUES (%s, %s, %s)
            """, (sub, True, True))

    for sub in IGNORED_LINKS:
        if sub_exists(sub):
            print("Updating {}".format(sub))
            cur.execute("""
            UPDATE subreddits SET skip_link=%s
            WHERE name=%s
            """, (True, sub))
        else:
            print("Inserting {}".format(sub))
            cur.execute("""
            INSERT INTO subreddits (name, skip_link)
            VALUES (%s, %s)
            """, (sub, True))

    for user in IGNORED_USERS:
        if user_exists(user):
            print("Updating {}".format(user))
            cur.execute("""
            UPDATE users SET skip_link=%s
            WHERE name=%s
            """, (True, user))
        else:
            print("Inserting {}".format(user))
            cur.execute("""
            INSERT INTO users (name, skip_link) VALUES (%s, %s)
            """, (user, True))

    db.commit()
    print("Default settings setup.")

def prune_db():
    prune_til = datetime.utcnow() - PRUNE_PERIOD

    cur.execute("""
    DELETE FROM links
    WHERE source IN (SELECT id FROM sources WHERE t < %s)
    """, (prune_til,))

    print("Pruned {} old links.".format(cur.rowcount))

    cur.execute("""
    DELETE FROM sources WHERE t < %s
    """, (prune_til,))

    print("Pruned {} old sources.".format(cur.rowcount))
    db.commit()

if __name__ == '__main__':
    if 'create' in sys.argv:
        create_tables()

    if 'populate' in sys.argv:
        populate_db()

    if 'prune' in sys.argv:
        prune_db()

db.close()

