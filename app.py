import streamlit as st
from google import genai
import os
from PIL import Image
import base64
import smtplib
from email.message import EmailMessage
import random
import string
import sqlite3
from datetime import datetime

# ==========================================
# 1. DATABASE & THESIS CORE (THE PERMANENT 5)
# ==========================================
st.set_page_config(page_title="XVentures Matchmaker", page_icon="🏛️", layout="wide")
DB_FILE = "summit_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    # The schema covers every detail for identity and AI classification
    conn.execute('''CREATE TABLE IF NOT EXISTS members 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  full_name TEXT, job_title TEXT, company TEXT,
                  mandate_focus TEXT, looking_for TEXT,
                  email TEXT, linkedin_url TEXT, 
                  full_identity_profile TEXT, timestamp REAL)''')
    
    # HARD-CODED THESIS CORE: These 5 stay no matter what.
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        profiles = [
            ("Amara Okafor", "Director of Digital Assets", "Abu Dhabi Sovereign Wealth Fund", 
             "Deploy $200M into tokenised real-world assets and blockchain infrastructure.", 
             "Startups with regulatory clarity, audited smart contracts, and institutional partnerships."),
            ("Marcus Chen", "CEO & Co-Founder", "VaultBridge", 
             "Institutional custody and settlement infrastructure for tokenised securities.", 
             "Strategic investors and introductions to Middle Eastern sovereign wealth funds."),
            ("Dr. Elena Vasquez", "General Partner", "Meridian Crypto Ventures", 
             "Infrastructure plays at the intersection of TradFi and DeFi. Series A-B focus.", 
             "Deal flow matching thesis, co-investors for larger rounds."),
            ("James Whitfield", "CTO", "NexaLayer", 
             "Enterprise-grade L2 with built-in compliance modules for regulated institutions.", 
             "Banks and asset managers willing to pilot the technology."),
            ("Sophie Bergmann", "Head of Digital Assets Innovation", "Deutsche Bundesbank", 
             "Exploring CBDC infrastructure and regulatory frameworks under MiCA.", 
             "Technology providers with compliance-first approaches and private sector partners.")
        ]
        for p in profiles:
            summary = f"NAME: {p[0]} | ROLE: {p[1]} | CO: {p[2]} | FOCUS: {p[3]} | NEEDS: {p[4]}"
            conn.execute("""INSERT INTO members (full_name, job_title, company, mandate_focus, looking_for, email, linkedin_url, full_identity_profile, timestamp) 
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                         (p[0], p[1], p[2], p[3], p[4], "core@xventures.com", "https://linkedin.com", summary, datetime.now().timestamp()))
    conn.commit(); conn.close()

init_db()

# BROWSER MEMORY KILLER (Universal Seed)
if "seed" not in st.session_state:
    st.session_state.seed = str(random.randint(100000, 999999))
if "step" not in st.session_state: 
    st.session_state.step = "idle"

def send_token_email(receiver_email, token, mode="Verification"):
    try:
        sender = st.secrets["email_settings"]["sender_email"]
        pwd = st.secrets["email_settings"]["app_password"]
        msg = EmailMessage()
        msg.set_content(f"Your XVentures {mode} Token: {token}")
        msg['Subject'] = f"XVentures {mode}"
        msg['From'] = sender
        msg['To'] = receiver_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, pwd)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.sidebar.error(f"Email Error: {e}")
        return False

# ==========================================
# 2. SIDEBAR (AUTH, DELETE, & LIVE TIME)
# ==========================================
st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px; border: 1px solid #FF4B4B;">
        <h2 style="margin:0; color: #FF4B4B;">{datetime.now().strftime("%H:%M:%S")}</h2>
        <h3 style="margin:0; opacity: 0.8;">{datetime.now().strftime("%d %b %Y")}</h3>
    </div>
""", unsafe_allow_html=True)

if os.path.exists("public.jpg"): 
    st.sidebar.image("public.jpg", use_container_width=True)

st.sidebar.markdown("---")

# Navigation buttons
if st.session_state.step in ["idle", "verified"]:
    if st.sidebar.button("➕ Register / Login", use_container_width=True):
        st.session_state.step = "auth_email"; st.rerun()
    if st.sidebar.button("🗑️ Remove My Profile", use_container_width=True):
        st.session_state.step = "del_email"; st.rerun()

# --- AUTHENTICATION FLOW ---
if st.session_state.step == "auth_email":
    st.sidebar.subheader("Step 1: Identity")
    e_in = st.sidebar.text_input(f"Email {st.session_state.seed}", key=f"e_{st.session_state.seed}")
    if st.sidebar.button("Send Access Token"):
        tok = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.session_state.generated_token = tok
        st.session_state.temp_email = e_in
        if send_token_email(e_in, tok, "Access"):
            st.session_state.step = "auth_token"; st.rerun()

