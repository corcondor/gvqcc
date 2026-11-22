"""One objective and acceptance gate for physical + hard-XAG candidates.

A candidate with a better numerical lambda, fewer ANF terms, or an unverified
KMX is never called an improved competition score. This is the missing
interface between physical training, discrete gauge proposals and compilation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import inf, isfinite, log
from typing import Callable


@dataclass(frozen=True)
class Physical:
    error_1: float
    error_2: float
    Lambda: float
    E_gap: float
    lambda_eff: float

    def valid(self) -> bool:
        return (all(isfinite(v) for v in asdict(self).values())
            and self.error_1 <= 0.020 and self.error_2 <= 0.020
            and self.Lambda > 49.0 and self.E_gap > 3.914898
            and self.lambda_eff > 0.0)


@dataclass(frozen=True)
class Hardware:
    toffoli_total: float
    qubits_total: int
    all_oracle_checks_passed: bool
    native_verifier_passed: bool

    def valid(self) -> bool:
        return self.all_oracle_checks_passed and self.native_verifier_passed and self.toffoli_total>0 and self.qubits_total>0


@dataclass(frozen=True)
class JointCandidate:
    name: str
    physics: Physical
    hardware: Hardware | None
    word_sha256: str
    compiler_sha256: str | None = None

    def combined_log_cost(self) -> float:
        """Only emit an actual score-comparable cost for a fully verified candidate."""
        if not self.physics.valid() or self.hardware is None or not self.hardware.valid():
            return inf
        return log(self.physics.lambda_eff)+log(self.hardware.toffoli_total)+log(self.hardware.qubits_total)


def dominance(a: JointCandidate,b: JointCandidate)->bool:
    """Only verified real candidates participate in the score Pareto front."""
    ca=a.combined_log_cost();cb=b.combined_log_cost()
    return ca < inf and cb < inf and ca < cb


def candidate_record(candidate: JointCandidate) -> dict:
    obj=asdict(candidate)
    cost=candidate.combined_log_cost()
    obj['score_comparable_cost']=None if cost==inf else cost
    obj['status']='READY_FOR_OFFICIAL_SCORE' if cost<inf else 'RESEARCH_ONLY_NOT_SCORABLE'
    return obj
