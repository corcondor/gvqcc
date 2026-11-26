"""Export planner instances into planner/inst/ (nb26an .txt format + .ten, plus .gs2 for 9-output ones)
and maintain planner/inst/manifest.json."""
import json, shutil, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
INST = HERE / "inst"
INST.mkdir(exist_ok=True)


def expected_planes(m, w, n):
    P = (2 ** w - 1) * (2 ** w - 2) // 6
    g = m * w - 2 * n
    return P * (2 ** m - 1) * 2.0 ** (-2 * g)


def load_manifest():
    p = INST / "manifest.json"
    return json.load(open(p)) if p.exists() else {"format": "nb26an inst: 'q w nfan k' then 'c col_0..col_{w-1}' "
            "(column = image of c(x)e_t in Q = out x low / R); .ten = 'q m w k n' + basis of R-perp over m*w bits",
            "instances": {}}


def save_manifest(m):
    m["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(m, open(INST / "manifest.json", "w"), indent=1)


def add(name, src_txt, bank, block, m, w, q, k, n, status, note="", src_ten=None, src_gs2=None, src_res=None):
    man = load_manifest()
    shutil.copyfile(src_txt, INST / f"{name}.txt")
    files = {"txt": f"{name}.txt"}
    for src, ext in ((src_ten, "ten"), (src_gs2, "gs2"), (src_res, "res")):
        if src and Path(src).exists():
            shutil.copyfile(src, INST / f"{name}.{ext}")
            files[ext] = f"{name}.{ext}"
    man["instances"][name] = dict(files=files, bank=bank, block=block, outputs=m, low_dim=w, q=q, k=k, products=n,
                                  expected_planes_random_W=round(expected_planes(m, w, n), 1), status=status, note=note)
    save_manifest(man)


def export_design(tag, status="solved by planner"):
    d = HERE / "designs" / tag
    des = json.load(open(d / "design.json")) if (d / "design.json").exists() else None
    for blk in (1, 2, 3):
        txt = d / f"{tag}_b{blk}.txt"
        if not txt.exists():
            continue
        md = json.load(open(d / f"{tag}_b{blk}.json"))
        k = md.get("k")
        res = d / (f"{tag}_b{blk}.res" if blk > 1 else f"{tag}_b1_s1.res")
        add(f"L{des['k'] if des else '?'}_b{blk}_{tag}", txt, des["k"] if des else None, blk, md["m"], md["w"], md["q"], k, md["n"], status,
            src_ten=d / f"{tag}_b{blk}.ten", src_gs2=d / f"{tag}_b{blk}.gs2", src_res=res)


if __name__ == "__main__":
    for tag in sys.argv[1:]:
        export_design(tag)
        print("exported", tag)
