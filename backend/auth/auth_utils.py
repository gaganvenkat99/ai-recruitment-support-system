import sqlite3
import bcrypt
import os

# ==============================
# DATABASE PATH
# ==============================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "recruitment_fixed_ids.db")

# ==============================
# ADMIN CREDENTIALS (CHANGE IF NEEDED)
# ==============================
ADMIN_USERNAME = "Bvivek@7702"
ADMIN_PASSWORD = "vivek@6604"


# ==============================
# REGISTER USER
# ==============================
def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed.decode())   # store as string
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        # user already exists
        return False

    except Exception as e:
        print("Register Error:", e)
        return False

    finally:
        conn.close()


# ==============================
# LOGIN USER
# ==============================
def login_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE username=?",
            (username,)
        )

        result = cursor.fetchone()

        if result:
            stored_password = result[0].encode()
            return bcrypt.checkpw(password.encode(), stored_password)

        return False

    except Exception as e:
        print("Login Error:", e)
        return False

    finally:
        conn.close()


# ==============================
# ADMIN VALIDATION
# ==============================
def is_admin(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD