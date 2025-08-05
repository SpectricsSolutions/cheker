import streamlit as st
import pandas as pd
from docx import Document
from collections import Counter

st.set_page_config(page_title="CSV Completeness Checker", layout="wide")

# === Load Rules from Word DOCX ===
def load_rules(docx_file):
    doc = Document(docx_file)
    rules = {}
    current_type = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if text.lower() in ["annual review", "pension transfer", "new business", "ad hoc withdrawal"]:
            current_type = text.strip().lower()
            rules[current_type] = []
        elif current_type and text:
            rules[current_type].append(text.strip().lower())
    return rules

# === Analyze CSV Rows ===
def analyze_csv(csv_df, rules):
    results = []
    issues_fields = Counter()

    for _, row in csv_df.iterrows():
        report_type = str(row.get("report type", "")).strip().lower()
        required_fields = rules.get(report_type, [])

        missing_fields = []
        for field in required_fields:
            value = row.get(field.lower(), "")
            if pd.isna(value) or str(value).strip().lower() in ["", "none", "nan"]:
                missing_fields.append(field)
                issues_fields[field] += 1

        if not missing_fields:
            status = "complete"
        elif len(missing_fields) <= 2:
            status = "incomplete"
        else:
            status = "missing data"

        results.append({
            "client": row.get("client name", "Unknown"),
            "report_type": report_type,
            "status": status,
            "missing": missing_fields
        })

    return results, issues_fields

# === Streamlit UI ===
st.title("📊 CSV Completeness Checker (by Report Type)")

csv_file = st.file_uploader("📥 Upload CSV File", type=["csv"])
rules_docx = st.file_uploader("📘 Upload Rules (DOCX)", type=["docx"])

if csv_file and rules_docx:
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip().str.lower()

    rules = load_rules(rules_docx)
    results, issues_fields = analyze_csv(df, rules)

    total = len(results)
    complete = sum(1 for r in results if r["status"] == "complete")
    incomplete = total - complete

    st.subheader("📈 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", total)
    col2.metric("✅ Complete", complete)
    col3.metric("❌ Incomplete", incomplete)

    st.subheader("🧾 Breakdown by Report Type")
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        breakdown = df_res.groupby(['report_type', 'status']).size().unstack(fill_value=0)
        st.dataframe(breakdown)

    st.subheader("⚠️ Common Missing Fields")
    if issues_fields:
        st.dataframe(pd.DataFrame(issues_fields.items(), columns=["Field", "Missing Count"]).sort_values(by="Missing Count", ascending=False))
    else:
        st.info("No missing fields found.")

    st.subheader("📋 Detailed Results")
    for r in results:
        with st.expander(f"{r['client']} ({r['report_type'].title()}): {r['status'].upper()}"):
            if r["missing"]:
                st.write("Missing Fields:", r["missing"])
            else:
                st.write("All required fields present ✅")

