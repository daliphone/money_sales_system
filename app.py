import streamlit as st
import pandas as pd
import os
import io  # 新增: 用於處理 Excel 檔案串流
from datetime import datetime

# --- 檔案路徑設定 ---
FILE_PRODUCTS = 'products.csv'
FILE_SALES = 'sales_log.csv'
FILE_EMPLOYEES = 'employees.csv'
ADMIN_PASSWORD = "8888"  # 【請修改】管理員密碼

# --- 初始化資料 ---
def init_data():
    if not os.path.exists(FILE_PRODUCTS):
        pd.DataFrame(columns=['商品名稱', '單件獎金']).to_csv(FILE_PRODUCTS, index=False)
    
    if not os.path.exists(FILE_SALES):
        pd.DataFrame(columns=['日期', '員工姓名', '商品名稱', '數量', '當時單件獎金', '總獎金']).to_csv(FILE_SALES, index=False)
        
    if not os.path.exists(FILE_EMPLOYEES):
        pd.DataFrame({'員工姓名': ['店長', '員工A']}).to_csv(FILE_EMPLOYEES, index=False)

# --- 資料讀寫函數 ---
def load_data(filename):
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- 主程式開始 ---
st.set_page_config(page_title="銷售獎勵系統 (Excel匯出版)", layout="wide")
init_data()

st.title("🏆 銷售商品獎勵紀錄系統")

# --- 側邊欄 ---
with st.sidebar:
    st.header("功能選單")
    choice = st.radio("前往", ["📝 銷售登記", "⚙️ 系統設定 (商品/員工)", "📊 業績統計"])
    
    st.markdown("---")
    st.header("🔐 管理員權限")
    
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
# 1. 銷售登記
# ==========================================
if choice == "📝 銷售登記":
    st.header("📝 登記銷售紀錄")

    df_products = load_data(FILE_PRODUCTS)
    df_employees = load_data(FILE_EMPLOYEES)
    df_sales = load_data(FILE_SALES)

    if df_products.empty:
        st.warning("⚠️ 尚未設定商品，請聯絡管理員。")
    elif df_employees.empty:
        st.warning("⚠️ 尚未設定員工名單，請聯絡管理員。")
    else:
        with st.form("entry_form"):
            col1, col2 = st.columns(2)
            emp_list = df_employees['員工姓名'].unique().tolist()
            user_name = col1.selectbox("員工姓名", emp_list)
            date_entry = col2.date_input("銷售日期", datetime.now())

            col3, col4 = st.columns(2)
            prod_list = df_products['商品名稱'].unique().tolist()
            product_select = col3.selectbox("銷售商品", prod_list)
            qty = col4.number_input("銷售數量", min_value=1, value=1, step=1)

            submit_log = st.form_submit_button("提交紀錄")

            if submit_log:
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
                save_data(df_sales, FILE_SALES)
                st.success(f"✅ 登記成功！ {user_name} - {product_select} x {qty}")

        st.subheader("📋 最近 5 筆紀錄")
        if not df_sales.empty:
            st.dataframe(df_sales.tail(5).sort_index(ascending=False), use_container_width=True)

