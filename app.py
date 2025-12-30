import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

# --- 檔案路徑設定 ---
FILE_PRODUCTS = 'products.csv'
FILE_SALES = 'sales_log.csv'
FILE_EMPLOYEES = 'employees.csv'
FILE_LOG = 'system_log.csv'  # 新增：操作日誌檔
ADMIN_PASSWORD = "8888"      # 【請修改】管理員密碼

# --- 初始化資料 ---
def init_data():
    if not os.path.exists(FILE_PRODUCTS):
        pd.DataFrame(columns=['商品名稱', '單件獎金']).to_csv(FILE_PRODUCTS, index=False)
    
    if not os.path.exists(FILE_SALES):
        pd.DataFrame(columns=['日期', '員工姓名', '商品名稱', '數量', '當時單件獎金', '總獎金']).to_csv(FILE_SALES, index=False)
        
    if not os.path.exists(FILE_EMPLOYEES):
        pd.DataFrame({'員工姓名': ['店長', '員工A']}).to_csv(FILE_EMPLOYEES, index=False)

    if not os.path.exists(FILE_LOG):
        pd.DataFrame(columns=['時間', '操作者', '動作', '詳細內容']).to_csv(FILE_LOG, index=False)

# --- 資料讀寫函數 ---
def load_data(filename):
    try:
        return pd.read_csv(filename)
    except Exception:
        return pd.DataFrame()

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- 新增：寫入操作日誌函數 ---
def log_operation(user, action, detail):
    """
    user: 操作者 (例如: '管理員', '員工A')
    action: 動作類型 (例如: '新增業績', '刪除紀錄')
    detail: 詳細說明
    """
    df_log = load_data(FILE_LOG)
    new_log = pd.DataFrame({
        '時間': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        '操作者': [user],
        '動作': [action],
        '詳細內容': [detail]
    })
    df_log = pd.concat([df_log, new_log], ignore_index=True)
    save_data(df_log, FILE_LOG)

# --- 主程式開始 ---
st.set_page_config(page_title="銷售獎勵系統 v5.0", layout="wide")
init_data()

st.title("🏆 銷售商品獎勵紀錄系統")

# --- 側邊欄 ---
with st.sidebar:
    st.header("功能選單")
    # 調整選單順序與名稱
    choice = st.radio("前往", ["📝 銷售登記", "⚙️ 後台管理 (設定/刪單/日誌)", "📊 業績統計與匯出"])
    
    st.markdown("---")
    st.header("🔐 管理員權限")
    
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if not st.session_state.is_admin:
        pwd_input = st.text_input("輸入密碼解鎖編輯權限", type="password")
        if pwd_input == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            log_operation("系統", "管理員登入", "登入成功")
            st.success("已登入管理員")
            st.rerun()
    else:
        st.success("管理員模式：可編輯")
        if st.button("登出"):
            log_operation("系統", "管理員登出", "登出成功")
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

    if df_products.empty or df_employees.empty:
        st.warning("⚠️ 請先至後台設定商品與員工名單。")
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
                
                # 紀錄日誌
                log_operation(user_name, "新增業績", f"{product_select} x {qty}, 獎金${total_reward}")
                
                st.success(f"✅ 登記成功！ {user_name} - {product_select} x {qty}")

        st.subheader("📋 最近 5 筆紀錄")
        if not df_sales.empty:
            st.dataframe(df_sales.tail(5).sort_index(ascending=False), use_container_width=True)

