import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io 
import shutil
import os

# ==========================================
# 1. DATABASE CONFIGURATION
# ==========================================
DB_FILE = "inventory_system.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    customer_code TEXT PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    joined_date DATE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    product_code TEXT PRIMARY KEY,
                    name TEXT,
                    current_stock INTEGER DEFAULT 0,
                    pack_size_multiplier INTEGER DEFAULT 1,
                    unit_type TEXT DEFAULT 'Single')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP,
                    type TEXT,
                    product_code TEXT,
                    customer_code TEXT,
                    quantity_packs INTEGER, 
                    total_units INTEGER,    
                    FOREIGN KEY(product_code) REFERENCES products(product_code),
                    FOREIGN KEY(customer_code) REFERENCES customers(customer_code))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_customers (
                    customer_code TEXT, name TEXT, address TEXT, joined_date DATE, deleted_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_products (
                    product_code TEXT, name TEXT, current_stock INTEGER, pack_size_multiplier INTEGER, unit_type TEXT, deleted_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_transactions (
                    original_id INTEGER, date TIMESTAMP, type TEXT, product_code TEXT, customer_code TEXT, 
                    quantity_packs INTEGER, total_units INTEGER, deleted_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def run_query(query, params=(), return_df=False):
    with sqlite3.connect(DB_FILE) as conn:
        if return_df:
            return pd.read_sql(query, conn, params=params)
        else:
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
            return c

init_db()

# Session State
if 'page_selection' not in st.session_state: st.session_state.page_selection = "📊 Executive Dashboard"
if 'cart' not in st.session_state: st.session_state.cart = []
if 'valid_customer' not in st.session_state: st.session_state.valid_customer = None
if 'dash_selected_cust' not in st.session_state: st.session_state.dash_selected_cust = None
if 'selected_product_code' not in st.session_state: st.session_state.selected_product_code = None 

# Edit State Variables
if 'edit_prod_data' not in st.session_state: st.session_state.edit_prod_data = None
if 'edit_cust_data' not in st.session_state: st.session_state.edit_cust_data = None
if 'cart_edit_index' not in st.session_state: st.session_state.cart_edit_index = None
if 'cust_history_view' not in st.session_state: st.session_state.cust_history_view = None
if 'prod_history_view' not in st.session_state: st.session_state.prod_history_view = None 
if 'edit_trans_id' not in st.session_state: st.session_state.edit_trans_id = None

# ==========================================
# 2. VISUALS & STYLING
# ==========================================
st.set_page_config(page_title="WPC Plastic MS", layout="wide", page_icon="🏭")

st.markdown("""
<style>
    html, body, [class*="css"] {font-size: 18px !important;}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {background-color: #0e1117 !important; border-right: 1px solid #303030;}
    .stRadio label {
        font-size: 20px !important; color: #ffffff !important;
        background-color: #262730; padding: 15px; margin-bottom: 10px;
        border-radius: 8px; border: 1px solid #404040; width: 100%; display: block;
    }
    .stRadio label:hover {background-color: #4e8cff !important; border-color: #4e8cff;}

    /* Main */
    div[data-testid="stMetricValue"] {font-size: 36px !important; font-weight: bold; color: #4e8cff;}
    
    .stTextInput input, .stNumberInput input {font-size: 20px !important; height: 50px !important;}
    .stSelectbox div[data-baseweb="select"] {font-size: 20px !important;}
    button {font-size: 18px !important; font-weight: 600 !important; padding: 10px 20px !important;}
</style>
""", unsafe_allow_html=True)

st.title("🏭 WPC Plastic Management System")

# SIDEBAR MENU
menu_options = [
    "📊 Executive Dashboard", 
    "🛒 Order", 
    "👥 Customer Database", 
    "📦 Inventory Database", 
    "♻️ Recycle Bin"
]

idx = 0
if st.session_state.page_selection in menu_options:
    idx = menu_options.index(st.session_state.page_selection)
selected = st.sidebar.radio("Main Menu", menu_options, index=idx)
if selected != st.session_state.page_selection:
    st.session_state.page_selection = selected
    st.rerun()
page = st.session_state.page_selection

# --- BACKUP & EXPORT FEATURE ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export Data")

# Excel Export Logic
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# Export Customer Button
if st.sidebar.button("📄 Export Customers"):
    df_c = run_query("SELECT * FROM customers", return_df=True)
    st.sidebar.download_button("Download CSV", data=df_c.to_csv(index=False), file_name="customers.csv", mime="text/csv")

# Export Inventory Button
if st.sidebar.button("📦 Export Inventory"):
    df_p = run_query("SELECT * FROM products", return_df=True)
    st.sidebar.download_button("Download CSV", data=df_p.to_csv(index=False), file_name="inventory.csv", mime="text/csv")

if st.sidebar.button("💾 Create System Backup"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    shutil.copy(DB_FILE, backup_filename)
    st.sidebar.success(f"Saved: {backup_filename}")

# Helper Functions
def format_df(df):
    return df.rename(columns={
        "product_code": "📦 Product Code", "name": "🏷️ Product Name", "current_stock": "📊 Quantity",
        "pack_size_multiplier": "📦 Pack Size", "customer_code": "👤 Customer",
        "address": "📍 Address", "date": "📅 Date", "type": "Type",
        "total_units": "🔢 Total Qty", "quantity_packs": "📦 Qty (Packs)", "unit_type": "📏 Type"
    })

# ==========================================
# PAGE: DASHBOARD
# ==========================================
if page == "📊 Executive Dashboard":
    st.header("📊 Executive Overview")
    
    try:
        low_stock_count = run_query("SELECT COUNT(*) as c FROM products WHERE (current_stock * pack_size_multiplier) < 150", return_df=True)['c'].iloc[0]
    except:
        low_stock_count = 0
    
    st.metric("⚠️ Low Stock Items", f"{low_stock_count}", delta_color="inverse")
    st.divider()

    # --- ADVANCED DASHBOARD SEARCH ---
    c_search, p_search = st.columns(2)
    
    with c_search:
        st.subheader("👤 Customer Analysis")
        dash_c_input = st.text_input("Find Customer (Name/Code)", placeholder="Type 'Ali'...", key="dash_c_in").strip()
        
        if dash_c_input:
            term = f"%{dash_c_input}%"
            res = run_query("SELECT * FROM customers WHERE name LIKE ? OR customer_code LIKE ?", (term, term), return_df=True)
            
            if len(res) == 0:
                st.warning("No Customer Found")
            elif len(res) == 1:
                st.session_state.dash_selected_cust = res.iloc[0]['customer_code']
            else:
                st.info(f"Found {len(res)} matches:")
                for i, row in res.iterrows():
                    if st.button(f"👉 {row['name']} ({row['customer_code']})", key=f"d_c_{row['customer_code']}"):
                        st.session_state.dash_selected_cust = row['customer_code']
                        st.rerun()

        if st.session_state.dash_selected_cust:
            cust_id = st.session_state.dash_selected_cust
            cust_info = run_query("SELECT * FROM customers WHERE customer_code=?", (cust_id,), return_df=True).iloc[0]
            
            st.success(f"📊 Analysis for: **{cust_info['name']}**")
            
            sales_data = run_query("""
                SELECT t.date, t.type, p.product_code, p.name as product_name, t.quantity_packs 
                FROM transactions t 
                JOIN products p ON t.product_code = p.product_code
                WHERE t.customer_code = ? 
            """, (cust_id,), return_df=True)
            
            if not sales_data.empty:
                # NET LOGIC
                sales_data['net_qty'] = sales_data.apply(
                    lambda x: x['quantity_packs'] if x['type'] == 'SALE' else -x['quantity_packs'], axis=1
                )
                
                sales_data['date'] = pd.to_datetime(sales_data['date'])
                
                # --- HISTORY TABLE ---
                st.markdown("### 📅 Purchase History")
                hist_display = sales_data[['date', 'type', 'product_code', 'product_name', 'quantity_packs']].copy()
                hist_display['date'] = hist_display['date'].dt.strftime('%Y-%m-%d')
                hist_display.columns = ['Date', 'Type', 'Code', 'Product', 'Qty (Packs)']
                st.dataframe(hist_display.sort_values(by='Date', ascending=False), use_container_width=True)

                # --- GROWTH METRICS ---
                st.markdown("### 📈 Monthly Growth (Net Packs)")
                now = datetime.now()
                current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                prev_month_end = current_month_start - timedelta(seconds=1)
                prev_month_start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                q1_data = sales_data[sales_data['date'] >= current_month_start]
                q2_data = sales_data[(sales_data['date'] >= prev_month_start) & (sales_data['date'] <= prev_month_end)]
                
                q1_group = q1_data.groupby(['product_code', 'product_name'])['net_qty'].sum().rename("Q1 (This Month)")
                q2_group = q2_data.groupby(['product_code', 'product_name'])['net_qty'].sum().rename("Q2 (Last Month)")
                
                analysis_df = pd.concat([q1_group, q2_group], axis=1).fillna(0)
                analysis_df['Growth %'] = ((analysis_df['Q1 (This Month)'] - analysis_df['Q2 (Last Month)']) / analysis_df['Q2 (Last Month)'].replace(0, 1)) * 100
                analysis_df['Growth %'] = analysis_df['Growth %'].apply(lambda x: f"{x:+.1f}%")
                
                st.dataframe(analysis_df.reset_index(), use_container_width=True)
            else:
                st.info("No transaction history found for this customer.")

    with p_search:
        st.subheader("📦 Product Check")
        dash_p_input = st.text_input("Find Product", placeholder="10HH...", key="dash_p_in").strip()
        
        if dash_p_input:
            term = f"%{dash_p_input}%"
            res = run_query("SELECT * FROM products WHERE name LIKE ? OR product_code LIKE ?", (term, term), return_df=True)
            
            if len(res) == 0:
                st.warning("No Product Found")
            else:
                st.caption(f"Found {len(res)} matches:")
                for i, row in res.iterrows():
                    with st.expander(f"📦 {row['name']} ({row['product_code']})"):
                        st.write(f"**Stock Quantity:** {row['current_stock']}")
                        st.write(f"**Pack Type:** {row['unit_type']}")
                        # Clean Calculation
                        try:
                            s = int(str(row['current_stock']).replace("b'", "").replace("'", ""))
                        except: s = 0
                        try:
                            m = int(str(row['pack_size_multiplier']).replace("b'", "").replace("'", ""))
                        except: m = 1
                        st.write(f"**Total Units Breakdown:** {s * m}")

# ==========================================
# PAGE: ORDER
# ==========================================
elif page == "🛒 Order":
    st.header("🛒 New Order / Stock Adjustment")

    # --- STEP 1: CUSTOMER ---
    c_input = st.text_input("Search Customer (Name or Code)", placeholder="Type 'Ali'...", key="c_search").strip()
    
    selected_cust_data = None
    
    if c_input:
        search_term = f"%{c_input}%"
        results = run_query("SELECT * FROM customers WHERE customer_code LIKE ? OR name LIKE ?", (search_term, search_term), return_df=True)
        
        if len(results) == 0:
            st.error("❌ No Customer Found")
            if st.button("➕ Create New Customer"):
                st.session_state.page_selection = "👥 Customer Database"
                st.rerun()
        elif len(results) == 1:
            selected_cust_data = results.iloc[0]
        else:
            st.warning(f"🔍 Found {len(results)} matches:")
            for i, row in results.iterrows():
                if st.button(f"👤 {row['name']} ({row['customer_code']}) - {row['address']}", key=f"sel_{row['customer_code']}"):
                    st.session_state.valid_customer = row['customer_code']
                    st.rerun()
            if st.session_state.valid_customer:
                filtered = results[results['customer_code'] == st.session_state.valid_customer]
                if not filtered.empty:
                    selected_cust_data = filtered.iloc[0]

    if selected_cust_data is not None:
        st.session_state.valid_customer = selected_cust_data['customer_code']
        
        # Info Box
        last_ord = run_query("SELECT MAX(date) as d FROM transactions WHERE customer_code=?", (selected_cust_data['customer_code'],), return_df=True)
        last_date_str = pd.to_datetime(last_ord.iloc[0]['d']).strftime('%d/%m/%Y') if pd.notnull(last_ord.iloc[0]['d']) else "N/A"
        join_date_str = pd.to_datetime(selected_cust_data['joined_date']).strftime('%d/%m/%Y')

        st.code(f"""
ID: {selected_cust_data['customer_code']}
NAME: {selected_cust_data['name']}
ADDRESS: {selected_cust_data['address']}
JOINED: {join_date_str}
LAST ORDER: {last_date_str}
        """, language="text")
    
    st.divider()

    # --- STEP 2: ITEMS ---
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    
    with c1:
        p_search = st.text_input("Search Product (Name or Code)", key="p_input", placeholder="Type 'Bag' or '10HH'").strip().upper()
        if p_search:
            term = f"%{p_search}%"
            p_results = run_query("SELECT * FROM products WHERE product_code LIKE ? OR name LIKE ?", (term, term), return_df=True)
            if len(p_results) == 1:
                st.session_state.selected_product_code = p_results.iloc[0]['product_code']
            elif len(p_results) > 1:
                st.caption(f"Found {len(p_results)} matches:")
                for i, row in p_results.iterrows():
                    # UPDATED: Show Stock in Button Label
                    btn_label = f"{row['product_code']} - {row['name']} (Qty: {row['current_stock']})"
                    if st.button(btn_label, key=f"psel_{row['product_code']}"):
                        st.session_state.selected_product_code = row['product_code']
                        st.rerun()
        
        if st.session_state.selected_product_code:
            prod_info = run_query("SELECT name, current_stock FROM products WHERE product_code=?", (st.session_state.selected_product_code,), return_df=True).iloc[0]
            st.success(f"🔹 Selected: **{st.session_state.selected_product_code}** | {prod_info['name']} | **Qty: {prod_info['current_stock']}**")

    with c2:
        txn_type = st.selectbox("Transaction Type", ["SALE", "RETURN", "LOST"])
    with c3:
        qty = st.number_input("Quantity", min_value=1, value=1)
    with c4:
        st.write("")
        st.write("")
        if st.button("➕ Add Item"):
            # --- SECURITY CHECK ---
            if not st.session_state.valid_customer:
                st.error("⚠️ PLEASE SELECT A CUSTOMER FIRST (Step 1)")
            elif not st.session_state.selected_product_code:
                st.error("⚠️ Please select a product.")
            else:
                cust_final = st.session_state.valid_customer
                if txn_type == "LOST": cust_final = "INTERNAL"
                prod_code = st.session_state.selected_product_code
                
                p_data = run_query("SELECT * FROM products WHERE product_code=?", (prod_code,), return_df=True)
                if not p_data.empty:
                    # Clean Stock
                    try: current_stock = int(p_data.iloc[0]['current_stock'])
                    except: current_stock = 0
                    try: mult = int(p_data.iloc[0]['pack_size_multiplier'])
                    except: mult = 1
                    
                    # --- RETURN LOGIC FIX ---
                    if txn_type == 'RETURN':
                        # Check if customer has bought enough to return
                        sales_hist = run_query("SELECT type, quantity_packs FROM transactions WHERE customer_code=? AND product_code=?", (cust_final, prod_code), return_df=True)
                        sales_hist['quantity_packs'] = pd.to_numeric(sales_hist['quantity_packs'], errors='coerce').fillna(0).astype(int)
                        
                        bought = sales_hist[sales_hist['type'] == 'SALE']['quantity_packs'].sum()
                        returned_already = sales_hist[sales_hist['type'] == 'RETURN']['quantity_packs'].sum()
                        net_owned = bought - returned_already
                        
                        if qty > net_owned:
                            # UPDATED RETURN ALERT TEXT
                            st.error(f"❌ Invalid Return: Customer only has {net_owned} packs.")
                            st.stop() 

                    # --- STOCK CHECK (For Sale/Lost) ---
                    pending_qty = 0
                    for item in st.session_state.cart:
                        if item['code'] == prod_code and item['type'] in ["SALE", "LOST"]:
                            pending_qty += item['qty']
                    
                    total_requested = qty + pending_qty
                    
                    if txn_type in ["SALE", "LOST"] and current_stock < total_requested:
                        st.error(f"❌ Insufficient Stock! Available: {current_stock}, Requested (Total): {total_requested}")
                    else:
                        found = False
                        for item in st.session_state.cart:
                            if item['code'] == prod_code and item['type'] == txn_type:
                                item['qty'] += qty
                                item['total'] = int(item['qty'] * mult)
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "code": prod_code, "name": p_data.iloc[0]['name'], "type": txn_type,
                                "qty": int(qty), "total": int(qty * mult), "customer": cust_final,
                                "mult": mult 
                            })
                        st.success("Added!")
                        st.session_state.selected_product_code = None
                        st.rerun()

    # --- CART ---
    if st.session_state.cart:
        st.divider()
        cust_display = st.session_state.valid_customer if st.session_state.valid_customer else "Internal"
        st.markdown(f"### 🛒 Order Summary")
        
        for i, item in enumerate(st.session_state.cart):
            
            is_editing = (st.session_state.cart_edit_index == i)
            col_a, col_b, col_c, col_d, col_e, col_f = st.columns([1, 2, 1, 2, 0.5, 0.5])
            col_a.write(f"**{item['code']}**")
            col_b.write(item['name'])
            col_c.write(f"{item['type']}")
            
            if is_editing:
                new_qty = col_d.number_input("New Qty", min_value=1, value=item['qty'], key=f"edit_qty_{i}")
                if col_e.button("💾", key=f"save_{i}"):
                    st.session_state.cart[i]['qty'] = new_qty
                    multiplier = st.session_state.cart[i].get('mult', 1) 
                    st.session_state.cart[i]['total'] = int(new_qty * multiplier)
                    st.session_state.cart_edit_index = None 
                    st.rerun()
            else:
                col_d.write(f"Qty: {item['qty']} (Total: {item['total']})")
                if col_e.button("✏️", key=f"ed_{i}"):
                    st.session_state.cart_edit_index = i
                    st.rerun()
            
            if col_f.button("❌", key=f"rem_{i}"):
                st.session_state.cart.pop(i)
                if st.session_state.cart_edit_index == i:
                    st.session_state.cart_edit_index = None
                st.rerun()
            st.markdown("<hr style='margin: 0; border-color: #444;'>", unsafe_allow_html=True)
            
        if st.button("✅ CONFIRM & PROCESS", type="primary", use_container_width=True):
            now = datetime.now()
            for item in st.session_state.cart:
                run_query("INSERT INTO transactions (date, type, product_code, customer_code, quantity_packs, total_units) VALUES (?,?,?,?,?,?)", 
                    (now, item['type'], item['code'], item['customer'], int(item['qty']), int(item['total'])))
                adj = -int(item['qty']) if item['type'] in ['SALE', 'LOST'] else int(item['qty'])
                run_query("UPDATE products SET current_stock = current_stock + ? WHERE product_code=?", (adj, item['code']))
            st.session_state.cart = []
            st.session_state.cart_edit_index = None
            st.balloons()
            st.success("Processed!")
            st.rerun()

# ==========================================
# PAGE: CUSTOMER DB
# ==========================================
elif page == "👥 Customer Database":
    st.header("👥 Customer Database")
    
    # --- CUSTOMER HISTORY/EDIT VIEW ---
    if st.session_state.cust_history_view:
        view_code = st.session_state.cust_history_view
        st.info(f"📜 Viewing Order History for: **{view_code}**")
        
        if st.button("⬅️ Back to Customer List"):
            st.session_state.cust_history_view = None
            st.session_state.edit_trans_id = None
            st.rerun()
            
        # Get Transactions
        hist_df = run_query("SELECT id, date, type, product_code, quantity_packs, total_units FROM transactions WHERE customer_code=? ORDER BY date DESC", (view_code,), return_df=True)
        
        for idx, row in hist_df.iterrows():
            is_row_edit = (st.session_state.edit_trans_id == row['id'])
            
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 2, 1, 1, 1])
            c1.write(f"{row['date']}")
            c2.write(f"{row['type']}")
            c3.write(f"{row['product_code']}")
            
            if is_row_edit:
                new_q = c4.number_input("Qty", value=row['quantity_packs'], key=f"h_e_{row['id']}")
                if c5.button("💾", key=f"h_s_{row['id']}"):
                    # Logic: Revert Old Stock -> Apply New Stock
                    pmult = run_query("SELECT pack_size_multiplier FROM products WHERE product_code=?", (row['product_code'],), return_df=True)
                    mult = pmult.iloc[0]['pack_size_multiplier'] if not pmult.empty else 1
                    
                    old_qty = row['quantity_packs']
                    diff = new_q - old_qty
                    
                    if row['type'] in ['SALE', 'LOST']:
                        run_query("UPDATE products SET current_stock = current_stock - ? WHERE product_code=?", (diff, row['product_code']))
                    else: # RETURN
                        run_query("UPDATE products SET current_stock = current_stock + ? WHERE product_code=?", (diff, row['product_code']))
                        
                    new_total = int(new_q * mult)
                    run_query("UPDATE transactions SET quantity_packs=?, total_units=? WHERE id=?", (new_q, new_total, row['id']))
                    
                    st.success("Updated!")
                    st.session_state.edit_trans_id = None
                    st.rerun()
            else:
                c4.write(f"Qty: {row['quantity_packs']}")
                if c5.button("✏️", key=f"h_btn_{row['id']}"):
                    st.session_state.edit_trans_id = row['id']
                    st.rerun()
            
            # --- NEW: DELETE TRANSACTION BUTTON ---
            if c6.button("🗑️", key=f"del_tr_{row['id']}"):
                # Reverse Stock before deleting
                if row['type'] in ['SALE', 'LOST']:
                    run_query("UPDATE products SET current_stock = current_stock + ? WHERE product_code=?", (row['quantity_packs'], row['product_code']))
                else: # RETURN
                    run_query("UPDATE products SET current_stock = current_stock - ? WHERE product_code=?", (row['quantity_packs'], row['product_code']))
                
                # Move to Recycle Bin
                run_query("INSERT INTO deleted_transactions (original_id, date, type, product_code, customer_code, quantity_packs, total_units, deleted_at) VALUES (?,?,?,?,?,?,?,?)",
                          (row['id'], row['date'], row['type'], row['product_code'], view_code, row['quantity_packs'], row['total_units'], datetime.now()))
                
                # Delete
                run_query("DELETE FROM transactions WHERE id=?", (row['id'],))
                st.success("Transaction Deleted and Stock Reversed!")
                st.rerun()
            st.divider()
            
    else:
        # NORMAL LIST VIEW
        default_code, default_name, default_addr = "", "", ""
        edit_mode = False
        
        if st.session_state.edit_cust_data is not None:
            edit_mode = True
            default_code = st.session_state.edit_cust_data['customer_code']
            default_name = st.session_state.edit_cust_data['name']
            default_addr = st.session_state.edit_cust_data['address']
        
        with st.expander(f"➕ {'Edit' if edit_mode else 'Add New'} Customer", expanded=edit_mode):
            c1, c2, c3 = st.columns(3)
            n_code = c1.text_input("Code (Unique)", value=default_code, disabled=edit_mode).strip().upper()
            n_name = c2.text_input("Name", value=default_name)
            n_addr = c3.text_input("Address", value=default_addr)
            
            if st.button("Save Customer"):
                if not edit_mode:
                    check = run_query("SELECT * FROM customers WHERE customer_code=?", (n_code,), return_df=True)
                    if not check.empty:
                        st.error("Customer Code already exists!")
                    else:
                        run_query("INSERT INTO customers VALUES (?,?,?,?)", (n_code, n_name, n_addr, datetime.now()))
                        st.success("Saved!")
                        st.rerun()
                else:
                    run_query("UPDATE customers SET name=?, address=? WHERE customer_code=?", (n_name, n_addr, n_code))
                    st.success("Updated!")
                    st.session_state.edit_cust_data = None 
                    st.rerun()
                    
            if edit_mode and st.button("Cancel Edit"):
                st.session_state.edit_cust_data = None
                st.rerun()

        cust_search = st.text_input("Search Customer Database", placeholder="Name or Code")
        query = "SELECT * FROM customers"
        params = ()
        if cust_search:
            query += " WHERE name LIKE ? OR customer_code LIKE ?"
            term = f"%{cust_search}%"
            params = (term, term)
        
        df = run_query(query, params, return_df=True)
        
        h1, h2, h3, h4 = st.columns([1, 2, 3, 2])
        h1.write("**ID**"); h2.write("**Name**"); h3.write("**Address**"); h4.write("**Action**")
        
        for i, row in df.iterrows():
            c1, c2, c3, c4 = st.columns([1, 2, 3, 2])
            c1.write(row['customer_code'])
            c2.write(row['name'])
            c3.write(row['address'])
            
            col_hist, col_edit, col_del = c4.columns(3)
            
            if col_hist.button("📜", key=f"hist_{row['customer_code']}"):
                st.session_state.cust_history_view = row['customer_code']
                st.rerun()
            
            if col_edit.button("✏️", key=f"cedit_{row['customer_code']}"):
                st.session_state.edit_cust_data = row
                st.rerun()
                
            if col_del.button("🗑️", key=f"cust_del_{row['customer_code']}"):
                run_query("INSERT INTO deleted_customers VALUES (?,?,?,?,?)", (row['customer_code'], row['name'], row['address'], row['joined_date'], datetime.now()))
                run_query("DELETE FROM customers WHERE customer_code=?", (row['customer_code'],))
                st.rerun()
            st.divider()

