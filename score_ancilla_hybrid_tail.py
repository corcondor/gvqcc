#!/usr/bin/env python3
"""Hybrid rolling-tail lifetime schedule with exact prefix phase ledger.

Forward flags except the last are HMR'd immediately after selecting (u,v).
Their phase is paid at existing reverse zero(v) queries. The final flag
survives, retaining the original seed seam. Reverse flags are unchanged.
This changes no Toffoli counts. It removes the rolling flag from all but
the last forward arithmetic stage, but does NOT establish global Q888.
"""
from pathlib import Path
import sys

SOURCE=Path('/workspace/scratch/7f542e06b7cf/official_sources/Syed_v12/source/dqi_source/src/controller_work')
sys.path.insert(0,str(SOURCE/'after_c5/extractor_width'))
import ew_paths  # noqa: F401,E402
import kickmix as km  # noqa: E402
import rolling_tail_early as Early  # noqa: E402
from score_ancilla_prefix_phase import PrefixPhaseLedger  # noqa: E402

zero_xor=Early.zero_xor
erase_zero_flag=Early.erase_zero_flag
gauge_prefix=Early.gauge_prefix
gauge_return=Early.gauge_return
validate_head_profile=Early.validate_head_profile
SlotToken=Early.SlotToken


class RollingTail(Early.RollingTail):
    def __init__(self,builder,first_index=18,stop_index=35):
        super().__init__(builder,first_index,stop_index)
        self.prefix_phases=PrefixPhaseLedger(builder,stop_index-first_index)
        self.measured_forward_indices=[]

    def begin_slot(self,numerator,denominator,index):
        assert self.pending is None and index==self.forward_next
        assert self.first_index<=index<self.stop_index
        assert len(numerator)==len(denominator)==24
        first=index==self.first_index
        current=self.current if first else self.builder.alloc_qubits(1)[0]
        assert current is not None and current not in numerator and current not in denominator
        zero_xor(self.builder,numerator,current)
        self.builder.cswap(current,numerator,denominator)
        if index+1<self.stop_index:
            mask=self.builder.alloc_bits(1)
            self.builder.hmr(km.array([current]),mask)
            self.prefix_phases.add_mask(index-self.first_index,mask)
            self.builder.free(km.array([current]))
            self.measured_forward_indices.append(index)
            self.current=None
        else:
            self.current=current
        token=SlotToken(index,self.current,first)
        self.pending=token
        return token

    def release_spare(self):
        super().release_spare()
        assert self.current is not None
        assert self.measured_forward_indices==list(range(self.first_index,self.stop_index-1))

    def resume_return(self):
        super().resume_return()
        self.prefix_phases.begin_reverse()

    def finish_return(self,numerator,denominator,token):
        assert token==self.pending and token.current is not None
        assert len(numerator)==len(denominator)==24
        previous=None
        if not token.first_boundary:
            previous=self.builder.alloc_qubits(1)[0]
            zero_xor(self.builder,denominator,previous)
            self.prefix_phases.pay_head(token.index-self.first_index,previous)
            self.builder.cx(token.current,previous)
        else:
            # f_(first-1)=0, so h_first=f_first. The existing current flag
            # is already this predicate; no first-head zero query is added.
            self.prefix_phases.pay_head(0,token.current)
        self.builder.cswap(token.current,numerator,denominator)
        erase_zero_flag(self.builder,numerator,token.current)
        self.builder.free(km.array([token.current]))
        self.current=previous
        self.pending=None
        self.return_next-=1

    def close(self):
        super().close()
        self.prefix_phases.close()

