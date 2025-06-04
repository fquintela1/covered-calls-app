
import streamlit as st
import pandas as pd
import uuid
from datetime import date
import io

# Personalizar tema con negro y naranja
st.markdown(
    """<style>
    body, .stApp {
        background-color: #111;
        color: #FFA500;
    }
    .stButton>button {
        background-color: #FFA500;
        color: black;
    }
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input {
        background-color: #222;
        color: #FFA500;
    }
    </style>""", unsafe_allow_html=True
)

st.set_page_config(page_title="Covered Calls Tracker", layout="centered")
st.title("📈 Covered Calls Tracker")

# Initialize session state
if "calls" not in st.session_state:
    st.session_state.calls = []

# Utility functions
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

def clear_on_focus(field_id):
    st.markdown(f"""
    <script>
    const field = window.parent.document.querySelectorAll('input[type=number]')[{field_id}];
    field.addEventListener('focus', function() {{
        if (field.value == '0') field.value = '';
    }});
    </script>
    """, unsafe_allow_html=True)

# Form to add new Covered Call
with st.form("Add Call"):
    ticker = st.text_input("Ticker", value="MSTR")
    strike = st.number_input("Strike Price", min_value=0.0, step=0.5, key="strike")
    premium = st.number_input("Premium Received", min_value=0.0, step=0.01, key="premium")
    expiration = st.date_input("Expiration Date", min_value=date.today())
    status = st.selectbox("Status", ["open", "closed", "expired", "assigned"])
    close_price = st.number_input("Close Price (if closed)", min_value=0.0, step=0.01, key="close")
    rolled_from = st.selectbox("Rolled From (if any)", ["None"] + [f"{c['ticker']} - {c['strike']}" for c in st.session_state.calls])
    spot_price = st.number_input("Spot Price (optional)", min_value=0.0, step=0.01, key="spot")
    submitted = st.form_submit_button("Add Covered Call")

    # Borrar ceros al hacer foco
    clear_on_focus(0)  # strike
    clear_on_focus(1)  # premium
    clear_on_focus(2)  # close
    clear_on_focus(3)  # spot

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
        st.success("Covered Call added!")

# Display all calls
st.subheader("📊 All Covered Calls")
df = pd.DataFrame(st.session_state.calls)
if not df.empty:
    df_display = df[["ticker", "strike", "premium", "expiration", "status", "close_price", "net_profit", "spot_price"]]
    st.dataframe(df_display, use_container_width=True)

    # Download logic using BytesIO
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="📥 Download as Excel",
        data=output.getvalue(),
        file_name="covered_calls.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Delete
    delete_id = st.selectbox("Select call to delete", options=["None"] + [f"{c['ticker']} - {c['strike']} ({c['id'][:6]})" for c in st.session_state.calls])
    if delete_id != "None":
        if st.button("Delete selected call"):
            selected_id = delete_id.split("(")[-1].strip(")")
            st.session_state.calls = [c for c in st.session_state.calls if not c["id"].startswith(selected_id)]
            st.experimental_rerun()
else:
    st.info("No Covered Calls registered yet.")
