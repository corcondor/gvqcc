"""Offline synthetic checks: no Kaggle downloads or competition submissions."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib
from research_20261116 import frontier_hybrid_builder as pkg

def sha(data):return hashlib.sha256(data).hexdigest()

class TestHybridBuilder(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder);public=root/'public';public.mkdir()
        inv=b'synthetic-only-invsqrt';dqi=b'synthetic-only-dqi'
        pins={'dqi.kmb':(sha(b'public-dqi'),10)}
        for name in ['dfthcsos/submission.npz']+[f'dfthcsos/angle_k_{i}.kmb' for i in range(15)]:
            data=name.encode()
            dest=public/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            pins[name]=(sha(data),len(data))
        source={'cells':[{'cell_type':'code','source':'PINNED = '+repr(pins)},
                         {'cell_type':'code','source':'INV = '+repr(base64.b64encode(zlib.compress(inv)).decode())}]}
        raw=json.dumps({'blob':{'source':json.dumps(source)}}).encode()
        mine=root/'own.zip'
        with zipfile.ZipFile(mine,'w') as z:z.writestr('dqi.kmb',dqi)
        return raw,public,mine,inv,dqi

    def test_literal_extraction(self):
        self.assertEqual(pkg.notebook_literal('VALUE = [1, 2]','VALUE'),[1,2])
        with self.assertRaises(ValueError):pkg.notebook_literal('VALUE = secret()','VALUE')

    def test_full_18_member_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            raw,public,mine,inv,dqi=self.fixture(td)
            out=Path(td)/'out.zip'
            with (patch.object(pkg,'INV_SHA',sha(inv)),
                  patch.object(pkg,'OWN_DQI_SHA',sha(dqi)),
                  patch.object(pkg,'OWN_ZIP_SHA',pkg.sha_file(mine))):
                result=pkg.build(raw,public,None,mine,out)
            self.assertEqual(result['member_count'],18)
            self.assertFalse(result['kaggle_submitted'])
            with zipfile.ZipFile(out) as z:
                self.assertEqual(z.read('invsqrt.kmb'),inv)
                self.assertEqual(z.read('dqi.kmb'),dqi)
            self.assertTrue(out.with_suffix('.json').exists())

    def test_chemistry_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            raw,public,mine,inv,dqi=self.fixture(td)
            (public/'dfthcsos/angle_k_0.kmb').write_bytes(b'wrong')
            out=Path(td)/'out.zip'
            with patch.object(pkg,'INV_SHA',sha(inv)):
                with self.assertRaises(ValueError):pkg.build(raw,public,None,mine,out)
            self.assertFalse(out.exists())

    def test_mismatched_dqi_rejected_and_no_archive(self):
        with tempfile.TemporaryDirectory() as td:
            raw,public,mine,inv,dqi=self.fixture(td)
            out=Path(td)/'out.zip'
            with (patch.object(pkg,'INV_SHA',sha(inv)),
                  patch.object(pkg,'OWN_DQI_SHA','0'*64),
                  patch.object(pkg,'OWN_ZIP_SHA',pkg.sha_file(mine))):
                with self.assertRaises(ValueError):pkg.build(raw,public,None,mine,out)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
