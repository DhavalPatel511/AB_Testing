"""
Streamlit Dashboard for A/B Testing Analysis
Run with: streamlit run dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
import json

# Page config
st.set_page_config(
    page_title="A/B Test Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 A/B Testing Dashboard: Desktop vs Mobile")
st.markdown("**Google Merchandise Store Conversion Analysis**")

# Sidebar
st.sidebar.header("Settings")
avg_order_value = st.sidebar.number_input("Average Order Value ($)", value=50, min_value=1)
confidence_level = st.sidebar.selectbox("Confidence Level", [0.90, 0.95, 0.99], index=1)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/google_merch_users.csv')
    return df

try:
    df = load_data()
    
    desktop = df[df['device'] == 'desktop']
    mobile = df[df['device'] == 'mobile']
    
    # Calculate metrics
    desktop_conv = desktop['converted'].sum()
    desktop_n = len(desktop)
    desktop_cr = desktop_conv / desktop_n
    
    mobile_conv = mobile['converted'].sum()
    mobile_n = len(mobile)
    mobile_cr = mobile_conv / mobile_n
    
    # Statistical test
    successes = np.array([desktop_conv, mobile_conv])
    nobs = np.array([desktop_n, mobile_n])
    z_stat, p_value = proportions_ztest(successes, nobs, alternative='two-sided')
    
    ci_low, ci_high = confint_proportions_2indep(
        desktop_conv, desktop_n,
        mobile_conv, mobile_n,
        method='wald'
    )
    
    # ========================================================================
    # KEY METRICS ROW
    # ========================================================================
    st.header("🎯 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Desktop CR",
            f"{desktop_cr*100:.2f}%",
            delta=f"{desktop_n:,} users"
        )
    
    with col2:
        st.metric(
            "Mobile CR",
            f"{mobile_cr*100:.2f}%",
            delta=f"{mobile_n:,} users"
        )
    
    with col3:
        lift = (desktop_cr - mobile_cr) / mobile_cr
        st.metric(
            "Desktop Lift",
            f"{lift*100:.1f}%",
            delta=f"{(desktop_cr - mobile_cr)*100:.2f}pp"
        )
    
    with col4:
        annual_revenue = mobile_n * (desktop_cr - mobile_cr) * avg_order_value * 12
        st.metric(
            "Annual Opportunity",
            f"${annual_revenue:,.0f}",
            delta=f"p={p_value:.3f}"
        )
    
    # ========================================================================
    # VISUALIZATION 1: Main Result
    # ========================================================================
    st.header("📊 Conversion Rate Comparison")
    
    se_desktop = (desktop_cr * (1-desktop_cr) / desktop_n) ** 0.5
    se_mobile = (mobile_cr * (1-mobile_cr) / mobile_n) ** 0.5
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['Desktop', 'Mobile'],
        y=[desktop_cr * 100, mobile_cr * 100],
        error_y=dict(
            type='data',
            array=[se_desktop * 1.96 * 100, se_mobile * 1.96 * 100]
        ),
        text=[f'{desktop_cr*100:.2f}%', f'{mobile_cr*100:.2f}%'],
        textposition='outside',
        marker=dict(
            color=['#2ecc71', '#e74c3c'],
            line=dict(color='black', width=1.5)
        )
    ))
    
    if p_value < 0.05:
        fig.add_annotation(
            x=0.5,
            y=max(desktop_cr, mobile_cr) * 100 * 1.2,
            text=f"★ Statistically Significant (p={p_value:.3f})",
            showarrow=False,
            font=dict(size=14, color='green', family='Arial Black')
        )
    
    fig.update_layout(
        yaxis_title='Conversion Rate (%)',
        showlegend=False,
        height=400,
        yaxis=dict(range=[0, max(desktop_cr, mobile_cr) * 100 * 1.4])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # STATISTICAL DETAILS
    # ========================================================================
    st.header("📈 Statistical Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Test Results")
        st.write(f"**Test Type:** Two-sample Z-test for proportions")
        st.write(f"**Z-statistic:** {z_stat:.3f}")
        st.write(f"**P-value:** {p_value:.4f}")
        st.write(f"**Significance:** {'✅ Yes' if p_value < 0.05 else '❌ No'} (α=0.05)")
    
    with col2:
        st.subheader("Effect Size")
        st.write(f"**Absolute Difference:** {(desktop_cr - mobile_cr)*100:.2f} pp")
        st.write(f"**Relative Lift:** {lift*100:.1f}%")
        st.write(f"**95% CI:** [{ci_low*100:.2f}pp, {ci_high*100:.2f}pp]")
    
    # ========================================================================
    # VISUALIZATION 2: Revenue Impact
    # ========================================================================
    st.header("💰 Business Impact")
    
    categories = ['Current Mobile<br>Revenue', 'If Mobile = Desktop<br>Revenue', 'Monthly<br>Opportunity']
    values = [
        mobile_n * mobile_cr * avg_order_value,
        mobile_n * desktop_cr * avg_order_value,
        mobile_n * (desktop_cr - mobile_cr) * avg_order_value
    ]
    
    colors = ['lightgray', '#2ecc71', '#3498db']
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=categories,
        y=values,
        text=[f'${v:,.0f}' for v in values],
        textposition='outside',
        marker_color=colors
    ))
    
    fig2.update_layout(
        yaxis_title='Revenue ($)',
        showlegend=False,
        height=350
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================
    st.header("🎯 Recommendations")
    
    if p_value < 0.05 and lift > 0.10:
        st.success("**STRONG RECOMMENDATION:** Invest in mobile optimization")
        st.write("""
        **Priority Actions:**
        1. Optimize mobile checkout flow (reduce form fields, add mobile payments)
        2. Improve mobile page load speed (< 3 seconds)
        3. A/B test mobile-specific improvements
        4. Focus on organic traffic first (highest desktop advantage)
        """)
    elif p_value < 0.05:
        st.warning("**MODERATE RECOMMENDATION:** Consider mobile optimization")
        st.write("Effect size is small but statistically significant. Test specific improvements.")
    else:
        st.info("**WEAK RECOMMENDATION:** Monitor, gather more data")
    
    # ========================================================================
    # RAW DATA
    # ========================================================================
    with st.expander("📋 View Raw Data"):
        st.subheader("Sample Data")
        st.dataframe(df.head(100))
        
        st.subheader("Summary Statistics")
        st.write(df.groupby('device').agg({
            'converted': ['count', 'sum', 'mean'],
            'page_views': 'mean',
            'num_sessions': 'mean'
        }))
    
    # ========================================================================
    # EXPORT RESULTS
    # ========================================================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Results")
    
    results = {
        'desktop_n': int(desktop_n),
        'mobile_n': int(mobile_n),
        'desktop_cr': float(desktop_cr),
        'mobile_cr': float(mobile_cr),
        'z_statistic': float(z_stat),
        'p_value': float(p_value),
        'ci_lower': float(ci_low),
        'ci_upper': float(ci_high),
        'lift_pct': float(lift * 100),
        'annual_revenue_impact': float(annual_revenue)
    }
    
    if st.sidebar.button("💾 Save Results to JSON"):
        with open('results/test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        st.sidebar.success("✅ Saved to results/test_results.json")

except FileNotFoundError:
    st.error("""
    ❌ **Data file not found!**
    
    Please ensure `data/google_merch_users.csv` exists in your project directory.
    """)
except Exception as e:
    st.error(f"❌ **Error:** {str(e)}")
    st.write("Please check your data file and try again.")

# Footer
st.markdown("---")
st.markdown("**A/B Testing Dashboard** | Built with Streamlit & Plotly")