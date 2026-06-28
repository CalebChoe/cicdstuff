import streamlit as st

st.title("Calc App")

a = st.number_input("First number", value=0)
b = st.number_input("Second number", value=0)

operation = st.selectbox("Operation", ["Add", "Subtract", "Multiply", "Divide"])

if st.button("Calculate"):
    if operation == "Add":
        st.success(f"Result: {a + b}")
    elif operation == "Subtract":
        st.success(f"Result: {a - b}")
    elif operation == "Multiply":
        st.success(f"Result: {a * b}")
    elif operation == "Divide":
        if b == 0:
            st.error("Cannot divide by zero")
        else:
            st.success(f"Result: {a / b}")