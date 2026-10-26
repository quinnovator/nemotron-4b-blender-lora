"""Draw the README figures as light and dark SVGs from results/.

Usage: python tools/figures.py   (writes docs/images/{heldout,architecture}-{light,dark}.svg)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"

THEMES = {
    "light": {"ink": "#1f2328", "muted": "#59636e", "grid": "#d1d9e0", "panel": "#f6f8fa",
              "box": "#ffffff", "nemo": "#12936a", "trl": "#6250d6", "accent": "#bf3989"},
    "dark": {"ink": "#e6edf3", "muted": "#9198a1", "grid": "#3d444d", "panel": "#151b23",
             "box": "#0d1117", "nemo": "#1aa679", "trl": "#8a7af0", "accent": "#e275ad"},
}
FONT = "font-family=\"-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif\""


def _svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT}>\n'
            + body + "\n</svg>\n")


def _held_out():
    nemo = {0: json.loads((ROOT / "results/nemotron4b/baseline_eval_transfer.json").read_text())["pass_at_1"]}
    for s in range(100, 601, 100):
        nemo[s] = json.loads((ROOT / f"results/nemotron4b/evals/step{s:05d}_eval_transfer.json").read_text())["pass_at_1"]
    trl = {int(k): v for k, v in json.loads((ROOT / "results/trl_comparison.json").read_text())
           ["runs"]["trl"]["eval_transfer"].items()}
    return nemo, trl


def held_out_chart(t):
    nemo, trl = _held_out()
    w, h, l, r, top, bot = 760, 400, 64, 150, 96, 52
    x = lambda s: round(l + (w - l - r) * s / 600, 1)            # noqa: E731
    y = lambda v: round(top + (h - top - bot) * (1 - v), 1)      # noqa: E731
    g = [f'<text x="{l}" y="26" font-size="17" font-weight="600" fill="{t["ink"]}">'
         'Held-out scenes solved on the first try</text>',
         f'<text x="{l}" y="47" font-size="13" fill="{t["muted"]}">pass@1 on 200 "between" tasks, '
         'a relation never seen in training (8 samples each)</text>']
    for v in [0, 0.25, 0.5, 0.75, 1.0]:
        g.append(f'<line x1="{l}" x2="{w - r}" y1="{y(v)}" y2="{y(v)}" stroke="{t["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{l - 10}" y="{y(v) + 4}" font-size="12" fill="{t["muted"]}" text-anchor="end">{v:.0%}</text>')
    for s in range(0, 601, 100):
        g.append(f'<text x="{x(s)}" y="{h - bot + 20}" font-size="12" fill="{t["muted"]}" text-anchor="middle">{s}</text>')
    g.append(f'<text x="{(l + w - r) / 2}" y="{h - 10}" font-size="12" fill="{t["muted"]}" '
             'text-anchor="middle">training step (0 = base model)</text>')
    for data, color, dash, label in [(trl, t["trl"], "6 4", "TRL"), (nemo, t["nemo"], "", "NeMo RL")]:
        pts = " ".join(f"{x(s)},{y(v)}" for s, v in sorted(data.items()))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        g.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5"{d} '
                 'stroke-linejoin="round" stroke-linecap="round"/>')
        for s, v in sorted(data.items()):
            g.append(f'<circle cx="{x(s)}" cy="{y(v)}" r="4.5" fill="{color}" stroke="{t["box"]}" stroke-width="2">'
                     f'<title>{label}, step {s}: {v:.1%}</title></circle>')
        g.append(f'<text x="{x(600) + 12}" y="{y(data[600]) + 5}" font-size="14" font-weight="600" '
                 f'fill="{t["ink"]}">{label} {data[600]:.0%}</text>')
    g.append(f'<text x="{x(0) + 10}" y="{y(nemo[0]) + 20}" font-size="12" fill="{t["muted"]}">'
             f'base {nemo[0]:.0%}</text>')
    lx = l
    for i, (color, dash, label) in enumerate([(t["nemo"], "", "NeMo RL + NeMo Gym"), (t["trl"], "6 4", "TRL, same setup")]):
        yy = 74
        lx = l + i * 180
        d = f' stroke-dasharray="{dash}"' if dash else ""
        g.append(f'<line x1="{lx}" x2="{lx + 24}" y1="{yy - 4}" y2="{yy - 4}" stroke="{color}" stroke-width="2.5"{d}/>')
        g.append(f'<text x="{lx + 32}" y="{yy}" font-size="12" fill="{t["ink"]}">{label}</text>')
    return _svg(w, h, "\n".join(g))


def _box(x, y, w, h, t, title, sub=None, fill=None, stroke=None):
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill or t["box"]}" '
         f'stroke="{stroke or t["grid"]}" stroke-width="1.5"/>']
    ty = y + (h / 2 + 5 if sub is None else h / 2 - 4)
    s.append(f'<text x="{x + w / 2}" y="{ty}" font-size="14" font-weight="600" fill="{t["ink"]}" '
             f'text-anchor="middle">{title}</text>')
    if sub:
        s.append(f'<text x="{x + w / 2}" y="{ty + 19}" font-size="12" fill="{t["muted"]}" text-anchor="middle">{sub}</text>')
    return "\n".join(s)


def _arrow(x1, y1, x2, y2, t, label=None, lx=None, ly=None, anchor="middle"):
    s = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{t["muted"]}" stroke-width="1.6" '
         'marker-end="url(#head)"/>']
    if label:
        s.append(f'<text x="{lx if lx is not None else (x1 + x2) / 2}" y="{ly if ly is not None else (y1 + y2) / 2 - 7}" '
                 f'font-size="12" fill="{t["muted"]}" text-anchor="{anchor}">{label}</text>')
    return "\n".join(s)


def architecture(t):
    w, h = 960, 420
    g = [f'<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{t["muted"]}"/></marker></defs>']
    # The NeMo RL container.
    g.append(f'<rect x="16" y="16" width="440" height="388" rx="14" fill="{t["panel"]}" stroke="{t["grid"]}" stroke-width="1.5"/>')
    g.append(f'<text x="36" y="44" font-size="15" font-weight="600" fill="{t["ink"]}">NeMo RL container</text>')
    g.append(f'<text x="36" y="64" font-size="12" fill="{t["muted"]}">one RTX 4090 · no Docker socket</text>')
    g.append(_box(46, 86, 330, 62, t, "GRPO policy: Megatron + LoRA r32", "Nemotron 3 Nano 4B, frozen base in bf16"))
    g.append(_box(46, 196, 330, 62, t, "vLLM rollouts (colocated)", "4 prompts × 8 samples per step"))
    g.append(_box(46, 306, 330, 70, t, "NeMo Gym: blender_scene", "extract code → run → score the scene",
                  stroke=t["nemo"]))
    g.append(_arrow(211, 150, 211, 194, t, "LoRA weights", 221, 177, "start"))
    g.append(_arrow(211, 260, 211, 304, t, "32 scripts", 221, 287, "start"))
    g.append(f'<path d="M376,320 H416 V117 H380" fill="none" stroke="{t["muted"]}" stroke-width="1.6" '
             'marker-end="url(#head)"/>')
    g.append(f'<text x="424" y="222" font-size="12" fill="{t["muted"]}" '
             'transform="rotate(-90 424 222)" text-anchor="middle">rewards</text>')
    # Host side.
    g.append(f'<text x="520" y="44" font-size="15" font-weight="600" fill="{t["ink"]}">Host</text>')
    g.append(_box(500, 300, 190, 82, t, "Sandbox broker", "127.0.0.1:8765"))
    g.append(_arrow(378, 334, 498, 334, t, "bpy code", 470, 326))
    g.append(_arrow(498, 360, 378, 360, t, "scene", 470, 378))
    for i in range(3):
        yy = 86 + i * 14
        g.append(f'<rect x="{740 + i * 10}" y="{yy}" width="190" height="150" rx="10" fill="{t["box"]}" '
                 f'stroke="{t["accent"] if i == 2 else t["grid"]}" stroke-width="1.5"/>')
    g.append(f'<text x="855" y="146" font-size="14" font-weight="600" fill="{t["ink"]}" text-anchor="middle">Blender 5.2 sandbox</text>')
    g.append(f'<text x="855" y="165" font-size="12" fill="{t["muted"]}" text-anchor="middle">one container per script</text>')
    for i, line in enumerate(["no network · read-only", "2 GB · 1 CPU · 128 pids", "40 s limit · non-root"]):
        g.append(f'<text x="855" y="{198 + i * 18}" font-size="12" fill="{t["muted"]}" text-anchor="middle">{line}</text>')
    g.append(_arrow(692, 322, 790, 268, t))
    g.append(f'<text x="760" y="300" font-size="12" fill="{t["muted"]}">'
             '<tspan x="760" dy="0">Run the script, save the scene,</tspan>'
             '<tspan x="760" dy="17">then a second, clean Blender</tspan>'
             '<tspan x="760" dy="17">measures every mesh: the script</tspan>'
             '<tspan x="760" dy="17">can never write its own score.</tspan></text>')
    return _svg(w, h, "\n".join(g))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"heldout-{name}.svg").write_text(held_out_chart(t))
        (OUT / f"architecture-{name}.svg").write_text(architecture(t))
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))


if __name__ == "__main__":
    main()
