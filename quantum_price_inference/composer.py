"""
Utilities for exporting Qiskit circuits to IBM Quantum Composer.

IBM Quantum Composer accepts OpenQASM 2.0 via a URL parameter:
    https://quantum.cloud.ibm.com/composer?code=<url-encoded-qasm>

No IBM account or credentials are required to open a circuit in the visual editor.
Saving or running on real hardware does require an IBM Quantum account.

Note: all qiskit imports are deferred inside functions so this module is safe to
import in environments where qiskit is not installed (import-safety rule).
"""

import asyncio
import logging
import urllib.parse
import webbrowser

log = logging.getLogger(__name__)

COMPOSER_BASE_URL = "https://quantum.cloud.ibm.com/composer"


def _composer_compatible_circuit(circuit):
    """Return a Composer-friendly version of the circuit.

    Composer is more reliable when fed plain OpenQASM 2 basis gates rather than
    nested library instructions with auto-generated custom gate definitions.

    Args:
        circuit: A Qiskit QuantumCircuit.

    Returns:
        A transpiled QuantumCircuit using only ``u`` and ``cx`` basis gates.
    """
    try:
        from qiskit import transpile  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("qiskit is required for circuit export. Install with: uv sync") from exc

    simplified = circuit.decompose(reps=10)
    return transpile(simplified, basis_gates=["u", "cx"], optimization_level=0)


def circuit_to_qasm2(circuit) -> str:
    """Return the OpenQASM 2.0 string for a Qiskit circuit.

    Args:
        circuit: A Qiskit QuantumCircuit.

    Returns:
        OpenQASM 2.0 source string.

    Raises:
        ImportError: if ``qiskit`` is not installed.
    """
    try:
        import qiskit.qasm2  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("qiskit is required for QASM export. Install with: uv sync") from exc

    return qiskit.qasm2.dumps(_composer_compatible_circuit(circuit))


def composer_url(circuit) -> str:
    """Return a Composer URL that pre-loads the given circuit.

    The URL encodes the full OpenQASM 2.0 program as a query parameter so
    no server-side upload is needed.

    Args:
        circuit: Any Qiskit QuantumCircuit.

    Returns:
        A URL string that can be opened in any browser.

    Raises:
        ImportError: if ``qiskit`` is not installed.
    """
    qasm = circuit_to_qasm2(circuit)
    encoded = urllib.parse.quote(qasm, safe="")
    return f"{COMPOSER_BASE_URL}?code={encoded}"


def open_in_composer(circuit) -> str:
    """Open the circuit in IBM Quantum Composer using the default browser.

    Args:
        circuit: Any Qiskit QuantumCircuit.

    Returns:
        The Composer URL that was opened.

    Raises:
        ImportError: if ``qiskit`` is not installed.
    """
    url = composer_url(circuit)
    log.info("Opening circuit in Composer: %s", url)
    webbrowser.open(url)
    return url


async def open_in_composer_async(circuit) -> str:
    """Async variant of :func:`open_in_composer`.

    Delegates the blocking ``webbrowser.open`` call to a thread so the event
    loop is not stalled.  Suitable for use inside FastAPI route handlers or
    async notebook cells.

    Args:
        circuit: Any Qiskit QuantumCircuit.

    Returns:
        The Composer URL that was opened.

    Raises:
        ImportError: if ``qiskit`` is not installed.
    """
    return await asyncio.to_thread(open_in_composer, circuit)
