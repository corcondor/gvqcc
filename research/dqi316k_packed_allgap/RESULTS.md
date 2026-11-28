# Packed all-gap Sylvester follow-up (research only)

Continues #245, #248, #265 and #267. Local KickMix 1.0.0 tests; Vercel quota returned HTTP 402. The native source and binary are supplied in the research conversation's downloadable archive; they have not been committed here. This PR contains the algebra/width/branch proof source and its CI.

| Scope | Q | Static paid | Tested cases | Errors |
|---|---:|---:|---:|---:|
| Coprime degree-17 packed solver, forward | 899 | 377072 | 68 | 0 |
| Same inverse | 899 | 377072 | 68 | 0 |
| Same roundtrip | 899 | 754144 | 68 | 0 |
| Repeated-padding-capable solver, forward | 900 | 380550 | 68 | 0 |
| Same inverse | 900 | 380550 | 68 | 0 |
| Same roundtrip | 900 | 761100 | 68 | 0 |
| D,N-input phase oracle, ungrouped | 900 | 874965 | 216 | 0 |
| D,N-input phase oracle, grouped middle products | 900 | 788573 | 216 | 0 |

The last oracle uses 18690532 operations; mixed-mask mean paid 758543; SHA256 b93309761a57db2d212904cc6433356fbda75113b7d0a483986150d718d08ca1. This is NOT a complete raw-syndrome DQI circuit and NOT an improvement over 316K. Uncomputed prefix and suffix integration remain unverified. No official score, submission, or merge.

Math: B=qA+r, p=hA+t and t=rv+Ak imply A(h+qv+k)+Bv=p in characteristic two. Fixed cyclic alignment uses a+i-j=n+i-(n-a+j). Nonzero frame and visited degree flags permit a zero-remainder terminal branch on the admitted RHS domain. The coefficient packing uses 865+16+1+18=900 qubits. For D=A^2+XB^2 and N=P^2+XQ^2 solve Au=P and At=Q modulo B. Then B^2 V=N+D(u^2+Xt^2), with V=(Z+Xt)^2+X(W+u)^2 and Z=(P+Au)/B,W=(Q+At)/B. Repeated nonphysical factors are handled if the right-hand sides are divisible by gcd(A,B). The grouped contraction replaces a k by m block of products by k+m-1 evaluation/interpolation products; exact tensor coefficients are checked by the local generator.

Lean scope: abstract characteristic-two lift identity, packed address/word/width arithmetic and conditional HMR parity. These do not prove the native circuit, field inverse implementation, or whole raw decoder. CI status must be checked separately.
