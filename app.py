# ============================================================
# FQCMS - Main Application Entry Point
# app.py
# ============================================================

import streamlit as st
from database.connection import init_database

# ── Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="FQCMS - Fruit Quality Claim System",
    page_icon="🍋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Initialise Database on first run ───────────────────────
init_database()

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
/* Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}

/* Dark background */
.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 50%, #0f1117 100%);
    min-height: 100vh;
}

/* Login card */
.login-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 40px;
    backdrop-filter: blur(10px);
}

/* Logo area */
.logo-area {
    text-align: center;
    padding: 20px 0 30px 0;
}

.logo-title {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}

.logo-subtitle {
    font-size: 14px;
    color: #8892a4;
    margin: 4px 0 0 0;
}

.logo-icon {
    font-size: 48px;
    margin-bottom: 12px;
}

/* Input fields */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #4f8ef7 !important;
    box-shadow: 0 0 0 2px rgba(79,142,247,0.2) !important;
}

.stTextInput label {
    color: #8892a4 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Login button */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #4f8ef7 0%, #7c3aed 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-top: 8px;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(79,142,247,0.4);
}

/* Error / success messages */
.stAlert {
    border-radius: 8px !important;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 24px 0;
}

/* Role badges */
.role-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px;
}

.badge-admin    { background:#ef444420; color:#ef4444; border:1px solid #ef444440; }
.badge-manager  { background:#f59e0b20; color:#f59e0b; border:1px solid #f59e0b40; }
.badge-exec     { background:#10b98120; color:#10b981; border:1px solid #10b98140; }
.badge-customer { background:#4f8ef720; color:#4f8ef7; border:1px solid #4f8ef740; }

/* Demo credentials box */
.demo-box {
    background: rgba(79,142,247,0.08);
    border: 1px solid rgba(79,142,247,0.2);
    border-radius: 10px;
    padding: 16px;
    margin-top: 16px;
}

.demo-title {
    color: #4f8ef7;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}

.demo-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 12px;
    color: #8892a4;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.demo-row:last-child { border-bottom: none; }
.demo-user { color: #ffffff; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialisation ───────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None


def login_user(username, password):
    """
    Validates credentials against the database.
    Returns user dict on success, None on failure.
    """
    import bcrypt
    from database.connection import get_connection

    if not username or not password:
        return None, "Please enter both username and password."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        row = cursor.execute("""
            SELECT u.id, u.username, u.full_name, u.email,
                   u.password_hash, u.is_active, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = ?
        """, (username.strip(),)).fetchone()
        conn.close()

        if not row:
            return None, "Invalid username or password."

        if not row["is_active"]:
            return None, "Your account has been disabled. Contact admin."

        if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            # Update last login time
            conn2 = get_connection()
            conn2.execute(
                "UPDATE users SET last_login_at = datetime('now') WHERE id = ?",
                (row["id"],)
            )
            conn2.commit()
            conn2.close()

            return dict(row), None
        else:
            return None, "Invalid username or password."

    except Exception as e:
        return None, f"Login error: {str(e)}"


def show_dashboard(user):
    """
    Routes user to their role-based dashboard after login.
    """
    role = user["role_name"]

    # ── Top Navigation Bar ──────────────────────────────────
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown("### 🍋 FQCMS")
    with col2:
        st.markdown(f"""
        <div style='text-align:center; padding-top:8px;'>
            <span style='color:#8892a4; font-size:13px;'>Welcome back,</span>
            <span style='color:#ffffff; font-weight:600; font-size:15px;'>
                &nbsp;{user['full_name']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

    st.divider()

    # ── Role Based Welcome ──────────────────────────────────
    role_colors = {
        "Admin":             "#ef4444",
        "Quality Manager":   "#f59e0b",
        "Quality Executive": "#10b981",
        "Customer":          "#4f8ef7",
    }
    color = role_colors.get(role, "#ffffff")

    st.markdown(f"""
    <div style='
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 24px;
    '>
        <h2 style='color:#ffffff; margin:0 0 6px 0;'>
            Good day, {user['full_name']}! 👋
        </h2>
        <p style='color:#8892a4; margin:0; font-size:14px;'>
            You are logged in as
            <span style='color:{color}; font-weight:600;'>{role}</span>
            &nbsp;·&nbsp; {user['email']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Stats ─────────────────────────────────────────
    from database.connection import get_connection
    conn = get_connection()

    total   = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    open_c  = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE status NOT IN ('Resolved','Closed')"
    ).fetchone()[0]
    closed  = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE status IN ('Resolved','Closed')"
    ).fetchone()[0]
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "📋 Total Claims",  total,  "#4f8ef7"),
        (c2, "🔴 Open Claims",   open_c, "#ef4444"),
        (c3, "✅ Closed Claims", closed, "#10b981"),
        (c4, "📊 Modules",       "7",    "#f59e0b"),
    ]
    for col, label, value, color in metrics:
        with col:
            st.markdown(f"""
            <div style='
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-top: 3px solid {color};
                border-radius: 10px;
                padding: 20px;
                text-align: center;
            '>
                <div style='font-size:28px; font-weight:700; color:{color};'>
                    {value}
                </div>
                <div style='font-size:12px; color:#8892a4; margin-top:4px;'>
                    {label}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Navigation Menu ─────────────────────────────────────
    st.markdown("""
    <h4 style='color:#ffffff; margin-bottom:16px;'>📌 Quick Navigation</h4>
    """, unsafe_allow_html=True)

    # Menu items based on role
    all_menus = {
        "Admin": [
            ("📋", "Submit a Claim",       "For testing the customer portal"),
            ("🎫", "Helpdesk Board",        "Manage all quality tickets"),
            ("🔬", "Investigations",        "Investigate open claims"),
            ("💰", "Settlements",          "Process claim settlements"),
            ("📊", "Dashboard",            "Management KPI reports"),
            ("⚙️", "Admin Settings",       "Users, roles, products"),
        ],
        "Quality Manager": [
            ("🎫", "Helpdesk Board",        "View and manage tickets"),
            ("💰", "Settlements",          "Approve or reject settlements"),
            ("📊", "Dashboard",            "KPI reports and analytics"),
        ],
        "Quality Executive": [
            ("🎫", "Helpdesk Board",        "View assigned tickets"),
            ("🔬", "Investigations",        "Investigate claims"),
            ("💰", "Settlements",          "Submit settlement proposals"),
        ],
        "Customer": [
            ("📋", "Submit a Claim",       "Lodge a new quality complaint"),
            ("🔍", "Track My Claims",      "View status of your claims"),
        ],
    }

    menus = all_menus.get(role, [])
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(menus):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                padding: 18px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: all 0.2s;
            '>
                <div style='font-size:24px;'>{icon}</div>
                <div style='color:#ffffff; font-weight:600;
                            font-size:14px; margin-top:8px;'>
                    {title}
                </div>
                <div style='color:#8892a4; font-size:12px; margin-top:4px;'>
                    {desc}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
  # ── Module Navigation Links ─────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Submit a New Claim", use_container_width=True):
            st.switch_page("pages/01_claim_portal.py")
    with col2:
        st.info("🚧 More modules coming soon...")


def show_login_page():
    """
    Renders the professional login page.
    """
    # Centre the login form
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        # Logo
        st.markdown("""
        <div class='logo-area'>
            <div class='logo-icon'>🍋</div>
            <p class='logo-title'>FQCMS</p>
            <p class='logo-subtitle'>Fruit Quality Claim Management System</p>
        </div>
        """, unsafe_allow_html=True)

        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password",
                                     placeholder="Enter your password")
            submit = st.form_submit_button("Sign In →")

            if submit:
                user, error = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.role = user["role_name"]
                    st.rerun()
                else:
                    st.error(f"❌ {error}")

        # Demo credentials
        st.markdown("""
        <div class='demo-box'>
            <div class='demo-title'>🔑 Demo Credentials (Password: Admin@1234)</div>
            <div class='demo-row'>
                <span class='demo-user'>admin</span>
                <span>System Administrator</span>
            </div>
            <div class='demo-row'>
                <span class='demo-user'>qmanager</span>
                <span>Quality Manager</span>
            </div>
            <div class='demo-row'>
                <span class='demo-user'>qexec1</span>
                <span>Quality Executive</span>
            </div>
            <div class='demo-row'>
                <span class='demo-user'>customer1</span>
                <span>Demo Customer</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style='text-align:center; color:#8892a4;
                  font-size:11px; margin-top:20px;'>
            🔒 Secured · Role-Based Access Control
        </p>
        """, unsafe_allow_html=True)


# ── Main Router ────────────────────────────────────────────
if st.session_state.logged_in and st.session_state.user:
    show_dashboard(st.session_state.user)
else:
    show_login_page()
