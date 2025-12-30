import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

# --- 檔案路徑設定 ---
FILE_PRODUCTS = 'products.csv'
FILE_SALES = 'sales_log.csv'
FILE_EMPLOYEES = 'employees.csv'
FILE_LOG = 'system_log.csv'
ADMIN_PASSWORD = "8888"  # 【請修改】管理員密碼

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

# --- 寫入操作日誌 ---
def log_operation(user, action, detail):
    df_log = load_data(FILE_LOG)
    new_log = pd.DataFrame({
        '時間': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        '操作者': [user],
        '動作': [action],
        '詳細內容': [detail]
    })
    df_log = pd.concat([df_log, new_log], ignore_index=True)
    save_data(df_log, FILE_LOG)

# --- 版面設定 ---
st.set_page_config(page_title="銷售獎勵系統 v7.0", layout="wide", page_icon="💰")
init_data()

# ==========================================
# 🎨 左側邊欄
# ==========================================
with st.sidebar:
    st.markdown("## 💰 銷售獎勵系統")
    st.caption(f"📅 今天是：{datetime.now().strftime('%Y-%m-%d')}")
    st.markdown("---")

    st.markdown("### 📌 功能選單")
    choice = st.radio(
        "請選擇功能：",
        ["📝 銷售登記", "⚙️ 後台管理", "📊 業績統計與匯出"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")

    st.markdown("### 🔐 權限狀態")
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if st.session_state.is_admin:
        with st.container():
            st.success("✅ 管理員已登入")
            st.caption("您可以編輯所有設定與刪除紀錄")
            if st.button("登出系統", use_container_width=True):
                log_operation("系統", "管理員登出", "登出成功")
                st.session_state.is_admin = False
                st.rerun()
    else:
        with st.expander("管理員登入 / 權限解鎖"):
            pwd_input = st.text_input("輸入密碼", type="password", placeholder="預設: 8888")
            if st.button("驗證登入", use_container_width=True):
                if pwd_input == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    log_operation("系統", "管理員登入", "登入成功")
                    st.success("登入成功！")
                    st.rerun()
                else:
                    st.error("密碼錯誤")
    
    st.markdown("---")
    st.caption("© 2025 Sales System v7.0")

# ==========================================
# 主畫面內容
# ==========================================

st.title(f"{choice.split(' ')[1]}")

# ------------------------------------------
# 功能 1: 銷售登記
# ------------------------------------------
if choice == "📝 銷售登記":
    df_products = load_data(FILE_PRODUCTS)
    df_employees = load_data(FILE_EMPLOYEES)
    df_sales = load_data(FILE_SALES)

    if df_products.empty or df_employees.empty:
        st.error("⚠️ 系統尚未初始化！請先至「後台管理」設定商品與員工。")
    else:
        with st.container(border=True):
            st.subheader("新增一筆銷售")
            with st.form("entry_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                emp_list = df_employees['員工姓名'].unique().tolist()
                user_name = col1.selectbox("👤 員工姓名", emp_list)
                date_entry = col2.date_input("📅 銷售日期", datetime.now())

                col3, col4 = st.columns(2)
                prod_list = df_products['商品名稱'].unique().tolist()
                product_select = col3.selectbox("📦 銷售商品", prod_list)
                qty = col4.number_input("🔢 銷售數量", min_value=1, value=1, step=1)

                submit_log = st.form_submit_button("確認提交", use_container_width=True, type="primary")

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
                    log_operation(user_name, "新增業績", f"{product_select} x {qty}, 獎金${total_reward}")
                    
                    st.toast(f"✅ 登記成功！ {user_name} 獲得獎金 ${total_reward}")

        st.markdown("### 📋 今日與近期紀錄")
        if not df_sales.empty:
            st.dataframe(df_sales.tail(5).sort_index(ascending=False), use_container_width=True)

# ------------------------------------------
# 功能 2: 後台管理
# ------------------------------------------
elif choice == "⚙️ 後台管理":
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎁 商品設定", "👥 員工設定", "🗑️ 銷售紀錄管理", "📜 系統日誌"])

    with tab1:
        df_products = load_data(FILE_PRODUCTS)
        st.dataframe(df_products, use_container_width=True)

        if st.session_state.is_admin:
            st.markdown("#### 🛠️ 新增/修改商品")
            with st.form("add_product"):
                c1, c2 = st.columns([2, 1])
                new_prod = c1.text_input("商品名稱")
                new_price = c2.number_input("單件獎金 ($)", min_value=0)
                if st.form_submit_button("儲存"):
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
                        st.rerun()
            
            if not df_products.empty:
                with st.expander("⚠️ 刪除商品 (點擊展開)"):
                    del_prod = st.selectbox("選擇商品", df_products['商品名稱'].tolist())
                    if st.button("確認刪除商品"):
                        df_products = df_products[df_products['商品名稱'] != del_prod]
                        save_data(df_products, FILE_PRODUCTS)
                        log_operation("管理員", "刪除商品", del_prod)
                        st.rerun()
        else:
            st.info("🔒 請先於左側登入管理員")

    with tab2:
        df_employees = load_data(FILE_EMPLOYEES)
        st.table(df_employees)

        if st.session_state.is_admin:
            with st.form("add_emp"):
                new_emp = st.text_input("新增員工姓名")
                if st.form_submit_button("新增"):
                    if new_emp and (df_employees.empty or new_emp not in df_employees['員工姓名'].values):
                        new_row = pd.DataFrame({'員工姓名': [new_emp]})
                        df_employees = pd.concat([df_employees, new_row], ignore_index=True)
                        save_data(df_employees, FILE_EMPLOYEES)
                        log_operation("管理員", "新增員工", new_emp)
                        st.rerun()
            
            if not df_employees.empty:
                 with st.expander("⚠️ 刪除員工 (點擊展開)"):
                    del_emp = st.selectbox("選擇員工", df_employees['員工姓名'].tolist())
                    if st.button("確認刪除員工"):
                        df_employees = df_employees[df_employees['員工姓名'] != del_emp]
                        save_data(df_employees, FILE_EMPLOYEES)
                        log_operation("管理員", "刪除員工", del_emp)
                        st.rerun()
        else:
            st.info("🔒 請先於左側登入管理員")

    with tab3:
        df_sales = load_data(FILE_SALES)
        if not df_sales.empty:
            st.dataframe(df_sales, use_container_width=True)
            if st.session_state.is_admin:
                st.markdown("#### 🗑️ 刪除紀錄")
                options = [f"{i}: {row['日期']} | {row['員工姓名']} | {row['商品名稱']} (x{row['數量']})" 
                           for i, row in df_sales.iterrows()]
                selected_option = st.selectbox("選擇要刪除的項目", ["請選擇"] + options)
                if st.button("確認刪除此筆"):
                    if selected_option != "請選擇":
                        idx = int(selected_option.split(":")[0])
                        content = selected_option.split(":", 1)[1]
                        df_sales = df_sales.drop(idx).reset_index(drop=True)
                        save_data(df_sales, FILE_SALES)
                        log_operation("管理員", "刪除業績", content)
                        st.success("已刪除")
                        st.rerun()
            else:
                 st.info("🔒 請先於左側登入管理員")
        else:
            st.write("無資料")

    with tab4:
        df_log = load_data(FILE_LOG)
        st.dataframe(df_log.sort_index(ascending=False), use_container_width=True)

# ------------------------------------------
# 功能 3: 統計與匯出
# ------------------------------------------
elif choice == "📊 業績統計與匯出":
    
    df_sales = load_data(FILE_SALES)

    if not df_sales.empty:
        # 確保數值欄位格式正確
        df_sales['數量'] = pd.to_numeric(df_sales['數量'], errors='coerce').fillna(0)
        df_sales['總獎金'] = pd.to_numeric(df_sales['總獎金'], errors='coerce').fillna(0)
        df_sales['當時單件獎金'] = pd.to_numeric(df_sales['當時單件獎金'], errors='coerce').fillna(0)

        # 1. 總覽 Pivot (簡單版)
        st.subheader("🏆 人員獎金排行榜")
        pivot_total = df_sales.pivot_table(
            index='員工姓名', values=['數量', '總獎金'], aggfunc='sum'
        ).reset_index().sort_values(by='總獎金', ascending=False)
        
        st.dataframe(pivot_total.style.format({"總獎金": "${:,.0f}"}), use_container_width=True)

        # 2. 詳細 Pivot (包含單件獎勵) --- 這裡做了修改
        st.subheader("📦 各人員銷售商品明細 (含設定獎金)")
        
        # 我們將「當時單件獎金」也放入 index 中，這樣它就會顯示出來
        pivot_detail = df_sales.pivot_table(
            index=['員工姓名', '商品名稱', '當時單件獎金'], 
            values=['數量', '總獎金'], 
            aggfunc='sum'
        ).reset_index()

        # 欄位更名，讓使用者更容易看得懂
        pivot_detail.rename(columns={'當時單件獎金': '單件獎勵(設定值)'}, inplace=True)
        
        # 重新排序與整理欄位順序
        pivot_detail = pivot_detail[['員工姓名', '商品名稱', '單件獎勵(設定值)', '數量', '總獎金']]
        pivot_detail = pivot_detail.sort_values(by=['員工姓名', '總獎金'], ascending=[True, False])

        st.dataframe(pivot_detail.style.format({"總獎金": "${:,.0f}", "單件獎勵(設定值)": "${:,.0f}"}), use_container_width=True)

        # 3. 匯出 Excel
        st.divider()
        st.markdown("### 📥 匯出完整報表")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: 總表
            pivot_total.to_excel(writer, sheet_name='1.人員獎金總表', index=False)
            
            # Sheet 2: 詳細明細 (員工-商品-單價)
            pivot_detail.to_excel(writer, sheet_name='2.銷售明細(含單價)', index=False)
            
            # Sheet 3: 原始資料
            df_sales.to_excel(writer, sheet_name='3.原始流水帳', index=False)
            
            # Sheet 4: 操作紀錄
            df_log_export = load_data(FILE_LOG)
            if not df_log_export.empty:
                df_log_export.to_excel(writer, sheet_name='4.系統操作日誌', index=False)
        
        excel_data = output.getvalue()
        filename = f"銷售獎勵總表_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        st.download_button(
            label=f"📥 點此下載 Excel ({filename})",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    else:
        st.info("⚠️ 目前尚無銷售資料。")