# ==========================================
# 2. 系統設定
# ==========================================
elif choice == "⚙️ 系統設定 (商品/員工)":
    st.header("⚙️ 系統參數設定")
    tab1, tab2 = st.tabs(["🎁 商品與獎金", "👥 員工名單管理"])

    with tab1:
        df_products = load_data(FILE_PRODUCTS)
        st.subheader("目前的獎勵商品")
        st.dataframe(df_products, use_container_width=True)

        if st.session_state.is_admin:
            st.markdown("### 🛠️ 編輯區 (管理員)")
            with st.form("add_product"):
                c1, c2 = st.columns([2, 1])
                new_prod = c1.text_input("新增/修改商品名稱")
                new_price = c2.number_input("獎金金額", min_value=0)
                
                if st.form_submit_button("儲存設定"):
                    if new_prod:
                        if not df_products.empty and new_prod in df_products['商品名稱'].values:
                            df_products.loc[df_products['商品名稱'] == new_prod, '單件獎金'] = new_price
                        else:
                            new_row = pd.DataFrame({'商品名稱': [new_prod], '單件獎金': [new_price]})
                            df_products = pd.concat([df_products, new_row], ignore_index=True)
                        save_data(df_products, FILE_PRODUCTS)
                        st.success("已更新商品資料")
                        st.rerun()
            
            if not df_products.empty:
                del_prod = st.selectbox("選擇要刪除的商品", ["請選擇"] + df_products['商品名稱'].tolist())
                if st.button("確認刪除商品"):
                    if del_prod != "請選擇":
                        df_products = df_products[df_products['商品名稱'] != del_prod]
                        save_data(df_products, FILE_PRODUCTS)
                        st.rerun()
        else:
            st.info("🔒 登入管理員密碼後即可編輯。")

    with tab2:
        df_employees = load_data(FILE_EMPLOYEES)
        st.subheader("目前的員工名單")
        st.table(df_employees)

        if st.session_state.is_admin:
            st.markdown("### 🛠️ 編輯區")
            with st.form("add_emp"):
                new_emp = st.text_input("新增員工姓名")
                if st.form_submit_button("新增員工"):
                    if new_emp:
                        if df_employees.empty or new_emp not in df_employees['員工姓名'].values:
                            new_row = pd.DataFrame({'員工姓名': [new_emp]})
                            df_employees = pd.concat([df_employees, new_row], ignore_index=True)
                            save_data(df_employees, FILE_EMPLOYEES)
                            st.success(f"已新增 {new_emp}")
                            st.rerun()
            
            if not df_employees.empty:
                del_emp = st.selectbox("選擇要刪除的員工", ["請選擇"] + df_employees['員工姓名'].tolist())
                if st.button("確認刪除員工"):
                    if del_emp != "請選擇":
                        df_employees = df_employees[df_employees['員工姓名'] != del_emp]
                        save_data(df_employees, FILE_EMPLOYEES)
                        st.rerun()
        else:
            st.info("🔒 登入管理員密碼後即可編輯。")

# ==========================================
# 3. 業績統計 (整合匯出)
# ==========================================
elif choice == "📊 業績統計":
    st.header("📊 業績計算與匯出")

    df_sales = load_data(FILE_SALES)

    if not df_sales.empty:
        df_sales['數量'] = pd.to_numeric(df_sales['數量'], errors='coerce').fillna(0)
        df_sales['總獎金'] = pd.to_numeric(df_sales['總獎金'], errors='coerce').fillna(0)

        st.markdown("### 🏆 人員獎金匯總表")
        pivot_df = df_sales.pivot_table(
            index='員工姓名',
            values=['數量', '總獎金'],
            aggfunc='sum'
        ).reset_index()
        
        st.dataframe(pivot_df.style.format({"總獎金": "${:,.0f}"}), use_container_width=True)

        st.divider()
        st.subheader("📥 匯出完整 Excel 報表")
        st.write("點擊下方按鈕下載 Excel 檔，檔案內包含兩個分頁：「獎金匯總」與「原始明細」。")

        # --- 產生 Excel 檔案 ---
        # 建立一個記憶體內的 Excel 檔案
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 分頁 1: 匯總表
            pivot_df.to_excel(writer, sheet_name='獎金匯總', index=False)
            # 分頁 2: 原始明細
            df_sales.to_excel(writer, sheet_name='原始明細', index=False)
        
        # 準備下載資料
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 下載完整 Excel 報表 (.xlsx)",
            data=excel_data,
            file_name=f'sales_report_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("目前尚無資料可供統計。")

st.sidebar.markdown("---")
st.sidebar.caption("Excel 整合匯出版 v4.0")
