import streamlit as st
import qiskit
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from engine_gemini import compute_bell_magic_from_circuit  # Importing your clean backend

# --- Page Config ---
st.set_page_config(
    page_title="Bell Magic Calculator",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0E1117; }
    
    /* Gradient Title */
    .title-text {
        font-weight: 700;
        font-size: 50px !important;
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: -10px;
    }
    
    /* Metric Cards */
    .metric-card {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #00C9FF;
    }
    .metric-value { font-size: 2.5rem; font-weight: bold; color: #F3F4F6; }
    .metric-label { font-size: 1rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Input Area */
    .stTextArea textarea {
        background-color: #111827;
        color: #A5B4FC;
        border: 1px solid #374151;
        font-family: 'Courier New', monospace;
    }
    
    /* Action Button */
    div.stButton > button {
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        font-size: 18px;
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.6);
        transform: scale(1.02);
    }

    /* CITATION CARD STYLING */
    .citation-box {
        background-color: #1F2937;
        border-left: 6px solid #F59E0B; /* Amber accent */
        border-radius: 8px;
        padding: 20px;
        margin-top: 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .citation-content h4 {
        margin: 0;
        color: #F3F4F6;
        font-size: 1.1rem;
    }
    .citation-content p {
        margin: 5px 0 0 0;
        color: #9CA3AF;
        font-style: italic;
    }
    .github-link {
        text-decoration: none;
        background-color: #374151;
        color: #E5E7EB !important;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        border: 1px solid #4B5563;
        transition: all 0.2s;
    }
    .github-link:hover {
        background-color: #4B5563;
        border-color: #9CA3AF;
        color: white !important;
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
    st.markdown("### ⚙️ Simulation Settings")
    st.markdown("Configure the noise model and sampling strategy.")
    st.write("---")
    depolarization = st.slider("Depolarization Error", 0.0, 0.2, 0.0, 0.01)
    n_samples = st.select_slider(
        "Simulation Type",
        options=[0, 1000, 5000, 10000, 20000],
        value=0,
        format_func=lambda x: "Exact Statevector (Slow)" if x == 0 else f"{x} Shots"
    )

# --- Main Layout ---
col_header_1, col_header_2 = st.columns([2, 1])
with col_header_1:
    st.markdown('<h1 class="title-text">Bell Magic Calculator</h1>', unsafe_allow_html=True)
    st.markdown('<div style="color: #9CA3AF;">Quantify the <b>non-stabilizerness</b> (Magic) of your Quantum Circuit.</div>', unsafe_allow_html=True)

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

with main_col1:
    st.markdown("### 💻 Input Circuit")
    code_input = st.text_area("Python Qiskit Code", value=default_code, height=350, label_visibility="collapsed")
    st.write("")
    if st.button("🚀 Calculate Magic Resources", type="primary"):
        run_simulation = True
    else:
        run_simulation = False

with main_col2:
    st.markdown("### 📊 Analysis Dashboard")
    if run_simulation:
        with st.status("Processing Quantum Circuit...", expanded=True) as status:
            circuit, error = extract_circuit_from_python(code_input)
            if error:
                status.update(label="Error detected", state="error")
                st.error(f"❌ {error}")
            elif circuit.num_qubits > 10:
                status.update(label="Circuit too large", state="error")
                st.error("Circuit too large! Max 10 qubits allowed.")
            else:
                try:
                    results = compute_bell_magic_from_circuit(circuit, depolarization_factor=depolarization, n_samples=n_samples)
                    status.update(label="Calculation Complete!", state="complete", expanded=False)
                    
                    # Display Cards
                    st.markdown(f"""
                    <div class="metric-card"><div class="metric-label">Bell Magic</div><div class="metric-value" style="color: #60A5FA;">{results['bell_magic']:.4f}</div></div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f"""
                    <div class="metric-card"><div class="metric-label">Additive Magic</div><div class="metric-value" style="color: #34D399;">{results['additive_bell_magic']:.4f}</div></div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f"""
                    <div class="metric-card"><div class="metric-label">State Purity</div><div class="metric-value" style="color: #A78BFA;">{results['purity']:.4f}</div></div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    status.update(label="Simulation Failed", state="error")
                    st.error(f"Error: {str(e)}")
    else:
        st.info("👋 Click **Calculate** to see magic metrics here.")

# --- Bottom Section: Reference ---
st.write("---")

# Beautiful Citation Block
st.markdown("""
<div class="citation-box">
    <div class="citation-content">
        <h4>📚 Scientific Reference & Inspiration</h4>
        <p>"Scalable Measures of Magic Resource for Quantum Computers" — Tobias Haug & M.S. Kim</p>
    </div>
    <a href="https://github.com/txhaug/bell-magic" target="_blank" class="github-link">
        📂 View on GitHub
    </a>
</div>
""", unsafe_allow_html=True)
