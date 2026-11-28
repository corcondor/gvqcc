"""Source-level shared coefficient alias and shifted-scale integration on the pinned #249 generator."""
from pathlib import Path
p=Path("build_fusion.py")
s=p.read_text()
old="from fft_fusion import fft_scan"
new="""# Cross-word alias: fold one high coefficient into the low output and repay from q0.
# Shifted scaling: transport shared scalar through the reverse aligned levels.
os.environ.update(ZN_ALIAS_LEVELS=','.join(map(str,range(3,17))),ZN_ALIAS_B='3,4,5',DQI_INT_SS_MAXM='11')
for x in ('dqi_zn_alias','dqi_int_shiftscale'):
    install(x)
from fft_fusion import fft_scan"""
assert s.count(old)==1
s=s.replace(old,new).replace("Path('full_fft.kmb')","Path('joint_alias.kmb')")
Path("build_alias.py").write_text(s)
