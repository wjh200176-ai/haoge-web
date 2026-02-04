import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime
import urllib3

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 设置页面标题
st.set_page_config(page_title="豪哥数据中心", page_icon="📱", layout="mobile")

# ================= 核心功能函数 =================

def get_crypto_prices():
    usdt, usd = 0.0, 0.0
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=cny", timeout=3, verify=False)
        usdt = float(r.json()['tether']['cny'])
    except: pass
    try:
        r2 = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3, verify=False)
        usd = float(r2.json()['rates']['CNY'])
    except: pass
    return usdt, usd

def get_team_factors(n, input_mul_a, input_mul_b):
    n = str(n).upper()
    s_rate = 0.33
    if n in ['JJJJHHHH1', 'EEEE', 'BOWEI'] or '重复ID' in n: return 0.0, s_rate
    if n == 'TTTT': return 0.3, 0.315
    if n in ['LLLZZZ', 'PPPDDD']: return 0.29, 0.29
    try: return float(input_mul_a), float(input_mul_b)
    except: return 0.25, 0.29

@st.cache_data(ttl=60)
def fetch_data(uid, date_str):
    url = "http://111.170.156.82:83/get/group/webCollectTotalData"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }
    payload = {
        "user_ids": uid, "date": date_str,
        "platform_type": "网页", "browser_type": "全部浏览器"
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
        if resp.status_code != 200: return None, f"报错: {resp.status_code}"
        data = resp.json()
        details = data.get('details', []) if isinstance(data, dict) else data
        team_map = {}
        if details:
            for item in details:
                raw_id = str(item.get('userId') or item.get('user_ids') or "").strip()
                if raw_id:
                    upper_id = raw_id.upper()
                    if upper_id == 'JJJJHHHH1': tid = 'JJJJHHHH1'
                    elif 'BOWEI' in upper_id: tid = 'BOWEI'
                    elif '开发者' in raw_id: tid = '重复ID'
                    else: tid = re.sub(r'\d+$', '', raw_id).upper()
                    team_map[tid] = team_map.get(tid, 0) + int(item.get('count', 0))
        return sorted([{'name': k, 'val': v} for k, v in team_map.items()], key=lambda x: x['val'], reverse=True), None
    except Exception as e: return None, str(e)

# ================= 手机端界面 =================

st.title("📱 豪哥数据中心")

# 输入区域
with st.expander("⚙️ 设置查询条件", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        uid_input = st.text_input("Leader ID", value="wang")
    with col2:
        date_input = st.date_input("日期", value=datetime.now())
    
    col3, col4 = st.columns(2)
    with col3:
        input_mul_a = st.number_input("代理价", 0.00, 1.00, 0.25, 0.01)
    with col4:
        input_mul_b = st.number_input("到手价", 0.00, 1.00, 0.29, 0.01)
    
    if st.button("🔍 开始查询", use_container_width=True, type="primary"):
        st.cache_data.clear()

# 结果显示
if uid_input:
    date_str = date_input.strftime("%Y-%m-%d")
    data_list, err = fetch_data(uid_input, date_str)
    
    if err:
        st.error(f"查询失败: {err}")
    elif data_list:
        total_val, total_wang = 0, 0
        c_t = c_r = c_e = c_j1 = c_bw = 0
        rows = []
        
        for d in data_list:
            v, n = d['val'], d['name']
            total_val += v
            if n == 'TTTT': c_t += v
            elif n == '重复ID': c_r += v
            elif n == 'EEEE': c_e += v
            elif n == 'JJJJHHHH1': c_j1 += v
            elif n == 'BOWEI': c_bw += v
            
            fa, fb = get_team_factors(n, input_mul_a, input_mul_b)
            profit = v * (fb - fa)
            if n not in ['重复ID', 'EEEE', 'BOWEI']: total_wang += profit
            rows.append({"团队": n, "数量": v, "利润": f"¥{profit:.1f}"})
            
        hao_val = (total_val - c_t - c_r - c_e - c_j1 - c_bw) * 0.04 + (c_t * 0.015) + ((c_r + c_e + c_j1 + c_bw) * 0.33)
        
        # 大字报显示（适合手机）
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("王靖晗净利", f"¥{total_wang:.1f}")
        c2.metric("豪哥净利", f"¥{hao_val:.1f}")
        c3, c4 = st.columns(2)
        c3.metric("总采集量", total_val)
        c4.metric("项目总值", f"¥{total_val*0.33:.1f}")
        
        st.write("📋 **团队明细**")
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.info("当前没有数据")
