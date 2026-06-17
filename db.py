import sqlite3
import random

DB_NAME = "tcg.db"


# =========================
# اتصال به دیتابیس
# =========================

def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================
# کاربران
# =========================

def register_user(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cur.fetchone()

    if user:
        db.close()
        return None

    points = random.randint(30, 120)

    cur.execute(
        "INSERT INTO users(user_id, points) VALUES(?, ?)",
        (user_id, points)
    )

    db.commit()
    db.close()

    return points


def get_points(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        "SELECT points FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    db.close()

    if row:
        return row[0]

    return 0


def add_points(user_id, amount):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, user_id)
    )

    db.commit()
    db.close()


def remove_points(user_id, amount):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        "UPDATE users SET points = points - ? WHERE user_id=?",
        (amount, user_id)
    )

    db.commit()
    db.close()


# =========================
# کارت های باز نشده
# =========================

def add_unopened_card(user_id, card_name, image_file):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        INSERT INTO unopened_cards
        (user_id, card_name, image_file)
        VALUES (?, ?, ?)
        """,
        (user_id, card_name, image_file)
    )

    db.commit()
    db.close()


def unopened_count(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM unopened_cards
        WHERE user_id=?
        """,
        (user_id,)
    )

    count = cur.fetchone()[0]

    db.close()

    return count


def get_next_unopened(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT
        id,
        user_id,
        card_name,
        image_file
        FROM unopened_cards
        WHERE user_id=?
        ORDER BY id ASC
        LIMIT 1
        """,
        (user_id,)
    )

    card = cur.fetchone()

    db.close()

    return card


def get_all_unopened(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT
        id,
        card_name,
        image_file
        FROM unopened_cards
        WHERE user_id=?
        ORDER BY id ASC
        """,
        (user_id,)
    )

    cards = cur.fetchall()

    db.close()

    return cards


# =========================
# اینونتوری
# =========================

def move_card_to_inventory(card_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT
        user_id,
        card_name,
        image_file
        FROM unopened_cards
        WHERE id=?
        """,
        (card_id,)
    )

    card = cur.fetchone()

    if not card:
        db.close()
        return False

    cur.execute(
        """
        INSERT INTO inventory
        (user_id, card_name, image_file)
        VALUES (?, ?, ?)
        """,
        card
    )

    cur.execute(
        """
        DELETE FROM unopened_cards
        WHERE id=?
        """,
        (card_id,)
    )

    db.commit()
    db.close()

    return True


def get_inventory(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT
        card_name,
        image_file
        FROM inventory
        WHERE user_id=?
        ORDER BY id ASC
        """,
        (user_id,)
    )

    cards = cur.fetchall()

    db.close()

    return cards


def inventory_count(user_id):

    db = get_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM inventory
        WHERE user_id=?
        """,
        (user_id,)
    )

    count = cur.fetchone()[0]

    db.close()

    return count