#!/usr/bin/env python3
"""Validate declared evidence, filter candidates and render an auditable report.

Standard library only. This is NOT a fact checker, manuscript reviewer or web
scraper. The host must read and verify the cited sources before marking a fact
verified. No acceptance probability or opaque fit score is computed here.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

MISSING = "未核到"
FACTS = ("identity", "scope", "article_type", "method_policy", "indexing",
         "jcr", "jif", "oa", "fees", "warnings")
ENDPOINTS = ("first_decision", "acceptance", "online", "indexing")
ROUTES = ("高分区优先", "时间优先", "适配优先")
FIT = {"strong": 0, "moderate": 1, "weak": 2}


def instant(text):
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("timestamp needs a timezone")
    return value


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def issn_ok(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{3}[\dX]", value):
        return False
    digits = value.replace("-", "")
    return (sum(int(digits[i]) * (8-i) for i in range(7)) +
            (10 if digits[-1] == "X" else int(digits[-1]))) % 11 == 0


def known(fact):
    return isinstance(fact, dict) and fact.get("status") == "verified"


def validate(bundle):
    """Return structural/evidence-contract errors, not a source-truth verdict."""
    errors = []
    if not isinstance(bundle, dict):
        return ["root must be an object"]
    if bundle.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    run = bundle.get("run", {})
    if not isinstance(run, dict):
        return ["run must be an object"]
    try:
        start, end = instant(run["started_at"]), instant(run["completed_at"])
        if end < start:
            raise ValueError("completion precedes start")
        if end > datetime.now(end.tzinfo):
            raise ValueError("completion is in the future")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"invalid run timestamps: {exc}")
        start = end = None
    if run.get("mode") not in ("live", "offline_fixture"):
        errors.append("run.mode must be live or offline_fixture")
    if type(run.get("web_available")) is not bool:
        errors.append("run.web_available must be boolean")
    profile = bundle.get("profile", {})
    if not isinstance(profile, dict):
        return errors + ["profile must be an object"]
    for key in ("summary", "article_types", "methods", "validation", "queries", "limitations"):
        if key not in profile:
            errors.append(f"profile.{key} missing")
    constraints = bundle.get("constraints", {})
    supported = {"jcr_quartiles", "jcr_category", "jcr_year", "scie_only", "oa_required",
                 "max_fee", "exclude_issns", "exclude_warnings", "warning_lists", "time_endpoint"}
    if not isinstance(constraints, dict):
        return errors + ["constraints must be an object"]
    for key in set(constraints) - supported:
        errors.append(f"unsupported hard constraint {key}; do not silently ignore it")
    if constraints.get("jcr_quartiles") and not constraints.get("jcr_category"):
        errors.append("hard JCR quartiles require an explicitly relevant category")
    if constraints.get("jcr_year") and not constraints.get("jcr_quartiles"):
        errors.append("jcr_year hard constraint requires jcr_quartiles")
    for key in ("scie_only", "oa_required", "exclude_warnings"):
        if key in constraints and type(constraints[key]) is not bool:
            errors.append(f"{key} must be boolean")
    if any(q not in ("Q1", "Q2", "Q3", "Q4") for q in constraints.get("jcr_quartiles", [])):
        errors.append("invalid JCR quartile constraint")
    if constraints.get("time_endpoint", "acceptance") not in ENDPOINTS:
        errors.append("invalid time endpoint")
    if constraints.get("exclude_warnings") and not constraints.get("warning_lists"):
        errors.append("warning exclusion needs named warning_lists")
    if "max_fee" in constraints and (not isinstance(constraints["max_fee"], dict) or
            not number(constraints["max_fee"].get("amount")) or not constraints["max_fee"].get("currency")):
        errors.append("max_fee needs nonnegative amount and currency")
    journals = bundle.get("journals")
    if not isinstance(journals, list):
        return errors + ["journals must be a list"]
    ids, identities = set(), set()

    def check_fact(fact, loc, paper=False):
        if not isinstance(fact, dict):
            errors.append(f"{loc}: fact must be an object")
            return
        if fact.get("status") not in ("verified", "unverified"):
            errors.append(f"{loc}: status must be verified/unverified")
        if not known(fact):
            if fact.get("value") is not None:
                errors.append(f"{loc}: unverified value must be null, not a guess")
            if not fact.get("reason"):
                errors.append(f"{loc}: missing failure reason")
        else:
            if not run.get("web_available"):
                errors.append(f"{loc}: cannot mark a fact verified without web")
            if fact.get("value") is None:
                errors.append(f"{loc}: verified fact has no value")
            if not fact.get("evidence"):
                errors.append(f"{loc}: verified fact needs evidence")
        evidence = fact.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{loc}: evidence must be a list")
            return
        for ev in evidence:
            if not isinstance(ev, dict):
                errors.append(f"{loc}: evidence entry must be an object")
                continue
            parsed = urlparse(ev.get("url", ""))
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(f"{loc}: invalid evidence URL")
            if known(fact) and ev.get("source_type") not in (("official", "bibliographic") if paper else ("official",)):
                errors.append(f"{loc}: verified fact requires authoritative evidence")
            if not ev.get("support"):
                errors.append(f"{loc}: missing supporting text/location")
            try:
                checked = instant(ev["checked_at"])
                if start and not start <= checked <= end:
                    errors.append(f"{loc}: evidence timestamp outside this run")
            except (ValueError, KeyError, TypeError):
                errors.append(f"{loc}: invalid checked_at")

    for journal in journals:
        if not isinstance(journal, dict):
            errors.append("journal must be an object")
            continue
        jid = journal.get("id", "")
        if not jid or jid in ids:
            errors.append(f"duplicate/missing journal id: {jid}")
        ids.add(jid)
        if not journal.get("title"):
            errors.append(f"{jid}: title missing")
        facts = journal.get("facts", {})
        if not isinstance(facts, dict) or not isinstance(journal.get("timelines"), dict):
            errors.append(f"{jid}: facts and timelines must be objects")
            continue
        for field in FACTS:
            check_fact(facts.get(field), f"{jid}.{field}")
        timing = journal.get("timelines", {})
        for endpoint in ENDPOINTS:
            fact = timing.get(endpoint)
            check_fact(fact, f"{jid}.timelines.{endpoint}")
            if known(fact):
                v = fact.get("value", {})
                if not isinstance(v, dict) or not number(v.get("days")) or not all(v.get(k) for k in
                        ("statistic", "start_event", "cohort", "period")):
                    errors.append(f"{jid}.{endpoint}: days/statistic/start_event/cohort/period required")
                elif type(v.get("ranking_usable")) is not bool:
                    errors.append(f"{jid}.{endpoint}: ranking_usable boolean required after checking current applicability")
                elif v["ranking_usable"] and any(v[k] in ("未核到", "unknown", "not reported") for k in ("statistic", "start_event", "cohort", "period")):
                    errors.append(f"{jid}.{endpoint}: unresolved timing definition cannot be ranked")
        if known(facts.get("identity")):
            value = facts["identity"]["value"]
            if not isinstance(value, dict) or not value.get("issns") or not all(issn_ok(i) for i in value.get("issns", [])):
                errors.append(f"{jid}: identity needs valid ISSNs")
            else:
                for issn in value["issns"]:
                    if issn in identities:
                        errors.append(f"{jid}: duplicated ISSN {issn}")
                    identities.add(issn)
        for field in ("article_type", "method_policy"):
            if known(facts.get(field)):
                v = facts[field]["value"]
                if not isinstance(v, dict) or type(v.get("allowed")) is not bool or not v.get("notes"):
                    errors.append(f"{jid}.{field}: allowed boolean and notes required")
        if known(facts.get("scope")):
            v = facts["scope"]["value"]
            if not isinstance(v, dict) or not v.get("quote") or not v.get("fit_explanation"):
                errors.append(f"{jid}.scope: quote and fit_explanation required")
            elif len(v["quote"].split()) > 25:
                errors.append(f"{jid}.scope: choose a shorter quotation (25-word default)")
            if not any(e.get("source_type") == "official" for e in facts["scope"].get("evidence", [])):
                errors.append(f"{jid}.scope: needs official evidence")
        for metric in ("jcr", "jif"):
            if known(facts.get(metric)):
                value = facts[metric]["value"]
                if not isinstance(value, dict) or type(value.get("year")) is not int:
                    errors.append(f"{jid}.{metric}: explicit metric year required")
                elif metric == "jif" and not number(value.get("number")):
                    errors.append(f"{jid}.jif: nonnegative JIF required")
                elif metric == "jcr":
                    cats = value.get("categories", [])
                    if not cats or any(not c.get("name") or c.get("quartile") not in ("Q1", "Q2", "Q3", "Q4") for c in cats):
                        errors.append(f"{jid}.jcr: named categories and JCR quartiles required")
        if known(facts.get("indexing")):
            v = facts["indexing"]["value"]
            if not isinstance(v, dict) or not isinstance(v.get("collections"), list) or type(v.get("wos_checked")) is not bool:
                errors.append(f"{jid}.indexing: collections and wos_checked required")
        if known(facts.get("oa")) and facts["oa"]["value"] not in ("gold", "hybrid", "subscription", "diamond"):
            errors.append(f"{jid}.oa: invalid OA model")
        if known(facts.get("fees")):
            v = facts["fees"]["value"]
            if not isinstance(v, dict) or not all(k in v for k in ("amount", "currency", "option", "total_known", "notes")):
                errors.append(f"{jid}.fees: amount/currency/option/total_known/notes required")
            elif not number(v["amount"]) or type(v["total_known"]) is not bool or v["option"] not in ("oa", "subscription"):
                errors.append(f"{jid}.fees: invalid amount or total_known")
        if known(facts.get("warnings")):
            v = facts["warnings"]["value"]
            if not isinstance(v, dict) or not isinstance(v.get("flags"), list) or not v.get("checked_lists") or not v.get("coverage_note"):
                errors.append(f"{jid}.warnings: flags, named checked_lists and coverage_note required")
        assessment = journal.get("assessment", {})
        if any(assessment.get(k) not in FIT for k in ("scope_fit", "method_fit")):
            errors.append(f"{jid}: scope_fit and method_fit must be strong/moderate/weak")
        if not assessment.get("reason") or not isinstance(assessment.get("limitations"), list):
            errors.append(f"{jid}: reason and limitations required")
        if not journal.get("ranking_category"):
            errors.append(f"{jid}: record ranking_category or 未核到")
        for precedent in journal.get("precedents", []):
            check_fact(precedent, f"{jid}.precedent", paper=True)
            if known(precedent):
                v = precedent["value"]
                if not isinstance(v, dict) or not all(v.get(k) for k in ("title", "date", "date_kind", "url", "similarity", "difference")):
                    errors.append(f"{jid}.precedent: bibliographic details and comparison required")
                elif v["date_kind"] not in ("publication", "acceptance", "submission"):
                    errors.append(f"{jid}.precedent: explicit date_kind required")
    return errors


def eligibility(journal, constraints):
    facts, pending, excluded = journal["facts"], [], []
    for field in ("identity", "scope", "article_type", "method_policy"):
        if not known(facts[field]):
            pending.append(f"{field}: {MISSING}")
    for field in ("article_type", "method_policy"):
        if known(facts[field]) and not facts[field]["value"]["allowed"]:
            excluded.append(f"{field}: {facts[field]['value']['notes']}")
    if any(journal["assessment"][k] == "weak" for k in ("scope_fit", "method_fit")):
        excluded.append("范围或方法适配弱；见评估理由")
    if known(facts["identity"]) and set(facts["identity"]["value"]["issns"]) & set(constraints.get("exclude_issns", [])):
        excluded.append("用户排除的 ISSN")
    if constraints.get("scie_only"):
        if not known(facts["indexing"]):
            pending.append("SCIE 收录未核到")
        elif "SCIE" not in facts["indexing"]["value"]["collections"]:
            if facts["indexing"]["value"]["wos_checked"]:
                excluded.append("WoS 收录核验不包含 SCIE")
            else:
                pending.append("SCIE 未核到；其他数据库收录不能代替 WoS 核验")
    if constraints.get("jcr_quartiles"):
        if not known(facts["jcr"]):
            pending.append("JCR 分区未核到")
        else:
            v = facts["jcr"]["value"]
            selected = [c for c in v["categories"] if c["name"].casefold() == constraints["jcr_category"].casefold()]
            if not selected or (constraints.get("jcr_year") and v["year"] != constraints["jcr_year"]):
                pending.append("指定 JCR 类别或年度未核到")
            elif selected[0]["quartile"] not in constraints["jcr_quartiles"]:
                excluded.append("不满足指定类别的 JCR 分区")
    if constraints.get("oa_required"):
        if not known(facts["oa"]):
            pending.append("OA 模式未核到")
        elif facts["oa"]["value"] == "subscription":
            excluded.append("不提供 OA 选项")
        elif known(facts["fees"]) and facts["fees"]["value"]["option"] != "oa":
            pending.append("OA 路径适用费用未核到")
    if "max_fee" in constraints:
        fee, limit = facts["fees"], constraints["max_fee"]
        if not known(fee) or not fee["value"]["total_known"]:
            pending.append("适用路径总费用未核到")
        elif fee["value"]["currency"] != limit["currency"]:
            pending.append("币种不同；未进行现查汇率换算")
        elif fee["value"]["amount"] > limit["amount"]:
            excluded.append("超过费用上限")
    if constraints.get("exclude_warnings"):
        warning = facts["warnings"]
        if not known(warning) or not set(constraints["warning_lists"]) <= set(warning["value"]["checked_lists"]):
            pending.append("指定预警名单覆盖未核到")
        elif warning["value"]["flags"]:
            excluded.append("核到风险记录：" + "; ".join(warning["value"]["flags"]))
    return ("excluded", excluded + pending) if excluded else (("pending", pending) if pending else ("eligible", []))


def rankings(bundle):
    if not bundle["run"]["web_available"]:
        return {"routes": {r: [] for r in ROUTES}, "pending": [], "excluded": [], "notes": ["无联网能力：仅输出稿件画像和检索计划。"]}
    c = bundle["constraints"]
    eligible, pending, excluded = [], [], []
    for journal in bundle["journals"]:
        status, reasons = eligibility(journal, c)
        if status == "eligible":
            eligible.append(journal)
        else:
            (pending if status == "pending" else excluded).append({"id": journal["id"], "reasons": reasons})
    fitkey = lambda j: (FIT[j["assessment"]["method_fit"]], FIT[j["assessment"]["scope_fit"]], j["title"])
    fit = sorted(eligible, key=fitkey)
    high, time, notes = [], [], []
    fit_levels = [(j["assessment"]["method_fit"], j["assessment"]["scope_fit"]) for j in eligible]
    if len(set(fit_levels)) < len(fit_levels):
        notes.append("适配等级相同时按刊名排列以保持显示稳定，不表示真实适配存在高低差距。")
    years = {j["facts"]["jcr"]["value"]["year"] for j in eligible if known(j["facts"]["jcr"])}
    ranking_year = c.get("jcr_year") or (max(years) if years else None)
    if len(years) > 1:
        notes.append(f"JCR 年度不同：高分区路线仅使用本次核到的最近数据年度 {ranking_year}；旧年度仍在详情展示。最近核到不等于已证明为最新发布年度。")
    for j in eligible:
        category = c.get("jcr_category") or j["ranking_category"]
        f = j["facts"]["jcr"]
        if known(f) and f["value"]["year"] == ranking_year:
            selected = [x for x in f["value"]["categories"] if x["name"].casefold() == category.casefold()]
            if selected:
                high.append((int(selected[0]["quartile"][1]), fitkey(j), j))
        t = j["timelines"][c.get("time_endpoint", "acceptance")]
        if known(t) and t["value"].get("ranking_usable") and all(e["source_type"] == "official" for e in t["evidence"]):
            v = t["value"]
            # Comparability group is part of output, not hidden in one universal rank.
            group = (v["start_event"], v["statistic"], v["cohort"], v["period"])
            time.append((group, v["days"], fitkey(j), j))
    groups = sorted({t[0] for t in time})
    if len(groups) > 1:
        notes.append("周期定义/统计期不同：时间路线按口径分组；组间不作快慢比较。")
    high.sort(key=lambda x: (x[0], x[1]))
    time.sort(key=lambda x: (x[0], x[1], x[2]))
    if not high:
        notes.append("高分区路线缺少适用类别的已核验 JCR，暂不排名。")
    if not time:
        notes.append("时间路线缺少目标终点的可比较官方周期，暂不排名。")
    return {"routes": {ROUTES[0]: [j["id"] for _, _, j in high[:3]],
                       ROUTES[1]: [j["id"] for _, _, _, j in time[:3]],
                       ROUTES[2]: [j["id"] for j in fit[:3]]},
            "pending": pending, "excluded": excluded, "notes": notes}


def clean(text):
    return str(text).replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|")


def fact_text(fact):
    if not known(fact):
        return MISSING + " — " + clean(fact["reason"])
    v = fact["value"]
    if isinstance(v, list):
        return clean(" / ".join(map(str, v)))
    if not isinstance(v, dict):
        return clean(v)
    if "categories" in v:
        return clean(f"{v['year']} JCR；" + "; ".join(f"{x['name']}: {x['quartile']}" for x in v["categories"]))
    if "collections" in v:
        return clean(" / ".join(v["collections"])) + ("；WoS 已核验" if v["wos_checked"] else "；WoS 具体 collection 未核到")
    if "number" in v:
        return clean(f"{v['year']} JIF: {v['number']}")
    if "days" in v:
        return clean(f"{v['days']} 天；{v['statistic']}；起点 {v['start_event']}；{v['cohort']}；统计期 {v['period']}" + ("" if v.get("ranking_usable") else "；仅展示，不用于时间排名"))
    if "amount" in v:
        return clean(f"{v['amount']} {v['currency']}；路径 {v['option']}；总费用已确认={v['total_known']}；{v['notes']}")
    if "flags" in v:
        return clean("；".join(v["flags"]) if v["flags"] else "在所查名单中未发现匹配记录") + "；" + clean(v["coverage_note"]) + "；名单：" + clean(" / ".join(v["checked_lists"]))
    if "allowed" in v:
        return clean(("允许：" if v["allowed"] else "不允许：") + v["notes"])
    if "issns" in v:
        return clean(" / ".join(v["issns"]))
    return clean(json.dumps(v, ensure_ascii=False))


def constraints_text(c):
    endpoints = dict(zip(ENDPOINTS, ("首轮决定", "接收", "上线", "完成检索")))
    parts = ["时间目标为" + endpoints[c.get("time_endpoint", "acceptance")]]
    if c.get("jcr_quartiles"):
        parts.append("JCR " + "/".join(c["jcr_quartiles"]) + "；类别 " + c["jcr_category"] + (f"；年度 {c['jcr_year']}" if c.get("jcr_year") else ""))
    if c.get("scie_only"):
        parts.append("必须 SCIE")
    if c.get("oa_required"):
        parts.append("必须可选 OA")
    if "max_fee" in c:
        parts.append(f"总费用上限 {c['max_fee']['amount']} {c['max_fee']['currency']}")
    if c.get("exclude_issns"):
        parts.append("排除 ISSN " + ", ".join(c["exclude_issns"]))
    if c.get("exclude_warnings"):
        parts.append("排除以下名单中的期刊：" + "、".join(c["warning_lists"]))
    return clean("；".join(parts) + "。未列出的项目未设硬限制。")


def render(bundle):
    ranking = rankings(bundle)
    out = ["# 医学选刊报告", "", f"核验区间：{bundle['run']['started_at']} — {bundle['run']['completed_at']}", ""]
    if bundle["run"]["mode"] == "offline_fixture":
        out += ["> 离线虚构测试样例。所有期刊和数字均为测试数据，不能用于投稿。", ""]
    else:
        out += ["> 本报告是本次核验的快照；后续使用须重新核验。适配排序不代表录用概率。", ""]
    out += ["## 稿件与条件", "", clean(bundle["profile"]["summary"]), "",
            "研究类型：" + clean(" / ".join(bundle["profile"]["article_types"])), "",
            "方法：" + clean(" / ".join(bundle["profile"]["methods"])), "",
            "验证：" + clean(bundle["profile"]["validation"]), "",
            "材料限制：" + clean("；".join(bundle["profile"]["limitations"]) or "未记录额外材料限制"), "",
            "投稿条件：" + constraints_text(bundle["constraints"]), ""]
    byid = {j["id"]: j for j in bundle["journals"]}
    for route, ids in ranking["routes"].items():
        out += ["## " + route, ""]
        if not ids:
            out += ["暂无可核验排名。见待核验项与原因。", ""]
        for jid in ids:
            j = byid[jid]
            if route == ROUTES[0]:
                reason = fact_text(j["facts"]["jcr"]) + "；采用类别：" + clean(bundle["constraints"].get("jcr_category") or j["ranking_category"])
            elif route == ROUTES[1]:
                reason = fact_text(j["timelines"][bundle["constraints"].get("time_endpoint", "acceptance")]) + "；不同口径不可横比"
            else:
                reason = clean(j["assessment"]["reason"])
            out += [f"- **{clean(j['title'])}** — {reason}"]
        out.append("")
    out += ranking["notes"] + [""]
    if not bundle["run"]["web_available"]:
        out += ["## 建议检索式", ""] + ["- " + clean(q) for q in bundle["profile"]["queries"]]
        return "\n".join(out) + "\n"
    for label, entries in (("待核验候选", ranking["pending"]), ("排除及理由", ranking["excluded"])):
        out += ["## " + label, ""]
        out += [f"- **{clean(byid[x['id']]['title'])}**：{clean('；'.join(x['reasons']))}" for x in entries] or ["本次无此类候选。"]
        out.append("")
    for j in bundle["journals"]:
        out += ["## " + clean(j["title"]), ""]
        scope = j["facts"]["scope"]
        if known(scope):
            out += ["> " + clean(scope["value"]["quote"]), "", clean(scope["value"]["fit_explanation"]), ""]
        else:
            out += ["Scope 原文：" + fact_text(scope), ""]
        out += ["方法适配判断：" + clean(j["assessment"]["reason"]), "",
                "局限／投稿挑战：" + clean("；".join(j["assessment"]["limitations"]) or "未记录额外局限；不代表没有风险"), "",
                "| 核验项 | 结果 |", "|---|---|"]
        labels = {"identity":"ISSN / 身份", "article_type":"文章类型政策", "method_policy":"方法政策", "indexing":"收录", "jcr":"JCR 分区", "jif":"影响因子", "oa":"OA 模式", "fees":"费用", "warnings":"风险与预警"}
        for key, label in labels.items():
            out.append(f"| {label} | {fact_text(j['facts'][key])} |")
        for endpoint, label in zip(ENDPOINTS, ("首轮决定", "接收", "上线", "检索收录")):
            out.append(f"| 周期：{label} | {fact_text(j['timelines'][endpoint])} |")
        out += ["", "### 发表先例", ""]
        if not j.get("precedents"):
            out.append("未核到 — 本次没有确认可用的同类先例。")
        for p in j.get("precedents", []):
            if known(p):
                v = p["value"]
                out.append(f"- [{clean(v['title'])}](<{v['url']}>) — {v['date']} ({v['date_kind']})；相似：{clean(v['similarity'])}；差别：{clean(v['difference'])}")
            else:
                out.append("- " + fact_text(p))
        out += ["", "### 核验记录", ""]
        for key, fact in list(j["facts"].items()) + list(j["timelines"].items()) + [("precedent", p) for p in j.get("precedents", [])]:
            for ev in fact.get("evidence", []):
                out.append(f"- {key}：[来源](<{ev['url']}>)；{ev['checked_at']}；{ev['source_type']}；依据：{clean(ev['support'])}")
        out.append("")
    out += ["## 下一步", "", "先核实待核验硬条件，再由作者选择目标期刊。请勿同时向多刊投稿。选定后可生成投稿信交接材料。", ""]
    return "\n".join(out)


def handoff(bundle, jid):
    journal = next((j for j in bundle["journals"] if j["id"] == jid), None)
    if journal is None:
        raise ValueError("unknown selected journal")
    state, reasons = eligibility(journal, bundle["constraints"])
    return {"schema_version": "1.0", "purpose": "cover_letter_handoff", "selected_by_user": True,
            "profile": bundle["profile"], "journal": journal, "verification_run": bundle["run"],
            "eligibility": state, "unresolved": reasons,
            "instruction": "Recheck current submission requirements. Do not invent author declarations or conceal unresolved issues."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--handoff-journal", help="Use only after the user selected this ID")
    parser.add_argument("--handoff-output", type=Path)
    args = parser.parse_args()
    try:
        bundle = json.loads(args.evidence.read_text(encoding="utf-8-sig"))
        errors = validate(bundle)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors = [f"invalid evidence input: {exc}"]
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render(bundle), encoding="utf-8")
    if args.handoff_journal:
        if not args.handoff_output:
            parser.error("--handoff-output required with --handoff-journal")
        try:
            value = handoff(bundle, args.handoff_journal)
        except ValueError as exc:
            parser.error(str(exc))
        args.handoff_output.parent.mkdir(parents=True, exist_ok=True)
        args.handoff_output.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"valid": True, "meaning": "Structural check only; source truth requires manual verification.",
                      **rankings(bundle)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
