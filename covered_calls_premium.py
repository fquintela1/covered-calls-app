
import streamlit as st
import pandas as pd
import uuid
from datetime import date
import io

st.set_page_config(page_title="Covered Calls Tracker", layout="wide")

st.markdown(
    """<style>
    body, .stApp {
        background-color: #0e0e0e;
        color: #f7931e;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    h1, h2, h3 {
        color: #f7931e;
    }
    label, .stTextInput label, .stNumberInput label, .stDateInput label, .stSelectbox label {
        color: #f7931e !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stDateInput input {
        background-color: #1f1f1f;
        color: #f7931e;
        border: 1px solid #444;
        border-radius: 5px;
        padding: 0.4rem;
    }
    .stButton>button {
        background-color: #f7931e;
        color: black;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ffa937;
        transform: scale(1.02);
    }
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 5px;
    }
    </style>""", unsafe_allow_html=True
)

st.title("📈 Covered Calls Tracker")

if "calls" not in st.session_state:
    st.session_state.calls = []

def generate_id():
    return str(uuid.uuid4())

def calculate_net_profit(premium, close_price, rolled_from_id, calls):
    profit = premium
    if close_price:
        profit -= close_price
    if rolled_from_id:
        for call in calls:
            if call["id"] == rolled_from_id:
                roll_loss = call["premium"] - (call["close_price"] or 0)
                profit += roll_loss
    return profit

with st.form("add_call_form"):
    st.subheader("➕ Add New Covered Call")
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Ticker", value="MSTR")
        strike = st.number_input("Strike Price", min_value=0.0, step=0.5, key="strike")
        premium = st.number_input("Premium Received", min_value=0.0, step=0.01, key="premium")
    with col2:
        expiration = st.date_input("Expiration Date", min_value=date.today())
        spot_price = st.number_input("Spot Price (optional)", min_value=0.0, step=0.01, key="spot")
        status = st.selectbox("Status", ["open", "closed", "expired", "assigned"])
    with col3:
        close_price = st.number_input("Close Price (if closed)", min_value=0.0, step=0.01, key="close")
        rolled_from = st.selectbox("Rolled From (if any)", ["None"] + [f"{c['ticker']} - {c['strike']}" for c in st.session_state.calls])
        submitted = st.form_submit_button("Add Covered Call")

    if submitted:
        rolled_from_id = None
        if rolled_from != "None":
            for c in st.session_state.calls:
                if f"{c['ticker']} - {c['strike']}" == rolled_from:
                    rolled_from_id = c["id"]
        new_call = {
            "id": generate_id(),
            "ticker": ticker,
            "strike": strike,
            "premium": premium,
            "expiration": expiration,
            "status": status,
            "close_price": close_price if status == "closed" else None,
            "rolled_from_id": rolled_from_id,
            "spot_price": spot_price,
        }
        new_call["net_profit"] = calculate_net_profit(premium, new_call["close_price"], rolled_from_id, st.session_state.calls)
        st.session_state.calls.append(new_call)
        st.success("✅ Covered Call added successfully!")

st.subheader("📊 Covered Calls Overview")
df = pd.DataFrame(st.session_state.calls)

if not df.empty:
    df_display = df[["ticker", "strike", "premium", "expiration", "status", "close_price", "net_profit", "spot_price"]]
    st.dataframe(df_display, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="covered_calls.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    delete_id = st.selectbox("🗑️ Delete call", options=["None"] + [f"{c['ticker']} - {c['strike']} ({c['id'][:6]})" for c in st.session_state.calls])
    if delete_id != "None":
        if st.button("Delete selected call"):
            selected_id = delete_id.split("(")[-1].strip(")")
            st.session_state.calls = [c for c in st.session_state.calls if not c["id"].startswith(selected_id)]
            st.rerun()
else:
    st.info("No Covered Calls registered yet.")
