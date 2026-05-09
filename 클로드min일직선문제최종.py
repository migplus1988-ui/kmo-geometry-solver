
from sympy import symbols, solve, Rational,simplify

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
# 규칙 1: 내심 → 이등분선
# ===========================
def rule_incenter_to_bisectors(facts):
    inc = get_constraint(facts, "is_incenter_of", point="I", target="ABC")
    if not inc:
        return False
    changed = False
    for fact in [
        {"type": "is_bisector", "line": "AI", "angle": "Angle_A"},
        {"type": "is_bisector", "line": "BI", "angle": "Angle_B"},
        {"type": "is_bisector", "line": "CI", "angle": "Angle_C"},
    ]:
        if add_derived(facts, fact, "내심_이등분선"):
            changed = True
    return changed

# ===========================
# 규칙 2: 각이등분선 평행선 정리
# ===========================
def rule_bisector_parallel(facts):
    if not get_constraint(facts, "is_parallel", line1="MN", line2="AB"):
        return False
    if not get_constraint(facts, "collinear", points=["M", "I", "N"]):
        return False
    changed = False
    cases = [
        ("AI", "N", "AC", "AN", "NI"),
        ("BI", "M", "BC", "BM", "MI"),
    ]
    for bisector, inter, line, seg1, seg2 in cases:
        if not get_constraint(facts, "is_bisector", line=bisector):
            continue
        if not get_constraint(facts, "on_line", point=inter, line=line):
            continue
        fact = {"type": "equal_length", "seg1": seg1, "seg2": seg2}
        if add_derived(facts, fact, f"각이등분선_평행선_정리_{bisector}"):
            changed = True
    return changed

# ===========================
# 규칙 3: 선분꺾기로 a+b 계산
# ===========================
def rule_ab_from_perimeter(facts):
    if not get_constraint(facts, "equal_length", seg1="AN", seg2="NI"):
        return False
    if not get_constraint(facts, "equal_length", seg1="BM", seg2="MI"):
        return False
    if not get_constraint(facts, "collinear", points=["M", "I", "N"]):
        return False
    perimeter = get_constraint(facts, "perimeter", target="CMN")
    if not perimeter:
        return False

    val = perimeter["value"]
    fact = {"type": "side_sum", "target": "a+b", "value": val}
    return add_derived(facts, fact, "선분꺾기_a+b=둘레CMN")

# ===========================
# 규칙 4: 피타고라스
# ===========================
def rule_pythagorean(facts):
    if not get_constraint(facts, "angle_val", target="Angle_C", value=90):
        return False
    changed = False
    ab = get_constraint(facts, "length", line="AB")
    bc = get_constraint(facts, "length", line="BC")
    ca = get_constraint(facts, "length", line="CA")

    if ab and bc and not ca:
        val = (ab["value"]**2 - bc["value"]**2) ** Rational(1,2)
        if add_derived(facts,
            {"type": "length", "line": "CA", "value": val},
            "피타고라스_CA"):
            changed = True
    if ab and ca and not bc:
        val = (ab["value"]**2 - ca["value"]**2) ** Rational(1,2)
        if add_derived(facts,
            {"type": "length", "line": "BC", "value": val},
            "피타고라스_BC"):
            changed = True
    if bc and ca and not ab:
        val = (bc["value"]**2 + ca["value"]**2) ** Rational(1,2)
        if add_derived(facts,
            {"type": "length", "line": "AB", "value": val},
            "피타고라스_AB"):
            changed = True
    return changed

# ===========================
# 규칙 5: sympy로 a, b 계산
# ===========================
def rule_solve_ab(facts):
    ab_sum = get_constraint(facts, "side_sum", target="a+b")
    c = get_constraint(facts, "length", line="AB")
    if not ab_sum or not c:
        return False

    a, b = symbols('a b', positive=True)
    eq1 = a + b - ab_sum["value"]
    eq2 = a**2 + b**2 - c["value"]**2

    solutions = solve([eq1, eq2], [a, b])
    if not solutions:
        return False

    changed = False
    # sympy 값 그대로 유지 (루트 보존!)
    a_val = solutions[0][0]
    b_val = solutions[0][1]

    print(f"  BC = {a_val}")
    print(f"  CA = {b_val}")
    print(f"  BC * CA = {a_val * b_val}")

    if add_derived(facts,
        {"type": "length", "line": "BC", "value": a_val},
        "sympy_solve_BC"):
        changed = True
    if add_derived(facts,
        {"type": "length", "line": "CA", "value": b_val},
        "sympy_solve_CA"):
        changed = True
    return changed

