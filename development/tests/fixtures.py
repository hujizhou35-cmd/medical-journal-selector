"""Fictional source data. Reserved example.org URLs; never real journal advice."""
import copy

STAMP = "2026-01-01T12:00:00+00:00"


def verified(value):
    return {"status": "verified", "value": value, "evidence": [{"url": "https://example.org/fictional-journal",
            "source_type": "official", "checked_at": STAMP, "support": "Fictional test source; not real evidence."}]}


def unknown(reason="测试缺失字段"):
    return {"status": "unverified", "value": None, "reason": reason, "evidence": []}


def fixture():
    journals = []
    for idx, (title, issn, q, days, fit) in enumerate([
        ("Fictional Clinical Journal", "9000-0005", "Q1", 120, "moderate"),
        ("Fictional Rapid Health", "9000-0013", "Q2", 60, "moderate"),
        ("Fictional Methods & Care", "9000-0021", "Q3", 100, "strong")]):
        journals.append({"id": f"j{idx}", "title": title, "ranking_category": "Public Health",
            "assessment": {"scope_fit": "strong", "method_fit": fit, "reason": "虚构队列研究与该虚构期刊读者和方法要求匹配。", "limitations": ["仅演示排序；非真实投稿建议。"]},
            "facts": {"identity": verified({"issns": [issn]}),
                "scope": verified({"quote": "We publish public health research.", "fit_explanation": "虚构 scope，演示如何引用和对应研究。"}),
                "article_type": verified({"allowed": True, "notes": "虚构 Original Research 政策"}),
                "method_policy": verified({"allowed": True, "notes": "虚构队列方法政策"}),
                "indexing": verified({"collections": ["SCIE"], "wos_checked": True}),
                "jcr": verified({"year": 2025, "categories": [{"name": "Public Health", "quartile": q}]}),
                "jif": verified({"year": 2025, "number": 3.5}), "oa": verified("gold"),
                "fees": verified({"amount": 1000, "currency": "USD", "option": "oa", "total_known": True, "notes": "虚构总费用"}),
                "warnings": unknown()},
            "timelines": {"first_decision": verified({"days": 10, "statistic": "median", "start_event": "submission", "cohort": "all submissions", "period": "2025", "ranking_usable": True}),
                "acceptance": verified({"days": days, "statistic": "median", "start_event": "submission", "cohort": "accepted articles", "period": "2025", "ranking_usable": True}),
                "online": unknown(), "indexing": unknown()}, "precedents": []})
    return {"schema_version": "1.0", "run": {"mode": "offline_fixture", "web_available": True, "started_at": "2026-01-01T11:59:00+00:00", "completed_at": "2026-01-01T12:01:00+00:00"},
            "profile": {"summary": "虚构教学案例：基层高血压随访队列。", "article_types": ["cohort"], "methods": ["multivariable analysis"], "validation": "无外部验证；非预测模型", "queries": ["hypertension cohort primary care"], "limitations": ["全部为虚构样例"]},
            "constraints": {"time_endpoint": "acceptance"}, "journals": copy.deepcopy(journals)}
