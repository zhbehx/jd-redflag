#!/usr/bin/env python3
"""扫描招聘 JD 里的红旗，给出风险分、证据与「面试该问什么」。

用法：
    python scripts/scan_jd.py jd.txt
    python scripts/scan_jd.py jd.txt --explain     # 显示每条的原文与问法
    python scripts/scan_jd.py jd.txt --json
    python scripts/scan_jd.py jd.txt --fail-over 60

退出码：0 正常；--fail-over 触发时 1；文件错误 2。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# (正则, 级别, 维度, 真实含义, 面试问法)
# 级别：H=高危(扣15) M=中危(扣7) L=提醒(扣3)
RULES: list[tuple[str, str, str, str, str]] = [
    # ---- 加班与作息 ----
    (r"抗压(能力)?强|承受(较大|一定)压力|能承受压力", "H", "加班与作息",
     "会加班，且大概率没有加班费", "最近三个月，团队最晚一次几点走？"),
    (r"狼性", "H", "加班与作息", "结果压倒一切，过程保障少", "完不成目标的人通常怎么处理？"),
    (r"弹性工作(制|时间)?", "M", "加班与作息", "弹性上班但不弹性下班，或不写工时", "每天有固定的核心协作时段吗？"),
    (r"高强度|高压力|工作强度大", "H", "加班与作息", "明确告诉你强度高", "平均每周实际工时大约多少？"),
    (r"大小周|单休|六天工作制|6天工作制", "H", "加班与作息", "法定外的额外工作日", "大小周有额外调休或补贴吗？"),
    (r"996|007|奋斗者|奋斗文化", "H", "加班与作息", "明确的高强度信号", "工时与加班费怎么算？"),
    (r"快速迭代|快节奏|节奏快", "M", "加班与作息", "需求变更频繁，排期紧", "一个需求从提出到上线典型周期多久？"),
    (r"随时响应|保持在线|on[- ]?call", "M", "加班与作息", "下班后也要回消息", "非工作时间的响应预期是什么？"),

    # ---- 薪资陷阱 ----
    (r"薪资面议|薪酬面议|待遇面议|工资面议", "H", "薪资陷阱",
     "不想写，通常低于市场", "这个岗位的预算区间是多少？"),
    (r"底薪\s*[+＋]|提成上不封顶|无责任底薪|有责任底薪", "H", "薪资陷阱",
     "底薪可能极低，收入靠提成", "底薪具体多少？提成按什么口径算？"),
    (r"绩效(占比|比例)\s*(4|5|6|7|8|9)\d%|绩效工资占", "H", "薪资陷阱",
     "大半工资看领导打分", "绩效指标是什么？去年实际发放比例？"),
    (r"试用期(工资|薪资).{0,8}(打|折|8折|80%)|试用期.{0,6}[六七八]折", "H", "薪资陷阱",
     "可能低于法定下限（不得低于转正后的 80%）", "试用期薪资是转正后的百分之多少？"),
    (r"期权|股权激励|原始股", "M", "薪资陷阱", "用未来抵现在", "行权价、成熟期、回购条款怎么定？"),
    (r"年薪\s*\d+\s*万|年包|总包", "M", "薪资陷阱", "可能是含年终与补贴的总数", "月薪和年终的占比各是多少？"),

    # ---- 职责混乱 ----
    (r"一人多岗|身兼数职|多岗位职责|一职多能", "M", "职责混乱",
     "编制不够，一个人干几个人的活", "这个岗位现在几个人？我进来补哪块？"),
    (r"其他(领导|上级|公司)交办|领导交办的一切", "M", "职责混乱", "工作边界无限", "临时事务大概占日常多少比例？"),
    (r"配合(老板|领导|总经理)处理.{0,6}事务", "M", "职责混乱", "可能是私人助理性质", "这个岗位和老板的工作边界怎么划？"),
    (r"不限经验|学历不限|经验不限", "L", "职责混乱", "低薪信号，或招不到人", "团队里同岗位的人是什么背景？"),

    # ---- 文化与话术 ----
    (r"大家庭|家文化|我们的家", "M", "文化与话术", "用情感替代制度与报酬", "团队的人员流动率大概多少？"),
    (r"主人翁(精神|意识)|把公司(当|当成)自己", "M", "文化与话术", "要你自愿多干", "超出职责的工作怎么算绩效？"),
    (r"能者多劳", "M", "文化与话术", "多劳但不多得", "多承担的部分在晋升或薪酬上怎么体现？"),
    (r"不要只看(钱|薪资)|要有情怀|情怀驱动", "H", "文化与话术", "钱给不到位", "（不用问，直接看薪资数字）"),
    (r"有激情|有梦想|认同(我们|公司)(的)?(文化|价值观)", "L", "文化与话术", "常见于早期公司或高强度团队", "公司现在最难的阶段是什么？"),
    (r"扁平化(管理)?|扁平管理", "L", "文化与话术", "可能没有明确汇报线与晋升机制", "晋升流程是什么样的？谁来评？"),

    # ---- 承诺模糊 ----
    (r"成长空间(大|巨大)|发展空间大", "M", "承诺模糊", "无法量化，通常是唯一优点", "过去一年团队里有人晋升或涨薪吗？"),
    (r"学习(机会|空间)多|能学到很多", "L", "承诺模糊", "可能是没人带你", "新人前三个月有带教吗？"),
    (r"未来(上市|IPO)|明年(上市|IPO)|即将上市", "M", "承诺模糊", "不要算进你的收入", "（忽略，只看现金）"),
    (r"行业前景(好|广阔)|朝阳行业", "L", "承诺模糊", "只说明行业，不说明这家公司", "公司在行业里排第几？主要对手是谁？"),

    # ---- 合规风险 ----
    (r"押金|扣押(身份证|证件|毕业证)", "H", "合规风险", "违法", "（直接不投）"),
    (r"无薪试岗|试岗.{0,4}无薪|免费试工", "H", "合规风险", "提供劳动即应付酬", "（直接不投）"),
    (r"不签(劳动)?合同|先(干活|上班)后签", "H", "合规风险", "应自用工之日起一个月内签合同", "什么时候签劳动合同？"),
    (r"自费(体检|培训|工装|押金)", "H", "合规风险", "变相收费", "这些费用由谁承担？"),
    (r"离职.{0,6}(3|三|6|六)个月|违约金", "M", "合规风险", "超过法定条件的约定可能无效", "劳动合同里具体怎么约定的？"),
    (r"体检自费|自带电脑|自备设备", "L", "合规风险", "成本转嫁给员工", "设备补贴有吗？"),
]

LEVEL_PENALTY = {"H": 15, "M": 7, "L": 3}
LEVEL_LABEL = {"H": "高危", "M": "中危", "L": "提醒"}

# 「没写什么」检查：(名称, 触发正则, 缺失时的提示)
MISSING_CHECKS = [
    ("薪资区间", r"\d+\s*[-–~至]\s*\d+\s*[kK千万]|\d+\s*[kK]\s*[-–~至]|月薪|年薪",
     "没写薪资区间：大概率低于市场，或想看你报多少"),
    ("五险一金", r"五险一金|社保|公积金",
     "没写社保：入职前必须问清什么时候开始缴"),
    ("工作时间", r"双休|工作时长|上班时间|9[:：]\d{2}|朝九|做五休二",
     "没写工时：默认按最差的假设（大小周或更差）"),
    ("团队规模", r"团队\s*\d+\s*人|\d+\s*人(的)?团队|直属.{0,4}\d+\s*人",
     "没写团队规模：可能是新设岗，或这个岗只有你一个人"),
]


def cjk_len(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))

DUTY_HEAD = re.compile(r"(?:岗位)?职责|工作内容|你将负责|工作职责")
REQ_HEAD = re.compile(r"任职(?:要求|资格)|岗位要求|我们希望你|职位要求|你需要具备")
OTHER_HEAD = re.compile(r"薪资|薪酬|待遇|福利|工作时间|上下班|团队(?:规模|情况)|汇报|加分项|工作地点|关于我们")


def duty_much_longer(text: str) -> bool:
    """职责段落是不是明显长于要求段落（1.5 倍以上）。"""
    d = DUTY_HEAD.search(text)
    r = REQ_HEAD.search(text)
    if not d or not r:
        return False
    if r.start() <= d.start():
        return False
    duty_text = text[d.start():r.start()]
    # 要求段落到下一个大标题或文末为止
    rest = text[r.start():]
    nxt = OTHER_HEAD.search(rest, r.end() - r.start())
    req_text = rest[: nxt.start()] if nxt else rest
    dlen, rlen = cjk_len(duty_text), cjk_len(req_text)
    return rlen > 0 and dlen > rlen * 1.5



def scan(text: str) -> dict:
    hits = []
    for pattern, level, dim, meaning, ask in RULES:
        for m in re.finditer(pattern, text, re.I):
            hits.append({
                "match": m.group(0),
                "level": level,
                "dimension": dim,
                "meaning": meaning,
                "ask": ask,
                "pos": m.start(),
            })

    # 同一维度同一词只保留一次，避免重复扣分
    seen: set[tuple[str, str]] = set()
    uniq = []
    for h in sorted(hits, key=lambda x: x["pos"]):
        key = (h["dimension"], h["match"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)

    # 职责长度 vs 要求长度：活多钱少的信号。
    # 必须按段落切分——早期版本从标题取到文末，导致 duty 恒大于 req，正常 JD 也误报。
    duty_heavy = duty_much_longer(text)

    penalty = sum(LEVEL_PENALTY[h["level"]] for h in uniq)
    if duty_heavy:
        penalty += 8
    score = min(100, penalty)

    if score >= 60:
        band = "高危：建议只当练手，去的话逐条问清"
    elif score >= 30:
        band = "需核实：可以投，但面试必须问到点上"
    else:
        band = "相对正常：正常投，注意下面「没写的东西」"

    missing = [{"item": name, "note": note}
               for name, pat, note in MISSING_CHECKS
               if not re.search(pat, text, re.I)]

    by_dim: dict[str, list] = {}
    for h in uniq:
        by_dim.setdefault(h["dimension"], []).append(h)

    return {
        "score": score,
        "band": band,
        "red_count": sum(1 for h in uniq if h["level"] == "H"),
        "yellow_count": sum(1 for h in uniq if h["level"] == "M"),
        "note_count": sum(1 for h in uniq if h["level"] == "L"),
        "hits": uniq,
        "by_dimension": {k: len(v) for k, v in by_dim.items()},
        "duty_heavy": duty_heavy,
        "missing": missing,
        "cjk_chars": cjk_len(text),
    }


def render(r: dict, explain: bool) -> str:
    out = []
    out.append(f"风险分：{r['score']}/100    {r['band']}")
    out.append(f"命中：高危 {r['red_count']} · 中危 {r['yellow_count']} · 提醒 {r['note_count']}"
               f"   （JD {r['cjk_chars']} 个汉字）")
    if r["duty_heavy"]:
        out.append("⚠️ 岗位职责比任职要求长 1.5 倍以上：典型的活多钱少结构")

    for dim, count in sorted(r["by_dimension"].items(), key=lambda x: -x[1]):
        out.append(f"\n【{dim}】{count} 条")
        for h in [x for x in r["hits"] if x["dimension"] == dim]:
            out.append(f"  [{LEVEL_LABEL[h['level']]}] 「{h['match']}」")
            if explain:
                out.append(f"       含义：{h['meaning']}")
                out.append(f"       问法：{h['ask']}")

    if r["missing"]:
        out.append("\n【JD 没写的（比写了的更值得警惕）】")
        for m in r["missing"]:
            out.append(f"  - {m['item']}：{m['note']}")

    if not explain:
        out.append("\n加 --explain 看每条红旗的含义与面试问法。")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="扫描招聘 JD 的红旗")
    ap.add_argument("file", help="JD 文本文件")
    ap.add_argument("--explain", action="store_true", help="显示含义与面试问法")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-over", type=float, default=None, help="风险分超过该值时退出码 1")
    args = ap.parse_args(argv)

    p = Path(args.file)
    if not p.is_file():
        print(f"找不到文件：{p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8-sig")
    if cjk_len(text) < 20:
        print("JD 太短（不足 20 个汉字），扫描结果不可靠。", file=sys.stderr)
        return 2

    r = scan(text)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(render(r, args.explain))

    if args.fail_over is not None and r["score"] > args.fail_over:
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
