"""
 Geo-Attack Predictions
=========================
Visual world map showing which countries are most likely
to be attacked next, with probability percentages.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.theme import CYBERPUNK_CSS

try:
    st.set_page_config(
        page_title="Geo Predictions | SOC",
        page_icon="",
        layout="wide"
    )
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align: center; padding: 20px 0 30px;">
    <h1 style="font-size: 2.5rem; font-weight: 700; margin: 0; color: #fff;">
         Geo-Attack Predictions
    </h1>
    <p style="color: #888; font-size: 0.9rem; letter-spacing: 2px; margin-top: 5px;">
        ML-POWERED COUNTRY THREAT FORECASTING
    </p>
</div>
""", unsafe_allow_html=True)

# Import geo predictor
try:
    from ml_engine.geo_predictor import predict_country_attacks, get_top_targets, get_globe_visualization_data
    GEO_LOADED = True
except ImportError as e:
    GEO_LOADED = False
    st.error(f"Geo predictor not available: {e}")

if GEO_LOADED:
    predictions = predict_country_attacks()
    top_targets = get_top_targets(5)
    
    # Summary banner
    top_country, top_data = top_targets[0]
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {top_data['color']}22, {top_data['color']}11);
        border: 1px solid {top_data['color']}66;
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        margin-bottom: 25px;
    ">
        <div style="font-size: 0.8rem; color: #888; letter-spacing: 2px;">HIGHEST RISK TARGET</div>
        <div style="font-size: 2.5rem; font-weight: 800; color: {top_data['color']}; margin: 10px 0;">
            {top_country} — {top_data['probability']}%
        </div>
        <div style="color: #aaa;">
            Most Likely Attack: <strong>{top_data['likely_attack']}</strong> | 
            Sectors at Risk: <strong>{', '.join(top_data['target_sectors'])}</strong> |
            ETA: <strong>{top_data['eta_hours']} hours</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Top 5 targets
    st.markdown("###  Top 5 Most Likely Targets")
    
    cols = st.columns(5)
    for i, (country, data) in enumerate(top_targets):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: rgba(0,0,0,0.3);
                border: 2px solid {data['color']}40;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                height: 220px;
            ">
                <div style="font-size: 0.7rem; color: #666;">#{i+1}</div>
                <div style="font-size: 1.5rem; margin: 5px 0;"></div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #fff;">{country}</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: {data['color']}; margin: 10px 0;">
                    {data['probability']}%
                </div>
                <div style="
                    background: {data['color']}33;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    color: {data['color']};
                    font-weight: 600;
                    display: inline-block;
                ">{data['risk_level']}</div>
                <div style="font-size: 0.75rem; color: #888; margin-top: 8px;">
                    {data['trend']} {data['likely_attack']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs([" Full Rankings", " Analysis Factors", " Trend Data"])
    
    with tab1:
        st.markdown("### All Countries by Attack Probability")
        
        for country, data in predictions.items():
            bar_width = data['probability']
            
            st.markdown(f"""
            <div style="
                background: rgba(0,0,0,0.2);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 12px 15px;
                margin: 8px 0;
                display: flex;
                align-items: center;
                gap: 15px;
            ">
                <div style="width: 120px; font-weight: 600;">{country}</div>
                <div style="flex: 1; background: #1a1a2e; border-radius: 4px; height: 25px; overflow: hidden;">
                    <div style="
                        width: {bar_width}%;
                        height: 100%;
                        background: linear-gradient(90deg, {data['color']}88, {data['color']});
                        display: flex;
                        align-items: center;
                        padding-left: 10px;
                        font-size: 0.85rem;
                        font-weight: 700;
                    ">{data['probability']}%</div>
                </div>
                <div style="width: 80px; text-align: center;">
                    <span style="
                        background: {data['color']}33;
                        color: {data['color']};
                        padding: 3px 8px;
                        border-radius: 4px;
                        font-size: 0.7rem;
                        font-weight: 600;
                    ">{data['risk_level']}</span>
                </div>
                <div style="width: 100px; color: #888; font-size: 0.8rem;">{data['likely_attack']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Prediction Factors Analysis")
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00D4FF; margin: 0;">How Predictions Are Calculated</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Our ML model considers multiple factors to predict attack probability:
            </p>
            <ul style="color: #FAFAFA;">
                <li><strong>Base Risk Profile:</strong> Historical attack frequency for each country</li>
                <li><strong>Temporal Factor:</strong> Time of day and day of week patterns</li>
                <li><strong>Trend Analysis:</strong> Recent vs historical attack comparison</li>
                <li><strong>Geopolitical Factor:</strong> Current global tensions and relations</li>
                <li><strong>Target Value:</strong> Economic and strategic importance</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("### Factor Breakdown by Country")
        
        # Display factor analysis for top 5
        for country, data in list(predictions.items())[:5]:
            factors = data.get('factors', {})
            
            with st.expander(f"**{country}** — {data['probability']}% ({data['risk_level']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    temporal = factors.get('temporal', 1.0)
                    temporal_color = "#00ff88" if temporal > 1 else "#888"
                    st.markdown(f"""
                    <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                        <div style="font-size: 2rem; font-weight: 800; color: {temporal_color};">{temporal}x</div>
                        <div style="font-size: 0.8rem; color: #888;">Temporal Factor</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    trend = factors.get('trend', 1.0)
                    trend_color = "#ff6600" if trend > 1.1 else "#00ff88" if trend < 0.9 else "#888"
                    st.markdown(f"""
                    <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                        <div style="font-size: 2rem; font-weight: 800; color: {trend_color};">{trend}x</div>
                        <div style="font-size: 0.8rem; color: #888;">Trend Factor</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    geo = factors.get('geopolitical', 1.0)
                    geo_color = "#ff0040" if geo > 1.2 else "#ffcc00" if geo > 1.0 else "#888"
                    st.markdown(f"""
                    <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                        <div style="font-size: 2rem; font-weight: 800; color: {geo_color};">{geo}x</div>
                        <div style="font-size: 0.8rem; color: #888;">Geopolitical Factor</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### Recent Attack Trends")
        
        import plotly.graph_objects as go
        
        # Create bar chart of recent attacks
        countries = [c for c, _ in list(predictions.items())[:10]]
        recent_attacks = [predictions[c]['recent_attacks'] for c in countries]
        colors = [predictions[c]['color'] for c in countries]
        
        fig = go.Figure(data=[
            go.Bar(
                x=countries,
                y=recent_attacks,
                marker_color=colors,
                text=recent_attacks,
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Recent Attacks (Last 7 Days)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            yaxis_title="Attack Count",
            xaxis_title="Country"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Probability vs Recent Attacks scatter
        all_countries = list(predictions.keys())
        probs = [predictions[c]['probability'] for c in all_countries]
        attacks = [predictions[c]['recent_attacks'] for c in all_countries]
        colors = [predictions[c]['color'] for c in all_countries]
        
        fig2 = go.Figure(data=[
            go.Scatter(
                x=attacks,
                y=probs,
                mode='markers+text',
                marker=dict(size=15, color=colors, line=dict(width=2, color='white')),
                text=all_countries,
                textposition='top center',
                textfont=dict(size=10)
            )
        ])
        
        fig2.update_layout(
            title="Probability vs Recent Attack Count",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis_title="Recent Attacks (7 days)",
            yaxis_title="Attack Probability (%)"
        )
        
        st.plotly_chart(fig2, use_container_width=True)

# Inject floating CORTEX orb
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
