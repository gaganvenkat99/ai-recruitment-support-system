import streamlit as st
import requests
from candidate_search_ui import render

BASE_URL = "http://127.0.0.1:8006"

# ==============================
# SESSION STATE
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ==============================
# SAFE REQUEST FUNCTION
# ==============================
def safe_post(url, payload):
    try:
        res = requests.post(url, json=payload)

        try:
            data = res.json()
        except:
            st.error("❌ Backend returned invalid response (not JSON)")
            return None

        return res.status_code, data

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend (server not running)")
        return None

    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


# ==============================
# LOGIN PAGE (NO SIGNUP)
# ==============================
def login_page():
    st.title("🔐 AI Recruitment System Login")

    st.info("👤 Contact admin to get login credentials")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.warning("⚠️ Please enter username and password")
            return

        result = safe_post(
            f"{BASE_URL}/auth/login",
            {"username": username, "password": password}
        )

        if result:
            status, data = result

            if status == 200 and "message" in data:
                st.session_state.logged_in = True
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error(data.get("error", "Invalid credentials"))


# ==============================
# MAIN APP FLOW
# ==============================
if not st.session_state.logged_in:
    login_page()
else:
    # ✅ KEEP YOUR ORIGINAL UI
    render()