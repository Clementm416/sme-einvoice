import streamlit as st
import pandas as pd
import json
import os
import io
import datetime
from autokit_pro import SME_AutoKit_Pro, get_styled_df

st.set_page_config(page_title="SME E-Invoice Compliance System", layout="wide", page_icon="🛡️")

CLIENTS_PATH = "clients_database.json"
BUYERS_PATH  = "buyers_database.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def clean(val):
    """Convert nan/None to empty string"""
    s = str(val).strip()
    return "" if s in ("nan", "None", "NaN") else s

def format_display_df(df):
    display = df.copy()
    if 'Price' in display.columns:
        display['Price'] = display['Price'].apply(lambda x: f"RM {float(x):,.2f}" if pd.notna(x) else "")
    if 'Qty' in display.columns:
        display['Qty'] = display['Qty'].apply(lambda x: int(float(x)) if pd.notna(x) else "")
    if 'Suggested_MSIC' in display.columns:
        display['Suggested_MSIC'] = display['Suggested_MSIC'].apply(lambda x: str(x).split('.')[0].zfill(5))
    return display

def main():
    st.title("🛡️ SME E-Invoice Compliance & Review System")
    st.markdown("---")

    if 'kit' not in st.session_state:
        st.session_state.kit = SME_AutoKit_Pro()

    st.sidebar.header("⚙️ Control Panel")
    menu = st.sidebar.radio("Navigation", [
        "📂 Scan & Correct Data",
        "🏢 Seller Profiles",
        "👤 Buyer Profiles",
        "🧠 Learning Memory",
        "📦 Export LHDN JSON"
    ])

    # ════════════════════════════════════════════════════════
    # Page 1: Scan & Correct
    # ════════════════════════════════════════════════════════
    if menu == "📂 Scan & Correct Data":
        st.subheader("📂 Step 1: Select Seller (Your Client)")

        clients = load_json(CLIENTS_PATH)
        buyers  = load_json(BUYERS_PATH)

        if not clients:
            st.warning("⚠️ No seller profiles found. Please go to 【🏢 Seller Profiles】 to add one first.")
            return

        selected_client = st.selectbox("Select Client Company (Seller)", list(clients.keys()))
        client_info = clients[selected_client]

        with st.expander(f"📋 {selected_client} — Company Details", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.info(f"**TIN**\n\n{client_info.get('tin', 'N/A')}")
            c2.info(f"**Registration No.**\n\n{client_info.get('reg_no', 'N/A')}")
            c3.info(f"**SST No.**\n\n{client_info.get('sst_no', 'N/A') or '(Exempt)'}")
            st.info(f"**Address:** {client_info.get('address', 'N/A')}")

        st.markdown("---")
        st.subheader("👤 Step 2: Buyer Information")

        buyer_mode = st.radio("Buyer Type", ["Select from Profile (B2B)", "One-time Entry (Retail / Walk-in)"], horizontal=True)
        buyer_info = {}

        if buyer_mode == "Select from Profile (B2B)":
            if not buyers:
                st.warning("⚠️ No buyer profiles yet. Go to 【👤 Buyer Profiles】 to add, or use one-time entry.")
            else:
                selected_buyer = st.selectbox("Select Buyer Company", list(buyers.keys()))
                buyer_info = buyers[selected_buyer]
                b1, b2, b3 = st.columns(3)
                b1.success(f"**TIN:** {buyer_info.get('tin', 'N/A')}")
                b2.success(f"**Reg. No.:** {buyer_info.get('reg_no', 'N/A')}")
                b3.success(f"**Address:** {buyer_info.get('address', 'N/A')}")
                buyer_info['name'] = selected_buyer
        else:
            r1, r2 = st.columns(2)
            with r1:
                retail_name    = st.text_input("Buyer Name / Company", placeholder="e.g. Ahmad bin Ali / ABC Trading")
                retail_tin     = st.text_input("Buyer TIN (enter 'NA' if none)", placeholder="e.g. IG12345678900")
            with r2:
                retail_reg     = st.text_input("Registration No. (optional)", placeholder="e.g. 202201056789")
                retail_address = st.text_input("Buyer Address", placeholder="e.g. No. 5, Jalan ABC, Johor Bahru")
            buyer_info = {
                "name":    retail_name,
                "tin":     retail_tin or "NA",
                "reg_no":  retail_reg or "NA",
                "address": retail_address or "NA"
            }

        st.markdown("---")
        st.subheader("🧾 Step 3: Invoice Details")
        inv1, inv2, inv3 = st.columns(3)
        with inv1:
            invoice_date = st.date_input("Invoice Date", value=datetime.date.today())
        with inv2:
            currency = st.selectbox("Currency", ["MYR", "USD", "SGD"])
        with inv3:
            invoice_note = st.text_input("Remarks (optional)", placeholder="e.g. Payment due 30 days")

        st.markdown("---")
        st.subheader("📂 Step 4: Upload Sales Data")
        uploaded_file = st.file_uploader("Upload client sales data (Excel / CSV)", type=['xlsx', 'csv'])

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

                target_col = next((c for c in df.columns if any(
                    k in str(c).lower() for k in ['item', 'desc', '商品', '描述'])), None)

                if target_col:
                    results = df[target_col].apply(st.session_state.kit.match_logic)
                    df['Suggested_MSIC']    = [r[0] for r in results]
                    df['Compliance_Status'] = [r[1] for r in results]
                    df['Export_Ready']      = df['Compliance_Status'].apply(lambda x: "YES" if "🟢" in x else "NO")

                    st.write("### 📊 Data Overview")
                    ready_df = df[df['Export_Ready'] == "YES"]
                    total_sales, total_tax = 0.0, 0.0
                    zero_tax_codes = ["47111"]

                    for _, row in ready_df.iterrows():
                        p    = float(row.get('Price', 0.0))
                        q    = float(row.get('Qty', 1.0))
                        code = str(row['Suggested_MSIC']).split('.')[0].zfill(5)
                        rate = 0.00 if code in zero_tax_codes else 0.06
                        sub  = p * q
                        total_sales += sub
                        total_tax   += sub * rate

                    total  = len(df)
                    green  = len(ready_df)
                    yellow = df['Compliance_Status'].str.contains('🟡').sum()
                    red    = df['Compliance_Status'].str.contains('🔴').sum()

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Client", selected_client)
                    m2.metric("🟢 Green", f"{green} / {total}")
                    m3.metric("🟡 Yellow", f"{yellow}")
                    m4.metric("Est. Revenue", f"RM {total_sales:,.2f}")
                    m5.metric("SST Payable", f"RM {total_tax:,.2f}", delta_color="inverse")
                    st.markdown("---")

                    st.write("### 🔍 Compliance Scan Results")
                    display_df = format_display_df(df)

                    def row_style(r):
                        status = str(r.get('Compliance_Status', ''))
                        bg = '#d4edda' if '🟢' in status else '#fff3cd' if '🟡' in status else '#f8d7da'
                        return [f'background-color: {bg}; color: #212529;' for _ in r]

                    st.dataframe(display_df.style.apply(row_style, axis=1), use_container_width=True)

                    st.markdown("---")
                    st.subheader("🛠️ Quick Correction (Learning Mode)")
                    needs_fix = df[df['Export_Ready'] == "NO"][target_col].unique()

                    if len(needs_fix) > 0:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            item_to_fix = st.selectbox("Select item to correct", needs_fix)
                        with col2:
                            new_code = st.text_input("Correct MSIC Code (5 digits)")
                        with col3:
                            st.write(""); st.write("")
                            if st.button("Confirm & Remember") and item_to_fix and new_code:
                                st.session_state.kit.save_correction(item_to_fix, new_code)
                                st.success("🧠 Saved! Refresh to apply.")
                                st.balloons()
                    else:
                        st.success("✅ All items passed! No manual correction needed.")

                    st.markdown("---")
                    st.subheader("📥 Download & Sync Data")

                    styled_df = get_styled_df(df)
                    output_buffer = io.BytesIO()
                    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                        styled_df.to_excel(writer, index=False)

                    safe_name = selected_client.replace(" ", "_").replace("/", "_")
                    internal_save_path = f"Optimized_{safe_name}.xlsx"

                    df['_client_name']    = selected_client
                    df['_client_tin']     = client_info.get('tin', '')
                    df['_client_reg']     = client_info.get('reg_no', '')
                    df['_client_address'] = client_info.get('address', '')
                    df['_client_sst']     = client_info.get('sst_no', '')
                    df['_buyer_name']     = buyer_info.get('name', '')
                    df['_buyer_tin']      = buyer_info.get('tin', '')
                    df['_buyer_reg']      = buyer_info.get('reg_no', '')
                    df['_buyer_address']  = buyer_info.get('address', '')
                    df['_invoice_date']   = str(invoice_date)
                    df['_currency']       = currency
                    df['_invoice_note']   = invoice_note
                    df.to_excel(internal_save_path, index=False)

                    st.download_button(
                        label="🚀 Download Verified Excel Report",
                        data=output_buffer.getvalue(),
                        file_name=f"Verified_{selected_client}_{uploaded_file.name}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.caption(f"✅ Backed up to: {internal_save_path} — ready for JSON export.")

                else:
                    st.warning("⚠️ Cannot find item column. Make sure headers contain 'Item' or 'Description'.")

            except Exception as e:
                st.error(f"Error reading file: {e}")

    # ════════════════════════════════════════════════════════
    # Page 2: Seller Profiles
    # ════════════════════════════════════════════════════════
    elif menu == "🏢 Seller Profiles":
        st.subheader("🏢 Seller Profiles (Your Clients)")
        clients = load_json(CLIENTS_PATH)

        with st.expander("➕ Add New Client", expanded=len(clients) == 0):
            n1, n2 = st.columns(2)
            with n1:
                new_name    = st.text_input("Company Name *", placeholder="e.g. Kedai Hardware ABC Sdn Bhd")
                new_tin     = st.text_input("TIN Number *", placeholder="e.g. C12345678900")
                new_reg     = st.text_input("SSM Registration No. *", placeholder="e.g. 202301012345")
            with n2:
                new_sst     = st.text_input("SST Number (leave blank if exempt)", placeholder="e.g. W10-1234-12345678")
                new_msic    = st.text_input("Primary MSIC Code *", placeholder="e.g. 46631")
                new_address = st.text_area("Business Address *", placeholder="No. 1, Jalan ABC, 12345 Johor Bahru, Johor", height=80)

            if st.button("💾 Save Client"):
                if new_name and new_tin and new_reg and new_address and new_msic:
                    clients[new_name] = {
                        "tin": new_tin.strip(), "reg_no": new_reg.strip(),
                        "sst_no": new_sst.strip(), "msic": new_msic.strip(),
                        "address": new_address.strip()
                    }
                    save_json(CLIENTS_PATH, clients)
                    st.success(f"✅ Saved: {new_name}")
                    st.rerun()
                else:
                    st.error("⚠️ Please fill in all required fields (marked *).")

        st.markdown("---")
        if clients:
            st.write(f"### 📋 Client List ({len(clients)} companies)")
            for name, info in clients.items():
                with st.expander(f"🏢 {name}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**TIN:** {info.get('tin','')}")
                    c2.write(f"**Reg. No.:** {info.get('reg_no','')}")
                    c3.write(f"**SST:** {info.get('sst_no','') or '(Exempt)'}")
                    st.write(f"**MSIC:** {info.get('msic','')} | **Address:** {info.get('address','')}")
                    if st.button("🗑️ Delete", key=f"del_c_{name}"):
                        del clients[name]
                        save_json(CLIENTS_PATH, clients)
                        st.rerun()
        else:
            st.info("No clients added yet.")

    # ════════════════════════════════════════════════════════
    # Page 3: Buyer Profiles
    # ════════════════════════════════════════════════════════
    elif menu == "👤 Buyer Profiles":
        st.subheader("👤 Buyer Profiles (Fixed B2B Customers)")
        buyers = load_json(BUYERS_PATH)

        with st.expander("➕ Add New Buyer", expanded=len(buyers) == 0):
            b1, b2 = st.columns(2)
            with b1:
                b_name    = st.text_input("Buyer Company Name *", placeholder="e.g. Pemborong XYZ Sdn Bhd")
                b_tin     = st.text_input("Buyer TIN *", placeholder="e.g. C98765432100")
                b_reg     = st.text_input("Registration No.", placeholder="e.g. 202201056789")
            with b2:
                b_email   = st.text_input("Email (optional)", placeholder="e.g. accounts@xyz.com")
                b_phone   = st.text_input("Phone (optional)", placeholder="e.g. 07-1234567")
                b_address = st.text_area("Buyer Address *", placeholder="No. 5, Jalan XYZ, Johor Bahru", height=80)

            if st.button("💾 Save Buyer"):
                if b_name and b_tin and b_address:
                    buyers[b_name] = {
                        "tin": b_tin.strip(), "reg_no": b_reg.strip(),
                        "email": b_email.strip(), "phone": b_phone.strip(),
                        "address": b_address.strip()
                    }
                    save_json(BUYERS_PATH, buyers)
                    st.success(f"✅ Saved: {b_name}")
                    st.rerun()
                else:
                    st.error("⚠️ Please fill in Company Name, TIN and Address.")

        st.markdown("---")
        if buyers:
            st.write(f"### 📋 Buyer List ({len(buyers)} companies)")
            for name, info in buyers.items():
                with st.expander(f"👤 {name}"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**TIN:** {info.get('tin','')}")
                    c2.write(f"**Reg. No.:** {info.get('reg_no','') or '(None)'}")
                    st.write(f"**Address:** {info.get('address','')}")
                    if st.button("🗑️ Delete", key=f"del_b_{name}"):
                        del buyers[name]
                        save_json(BUYERS_PATH, buyers)
                        st.rerun()
        else:
            st.info("No buyers added yet.")

    # ════════════════════════════════════════════════════════
    # Page 4: Learning Memory
    # ════════════════════════════════════════════════════════
    elif menu == "🧠 Learning Memory":
        st.subheader("🧠 Industry Learning Memory")
        memory = load_json('user_learning_memory.json')
        if memory:
            st.table(pd.DataFrame(list(memory.items()), columns=['Item Name', 'Locked MSIC Code']))
        else:
            st.info("Memory is empty. No manual corrections recorded yet.")

    # ════════════════════════════════════════════════════════
    # Page 5: Export JSON
    # ════════════════════════════════════════════════════════
    elif menu == "📦 Export LHDN JSON":
        st.subheader("📦 Generate Submission Package (SDK Ready)")

        opt_files = [f for f in os.listdir('.') if f.startswith("Optimized_") and f.endswith(".xlsx")]

        if not opt_files:
            st.warning("⚠️ No optimized files detected. Please process data in 【Scan & Correct Data】 first.")
        else:
            st.success(f"✅ {len(opt_files)} file(s) ready for export")
            for f in opt_files:
                st.caption(f"📄 {f}")

        if st.button("Generate JSON Package"):
            with st.spinner('Scanning data and calculating tax...'):
                if st.session_state.kit.generate_lhdn_batch_json():
                    st.success("✅ JSON package generated successfully!")
                    if os.path.exists('lhdn_submission_batch.json'):
                        with open('lhdn_submission_batch.json', 'r', encoding='utf-8') as f:
                            json_data = f.read()
                        st.download_button(
                            label="💾 Download JSON Submission Package",
                            data=json_data,
                            file_name="LHDN_Final_Submission.json",
                            mime="application/json"
                        )
                        with st.expander("👁️ Preview JSON"):
                            st.json(json.loads(json_data))
                else:
                    st.error("❌ Export failed: No items marked as YES (green) found.")

if __name__ == "__main__":
    main()
