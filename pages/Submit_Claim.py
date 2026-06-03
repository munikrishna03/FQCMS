# ============================================================
# FQCMS - Public Customer Claim Submission Form
# pages/Submit_Claim.py
# No login required — share this URL with customers
# ============================================================

import streamlit as st
import cloudinary
import cloudinary.uploader
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from database.connection import init_database, get_connection

st.set_page_config(
    page_title="Submit a Quality Claim - FQCMS",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_database()

cloudinary.config(
    cloud_name = st.secrets.get("CLOUDINARY_CLOUD_NAME",""),
    api_key    = st.secrets.get("CLOUDINARY_API_KEY",""),
    api_secret = st.secrets.get("CLOUDINARY_API_SECRET",""),
    secure     = True
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}
.stDeployButton {display: none;}

.stApp {
    background: #f1f5f9 !important;
}
[data-testid="stMainBlockContainer"] {
    background: #f1f5f9 !important;
}
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
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
}
.stButton > button {
    background: linear-gradient(
        135deg,#3b82f6,#6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px
        rgba(59,130,246,0.35) !important;
}
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
</style>
""", unsafe_allow_html=True)

if "pub_submitted" not in st.session_state:
    st.session_state.pub_submitted = False
if "pub_ticket" not in st.session_state:
    st.session_state.pub_ticket    = None
if "pub_data" not in st.session_state:
    st.session_state.pub_data      = {}


def get_products():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id,name FROM products "
        "WHERE is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return rows

def get_defects(product_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id,name FROM defect_types "
        "WHERE product_id=? AND is_active=1 "
        "ORDER BY name", (product_id,)
    ).fetchall()
    conn.close()
    return rows

def get_customers():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id,customer_code,customer_name "
        "FROM customers WHERE is_active=1 "
        "ORDER BY customer_name"
    ).fetchall()
    conn.close()
    return rows

def generate_ticket_number():
    conn = get_connection()
    conn.execute(
        "UPDATE ticket_counter "
        "SET last_value=last_value+1 WHERE id=1"
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
            claim_id,original_filename,
            stored_filename,file_type,mime_type,
            file_size_bytes,gdrive_file_id,
            gdrive_view_url
        ) VALUES (?,?,?,?,?,?,?,?)
    """, (claim_id,filename,public_id,file_type,
          mime_type,size,public_id,url))
    conn.commit()
    conn.close()

