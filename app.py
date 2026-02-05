import streamlit as st
import qiskit
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from engine_gemini import compute_bell_magic_from_circuit  # Importing your clean backend

# --- Page Config ---
st.set_page_config(page_title="Bell Magic Calculator", page_icon="⚛️")

st.title("⚛️ Bell Magic Calculator")
st.markdown("""
**Calculate the non-stabilizerness (Magic) of your Quantum Circuit.**
Paste your Qiskit code below. The app will simulate the circuit, strip measurements, 
and calculate the Bell Magic metric.
""")

# --- Sidebar Parameters ---
st.sidebar.header("Simulation Settings")
depolarization = st.sidebar.slider("Depolarization Error", 0.0, 0.2, 0.0, 0.01)
n_samples = st.sidebar.select_slider(
    "Simulation Type",
    options=[0, 1000, 5000, 10000, 20000],
    value=0,
    format_func=lambda x: "Exact Statevector (Slow)" if x == 0 else f"{x} Shots"
)

# --- Helper: Circuit Extractor ---
def extract_circuit_from_python(code_string):
    """Safely executes Python string to find a 'circuit' object."""
    local_scope = {}
    # specific imports users might need
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
        
        # Look for 'circuit' or 'qc'
        if 'circuit' in local_scope and isinstance(local_scope['circuit'], QuantumCircuit):
            return local_scope['circuit'], None
        elif 'qc' in local_scope and isinstance(local_scope['qc'], QuantumCircuit):
            return local_scope['qc'], None
        else:
            return None, "Variable 'circuit' or 'qc' not found in code."
            
    except Exception as e:
        return None, f"Syntax Error: {e}"

# --- Input Area (Default is your original circuit) ---
default_code = """from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from numpy import pi

qreg_q = QuantumRegister(2, 'q')
creg_c = ClassicalRegister(2, 'c')
circuit = QuantumCircuit(qreg_q, creg_c)

circuit.h(qreg_q[0])
circuit.t(qreg_q[0]) # non-Clifford gate
circuit.cx(qreg_q[0], qreg_q[1])
circuit.measure(qreg_q[0], creg_c[0])
circuit.measure(qreg_q[1], creg_c[1])
"""

code_input = st.text_area("Python Qiskit Code", value=default_code, height=300)

# --- Main Execution ---
if st.button("Calculate Bell Magic", type="primary"):
    with st.spinner("Compiling and Simulating..."):
        
        # 1. Extract Circuit
        circuit, error = extract_circuit_from_python(code_input)
        
        if error:
            st.error(f"❌ {error}")
        else:
            try:
                # 2. Safety Check (Prevent massive circuits crashing server)
                if circuit.num_qubits > 10:
                    st.error("Circuit too large! Max 10 qubits allowed for online demo.")
                    st.stop()

                # 3. Visuals
                st.subheader("Circuit Diagram")
                st.text(circuit.draw(output='text'))
                
                # 4. Run Calculation
                results = compute_bell_magic_from_circuit(
                    circuit, 
                    depolarization_factor=depolarization, 
                    n_samples=n_samples
                )

                # 5. Display Results
                st.success("Calculation Complete")
                c1, c2, c3 = st.columns(3)
                c1.metric("Bell Magic", f"{results['bell_magic']:.4f}")
                c2.metric("Additive Magic", f"{results['additive_bell_magic']:.4f}")
                c3.metric("Purity", f"{results['purity']:.4f}")

            except Exception as e:

                st.error(f"Simulation Error: {str(e)}")
