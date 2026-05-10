import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# -- Page Configuration --
st.set_page_config(page_title="Universal Data Explorer", layout="wide")

# ── Session State Initialization ──────────────────────────────────────────────
# We use session_state so Streamlit remembers our data even when we click buttons
if "df" not in st.session_state:
    st.session_state.df = None
if "filename" not in st.session_state:
    st.session_state.filename = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    uploaded_file = st.file_uploader(
        "Upload your data",
        type=["csv", "xlsx", "xls", "json"],
        help="Supports CSV, Excel, and JSON formats."
    )

    if st.button("Clear Session"):
        st.session_state.df = None
        st.session_state.filename = None
        st.rerun()

# ── Data Loading Logic ────────────────────────────────────────────────────────
if uploaded_file is not None and st.session_state.filename != uploaded_file.name:
    with st.status("Parsing file contents...", expanded=True) as status:
        try:
            ext = uploaded_file.name.split(".")[-1].lower()
            if ext == "csv":
                st.write("Reading CSV...")
                df = pd.read_csv(uploaded_file)
            elif ext in ["xlsx", "xls"]:
                st.write("Reading Excel...")
                df = pd.read_excel(uploaded_file)
            elif ext == "json":
                st.write("Reading JSON...")
                df = pd.read_json(uploaded_file)

            st.session_state.df = df
            st.session_state.filename = uploaded_file.name
            status.update(label="✅ Data Loaded Successfully!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Error Loading File", state="error")
            st.error(f"Details: {e}")

# ── Main UI ───────────────────────────────────────────────────────────────────
st.title("📊 Universal Data Explorer")

if st.session_state.df is not None:
    df = st.session_state.df

    # ── Metrics ───────────────────────────────────────────────────────────────
    # We'll calculate a few basic stats to show off the metric component
    num_rows = len(df)
    num_cols = len(df.columns)
    numeric_df = df.select_dtypes(include="number")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Rows", f"{num_rows:,}")
    m2.metric("Total Columns", num_cols)
    m3.metric("Numeric Fields", len(numeric_df.columns), delta_color="normal")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📝 Edit Data", "📈 Visualization", "📋 Raw Stats"])

    with tab1:
        st.subheader("Interactive Data Editor")
        st.write("Changes made here will reflect in the chart and downloads.")
        # Data Editor allows live manipulation of the dataframe
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
        st.session_state.df = edited_df  # Update session state with edits

        st.download_button(
            label="⬇️ Download Edited Data (CSV)",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name=f"edited_{st.session_state.filename}.csv",
            mime="text/csv"
        )

    with tab2:
        st.subheader("Data Insights")
        if not numeric_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                y_col = st.selectbox("Select Numeric Column (Y)", numeric_df.columns)
            with col2:
                # Try to find a categorical column for the X-axis
                cat_cols = df.select_dtypes(exclude="number").columns.tolist()
                x_col = st.selectbox("Select Category Column (X)", cat_cols if cat_cols else df.columns)

            agg_type = st.radio("Aggregation", ["Mean", "Sum", "Count"], horizontal=True)

            # Simple aggregation logic
            agg_map = {"Mean": "mean", "Sum": "sum", "Count": "count"}
            chart_data = edited_df.groupby(x_col)[y_col].agg(agg_map[agg_type]).sort_values(ascending=False).head(20)

            # Plotting
            fig, ax = plt.subplots(figsize=(10, 5))
            chart_data.plot(kind="bar", ax=ax, color="#1f77b4")
            ax.set_title(f"{agg_type} of {y_col} by {x_col}")
            st.pyplot(fig)
        else:
            st.warning("No numeric data available to generate charts.")

    with tab3:
        st.subheader("Statistical Summary")
        st.dataframe(edited_df.describe(), use_container_width=True)

        st.subheader("Data Types")
        st.write(edited_df.dtypes.to_dict())

else:
    st.info("👈 Please upload a CSV, Excel, or JSON file in the sidebar to get started.")
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000",
             caption="Ready for some data?")