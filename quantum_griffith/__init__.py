"""Quantum Griffith: cost-aware reversible synthesis of learned Boolean networks.

Inspired by Griffith (https://github.com/tsukushi-gate/Griffith).
No upstream source code is copied. All circuits are exact X/CX/CCX
permutations with clean work qubits; no phase-relative substitutions.
"""
from .reversible import Circuit, Gate, ResourceCost, verify_oracle
from .synthesis import (anf_terms, synthesize, search_affine, search_joint_affine,
                        SynthesisResult, JointSynthesisResult)
from .logic_dag import LogicGate, LogicDAG, lower_logic_dag
from .griffith_adapter import (from_griffith_ir, load_griffith_ir,
                              compile_griffith_ir, UnsupportedGriffithIR)

__all__ = [
    "Circuit", "Gate", "ResourceCost", "verify_oracle",
    "anf_terms", "synthesize", "search_affine", "search_joint_affine",
    "SynthesisResult", "JointSynthesisResult",
    "LogicGate", "LogicDAG", "lower_logic_dag",
    "from_griffith_ir", "load_griffith_ir", "compile_griffith_ir",
    "UnsupportedGriffithIR",
]