# ===========================
# 넓이 계산 시도
# ===========================
def try_area(facts):
    # 방법1: (1/2)*BC*CA
    bc = get_constraint(facts, "length", line="BC")
    ca = get_constraint(facts, "length", line="CA")
    if bc and ca:
        area = Rational(1,2) * bc["value"] * ca["value"]
        area =simplify(area)
        print(f"\n  ✅ 넓이계산: (1/2)*BC*CA = {area}")
        return area
    # 방법2: r*s
    r = get_constraint(facts, "inradius")
    s = get_constraint(facts, "semiperimeter", triangle="ABC")
    if r and s:
        area = r["value"] * s["value"]
        print(f"\n  ✅ 넓이계산: r*s = {area}")
        return area
    return None

# ===========================
# 규칙 DB
# ===========================
rule_db = [
    {
        "name": "내심_이등분선",
        "can_apply": lambda f:
            get_constraint(f, "is_incenter_of",
                          point="I", target="ABC") is not None,
        "apply": rule_incenter_to_bisectors
    },
    {
        "name": "각이등분선_평행선_정리",
        "can_apply": lambda f:
            get_constraint(f, "is_bisector") is not None
            and get_constraint(f, "is_parallel",
                             line1="MN", line2="AB") is not None
            and get_constraint(f, "collinear",
                             points=["M","I","N"]) is not None,
        "apply": rule_bisector_parallel
    },
    {
        "name": "선분꺾기_a+b",
        "can_apply": lambda f:
            get_constraint(f, "equal_length",
                          seg1="AN", seg2="NI") is not None
            and get_constraint(f, "equal_length",
                             seg1="BM", seg2="MI") is not None,
        "apply": rule_ab_from_perimeter
    },
    {
        "name": "피타고라스",
        "can_apply": lambda f:
            get_constraint(f, "angle_val",
                          target="Angle_C", value=90) is not None,
        "apply": rule_pythagorean
    },
    {
        "name": "sympy_풀기",
        "can_apply": lambda f:
            get_constraint(f, "side_sum", target="a+b") is not None
            and get_constraint(f, "length", line="AB") is not None,
        "apply": rule_solve_ab
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

        # 넓이 계산 시도
        area = try_area(facts)
        if area:
            print(f"\n{'='*40}")
            print(f"✅ 정답: △ABC 넓이 = {area}")
            print(f"{'='*40}")
            print("\n📝 풀이 과정:")
            for i, s in enumerate(facts["proof_steps"]):
                print(f"  {i+1}. {s['reason']}")
                print(f"     → {s['derived']}")
            return area

        # 규칙 적용
        for rule in rule_db:
            if rule["can_apply"](facts):
                print(f"  🔍 [{rule['name']}] 적용 시도...")
                rule["apply"](facts)

        # facts 변화 없으면 STOP
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
        "points": ["A", "B", "C", "I", "M", "N"],
        "lines": ["AB", "BC", "CA", "MN"],
        "triangles": ["ABC", "CMN"]
    },
    "constraints": [
        {"type": "angle_val", "target": "Angle_C", "value": 90},
        {"type": "is_incenter_of", "point": "I", "target": "ABC"},
        {"type": "is_parallel", "line1": "MN", "line2": "AB"},
        {"type": "collinear", "points": ["M", "I", "N"]},
        {"type": "on_line", "point": "M", "line": "BC"},
        {"type": "on_line", "point": "N", "line": "AC"},
        {"type": "length", "line": "AB", "value": 36},
        {"type": "perimeter", "target": "CMN", "value": 48}
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "area", "triangle": "ABC"}
}

solve_problem(facts)
