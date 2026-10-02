"""Render stored bilingual examples without replacing their evidence timestamps."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/medical-journal-selector/scripts"))
from selector import validate, render

out = ROOT / "docs/examples"
for name in ("fictional", "live"):
    for language in ("en", "zh-CN"):
        evidence_name=name+("-evidence.en.json" if language=="en" else "-evidence.json")
        b=json.loads((out/evidence_name).read_text(encoding="utf-8"))
        assert not validate(b), validate(b)
        if language=="en":
            target=name+"-report.md"
            links=f"[简体中文]({name}-report.zh-CN.md) · [All examples](README.md) · [Evidence]({evidence_name})"
            note=("Fictional journals and figures for demonstration only." if name=="fictional" else
                  "English translation of the original verification snapshot. Numbers, statuses and acquisition times were preserved; this formatting update did not perform new verification.")
        else:
            target=name+"-report.zh-CN.md"
            links=f"[English]({name}-report.md) · [全部示例](README.zh-CN.md) · [结构化证据]({evidence_name})"
            note=("虚构期刊和数字，仅用于展示格式。" if name=="fictional" else
                  "沿用原核验快照展示报告格式，数字、状态和抓取时间均未修改；本次排版更新未重新核验动态信息。")
        heading,body=render(b,language).split("\n",1)
        (out/target).write_text(heading+"\n\n"+links+"\n\n> "+note+"\n"+body,encoding="utf-8",newline="\n")
print("English and Chinese examples rendered; no new journal verification claimed.")