# ==========================================
# 2. 後台管理 (設定/刪單/日誌)
# ==========================================
elif choice == "⚙️ 後台管理 (設定/刪單/日誌)":
    st.header("⚙️ 後台管理系統")
    
    # 分頁設計
    tab1, tab2, tab3, tab4 = st.tabs(["🎁 商品設定", "👥 員工設定", "🗑️ 銷售紀錄管理", "📜 系統操作日誌"])

    # --- Tab 1: 商品管理 ---
    with tab1:
        df_products = load_data(FILE_PRODUCTS)
        st.dataframe(df_products, use_container_width=True)

        if st.session_state.is_admin:
            st.markdown("### 🛠️ 編輯區 (管理員)")
            with st.form("add_product"):
                c1, c2 = st.columns([2, 1])
                new_prod = c1.text_input("新增/修改商品名稱")
                new_price = c2.number_input("獎金金額", min_value=0)
                
                if st.form_submit_button("儲存設定"):
                    if new_prod:
                        action_type = "新增商品"
                        if not df_products.empty and new_prod in df_products['商品名稱'].values:
                            df_products.loc[df_products['商品名稱'] == new_prod, '單件獎金'] = new_price
                            action_type = "修改商品"
                        else:
                            new_row = pd.DataFrame({'商品名稱': [new_prod], '單件獎金': [new_price]})
                            df_products = pd.concat([df_products, new_row], ignore_index=True)
                        
                        save_data(df_products, FILE_PRODUCTS)
                        log_operation("管理員", action_type, f"{new_prod} (${new_price})")
                        st.success("已更新商品資料")
                        st.rerun()
            
            if not df_products.empty:
                del_prod = st.selectbox("選擇要刪除的商品", ["請選擇"] + df_products['商品名稱'].tolist())
                if st.button("確認刪除商品"):
                    if del_prod != "請選擇":
                        df_products = df_products[df_products['商品名稱'] != del_prod]
                        save_data(df_products, FILE_PRODUCTS)
                        log_operation("管理員", "刪除商品", del_prod)
                        st.rerun()
        else:
            st.info("🔒 登入後可編輯")

    # --- Tab 2: 員工管理 ---
    with tab2:
        df_employees = load_data(FILE_EMPLOYEES)
        st.table(df_employees)

        if st.session_state.is_admin:
            with st.form("add_emp"):
                new_emp = st.text_input("新增員工姓名")
                if st.form_submit_button("新增員工"):
                    if new_emp:
                        if df_employees.empty or new_emp not in df_employees['員工姓名'].values:
                            new_row = pd.DataFrame({'員工姓名': [new_emp]})
                            df_employees = pd.concat([df_employees, new_row], ignore_index=True)
                            save_data(df_employees, FILE_EMPLOYEES)
                            log_operation("管理員", "新增員工", new_emp)
                            st.success(f"已新增 {new_emp}")
                            st.rerun()
            
            if not df_employees.empty:
                del_emp = st.selectbox("選擇要刪除的員工", ["請選擇"] + df_employees['員工姓名'].tolist())
                if st.button("確認刪除員工"):
                    if del_emp != "請選擇":
                        df_employees = df_employees[df_employees['員工姓名'] != del_emp]
                        save_data(df_employees, FILE_EMPLOYEES)
                        log_operation("管理員", "刪除員工", del_emp)
                        st.rerun()
        else:
            st.info("🔒 登入後可編輯")

    # --- Tab 3: 銷售紀錄管理 (刪除功能) ---
    with tab3:
        st.subheader("🗑️ 刪除錯誤的銷售紀錄")
        df_sales = load_data(FILE_SALES)
        
        if not df_sales.empty:
            # 顯示完整表格，包含 Index，方便對照
            st.dataframe(df_sales, use_container_width=True)

            if st.session_state.is_admin:
                st.markdown("#### 選擇要刪除的資料")
                # 製作一個下拉選單，顯示 "索引: 內容" 讓管理員選
                options = [f"{i}: {row['日期']} - {row['員工姓名']} - {row['商品名稱']} (x{row['數量']})" 
                           for i, row in df_sales.iterrows()]
                
                selected_option = st.selectbox("請選擇要刪除的項目", ["請選擇"] + options)
                
                if st.button("❌ 永久刪除此筆紀錄"):
                    if selected_option != "請選擇":
                        # 取出開頭的 index 數字
                        index_to_del = int(selected_option.split(":")[0])
                        
                        # 紀錄要被刪除的內容以便寫入 Log
                        deleted_content = selected_option.split(":", 1)[1]
                        
                        # 刪除該行
                        df_sales = df_sales.drop(index_to_del)
                        # 重置 index 避免斷號 (選擇性，這裡不重置以維持歷史對照也可以，但 CSV 重寫建議重置)
                        df_sales = df_sales.reset_index(drop=True)
                        
                        save_data(df_sales, FILE_SALES)
                        log_operation("管理員", "刪除業績", f"原紀錄: {deleted_content}")
                        
                        st.success("已刪除該筆資料")
                        st.rerun()
            else:
                st.warning("🔒 只有管理員可以刪除銷售紀錄。")
        else:
            st.info("目前無銷售紀錄。")

    # --- Tab 4: 系統操作日誌 ---
    with tab4:
        st.subheader("📜 系統操作紀錄")
        df_log = load_data(FILE_LOG)
        if not df_log.empty:
            # 最新的顯示在最上面
            st.dataframe(df_log.sort_index(ascending=False), use_container_width=True)
        else:
            st.info("目前無操作紀錄。")

# ==========================================
# 3. 業績統計與匯出
# ==========================================
elif choice == "📊 業績統計與匯出":
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
        st.subheader("📥 匯出報表")
        
        # --- 產生 Excel 檔案 ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pivot_df.to_excel(writer, sheet_name='獎金匯總', index=False)
            df_sales.to_excel(writer, sheet_name='原始明細', index=False)
            
            # 也可以把操作日誌一起匯出，方便查核
            df_log_export = load_data(FILE_LOG)
            if not df_log_export.empty:
                df_log_export.to_excel(writer, sheet_name='操作日誌', index=False)
        
        excel_data = output.getvalue()
        
        # 設定匯出檔名：銷售獎勵總表 + 今天日期 (YYYYMMDD)
        export_filename = f"銷售獎勵總表_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        st.download_button(
            label=f"📥 下載 Excel ({export_filename})",
            data=excel_data,
            file_name=export_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("目前尚無資料可供統計。")

st.sidebar.markdown("---")
st.sidebar.caption("全功能版 v5.0")
