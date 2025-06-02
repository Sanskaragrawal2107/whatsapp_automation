import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
import tempfile

# === Supabase Config ===
SUPABASE_URL = "https://ljfnqdellbkxokuldwmt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqZm5xZGVsbGJreG9rdWxkd210Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg4ODIwMzQsImV4cCI6MjA2NDQ1ODAzNH0.BsAoQM_xdhYGQNGHwNtHMdHSSxnrYhO5gSMQnCRtLb0"
BUCKET_NAME = "test"
EXPIRY_SECONDS = 3600
STORAGE_FOLDER = "uploads"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📄 PDF Uploader to Supabase with Signed URLs")

# === File Upload ===
uploaded_file = st.file_uploader("Upload CSV containing PDF paths", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if "file path" not in df.columns:
        st.error("❌ 'file path' column not found in CSV.")
        st.stop()

    st.write("📁 Found rows:", len(df))

    updated_rows = []
    for index, row in df.iterrows():
        local_path = row["file path"].strip()
        file_name = os.path.basename(local_path)
        supabase_path = f"{STORAGE_FOLDER}/{file_name}"

        try:
            with open(local_path, "rb") as f:
                supabase.storage.from_(BUCKET_NAME).update(
                    supabase_path, f, {"content-type": "application/pdf"}
                )

            signed = supabase.storage.from_(BUCKET_NAME).create_signed_url(
                supabase_path, EXPIRY_SECONDS
            )
            signed_url = signed.get("signedURL", "URL generation failed")
            df.at[index, "signed_url"] = signed_url
            st.success(f"✅ Uploaded: {file_name}")
        except Exception as e:
            df.at[index, "signed_url"] = f"ERROR: {e}"
            st.error(f"❌ Failed: {file_name} - {e}")

    # === Show Download Link ===
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        df.to_csv(tmp.name, index=False)
        st.download_button(
            label="📥 Download CSV with Signed URLs",
            data=open(tmp.name, "rb"),
            file_name="output_with_signed_urls.csv",
            mime="text/csv"
        )

    # Show table
    st.write("✅ Final Output Preview")
    st.dataframe(df)
