import numpy as np
import qiskit as qk
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.circuit import Measure, Reset
from qiskit_aer import Aer
from qiskit_aer.noise import NoiseModel, depolarizing_error  # ADDED: For realistic circuit noise

# ---- Helper Functions ----

def numberToBase(n, b, n_qubits):
    if n == 0:
        return np.zeros(n_qubits, dtype=int)
    digits = np.zeros(n_qubits, dtype=int)
    counter = 0
    while n:
        digits[counter] = int(n % b)
        n //= b
        counter += 1
    return digits[::-1]

def does_pauli_not_commute(pauli1, pauli2):
    if pauli1 != pauli2 and pauli1 != 0 and pauli2 != 0:
        return 1
    else:
        return 0

def get_pauli_commute_map():
    x1 = np.arange(4)
    x2 = np.arange(4)
    map_pauli_commute = np.zeros(16)
    for i in range(4):
        for j in range(4):
            map_pauli_commute[4 * i + j] = does_pauli_not_commute(x1[i], x2[j])
    return map_pauli_commute

def bell_magic_exact(bitstrings_sampled, sampled_states_probs):
    pauli_commute_map = get_pauli_commute_map()
    string_length = len(bitstrings_sampled[0])
    n_qubits = string_length // 2
    n_bitstring_samples = len(bitstrings_sampled)
    
    bitstrings_added_list = np.zeros([((n_bitstring_samples - 1) * n_bitstring_samples) // 2, string_length], dtype=int)
    bitstrings_added_probs = np.zeros([((n_bitstring_samples - 1) * n_bitstring_samples) // 2])

    start = 0
    for q in range(n_bitstring_samples - 1):
        bitstrings_added_list[start:start + n_bitstring_samples - q - 1, :] = (bitstrings_sampled[q] + bitstrings_sampled[q + 1:]) % 2
        bitstrings_added_probs[start:start + n_bitstring_samples - q - 1] = 2 * sampled_states_probs[q] * sampled_states_probs[q + 1:]
        start += n_bitstring_samples - q - 1

    bitstrings_added_probs = np.array(bitstrings_added_probs)
    bitstrings_added_list_unique, bitstrings_added_list_unique_inverse = np.unique(bitstrings_added_list, axis=0, return_inverse=True)
    bitstrings_added_probs_unique = np.zeros(len(bitstrings_added_list_unique))
    for i in range(len(bitstrings_added_list_unique_inverse)):
        bitstrings_added_probs_unique[bitstrings_added_list_unique_inverse[i]] += bitstrings_added_probs[i]

    sampled_basis4 = [2 * bitstrings_added_list_unique[k][:n_qubits] + bitstrings_added_list_unique[k][n_qubits:] for k in range(len(bitstrings_added_list_unique))]

    not_commute_probs_sampled = np.zeros([len(bitstrings_added_list_unique), len(bitstrings_added_list_unique)])
    for q in range(len(bitstrings_added_list_unique)):
        not_commute_probs_sampled[q, :] = bitstrings_added_probs_unique[q] * bitstrings_added_probs_unique * (np.sum(pauli_commute_map[4 * sampled_basis4[q] + sampled_basis4], axis=1) % 2)

    Bell_magic_exact = np.sum(2 * not_commute_probs_sampled)
    return Bell_magic_exact

def SWAP_purity(bitstrings_sampled, sampled_states_probs):
    string_length = len(bitstrings_sampled[0])
    n_qubits = string_length // 2
    parity_list = np.array([np.sum((bitstrings_sampled[i, :n_qubits] + bitstrings_sampled[i, n_qubits:]) > 1) % 2 for i in range(len(bitstrings_sampled))], dtype=int)
    purity = 1 - 2 * np.sum(sampled_states_probs * parity_list)
    return purity

def bell_magic_sample(bitstrings_sampled, sampled_states_probs, n_samples=0, n_resample=1):
    rng = np.random.default_rng(2) # Fixed seed for consistency
    pauli_commute_map = get_pauli_commute_map()
    string_length = len(bitstrings_sampled[0])
    n_qubits = string_length // 2

    if n_samples == 0:
        raise NameError("Not implemented")

    counts = np.array(np.round(sampled_states_probs * n_samples), dtype=int)
    
    sample_list = np.zeros(n_samples, dtype=int)
    start = 0
    for i in range(len(bitstrings_sampled)):
        sample_list[start:start + counts[i]] = i
        start += counts[i]

    replace = True if n_samples < 4 else False
    
    rep_sample_list = []
    for rep in range(n_resample):
        rep_sample_list.append(rng.choice(sample_list, 4, replace=replace))

    rep_sample_list = np.array(rep_sample_list)

    bitstring_added1 = (bitstrings_sampled[rep_sample_list[:, 0]] + bitstrings_sampled[rep_sample_list[:, 1]]) % 2
    bitstring_added2 = (bitstrings_sampled[rep_sample_list[:, 2]] + bitstrings_sampled[rep_sample_list[:, 3]]) % 2

    sampled_basis4_1 = 2 * bitstring_added1[:, :n_qubits] + bitstring_added1[:, n_qubits:]
    sampled_basis4_2 = 2 * bitstring_added2[:, :n_qubits] + bitstring_added2[:, n_qubits:]

    sum_noncommute_return_list = np.mean(2 * (np.sum(pauli_commute_map[4 * sampled_basis4_1 + sampled_basis4_2], axis=1) % 2))
    Bell_magic_sampled = np.mean(sum_noncommute_return_list)

    return Bell_magic_sampled

def strip_measurements(circuit):
    n_qubits = circuit.num_qubits
    q = QuantumRegister(n_qubits)
    new_circuit = QuantumCircuit(q)

    for inst in circuit.data:
        op = inst.operation
        qargs = inst.qubits

        if isinstance(op, (Measure, Reset)):
            continue
        
        has_classical_condition = (hasattr(inst, "condition_bits") and inst.condition_bits) or \
                                  (hasattr(op, "condition") and op.condition is not None)
        
        if has_classical_condition:
            continue

        mapped_qubits = [q[circuit.qubits.index(qb)] for qb in qargs]
        new_circuit.append(op, mapped_qubits)

    return new_circuit

# FIXED: Added 'add_measurement' flag so Exact Mode doesn't collapse the statevector
def bell_magic_circuit_from_state(state_circuit, add_measurement=True):
    n = state_circuit.num_qubits
    q = QuantumRegister(2 * n, 'q')
    
    if add_measurement:
        c = ClassicalRegister(2 * n, 'c')
        qc = QuantumCircuit(q, c)
    else:
        qc = QuantumCircuit(q)

    qc.compose(state_circuit, qubits=range(n), inplace=True)
    qc.compose(state_circuit, qubits=range(n, 2 * n), inplace=True)

    for i in range(n):
        qc.cx(i, i + n)
        qc.h(i)

    if add_measurement:
        qc.measure(q, c)
        
    return qc


# ---- Main Computation Function (Called by Website) ----

def compute_bell_magic_from_circuit(circuit, depolarization_factor=0.0, n_samples=0):
    
    # Safety: Limit parameters
    depolarization_factor = max(0.0, min(depolarization_factor, 0.2))
    
    # 1. Prepare State
    state_circuit = strip_measurements(circuit)
    n_qubits = state_circuit.num_qubits

    # 2. Run Simulation
    if n_samples == 0:
        # EXACT MODE: Do not append measurements, use save_statevector()
        bell_circuit = bell_magic_circuit_from_state(state_circuit, add_measurement=False)
        backend = Aer.get_backend("aer_simulator_statevector")
        
        bell_circuit.save_statevector()
        compiled = transpile(bell_circuit, backend)
        result = backend.run(compiled).result()

        probs = np.abs(result.get_statevector()) ** 2
        bitstrings = np.array([
            numberToBase(i, 2, 2 * n_qubits)[::-1]
            for i in range(4 ** n_qubits)
        ])

        if depolarization_factor > 0:
            p_global = depolarization_factor * (2 - depolarization_factor)
            probs = ((1 - p_global) * probs + p_global / (4 ** n_qubits))

    else:
        # SAMPLING MODE: Append measurements and apply Qiskit NoiseModel
        bell_circuit = bell_magic_circuit_from_state(state_circuit, add_measurement=True)
        backend = Aer.get_backend("aer_simulator")
        compiled = transpile(bell_circuit, backend)

        if depolarization_factor > 0:
            # FIXED: Build and inject physical depolarizing channel
            noise_model = NoiseModel()
            error_1 = depolarizing_error(depolarization_factor, 1)
            error_2 = depolarizing_error(depolarization_factor, 2)
            
            # Apply to common 1-qubit and 2-qubit gates
            noise_model.add_all_qubit_quantum_error(error_1, ['u1', 'u2', 'u3', 'rx', 'ry', 'rz', 'h', 't', 's', 'x', 'y', 'z'])
            noise_model.add_all_qubit_quantum_error(error_2, ['cx', 'cz', 'swap', 'ccx'])
            
            result = backend.run(compiled, shots=n_samples, noise_model=noise_model).result()
        else:
            result = backend.run(compiled, shots=n_samples).result()

        counts = result.get_counts()
        bitstrings = []
        probs = []

        for bitstr, cnt in counts.items():
            bitstrings.append(np.array([int(b) for b in bitstr[::-1]]))
            probs.append(cnt / n_samples)

        bitstrings = np.array(bitstrings)
        probs = np.array(probs)

    # 3. Compute Magic
    n_resample = 10 * n_samples if n_samples > 0 else 0
    
    bell_magic = (
        bell_magic_exact(bitstrings, probs)
        if n_samples == 0
        else bell_magic_sample(bitstrings, probs, n_samples, n_resample)
    )

    purity = SWAP_purity(bitstrings, probs)
    additive_magic = -np.log2(1 - bell_magic) if bell_magic < 1 else 100 # avoid log(0)

    return {
        "bell_magic": float(bell_magic),
        "additive_bell_magic": float(additive_magic),
        "purity": float(purity),
        "n_qubits": int(n_qubits)
    }