# ==========================================
# PAGE: INVENTORY DB
# ==========================================
elif page == "📦 Inventory Database":
    st.header("📦 Inventory Database")
    
    # --- PRODUCT HISTORY VIEW ---
    if st.session_state.prod_history_view:
        view_code = st.session_state.prod_history_view
        st.info(f"📜 Transaction History for: **{view_code}**")
        
        if st.button("⬅️ Back to Inventory"):
            st.session_state.prod_history_view = None
            st.rerun()
            
        trans_df = run_query("""
            SELECT t.date, t.type, 
            CASE WHEN t.customer_code IS NULL THEN 'INTERNAL' ELSE c.name END as cust_name, 
            t.quantity_packs, t.total_units 
            FROM transactions t 
            LEFT JOIN customers c ON t.customer_code = c.customer_code
            WHERE t.product_code=? ORDER BY t.date DESC
        """, (view_code,), return_df=True)
        
        # FIX: Ensure quantity_packs and total_units are treated as numbers and handle errors safely
        trans_df['quantity_packs'] = pd.to_numeric(trans_df['quantity_packs'], errors='coerce').fillna(0).astype(int)
        trans_df['total_units'] = pd.to_numeric(trans_df['total_units'], errors='coerce').fillna(0).astype(int)
        
        st.dataframe(trans_df, use_container_width=True)
        
    else:
        # NORMAL INVENTORY LIST
        tab1, tab2 = st.tabs(["Database", "Alerts"])
        
        with tab1:
            def_code, def_name, def_stock, def_pack = "", "", 0, 1
            def_type = "Single"
            inv_edit_mode = False
            
            if st.session_state.edit_prod_data is not None:
                inv_edit_mode = True
                row = st.session_state.edit_prod_data
                def_code = row['product_code']
                def_name = row['name']
                try: def_stock = int(row['current_stock'])
                except: def_stock = 0
                def_pack = int(row['pack_size_multiplier'])
                def_type = row['unit_type']

            with st.expander(f"➕ {'Edit' if inv_edit_mode else 'Add'} Product", expanded=inv_edit_mode):
                c1, c2, c3, c4 = st.columns(4)
                p_c = c1.text_input("Code", value=def_code, disabled=inv_edit_mode).strip().upper()
                p_n = c2.text_input("Name", value=def_name)
                p_s = c3.number_input("Stock", value=def_stock)
                
                type_options = ["Single", "Pack"]
                try: type_idx = type_options.index(def_type)
                except: type_idx = 0
                
                p_type = c4.selectbox("Type", type_options, index=type_idx)
                
                p_pack = 1
                if p_type == "Pack":
                    p_pack = st.number_input("Pack Size", value=def_pack if def_pack > 1 else 30, min_value=1)
                    
                if st.button("Save Product"):
                    if not p_c or not p_n:
                        st.error("⚠️ Code and Name are required!")
                    else:
                        if not inv_edit_mode:
                            check = run_query("SELECT * FROM products WHERE product_code=?", (p_c,), return_df=True)
                            if not check.empty:
                                st.error("Product Code Already Exists!")
                            else:
                                run_query("INSERT INTO products (product_code, name, current_stock, pack_size_multiplier, unit_type) VALUES (?,?,?,?,?)",
                                          (p_c, p_n, int(p_s), int(p_pack), p_type))
                                st.success("Saved!")
                                st.rerun()
                        else:
                            # --- INVENTORY ADJUSTMENT LOGGING ---
                            old_data = run_query("SELECT current_stock FROM products WHERE product_code=?", (p_c,), return_df=True).iloc[0]
                            try: old_stock = int(old_data['current_stock'])
                            except: old_stock = 0
                            
                            diff = int(p_s) - old_stock
                            
                            if diff != 0:
                                # Log positive or negative adjustment correctly
                                run_query("INSERT INTO transactions (date, type, product_code, quantity_packs, total_units) VALUES (?,?,?,?,?)", 
                                          (datetime.now(), 'ADJUSTMENT', p_c, diff, diff * int(p_pack)))
                            
                            run_query("UPDATE products SET name=?, current_stock=?, pack_size_multiplier=?, unit_type=? WHERE product_code=?", 
                                      (p_n, int(p_s), int(p_pack), p_type, p_c))
                            st.success("Updated!")
                            st.session_state.edit_prod_data = None
                            st.rerun()
                        
                if inv_edit_mode and st.button("Cancel Edit"):
                    st.session_state.edit_prod_data = None
                    st.rerun()
            
            inv_search = st.text_input("Search Inventory Database", placeholder="Product Name or Code")
            query = "SELECT * FROM products"
            params = ()
            if inv_search:
                query += " WHERE product_code LIKE ? OR name LIKE ?"
                term = f"%{inv_search}%"
                params = (term, term)
                
            df = run_query(query, params, return_df=True)
            
            # --- FIX: FORCE CLEAN INVENTORY DISPLAY ---
            # This strips bad characters from columns so numbers appear correctly
            for col in ['current_stock', 'pack_size_multiplier']:
                df[col] = df[col].astype(str).str.extract(r'(-?\d+)').fillna(0).astype(int)

            h1, h2, h3, h4, h5 = st.columns([1, 2, 1, 1, 2])
            h1.write("**Product Code**")
            h2.write("**Product Name**")
            h3.write("**Quantity**")
            h4.write("**Pack Size**")
            h5.write("**Action**")
            
            for i, row in df.iterrows():
                c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 1, 2])
                c1.write(row['product_code'])
                c2.write(row['name'])
                c3.write(f"{row['current_stock']}")
                c4.write(f"{row['pack_size_multiplier']}")
                
                col_hist, col_edit, col_del = c5.columns(3)
                
                if col_hist.button("📜", key=f"hist_p_{row['product_code']}"):
                    st.session_state.prod_history_view = row['product_code']
                    st.rerun()
                
                if col_edit.button("✏️", key=f"pedit_{row['product_code']}"):
                    st.session_state.edit_prod_data = row
                    st.rerun()
                    
                if col_del.button("🗑️", key=f"inv_del_{row['product_code']}"):
                    run_query("INSERT INTO deleted_products (product_code, name, current_stock, pack_size_multiplier, unit_type, deleted_at) VALUES (?,?,?,?,?,?)", 
                              (row['product_code'], row['name'], row['current_stock'], row['pack_size_multiplier'], row.get('unit_type', 'Single'), datetime.now()))
                    run_query("DELETE FROM products WHERE product_code=?", (row['product_code'],))
                    st.rerun()
                st.divider()

        with tab2:
            st.subheader("⚠️ Low Stock Analytics")
            df_p = run_query("SELECT * FROM products", return_df=True)
            if not df_p.empty:
                df_p['total_units'] = df_p['current_stock'] * df_p['pack_size_multiplier']
                df_p['Pack Type'] = df_p['pack_size_multiplier'].apply(lambda x: "📦 Large Pack" if x > 1 else "👤 Single Unit")
                fig = px.bar(df_p, x='product_code', y='total_units', color='Pack Type',
                             color_discrete_map={"📦 Large Pack": "#FF9900", "👤 Single Unit": "#00CC96"})
                fig.add_hline(y=150, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PAGE: RESTORE
# ==========================================
elif page == "♻️ Recycle Bin":
    st.header("♻️ Restore Data")
    tab1, tab2, tab3 = st.tabs(["Deleted Sales", "Deleted Customers", "Deleted Products"])
    with tab1:
        dt = run_query("SELECT * FROM deleted_transactions", return_df=True)
        if not dt.empty:
            for i, row in dt.iterrows():
                col_a, col_b = st.columns([4, 1])
                col_a.write(f"📅 {row['date']} | {row['type']} | {row['product_code']} (Qty: {row['quantity_packs']})")
                if col_b.button("Restore", key=f"rst_t_{i}"):
                    run_query("INSERT INTO transactions (date, type, product_code, customer_code, quantity_packs, total_units) VALUES (?,?,?,?,?,?)",
                             (row['date'], row['type'], row['product_code'], row['customer_code'], row['quantity_packs'], row['total_units']))
                    if row['type'] in ['SALE', 'LOST']:
                        run_query("UPDATE products SET current_stock = current_stock - ? WHERE product_code=?", (row['quantity_packs'], row['product_code']))
                    else:
                        run_query("UPDATE products SET current_stock = current_stock + ? WHERE product_code=?", (row['quantity_packs'], row['product_code']))
                    run_query("DELETE FROM deleted_transactions WHERE original_id=?", (row['original_id'],))
                    st.success("Transaction Restored!"); st.rerun()
        else:
            st.info("No deleted transactions found.")
    with tab2:
        dc = run_query("SELECT * FROM deleted_customers", return_df=True)
        for i, row in dc.iterrows():
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"{row['name']} ({row['customer_code']})")
            if col_b.button("Restore", key=f"rst_c_{i}"):
                run_query("INSERT OR REPLACE INTO customers VALUES (?,?,?,?)", (row['customer_code'], row['name'], row['address'], row['joined_date']))
                run_query("DELETE FROM deleted_customers WHERE customer_code=?", (row['customer_code'],))
                st.success("Restored!"); st.rerun()
    with tab3:
        dp = run_query("SELECT * FROM deleted_products", return_df=True)
        for i, row in dp.iterrows():
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"{row['name']} ({row['product_code']})")
            if col_b.button("Restore", key=f"rst_p_{i}"):
                run_query("INSERT OR REPLACE INTO products (product_code, name, current_stock, pack_size_multiplier, unit_type) VALUES (?,?,?,?,?)", 
                          (row['product_code'], row['name'], row['current_stock'], row['pack_size_multiplier'], row.get('unit_type', 'Single')))
                run_query("DELETE FROM deleted_products WHERE product_code=?", (row['product_code'],))
                st.success("Restored!"); st.rerun()