def submit_claim(data):
    conn    = get_connection()
    cursor  = conn.cursor()
    ticket  = generate_ticket_number()
    sla_map = {
        "Critical":(2,24),
        "Major":(4,48),
        "Minor":(8,72)
    }
    rh,resh  = sla_map[data["priority"]]
    now      = datetime.now()
    r_due    = (now+timedelta(hours=rh)).strftime(
        "%Y-%m-%d %H:%M:%S")
    res_due  = (now+timedelta(hours=resh)).strftime(
        "%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO claims (
                ticket_number,customer_id,product_id,
                defect_type_id,invoice_number,
                invoice_date,quantity_received,
                quantity_claimed,quantity_unit,
                defect_description,priority,status,
                sla_response_due_at,
                sla_resolution_due_at,
                submitted_by_name,submitted_by_email,
                submitted_by_mobile
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,
                      'New',?,?,?,?,?)
        """, (
            ticket,data["customer_id"],
            data["product_id"],
            data["defect_type_id"],
            data["invoice_number"],
            data["invoice_date"],
            data["quantity_received"],
            data["quantity_claimed"],
            data["quantity_unit"],
            data["defect_description"],
            data["priority"],
            r_due,res_due,
            data["contact_name"],
            data["email"],data["mobile"],
        ))
        cid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO sla_tracking "
            "(claim_id,priority,response_due_at,"
            "resolution_due_at) VALUES (?,?,?,?)",
            (cid,data["priority"],r_due,res_due))
        cursor.execute(
            "INSERT INTO audit_logs "
            "(claim_id,action,entity_type,"
            "entity_id,new_value) VALUES "
            "(?,'CLAIM_CREATED','claim',?,?)",
            (cid,cid,ticket))
        conn.commit()
        conn.close()
        return ticket, cid, None
    except Exception as e:
        conn.rollback()
        conn.close()
        return None, None, str(e)

def upload_file(file, ticket_number,
                file_type="photo"):
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=f"FQCMS/{ticket_number}",
            resource_type=(
                "video" if file_type=="video"
                else "image"),
            use_filename=True,
            unique_filename=True,
        )
        return (result.get("secure_url"),
                result.get("public_id"))
    except Exception as e:
        return None, str(e)

def send_email(to_email, customer_name,
               ticket_number, product,
               defect, priority,
               claim_value_inr):
    try:
        gmail    = st.secrets.get("GMAIL_ADDRESS","")
        app_pass = st.secrets.get(
            "GMAIL_APP_PASSWORD","")
        if not gmail or not app_pass:
            return False
        pcolors = {
            "Critical":"#ef4444",
            "Major":"#f59e0b",
            "Minor":"#10b981"
        }
        pcolor  = pcolors.get(priority,"#10b981")
        sla_map = {
            "Critical":
                "Response: 2h | Resolution: 24h",
            "Major":
                "Response: 4h | Resolution: 48h",
            "Minor":
                "Response: 8h | Resolution: 72h",
        }
        value_row = ""
        if claim_value_inr and claim_value_inr > 0:
            value_row = f"""
            <tr><td style="padding:10px;color:#6b7280;
            border-bottom:1px solid #e5e7eb;">
            Claim Value</td>
            <td style="padding:10px;color:#1e293b;
            font-weight:700;
            border-bottom:1px solid #e5e7eb;">
            ₹{claim_value_inr:,.2f}</td></tr>"""

        html = f"""<!DOCTYPE html><html><body
        style="font-family:Arial;background:#f4f4f4;
        padding:20px;">
        <div style="max-width:600px;margin:0 auto;
        background:#fff;border-radius:12px;
        overflow:hidden;">
        <div style="background:linear-gradient(
        135deg,#1e293b,#334155);padding:30px;
        text-align:center;">
        <div style="font-size:36px;">🍋</div>
        <h1 style="color:#fff;margin:8px 0 4px;
        font-size:22px;">FQCMS</h1></div>
        <div style="padding:32px;">
        <h2 style="color:#1e293b;">
        ✅ Claim Received</h2>
        <p style="color:#475569;">Dear <strong>
        {customer_name}</strong>,<br>
        Your quality claim has been received.</p>
        <div style="background:#f0fdf4;
        border:2px solid #10b981;
        border-radius:10px;padding:20px;
        text-align:center;margin:20px 0;">
        <p style="color:#64748b;font-size:12px;
        text-transform:uppercase;margin:0;">
        Ticket Number</p>
        <p style="color:#10b981;font-size:32px;
        font-weight:700;letter-spacing:3px;
        margin:8px 0;">{ticket_number}</p>
        </div>
        <table style="width:100%;
        border-collapse:collapse;">
        <tr><td style="padding:10px;color:#6b7280;
        width:40%;border-bottom:1px solid #e5e7eb;">
        Product</td>
        <td style="padding:10px;color:#1e293b;
        font-weight:600;
        border-bottom:1px solid #e5e7eb;">
        {product}</td></tr>
        <tr><td style="padding:10px;color:#6b7280;
        border-bottom:1px solid #e5e7eb;">
        Defect</td>
        <td style="padding:10px;color:#1e293b;
        font-weight:600;
        border-bottom:1px solid #e5e7eb;">
        {defect}</td></tr>
        <tr><td style="padding:10px;color:#6b7280;
        border-bottom:1px solid #e5e7eb;">
        Priority</td>
        <td style="padding:10px;color:{pcolor};
        font-weight:700;
        border-bottom:1px solid #e5e7eb;">
        {priority}</td></tr>
        {value_row}
        <tr><td style="padding:10px;color:#6b7280;">
        SLA</td>
        <td style="padding:10px;color:#1e293b;">
        {sla_map.get(priority,"")}</td></tr>
        </table></div>
        <div style="background:#f8fafc;padding:16px;
        text-align:center;
        border-top:1px solid #e2e8f0;">
        <p style="color:#94a3b8;font-size:12px;
        margin:0;">Automated email from FQCMS
        </p></div></div></body></html>"""

        msg            = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"✅ Claim {ticket_number} | FQCMS")
        msg["From"]    = gmail
        msg["To"]      = to_email
        msg.attach(MIMEText(html,"html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",465,context=ctx
        ) as s:
            s.login(gmail,app_pass)
            s.sendmail(gmail,to_email,msg.as_string())
        return True
    except Exception:
        return False


def show_success():
    data   = st.session_state.pub_data
    ticket = st.session_state.pub_ticket
    pcolors = {
        "Critical":"#ef4444",
        "Major":"#f59e0b",
        "Minor":"#10b981"
    }
    pcolor = pcolors.get(
        data.get("priority","Minor"),"#10b981")

    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px;'>
        <span style='font-size:32px;'>🍋</span>
        <span style='color:#1e293b;font-weight:700;
                     font-size:20px;margin-left:8px;'>
            FQCMS</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:linear-gradient(
                135deg,#f0fdf4,#dcfce7);
                border:2px solid #10b981;
                border-radius:20px;padding:48px 32px;
                text-align:center;margin:16px auto;
                max-width:600px;'>
        <div style='font-size:64px;'>✅</div>
        <div style='color:#10b981;font-size:13px;
                    font-weight:600;
                    text-transform:uppercase;
                    letter-spacing:2px;
                    margin-top:16px;'>
            Claim Submitted Successfully</div>
        <div style='font-size:44px;font-weight:700;
                    color:#10b981;letter-spacing:4px;
                    margin:16px 0;
                    font-family:monospace;'>
            {ticket}</div>
        <div style='color:#64748b;font-size:14px;'>
            Save this ticket number for reference
        </div>
    </div>
    """, unsafe_allow_html=True)

    _,mid,_ = st.columns([1,2,1])
    with mid:
        value_text = ""
        if data.get("claim_value_inr",0) > 0:
            value_text = (
                f"₹{data['claim_value_inr']:,.2f}")

        st.markdown(f"""
        <div style='background:#ffffff;
                    border:1px solid #e2e8f0;
                    border-radius:12px;padding:20px;
                    margin-bottom:16px;'>
            <div style='color:#64748b;font-size:11px;
                        font-weight:600;
                        text-transform:uppercase;
                        margin-bottom:12px;'>
                Claim Summary</div>
            <table style='width:100%;font-size:13px;'>
            <tr><td style='color:#64748b;padding:6px 0;
                width:45%;'>Customer</td>
                <td style='color:#1e293b;
                    font-weight:600;'>
                {data.get("customer_name","")}</td></tr>
            <tr><td style='color:#64748b;padding:6px 0;'>
                Product</td>
                <td style='color:#1e293b;font-weight:600;'>
                {data.get("product_name","")}</td></tr>
            <tr><td style='color:#64748b;padding:6px 0;'>
                Defect</td>
                <td style='color:#1e293b;'>
                {data.get("defect_name","")}</td></tr>
            <tr><td style='color:#64748b;padding:6px 0;'>
                Priority</td>
                <td style='color:{pcolor};
                    font-weight:700;'>
                {data.get("priority","")}</td></tr>
            <tr><td style='color:#64748b;padding:6px 0;'>
                Qty Claimed</td>
                <td style='color:#1e293b;'>
                {data.get("quantity_claimed","")}
                {data.get("quantity_unit","")}</td></tr>
            {"<tr><td style='color:#64748b;padding:6px 0;'>Claim Value</td><td style='color:#f59e0b;font-weight:700;'>"+value_text+"</td></tr>" if value_text else ""}
            </table>
        </div>
        """, unsafe_allow_html=True)

        if data.get("email_sent"):
            st.success(
                f"📧 Confirmation sent to "
                f"**{data.get('email')}**")
        else:
            st.warning(
                "📧 Could not send email. "
                "Please save ticket number manually.")

        sla_map = {
            "Critical":("2 hours","24 hours"),
            "Major":   ("4 hours","48 hours"),
            "Minor":   ("8 hours","72 hours"),
        }
        resp,resol = sla_map.get(
            data.get("priority","Minor"),
            ("8 hours","72 hours"))
        st.markdown(f"""
        <div style='background:#eff6ff;
                    border:1px solid #bfdbfe;
                    border-radius:10px;padding:16px;
                    margin-top:8px;'>
            <div style='color:#3b82f6;font-weight:600;
                        margin-bottom:8px;'>
                ⏱️ SLA Commitment</div>
            <div style='color:#475569;font-size:13px;'>
                Response within
                <strong>{resp}</strong> ·
                Resolution within
                <strong>{resol}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("📋 Submit Another Claim",
                     use_container_width=True):
            st.session_state.pub_submitted = False
            st.session_state.pub_ticket    = None
            st.session_state.pub_data      = {}
            st.rerun()


def show_form():
    st.markdown("""
    <div style='text-align:center;padding:24px 0 8px;'>
        <div style='font-size:48px;'>🍋</div>
        <h1 style='color:#1e293b;margin:8px 0 4px;
                   font-size:26px;'>
            Submit a Quality Claim</h1>
        <p style='color:#64748b;font-size:14px;margin:0;'>
            Fill in the form below to lodge a
            fruit quality complaint.
        </p>
    </div>
    <hr style='border:none;border-top:1px solid #e2e8f0;
               margin:20px 0;'>
    """, unsafe_allow_html=True)

    customers    = get_customers()
    products     = get_products()
    cust_options = {
        f"{c['customer_code']} — {c['customer_name']}":
        c["id"] for c in customers
    }
    prod_options = {p["name"]:p["id"] for p in products}

    st.markdown(
        "<div class='section-header'>"
        "🍋 Product & Defect Details</div>",
        unsafe_allow_html=True)
    pd1,pd2 = st.columns(2)
    with pd1:
        sel_prod = st.selectbox(
            "Product *",
            list(prod_options.keys()),
            key="pub_product")
    with pd2:
        defect_rows    = get_defects(
            prod_options[sel_prod])
        defect_options = {
            d["name"]:d["id"] for d in defect_rows}
        sel_defect = st.selectbox(
            "Defect Type *",
            list(defect_options.keys()),
            key="pub_defect")

    st.markdown(
        "<div class='section-header'>"
        "📎 Photos & Videos (Optional)</div>",
        unsafe_allow_html=True)
    cu1,cu2 = st.columns(2)
    with cu1:
        uploaded_photos = st.file_uploader(
            "📷 Upload Photos",
            type=["jpg","jpeg","png","heic"],
            accept_multiple_files=True,
            key="pub_photos")
    with cu2:
        uploaded_videos = st.file_uploader(
            "🎥 Upload Videos",
            type=["mp4","mov"],
            accept_multiple_files=True,
            key="pub_videos")
    if uploaded_photos:
        cols = st.columns(min(len(uploaded_photos),5))
        for i,p in enumerate(uploaded_photos[:5]):
            with cols[i]: st.image(p,width=100)

    with st.form("public_claim_form",
                 clear_on_submit=False):
        st.markdown(
            "<div class='section-header'>"
            "👤 Your Information</div>",
            unsafe_allow_html=True)
        r1c1,r1c2 = st.columns(2)
        with r1c1:
            sel_cust = st.selectbox(
                "Your Company *",
                list(cust_options.keys()))
            contact_name = st.text_input(
                "Your Name *",
                placeholder="Full name")
        with r1c2:
            email = st.text_input(
                "Email Address *",
                placeholder="your@email.com")
            mobile = st.text_input(
                "Mobile Number *",
                placeholder="10-digit number")

        st.markdown(
            "<div class='section-header'>"
            "🧾 Invoice Details</div>",
            unsafe_allow_html=True)
        r2c1,r2c2,r2c3 = st.columns(3)
        with r2c1:
            invoice_number = st.text_input(
                "Invoice Number *",
                placeholder="INV-2024-001")
        with r2c2:
            invoice_date = st.date_input(
                "Invoice Date *",
                value=date.today(),
                max_value=date.today())
        with r2c3:
            qty_unit = st.selectbox(
                "Unit",
                ["KG","Box","Carton","Punnet","Piece"])

        st.markdown(
            "<div class='section-header'>"
            "📦 Quantity & Claim Value</div>",
            unsafe_allow_html=True)
        r3c1,r3c2,r3c3,r3c4 = st.columns(4)
        with r3c1:
            qty_received = st.number_input(
                "Qty Received *",
                min_value=0.0,step=0.5,format="%.1f")
        with r3c2:
            qty_claimed = st.number_input(
                "Qty Claimed *",
                min_value=0.0,step=0.5,format="%.1f")
        with r3c3:
            claim_value_inr = st.number_input(
                "Claim Value (₹ INR)",
                min_value=0.0,step=100.0,
                format="%.2f")
        with r3c4:
            priority = st.selectbox(
                "Priority *",
                ["Minor","Major","Critical"])

        st.markdown(
            "<div class='section-header'>"
            "📝 Defect Description</div>",
            unsafe_allow_html=True)
        description = st.text_area(
            "Describe the quality issue *",
            placeholder=(
                "• What defect did you find?\n"
                "• How many units affected?\n"
                "• When did you notice the issue?\n"
                "• Storage and handling conditions?"
            ),
            height=150)

        st.markdown("<br>",unsafe_allow_html=True)
        agree = st.checkbox(
            "I confirm that the information provided "
            "is accurate and complete.")

        st.markdown("<br>",unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "🚀 Submit Quality Claim",
            use_container_width=True)

        if submitted:
            errors = []
            if not agree:
                errors.append(
                    "Please confirm the information "
                    "is accurate.")
            if not contact_name.strip():
                errors.append("Your Name is required.")
            if not email.strip() or "@" not in email:
                errors.append("Valid email required.")
            if not mobile.strip() or \
               len(mobile.strip())<10:
                errors.append(
                    "Valid 10-digit mobile required.")
            if not invoice_number.strip():
                errors.append(
                    "Invoice Number required.")
            if qty_received <= 0:
                errors.append(
                    "Qty Received must be > 0.")
            if qty_claimed <= 0:
                errors.append(
                    "Qty Claimed must be > 0.")
            if qty_claimed > qty_received:
                errors.append(
                    "Qty Claimed cannot exceed "
                    "Qty Received.")
            if not description.strip():
                errors.append(
                    "Defect Description required.")
            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                with st.spinner("Submitting..."):
                    ticket,cid,err = submit_claim({
                        "customer_id":
                            cust_options[sel_cust],
                        "product_id":
                            prod_options[sel_prod],
                        "product_name":sel_prod,
                        "defect_type_id":
                            defect_options[sel_defect],
                        "invoice_number":
                            invoice_number.strip(),
                        "invoice_date":
                            str(invoice_date),
                        "quantity_received":
                            qty_received,
                        "quantity_claimed":
                            qty_claimed,
                        "quantity_unit":qty_unit,
                        "defect_description":
                            description.strip(),
                        "priority":priority,
                        "contact_name":
                            contact_name.strip(),
                        "email":email.strip(),
                        "mobile":mobile.strip(),
                    })
                    if not ticket:
                        st.error(
                            f"❌ Submission failed: "
                            f"{err}")
                        st.stop()
                    uploaded_names = []
                    for f in (uploaded_photos or []):
                        url,pid = upload_file(
                            f,ticket,"photo")
                        if url:
                            save_attachment(
                                cid,f.name,"photo",
                                f.type,f.size,url,pid)
                            uploaded_names.append(
                                f.name)
                    for f in (uploaded_videos or []):
                        url,pid = upload_file(
                            f,ticket,"video")
                        if url:
                            save_attachment(
                                cid,f.name,"video",
                                f.type,f.size,url,pid)
                            uploaded_names.append(
                                f.name)
                    email_sent = send_email(
                        to_email=email.strip(),
                        customer_name=
                            contact_name.strip(),
                        ticket_number=ticket,
                        product=sel_prod,
                        defect=sel_defect,
                        priority=priority,
                        claim_value_inr=claim_value_inr
                    )
                    st.session_state.pub_submitted = True
                    st.session_state.pub_ticket    = ticket
                    st.session_state.pub_data      = {
                        "customer_name":
                            sel_cust.split("—")[-1]
                            .strip(),
                        "product_name":  sel_prod,
                        "defect_name":   sel_defect,
                        "priority":      priority,
                        "quantity_claimed": qty_claimed,
                        "quantity_unit": qty_unit,
                        "claim_value_inr":
                            claim_value_inr,
                        "email":         email.strip(),
                        "email_sent":    email_sent,
                        "uploaded_files":
                            uploaded_names,
                    }
                    st.rerun()


if st.session_state.pub_submitted:
    show_success()
else:
    show_form()
