"""
Utilities for exporting Qiskit circuits to IBM Quantum Composer.

IBM Quantum Composer accepts OpenQASM 2.0 via a URL parameter:
    https://quantum.cloud.ibm.com/composer?code=<url-encoded-qasm>

No IBM account or credentials are required to open a circuit in the visual editor.
Saving or running on real hardware does require an IBM Quantum account.
"""

import urllib.parse
import webbrowser

import qiskit.qasm2
from qiskit import QuantumCircuit

COMPOSER_BASE_URL = "https://quantum.cloud.ibm.com/composer"


def circuit_to_qasm2(circuit: QuantumCircuit) -> str:
    """Return the OpenQASM 2.0 string for a Qiskit circuit."""
    return qiskit.qasm2.dumps(circuit)


def composer_url(circuit: QuantumCircuit) -> str:
    """Return a Composer URL that pre-loads the given circuit.

    The URL encodes the full OpenQASM 2.0 program as a query parameter so
    no server-side upload is needed.

    Args:
        circuit: Any Qiskit QuantumCircuit.

    Returns:
        A URL string that can be opened in any browser.
    """
    qasm = circuit_to_qasm2(circuit)
    encoded = urllib.parse.quote(qasm, safe="")
    return f"{COMPOSER_BASE_URL}?code={encoded}"


def open_in_composer(circuit: QuantumCircuit) -> str:
    """Open the circuit in IBM Quantum Composer using the default browser.

    Args:
        circuit: Any Qiskit QuantumCircuit.

    Returns:
        The Composer URL that was opened.
    """
    url = composer_url(circuit)
    webbrowser.open(url)
    return url
