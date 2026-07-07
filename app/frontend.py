import streamlit as st
import requests
import base64
import urllib.parse
import pandas as pd

st.set_page_config(
    page_title="Family Fitness Tracker",
    page_icon="👟",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Page background */
    .stApp { background-color: #f0f7f4; }

    /* Card-style containers */
    .activity-card {
        background: white;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #2ecc71;
    }
    .leaderboard-card {
        background: white;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .gold   { border-left: 5px solid #f1c40f; }
    .silver { border-left: 5px solid #95a5a6; }
    .bronze { border-left: 5px solid #cd7f32; }
    .other  { border-left: 5px solid #3498db; }

    /* Metric labels */
    [data-testid="stMetricLabel"] { font-size: 0.8rem; color: #666; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; color: #2c3e50; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a3c34; }
    [data-testid="stSidebar"] * { color: #e8f5e9 !important; }
    [data-testid="stSidebar"] .stRadio label { font-size: 1rem; }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background-color: #27ae60;
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover { background-color: #219150; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

BASE_URL = "http://localhost:8000"


def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


# ── Helpers ───────────────────────────────────────────────────────────────────
def encode_text_for_overlay(text):
    if not text:
        return ""
    base64_text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    return urllib.parse.quote(base64_text)


def create_transformed_url(original_url, transformation_params, caption=None):
    if caption:
        encoded_caption = encode_text_for_overlay(caption)
        transformation_params = f"l-text,ie-{encoded_caption},ly-N20,lx-20,fs-100,co-white,bg-000000A0,l-end"
    if not transformation_params:
        return original_url
    parts = original_url.split("/")
    base_url = "/".join(parts[:4])
    file_path = "/".join(parts[4:])
    return f"{base_url}/tr:{transformation_params}/{file_path}"


def fmt_steps(val):
    return f"{val:,}" if val else "—"


def fmt_dist(val):
    return f"{val:.2f} km" if val is not None else "—"


def fmt_dur(val):
    return f"{val:.0f} min" if val is not None else "—"


# ── Pages ─────────────────────────────────────────────────────────────────────

def login_page():
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 👟 Family Fitness Tracker")
        st.markdown("Track steps, distance, and celebrate every milestone together.")
        st.markdown("---")

        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")

        if email and password:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Log In", type="primary", use_container_width=True):
                    r = requests.post(
                        f"{BASE_URL}/auth/jwt/login",
                        data={"username": email, "password": password},
                    )
                    if r.status_code == 200:
                        st.session_state.token = r.json()["access_token"]
                        me = requests.get(f"{BASE_URL}/users/me", headers=get_headers())
                        if me.status_code == 200:
                            st.session_state.user = me.json()
                            st.rerun()
                        else:
                            st.error("Could not fetch user profile.")
                    else:
                        st.error("Invalid email or password.")
            with col2:
                if st.button("Sign Up", use_container_width=True):
                    r = requests.post(
                        f"{BASE_URL}/auth/register",
                        json={"email": email, "password": password},
                    )
                    if r.status_code == 201:
                        st.success("Account created! You can now log in.")
                    else:
                        detail = r.json().get("detail", "Registration failed.")
                        st.error(f"Sign-up failed: {detail}")
        else:
            st.info("Enter your email and password to get started.")


def feed_page():
    st.markdown("## 🏃 Activity Feed")
    st.caption("Latest workouts from your family")
    st.markdown("---")

    r = requests.get(f"{BASE_URL}/feed", headers=get_headers())
    if r.status_code != 200:
        st.error(f"Could not load feed. (Status {r.status_code}: {r.text})")
        return

    posts = r.json()["posts"]
    if not posts:
        st.info("No activities logged yet. Be the first to share a workout!")
        return

    for post in posts:
        with st.container():
            st.markdown(
                f"""<div class="activity-card">
                    <strong>{post['email']}</strong> &nbsp;·&nbsp;
                    <span style="color:#888;font-size:0.85rem">{post['created_at'][:10]}</span>
                </div>""",
                unsafe_allow_html=True,
            )

            # Metrics row
            m1, m2, m3 = st.columns(3)
            m1.metric("👣 Steps", fmt_steps(post.get("steps")))
            m2.metric("📍 Distance", fmt_dist(post.get("distance")))
            m3.metric("⏱ Duration", fmt_dur(post.get("duration")))

            # Media
            url = post.get("url", "")
            caption = post.get("caption", "")
            if url:
                if post.get("file_type") == "photo":
                    st.image(create_transformed_url(url, "", caption), width=420)
                else:
                    st.video(create_transformed_url(url, "w-420,h-240,cm-pad_resize,bg-blurred"))
                    if caption:
                        st.caption(caption)
            elif caption:
                st.write(caption)

            # Delete button (owner only)
            if post.get("is_owner"):
                if st.button("Remove", key=f"del_{post['id']}"):
                    dr = requests.delete(
                        f"{BASE_URL}/posts/{post['id']}", headers=get_headers()
                    )
                    if dr.status_code == 200:
                        st.success("Activity removed.")
                        st.rerun()
                    else:
                        st.error("Could not remove activity.")

            st.markdown("<br>", unsafe_allow_html=True)


def upload_page():
    st.markdown("## 📤 Log an Activity")
    st.caption("Share your workout with the family")
    st.markdown("---")

    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Screenshot or video of your activity",
            type=["png", "jpg", "jpeg", "mp4", "avi", "mov", "mkv", "webm"],
        )
        caption = st.text_area("Note (optional)", placeholder="e.g. Morning jog around the park!")

        col1, col2, col3 = st.columns(3)
        with col1:
            steps = st.number_input("Steps", min_value=0, step=100, value=0)
        with col2:
            distance = st.number_input("Distance (km)", min_value=0.0, step=0.1, format="%.2f")
        with col3:
            duration = st.number_input("Duration (min)", min_value=0.0, step=1.0, format="%.0f")

        submitted = st.form_submit_button("Share Activity", type="primary", use_container_width=True)

    if submitted:
        if not uploaded_file:
            st.warning("Please attach a screenshot or video before sharing.")
            return
        with st.spinner("Uploading your activity..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {
                "caption": caption,
                "steps": steps if steps else None,
                "distance": distance if distance else None,
                "duration": duration if duration else None,
            }
            r = requests.post(
                f"{BASE_URL}/upload", files=files, data=data, headers=get_headers()
            )
        if r.status_code == 200:
            st.success("Activity shared! Head to the feed to see it.")
        else:
            st.error(f"Upload failed. ({r.status_code}: {r.text})")


def leaderboard_page():
    st.markdown("## 🏆 Family Leaderboard")
    st.caption("Ranked by total steps — keep moving!")
    st.markdown("---")

    r = requests.get(f"{BASE_URL}/leaderboard", headers=get_headers())
    if r.status_code != 200:
        st.error(f"Could not load leaderboard. ({r.status_code}: {r.text})")
        return

    entries = r.json()["leaderboard"]

    priority = {"mom": 0, "dad": 1}

    rows = []
    for entry in entries:
        name = entry["email"].split("@")[0]
        rows.append({
            "_order": priority.get(name.lower(), 99),
            "Name": name,
            "Steps": int(entry["total_steps"]),
            "Distance (km)": round(float(entry["total_distance"]), 2),
            "Activities": int(entry["post_count"]),
        })

    rows.sort(key=lambda x: (x["_order"], -x["Steps"]))
    for row in rows:
        del row["_order"]

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── App shell ─────────────────────────────────────────────────────────────────
if st.session_state.user is None:
    login_page()
else:
    user_email = st.session_state.user["email"]

    with st.sidebar:
        st.markdown("### 👟 Family Fitness")
        st.markdown(f"Logged in as **{user_email}**")
        st.markdown("---")
        page = st.radio(
            "Navigate",
            ["🏃 Activity Feed", "📤 Log Activity", "🏆 Leaderboard"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        if st.button("Log Out", use_container_width=True):
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()

    if page == "🏃 Activity Feed":
        feed_page()
    elif page == "📤 Log Activity":
        upload_page()
    else:
        leaderboard_page()
