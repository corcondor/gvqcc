#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Portable entry point for the bundled CCCZ and invsqrt research checks."""
import argparse
from pathlib import Path
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('task',choices=['cccz','invsqrt'])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--official-root',type=Path)
    a=p.parse_args()
    if a.output.exists():
        p.error('choose a new output path; archived receipts are immutable')
    if a.task=='cccz':
        import score7_cccz_exact as module
        sys.argv=['score7_cccz_exact.py','--output',str(a.output)]
    else:
        import score7_invsqrt_phase_blocks as module
        root=a.official_root or Path(__file__).resolve().parents[1]/'official_sources'
        module.VERIFIER=root/'Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py'
        if not module.VERIFIER.is_file():p.error('official-root must contain Inzainos/verifiers')
        sys.argv=['score7_invsqrt_phase_blocks.py','--out',str(a.output)]
    module.main()

if __name__=='__main__':main()