elif st.session_state.step == "auth_token":
    st.sidebar.subheader("Step 2: Token")
    t_in = st.sidebar.text_input("Enter 6-Digit Code", key=f"t_{st.session_state.seed}")
    if st.sidebar.button("Verify & Enter"):
        if t_in.strip() == st.session_state.generated_token:
            st.session_state.step = "verified"; st.rerun()

# --- DELETION FLOW ---
elif st.session_state.step == "del_email":
    st.sidebar.subheader("Remove Profile")
    de_in = st.sidebar.text_input("Confirm Email", key=f"de_{st.session_state.seed}")
    if st.sidebar.button("Send Deletion Code"):
        dtok = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        st.session_state.generated_token = dtok
        st.session_state.temp_email = de_in
        if send_token_email(de_in, dtok, "Deletion"):
            st.session_state.step = "del_token"; st.rerun()

elif st.session_state.step == "del_token":
    dt_in = st.sidebar.text_input("Enter Deletion Code", key=f"dt_{st.session_state.seed}")
    if st.sidebar.button("PERMANENTLY DELETE"):
        if dt_in.strip() == st.session_state.generated_token:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("DELETE FROM members WHERE email=?", (st.session_state.temp_email,))
            conn.commit(); conn.close()
            st.session_state.step = "idle"; st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🏠 Home / Reset Session"):
    st.session_state.seed = str(random.randint(100000, 999999))
    st.session_state.step = "idle"; st.rerun()

# ==========================================
# 3. MAIN AREA (THE STRATEGIC BROKER)
# ==========================================
st.title("🏛️ XVentures Identity Classification Engine")

if st.session_state.step == "verified":
    st.subheader("📝 Strategic Profile Registration")
    s = st.session_state.seed
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(f"Full Name [ID:{s}]", key=f"n_{s}")
            title = st.text_input(f"Job Title [ID:{s}]", key=f"ti_{s}")
            comp = st.text_input(f"Company/Institution [ID:{s}]", key=f"co_{s}")
        with c2:
            link = st.text_input(f"LinkedIn URL [ID:{s}]", key=f"l_{s}")
            email = st.text_input("Verified Email", value=st.session_state.temp_email, disabled=True)
        
        mandate = st.text_area(f"Mandate Focus (Classification Data) [ID:{s}]", key=f"m_{s}")
        looking = st.text_area(f"Strategic Needs [ID:{s}]", key=f"lk_{s}")
        
        if st.button("Complete Registration & Join Parade", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            summary = f"NAME: {name} | ROLE: {title} | CO: {comp} | FOCUS: {mandate} | NEEDS: {looking}"
            conn.execute("""INSERT INTO members (full_name, job_title, company, mandate_focus, looking_for, email, linkedin_url, full_identity_profile, timestamp) 
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                         (name, title, comp, mandate, looking, email, link, summary, datetime.now().timestamp()))
            conn.commit(); conn.close()
            st.session_state.step = "idle"; st.rerun()

else:
    if os.path.exists("paris_bg.png"): 
        st.image("paris_bg.png", width=600)
    
    st.markdown("---")
    st.subheader("🔍 AI Identity Analysis (The Broker)")
    
    query = st.text_area("Analyze the integration between participants (e.g. 'Who should meet Marcus and why?'):", key=f"q_{st.session_state.seed}")
    
    if st.button("Broker Strategic Matches", type="primary"):
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        pool_data = sqlite3.connect(DB_FILE).execute("SELECT full_identity_profile FROM members").fetchall()
        pool = "\n".join([row[0] for row in pool_data])
        
        prompt = f"""
        Identity Pool: {pool}
        System Role: You are a Strategic Broker.
        Task: Analyze the synergy between these people based on the query: '{query}'.
        Explain why they need to meet (e.g. Marcus has the tech, Amara has the $200M).
        Identify potential roadblocks (e.g. Sophie's regulatory constraints).
        RANK matches by strategic priority.
        """
        res = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        st.markdown(res.text)

# ==========================================
# 4. THE PARADE (p1-p5)
# ==========================================
people = ["p1.png", "p2.png", "p3.png", "p4.png", "p5.png"]
found = [p for p in people if os.path.exists(p)]
if found:
    html = ""
    vips = len(sqlite3.connect(DB_FILE).execute("SELECT 1 FROM members").fetchall())
    for i in range(vips):
        with open(found[i % len(found)], "rb") as f: b64 = base64.b64encode(f.read()).decode()
        html += f'<div class="walker" style="animation: slide-loop-left {15+random.randint(0,10)}s linear infinite; animation-delay: {i*5}s;"><img src="data:image/png;base64,{b64}"></div>'
    
    st.markdown(f"""
        <style>
        .parade-container {{ width: 100%; height: 180px; position: relative; overflow: hidden; }}
        .walker {{ position: absolute; right: -200px; bottom: 10px; width: 120px; }}
        @keyframes slide-loop-left {{ 0% {{ right: -200px; }} 100% {{ right: 100%; }} }}
        </style>
        <div class="parade-container">{html}</div>
    """, unsafe_allow_html=True)