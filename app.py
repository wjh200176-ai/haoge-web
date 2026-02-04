import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime
import urllib3

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 1. 页面配置 (必须在第一行) =================
st.set_page_config(
    page_title="豪哥数据中心", 
    page_icon="📱", 
    layout="wide", # 这里的 wide 适配手机效果更好
    initial_sidebar_state="collapsed" # 默认收起侧边栏，更像APP
)

# ================= 2. 注入CSS (美化 + 去广告) =================
st.markdown("""
    <style>
    /* 1. 隐藏 Streamlit 自带的菜单、页脚、顶部红线 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 2. 全局深色背景模拟 */
    .stApp {
        background-color: #0E1117;
    }
    
    /* 3. 卡片样式优化 */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #41444C;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    
    /* 4. 关键数字颜色 */
    /* 利润文字设为金色 */
    div[data-testid="stMetricValue"] {
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ================= 3. 核心功能函数 (逻辑不变) =================

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
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    payload = {"user_ids": uid, "date": date_str, "platform_type": "网页", "browser_type": "全部浏览器"}
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

# ================= 4. 手机端界面布局 =================

st.markdown("<h3 style='text-align: center; color: #E4E4E7;'>📱 豪哥数据中心</h3>", unsafe_allow_html=True)

# 输入区域 (用折叠栏收纳，保持界面整洁)
with st.expander("🛠️ 点击设置查询条件", expanded=False):
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
    
    if st.button("🚀 刷新查询", use_container_width=True, type="primary"):
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
        
        # === 核心数据看板 (美化版) ===
        st.markdown("---")
        
        # 第一行：最关心的利润
        c1, c2 = st.columns(2)
        with c1:
            st.metric("👑 王靖晗净利", f"¥{total_wang:.1f}")
        with c2:
            st.metric("💰 豪哥净利", f"¥{hao_val:.1f}")
        
        # 第二行：统计数据
        st.markdown("<br>", unsafe_allow_html=True) # 加点空隙
        c3, c4 = st.columns(2)
        with c3:
            st.metric("📊 总采集量", total_val)
        with c4:
            st.metric("📈 项目总值", f"¥{total_val*0.33:.1f}")
        
        # 详细表格
        st.markdown("---")
        st.markdown("<h5 style='color: #A1A1AA;'>📋 团队明细表</h5>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.info("当前没有数据")
