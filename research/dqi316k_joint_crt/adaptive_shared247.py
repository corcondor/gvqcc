"""Reuse the shared multipoint schedule in both adaptive #253 pad maps."""
import invariant247 as Base
import grouped_guard247 as G
import shared_multipoint247 as S
import adaptive247 as A
G.unit_power=S.unit_power
Base.Guard.reciprocal=G.reciprocal
if __name__=='__main__':A.main()
