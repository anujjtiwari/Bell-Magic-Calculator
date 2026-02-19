import streamlit as st
import qiskit
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from engine_gemini import compute_bell_magic_from_circuit  # Importing your clean backend

# --- Page Config ---
st.set_page_config(
    page_title="Bell Magic Calculator",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Cyber/Futuristic UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');

    /* Main Cyber Background with Subtle Grid */
    .stApp { 
        background-color: #050505; 
        background-image: 
            linear-gradient(rgba(0, 201, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 201, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
    }
    
    /* Global Fonts */
    h1, h2, h3, h4 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
    }
    
    /* Gradient Title */
    .title-text {
        font-weight: 700;
        font-size: 50px !important;
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: -10px;
        text-shadow: 0px 0px 20px rgba(0, 201, 255, 0.2);
    }
    
    /* Cyber Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, #0f172a, #1e293b);
        border: 1px solid #1e293b;
        border-top: 2px solid #00C9FF; /* Cyber cyan accent */
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; width: 50%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 201, 255, 0.1), transparent);
        transition: left 0.5s ease;
    }
    .metric-card:hover::before {
        left: 100%;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-top-color: #92FE9D;
        box-shadow: 0 10px 25px rgba(146, 254, 157, 0.2);
    }
    .metric-value { font-size: 2.5rem; font-weight: bold; color: #F3F4F6; font-family: 'Share Tech Mono', monospace; }
    .metric-label { font-size: 1rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 2px; }
    
    /* Hacker Terminal Input Area */
    .stTextArea textarea {
        background-color: #000000 !important;
        color: #00FF41 !important; /* Matrix Green */
        border: 1px solid #00C9FF !important;
        box-shadow: 0 0 10px rgba(0, 201, 255, 0.1);
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 16px;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        box-shadow: 0 0 20px rgba(0, 201, 255, 0.4);
        border-color: #92FE9D !important;
    }
    
    /* Neon Action Button */
    div.stButton > button {
        background: transparent;
        color: #00C9FF;
        border: 2px solid #00C9FF;
        padding: 12px 28px;
        font-size: 18px;
        border-radius: 4px;
        width: 100%;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease;
        box-shadow: inset 0 0 10px rgba(0, 201, 255, 0.2), 0 0 10px rgba(0, 201, 255, 0.2);
    }
    div.stButton > button:hover {
        background: #00C9FF;
        color: #000000;
        box-shadow: inset 0 0 20px rgba(0, 201, 255, 0.6), 0 0 20px rgba(0, 201, 255, 0.6);
        transform: scale(1.02);
    }

    /* CITATION CARD STYLING */
    .citation-box {
        background-color: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #F59E0B;
        border-radius: 4px;
        padding: 20px;
        margin-top: 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        backdrop-filter: blur(5px);
    }
    .citation-content h4 { margin: 0; color: #F3F4F6; font-size: 1.1rem; }
    .citation-content p { margin: 5px 0 0 0; color: #9CA3AF; font-style: italic; }
    .github-link {
        text-decoration: none;
        background-color: transparent;
        color: #F59E0B !important;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        border: 1px solid #F59E0B;
        transition: all 0.2s;
        font-family: 'Orbitron', sans-serif;
    }
    .github-link:hover {
        background-color: #F59E0B;
        color: #000 !important;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- Helper: Circuit Extractor ---
def extract_circuit_from_python(code_string):
    local_scope = {}
    global_scope = {
        "qiskit": qiskit,
        "QuantumCircuit": QuantumCircuit,
        "QuantumRegister": QuantumRegister,
        "ClassicalRegister": ClassicalRegister,
        "np": np,
        "pi": np.pi
    }
    try:
        exec(code_string, global_scope, local_scope)
        if 'circuit' in local_scope and isinstance(local_scope['circuit'], QuantumCircuit):
            return local_scope['circuit'], None
        elif 'qc' in local_scope and isinstance(local_scope['qc'], QuantumCircuit):
            return local_scope['qc'], None
        else:
            return None, "Variable 'circuit' or 'qc' not found."
    except Exception as e:
        return None, f"Syntax Error: {e}"

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM SETTINGS")
    st.markdown("<div style='color: #9CA3AF; font-size: 0.9em; margin-bottom: 15px;'>Calibrate noise & sampling parameters</div>", unsafe_allow_html=True)
    depolarization = st.slider("Depolarization Error", 0.0, 0.2, 0.0, 0.01)
    n_samples = st.select_slider(
        "Simulation Type",
        options=[0, 1000, 5000, 10000, 20000],
        value=0,
        format_func=lambda x: "Exact Statevector" if x == 0 else f"{x} Shots"
    )

# --- Main Layout ---
col_header_1, col_header_2 = st.columns([2, 1])
with col_header_1:
    st.markdown('<h1 class="title-text">BELL MAGIC TERMINAL</h1>', unsafe_allow_html=True)
    st.markdown('<div style="color: #00FF41; font-family: \'Share Tech Mono\', monospace; margin-top: 5px;">> QUANTIFY NON-STABILIZERNESS // INITIALIZE METRICS</div>', unsafe_allow_html=True)

st.write("") 
main_col1, main_col2 = st.columns([1.5, 1], gap="large")

default_code = """from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from numpy import pi

qreg_q = QuantumRegister(2, 'q')
creg_c = ClassicalRegister(2, 'c')
circuit = QuantumCircuit(qreg_q, creg_c)

circuit.h(qreg_q[0])
circuit.t(qreg_q[0]) 
circuit.cx(qreg_q[0], qreg_q[1])
circuit.measure(qreg_q[0], creg_c[0])
circuit.measure(qreg_q[1], creg_c[1])
"""

circuit, error = None, None

with main_col1:
    st.markdown("### Please paste your Qiskit code below ↓")
    code_input = st.text_area("Python Qiskit Code", value=default_code, height=350, label_visibility="collapsed")
    st.write("")
    
    run_simulation = st.button("🚀 EXECUTE MAGIC PROTOCOL", type="primary")

    if run_simulation:
        circuit, error = extract_circuit_from_python(code_input)
        
        if not error and circuit.num_qubits <= 10:
            st.markdown("### 🧩 // TOPOLOGY_RENDER")
            
            # Print ASCII text-based diagram in a monospace block
            st.markdown("```text\n" + str(circuit.draw(output="text")) + "\n```")
            
            # Print Custom Dark-Themed Matplotlib graphical diagram
            try:
                st.markdown("**VISUAL_OUTPUT:**")
                
                # Custom dictionary for a cyber Qiskit style
                cyber_style = {
                    "backgroundcolor": "#000000",
                    "textcolor": "#00FF41",
                    "linecolor": "#00C9FF",
                    "gatetextcolor": "#000000",
                    "gatefacecolor": "#00C9FF"
                }
                
                fig = circuit.draw(output="mpl", fold=-1, style=cyber_style)
                # Set the outer padding color to match the grid background
                fig.patch.set_facecolor('#050505') 
                
                st.pyplot(fig)
                plt.close(fig)
            except Exception as e:
                st.warning(f"Could not generate graphical drawing. Error: {e}")

with main_col2:
    st.markdown("### 📊 // TELEMETRY")
    if run_simulation:
        with st.status("INITIALIZING QUANTUM ENGINE...", expanded=True) as status:
            if error:
                status.update(label="CRITICAL ERROR DETECTED", state="error")
                st.error(f"❌ {error}")
            elif circuit.num_qubits > 10:
                status.update(label="OVERFLOW: MAX QUBITS EXCEEDED", state="error")
                st.error("Circuit too large! Max 10 qubits allowed.")
            else:
                try:
                    results = compute_bell_magic_from_circuit(circuit, depolarization_factor=depolarization, n_samples=n_samples)
                    status.update(label="PROTOCOL COMPLETE", state="complete", expanded=False)
                    
                    # Display Cards
                    st.markdown(f"""
                    <div class="metric-card"><div class="metric-label">BELL MAGIC</div><div class="metric-value" style="color: #00C9FF;">{results['bell_magic']:.4f}</div></div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f"""
                    <div class="metric-card"><div class="metric-label">ADDITIVE MAGIC</div><div class="metric-value" style="color: #92FE9D;">{results['additive_bell_magic']:.4f}</div></div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f"""
                    <div class="metric-card"><div class="metric-label">STATE PURITY</div><div class="metric-value" style="color: #A78BFA;">{results['purity']:.4f}</div></div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    status.update(label="SIMULATION FAILURE", state="error")
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Awaiting execution command. Press **EXECUTE** to begin telemetry.")

# --- Bottom Section: Reference ---
st.write("---")

st.markdown("""
<div class="citation-box">
    <div class="citation-content">
        <h4>An inspired work from</h4>
        <p>"Scalable Measures of Magic Resource for Quantum Computers" — Tobias Haug & M.S. Kim</p>
    </div>
    <a href="https://github.com/txhaug/bell-magic" target="_blank" class="github-link">
        > ACCESS_REPO
    </a>
</div>
""", unsafe_allow_html=True)