# ============================================================
# FQCMS - Main Application Entry Point
# app.py
# ============================================================

import streamlit as st
import cloudinary
import cloudinary.uploader
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.connection import init_database, get_connection

st.set_page_config(
    page_title="FQCMS - Fruit Quality Claim System",
    page_icon="🍋",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_database()

cloudinary.config(
    cloud_name = st.secrets.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key    = st.secrets.get("CLOUDINARY_API_KEY", ""),
    api_secret = st.secrets.get("CLOUDINARY_API_SECRET", ""),
    secure     = True
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Light Theme ── */
.stApp {
    background: #f1f5f9 !important;
}

/* Main content area */
[data-testid="stMainBlockContainer"] {
    background: #f1f5f9 !important;
}

/* All text default */
* { color: #1e293b; }

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
    caret-color: #1e293b !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #94a3b8 !important;
}
.stTextInput label, .stTextArea label,
.stSelectbox label, .stDateInput label,
.stNumberInput label {
    color: #475569 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(59,130,246,0.35) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right: 1px solid #334155 !important;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid #334155 !important;
    color: #94a3b8 !important;
    width: 100% !important;
    text-align: left !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(59,130,246,0.15) !important;
    color: #ffffff !important;
    border-color: #3b82f6 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Section headers */
.section-header {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    margin: 24px 0 16px 0;
    color: #1d4ed8;
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Cards */
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* Expander */
.streamlit-expanderHeader {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
}

/* Radio buttons */
.stRadio label {
    color: #475569 !important;
}

/* Info/success/warning */
.stAlert {
    border-radius: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important;
    border-radius: 8px !important;
    padding: 4px !important;
    border: 1px solid #e2e8f0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: #475569 !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: #3b82f6 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ───────────────────────────────────────────
if "logged_in"       not in st.session_state:
    st.session_state.logged_in       = False
if "user"            not in st.session_state:
    st.session_state.user            = None
if "current_page"    not in st.session_state:
    st.session_state.current_page    = "dashboard"
if "claim_submitted" not in st.session_state:
    st.session_state.claim_submitted = False
if "selected_claim"  not in st.session_state:
    st.session_state.selected_claim  = None


# ══════════════════════════════════════════════════════════
# EMAIL
# ══════════════════════════════════════════════════════════

def send_confirmation_email(to_email, customer_name, ticket_number,
                             product, defect, priority):
    try:
        gmail    = st.secrets.get("GMAIL_ADDRESS", "")
        app_pass = st.secrets.get("GMAIL_APP_PASSWORD", "")
        if not gmail or not app_pass:
            return False, "Email not configured."
        pcolors  = {
            "Critical":"#ef4444",
            "Major":"#f59e0b",
            "Minor":"#10b981"
        }
        pcolor   = pcolors.get(priority, "#10b981")
        sla_map  = {
            "Critical": "Response: 2 hours | Resolution: 24 hours",
            "Major":    "Response: 4 hours | Resolution: 48 hours",
            "Minor":    "Response: 8 hours | Resolution: 72 hours",
        }
        html = f"""<!DOCTYPE html><html><body style="font-family:Arial;
        background:#f4f4f4;padding:20px;">
        <div style="max-width:600px;margin:0 auto;background:#fff;
        border-radius:12px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#1e293b,#334155);
        padding:30px;text-align:center;">
        <div style="font-size:36px;">🍋</div>
        <h1 style="color:#fff;margin:8px 0 4px;font-size:22px;">FQCMS</h1>
        <p style="color:#94a3b8;margin:0;font-size:13px;">
        Fruit Quality Claim Management System</p></div>
        <div style="padding:32px;">
        <h2 style="color:#1e293b;">✅ Claim Submitted Successfully</h2>
        <p style="color:#475569;">Dear <strong>{customer_name}</strong>,
        your quality claim has been received.</p>
        <div style="background:#f0fdf4;border:2px solid #10b981;
        border-radius:10px;padding:20px;text-align:center;margin:20px 0;">
        <p style="color:#475569;font-size:12px;
        text-transform:uppercase;margin:0;">Ticket Number</p>
        <p style="color:#10b981;font-size:32px;font-weight:700;
        letter-spacing:3px;margin:8px 0;">{ticket_number}</p></div>
        <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:8px;color:#475569;width:40%;
        border-bottom:1px solid #e2e8f0;">Product</td>
        <td style="padding:8px;color:#1e293b;font-weight:600;
        border-bottom:1px solid #e2e8f0;">{product}</td></tr>
        <tr><td style="padding:8px;color:#475569;
        border-bottom:1px solid #e2e8f0;">Defect</td>
        <td style="padding:8px;color:#1e293b;font-weight:600;
        border-bottom:1px solid #e2e8f0;">{defect}</td></tr>
        <tr><td style="padding:8px;color:#475569;">Priority</td>
        <td style="padding:8px;color:{pcolor};font-weight:700;">
        {priority}</td></tr></table>
        <p style="color:#475569;font-size:13px;margin-top:16px;">
        SLA: {sla_map.get(priority,"")}</p></div>
        <div style="background:#f8fafc;padding:16px;text-align:center;
        border-top:1px solid #e2e8f0;">
        <p style="color:#94a3b8;font-size:12px;margin:0;">
        Automated email from FQCMS</p></div></div>
        </body></html>"""
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = f"✅ Claim {ticket_number} Received | FQCMS"
        msg["From"]    = gmail
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(gmail, app_pass)
            s.sendmail(gmail, to_email, msg.as_string())
        return True, "Sent"
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════
# CLOUDINARY
# ══════════════════════════════════════════════════════════

def upload_to_cloudinary(file, ticket_number, file_type="photo"):
    try:
        result = cloudinary.uploader.upload(
            file,
            folder          = f"FQCMS/{ticket_number}",
            resource_type   = "video" if file_type=="video" else "image",
            use_filename    = True,
            unique_filename = True,
        )
        return result.get("secure_url"), result.get("public_id")
    except Exception as e:
        return None, str(e)


# ══════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════

def login_user(username, password):
    import bcrypt
    if not username or not password:
        return None, "Please enter both fields."
    try:
        conn = get_connection()
        row  = conn.execute("""
            SELECT u.id, u.username, u.full_name, u.email,
                   u.password_hash, u.is_active, r.name as role_name
            FROM users u JOIN roles r ON u.role_id = r.id
            WHERE u.username = ?
        """, (username.strip(),)).fetchone()
        conn.close()
        if not row:
            return None, "Invalid username or password."
        if not row["is_active"]:
            return None, "Account disabled."
        if bcrypt.checkpw(password.encode(),
                          row["password_hash"].encode()):
            conn2 = get_connection()
            conn2.execute(
                "UPDATE users SET last_login_at=datetime('now') "
                "WHERE id=?", (row["id"],)
            )
            conn2.commit()
            conn2.close()
            return dict(row), None
        return None, "Invalid username or password."
    except Exception as e:
        return None, str(e)


# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════

def show_sidebar(user):
    role = user["role_name"]
    role_colors = {
        "Admin":             "#ef4444",
        "Quality Manager":   "#f59e0b",
        "Quality Executive": "#10b981",
        "Customer":          "#3b82f6",
    }
    color = role_colors.get(role, "#ffffff")
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 8px 8px;text-align:center;'>
            <div style='font-size:36px;'>🍋</div>
            <div style='color:#ffffff;font-weight:700;
                        font-size:18px;margin-top:4px;'>FQCMS</div>
            <div style='color:#94a3b8;font-size:11px;'>
                Fruit Quality Claims</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown(f"""
        <div style='padding:10px;background:rgba(255,255,255,0.06);
                    border-radius:8px;margin-bottom:12px;'>
            <div style='color:#ffffff;font-weight:600;
                        font-size:13px;'>👤 {user['full_name']}</div>
            <div style='color:{color};font-size:11px;
                        margin-top:2px;'>● {role}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style='color:#64748b;font-size:11px;font-weight:600;
                    text-transform:uppercase;letter-spacing:1px;
                    padding:4px 0 8px;'>Navigation</div>
        """, unsafe_allow_html=True)

        nav_items = [
            ("🏠  Home Dashboard",  "dashboard",      True),
            ("📋  Submit a Claim",  "claim_portal",   True),
            ("🎫  Helpdesk Board",  "helpdesk",
             role in ["Admin","Quality Manager","Quality Executive"]),
            ("🔬  Investigations",  "investigations",
             role in ["Admin","Quality Manager","Quality Executive"]),
            ("💰  Settlements",     "settlements",
             role in ["Admin","Quality Manager","Quality Executive"]),
            ("📊  Dashboard",       "mgmt_dashboard",
             role in ["Admin","Quality Manager"]),
            ("⚙️  Admin Settings",  "admin",
             role == "Admin"),
        ]
        for label, page, visible in nav_items:
            if visible:
                if st.button(label, key=f"nav_{page}"):
                    st.session_state.current_page    = page
                    st.session_state.claim_submitted = False
                    st.session_state.selected_claim  = None
                    st.rerun()

        st.divider()
        if st.button("🚪  Logout", key="nav_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ══════════════════════════════════════════════════════════
# HOME DASHBOARD
# ══════════════════════════════════════════════════════════

def show_dashboard(user):
    role = user["role_name"]
    role_colors = {
        "Admin":             "#ef4444",
        "Quality Manager":   "#f59e0b",
        "Quality Executive": "#10b981",
        "Customer":          "#3b82f6",
    }
    color = role_colors.get(role, "#3b82f6")

    st.markdown(f"""
    <div style='background:#ffffff;border:1px solid #e2e8f0;
                border-left:4px solid {color};border-radius:12px;
                padding:24px 28px;margin-bottom:24px;
                box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
        <h2 style='color:#1e293b;margin:0 0 6px;'>
            Good day, {user['full_name']}! 👋</h2>
        <p style='color:#64748b;margin:0;font-size:14px;'>
            Logged in as
            <span style='color:{color};font-weight:600;'>{role}</span>
            &nbsp;·&nbsp; {user['email']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    conn   = get_connection()
    total  = conn.execute(
        "SELECT COUNT(*) FROM claims").fetchone()[0]
    open_c = conn.execute(
        "SELECT COUNT(*) FROM claims "
        "WHERE status NOT IN ('Resolved','Closed')").fetchone()[0]
    closed = conn.execute(
        "SELECT COUNT(*) FROM claims "
        "WHERE status IN ('Resolved','Closed')").fetchone()[0]
    new_c  = conn.execute(
        "SELECT COUNT(*) FROM claims "
        "WHERE status='New'").fetchone()[0]
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, clr, bg in [
        (c1, "📋 Total Claims",  total,  "#3b82f6", "#eff6ff"),
        (c2, "🆕 New Claims",    new_c,  "#ef4444", "#fef2f2"),
        (c3, "🔓 Open Claims",   open_c, "#f59e0b", "#fffbeb"),
        (c4, "✅ Closed Claims", closed, "#10b981", "#f0fdf4"),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:{bg};border:1px solid #e2e8f0;
                        border-top:3px solid {clr};border-radius:10px;
                        padding:20px;text-align:center;
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);'>
                <div style='font-size:28px;font-weight:700;
                            color:{clr};'>{value}</div>
                <div style='font-size:12px;color:#64748b;
                            margin-top:4px;font-weight:500;'>
                    {label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <h4 style='color:#1e293b;margin-bottom:16px;'>
        📌 Quick Actions</h4>
    """, unsafe_allow_html=True)

    qa1, qa2, qa3 = st.columns(3)
    cards = [
        (qa1, "📋", "Submit a Claim",
         "Lodge a new quality complaint", "qa_claim", "claim_portal"),
        (qa2, "🎫", "Helpdesk Board",
         "View and manage all tickets",   "qa_help",  "helpdesk"),
        (qa3, "🔬", "Investigations",
         "Investigate open claims",       "qa_inv",   "investigations"),
    ]
    for col, icon, title, desc, key, page in cards:
        with col:
            st.markdown(f"""
            <div style='background:#ffffff;border:1px solid #e2e8f0;
                        border-radius:10px;padding:18px;margin-bottom:8px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);'>
                <div style='font-size:28px;'>{icon}</div>
                <div style='color:#1e293b;font-weight:600;font-size:14px;
                            margin-top:8px;'>{title}</div>
                <div style='color:#64748b;font-size:12px;margin-top:4px;'>
                    {desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open →", key=key,
                         use_container_width=True):
                st.session_state.current_page    = page
                st.session_state.claim_submitted = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Use the left sidebar to navigate between all modules.")


# ══════════════════════════════════════════════════════════
# CLAIM PORTAL HELPERS
# ══════════════════════════════════════════════════════════

def get_products():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name FROM products WHERE is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return rows

def get_defects(product_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name FROM defect_types "
        "WHERE product_id=? AND is_active=1 ORDER BY name",
        (product_id,)
    ).fetchall()
    conn.close()
    return rows

def get_customers():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, customer_code, customer_name FROM customers "
        "WHERE is_active=1 ORDER BY customer_name"
    ).fetchall()
    conn.close()
    return rows

def generate_ticket_number():
    conn = get_connection()
    conn.execute(
        "UPDATE ticket_counter SET last_value=last_value+1 WHERE id=1"
    )
    conn.commit()
    row = conn.execute(
        "SELECT last_value FROM ticket_counter WHERE id=1"
    ).fetchone()
    conn.close()
    return f"FRUIT-{row['last_value']:06d}"

def save_attachment(claim_id, filename, file_type,
                    mime_type, size, url, public_id):
    conn = get_connection()
    conn.execute("""
        INSERT INTO attachments (
            claim_id, original_filename, stored_filename,
            file_type, mime_type, file_size_bytes,
            gdrive_file_id, gdrive_view_url
        ) VALUES (?,?,?,?,?,?,?,?)
    """, (claim_id, filename, public_id,
          file_type, mime_type, size, public_id, url))
    conn.commit()
    conn.close()

def submit_claim(data):
    from datetime import datetime, timedelta
    conn    = get_connection()
    cursor  = conn.cursor()
    ticket  = generate_ticket_number()
    sla_map = {
        "Critical":(2,24),
        "Major":(4,48),
        "Minor":(8,72)
    }
    rh, resh = sla_map[data["priority"]]
    now     = datetime.now()
    r_due   = (now+timedelta(hours=rh)).strftime("%Y-%m-%d %H:%M:%S")
    res_due = (now+timedelta(hours=resh)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO claims (
                ticket_number,customer_id,product_id,defect_type_id,
                invoice_number,invoice_date,quantity_received,
                quantity_claimed,quantity_unit,defect_description,
                priority,status,sla_response_due_at,
                sla_resolution_due_at,submitted_by_name,
                submitted_by_email,submitted_by_mobile
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,'New',?,?,?,?,?)
        """, (
            ticket,data["customer_id"],data["product_id"],
            data["defect_type_id"],data["invoice_number"],
            data["invoice_date"],data["quantity_received"],
            data["quantity_claimed"],data["quantity_unit"],
            data["defect_description"],data["priority"],
            r_due,res_due,data["contact_name"],
            data["email"],data["mobile"],
        ))
        cid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO sla_tracking (claim_id,priority,"
            "response_due_at,resolution_due_at) VALUES (?,?,?,?)",
            (cid,data["priority"],r_due,res_due)
        )
        cursor.execute(
            "INSERT INTO audit_logs (claim_id,action,entity_type,"
            "entity_id,new_value) VALUES (?,'CLAIM_CREATED','claim',?,?)",
            (cid,cid,ticket)
        )
        conn.commit()
        conn.close()
        return ticket, cid, None
    except Exception as e:
        conn.rollback()
        conn.close()
        return None, None, str(e)


# ══════════════════════════════════════════════════════════
# CLAIM PORTAL PAGE
# ══════════════════════════════════════════════════════════

def show_claim_portal():
    from datetime import date

    if st.session_state.claim_submitted:
        data   = st.session_state.get("submitted_data",{})
        pcolors = {
            "Critical":"#ef4444",
            "Major":"#f59e0b",
            "Minor":"#10b981"
        }
        pcolor = pcolors.get(data.get("priority","Minor"),"#10b981")
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);
                    border:2px solid #10b981;border-radius:16px;
                    padding:40px;text-align:center;margin:24px 0;
                    max-width:600px;margin-left:auto;margin-right:auto;'>
            <div style='font-size:56px;'>✅</div>
            <div style='color:#166534;font-size:13px;font-weight:600;
                        text-transform:uppercase;letter-spacing:1px;
                        margin-top:12px;'>Claim Submitted Successfully</div>
            <div style='font-size:40px;font-weight:700;color:#10b981;
                        letter-spacing:3px;margin:16px 0;
                        font-family:monospace;'>
                {st.session_state.ticket_number}</div>
            <div style='color:#475569;font-size:14px;'>
                Save this ticket number for reference</div>
            <div style='margin-top:16px;font-size:14px;'>
                <span style='color:#64748b;'>Product:</span>
                <span style='color:#1e293b;font-weight:600;'>
                    &nbsp;{data.get("product_name","")}</span>
                &nbsp;·&nbsp;
                <span style='color:#64748b;'>Priority:</span>
                <span style='color:{pcolor};font-weight:600;'>
                    &nbsp;{data.get("priority","")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if data.get("email_sent"):
            st.success(
                f"📧 Confirmation sent to {data.get('email')}"
            )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📋 Submit Another",
                         use_container_width=True):
                st.session_state.claim_submitted = False
                st.rerun()
        with col_b:
            if st.button("🏠 Back to Dashboard",
                         use_container_width=True):
                st.session_state.claim_submitted = False
                st.session_state.current_page    = "dashboard"
                st.rerun()
        return

    st.markdown("""
    <div style='margin-bottom:24px;'>
        <h2 style='color:#1e293b;margin:0;'>📋 Submit a Quality Claim</h2>
        <p style='color:#64748b;margin:6px 0 0;font-size:14px;'>
            Internal claim submission form.</p>
    </div>
    """, unsafe_allow_html=True)

    customers    = get_customers()
    products     = get_products()
    cust_options = {
        f"{c['customer_code']} — {c['customer_name']}": c["id"]
        for c in customers
    }
    prod_options = {p["name"]: p["id"] for p in products}

    st.markdown(
        "<div class='section-header'>🍋 Product & Defect</div>",
        unsafe_allow_html=True
    )
    pd1, pd2 = st.columns(2)
    with pd1:
        sel_prod = st.selectbox("Product *",
                                list(prod_options.keys()),
                                key="product_selector")
    with pd2:
        defect_rows    = get_defects(prod_options[sel_prod])
        defect_options = {d["name"]: d["id"] for d in defect_rows}
        sel_defect     = st.selectbox("Defect Type *",
                                      list(defect_options.keys()),
                                      key="defect_selector")

    st.markdown(
        "<div class='section-header'>📎 Attachments (Optional)</div>",
        unsafe_allow_html=True
    )
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        uploaded_photos = st.file_uploader(
            "Photos (JPG/PNG)",
            type=["jpg","jpeg","png","heic"],
            accept_multiple_files=True,
            key="photo_uploader"
        )
    with col_u2:
        uploaded_videos = st.file_uploader(
            "Videos (MP4/MOV)",
            type=["mp4","mov"],
            accept_multiple_files=True,
            key="video_uploader"
        )
    if uploaded_photos:
        cols = st.columns(min(len(uploaded_photos),5))
        for i, p in enumerate(uploaded_photos[:5]):
            with cols[i]:
                st.image(p, width=100)

    with st.form("claim_form", clear_on_submit=False):
        st.markdown(
            "<div class='section-header'>👤 Customer Information</div>",
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        with c1:
            sel_cust     = st.selectbox("Customer *",
                                        list(cust_options.keys()))
            contact_name = st.text_input("Contact Person *",
                                         placeholder="Full name")
        with c2:
            email  = st.text_input("Email *",
                                   placeholder="email@example.com")
            mobile = st.text_input("Mobile *",
                                   placeholder="10-digit number")

        st.markdown(
            "<div class='section-header'>🧾 Invoice Details</div>",
            unsafe_allow_html=True
        )
        c3, c4, c5 = st.columns(3)
        with c3:
            invoice_number = st.text_input("Invoice Number *",
                                           placeholder="INV-2024-001")
        with c4:
            invoice_date = st.date_input("Invoice Date *",
                                         value=date.today(),
                                         max_value=date.today())
        with c5:
            qty_unit = st.selectbox("Unit",
                                    ["KG","Box","Carton","Punnet","Piece"])

        st.markdown(
            "<div class='section-header'>📦 Quantity & Priority</div>",
            unsafe_allow_html=True
        )
        c6, c7, c8 = st.columns(3)
        with c6:
            qty_received = st.number_input("Qty Received *",
                                           min_value=0.0,step=0.5,
                                           format="%.1f")
        with c7:
            qty_claimed = st.number_input("Qty Claimed *",
                                          min_value=0.0,step=0.5,
                                          format="%.1f")
        with c8:
            priority = st.selectbox("Priority *",
                                    ["Minor","Major","Critical"])

        st.markdown(
            "<div class='section-header'>📝 Description</div>",
            unsafe_allow_html=True
        )
        description = st.text_area("Describe the defect *",
                                   height=120,
                                   placeholder="Describe the issue...")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "🚀 Submit Claim", use_container_width=True
        )

        if submitted:
            errors = []
            if not contact_name.strip():
                errors.append("Contact name required.")
            if not email.strip() or "@" not in email:
                errors.append("Valid email required.")
            if not mobile.strip() or len(mobile.strip()) < 10:
                errors.append("Valid mobile required.")
            if not invoice_number.strip():
                errors.append("Invoice number required.")
            if qty_claimed <= 0:
                errors.append("Qty Claimed must be > 0.")
            if qty_claimed > qty_received:
                errors.append("Claimed cannot exceed Received.")
            if not description.strip():
                errors.append("Description required.")
            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                with st.spinner("Submitting..."):
                    ticket, cid, err = submit_claim({
                        "customer_id":        cust_options[sel_cust],
                        "product_id":         prod_options[sel_prod],
                        "product_name":       sel_prod,
                        "defect_type_id":     defect_options[sel_defect],
                        "invoice_number":     invoice_number.strip(),
                        "invoice_date":       str(invoice_date),
                        "quantity_received":  qty_received,
                        "quantity_claimed":   qty_claimed,
                        "quantity_unit":      qty_unit,
                        "defect_description": description.strip(),
                        "priority":           priority,
                        "contact_name":       contact_name.strip(),
                        "email":              email.strip(),
                        "mobile":             mobile.strip(),
                    })
                    if not ticket:
                        st.error(f"❌ Failed: {err}")
                    else:
                        uploaded_names = []
                        for f in (uploaded_photos or []):
                            url, pid = upload_to_cloudinary(
                                f, ticket, "photo")
                            if url:
                                save_attachment(cid,f.name,"photo",
                                    f.type,f.size,url,pid)
                                uploaded_names.append(f.name)
                        for f in (uploaded_videos or []):
                            url, pid = upload_to_cloudinary(
                                f, ticket, "video")
                            if url:
                                save_attachment(cid,f.name,"video",
                                    f.type,f.size,url,pid)
                                uploaded_names.append(f.name)
                        email_sent, _ = send_confirmation_email(
                            email.strip(),contact_name.strip(),
                            ticket,sel_prod,sel_defect,priority
                        )
                        st.session_state.claim_submitted = True
                        st.session_state.ticket_number   = ticket
                        st.session_state.submitted_data  = {
                            "product_name": sel_prod,
                            "priority":     priority,
                            "email":        email.strip(),
                            "email_sent":   email_sent,
                        }
                        st.rerun()


# ══════════════════════════════════════════════════════════
# HELPDESK HELPERS
# ══════════════════════════════════════════════════════════

def get_priority_color(priority):
    return {
        "Critical":"#ef4444",
        "Major":"#f59e0b",
        "Minor":"#10b981"
    }.get(priority,"#64748b")

def get_status_color(status):
    return {
        "New":"#3b82f6",
        "Assigned":"#8b5cf6",
        "Investigation":"#f59e0b",
        "Pending Approval":"#f97316",
        "Resolved":"#10b981",
        "Closed":"#64748b",
    }.get(status,"#64748b")

def get_ageing(created_at):
    from datetime import datetime
    try:
        created = datetime.strptime(created_at[:19],"%Y-%m-%d %H:%M:%S")
        delta   = datetime.now() - created
        days    = delta.days
        hours   = delta.seconds // 3600
        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h {(delta.seconds%3600)//60}m"
    except Exception:
        return "N/A"

def get_sla_status(resolution_due, status):
    from datetime import datetime
    if status in ("Resolved","Closed"):
        return "ok"
    try:
        due  = datetime.strptime(
            resolution_due[:19],"%Y-%m-%d %H:%M:%S")
        diff = (due - datetime.now()).total_seconds()
        if diff < 0:      return "breached"
        if diff < 14400:  return "warning"
        return "ok"
    except Exception:
        return "ok"

def update_claim_status(claim_id, new_status, user_id):
    from datetime import datetime
    conn = get_connection()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    old  = conn.execute(
        "SELECT status FROM claims WHERE id=?",(claim_id,)
    ).fetchone()
    old_status = old["status"] if old else ""
    conn.execute(
        "UPDATE claims SET status=?,updated_at=? WHERE id=?",
        (new_status,now,claim_id)
    )
    if new_status == "Resolved":
        conn.execute(
            "UPDATE claims SET resolved_at=? WHERE id=?",
            (now,claim_id))
    if new_status == "Closed":
        conn.execute(
            "UPDATE claims SET closed_at=? WHERE id=?",
            (now,claim_id))
    conn.execute("""
        INSERT INTO audit_logs
        (claim_id,user_id,action,entity_type,entity_id,
         old_value,new_value)
        VALUES (?,?,'STATUS_CHANGE','claim',?,?,?)
    """, (claim_id,user_id,claim_id,old_status,new_status))
    conn.commit()
    conn.close()

def assign_claim(claim_id, assignee_id, user_id):
    from datetime import datetime
    conn = get_connection()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE claims
        SET assigned_to_id=?,assigned_at=?,
            status=CASE WHEN status='New' THEN 'Assigned'
                        ELSE status END,
            updated_at=?
        WHERE id=?
    """, (assignee_id,now,now,claim_id))
    conn.execute("""
        INSERT INTO audit_logs
        (claim_id,user_id,action,entity_type,entity_id,new_value)
        VALUES (?,?,'ASSIGNMENT','claim',?,?)
    """, (claim_id,user_id,claim_id,str(assignee_id)))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════
# HELPDESK BOARD
# ══════════════════════════════════════════════════════════

def show_helpdesk(user):
    role = user["role_name"]
    st.markdown("""
    <div style='margin-bottom:20px;'>
        <h2 style='color:#1e293b;margin:0;'>🎫 Helpdesk Board</h2>
        <p style='color:#64748b;margin:6px 0 0;font-size:14px;'>
            Manage and track all quality claims.</p>
    </div>
    """, unsafe_allow_html=True)

    f1,f2,f3,f4 = st.columns(4)
    with f1:
        fp = st.selectbox("Product",
            ["All","Banana","Pomegranate","Arils"],key="hd_prod")
    with f2:
        fpr = st.selectbox("Priority",
            ["All","Critical","Major","Minor"],key="hd_pri")
    with f3:
        fs = st.selectbox("Status",
            ["All","New","Assigned","Investigation",
             "Pending Approval","Resolved","Closed"],key="hd_st")
    with f4:
        search = st.text_input("Search",
            placeholder="Ticket / Customer",key="hd_srch")

    conn   = get_connection()
    query  = """
        SELECT c.id,c.ticket_number,c.status,c.priority,
               c.created_at,c.sla_resolution_due_at,
               cu.customer_name,p.name as product_name,
               dt.name as defect_name,u.full_name as assigned_to,
               c.defect_description,c.quantity_claimed,
               c.quantity_unit,c.submitted_by_name,
               c.submitted_by_email
        FROM claims c
        JOIN customers cu ON c.customer_id=cu.id
        JOIN products p   ON c.product_id=p.id
        JOIN defect_types dt ON c.defect_type_id=dt.id
        LEFT JOIN users u ON c.assigned_to_id=u.id
        WHERE 1=1
    """
    params = []
    if fp  != "All": query+=" AND p.name=?";    params.append(fp)
    if fpr != "All": query+=" AND c.priority=?";params.append(fpr)
    if fs  != "All": query+=" AND c.status=?";  params.append(fs)
    if search:
        query += (" AND (c.ticket_number LIKE ? "
                  "OR cu.customer_name LIKE ?)")
        params.extend([f"%{search}%",f"%{search}%"])
    query  += " ORDER BY c.created_at DESC"
    claims  = conn.execute(query,params).fetchall()
    execs   = conn.execute("""
        SELECT u.id,u.full_name FROM users u
        JOIN roles r ON u.role_id=r.id
        WHERE r.name IN ('Quality Executive','Quality Manager','Admin')
        AND u.is_active=1
    """).fetchall()
    conn.close()

    exec_opts = {"Unassigned":None}
    exec_opts.update({e["full_name"]:e["id"] for e in execs})

    s1,s2,s3,s4 = st.columns(4)
    for col,label,value,clr,bg in [
        (s1,"Total",   len(claims),
         "#3b82f6","#eff6ff"),
        (s2,"New",
         sum(1 for c in claims if c["status"]=="New"),
         "#ef4444","#fef2f2"),
        (s3,"Open",
         sum(1 for c in claims
             if c["status"] not in ("Resolved","Closed")),
         "#f59e0b","#fffbeb"),
        (s4,"Closed",
         sum(1 for c in claims
             if c["status"] in ("Resolved","Closed")),
         "#10b981","#f0fdf4"),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:{bg};border:1px solid #e2e8f0;
                        border-top:3px solid {clr};border-radius:10px;
                        padding:14px;text-align:center;
                        margin-bottom:16px;'>
                <div style='font-size:24px;font-weight:700;
                            color:{clr};'>{value}</div>
                <div style='font-size:11px;color:#64748b;
                            margin-top:2px;font-weight:500;'>
                    {label}</div>
            </div>
            """, unsafe_allow_html=True)

    if not claims:
        st.info("No claims found matching your filters.")
        return

    view = st.radio("View",["📋 List","🗂️ Kanban"],
                    horizontal=True,key="hd_view")

    if view == "🗂️ Kanban":
        show_kanban(claims)
    else:
        show_list_view(claims, role, exec_opts)


def show_kanban(claims):
    statuses = [
        ("New","#3b82f6"),("Assigned","#8b5cf6"),
        ("Investigation","#f59e0b"),
        ("Pending Approval","#f97316"),
        ("Resolved","#10b981"),("Closed","#64748b"),
    ]
    cols = st.columns(len(statuses))
    for col,(status,color) in zip(cols,statuses):
        sc = [c for c in claims if c["status"]==status]
        with col:
            st.markdown(f"""
            <div style='background:#ffffff;border:1px solid #e2e8f0;
                        border-top:3px solid {color};border-radius:10px;
                        padding:10px;margin-bottom:8px;'>
                <div style='color:{color};font-weight:700;font-size:11px;
                            text-transform:uppercase;'>{status}</div>
                <div style='color:#64748b;font-size:11px;'>
                    {len(sc)} ticket(s)</div>
            </div>
            """, unsafe_allow_html=True)
            for c in sc:
                pc  = get_priority_color(c["priority"])
                age = get_ageing(c["created_at"])
                sla = get_sla_status(
                    c["sla_resolution_due_at"] or "",c["status"])
                si  = ("🔴" if sla=="breached" else
                       "🟡" if sla=="warning"  else "🟢")
                st.markdown(f"""
                <div style='background:#ffffff;
                            border:1px solid #e2e8f0;
                            border-left:3px solid {pc};
                            border-radius:8px;padding:10px;
                            margin-bottom:8px;
                            box-shadow:0 1px 2px rgba(0,0,0,0.04);'>
                    <div style='color:#3b82f6;font-size:11px;
                                font-weight:700;'>
                        {c["ticket_number"]}</div>
                    <div style='color:#1e293b;font-size:12px;
                                font-weight:600;margin:3px 0;'>
                        {c["customer_name"]}</div>
                    <div style='color:#64748b;font-size:11px;'>
                        {c["product_name"]}</div>
                    <div style='display:flex;
                                justify-content:space-between;
                                margin-top:6px;font-size:10px;'>
                        <span style='color:{pc};font-weight:600;'>
                            {c["priority"]}</span>
                        <span style='color:#64748b;'>⏱{age}</span>
                        <span>{si}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def show_list_view(claims, role, exec_opts):
    status_opts = ["New","Assigned","Investigation",
                   "Pending Approval","Resolved","Closed"]
    for c in claims:
        pc  = get_priority_color(c["priority"])
        sc  = get_status_color(c["status"])
        age = get_ageing(c["created_at"])
        sla = get_sla_status(
            c["sla_resolution_due_at"] or "",c["status"])
        slac = ("#ef4444" if sla=="breached" else
                "#f59e0b" if sla=="warning"  else "#10b981")
        slal = ("⚠️ Breached" if sla=="breached" else
                "⚡ Warning"  if sla=="warning"  else "✅ OK")

        with st.expander(
            f"🎫 {c['ticket_number']}  |  {c['customer_name']}  "
            f"|  {c['product_name']}  |  {c['status']}  "
            f"|  Age: {age}"
        ):
            d1,d2 = st.columns([2,1])
            with d1:
                st.markdown(f"""
                <div style='background:#ffffff;
                            border:1px solid #e2e8f0;
                            border-radius:10px;padding:16px;'>
                    <div style='display:flex;gap:6px;
                                flex-wrap:wrap;margin-bottom:12px;'>
                        <span style='background:{pc}15;color:{pc};
                            padding:3px 10px;border-radius:20px;
                            font-size:11px;font-weight:700;
                            border:1px solid {pc}30;'>
                            {c["priority"]}</span>
                        <span style='background:{sc}15;color:{sc};
                            padding:3px 10px;border-radius:20px;
                            font-size:11px;font-weight:700;
                            border:1px solid {sc}30;'>
                            {c["status"]}</span>
                        <span style='background:{slac}15;color:{slac};
                            padding:3px 10px;border-radius:20px;
                            font-size:11px;font-weight:600;
                            border:1px solid {slac}30;'>
                            {slal}</span>
                    </div>
                    <table style='width:100%;font-size:13px;
                                  border-collapse:collapse;'>
                        <tr><td style='color:#64748b;padding:5px 0;
                            width:35%;'>Customer</td>
                            <td style='color:#1e293b;font-weight:600;'>
                            {c["customer_name"]}</td></tr>
                        <tr><td style='color:#64748b;padding:5px 0;'>
                            Contact</td>
                            <td style='color:#1e293b;'>
                            {c["submitted_by_name"]} ·
                            {c["submitted_by_email"]}</td></tr>
                        <tr><td style='color:#64748b;padding:5px 0;'>
                            Product</td>
                            <td style='color:#1e293b;'>
                            {c["product_name"]}</td></tr>
                        <tr><td style='color:#64748b;padding:5px 0;'>
                            Defect</td>
                            <td style='color:#1e293b;'>
                            {c["defect_name"]}</td></tr>
                        <tr><td style='color:#64748b;padding:5px 0;'>
                            Quantity</td>
                            <td style='color:#1e293b;'>
                            Claimed {c["quantity_claimed"]}
                            {c["quantity_unit"]}</td></tr>
                        <tr><td style='color:#64748b;padding:5px 0;'>
                            Assigned To</td>
                            <td style='color:#1e293b;'>
                            {c["assigned_to"] or "Unassigned"}</td></tr>
                        <tr><td style='color:#64748b;padding:5px 0;'>
                            Ageing</td>
                            <td style='color:#f59e0b;font-weight:600;'>
                            {age}</td></tr>
                    </table>
                    <div style='margin-top:10px;padding:10px;
                        background:#f8fafc;border-radius:8px;'>
                        <div style='color:#64748b;font-size:11px;
                            font-weight:600;margin-bottom:4px;'>
                            DEFECT DESCRIPTION</div>
                        <div style='color:#1e293b;font-size:13px;'>
                            {c["defect_description"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                st.markdown("""
                <div style='background:#ffffff;border:1px solid #e2e8f0;
                            border-radius:10px;padding:16px;'>
                    <div style='color:#3b82f6;font-weight:600;
                                font-size:13px;margin-bottom:12px;'>
                        ⚡ Actions</div>
                """, unsafe_allow_html=True)
                if role in ["Admin","Quality Manager",
                            "Quality Executive"]:
                    ns = st.selectbox("Update Status",status_opts,
                        index=status_opts.index(c["status"]),
                        key=f"st_{c['id']}")
                    if st.button("💾 Save Status",
                                 key=f"sv_{c['id']}",
                                 use_container_width=True):
                        if ns != c["status"]:
                            update_claim_status(
                                c["id"],ns,
                                st.session_state.user["id"])
                            st.success(f"✅ Updated to {ns}")
                            st.rerun()
                        else:
                            st.info("No change.")
                    st.markdown("<br>", unsafe_allow_html=True)
                    asgn = st.selectbox("Assign To",
                        list(exec_opts.keys()),
                        key=f"asgn_{c['id']}")
                    if st.button("👤 Assign",
                                 key=f"do_asgn_{c['id']}",
                                 use_container_width=True):
                        assign_claim(c["id"],exec_opts[asgn],
                            st.session_state.user["id"])
                        st.success(f"✅ Assigned to {asgn}")
                        st.rerun()

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🔬 Investigate",
                                 key=f"inv_{c['id']}",
                                 use_container_width=True):
                        st.session_state.selected_claim = c["id"]
                        st.session_state.current_page   = "investigations"
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# INVESTIGATIONS PAGE
# ══════════════════════════════════════════════════════════

def show_investigations(user):
    role = user["role_name"]

    st.markdown("""
    <div style='margin-bottom:20px;'>
        <h2 style='color:#1e293b;margin:0;'>🔬 Investigation Workspace</h2>
        <p style='color:#64748b;margin:6px 0 0;font-size:14px;'>
            Investigate claims, record root causes and add notes.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Claim Selector ────────────────────────────────────
    conn   = get_connection()
    claims = conn.execute("""
        SELECT c.id, c.ticket_number, c.status, c.priority,
               cu.customer_name, p.name as product_name,
               dt.name as defect_name, c.defect_description,
               c.quantity_claimed, c.quantity_unit,
               c.submitted_by_name, c.submitted_by_email,
               c.submitted_by_mobile, c.invoice_number,
               c.invoice_date, c.created_at,
               c.sla_resolution_due_at
        FROM claims c
        JOIN customers cu ON c.customer_id=cu.id
        JOIN products p   ON c.product_id=p.id
        JOIN defect_types dt ON c.defect_type_id=dt.id
        WHERE c.status NOT IN ('Closed')
        ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()

    if not claims:
        st.info("No active claims to investigate.")
        return

    claim_opts = {
        f"{c['ticket_number']} — {c['customer_name']} "
        f"({c['product_name']})": c["id"]
        for c in claims
    }

    # Auto-select if coming from helpdesk
    default_idx = 0
    if st.session_state.selected_claim:
        for i, cid in enumerate(claim_opts.values()):
            if cid == st.session_state.selected_claim:
                default_idx = i
                break

    selected_label = st.selectbox(
        "Select Claim to Investigate",
        list(claim_opts.keys()),
        index=default_idx,
        key="inv_claim_select"
    )
    claim_id = claim_opts[selected_label]
    claim    = next(
        c for c in claims if c["id"] == claim_id
    )

    # ── Claim Header Card ─────────────────────────────────
    pc  = get_priority_color(claim["priority"])
    sc  = get_status_color(claim["status"])
    age = get_ageing(claim["created_at"])
    sla = get_sla_status(
        claim["sla_resolution_due_at"] or "", claim["status"])
    slac = ("#ef4444" if sla=="breached" else
            "#f59e0b" if sla=="warning"  else "#10b981")

    st.markdown(f"""
    <div style='background:#ffffff;border:1px solid #e2e8f0;
                border-left:4px solid {pc};border-radius:12px;
                padding:16px 20px;margin-bottom:16px;
                box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
        <div style='display:flex;justify-content:space-between;
                    align-items:center;flex-wrap:wrap;gap:8px;'>
            <div>
                <span style='color:#3b82f6;font-size:18px;
                             font-weight:700;'>
                    {claim["ticket_number"]}</span>
                <span style='color:#64748b;font-size:14px;
                             margin-left:12px;'>
                    {claim["customer_name"]} ·
                    {claim["product_name"]} ·
                    {claim["defect_name"]}</span>
            </div>
            <div style='display:flex;gap:6px;'>
                <span style='background:{pc}15;color:{pc};
                    padding:4px 12px;border-radius:20px;
                    font-size:12px;font-weight:700;
                    border:1px solid {pc}30;'>
                    {claim["priority"]}</span>
                <span style='background:{sc}15;color:{sc};
                    padding:4px 12px;border-radius:20px;
                    font-size:12px;font-weight:700;
                    border:1px solid {sc}30;'>
                    {claim["status"]}</span>
                <span style='background:{slac}15;color:{slac};
                    padding:4px 12px;border-radius:20px;
                    font-size:12px;font-weight:600;
                    border:1px solid {slac}30;'>
                    ⏱ Age: {age}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Customer Details",
        "📎 Attachments",
        "🔬 Investigation",
        "📝 Internal Notes",
        "✅ Resolution"
    ])

    # ── TAB 1: Customer Details ───────────────────────────
    with tab1:
        st.markdown("""
        <div class='section-header'>👤 Customer & Claim Information
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style='background:#ffffff;border:1px solid #e2e8f0;
                        border-radius:10px;padding:16px;'>
                <div style='color:#64748b;font-size:11px;font-weight:600;
                            text-transform:uppercase;margin-bottom:12px;'>
                    Contact Information</div>
                <table style='width:100%;font-size:13px;'>
                    <tr><td style='color:#64748b;padding:5px 0;width:40%;'>
                        Name</td>
                        <td style='color:#1e293b;font-weight:600;'>
                        {claim["submitted_by_name"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Email</td>
                        <td style='color:#1e293b;'>
                        {claim["submitted_by_email"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Mobile</td>
                        <td style='color:#1e293b;'>
                        {claim["submitted_by_mobile"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Customer</td>
                        <td style='color:#1e293b;font-weight:600;'>
                        {claim["customer_name"]}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='background:#ffffff;border:1px solid #e2e8f0;
                        border-radius:10px;padding:16px;'>
                <div style='color:#64748b;font-size:11px;font-weight:600;
                            text-transform:uppercase;margin-bottom:12px;'>
                    Claim Details</div>
                <table style='width:100%;font-size:13px;'>
                    <tr><td style='color:#64748b;padding:5px 0;width:40%;'>
                        Invoice No.</td>
                        <td style='color:#1e293b;font-weight:600;'>
                        {claim["invoice_number"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Invoice Date</td>
                        <td style='color:#1e293b;'>
                        {claim["invoice_date"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Product</td>
                        <td style='color:#1e293b;font-weight:600;'>
                        {claim["product_name"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Defect</td>
                        <td style='color:#1e293b;'>
                        {claim["defect_name"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Qty Claimed</td>
                        <td style='color:#1e293b;'>
                        {claim["quantity_claimed"]}
                        {claim["quantity_unit"]}</td></tr>
                    <tr><td style='color:#64748b;padding:5px 0;'>
                        Submitted</td>
                        <td style='color:#1e293b;'>
                        {claim["created_at"][:16]}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class='section-header'>📝 Defect Description</div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:#fffbeb;border:1px solid #fcd34d;
                    border-radius:10px;padding:16px;
                    color:#92400e;font-size:14px;line-height:1.6;'>
            {claim["defect_description"]}
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 2: Attachments ────────────────────────────────
    with tab2:
        st.markdown("""
        <div class='section-header'>📎 Customer Uploaded Files</div>
        """, unsafe_allow_html=True)

        conn  = get_connection()
        files = conn.execute("""
            SELECT original_filename, file_type,
                   file_size_bytes, gdrive_view_url, uploaded_at
            FROM attachments WHERE claim_id=?
            ORDER BY uploaded_at DESC
        """, (claim_id,)).fetchall()
        conn.close()

        if not files:
            st.info("No files uploaded for this claim.")
        else:
            for f in files:
                size_kb = round(f["file_size_bytes"] / 1024, 1)
                icon    = "🖼️" if f["file_type"] == "photo" else "🎥"
                st.markdown(f"""
                <div style='background:#ffffff;border:1px solid #e2e8f0;
                            border-radius:8px;padding:12px 16px;
                            margin-bottom:8px;display:flex;
                            justify-content:space-between;
                            align-items:center;'>
                    <div>
                        <span style='font-size:16px;'>{icon}</span>
                        <span style='color:#1e293b;font-weight:600;
                                     font-size:13px;margin-left:8px;'>
                            {f["original_filename"]}</span>
                        <span style='color:#64748b;font-size:12px;
                                     margin-left:8px;'>
                            {size_kb} KB · {f["uploaded_at"][:16]}</span>
                    </div>
                    <a href='{f["gdrive_view_url"]}' target='_blank'
                       style='background:#eff6ff;color:#3b82f6;
                              padding:6px 14px;border-radius:6px;
                              text-decoration:none;font-size:12px;
                              font-weight:600;border:1px solid #bfdbfe;'>
                        👁️ View
                    </a>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 3: Investigation ──────────────────────────────
    with tab3:
        st.markdown("""
        <div class='section-header'>🔬 Investigation Details</div>
        """, unsafe_allow_html=True)

        conn = get_connection()
        inv  = conn.execute(
            "SELECT * FROM investigations WHERE claim_id=?",
            (claim_id,)
        ).fetchone()
        conn.close()

        root_cause_options = [
            "Select Root Cause",
            "Farm Issue",
            "Harvesting Issue",
            "Packing Issue",
            "Packhouse Issue",
            "Cold Chain Issue",
            "Transport Damage",
            "Customer Storage Issue",
            "Other"
        ]

        with st.form(f"inv_form_{claim_id}"):
            ic1, ic2 = st.columns(2)
            with ic1:
                root_cause = st.selectbox(
                    "Root Cause Category *",
                    root_cause_options,
                    index=root_cause_options.index(
                        inv["root_cause_category"]
                    ) if inv and inv["root_cause_category"]
                      in root_cause_options else 0
                )
                inspector = st.text_input(
                    "Inspector Name",
                    value=inv["inspector_name"] if inv else "",
                    placeholder="Name of inspector"
                )
            with ic2:
                from datetime import date as dt_date
                insp_date = st.date_input(
                    "Inspection Date",
                    value=dt_date.today()
                )
                lab_ref = st.text_input(
                    "Lab Report Reference",
                    value=inv["lab_report_ref"] if inv else "",
                    placeholder="LAB-2024-001"
                )

            root_details = st.text_area(
                "Root Cause Details *",
                value=inv["root_cause_details"] if inv else "",
                placeholder="Describe the root cause in detail...",
                height=100
            )
            findings = st.text_area(
                "Investigation Findings *",
                value=inv["findings"] if inv else "",
                placeholder="What was found during investigation?",
                height=100
            )
            ic3, ic4 = st.columns(2)
            with ic3:
                corrective = st.text_area(
                    "Corrective Action",
                    value=inv["corrective_action"] if inv else "",
                    placeholder="Immediate action taken...",
                    height=80
                )
            with ic4:
                preventive = st.text_area(
                    "Preventive Action",
                    value=inv["preventive_action"] if inv else "",
                    placeholder="Action to prevent recurrence...",
                    height=80
                )

            save_inv = st.form_submit_button(
                "💾 Save Investigation",
                use_container_width=True
            )

            if save_inv:
                if root_cause == "Select Root Cause":
                    st.error("❌ Please select a root cause.")
                elif not root_details.strip():
                    st.error("❌ Root cause details required.")
                elif not findings.strip():
                    st.error("❌ Findings required.")
                else:
                    from datetime import datetime
                    conn = get_connection()
                    now  = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S")
                    if inv:
                        conn.execute("""
                            UPDATE investigations SET
                                root_cause_category=?,
                                root_cause_details=?,
                                findings=?,
                                corrective_action=?,
                                preventive_action=?,
                                inspection_date=?,
                                inspector_name=?,
                                lab_report_ref=?,
                                updated_at=?
                            WHERE claim_id=?
                        """, (
                            root_cause, root_details.strip(),
                            findings.strip(),
                            corrective.strip(),
                            preventive.strip(),
                            str(insp_date),
                            inspector.strip(),
                            lab_ref.strip(),
                            now, claim_id
                        ))
                    else:
                        conn.execute("""
                            INSERT INTO investigations (
                                claim_id,root_cause_category,
                                root_cause_details,findings,
                                corrective_action,preventive_action,
                                inspection_date,inspector_name,
                                lab_report_ref,investigator_id,
                                started_at,created_at,updated_at
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            claim_id, root_cause,
                            root_details.strip(),
                            findings.strip(),
                            corrective.strip(),
                            preventive.strip(),
                            str(insp_date),
                            inspector.strip(),
                            lab_ref.strip(),
                            user["id"], now, now, now
                        ))
                    # Auto update status
                    conn.execute("""
                        UPDATE claims SET status='Investigation',
                        updated_at=? WHERE id=? AND status='Assigned'
                    """, (now, claim_id))
                    conn.execute("""
                        INSERT INTO audit_logs
                        (claim_id,user_id,action,entity_type,
                         entity_id,new_value)
                        VALUES (?,?,'INVESTIGATION_SAVED',
                                'investigation',?,?)
                    """, (claim_id, user["id"], claim_id,
                          root_cause))
                    conn.commit()
                    conn.close()
                    st.success(
                        "✅ Investigation saved successfully!"
                    )
                    st.rerun()

    # ── TAB 4: Internal Notes ─────────────────────────────
    with tab4:
        st.markdown("""
        <div class='section-header'>📝 Internal Notes</div>
        <p style='color:#64748b;font-size:13px;margin-bottom:16px;'>
            ⚠️ Internal notes are NOT visible to customers.
        </p>
        """, unsafe_allow_html=True)

        # Add note
        with st.form(f"note_form_{claim_id}"):
            note_text = st.text_area(
                "Add Internal Note",
                placeholder="Type your internal note here...",
                height=100
            )
            save_note = st.form_submit_button(
                "📝 Add Note", use_container_width=True
            )
            if save_note:
                if not note_text.strip():
                    st.error("❌ Note cannot be empty.")
                else:
                    from datetime import datetime
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO internal_notes
                        (claim_id, author_id, note, is_internal)
                        VALUES (?,?,?,1)
                    """, (claim_id, user["id"],
                          note_text.strip()))
                    conn.execute("""
                        INSERT INTO audit_logs
                        (claim_id,user_id,action,entity_type,
                         entity_id)
                        VALUES (?,?,'NOTE_ADDED','note',?)
                    """, (claim_id, user["id"], claim_id))
                    conn.commit()
                    conn.close()
                    st.success("✅ Note added!")
                    st.rerun()

        # Show existing notes
        conn  = get_connection()
        notes = conn.execute("""
            SELECT n.note, n.created_at, u.full_name
            FROM internal_notes n
            JOIN users u ON n.author_id=u.id
            WHERE n.claim_id=? AND n.is_internal=1
            ORDER BY n.created_at DESC
        """, (claim_id,)).fetchall()
        conn.close()

        if notes:
            for note in notes:
                st.markdown(f"""
                <div style='background:#ffffff;
                            border:1px solid #e2e8f0;
                            border-left:4px solid #3b82f6;
                            border-radius:8px;padding:14px;
                            margin-bottom:10px;'>
                    <div style='display:flex;
                                justify-content:space-between;
                                margin-bottom:8px;'>
                        <span style='color:#1e293b;font-weight:600;
                                     font-size:13px;'>
                            👤 {note["full_name"]}</span>
                        <span style='color:#94a3b8;font-size:12px;'>
                            {note["created_at"][:16]}</span>
                    </div>
                    <div style='color:#475569;font-size:13px;
                                line-height:1.6;'>
                        {note["note"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No internal notes yet.")

    # ── TAB 5: Resolution ─────────────────────────────────
    with tab5:
        st.markdown("""
        <div class='section-header'>✅ Resolution & Status Update
        </div>""", unsafe_allow_html=True)

        status_opts = [
            "New","Assigned","Investigation",
            "Pending Approval","Resolved","Closed"
        ]

        with st.form(f"res_form_{claim_id}"):
            new_status = st.selectbox(
                "Update Claim Status",
                status_opts,
                index=status_opts.index(claim["status"])
            )
            resolution_note = st.text_area(
                "Resolution Note",
                placeholder="Describe how this claim was resolved...",
                height=100
            )
            save_res = st.form_submit_button(
                "✅ Save Resolution",
                use_container_width=True
            )
            if save_res:
                from datetime import datetime
                conn = get_connection()
                now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_claim_status(
                    claim_id, new_status, user["id"]
                )
                if resolution_note.strip():
                    conn.execute("""
                        INSERT INTO internal_notes
                        (claim_id,author_id,note,is_internal)
                        VALUES (?,?,?,1)
                    """, (claim_id, user["id"],
                          f"[RESOLUTION] {resolution_note.strip()}"))
                    conn.commit()
                conn.close()
                st.success(
                    f"✅ Status updated to {new_status}"
                )
                st.rerun()

        # Audit Trail
        st.markdown("""
        <div class='section-header'>📋 Audit Trail</div>
        """, unsafe_allow_html=True)

        conn  = get_connection()
        logs  = conn.execute("""
            SELECT a.action, a.old_value, a.new_value,
                   a.created_at, u.full_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id=u.id
            WHERE a.claim_id=?
            ORDER BY a.created_at DESC
        """, (claim_id,)).fetchall()
        conn.close()

        if logs:
            for log in logs:
                action_icons = {
                    "CLAIM_CREATED":       "🆕",
                    "STATUS_CHANGE":       "🔄",
                    "ASSIGNMENT":          "👤",
                    "NOTE_ADDED":          "📝",
                    "INVESTIGATION_SAVED": "🔬",
                }
                icon = action_icons.get(log["action"], "📋")
                detail = ""
                if log["action"] == "STATUS_CHANGE":
                    detail = (f"{log['old_value']} → "
                              f"{log['new_value']}")
                elif log["action"] == "INVESTIGATION_SAVED":
                    detail = f"Root cause: {log['new_value']}"
                else:
                    detail = log["new_value"] or ""

                st.markdown(f"""
                <div style='display:flex;gap:12px;padding:10px 0;
                            border-bottom:1px solid #f1f5f9;
                            align-items:flex-start;'>
                    <span style='font-size:16px;margin-top:2px;'>
                        {icon}</span>
                    <div style='flex:1;'>
                        <div style='color:#1e293b;font-size:13px;
                                    font-weight:600;'>
                            {log["action"].replace("_"," ").title()}
                        </div>
                        <div style='color:#64748b;font-size:12px;'>
                            {detail}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:#94a3b8;font-size:11px;'>
                            {log["created_at"][:16]}</div>
                        <div style='color:#64748b;font-size:11px;'>
                            {log["full_name"] or "System"}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No audit trail yet.")


# ══════════════════════════════════════════════════════════
# COMING SOON
# ══════════════════════════════════════════════════════════

def show_coming_soon(title, icon):
    st.markdown(f"""
    <div style='text-align:center;padding:80px 20px;'>
        <div style='font-size:64px;'>{icon}</div>
        <h2 style='color:#1e293b;margin:16px 0 8px;'>{title}</h2>
        <p style='color:#64748b;font-size:15px;'>
            This module is being built. Coming very soon!</p>
        <div style='background:#eff6ff;border:1px solid #bfdbfe;
                    border-radius:10px;padding:16px;
                    display:inline-block;margin-top:24px;'>
            <span style='color:#3b82f6;font-size:13px;'>
                🔧 Under Construction</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════

def show_login_page():
    _, col, _ = st.columns([1,1.2,1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:20px 0 30px;'>
            <div style='font-size:52px;'>🍋</div>
            <p style='font-size:28px;font-weight:700;color:#1e293b;
                      margin:8px 0 0;'>FQCMS</p>
            <p style='font-size:14px;color:#64748b;margin:4px 0 0;'>
                Fruit Quality Claim Management System</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username",
                placeholder="Enter your username")
            password = st.text_input("Password",type="password",
                placeholder="Enter your password")
            submit   = st.form_submit_button("Sign In →",
                use_container_width=True)
            if submit:
                user, error = login_user(username, password)
                if user:
                    st.session_state.logged_in    = True
                    st.session_state.user         = user
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ {error}")

        st.markdown("""
        <div style='background:#eff6ff;border:1px solid #bfdbfe;
                    border-radius:10px;padding:16px;margin-top:16px;'>
            <div style='color:#1d4ed8;font-size:12px;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.5px;
                        margin-bottom:10px;'>
                🔑 Demo Credentials — Password: Admin@1234</div>
            <div style='color:#475569;font-size:13px;line-height:2.2;'>
                <span style='color:#1e293b;font-weight:600;'>
                    admin</span> → System Administrator<br>
                <span style='color:#1e293b;font-weight:600;'>
                    qmanager</span> → Quality Manager<br>
                <span style='color:#1e293b;font-weight:600;'>
                    qexec1</span> → Quality Executive<br>
                <span style='color:#1e293b;font-weight:600;'>
                    customer1</span> → Demo Customer
            </div>
        </div>
        <p style='text-align:center;color:#94a3b8;font-size:11px;
                  margin-top:16px;'>
            🔒 Secured · Role-Based Access Control</p>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════

if not st.session_state.logged_in:
    show_login_page()
else:
    user = st.session_state.user
    show_sidebar(user)
    page = st.session_state.current_page

    if page == "dashboard":
        show_dashboard(user)
    elif page == "claim_portal":
        show_claim_portal()
    elif page == "helpdesk":
        show_helpdesk(user)
    elif page == "investigations":
        show_investigations(user)
    elif page == "settlements":
        show_coming_soon("Settlements","💰")
    elif page == "mgmt_dashboard":
        show_coming_soon("Management Dashboard","📊")
    elif page == "admin":
        show_coming_soon("Admin Settings","⚙️")
    else:
        show_dashboard(user)
