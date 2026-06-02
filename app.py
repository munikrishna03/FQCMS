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
.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 50%, #0f1117 100%);
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    color: #111827 !important;
    caret-color: #111827 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    background: #ffffff !important;
    border-color: #4f8ef7 !important;
    color: #111827 !important;
    box-shadow: 0 0 0 2px rgba(79,142,247,0.25) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #9ca3af !important;
}
.stTextInput label, .stTextArea label,
.stSelectbox label, .stDateInput label,
.stNumberInput label {
    color: #cbd5e1 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    color: #111827 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #4f8ef7 0%, #7c3aed 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(79,142,247,0.4) !important;
}
[data-testid="stSidebar"] {
    background: #12151f !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #8892a4 !important;
    width: 100% !important;
    text-align: left !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(79,142,247,0.1) !important;
    color: #ffffff !important;
    border-color: #4f8ef7 !important;
    transform: none !important;
    box-shadow: none !important;
}
.section-header {
    background: rgba(79,142,247,0.08);
    border-left: 4px solid #4f8ef7;
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    margin: 24px 0 16px 0;
    color: #4f8ef7;
    font-weight: 600;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
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
        pcolors  = {"Critical":"#ef4444","Major":"#f59e0b","Minor":"#10b981"}
        pcolor   = pcolors.get(priority, "#10b981")
        sla_map  = {
            "Critical": "Response: 2 hours | Resolution: 24 hours",
            "Major":    "Response: 4 hours | Resolution: 48 hours",
            "Minor":    "Response: 8 hours | Resolution: 72 hours",
        }
        sla_text = sla_map.get(priority, "")
        html_body = f"""
        <!DOCTYPE html><html><body style="font-family:Arial,sans-serif;
        background:#f4f4f4;margin:0;padding:20px;">
        <div style="max-width:600px;margin:0 auto;background:#ffffff;
        border-radius:12px;overflow:hidden;
        box-shadow:0 4px 20px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#1a1d2e,#2d3748);
        padding:30px;text-align:center;">
        <div style="font-size:36px;">🍋</div>
        <h1 style="color:#ffffff;margin:8px 0 4px 0;font-size:22px;">
        FQCMS</h1>
        <p style="color:#8892a4;margin:0;font-size:13px;">
        Fruit Quality Claim Management System</p></div>
        <div style="padding:32px;">
        <h2 style="color:#111827;margin:0 0 8px 0;">
        ✅ Claim Submitted Successfully</h2>
        <p style="color:#6b7280;font-size:14px;">
        Dear <strong>{customer_name}</strong>,<br><br>
        Your quality claim has been received. Our team will
        contact you within the SLA timeline.</p>
        <div style="background:#f0fdf4;border:2px solid #10b981;
        border-radius:10px;padding:20px;text-align:center;margin:24px 0;">
        <p style="color:#6b7280;font-size:12px;
        text-transform:uppercase;margin:0;">Your Ticket Number</p>
        <p style="color:#10b981;font-size:32px;font-weight:700;
        letter-spacing:3px;margin:8px 0;">{ticket_number}</p>
        <p style="color:#6b7280;font-size:12px;margin:0;">
        Quote this in all communications</p></div>
        <table style="width:100%;border-collapse:collapse;">
        <tr style="background:#f9fafb;">
        <td style="padding:10px 14px;color:#6b7280;font-size:13px;
        width:40%;border-bottom:1px solid #e5e7eb;">Product</td>
        <td style="padding:10px 14px;color:#111827;font-weight:600;
        font-size:13px;border-bottom:1px solid #e5e7eb;">{product}</td>
        </tr>
        <tr>
        <td style="padding:10px 14px;color:#6b7280;font-size:13px;
        border-bottom:1px solid #e5e7eb;">Defect</td>
        <td style="padding:10px 14px;color:#111827;font-weight:600;
        font-size:13px;border-bottom:1px solid #e5e7eb;">{defect}</td>
        </tr>
        <tr style="background:#f9fafb;">
        <td style="padding:10px 14px;color:#6b7280;font-size:13px;
        border-bottom:1px solid #e5e7eb;">Priority</td>
        <td style="padding:10px 14px;font-weight:700;font-size:13px;
        color:{pcolor};border-bottom:1px solid #e5e7eb;">{priority}</td>
        </tr>
        <tr>
        <td style="padding:10px 14px;color:#6b7280;font-size:13px;">
        SLA</td>
        <td style="padding:10px 14px;color:#111827;font-weight:600;
        font-size:13px;">{sla_text}</td>
        </tr></table></div>
        <div style="background:#f9fafb;padding:20px;text-align:center;
        border-top:1px solid #e5e7eb;">
        <p style="color:#9ca3af;font-size:12px;margin:0;">
        Automated email from FQCMS. Do not reply.</p>
        </div></div></body></html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"✅ Claim Received — {ticket_number} | FQCMS"
        msg["From"]    = gmail
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                               context=context) as server:
            server.login(gmail, app_pass)
            server.sendmail(gmail, to_email, msg.as_string())
        return True, "Email sent."
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════
# CLOUDINARY
# ══════════════════════════════════════════════════════════

def upload_to_cloudinary(file, ticket_number, file_type="photo"):
    try:
        folder   = f"FQCMS/{ticket_number}"
        resource = "video" if file_type == "video" else "image"
        result   = cloudinary.uploader.upload(
            file,
            folder          = folder,
            resource_type   = resource,
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
        return None, "Please enter both username and password."
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
            return None, "Account disabled. Contact admin."
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
        return None, f"Login error: {str(e)}"


# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════

def show_sidebar(user):
    role = user["role_name"]
    role_colors = {
        "Admin":             "#ef4444",
        "Quality Manager":   "#f59e0b",
        "Quality Executive": "#10b981",
        "Customer":          "#4f8ef7",
    }
    color = role_colors.get(role, "#ffffff")
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 8px 8px 8px;text-align:center;'>
            <div style='font-size:36px;'>🍋</div>
            <div style='color:#ffffff;font-weight:700;
                        font-size:18px;margin-top:4px;'>FQCMS</div>
            <div style='color:#8892a4;font-size:11px;'>
                Fruit Quality Claims</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown(f"""
        <div style='padding:10px;background:rgba(255,255,255,0.04);
                    border-radius:8px;margin-bottom:12px;'>
            <div style='color:#ffffff;font-weight:600;
                        font-size:13px;'>👤 {user['full_name']}</div>
            <div style='color:{color};font-size:11px;
                        margin-top:2px;'>● {role}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style='color:#8892a4;font-size:11px;font-weight:600;
                    text-transform:uppercase;letter-spacing:1px;
                    padding:4px 0 8px 0;'>Navigation</div>
        """, unsafe_allow_html=True)

        if st.button("🏠  Home Dashboard", key="nav_home"):
            st.session_state.current_page    = "dashboard"
            st.session_state.claim_submitted = False
            st.rerun()
        if st.button("📋  Submit a Claim", key="nav_claim"):
            st.session_state.current_page    = "claim_portal"
            st.session_state.claim_submitted = False
            st.rerun()
        if role in ["Admin","Quality Manager","Quality Executive"]:
            if st.button("🎫  Helpdesk Board", key="nav_helpdesk"):
                st.session_state.current_page = "helpdesk"
                st.rerun()
        if role in ["Admin","Quality Executive"]:
            if st.button("🔬  Investigations", key="nav_invest"):
                st.session_state.current_page = "investigations"
                st.rerun()
        if role in ["Admin","Quality Manager","Quality Executive"]:
            if st.button("💰  Settlements", key="nav_settle"):
                st.session_state.current_page = "settlements"
                st.rerun()
        if role in ["Admin","Quality Manager"]:
            if st.button("📊  Dashboard", key="nav_mgmt"):
                st.session_state.current_page = "mgmt_dashboard"
                st.rerun()
        if role == "Admin":
            if st.button("⚙️  Admin Settings", key="nav_admin"):
                st.session_state.current_page = "admin"
                st.rerun()
        st.divider()
        if st.button("🚪  Logout", key="nav_logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
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
        "Customer":          "#4f8ef7",
    }
    color = role_colors.get(role, "#ffffff")
    st.markdown(f"""
    <div style='background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                border-left:4px solid {color};
                border-radius:12px;padding:24px 28px;
                margin-bottom:24px;'>
        <h2 style='color:#ffffff;margin:0 0 6px 0;'>
            Good day, {user['full_name']}! 👋</h2>
        <p style='color:#8892a4;margin:0;font-size:14px;'>
            Logged in as
            <span style='color:{color};font-weight:600;'>{role}</span>
            &nbsp;·&nbsp; {user['email']}</p>
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
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, clr in [
        (c1, "📋 Total Claims",  total,  "#4f8ef7"),
        (c2, "🔴 Open Claims",   open_c, "#ef4444"),
        (c3, "✅ Closed Claims", closed, "#10b981"),
        (c4, "📦 Modules",       "7",    "#f59e0b"),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.04);
                        border:1px solid rgba(255,255,255,0.08);
                        border-top:3px solid {clr};
                        border-radius:10px;padding:20px;
                        text-align:center;'>
                <div style='font-size:28px;font-weight:700;
                            color:{clr};'>{value}</div>
                <div style='font-size:12px;color:#8892a4;
                            margin-top:4px;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <h4 style='color:#ffffff;margin-bottom:16px;'>
        📌 Quick Actions</h4>
    """, unsafe_allow_html=True)

    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.04);
                    border:1px solid rgba(255,255,255,0.08);
                    border-radius:10px;padding:18px;margin-bottom:8px;'>
            <div style='font-size:28px;'>📋</div>
            <div style='color:#ffffff;font-weight:600;font-size:14px;
                        margin-top:8px;'>Submit a Claim</div>
            <div style='color:#8892a4;font-size:12px;margin-top:4px;'>
                Lodge a quality complaint</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Claim Form →", key="qa_claim",
                     use_container_width=True):
            st.session_state.current_page    = "claim_portal"
            st.session_state.claim_submitted = False
            st.rerun()
    with qa2:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.04);
                    border:1px solid rgba(255,255,255,0.08);
                    border-radius:10px;padding:18px;margin-bottom:8px;'>
            <div style='font-size:28px;'>🎫</div>
            <div style='color:#ffffff;font-weight:600;font-size:14px;
                        margin-top:8px;'>Helpdesk Board</div>
            <div style='color:#8892a4;font-size:12px;margin-top:4px;'>
                View all tickets</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Helpdesk →", key="qa_helpdesk",
                     use_container_width=True):
            st.session_state.current_page = "helpdesk"
            st.rerun()
    with qa3:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.04);
                    border:1px solid rgba(255,255,255,0.08);
                    border-radius:10px;padding:18px;margin-bottom:8px;'>
            <div style='font-size:28px;'>📊</div>
            <div style='color:#ffffff;font-weight:600;font-size:14px;
                        margin-top:8px;'>Dashboard</div>
            <div style='color:#8892a4;font-size:12px;margin-top:4px;'>
                KPI reports</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Dashboard →", key="qa_dash",
                     use_container_width=True):
            st.session_state.current_page = "mgmt_dashboard"
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
    """, (claim_id, filename, public_id, file_type,
          mime_type, size, public_id, url))
    conn.commit()
    conn.close()

