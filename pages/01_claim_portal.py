# ============================================================
# FQCMS - Customer Claim Submission Portal
# pages/01_claim_portal.py
# ============================================================

import streamlit as st
from datetime import date
from database.connection import get_connection, init_database

# ── Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="Submit a Claim - FQCMS",
    page_icon="📋",
    layout="wide"
)

# ── Ensure DB is ready ─────────────────────────────────────
init_database()

# ── Custom CSS ─────────────────────────────────────────────
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

/* Section headers */
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

/* Input styling */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

.stTextInput label, .stTextArea label,
.stSelectbox label, .stDateInput label,
.stNumberInput label {
    color: #8892a4 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Submit button */
.stButton > button {
    background: linear-gradient(135deg, #4f8ef7 0%, #7c3aed 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 32px;
    font-size: 15px;
    font-weight: 600;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(79,142,247,0.4);
}

/* Success ticket card */
.ticket-success {
    background: linear-gradient(135deg, #10b98115, #059f4615);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    margin: 24px 0;
}

.ticket-number {
    font-size: 36px;
    font-weight: 700;
    color: #10b981;
    letter-spacing: 2px;
    margin: 12px 0;
}

.ticket-label {
    color: #8892a4;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Priority badges */
.priority-critical { color: #ef4444; font-weight: 600; }
.priority-major    { color: #f59e0b; font-weight: 600; }
.priority-minor    { color: #10b981; font-weight: 600; }

/* Form card */
.form-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ───────────────────────────────────────

def generate_ticket_number():
    """Generates next ticket number in FRUIT-XXXXXX format."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE ticket_counter SET last_value = last_value + 1 WHERE id = 1")
    conn.commit()
    row = cursor.execute("SELECT last_value FROM ticket_counter WHERE id = 1").fetchone()
    conn.close()
    return f"FRUIT-{row['last_value']:06d}"


def get_products():
    """Returns list of active products."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name FROM products WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


def get_defects_for_product(product_id):
    """Returns defect types for a given product."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name FROM defect_types WHERE product_id = ? AND is_active = 1",
        (product_id,)
    ).fetchall()
    conn.close()
    return rows


def get_customers():
    """Returns all active customers."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, customer_code, customer_name FROM customers WHERE is_active = 1 ORDER BY customer_name"
    ).fetchall()
    conn.close()
    return rows


def get_sla_deadline(priority):
    """Returns response and resolution deadlines based on priority."""
    from datetime import datetime, timedelta
    conn = get_connection()
    row = conn.execute(
        "SELECT response_hours, resolution_hours FROM sla_rules WHERE priority = ?",
        (priority,)
    ).fetchone()
    conn.close()
    now = datetime.now()
    response_due  = (now + timedelta(hours=row["response_hours"])).strftime("%Y-%m-%d %H:%M:%S")
    resolution_due = (now + timedelta(hours=row["resolution_hours"])).strftime("%Y-%m-%d %H:%M:%S")
    return response_due, resolution_due


def submit_claim(data):
    """
    Inserts a new claim into the database.
    Creates SLA tracking record.
    Returns ticket number on success.
    """
    conn = get_connection()
    cursor = conn.cursor()

    ticket_number = generate_ticket_number()
    response_due, resolution_due = get_sla_deadline(data["priority"])

    try:
        # Insert claim
        cursor.execute("""
            INSERT INTO claims (
                ticket_number, customer_id, product_id, defect_type_id,
                invoice_number, invoice_date, quantity_received, quantity_claimed,
                quantity_unit, defect_description, priority, status,
                sla_response_due_at, sla_resolution_due_at,
                submitted_by_name, submitted_by_email, submitted_by_mobile
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', ?, ?, ?, ?, ?)
        """, (
            ticket_number,
            data["customer_id"],
            data["product_id"],
            data["defect_type_id"],
            data["invoice_number"],
            data["invoice_date"],
            data["quantity_received"],
            data["quantity_claimed"],
            data["quantity_unit"],
            data["defect_description"],
            data["priority"],
            response_due,
            resolution_due,
            data["contact_name"],
            data["email"],
            data["mobile"],
        ))

        claim_id = cursor.lastrowid

        # Create SLA tracking record
        cursor.execute("""
            INSERT INTO sla_tracking (
                claim_id, priority, response_due_at, resolution_due_at
            ) VALUES (?, ?, ?, ?)
        """, (claim_id, data["priority"], response_due, resolution_due))

        # Audit log
        cursor.execute("""
            INSERT INTO audit_logs (claim_id, action, entity_type, entity_id, new_value)
            VALUES (?, 'CLAIM_CREATED', 'claim', ?, ?)
        """, (claim_id, claim_id, ticket_number))

        conn.commit()
        conn.close()
        return ticket_number, None

    except Exception as e:
        conn.rollback()
        conn.close()
        return None, str(e)


def validate_form(data):
    """Validates all required form fields. Returns list of errors."""
    errors = []
    if not data.get("contact_name"):
        errors.append("Contact Person name is required.")
    if not data.get("email") or "@" not in data.get("email", ""):
        errors.append("Valid email address is required.")
    if not data.get("mobile") or len(data.get("mobile", "")) < 10:
        errors.append("Valid 10-digit mobile number is required.")
    if not data.get("invoice_number"):
        errors.append("Invoice Number is required.")
    if data.get("quantity_claimed", 0) <= 0:
        errors.append("Quantity Claimed must be greater than 0.")
    if data.get("quantity_claimed", 0) > data.get("quantity_received", 0):
        errors.append("Quantity Claimed cannot exceed Quantity Received.")
    if not data.get("defect_description"):
        errors.append("Defect Description is required.")
    return errors


# ── Main Page ──────────────────────────────────────────────

def show_success_screen(ticket_number, priority, product_name, customer_name):
    """Shows ticket confirmation after successful submission."""
    priority_colors = {
        "Critical": "#ef4444",
        "Major":    "#f59e0b",
        "Minor":    "#10b981"
    }
    color = priority_colors.get(priority, "#10b981")

    st.markdown(f"""
    <div class='ticket-success'>
        <div style='font-size:48px;'>✅</div>
        <div class='ticket-label'>Your Claim Has Been Submitted</div>
        <div class='ticket-number'>{ticket_number}</div>
        <div style='color:#8892a4; font-size:14px; margin-top:8px;'>
            Save this ticket number to track your claim
        </div>
        <div style='margin-top:20px; display:flex;
                    justify-content:center; gap:24px; flex-wrap:wrap;'>
            <div style='text-align:center;'>
                <div style='color:#8892a4; font-size:11px;
                            text-transform:uppercase;'>Customer</div>
                <div style='color:#fff; font-weight:600;
                            font-size:14px;'>{customer_name}</div>
            </div>
            <div style='text-align:center;'>
                <div style='color:#8892a4; font-size:11px;
                            text-transform:uppercase;'>Product</div>
                <div style='color:#fff; font-weight:600;
                            font-size:14px;'>{product_name}</div>
            </div>
            <div style='text-align:center;'>
                <div style='color:#8892a4; font-size:11px;
                            text-transform:uppercase;'>Priority</div>
                <div style='font-weight:600; font-size:14px;
                            color:{color};'>{priority}</div>
            </div>
            <div style='text-align:center;'>
                <div style='color:#8892a4; font-size:11px;
                            text-transform:uppercase;'>Status</div>
                <div style='color:#4f8ef7; font-weight:600;
                            font-size:14px;'>New</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("📧 Our quality team will contact you within the SLA timeline. "
            "Please quote your ticket number in all communications.")

    if st.button("📋 Submit Another Claim"):
        st.session_state.claim_submitted = False
        st.session_state.ticket_number   = None
        st.rerun()


def show_claim_form():
    """Renders the full claim submission form."""

    # ── Page Header ─────────────────────────────────────────
    st.markdown("""
    <div style='padding: 8px 0 24px 0;'>
        <h2 style='color:#ffffff; margin:0;'>📋 Submit a Quality Claim</h2>
        <p style='color:#8892a4; margin:4px 0 0 0; font-size:14px;'>
            Fill in the form below to lodge a fruit quality complaint.
            All fields marked with * are required.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load reference data ──────────────────────────────────
    customers = get_customers()
    products  = get_products()

    customer_options = {f"{c['customer_code']} — {c['customer_name']}": c["id"]
                        for c in customers}
    product_options  = {p["name"]: p["id"] for p in products}

    # ── Form ────────────────────────────────────────────────
    with st.form("claim_form", clear_on_submit=False):

        # Section 1: Customer Information
        st.markdown("<div class='section-header'>👤 Customer Information</div>",
                    unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            selected_customer = st.selectbox(
                "Customer *",
                options=list(customer_options.keys()),
                help="Select your company name"
            )
            contact_name = st.text_input(
                "Contact Person *",
                placeholder="Your full name"
            )
        with col2:
            email = st.text_input(
                "Email Address *",
                placeholder="your@email.com"
            )
            mobile = st.text_input(
                "Mobile Number *",
                placeholder="10-digit mobile number"
            )

        # Section 2: Invoice Details
        st.markdown("<div class='section-header'>🧾 Invoice Details</div>",
                    unsafe_allow_html=True)

        col3, col4, col5 = st.columns(3)
        with col3:
            invoice_number = st.text_input(
                "Invoice Number *",
                placeholder="e.g. INV-2024-001"
            )
        with col4:
            invoice_date = st.date_input(
                "Invoice Date *",
                value=date.today(),
                max_value=date.today()
            )
        with col5:
            quantity_unit = st.selectbox(
                "Unit",
                options=["KG", "Box", "Carton", "Punnet", "Piece"]
            )

        # Section 3: Product & Defect
        st.markdown("<div class='section-header'>🍋 Product & Defect Details</div>",
                    unsafe_allow_html=True)

        col6, col7 = st.columns(2)
        with col6:
            selected_product = st.selectbox(
                "Product *",
                options=list(product_options.keys())
            )
        with col7:
            # Dynamic defects based on product selection
            product_id    = product_options[selected_product]
            defect_rows   = get_defects_for_product(product_id)
            defect_options = {d["name"]: d["id"] for d in defect_rows}
            selected_defect = st.selectbox(
                "Defect Type *",
                options=list(defect_options.keys())
            )

        col8, col9, col10 = st.columns(3)
        with col8:
            quantity_received = st.number_input(
                "Quantity Received *",
                min_value=0.0,
                step=0.5,
                format="%.1f"
            )
        with col9:
            quantity_claimed = st.number_input(
                "Quantity Claimed *",
                min_value=0.0,
                step=0.5,
                format="%.1f"
            )
        with col10:
            priority = st.selectbox(
                "Priority *",
                options=["Minor", "Major", "Critical"],
                help="Critical=2hr SLA, Major=4hr SLA, Minor=8hr SLA"
            )

        # Section 4: Description
        st.markdown("<div class='section-header'>📝 Claim Description</div>",
                    unsafe_allow_html=True)

        defect_description = st.text_area(
            "Describe the defect in detail *",
            placeholder="Please describe the quality issue in detail. "
                        "Include when you noticed it, how many units are affected, "
                        "and any other relevant information...",
            height=120
        )

        # Section 5: Priority Guide
        st.markdown("<div class='section-header'>ℹ️ Priority & SLA Guide</div>",
                    unsafe_allow_html=True)

        gc1, gc2, gc3 = st.columns(3)
        with gc1:
            st.markdown("""
            <div style='background:rgba(239,68,68,0.08); border:1px solid
                        rgba(239,68,68,0.3); border-radius:8px; padding:12px;'>
                <div style='color:#ef4444; font-weight:700;'>🔴 Critical</div>
                <div style='color:#8892a4; font-size:12px; margin-top:4px;'>
                    Response: 2 hours<br>Resolution: 24 hours<br>
                    <i>Total product loss, food safety risk</i>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with gc2:
            st.markdown("""
            <div style='background:rgba(245,158,11,0.08); border:1px solid
                        rgba(245,158,11,0.3); border-radius:8px; padding:12px;'>
                <div style='color:#f59e0b; font-weight:700;'>🟡 Major</div>
                <div style='color:#8892a4; font-size:12px; margin-top:4px;'>
                    Response: 4 hours<br>Resolution: 48 hours<br>
                    <i>Significant quality issue, partial loss</i>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with gc3:
            st.markdown("""
            <div style='background:rgba(16,185,129,0.08); border:1px solid
                        rgba(16,185,129,0.3); border-radius:8px; padding:12px;'>
                <div style='color:#10b981; font-weight:700;'>🟢 Minor</div>
                <div style='color:#8892a4; font-size:12px; margin-top:4px;'>
                    Response: 8 hours<br>Resolution: 72 hours<br>
                    <i>Minor defects, small quantity affected</i>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Submit button
        submitted = st.form_submit_button("🚀 Submit Quality Claim")

        if submitted:
            form_data = {
                "customer_id":       customer_options[selected_customer],
                "customer_name":     selected_customer,
                "product_id":        product_options[selected_product],
                "product_name":      selected_product,
                "defect_type_id":    defect_options[selected_defect],
                "invoice_number":    invoice_number,
                "invoice_date":      str(invoice_date),
                "quantity_received": quantity_received,
                "quantity_claimed":  quantity_claimed,
                "quantity_unit":     quantity_unit,
                "defect_description": defect_description,
                "priority":          priority,
                "contact_name":      contact_name,
                "email":             email,
                "mobile":            mobile,
            }

            # Validate
            errors = validate_form(form_data)
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                # Submit to database
                ticket_number, error = submit_claim(form_data)
                if ticket_number:
                    st.session_state.claim_submitted = True
                    st.session_state.ticket_number   = ticket_number
                    st.session_state.submitted_data  = form_data
                    st.rerun()
                else:
                    st.error(f"❌ Submission failed: {error}")


# ── Page Router ────────────────────────────────────────────
if "claim_submitted" not in st.session_state:
    st.session_state.claim_submitted = False

if st.session_state.claim_submitted:
    data = st.session_state.get("submitted_data", {})
    show_success_screen(
        ticket_number=st.session_state.ticket_number,
        priority=data.get("priority", "Minor"),
        product_name=data.get("product_name", ""),
        customer_name=data.get("customer_name", ""),
    )
else:
    show_claim_form()
