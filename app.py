import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 設定區 ---
SHEET_PRODUCTS = "Products"
SHEET_SALES = "SalesLog"
SHEET_EMPLOYEES = "Employees"
ADMIN_PASSWORD = "8888"  # 【請修改】這是管理員密碼

st.set_page_config(page_title="銷售獎勵系統", layout="wide")
st.title("🏆 銷售商品獎勵紀錄系統")

# --- 連線設定 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 資料讀寫函數 ---
def get_data(worksheet_name, expected_columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df.empty or df.columns.size == 0:
            return pd.DataFrame(columns=expected_columns)
        # 確保欄位存在
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        # 去除全空行
        df = df.dropna(how='all')
        return df
    except Exception:
        return pd.DataFrame(columns=expected_columns)

def update_data(df, worksheet_name):
    conn.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear()

# --- 側邊欄：導航與登入 ---
with st.sidebar:
    st.header("功能選單")
    choice = st.radio("前往", ["📝 銷售登記", "⚙️ 系統設定 (商品/員工)", "📊 業績統計"])
    
    st.markdown("---")
    st.header("🔐 管理員權限")
    # 權限狀態管理
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if not st.session_state.is_admin:
        pwd_input = st.text_input("輸入密碼解鎖編輯權限", type="password")
        if pwd_input == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.success("已登入管理員")
            st.rerun()
    else:
        st.success("管理員模式：可編輯")
        if st.button("登出"):
            st.session_state.is_admin = False
            st.rerun()

# ==========================================
# 1. 銷售登記 (前台)
# ==========================================
if choice == "📝 銷售登記":
    st.header("📝 登記銷售紀錄")

    # 讀取資料
    df_products = get_data(SHEET_PRODUCTS, ['商品名稱', '單件獎金'])
    df_employees = get_data(SHEET_EMPLOYEES, ['員工姓名'])
    df_sales = get_data(SHEET_SALES, ['日期', '員工姓名', '商品名稱', '數量', '當時單件獎金', '總獎金'])

    # 檢查設定是否完整
    if df_products.empty:
        st.warning("⚠️ 尚未設定商品，請聯絡管理員。")
    elif df_employees.empty:
        st.warning("⚠️ 尚未設定員工名單，請聯絡管理員。")
    else:
        with st.form("entry_form"):
            col1, col2 = st.columns(2)
            # 這裡改成從 Google Sheet 讀取的員工名單
            employee_list = df_employees['員工姓名'].dropna().unique().tolist()
            user_name = col1.selectbox("員工姓名", employee_list)
            date_entry = col2.date_input("銷售日期", datetime.now())

            col3, col4 = st.columns(2)
            # 商品選單
            product_list = df_products['商品名稱'].dropna().unique().tolist()
            product_select = col3.selectbox("銷售商品", product_list)
            qty = col4.number_input("銷售數量", min_value=1, value=1, step=1)

            submit_log = st.form_submit_button("提交紀錄")

            if submit_log:
                # 抓取當前獎金
                try:
                    reward_row = df_products[df_products['商品名稱'] == product_select]
                    current_reward = float(reward_row['單件獎金'].values[0])
                except:
                    current_reward = 0
                
                total_reward = current_reward * qty

                new_record = pd.DataFrame({
                    '日期': [str(date_entry)],
                    '員工姓名': [user_name],
                    '商品名稱': [product_select],
                    '數量': [qty],
                    '當時單件獎金': [current_reward],
                    '總獎金': [total_reward]
                })

                df_sales = pd.concat([df_sales, new_record], ignore_index=True)
                update_data(df_sales, SHEET_SALES)
                st.success(f"✅ 登記成功！ {user_name} - {product_select} x {qty}")

        # 顯示最近紀錄
        st.subheader("📋 最近 5 筆紀錄")
        if not df_sales.empty:
            st.dataframe(df_sales.tail(5).sort_index(ascending=False), use_container_width=True)

# ==========================================
# 2. 系統設定 (商品/員工) - 有權限控制
# ==========================================
elif choice == "⚙️ 系統設定 (商品/員工)":
    st.header("⚙️ 系統參數設定")

    tab1, tab2 = st.tabs(["🎁 商品與獎金", "👥 員工名單管理"])

    # --- Tab 1: 商品管理 ---
    with tab1:
        df_products = get_data(SHEET_PRODUCTS, ['商品名稱', '單件獎金'])
        
        # 顯示目前的設定 (所有人可見)
        st.subheader("目前的獎勵商品")
        st.dataframe(df_products, use_container_width=True)

        if st.session_state.is_admin:
            st.markdown("### 🛠️ 編輯區 (僅管理員可見)")
            with st.form("add_product"):
                c1, c2 = st.columns([2, 1])
                new_prod = c1.text_input("新增/修改商品名稱")
                new_price = c2.number_input("獎金金額", min_value=0)
                if st.form_submit_button("儲存設定"):
                    if new_prod:
                        # 更新或新增
                        if new_prod in df_products['商品名稱'].values:
                            df_products.loc[df_products['商品名稱'] == new_prod, '單件獎金'] = new_price
                        else:
                            new_row = pd.DataFrame({'商品名稱': [new_prod], '單件獎金': [new_price]})
                            df_products = pd.concat([df_products, new_row], ignore_index=True)
                        update_data(df_products, SHEET_PRODUCTS)
                        st.success("已更新商品資料")
                        st.rerun()
            
            # 刪除功能
            del_prod = st.selectbox("選擇要刪除的商品", ["請選擇"] + df_products['商品名稱'].tolist())
            if st.button("確認刪除商品"):
                if del_prod != "請選擇":
                    df_products = df_products[df_products['商品名稱'] != del_prod]
                    update_data(df_products, SHEET_PRODUCTS)
                    st.rerun()
        else:
            st.info("🔒 登入管理員密碼後即可編輯商品與金額。")

    # --- Tab 2: 員工管理 ---
    with tab2:
        df_employees = get_data(SHEET_EMPLOYEES, ['員工姓名'])
        
        st.subheader("目前的員工名單")
        # 簡單呈現列表
        st.table(df_employees)

        if st.session_state.is_admin:
            st.markdown("### 🛠️ 編輯區")
            with st.form("add_emp"):
                new_emp = st.text_input("新增員工姓名")
                if st.form_submit_button("新增員工"):
                    if new_emp and new_emp not in df_employees['員工姓名'].values:
                        new_row = pd.DataFrame({'員工姓名': [new_emp]})
                        df_employees = pd.concat([df_employees, new_row], ignore_index=True)
                        update_data(df_employees, SHEET_EMPLOYEES)
                        st.success(f"已新增 {new_emp}")
                        st.rerun()
            
            # 刪除員工
            del_emp = st.selectbox("選擇要刪除的員工", ["請選擇"] + df_employees['員工姓名'].tolist())
            if st.button("確認刪除員工"):
                if del_emp != "請選擇":
                    df_employees = df_employees[df_employees['員工姓名'] != del_emp]
                    update_data(df_employees, SHEET_EMPLOYEES)
                    st.rerun()
        else:
            st.info("🔒 登入管理員密碼後即可新增或移除員工。")

# ==========================================
# 3. 業績統計 (匯出)
# ==========================================
elif choice == "📊 業績統計":
    st.header("📊 業績計算與匯出")

    df_sales = get_data(SHEET_SALES, ['日期', '員工姓名', '商品名稱', '數量', '當時單件獎金', '總獎金'])

    if not df_sales.empty:
        # 資料型態轉換確保計算無誤
        df_sales['數量'] = pd.to_numeric(df_sales['數量'], errors='coerce').fillna(0)
        df_sales['總獎金'] = pd.to_numeric(df_sales['總獎金'], errors='coerce').fillna(0)

        # 1. 總表預覽
        st.markdown("### 🏆 人員獎金匯總表")
        pivot_df = df_sales.pivot_table(
            index='員工姓名',
            values=['數量', '總獎金'],
            aggfunc='sum'
        ).reset_index()
        
        # 顯示美化後的表格
        st.dataframe(pivot_df.style.format({"總獎金": "${:,.0f}"}), use_container_width=True)

        # 2. 匯出按鈕
        st.markdown("### 📤 匯出資料")
        col1, col2 = st.columns(2)
        
        # 匯出匯總表
        csv_summary = pivot_df.to_csv(index=False).encode('utf-8-sig')
        col1.download_button(
            label="下載「人員統計匯總表」 (CSV)",
            data=csv_summary,
            file_name='sales_summary_report.csv',
            mime='text/csv',
        )

        # 匯出明細表
        csv_detail = df_sales.to_csv(index=False).encode('utf-8-sig')
        col2.download_button(
            label="下載「完整交易明細」 (CSV)",
            data=csv_detail,
            file_name='sales_detail_log.csv',
            mime='text/csv',
        )

    else:
        st.info("目前尚無資料可供統計。")