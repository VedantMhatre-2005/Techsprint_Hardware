"""
SafeLabs - Autonomous Server & Lab Guardian Dashboard
Real-time monitoring and AI-powered insights for lab safety
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import google.generativeai as genai

# Page configuration
st.set_page_config(
    page_title="SafeLabs - Lab Guardian",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background: #ff4444;
        padding: 1rem;
        border-radius: 5px;
        color: white;
        font-weight: bold;
    }
    .alert-warning {
        background: #ffbb33;
        padding: 1rem;
        border-radius: 5px;
        color: #333;
        font-weight: bold;
    }
    .alert-safe {
        background: #00C851;
        padding: 1rem;
        border-radius: 5px;
        color: white;
        font-weight: bold;
    }
    .ai-insight {
        background: #f0f7ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
@st.cache_resource
def init_firebase():
    """Initialize Firebase connection"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Try to load service account from file
            try:
                cred = credentials.Certificate('firebase-service-account.json')
            except FileNotFoundError:
                st.error("firebase-service-account.json not found!")
                st.info("Please add your Firebase service account JSON file to the project directory.")
                return None
            
            # Initialize with your database URL
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://safelabs-monitor-ab705-default-rtdb.firebaseio.com'
            })
        return db.reference('/')
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        return None

# Initialize Gemini AI (optional - for AI insights)
def init_gemini_ai(api_key=None):
    """Initialize Gemini AI for insights generation"""
    if api_key:
        try:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-pro')
        except Exception as e:
            st.warning(f"Could not initialize Gemini AI: {e}")
    return None

# Fetch latest sensor data
def get_latest_data(device_id="sensor_node_01"):
    """Fetch the latest sensor readings from Firebase"""
    try:
        ref = db.reference(f'/devices/{device_id}/latest')
        data = ref.get()
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Fetch historical data
def get_historical_data(device_id="sensor_node_01", limit=100):
    """Fetch historical sensor data"""
    try:
        ref = db.reference(f'/devices/{device_id}/history')
        data = ref.order_by_key().limit_to_last(limit).get()
        if data:
            df = pd.DataFrame.from_dict(data, orient='index')
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching historical data: {e}")
        return pd.DataFrame()

# Get AC control status
def get_ac_status(device_id="sensor_node_01"):
    """Get AC control status from Firebase"""
    try:
        ref = db.reference(f'/labs/{device_id}/ac')
        return ref.get() or False
    except:
        return False

# Set AC control status
def set_ac_status(device_id, status):
    """Set AC control status in Firebase"""
    try:
        ref = db.reference(f'/labs/{device_id}/ac')
        ref.set(status)
        return True
    except Exception as e:
        st.error(f"Error setting AC status: {e}")
        return False

# Generate AI insights using Gemini
def generate_ai_insights(sensor_data, gemini_model):
    """Generate AI-powered insights from sensor data"""
    if not gemini_model or not sensor_data:
        return None
    
    try:
        prompt = f"""
You are SafeLabs Virtual Facility Manager, an AI assistant for university lab safety.

Current Sensor Readings:
- Temperature: {sensor_data.get('temperature', 'N/A')}°C
- Humidity: {sensor_data.get('humidity', 'N/A')}%
- Gas Level: {sensor_data.get('gas_ppm', 'N/A')} ppm
- Motion Detected: {sensor_data.get('motion_detected', 'N/A')}
- 1h Avg Temperature: {sensor_data.get('avg_temp_1h', 'N/A')}°C
- 1h Avg Humidity: {sensor_data.get('avg_hum_1h', 'N/A')}%

Safe Ranges:
- Temperature: 18-26°C (optimal server room temp: 18-22°C)
- Humidity: 30-60%
- Gas: < 500 ppm

Provide a concise risk assessment and action recommendations in 2-3 sentences.
Focus on: safety status, energy efficiency, and immediate actions needed.
"""
        
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.warning(f"AI insights temporarily unavailable: {e}")
        return None

