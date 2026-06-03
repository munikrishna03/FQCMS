import streamlit as st
import psycopg2
import psycopg2.extras


def get_connection():
    conn = psycopg2.connect(
        host     = st.secrets["DB_HOST"],
        port     = st.secrets["DB_PORT"],
        dbname   = st.secrets["DB_NAME"],
        user     = st.secrets["DB_USER"],
        password = st.secrets["DB_PASSWORD"],
        sslmode  = "require"
    )
    conn.autocommit = False
    return conn


def dict_cursor(conn):
    return conn.cursor(
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def init_database():
    import bcrypt
    conn   = get_connection()
    cursor = dict_cursor(conn)
    try:
        # Roles
        for name, desc in [
            ("Admin",             "Full system access"),
            ("Quality Manager",   "Approves settlements"),
            ("Quality Executive", "Investigates claims"),
            ("Customer",          "Submits claims"),
        ]:
            cursor.execute("""
                INSERT INTO roles(name,description)
                VALUES (%s,%s)
                ON CONFLICT(name) DO NOTHING
            """, (name, desc))

        # Products
        for name, desc in [
            ("Banana",      "Fresh banana bunches"),
            ("Pomegranate", "Fresh pomegranate"),
            ("Arils",       "Fresh pomegranate arils"),
        ]:
            cursor.execute("""
                INSERT INTO products(name,description)
                VALUES (%s,%s)
                ON CONFLICT(name) DO NOTHING
            """, (name, desc))

        conn.commit()

        # Defects
        defects = {
            "Banana": [
                "Overripe","Underripe","Crown Rot",
                "Bruising","Physical Damage",
                "Colour Issue"
            ],
            "Pomegranate": [
                "Internal Blackening","Cracking",
                "Shrivelling","Skin Damage",
                "Size Variation"
            ],
            "Arils": [
                "Leakage","Fermentation","Browning",
                "Seal Failure","Foreign Matter"
            ],
        }
        for product_name, defect_list \
                in defects.items():
            cursor.execute(
                "SELECT id FROM products WHERE name=%s",
                (product_name,)
            )
            row = cursor.fetchone()
            if row:
                for defect in defect_list:
                    cursor.execute("""
                        INSERT INTO defect_types
                            (product_id,name)
                        VALUES (%s,%s)
                        ON CONFLICT DO NOTHING
                    """, (row["id"], defect))

        # Ticket counter
        cursor.execute("""
            INSERT INTO ticket_counter(id,last_value)
            VALUES (1,0)
            ON CONFLICT DO NOTHING
        """)

        # SLA Rules
        for priority,resp,resol,esc in [
            ("Critical", 2,  24, 20),
            ("Major",    4,  48, 40),
            ("Minor",    8,  72, 60),
        ]:
            cursor.execute("""
                INSERT INTO sla_rules(priority,
                    response_hours,resolution_hours,
                    escalation_hours)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT(priority) DO NOTHING
            """, (priority,resp,resol,esc))

        # Default users
        default_password = "Admin@1234"
        hashed = bcrypt.hashpw(
            default_password.encode(),
            bcrypt.gensalt()
        ).decode()

        for role_name in [
            "Admin","Quality Manager",
            "Quality Executive","Customer"
        ]:
            cursor.execute(
                "SELECT id FROM roles WHERE name=%s",
                (role_name,)
            )
            r = cursor.fetchone()
            if not r:
                continue
            role_id = r["id"]

            users_for_role = {
                "Admin": [
                    ("admin","admin@fqcms.com",
                     "System Administrator")
                ],
                "Quality Manager": [
                    ("qmanager","qm@fqcms.com",
                     "Quality Manager")
                ],
                "Quality Executive": [
                    ("qexec1","qe1@fqcms.com",
                     "Quality Executive 1"),
                    ("procurement",
                     "procurement@fqcms.com",
                     "Procurement Team")
                ],
                "Customer": [
                    ("customer1","cust1@example.com",
                     "Demo Customer")
                ],
            }
            for username,email,name in \
                    users_for_role.get(role_name,[]):
                cursor.execute("""
                    INSERT INTO users(username,email,
                        password_hash,full_name,
                        role_id)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT(username) DO NOTHING
                """, (username,email,hashed,
                      name,role_id))

        # Sample customers
        for code,name,contact,email,mobile,city in [
            ("CUST-001","Reliance Fresh",
             "Ramesh Sharma",
             "ramesh@reliancefresh.com",
             "9876543210","Mumbai"),
            ("CUST-002","Big Bazaar Fruits",
             "Sunita Rao",
             "sunita@bigbazaar.com",
             "9123456780","Delhi"),
            ("CUST-003","Nature Basket",
             "Priya Nair",
             "priya@naturebasket.com",
             "9988776655","Bangalore"),
            ("CUST-004","Spencer Retail",
             "Aakash Joshi",
             "aakash@spencers.com",
             "9871234567","Hyderabad"),
            ("CUST-005","Star Fruit Exports",
             "Meena Pillai",
             "meena@starexports.com",
             "9765432109","Chennai"),
        ]:
            cursor.execute("""
                INSERT INTO customers(customer_code,
                    customer_name,contact_person,
                    email,mobile,city)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT(customer_code) DO NOTHING
            """, (code,name,contact,
                  email,mobile,city))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