def submit_claim(data):
    from datetime import datetime, timedelta
    conn    = get_connection()
    cursor  = conn.cursor()
    ticket  = generate_ticket_number()
    sla_map = {"Critical":(2,24),"Major":(4,48),"Minor":(8,72)}
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
        data   = st.session_state.get("submitted_data", {})
        pcolors = {"Critical":"#ef4444","Major":"#f59e0b","Minor":"#10b981"}
        pcolor  = pcolors.get(data.get("priority","Minor"),"#10b981")
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#10b98115,#059f4615);
                    border:2px solid #10b981;border-radius:16px;
                    padding:40px;text-align:center;margin:24px 0;'>
            <div style='font-size:56px;'>✅</div>
            <div style='color:#8892a4;font-size:13px;font-weight:600;
                        text-transform:uppercase;letter-spacing:1px;
                        margin-top:12px;'>Claim Submitted Successfully</div>
            <div style='font-size:40px;font-weight:700;color:#10b981;
                        letter-spacing:3px;margin:16px 0;'>
                {st.session_state.ticket_number}</div>
            <div style='color:#8892a4;font-size:14px;'>
                Save this ticket number for future reference</div>
            <div style='margin-top:20px;font-size:14px;'>
                <span style='color:#8892a4;'>Product:</span>
                <span style='color:#fff;font-weight:600;'>
                    &nbsp;{data.get("product_name","")}</span>
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span style='color:#8892a4;'>Priority:</span>
                <span style='color:{pcolor};font-weight:600;'>
                    &nbsp;{data.get("priority","")}</span>
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span style='color:#8892a4;'>Status:</span>
                <span style='color:#4f8ef7;font-weight:600;'>
                    &nbsp;New</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if data.get("email_sent"):
            st.success(f"📧 Confirmation email sent to {data.get('email')}")
        else:
            st.warning("📧 Email could not be sent. "
                       "Save your ticket number manually.")
        if data.get("uploaded_files"):
            st.markdown("""
            <div style='background:rgba(79,142,247,0.08);
                        border:1px solid rgba(79,142,247,0.2);
                        border-radius:10px;padding:16px;margin:16px 0;'>
                <div style='color:#4f8ef7;font-weight:600;
                            margin-bottom:8px;'>📎 Uploaded Files</div>
            """, unsafe_allow_html=True)
            for f in data["uploaded_files"]:
                st.markdown(f"✅ {f}")
            st.markdown("</div>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📋 Submit Another Claim",
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
    <div style='padding:8px 0 20px 0;'>
        <h2 style='color:#ffffff;margin:0;'>📋 Submit a Quality Claim</h2>
        <p style='color:#8892a4;margin:6px 0 0 0;font-size:14px;'>
            Fill in all fields marked * to lodge a complaint.</p>
    </div>
    """, unsafe_allow_html=True)

    customers    = get_customers()
    products     = get_products()
    cust_options = {
        f"{c['customer_code']} — {c['customer_name']}": c["id"]
        for c in customers
    }
    prod_options = {p["name"]: p["id"] for p in products}

    st.markdown("<div class='section-header'>🍋 Product & Defect</div>",
                unsafe_allow_html=True)
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
    st.markdown("""
    <p style='color:#8892a4;font-size:13px;margin-bottom:8px;'>
        Upload photos or videos of the defect.
        Photos: JPG, PNG (max 10MB) · Videos: MP4, MOV (max 50MB)
    </p>
    """, unsafe_allow_html=True)
    uploaded_photos = st.file_uploader(
        "Upload Photos",
        type=["jpg","jpeg","png","heic"],
        accept_multiple_files=True,
        key="photo_uploader"
    )
    uploaded_videos = st.file_uploader(
        "Upload Videos",
        type=["mp4","mov"],
        accept_multiple_files=True,
        key="video_uploader"
    )
    if uploaded_photos:
        st.markdown(f"""
        <div style='color:#10b981;font-size:13px;margin:8px 0;'>
            ✅ {len(uploaded_photos)} photo(s) ready
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(min(len(uploaded_photos), 4))
        for i, photo in enumerate(uploaded_photos[:4]):
            with cols[i]:
                st.image(photo, width=120)
    if uploaded_videos:
        st.markdown(f"""
        <div style='color:#10b981;font-size:13px;margin:8px 0;'>
            ✅ {len(uploaded_videos)} video(s) ready
        </div>
        """, unsafe_allow_html=True)

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
                                         placeholder="Your full name")
        with c2:
            email  = st.text_input("Email Address *",
                                   placeholder="your@email.com")
            mobile = st.text_input("Mobile Number *",
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
            qty_received = st.number_input("Quantity Received *",
                                           min_value=0.0, step=0.5,
                                           format="%.1f")
        with c7:
            qty_claimed = st.number_input("Quantity Claimed *",
                                          min_value=0.0, step=0.5,
                                          format="%.1f")
        with c8:
            priority = st.selectbox("Priority *",
                                    ["Minor","Major","Critical"])

        st.markdown(
            "<div class='section-header'>📝 Defect Description</div>",
            unsafe_allow_html=True
        )
        description = st.text_area(
            "Describe the defect in detail *",
            placeholder="Describe the quality issue clearly...",
            height=130
        )

        st.markdown(
            "<div class='section-header'>ℹ️ SLA Guide</div>",
            unsafe_allow_html=True
        )
        g1, g2, g3 = st.columns(3)
        with g1:
            st.markdown("""
            <div style='background:rgba(239,68,68,0.08);
                border:1px solid rgba(239,68,68,0.3);
                border-radius:8px;padding:12px;'>
                <div style='color:#ef4444;font-weight:700;'>
                    🔴 Critical</div>
                <div style='color:#8892a4;font-size:12px;margin-top:4px;'>
                    Response: 2h · Resolution: 24h</div>
            </div>
            """, unsafe_allow_html=True)
        with g2:
            st.markdown("""
            <div style='background:rgba(245,158,11,0.08);
                border:1px solid rgba(245,158,11,0.3);
                border-radius:8px;padding:12px;'>
                <div style='color:#f59e0b;font-weight:700;'>
                    🟡 Major</div>
                <div style='color:#8892a4;font-size:12px;margin-top:4px;'>
                    Response: 4h · Resolution: 48h</div>
            </div>
            """, unsafe_allow_html=True)
        with g3:
            st.markdown("""
            <div style='background:rgba(16,185,129,0.08);
                border:1px solid rgba(16,185,129,0.3);
                border-radius:8px;padding:12px;'>
                <div style='color:#10b981;font-weight:700;'>
                    🟢 Minor</div>
                <div style='color:#8892a4;font-size:12px;margin-top:4px;'>
                    Response: 8h · Resolution: 72h</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "🚀 Submit Quality Claim", use_container_width=True
        )

        if submitted:
            errors = []
            if not contact_name.strip():
                errors.append("Contact Person name is required.")
            if not email.strip() or "@" not in email:
                errors.append("Valid email address is required.")
            if not mobile.strip() or len(mobile.strip()) < 10:
                errors.append("Valid 10-digit mobile number is required.")
            if not invoice_number.strip():
                errors.append("Invoice Number is required.")
            if qty_claimed <= 0:
                errors.append("Quantity Claimed must be greater than 0.")
            if qty_claimed > qty_received:
                errors.append("Claimed cannot exceed Received.")
            if not description.strip():
                errors.append("Defect Description is required.")

            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                with st.spinner("Submitting your claim..."):
                    ticket, claim_id, error = submit_claim({
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
                        st.error(f"❌ Submission failed: {error}")
                    else:
                        uploaded_names = []
                        all_files = []
                        if uploaded_photos:
                            for f in uploaded_photos:
                                all_files.append((f,"photo"))
                        if uploaded_videos:
                            for f in uploaded_videos:
                                all_files.append((f,"video"))
                        for f, ftype in all_files:
                            url, pub_id = upload_to_cloudinary(
                                f, ticket, ftype)
                            if url:
                                save_attachment(
                                    claim_id, f.name, ftype,
                                    f.type, f.size, url, pub_id)
                                uploaded_names.append(f.name)
                        email_sent, _ = send_confirmation_email(
                            to_email      = email.strip(),
                            customer_name = contact_name.strip(),
                            ticket_number = ticket,
                            product       = sel_prod,
                            defect        = sel_defect,
                            priority      = priority
                        )
                        st.session_state.claim_submitted = True
                        st.session_state.ticket_number   = ticket
                        st.session_state.submitted_data  = {
                            "product_name":   sel_prod,
                            "priority":       priority,
                            "email":          email.strip(),
                            "email_sent":     email_sent,
                            "uploaded_files": uploaded_names,
                        }
                        st.rerun()


# ══════════════════════════════════════════════════════════
# HELPDESK HELPERS
# ══════════════════════════════════════════════════════════

def get_priority_color(priority):
    return {
        "Critical": "#ef4444",
        "Major":    "#f59e0b",
        "Minor":    "#10b981"
    }.get(priority, "#8892a4")

def get_status_color(status):
    return {
        "New":              "#4f8ef7",
        "Assigned":         "#8b5cf6",
        "Investigation":    "#f59e0b",
        "Pending Approval": "#f97316",
        "Resolved":         "#10b981",
        "Closed":           "#6b7280",
    }.get(status, "#8892a4")

def get_ageing(created_at):
    from datetime import datetime
    try:
        created = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
        delta   = datetime.now() - created
        days    = delta.days
        hours   = delta.seconds // 3600
        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h {(delta.seconds % 3600)//60}m"
    except Exception:
        return "N/A"

def get_sla_status(resolution_due, status):
    from datetime import datetime
    if status in ("Resolved","Closed"):
        return "ok"
    try:
        due  = datetime.strptime(resolution_due[:19], "%Y-%m-%d %H:%M:%S")
        diff = (due - datetime.now()).total_seconds()
        if diff < 0:
            return "breached"
        if diff < 3600 * 4:
            return "warning"
        return "ok"
    except Exception:
        return "ok"

def update_claim_status(claim_id, new_status, user_id):
    from datetime import datetime
    conn = get_connection()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    old  = conn.execute(
        "SELECT status FROM claims WHERE id=?", (claim_id,)
    ).fetchone()
    old_status = old["status"] if old else ""
    conn.execute(
        "UPDATE claims SET status=?, updated_at=? WHERE id=?",
        (new_status, now, claim_id)
    )
    if new_status == "Resolved":
        conn.execute(
            "UPDATE claims SET resolved_at=? WHERE id=?",
            (now, claim_id)
        )
    if new_status == "Closed":
        conn.execute(
            "UPDATE claims SET closed_at=? WHERE id=?",
            (now, claim_id)
        )
    conn.execute("""
        INSERT INTO audit_logs
        (claim_id,user_id,action,entity_type,entity_id,old_value,new_value)
        VALUES (?,?,'STATUS_CHANGE','claim',?,?,?)
    """, (claim_id, user_id, claim_id, old_status, new_status))
    conn.commit()
    conn.close()

def assign_claim(claim_id, assignee_id, user_id):
    from datetime import datetime
    conn = get_connection()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE claims
        SET assigned_to_id=?, assigned_at=?,
            status=CASE WHEN status='New' THEN 'Assigned' ELSE status END,
            updated_at=?
        WHERE id=?
    """, (assignee_id, now, now, claim_id))
    conn.execute("""
        INSERT INTO audit_logs
        (claim_id,user_id,action,entity_type,entity_id,new_value)
        VALUES (?,?,'ASSIGNMENT','claim',?,?)
    """, (claim_id, user_id, claim_id, str(assignee_id)))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════
# HELPDESK KANBAN BOARD
# ══════════════════════════════════════════════════════════

def show_helpdesk(user):
    role = user["role_name"]
    st.markdown("""
    <div style='padding:8px 0 20px 0;'>
        <h2 style='color:#ffffff;margin:0;'>🎫 Helpdesk Board</h2>
        <p style='color:#8892a4;margin:6px 0 0 0;font-size:14px;'>
            Manage and track all quality claims.</p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        filter_product = st.selectbox(
            "Filter by Product",
            ["All Products","Banana","Pomegranate","Arils"],
            key="hd_product"
        )
    with f2:
        filter_priority = st.selectbox(
            "Filter by Priority",
            ["All Priorities","Critical","Major","Minor"],
            key="hd_priority"
        )
    with f3:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All Status","New","Assigned","Investigation",
             "Pending Approval","Resolved","Closed"],
            key="hd_status"
        )
    with f4:
        search_term = st.text_input(
            "Search",
            placeholder="Ticket / Customer",
            key="hd_search"
        )

    conn   = get_connection()
    query  = """
        SELECT c.id, c.ticket_number, c.status, c.priority,
               c.created_at, c.updated_at,
               c.sla_response_due_at, c.sla_resolution_due_at,
               cu.customer_name, p.name as product_name,
               dt.name as defect_name,
               u.full_name as assigned_to,
               c.defect_description, c.quantity_claimed,
               c.quantity_unit, c.submitted_by_name,
               c.submitted_by_email
        FROM claims c
        JOIN customers cu  ON c.customer_id   = cu.id
        JOIN products  p   ON c.product_id    = p.id
        JOIN defect_types dt ON c.defect_type_id = dt.id
        LEFT JOIN users u  ON c.assigned_to_id = u.id
        WHERE 1=1
    """
    params = []
    if filter_product != "All Products":
        query += " AND p.name=?"
        params.append(filter_product)
    if filter_priority != "All Priorities":
        query += " AND c.priority=?"
        params.append(filter_priority)
    if filter_status != "All Status":
        query += " AND c.status=?"
        params.append(filter_status)
    if search_term:
        query += " AND (c.ticket_number LIKE ? OR cu.customer_name LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    query += " ORDER BY c.created_at DESC"
    claims = conn.execute(query, params).fetchall()

    executives = conn.execute("""
        SELECT u.id, u.full_name FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE r.name IN ('Quality Executive','Quality Manager','Admin')
        AND u.is_active=1
    """).fetchall()
    conn.close()

    exec_options = {"Unassigned": None}
    exec_options.update({e["full_name"]: e["id"] for e in executives})

    total    = len(claims)
    new_c    = sum(1 for c in claims if c["status"] == "New")
    open_c   = sum(1 for c in claims
                   if c["status"] not in ("Resolved","Closed"))
    closed_c = sum(1 for c in claims
                   if c["status"] in ("Resolved","Closed"))

    s1, s2, s3, s4 = st.columns(4)
    for col, label, value, clr in [
        (s1, "Total",   total,    "#4f8ef7"),
        (s2, "New",     new_c,    "#ef4444"),
        (s3, "Open",    open_c,   "#f59e0b"),
        (s4, "Closed",  closed_c, "#10b981"),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.04);
                        border:1px solid rgba(255,255,255,0.08);
                        border-top:3px solid {clr};
                        border-radius:10px;padding:14px;
                        text-align:center;margin-bottom:16px;'>
                <div style='font-size:24px;font-weight:700;
                            color:{clr};'>{value}</div>
                <div style='font-size:11px;color:#8892a4;
                            margin-top:2px;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    if not claims:
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;'>
            <div style='font-size:48px;'>🎫</div>
            <h3 style='color:#ffffff;margin:16px 0 8px 0;'>
                No Claims Found</h3>
            <p style='color:#8892a4;'>
                No claims match your filters.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    view_mode = st.radio(
        "View Mode",
        ["📋 List View", "🗂️ Kanban View"],
        horizontal=True,
        key="hd_view_mode"
    )

    if view_mode == "🗂️ Kanban View":
        show_kanban(claims)
    else:
        show_list_view(claims, role, exec_options)


def show_kanban(claims):
    statuses = [
        ("New",              "#4f8ef7"),
        ("Assigned",         "#8b5cf6"),
        ("Investigation",    "#f59e0b"),
        ("Pending Approval", "#f97316"),
        ("Resolved",         "#10b981"),
        ("Closed",           "#6b7280"),
    ]
    cols = st.columns(len(statuses))
    for col, (status, color) in zip(cols, statuses):
        status_claims = [c for c in claims if c["status"] == status]
        with col:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.04);
                        border:1px solid rgba(255,255,255,0.08);
                        border-top:3px solid {color};
                        border-radius:10px;padding:10px;
                        margin-bottom:8px;'>
                <div style='color:{color};font-weight:700;
                            font-size:12px;text-transform:uppercase;
                            letter-spacing:0.5px;'>{status}</div>
                <div style='color:#8892a4;font-size:11px;'>
                    {len(status_claims)} ticket(s)</div>
            </div>
            """, unsafe_allow_html=True)
            for claim in status_claims:
                pcolor  = get_priority_color(claim["priority"])
                ageing  = get_ageing(claim["created_at"])
                sla_st  = get_sla_status(
                    claim["sla_resolution_due_at"] or "",
                    claim["status"]
                )
                sla_icon = (
                    "🔴" if sla_st == "breached" else
                    "🟡" if sla_st == "warning"  else "🟢"
                )
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.05);
                            border:1px solid rgba(255,255,255,0.1);
                            border-left:3px solid {pcolor};
                            border-radius:8px;padding:10px;
                            margin-bottom:8px;'>
                    <div style='color:#4f8ef7;font-size:11px;
                                font-weight:700;'>
                        {claim["ticket_number"]}</div>
                    <div style='color:#ffffff;font-size:12px;
                                font-weight:600;margin:4px 0;'>
                        {claim["customer_name"]}</div>
                    <div style='color:#8892a4;font-size:11px;'>
                        {claim["product_name"]}</div>
                    <div style='display:flex;justify-content:space-between;
                                margin-top:6px;font-size:10px;'>
                        <span style='color:{pcolor};font-weight:600;'>
                            {claim["priority"]}</span>
                        <span style='color:#8892a4;'>⏱ {ageing}</span>
                        <span>{sla_icon}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def show_list_view(claims, role, exec_options):
    status_options = [
        "New","Assigned","Investigation",
        "Pending Approval","Resolved","Closed"
    ]
    for claim in claims:
        pcolor  = get_priority_color(claim["priority"])
        scolor  = get_status_color(claim["status"])
        ageing  = get_ageing(claim["created_at"])
        sla_st  = get_sla_status(
            claim["sla_resolution_due_at"] or "",
            claim["status"]
        )
        sla_color = (
            "#ef4444" if sla_st == "breached" else
            "#f59e0b" if sla_st == "warning"  else "#10b981"
        )
        sla_label = (
            "⚠️ SLA Breached" if sla_st == "breached" else
            "⚡ SLA Warning"  if sla_st == "warning"  else
            "✅ SLA OK"
        )
        with st.expander(
            f"🎫 {claim['ticket_number']}  |  "
            f"{claim['customer_name']}  |  "
            f"{claim['product_name']}  |  "
            f"{claim['status']}  |  Age: {ageing}"
        ):
            d1, d2 = st.columns([2,1])
            with d1:
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03);
                            border:1px solid rgba(255,255,255,0.08);
                            border-radius:10px;padding:16px;'>
                    <div style='display:flex;gap:8px;
                                flex-wrap:wrap;margin-bottom:12px;'>
                        <span style='background:{pcolor}20;color:{pcolor};
                                     padding:3px 10px;border-radius:20px;
                                     font-size:11px;font-weight:700;
                                     border:1px solid {pcolor}40;'>
                            {claim["priority"]}</span>
                        <span style='background:{scolor}20;color:{scolor};
                                     padding:3px 10px;border-radius:20px;
                                     font-size:11px;font-weight:700;
                                     border:1px solid {scolor}40;'>
                            {claim["status"]}</span>
                        <span style='background:{sla_color}20;
                                     color:{sla_color};padding:3px 10px;
                                     border-radius:20px;font-size:11px;
                                     font-weight:600;border:1px solid
                                     {sla_color}40;'>
                            {sla_label}</span>
                    </div>
                    <table style='width:100%;font-size:13px;'>
                        <tr><td style='color:#8892a4;padding:4px 0;
                            width:40%;'>Customer</td>
                            <td style='color:#fff;font-weight:600;'>
                            {claim["customer_name"]}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Contact</td>
                            <td style='color:#fff;'>
                            {claim["submitted_by_name"]} ·
                            {claim["submitted_by_email"]}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Product</td>
                            <td style='color:#fff;'>
                            {claim["product_name"]}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Defect</td>
                            <td style='color:#fff;'>
                            {claim["defect_name"]}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Quantity</td>
                            <td style='color:#fff;'>
                            Claimed {claim["quantity_claimed"]}
                            {claim["quantity_unit"]}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Assigned To</td>
                            <td style='color:#fff;'>
                            {claim["assigned_to"] or "Unassigned"}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Submitted</td>
                            <td style='color:#fff;'>
                            {claim["created_at"][:16]}</td></tr>
                        <tr><td style='color:#8892a4;padding:4px 0;'>
                            Ageing</td>
                            <td style='color:#f59e0b;font-weight:600;'>
                            {ageing}</td></tr>
                    </table>
                    <div style='margin-top:12px;padding:10px;
                                background:rgba(255,255,255,0.03);
                                border-radius:8px;'>
                        <div style='color:#8892a4;font-size:11px;
                                    margin-bottom:4px;'>
                            DEFECT DESCRIPTION</div>
                        <div style='color:#fff;font-size:13px;'>
                            {claim["defect_description"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with d2:
                st.markdown("""
                <div style='background:rgba(255,255,255,0.03);
                            border:1px solid rgba(255,255,255,0.08);
                            border-radius:10px;padding:16px;'>
                    <div style='color:#4f8ef7;font-weight:600;
                                font-size:13px;margin-bottom:12px;'>
                        ⚡ Actions</div>
                """, unsafe_allow_html=True)

                if role in ["Admin","Quality Manager","Quality Executive"]:
                    new_status = st.selectbox(
                        "Update Status",
                        status_options,
                        index=status_options.index(claim["status"]),
                        key=f"status_{claim['id']}"
                    )
                    if st.button("💾 Save Status",
                                 key=f"save_{claim['id']}",
                                 use_container_width=True):
                        if new_status != claim["status"]:
                            update_claim_status(
                                claim["id"], new_status,
                                st.session_state.user["id"]
                            )
                            st.success(f"✅ Updated to {new_status}")
                            st.rerun()
                        else:
                            st.info("No change.")

                    st.markdown("<br>", unsafe_allow_html=True)

                    assignee = st.selectbox(
                        "Assign To",
                        list(exec_options.keys()),
                        key=f"assign_{claim['id']}"
                    )
                    if st.button("👤 Assign",
                                 key=f"do_assign_{claim['id']}",
                                 use_container_width=True):
                        assign_claim(
                            claim["id"],
                            exec_options[assignee],
                            st.session_state.user["id"]
                        )
                        st.success(f"✅ Assigned to {assignee}")
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# COMING SOON
# ══════════════════════════════════════════════════════════

def show_coming_soon(title, icon):
    st.markdown(f"""
    <div style='text-align:center;padding:80px 20px;'>
        <div style='font-size:64px;'>{icon}</div>
        <h2 style='color:#ffffff;margin:16px 0 8px 0;'>{title}</h2>
        <p style='color:#8892a4;font-size:15px;'>
            This module is being built. Coming very soon!</p>
        <div style='background:rgba(79,142,247,0.08);
                    border:1px solid rgba(79,142,247,0.2);
                    border-radius:10px;padding:16px;
                    display:inline-block;margin-top:24px;'>
            <span style='color:#4f8ef7;font-size:13px;'>
                🔧 Under Construction</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════

def show_login_page():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:20px 0 30px 0;'>
            <div style='font-size:52px;'>🍋</div>
            <p style='font-size:28px;font-weight:700;color:#ffffff;
                      margin:8px 0 0 0;'>FQCMS</p>
            <p style='font-size:14px;color:#8892a4;margin:4px 0 0 0;'>
                Fruit Quality Claim Management System</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username",
                                     placeholder="Enter your username")
            password = st.text_input("Password", type="password",
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
        <div style='background:rgba(79,142,247,0.08);
                    border:1px solid rgba(79,142,247,0.2);
                    border-radius:10px;padding:16px;margin-top:16px;'>
            <div style='color:#4f8ef7;font-size:12px;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.5px;
                        margin-bottom:10px;'>
                🔑 Demo Credentials — Password: Admin@1234</div>
            <div style='color:#8892a4;font-size:13px;line-height:2.2;'>
                <span style='color:#fff;font-weight:600;'>admin</span>
                &nbsp;→ System Administrator<br>
                <span style='color:#fff;font-weight:600;'>qmanager</span>
                &nbsp;→ Quality Manager<br>
                <span style='color:#fff;font-weight:600;'>qexec1</span>
                &nbsp;→ Quality Executive<br>
                <span style='color:#fff;font-weight:600;'>customer1</span>
                &nbsp;→ Demo Customer
            </div>
        </div>
        <p style='text-align:center;color:#8892a4;font-size:11px;
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
        show_coming_soon("Investigations", "🔬")
    elif page == "settlements":
        show_coming_soon("Settlements", "💰")
    elif page == "mgmt_dashboard":
        show_coming_soon("Management Dashboard", "📊")
    elif page == "admin":
        show_coming_soon("Admin Settings", "⚙️")
    else:
        show_dashboard(user)