# Check if sensor is online (data is recent)
def is_sensor_online(data, timeout_seconds=30):
    """Check if sensor data is recent (within timeout)"""
    if not data:
        return False
    
    try:
        # If timestamp exists, check it
        if 'timestamp' in data:
            data_timestamp = data.get('timestamp', 0)
            current_time = int(time.time())
            
            # Check if timestamp looks like Unix time (> 1000000000) or boot time (< 100000)
            if data_timestamp > 1000000000:
                # Unix timestamp - check age
                age_seconds = current_time - data_timestamp
                return age_seconds <= timeout_seconds
            else:
                # Boot time from ESP32 - just check if data exists and has recent activity
                # We'll consider it online if we have sensor readings
                return True  # Data exists, assume online for boot timestamps
        
        # Fallback: if we have sensor data fields, consider it online
        return 'temperature' in data or 'humidity' in data
    except:
        return True  # On error, assume online if data exists

# Analyze sensor data and detect anomalies
def analyze_data(data):
    """Analyze sensor data and return status"""
    if not data:
        return "UNKNOWN", "No data available", "gray"
    
    # Check if sensor is online
    if not is_sensor_online(data):
        return "OFFLINE", "Sensor not responding - simulator may be stopped", "gray"
    
    temp = data.get('temperature', 0)
    humidity = data.get('humidity', 0)
    gas_ppm = data.get('gas_ppm', 0)
    motion = data.get('motion_detected', False)
    
    # Critical conditions
    critical_issues = []
    warnings = []
    
    if temp > 30 or temp < 10:
        critical_issues.append(f"Critical Temperature: {temp}°C")
    elif temp > 26 or temp < 18:
        warnings.append(f"Temperature Warning: {temp}°C")
    
    if humidity > 70 or humidity < 20:
        critical_issues.append(f"Critical Humidity: {humidity}%")
    elif humidity > 60 or humidity < 30:
        warnings.append(f"Humidity Warning: {humidity}%")
    
    if gas_ppm > 800:
        critical_issues.append(f"Dangerous Gas Level: {gas_ppm} ppm")
    elif gas_ppm > 500:
        warnings.append(f"Elevated Gas Level: {gas_ppm} ppm")
    
    # Determine overall status
    if critical_issues:
        return "CRITICAL", " | ".join(critical_issues), "red"
    elif warnings:
        return "WARNING", " | ".join(warnings), "orange"
    else:
        return "SAFE", "All parameters within safe range", "green"

