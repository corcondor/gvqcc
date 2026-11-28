from pathlib import Path
s=Path("build_alias.py").read_text()
old="from fft_fusion import fft_scan"
assert s.count(old)==1
# Set the upstream switches before importing its module.
s=s.replace("import loader_cache;loader_cache.install()","os.environ.update(DQI_PUB_PFD_P0='1',DQI_INT_PFDT='1',DQI_INT_PFDC='1')\nimport loader_cache;loader_cache.install()")
s=s.replace("Path('joint_alias.kmb')","Path('joint_grouped.kmb')")
# Use the existing #259 builder and no replacement decoder.
Path('build_grouped.py').write_text(s)
