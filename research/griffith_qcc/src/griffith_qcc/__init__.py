"""Griffith-inspired, exact-verified research tools for GVQCC.

This package is original adapter code, not an official Griffith fork. The
upstream Griffith framework is Apache-2.0. All new learned proposals require
an independent exact verifier before they can be used in KickMix.
"""
from .xag import Affine, AndProduct, XAG, affine_functions, synthesize_shared_one_and
from .chemistry import audit, load_words, helper_report, bank_delta_tables
from .joint import Physical, Hardware, JointCandidate, candidate_record
__all__ = ['Affine','AndProduct','XAG','affine_functions','synthesize_shared_one_and',
           'audit','load_words','helper_report','bank_delta_tables',
           'Physical','Hardware','JointCandidate','candidate_record']
