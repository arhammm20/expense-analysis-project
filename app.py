import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

st.set_page_config(page_title="Smart Expense Dashboard", layout="wide")

st.title("Smart Expense Analytics Dashboard")

file = st.file_uploader("Upload ANY CSV File", type=["csv"])

# ================= SAFE COLUMN DETECTION =================
def find_column(df, candidates):
    for col in df.columns:
        if col.strip().lower() in candidates:
            return col
    return None

# ================= PDF GENERATOR =================
def generate_pdf(summary_data, table_data):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Expense Report", styles['Title']))
    content.append(Spacer(1, 12))

    for item in summary_data:
        content.append(Paragraph(item, styles['Normal']))
        content.append(Spacer(1, 8))

    content.append(Spacer(1, 12))

    table = Table(table_data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ])

    content.append(table)

    doc.build(content)
    buffer.seek(0)
    return buffer

# ================= MAIN =================
if file:

    try:
        df = pd.read_csv(file)

        # ================= CLEAN COLUMN NAMES =================
        df.columns = df.columns.str.strip().str.lower()

        # ================= AUTO DETECT COLUMNS =================
        amount_col = find_column(df, ['amount','price','value','cost','amt'])
        type_col = find_column(df, ['type','transaction type','debit/credit'])
        desc_col = find_column(df, ['description','desc','narration','details','remark'])
        date_col = find_column(df, ['date','transaction date'])

        if amount_col is None:
            st.error("❌ Amount column not found")
            st.stop()

        if type_col is None:
            st.error("❌ Type column not found")
            st.stop()

        if desc_col is None:
            df['description'] = "unknown"
            desc_col = 'description'

        # ================= CLEANING =================
        df['amount'] = pd.to_numeric(df[amount_col], errors='coerce')
        df = df.dropna(subset=['amount'])

        df['type'] = df[type_col].astype(str).str.lower().str.strip()
        df['description'] = df[desc_col].astype(str).str.lower().str.strip()

        df = df.drop_duplicates()

        # ================= CATEGORY ENGINE =================
        def get_category(desc):
            desc = str(desc).lower()

            if "zomato" in desc or "swiggy" in desc:
                return "Food"
            elif "amazon" in desc or "flipkart" in desc:
                return "Shopping"
            elif "uber" in desc or "ola" in desc:
                return "Transport"
            elif "rent" in desc or "bill" in desc:
                return "Bills"
            else:
                return "Other"

        df['category'] = df['description'].apply(get_category)

        # ================= POWER BI SLICERS (SYNCED) =================
        st.sidebar.header("🔍 Power BI Slicers")

        # Type filter
        type_options = df['type'].dropna().unique()

        selected_type = st.sidebar.multiselect(
            "Transaction Type",
            options=type_options,
            default=type_options
        )

        df = df[df['type'].isin(selected_type)]

        # Re-split after type filter
        expense_df = df[df['type'].str.contains('debit', na=False)]
        income_df = df[df['type'].str.contains('credit', na=False)]

        # Category filter
        category_options = expense_df['category'].dropna().unique()

        selected_category = st.sidebar.multiselect(
            "Category",
            options=category_options,
            default=category_options
        )

        expense_df = expense_df[expense_df['category'].isin(selected_category)]

        # Amount filter
        if not expense_df.empty:
            min_amt = float(expense_df['amount'].min())
            max_amt = float(expense_df['amount'].max())

            amount_range = st.sidebar.slider(
                "Amount Range",
                min_value=min_amt,
                max_value=max_amt,
                value=(min_amt, max_amt)
            )

            expense_df = expense_df[
                (expense_df['amount'] >= amount_range[0]) &
                (expense_df['amount'] <= amount_range[1])
            ]

        # ================= KPIs =================
        st.subheader("📊 Key Metrics")

        total_debit = expense_df['amount'].sum()
        total_credit = income_df['amount'].sum()
        savings = total_credit - total_debit

        col1, col2, col3 = st.columns(3)

        col1.metric("💳 Debit", f"₹{total_debit:,.0f}")
        col2.metric("💰 Credit", f"₹{total_credit:,.0f}")
        col3.metric("📈 Savings", f"₹{savings:,.0f}")

        st.divider()

        # ================= TOP SPENDERS =================
        st.subheader("💳 Top Spending Contributors")

        top_spenders = (
            expense_df.groupby('description')['amount']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        st.bar_chart(top_spenders)

        st.divider()

        # ================= MONTHLY TREND =================
        if date_col:
            st.subheader("📈 Monthly Trend")

            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            expense_df = df[df['type'].str.contains('debit', na=False)].copy()

            expense_df['month'] = expense_df[date_col].dt.month

            monthly = expense_df.groupby('month')['amount'].sum()
            st.line_chart(monthly)

        st.divider()

        # ================= TOP TRANSACTIONS =================
        st.subheader("Top Transactions")

        top_txn = (
            expense_df.groupby(['description','category'], as_index=False)['amount']
            .sum()
            .sort_values('amount', ascending=False)
            .head(10)
        )

        st.dataframe(top_txn, use_container_width=True)

        # ================= PDF EXPORT =================
        summary = [
            f"Total Debit: ₹{total_debit:,.0f}",
            f"Total Credit: ₹{total_credit:,.0f}",
            f"Savings: ₹{savings:,.0f}"
        ]

        pdf_buffer = generate_pdf(summary, top_txn.values.tolist())

        st.download_button(
            "📄 Download PDF Report",
            pdf_buffer,
            "expense_report.pdf",
            "application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

else:
    st.info("Upload any CSV file to start analysis")