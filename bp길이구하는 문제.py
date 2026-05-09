
from sympy import Rational, simplify

# ===========================
# 헬퍼 함수
# ===========================
def get_constraint(facts, type, **kwargs):
    all_facts = facts["constraints"] + facts["derived"]
    for c in all_facts:
        if c["type"] == type:
            if all(c.get(k) == v for k, v in kwargs.items()):
                return c
    return None

def add_derived(facts, fact, reason):
    for d in facts["derived"]:
        if d == fact:
            return False
    facts["derived"].append(fact)
    facts["proof_steps"].append({"derived": fact, "reason": reason})
    print(f"  ✅ [{reason}]: {fact}")
    return True

# ===========================
# 규칙 1: 선분 방향 통일 AB=BA
# ===========================
def rule_segment_direction(facts):
    changed = False
    all_facts = facts["constraints"] + facts["derived"]
    lengths = [f for f in all_facts if f["type"] == "length"]

    for seg in lengths:
        line = seg["line"]
        reverse = line[::-1]  # AB → BA
        if not get_constraint(facts, "length", line=reverse):
            if add_derived(facts,
                {"type": "length", "line": reverse,
                 "value": seg["value"]},
                f"선분방향_{reverse}={line}"):
                changed = True
    return changed

# ===========================
# 규칙 2: 선분 분할 레마
# ===========================
def rule_segment_break(facts):
    changed = False
    all_facts = facts["constraints"] + facts["derived"]
    collinears = [f for f in all_facts if f["type"] == "collinear"]

    for col in collinears:
        pts = col["points"]  # [A, Q, B]
        # 순서대로: pts[0]+pts[2] = pts[0]+pts[1] + pts[1]+pts[2]
        cases = [
            (pts[0]+pts[2], pts[0]+pts[1], pts[1]+pts[2]),
            (pts[2]+pts[0], pts[2]+pts[1], pts[1]+pts[0]),
        ]
        for full, seg1, seg2 in cases:
            f  = get_constraint(facts, "length", line=full)
            s1 = get_constraint(facts, "length", line=seg1)
            s2 = get_constraint(facts, "length", line=seg2)

            if f and s1 and not s2:
                val = f["value"] - s1["value"]
                if add_derived(facts,
                    {"type": "length", "line": seg2, "value": val},
                    f"선분분할레마_{seg2}={full}-{seg1}"):
                    changed = True

            if f and s2 and not s1:
                val = f["value"] - s2["value"]
                if add_derived(facts,
                    {"type": "length", "line": seg1, "value": val},
                    f"선분분할레마_{seg1}={full}-{seg2}"):
                    changed = True

            if s1 and s2 and not f:
                val = s1["value"] + s2["value"]
                if add_derived(facts,
                    {"type": "length", "line": full, "value": val},
                    f"선분분할레마_{full}={seg1}+{seg2}"):
                    changed = True

    return changed

# ===========================
# 규칙 3: 방멱 정리
# BQ × BA = BP × BC
# ===========================
def rule_power_of_point(facts):
    circle = get_constraint(facts, "circumcircle",
                           triangle="APC", name="Ω")
    if not circle:
        return False

    bq = get_constraint(facts, "length", line="BQ")
    ba = get_constraint(facts, "length", line="BA")
    bc = get_constraint(facts, "length", line="BC")
    bp = get_constraint(facts, "length", line="BP")

    if not bq or not ba or not bc:
        return False

    changed = False
    if not bp:
        val = Rational(bq["value"] * ba["value"]) / bc["value"]
        if add_derived(facts,
            {"type": "length", "line": "BP", "value": val},
            "방멱정리_BP=BQ×BA/BC"):
            changed = True
    return changed

# ===========================
# 목표: BP 길이
# ===========================
def try_answer(facts):
    bp = get_constraint(facts, "length", line="BP")
    if bp:
        val = bp["value"]
        print(f"\n  ✅ BP = {val}")
        if hasattr(val, 'p'):
            print(f"  ✅ m+n = {val.p}+{val.q} = {val.p + val.q}")
        return val
    return None

# ===========================
# 규칙 DB
# ===========================
rule_db = [
    {
        "name": "선분방향통일",
        "can_apply": lambda f:
            any(c["type"] == "length"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_segment_direction
    },
    {
        "name": "선분분할레마",
        "can_apply": lambda f:
            any(c["type"] == "collinear"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_segment_break
    },
    {
        "name": "방멱정리",
        "can_apply": lambda f:
            get_constraint(f, "circumcircle",
                          triangle="APC", name="Ω") is not None
            and get_constraint(f, "length", line="BQ") is not None,
        "apply": rule_power_of_point
    },
]

# ===========================
# 추론 엔진
# ===========================
def solve_problem(facts):
    print("=" * 40)
    print("추론 시작!")
    print("=" * 40)

    step = 0
    while True:
        print(f"\n--- {step}단계 ---")
        prev_derived = facts["derived"].copy()

        answer = try_answer(facts)
        if answer:
            print(f"\n{'='*40}")
            print(f"✅ 정답: BP = {answer}")
            print(f"{'='*40}")
            print("\n📝 풀이 과정:")
            for i, s in enumerate(facts["proof_steps"]):
                print(f"  {i+1}. {s['reason']}")
                print(f"     → {s['derived']}")
            return answer

        for rule in rule_db:
            if rule["can_apply"](facts):
                print(f"  🔍 [{rule['name']}] 적용 시도...")
                rule["apply"](facts)

        if facts["derived"] == prev_derived:
            print("\n❌ 더 이상 추론 불가 STOP")
            print("\n현재 derived facts:")
            for d in facts["derived"]:
                print(f"  {d}")
            return None

        step += 1

# ===========================
# Facts 초기화 및 실행
# ===========================
facts = {
    "entities": {
        "points": ["A", "B", "C", "P", "Q"],
        "lines": ["AB", "BC", "CA"],
        "triangles": ["ABC", "APC"],
        "circles": ["Ω"]
    },
    "constraints": [
        {"type": "length", "line": "AB", "value": Rational(12)},
        {"type": "length", "line": "BC", "value": Rational(10)},
        {"type": "length", "line": "CA", "value": Rational(9)},
        {"type": "length", "line": "AQ", "value": Rational(19, 3)},
        {"type": "collinear", "points": ["A", "Q", "B"]},
        {"type": "collinear", "points": ["B", "P", "C"]},
        {"type": "circumcircle", "triangle": "APC", "name": "Ω"},
        {"type": "on_circle", "point": "Q", "circle": "Ω"},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length", "line": "BP"}
}

solve_problem(facts)
