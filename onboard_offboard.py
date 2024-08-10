import streamlit as st
import datetime as dt

st.title("Welcome Paul Sweeting")

st.header(f"The Time Is {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")

with st.container(border=True):
    st.write("### Alerts:")
    st.write("- **09:12AM** - NWAS are having issues with connecting calls to CAS")
    st.write("- **09:22AM** - EHR needs you to reauthenticate before shift starts")

st.selectbox("Choose Role", ["Despatcher", "Call Handler", "Shift Lead"])

if st.toggle("Slide to clock in"):
    with st.container(border=True):
        st.subheader("Task Due")
        st.write("✅ Due: Sign Off handover from Clare Tooney")
        st.write("✅ Due: Delta Car Laptop Connectivity")
        st.write("✅ 11am: Check Room 246 Medicines Fridge")
        st.write("✅ 12pm: NWAS Opal Call ")
        st.write("✅ 13:00pm: Water Meeting Reception Handover")
