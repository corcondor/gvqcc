"""Native KickMix KMX parser/roundtrip of a REAL rank2 cross-group C46 circuit.
Native parsing is not equivalent to official KickMix simulation/FeMoCo PASS.
"""
from __future__ import annotations
import unittest,sys,io,hashlib,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for local,hosted in [('gvqcc_multiform','.'),('gvqcc_multiform_v3','multiangle_v3'),('gvqcc_multiform_v4','multiangle_v4'),('gvqcc_multiform_v5','multiangle_v5')]:
    sys.path.insert(0,str(ROOT/(local if (ROOT/local).exists() else hosted)))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pinned_c46_words import words
from global20_rank_hmr import compile_rank_r
from independent_interleaved import independent_verify

class NativeRank2Test(unittest.TestCase):
    def test_rank2_interleaved_cx_conditional_cz_native_roundtrip(self):
        try:import kickmix as km
        except ImportError:self.skipTest('kickmix not available on CPython 3.13')
        tab=words()
        c,st=compile_rank_r(tab,13,support=8,initial_basis='grouped',basis_exchange=True)
        self.assertEqual(st['CCX'],579)
        self.assertGreater(st['selector_rank_hist'].get(2,0),0)
        kmx=('\n'.join(c.kmx_lines())+'\n').encode()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'real.kmx';path.write_bytes(kmx)
            prove=independent_verify(path,tab,13)
            self.assertEqual(prove['CCX'],st['CCX'])
            self.assertGreater(prove['multi_CZ_events'],0)
        source=km.Circuit.from_file(io.BytesIO(kmx),format='kmx')
        self.assertEqual(source.num_qubits,127)
        binary=io.BytesIO();source.to_file(binary,format='kmb');binary.seek(0)
        actual=km.Circuit.from_file(binary,format='kmb')
        self.assertEqual(actual.num_qubits,127)
        print('NATIVE_KMX_RANK2_PASS slot13 Q127 CCX579',hashlib.sha256(kmx).hexdigest(),flush=True)

if __name__=='__main__':unittest.main(verbosity=2)
