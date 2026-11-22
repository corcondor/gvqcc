"""Differentiable affine-XOR/AND synthesis with exact hard-circuit validation.

This is an original Griffith-inspired research adapter, not part of Griffith.
A *soft* neural prediction is never treated as a valid circuit; only the hard
XAG extracted from weights and checked on all care inputs is an accepted model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .xag import Affine, AndProduct, XAG, synthesize_shared_one_and


def train_xag(targets: Sequence[int], *, num_inputs: int, products: int = 1,
              trials: int = 8, steps: int = 350, lr: float = 0.08,
              weight_cost: float = 0.01, seed: int = 20261122,
              exact_warm_start: bool = True) -> tuple[XAG | None, dict]:
    """Learn gate fan-in and XOR readout together; return only exact hard result.

    `products` is a hard maximum, not a claimed multiplicative complexity.
    A full n-input truth-table is required; no sample-only fidelity claim.
    Exact one-AND construction is used as a warm start if available, and
    learned variants are still validated independently before acceptance.
    """
    try:
        import torch
        import torch.nn as nn
    except ImportError as e:
        raise RuntimeError('Install optional PyTorch for the learned search') from e

    if not 1 <= num_inputs <= 8 or products < 0:
        raise ValueError('intended for small cut windows (1..8 input bits)')
    count = 1 << num_inputs
    if any(t < 0 or (t >> count) for t in targets):
        raise ValueError('expected exact packed truth tables for full input domain')
    x = torch.tensor([[(a >> i) & 1 for i in range(num_inputs)] for a in range(count)], dtype=torch.float32)
    y = torch.tensor([[(int(t) >> a) & 1 for t in targets] for a in range(count)], dtype=torch.float32)

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.fanins = nn.Parameter(torch.randn(products, 2, num_inputs + products + 1)*0.5)
            self.readout = nn.Parameter(torch.randn(len(targets), num_inputs + products + 1)*0.5)
            self.register_buffer('allowed', torch.tensor([[[1.0 if j <= num_inputs+i else 0.0
                for j in range(num_inputs+products+1)] for _ in range(2)] for i in range(products)]))

        @staticmethod
        def soft_xor(signals, logits):
            # Multilinear extension of XOR. Exact for bits and hard 0/1 masks.
            p = torch.sigmoid(logits)
            return (1.0 - torch.prod(1.0 - 2.0*signals*p, dim=-1))*0.5

        def forward(self, batch):
            signals = [torch.ones(batch.shape[0],dtype=batch.dtype,device=batch.device)]
            signals += [batch[:,i] for i in range(num_inputs)]
            for i in range(products):
                s = torch.stack(signals,dim=1)
                f0 = self.soft_xor(s, self.fanins[i,0,:num_inputs+i+1])
                f1 = self.soft_xor(s, self.fanins[i,1,:num_inputs+i+1])
                signals.append(f0*f1)
            a = torch.stack(signals,dim=1)
            preds = [self.soft_xor(a,self.readout[o]) for o in range(len(targets))]
            return torch.stack(preds,dim=-1)

        def hard(self):
            fs, outs = [], []
            def decode_row(row, max_signal):
                bits = (row[:max_signal+1] > 0).tolist()
                return Affine(sum(1 << (j-1) for j in range(1,len(bits)) if bits[j]), int(bits[0]))
            for i in range(products):
                fs.append(AndProduct(decode_row(self.fanins[i,0],num_inputs+i),
                                     decode_row(self.fanins[i,1],num_inputs+i)))
            for o in range(len(targets)):
                outs.append(decode_row(self.readout[o],num_inputs+products))
            return XAG(num_inputs, tuple(fs), tuple(outs))

    torch.manual_seed(seed)
    history = []
    best: XAG | None = None
    warm = synthesize_shared_one_and(targets, num_inputs) if products == 1 and exact_warm_start and num_inputs <= 6 else None
    # Baseline exact witness is retained even if a learned proposal regresses.
    best_source = 'exact_algebraic_seed' if warm is not None else None
    if warm is not None:
        best = warm
    for t in range(trials):
        torch.manual_seed(seed+t)
        model=Net()
        if t==0 and warm is not None and len(warm.products)==1:
            with torch.no_grad():
                model.fanins.fill_(-5.0)
                for b,g in enumerate((warm.products[0].left,warm.products[0].right)):
                    if g.constant:model.fanins[0,b,0]=5.0
                    for i in range(num_inputs):
                        if (g.mask >> i)&1:model.fanins[0,b,i+1]=5.0
                model.readout.fill_(-5.0)
                for o,g in enumerate(warm.outputs):
                    if g.constant:model.readout[o,0]=5.0
                    for i in range(num_inputs+products):
                        if (g.mask >> i)&1:model.readout[o,i+1]=5.0
        opt=torch.optim.Adam(model.parameters(),lr=lr)
        losses=[]
        for step in range(steps):
            pred=model(x)
            err=((pred-y)**2).mean()
            probs=torch.sigmoid(model.readout[:,num_inputs+1:])
            # Regularize use of nonlinear features; CNOT/XOR are free here.
            soft_cost=(1-torch.prod(1-probs,dim=0)).sum() if products else err.new_tensor(0)
            # Encourage discrete gates to close the soft/hard gap.
            all_w=torch.cat((model.fanins.reshape(-1),model.readout.reshape(-1)))
            p=torch.sigmoid(all_w)
            sharpness=(p*(1-p)).mean()
            loss=err+weight_cost*soft_cost+0.03*sharpness
            opt.zero_grad();loss.backward();opt.step()
            if step % 50 == 0 or step==steps-1:losses.append([step,float(err.detach()),float(soft_cost.detach())])
        candidate=model.hard()
        bits=candidate.truth_tables()
        wrong=sum(((a^b).bit_count()) for a,b in zip(bits,targets))
        history.append({'trial':t,'hard_bit_errors':wrong,'loss_trace':losses})
        if wrong==0 and (best is None or len(candidate.products)<len(best.products)):
            best=candidate
            best_source='learned_hard_rounded'
            if not len(best.products):break
    if best is not None:best.assert_exact(targets)
    return best,{'status':'EXACT' if best else 'NO_EXACT_HARD_CIRCUIT',
                 'source':'Griffith-inspired original affine-XAG learner',
                 'input_bits':num_inputs,'outputs':len(targets),'hard_witness_products':len(best.products) if best else None,
                 'witness_origin':best_source,
                 'trials':history,'not_a_competition_score':True}