# Main dashboard
def main():
    # Header
    st.markdown('<div class="main-header">SafeLabs - Lab Guardian Dashboard</div>', unsafe_allow_html=True)
    
    # Initialize Firebase
    firebase_ref = init_firebase()
    if not firebase_ref:
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/laboratory.png", width=100)
        st.title("Settings")
        
        # Multi-Lab Selector
        st.subheader("Select Lab")
        device_id = st.selectbox(
            "Lab/Device",
            ["sensor_node_01", "sensor_node_02", "sensor_node_03"],
            format_func=lambda x: {
                "sensor_node_01": "🔬 Computer Lab A",
                "sensor_node_02": "🖥️ Server Room B", 
                "sensor_node_03": "💻 Research Lab C"
            }[x],
            help="Choose which lab to monitor"
        )
        
        # Show all labs status summary
        st.markdown("---")
        st.subheader("All Labs Status")
        for lab_id in ["sensor_node_01", "sensor_node_02", "sensor_node_03"]:
            lab_data = get_latest_data(lab_id)
            if lab_data:
                status, _, color = analyze_data(lab_data)
                emoji = "🟢" if status == "SAFE" else "🟡" if status == "WARNING" else "🔴" if status == "CRITICAL" else "⚫"
                lab_name = {
                    "sensor_node_01": "Lab A",
                    "sensor_node_02": "Room B",
                    "sensor_node_03": "Lab C"
                }[lab_id]
                st.markdown(f"{emoji} **{lab_name}**: {status}")
            else:
                lab_name = {
                    "sensor_node_01": "Lab A",
                    "sensor_node_02": "Room B",
                    "sensor_node_03": "Lab C"
                }[lab_id]
                st.markdown(f"⚫ **{lab_name}**: OFFLINE")
        
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
        
        st.markdown("---")
        st.subheader("AI Assistant")
        gemini_api_key = st.text_input(
            "Gemini API Key (Optional)",
            type="password",
            help="Enter your Gemini API key for AI-powered insights"
        )
        
        gemini_model = init_gemini_ai(gemini_api_key) if gemini_api_key else None
        
        st.markdown("---")
        st.subheader("Data Range")
        data_limit = st.slider("Historical data points", 10, 500, 100)
        
        st.markdown("---")
        st.info("**About SafeLabs**\n\nAI-powered facility monitoring for university labs and server rooms.")
    
    # Display current lab name
    lab_names = {
        "sensor_node_01": "🔬 Computer Lab A",
        "sensor_node_02": "🖥️ Server Room B",
        "sensor_node_03": "💻 Research Lab C"
    }
    st.markdown(f"### Monitoring: {lab_names.get(device_id, device_id)}")
    st.markdown("---")
    
    # Fetch latest data
    latest_data = get_latest_data(device_id)
    
    if not latest_data:
        st.warning("No sensor data available. Make sure the IoT device is sending data to Firebase.")
        # Only stop here effectively, but allow rerun if needed? 
        # Actually st.stop() will kill the script. If we want auto-refresh to work even when no data, 
        # we might need to handle this differently. But for now, let's fix the main render loop.
        if auto_refresh:
            time.sleep(5)
            st.rerun()
        st.stop()
    
    # Analyze data
    status, message, color = analyze_data(latest_data)
    is_online = is_sensor_online(latest_data)
    
    # Status Banner
    if status == "OFFLINE" or not is_online:
        st.markdown(f'<div class="alert-warning">⚫ OFFLINE: Sensor not responding</div>', unsafe_allow_html=True)
        st.info("💡 **Tip**: Start the Wokwi simulation for this lab to see live data")
        
        # Show offline state with empty metrics
        st.subheader("Live Sensor Readings")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Temperature", value="-- °C", delta="Offline")
        with col2:
            st.metric(label="Humidity", value="-- %", delta="Offline")
        with col3:
            st.metric(label="Gas Level", value="-- ppm", delta="Offline")
        with col4:
            st.metric(label="Occupancy", value="Unknown", delta="Offline")
        
        st.markdown("---")
        st.warning("⚠️ Sensor offline - Start the simulation to view real-time data")
        
        # Auto-refresh for offline state
        if auto_refresh:
            time.sleep(5)
            st.rerun()
        st.stop()
    
    # ONLINE - Show full dashboard
    elif status == "CRITICAL":
        st.markdown(f'<div class="alert-critical">🔴 CRITICAL ALERT: {message}</div>', unsafe_allow_html=True)
    elif status == "WARNING":
        st.markdown(f'<div class="alert-warning">🟡 WARNING: {message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-safe">🟢 System Status: {message}</div>', unsafe_allow_html=True)
    
    st.markdown("")
    
    # Show last update time
    timestamp = latest_data.get('timestamp', 0)
    if timestamp > 0:
        if timestamp > 1000000000:
            # Unix timestamp
            last_update = datetime.fromtimestamp(timestamp)
            st.caption(f"📡 Last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            # Boot time in seconds
            st.caption(f"📡 Sensor uptime: {timestamp} seconds")
    
    # AI Insights Section
    if gemini_model:
        with st.expander("AI Virtual Facility Manager Insights", expanded=True):
            with st.spinner("Generating AI insights..."):
                insights = generate_ai_insights(latest_data, gemini_model)
                if insights:
                    st.markdown(f'<div class="ai-insight"><strong>AI Analysis:</strong><br>{insights}</div>', unsafe_allow_html=True)
    
    # Real-time Metrics
    st.subheader("Live Sensor Readings")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp = latest_data.get('temperature', 0)
        temp_delta = temp - latest_data.get('avg_temp_1h', temp)
        st.metric(
            label="Temperature",
            value=f"{temp:.1f}°C",
            delta=f"{temp_delta:.1f}°C vs 1h avg",
            delta_color="inverse"
        )
    
    with col2:
        humidity = latest_data.get('humidity', 0)
        hum_delta = humidity - latest_data.get('avg_hum_1h', humidity)
        st.metric(
            label="Humidity",
            value=f"{humidity:.1f}%",
            delta=f"{hum_delta:.1f}% vs 1h avg",
            delta_color="inverse"
        )
    
    with col3:
        gas = latest_data.get('gas_ppm', 0)
        gas_status = "Safe" if gas < 500 else "Elevated" if gas < 800 else "Danger"
        st.metric(
            label="Gas Level",
            value=f"{gas:.0f} ppm",
            delta=gas_status
        )
    
    with col4:
        motion = latest_data.get('motion_detected', False)
        st.metric(
            label="Occupancy",
            value="Occupied" if motion else "Empty",
            delta="Motion Detected" if motion else "No Motion"
        )
    
    st.markdown("---")
    
    # Energy Automation Control
    st.subheader("Energy Automation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ac_status = get_ac_status(device_id)
        
        st.markdown(f"""
        **AC/Cooling System Status:** {'ON' if ac_status else 'OFF'}
        
        *Occupancy-based automation helps reduce energy waste when labs are empty.*
        """)
        
        # Recommendation based on data
        if not motion and ac_status:
            st.warning("**Energy Saving Tip:** Lab is empty but AC is ON. Consider turning it off.")
        elif motion and not ac_status and temp > 26:
            st.info("**Comfort Tip:** Lab is occupied and temperature is high. Consider turning AC on.")
    
    with col2:
        st.markdown("**Manual Control**")
        if st.button("Turn AC ON", use_container_width=True):
            if set_ac_status(device_id, True):
                st.success("AC turned ON")
                time.sleep(1)
                st.rerun()
        
        if st.button("Turn AC OFF", use_container_width=True):
            if set_ac_status(device_id, False):
                st.success("AC turned OFF")
                time.sleep(1)
                st.rerun()
    
    st.markdown("---")
    
    # Historical Charts
    st.subheader("Historical Trends")
    
    hist_data = get_historical_data(device_id, limit=data_limit)
    
    if not hist_data.empty:
        tab1, tab2, tab3 = st.tabs(["Temperature & Humidity", "Gas Levels", "Occupancy"])
        
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_data['datetime'],
                y=hist_data['temperature'],
                name='Temperature (°C)',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=hist_data['datetime'],
                y=hist_data['humidity'],
                name='Humidity (%)',
                line=dict(color='#1f77b4', width=2),
                yaxis='y2'
            ))
            
            # Add safe range bands
            fig.add_hrect(y0=18, y1=26, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Safe Temp Range")
            
            fig.update_layout(
                title='Temperature and Humidity Over Time',
                xaxis_title='Time',
                yaxis_title='Temperature (°C)',
                yaxis2=dict(title='Humidity (%)', overlaying='y', side='right'),
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.area(
                hist_data,
                x='datetime',
                y='gas_ppm',
                title='Gas Levels Over Time',
                labels={'gas_ppm': 'Gas (ppm)', 'datetime': 'Time'}
            )
            fig.add_hline(y=500, line_dash="dash", line_color="orange", annotation_text="Warning Threshold")
            fig.add_hline(y=800, line_dash="dash", line_color="red", annotation_text="Critical Threshold")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Convert boolean to int for plotting
            hist_data['motion_int'] = hist_data['motion_detected'].astype(int)
            
            fig = px.scatter(
                hist_data,
                x='datetime',
                y='motion_int',
                title='Occupancy Detection Timeline',
                labels={'motion_int': 'Motion Detected', 'datetime': 'Time'},
                color='motion_int',
                color_continuous_scale=['red', 'green']
            )
            fig.update_layout(height=400, yaxis=dict(tickmode='array', tickvals=[0, 1], ticktext=['No Motion', 'Motion']))
            st.plotly_chart(fig, use_container_width=True)
            
            # Occupancy statistics
            col1, col2, col3 = st.columns(3)
            total_readings = len(hist_data)
            occupied_readings = hist_data['motion_detected'].sum()
            occupancy_rate = (occupied_readings / total_readings * 100) if total_readings > 0 else 0
            
            col1.metric("Total Readings", total_readings)
            col2.metric("Occupied", occupied_readings)
            col3.metric("Occupancy Rate", f"{occupancy_rate:.1f}%")
    else:
        st.info("No historical data available yet. Data will appear as the sensor sends readings.")
    
    st.markdown("---")
    
    # Data Table
    with st.expander("View Raw Data"):
        if not hist_data.empty:
            st.dataframe(
                hist_data[['datetime', 'temperature', 'humidity', 'gas_ppm', 'motion_detected', 'avg_temp_1h', 'avg_hum_1h']].tail(20),
                use_container_width=True
            )
        else:
            st.info("No data available")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <strong>SafeLabs</strong> - Autonomous Server & Lab Guardian<br>
        Powered by IoT, Cloud, and AI | Built for Educational Excellence<br>
        Last updated: {time}
    </div>
    """.format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

    # Auto-refresh logic (Moved to end)
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
