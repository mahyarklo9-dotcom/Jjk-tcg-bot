import sqlite3
import random
import time

DB_NAME = "tcg.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================
# INIT TABLES
# =========================
def init_db():
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS unopened_cards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        card_name TEXT,
        image_file TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        card_name TEXT,
        image_file TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cooldown(
        user_id INTEGER PRIMARY KEY,
        last_time INTEGER
    )
    """)

    db.commit()
    db.close()


# =========================
# USERS
# =========================
def register_user(user_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if row:
        db.close()
        return row[0]

    points = random.randint(30, 120)

    cur.execute(
        "INSERT INTO users(user_id, points) VALUES(?,?)",
        (user_id, points)
    )

    db.commit()
    db.close()

    return points


def get_points(user_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    db.close()

    return row[0] if row and row[0] is not None else 0


def add_points(user_id, amount):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    INSERT INTO users(user_id, points)
    VALUES(?,?)
    ON CONFLICT(user_id) DO UPDATE SET points = points + ?
    """, (user_id, amount, amount))

    db.commit()
    db.close()


def remove_points(user_id, amount):
    add_points(user_id, -amount)


# =========================
# CARDS
# =========================
def add_unopened_card(user_id, name, img):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    INSERT INTO unopened_cards(user_id, card_name, image_file)
    VALUES(?,?,?)
    """, (user_id, name, img))

    db.commit()
    db.close()


def get_next_unopened(user_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    SELECT id, user_id, card_name, image_file
    FROM unopened_cards
    WHERE user_id=?
    ORDER BY id ASC
    LIMIT 1
    """, (user_id,))

    row = cur.fetchone()
    db.close()
    return row


def move_card_to_inventory(card_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    SELECT user_id, card_name, image_file
    FROM unopened_cards
    WHERE id=?
    """, (card_id,))

    card = cur.fetchone()

    if not card:
        db.close()
        return

    cur.execute("""
    INSERT INTO inventory(user_id, card_name, image_file)
    VALUES(?,?,?)
    """, card)

    cur.execute("DELETE FROM unopened_cards WHERE id=?", (card_id,))

    db.commit()
    db.close()


def unopened_count(user_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    SELECT COUNT(*) FROM unopened_cards WHERE user_id=?
    """, (user_id,))

    count = cur.fetchone()[0]

    db.close()
    return count


def get_inventory(user_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    SELECT card_name FROM inventory WHERE user_id=?
    """, (user_id,))

    rows = cur.fetchall()

    db.close()
    return rows


def get_card_by_name(user_id, name):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    SELECT id FROM inventory
    WHERE user_id=? AND card_name=?
    LIMIT 1
    """, (user_id, name))

    row = cur.fetchone()

    db.close()
    return row


def transfer_card(card_id, from_user, to_user):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    UPDATE inventory
    SET user_id=?
    WHERE id=? AND user_id=?
    """, (to_user, card_id, from_user))

    db.commit()
    db.close()


# =========================
# CHANS
# =========================
def get_last_chans(user_id):
    db = get_connection()
    cur = db.cursor()

    cur.execute("SELECT last_time FROM cooldown WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    db.close()

    return row[0] if row else 0


def set_last_chans(user_id, t):
    db = get_connection()
    cur = db.cursor()

    cur.execute("""
    INSERT INTO cooldown(user_id, last_time)
    VALUES(?,?)
    ON CONFLICT(user_id) DO UPDATE SET last_time=excluded.last_time
    """, (user_id, t))

    db.commit()
    db.close()
