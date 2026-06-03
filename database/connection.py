# ============================================================
# FQCMS - Database Connection Module
# database/connection.py
# ============================================================

import sqlite3
import os
import streamlit as st

# Database file path — stored in project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fqcms.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            full_name       TEXT NOT NULL,
            role_id         INTEGER NOT NULL REFERENCES roles(id),
            is_active       INTEGER NOT NULL DEFAULT 1,
            last_login_at   TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_code   TEXT NOT NULL UNIQUE,
            customer_name   TEXT NOT NULL,
            contact_person  TEXT NOT NULL,
            email           TEXT NOT NULL,
            mobile          TEXT NOT NULL,
            address         TEXT,
            city            TEXT,
            country         TEXT DEFAULT 'India',
            is_active       INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defect_types (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL REFERENCES products(id),
            name        TEXT NOT NULL,
            description TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(product_id, name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sla_rules (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            priority            TEXT NOT NULL UNIQUE,
            response_hours      INTEGER NOT NULL,
            resolution_hours    INTEGER NOT NULL,
            escalation_hours    INTEGER NOT NULL,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_counter (
            id          INTEGER PRIMARY KEY CHECK(id = 1),
            last_value  INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number           TEXT NOT NULL UNIQUE,
            customer_id             INTEGER NOT NULL REFERENCES customers(id),
            product_id              INTEGER NOT NULL REFERENCES products(id),
            defect_type_id          INTEGER NOT NULL REFERENCES defect_types(id),
            invoice_number          TEXT NOT NULL,
            invoice_date            TEXT NOT NULL,
            quantity_received       REAL NOT NULL,
            quantity_claimed        REAL NOT NULL,
            quantity_unit           TEXT NOT NULL DEFAULT 'KG',
            defect_description      TEXT NOT NULL,
            priority                TEXT NOT NULL DEFAULT 'Minor',
            status                  TEXT NOT NULL DEFAULT 'New',
            assigned_to_id          INTEGER REFERENCES users(id),
            assigned_at             TEXT,
            sla_response_due_at     TEXT,
            sla_resolution_due_at   TEXT,
            sla_response_met        INTEGER DEFAULT 0,
            sla_resolution_met      INTEGER DEFAULT 0,
            gdrive_folder_id        TEXT,
            gdrive_folder_url       TEXT,
            submitted_by_name       TEXT NOT NULL,
            submitted_by_email      TEXT NOT NULL,
            submitted_by_mobile     TEXT NOT NULL,
            created_at              TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at              TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_at             TEXT,
            closed_at               TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id            INTEGER NOT NULL REFERENCES claims(id),
            original_filename   TEXT NOT NULL,
            stored_filename     TEXT NOT NULL,
            file_type           TEXT NOT NULL,
            mime_type           TEXT NOT NULL,
            file_size_bytes     INTEGER NOT NULL,
            gdrive_file_id      TEXT,
            gdrive_view_url     TEXT,
            gdrive_download_url TEXT,
            uploaded_by_id      INTEGER REFERENCES users(id),
            uploaded_at         TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id            INTEGER NOT NULL UNIQUE REFERENCES claims(id),
            root_cause_category TEXT,
            root_cause_details  TEXT,
            findings            TEXT,
            corrective_action   TEXT,
            preventive_action   TEXT,
            inspection_date     TEXT,
            inspector_name      TEXT,
            lab_report_ref      TEXT,
            investigator_id     INTEGER REFERENCES users(id),
            started_at          TEXT,
            completed_at        TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id    INTEGER NOT NULL REFERENCES claims(id),
            author_id   INTEGER NOT NULL REFERENCES users(id),
            note        TEXT NOT NULL,
            is_internal INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id            INTEGER NOT NULL UNIQUE REFERENCES claims(id),
            decision            TEXT NOT NULL,
            approved_quantity   REAL DEFAULT 0,
            credit_amount       REAL DEFAULT 0,
            currency            TEXT NOT NULL DEFAULT 'INR',
            remarks             TEXT,
            submitted_by_id     INTEGER NOT NULL REFERENCES users(id),
            submitted_at        TEXT NOT NULL DEFAULT (datetime('now')),
            approved_by_id      INTEGER REFERENCES users(id),
            approved_at         TEXT,
            settlement_status   TEXT NOT NULL DEFAULT 'Pending',
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sla_tracking (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id            INTEGER NOT NULL UNIQUE REFERENCES claims(id),
            priority            TEXT NOT NULL,
            response_due_at     TEXT NOT NULL,
            resolution_due_at   TEXT NOT NULL,
            first_response_at   TEXT,
            resolved_at         TEXT,
            response_breached   INTEGER NOT NULL DEFAULT 0,
            resolution_breached INTEGER NOT NULL DEFAULT 0,
            escalated           INTEGER NOT NULL DEFAULT 0,
            escalated_at        TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id    INTEGER REFERENCES claims(id),
            user_id     INTEGER REFERENCES users(id),
            action      TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id   INTEGER,
            old_value   TEXT,
            new_value   TEXT,
            ip_address  TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_status   ON claims(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_priority ON claims(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_customer ON claims(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_created  ON claims(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_claim     ON audit_logs(claim_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_claim     ON internal_notes(claim_id)")

    conn.commit()
    _seed_reference_data(cursor, conn)
    conn.close()


def _seed_reference_data(cursor, conn):
    import bcrypt

    roles = [
        ("Admin",             "Full system access"),
        ("Quality Manager",   "Approves settlements and views all claims"),
        ("Quality Executive", "Investigates claims and updates status"),
        ("Customer",          "Submits and tracks own claims"),
    ]
    for name, desc in roles:
        cursor.execute(
            "INSERT OR IGNORE INTO roles(name, description) VALUES (?, ?)",
            (name, desc)
        )

    sla_rules = [
        ("Critical", 2,  24, 20),
        ("Major",    4,  48, 40),
        ("Minor",    8,  72, 60),
    ]
    for priority, resp, resol, esc in sla_rules:
        cursor.execute(
            """INSERT OR IGNORE INTO sla_rules
               (priority, response_hours, resolution_hours, escalation_hours)
               VALUES (?, ?, ?, ?)""",
            (priority, resp, resol, esc)
        )

    products = [
        ("Banana",      "Fresh banana bunches and boxes"),
        ("Pomegranate", "Fresh pomegranate whole fruit"),
        ("Arils",       "Fresh pomegranate arils in sealed punnets"),
    ]
    for name, desc in products:
        cursor.execute(
            "INSERT OR IGNORE INTO products(name, description) VALUES (?, ?)",
            (name, desc)
        )

    conn.commit()

    defects = {
        "Banana":      ["Overripe", "Underripe", "Crown Rot", "Bruising", "Physical Damage", "Colour Issue"],
        "Pomegranate": ["Internal Blackening", "Cracking", "Shrivelling", "Skin Damage", "Size Variation"],
        "Arils":       ["Leakage", "Fermentation", "Browning", "Seal Failure", "Foreign Matter"],
    }
    for product_name, defect_list in defects.items():
        row = cursor.execute(
            "SELECT id FROM products WHERE name = ?", (product_name,)
        ).fetchone()
        if row:
            for defect in defect_list:
                cursor.execute(
                    "INSERT OR IGNORE INTO defect_types(product_id, name) VALUES (?, ?)",
                    (row["id"], defect)
                )

    cursor.execute("INSERT OR IGNORE INTO ticket_counter(id, last_value) VALUES (1, 0)")

    default_password = "Admin@1234"
    hashed = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()

    default_users = [
        ("admin",     "admin@fqcms.com",   hashed, "System Administrator", 1),
        ("qmanager",  "qm@fqcms.com",      hashed, "Quality Manager",      2),
        ("qexec1",    "qe1@fqcms.com",     hashed, "Quality Executive 1",  3),
        ("customer1", "cust1@example.com", hashed, "Demo Customer",        4),
    ]
    for username, email, pw_hash, full_name, role_id in default_users:
        cursor.execute(
            """INSERT OR IGNORE INTO users
               (username, email, password_hash, full_name, role_id)
               VALUES (?, ?, ?, ?, ?)""",
            (username, email, pw_hash, full_name, role_id)
        )

    customers = [
        ("CUST-001", "Reliance Fresh",     "Ramesh Sharma", "ramesh@reliancefresh.com", "9876543210", "Mumbai"),
        ("CUST-002", "Big Bazaar Fruits",  "Sunita Rao",    "sunita@bigbazaar.com",     "9123456780", "Delhi"),
        ("CUST-003", "Nature Basket",      "Priya Nair",    "priya@naturebasket.com",   "9988776655", "Bangalore"),
        ("CUST-004", "Spencer Retail",     "Aakash Joshi",  "aakash@spencers.com",      "9871234567", "Hyderabad"),
        ("CUST-005", "Star Fruit Exports", "Meena Pillai",  "meena@starexports.com",    "9765432109", "Chennai"),
    ]
    for code, name, contact, email, mobile, city in customers:
        cursor.execute(
            """INSERT OR IGNORE INTO customers
               (customer_code, customer_name, contact_person, email, mobile, city)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (code, name, contact, email, mobile, city)
        )

    conn.commit()
