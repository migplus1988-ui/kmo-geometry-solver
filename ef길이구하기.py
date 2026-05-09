from sympy import Rational, sqrt, simplify
from itertools import combinations

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

def get_all_constraints(facts, type, **kwargs):
    all_facts = facts["constraints"] + facts["derived"]
    result = []
    for c in all_facts:
        if c["type"] == type:
            if all(c.get(k) == v for k, v in kwargs.items()):
                result.append(c)
    return result

def add_derived(facts, fact, reason):
    for d in facts["derived"]:
        if d == fact:
            return False
    facts["derived"].append(fact)
    facts["proof_steps"].append({"derived": fact, "reason": reason})
    print(f"  ✅ [{reason}]: {fact}")
    return True

# ===========================
# 공리: AB = BA 자동처리
# ===========================
def init_facts(facts):
    for c in facts["constraints"][:]:
        if c["type"] == "length":
            line = c["line"]
            reverse = line[::-1]
            if not get_constraint(facts, "length", line=reverse):
                facts["constraints"].append(
                    {"type": "length",
                     "line": reverse,
                     "value": c["value"]}
                )

# ===========================
# 원 위의 점 목록 구하기
# ===========================
def get_circle_points(facts, circle_name):
    all_facts = facts["constraints"] + facts["derived"]
    circles = [f for f in all_facts
               if f["type"] == "circumcircle"
               and f["name"] == circle_name]
    if not circles:
        return []
    tri = circles[0]["triangle"]
    tri_pts = list(tri)
    on_circle = tri_pts + [
        f["point"] for f in all_facts
        if f["type"] == "on_circle"
        and f["circle"] == circle_name
    ]
    return list(set(on_circle))

# ===========================
# 선분 길이 찾기 (양방향)
# ===========================
def get_length(facts, p1, p2):
    result = get_constraint(facts, "length", line=p1+p2)
    if not result:
        result = get_constraint(facts, "length", line=p2+p1)
    return result

# ===========================
# 규칙 1: 선분 분할 레마
# ===========================
def rule_segment_break(facts):
    changed = False
    all_facts = facts["constraints"] + facts["derived"]
    collinears = [f for f in all_facts if f["type"] == "collinear"]

    for col in collinears:
        pts = col["points"]
        cases = [
            (pts[0]+pts[2], pts[0]+pts[1], pts[1]+pts[2]),
            (pts[2]+pts[0], pts[2]+pts[1], pts[1]+pts[0]),
        ]
        for full, seg1, seg2 in cases:
            f  = get_length(facts, pts[0], pts[2])
            s1 = get_length(facts, pts[0], pts[1])
            s2 = get_length(facts, pts[1], pts[2])

            if f and s1 and not s2:
                val = f["value"] - s1["value"]
                if val > 0:
                    if add_derived(facts,
                        {"type": "length", "line": seg2, "value": val},
                        f"선분분할레마_{seg2}={full}-{seg1}"):
                        changed = True

            if f and s2 and not s1:
                val = f["value"] - s2["value"]
                if val > 0:
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
# 규칙 2: 중선정리
# ===========================
def rule_median(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    midpoints = [f for f in all_facts if f["type"] == "midpoint"]

    for mid in midpoints:
        d    = mid["point"]
        line = mid["line"]
        p1, p2 = line[0], line[1]

        # 모든 점에서 중선 탐색
        all_pts = facts["entities"]["points"]
        for a in all_pts:
            if a == d or a == p1 or a == p2:
                continue

            ab = get_length(facts, a, p1)
            ac = get_length(facts, a, p2)
            ad = get_length(facts, a, d)
            bc = get_length(facts, p1, p2)

            # BC 구하기
            if ab and ac and ad and not bc:
                val = simplify(sqrt(
                    2*(ab["value"]**2 + ac["value"]**2)
                    - 4*ad["value"]**2
                ))
                if add_derived(facts,
                    {"type": "length", "line": p1+p2, "value": val},
                    f"중선정리_{p1+p2}"):
                    changed = True

            # AD 구하기
            if ab and ac and bc and not ad:
                val = simplify(sqrt(
                    (2*ab["value"]**2 + 2*ac["value"]**2
                     - bc["value"]**2) / 4
                ))
                if add_derived(facts,
                    {"type": "length", "line": a+d, "value": val},
                    f"중선정리_{a+d}"):
                    changed = True
    return changed

# ===========================
# 규칙 3: 헤론공식
# ===========================
def rule_heron(facts):
    changed = False
    triangles = facts["entities"]["triangles"]

    for tri in triangles:
        pts = list(tri)
        p1, p2, p3 = pts[0], pts[1], pts[2]

        s0 = get_length(facts, p1, p2)
        s1 = get_length(facts, p2, p3)
        s2 = get_length(facts, p1, p3)
        area = get_constraint(facts, "area", triangle=tri)

        if s0 and s1 and s2 and not area:
            a = s0["value"]
            b = s1["value"]
            c = s2["value"]
            s = (a + b + c) / 2
            val = simplify(sqrt(s*(s-a)*(s-b)*(s-c)))
            if add_derived(facts,
                {"type": "area", "triangle": tri, "value": val},
                f"헤론공식_{tri}"):
                changed = True
    return changed

# ===========================
# 규칙 4: 중점 넓이
# ===========================
def rule_midpoint_area(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    midpoints = [f for f in all_facts if f["type"] == "midpoint"]

    for mid in midpoints:
        d    = mid["point"]
        line = mid["line"]
        p1, p2 = line[0], line[1]

        all_pts = facts["entities"]["points"]
        for a in all_pts:
            if a == d or a == p1 or a == p2:
                continue

            # [Ap1p2] 찾기
            for tri in [a+p1+p2, a+p2+p1,
                        p1+a+p2, p1+p2+a,
                        p2+a+p1, p2+p1+a]:
                area_full = get_constraint(facts, "area", triangle=tri)
                if not area_full:
                    continue

                for sub_tri in [a+p1+d, a+p2+d,
                                p1+a+d, p2+a+d]:
                    if not get_constraint(facts, "area", triangle=sub_tri):
                        val = area_full["value"] / 2
                        if add_derived(facts,
                            {"type": "area", "triangle": sub_tri, "value": val},
                            f"중점넓이_{sub_tri}={tri}/2"):
                            changed = True
    return changed

# ===========================
# 규칙 5: 수선의 발 넓이
# ===========================
def rule_altitude_from_area(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    perps = [f for f in all_facts if f["type"] == "perpendicular"]

    for perp in perps:
        foot = perp["foot"]
        frm  = perp["from"]
        to   = perp["to"]
        p1, p2 = to[0], to[1]

        # 모든 삼각형 순열
        for tri in [frm+p1+p2, frm+p2+p1,
                    p1+frm+p2, p1+p2+frm,
                    p2+frm+p1, p2+p1+frm]:
            area = get_constraint(facts, "area", triangle=tri)
            base = get_length(facts, p1, p2)
            height = get_length(facts, frm, foot)

            if area and base and not height:
                val = simplify(2 * area["value"] / base["value"])
                if add_derived(facts,
                    {"type": "length", "line": frm+foot, "value": val},
                    f"수선의발_{frm+foot}=2[{tri}]/{to}"):
                    changed = True
    return changed

# ===========================
# 규칙 6: 피타고라스
# ===========================
def rule_pythagorean(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    perps = [f for f in all_facts if f["type"] == "perpendicular"]

    for perp in perps:
        foot = perp["foot"]
        frm  = perp["from"]
        to   = perp["to"]
        p1, p2 = to[0], to[1]

        # frm-foot 수직
        # frm-foot ⊥ p1-p2
        # 직각삼각형: frm, foot, p1 또는 frm, foot, p2
        for other in [p1, p2]:
            l1 = get_length(facts, frm, foot)   # 높이
            l2 = get_length(facts, foot, other)  # 밑변
            h  = get_length(facts, frm, other)   # 빗변

            if l1 and l2 and not h:
                val = simplify(sqrt(
                    l1["value"]**2 + l2["value"]**2))
                if add_derived(facts,
                    {"type": "length",
                     "line": frm+other, "value": val},
                    f"피타고라스_{frm+other}"):
                    changed = True

            if l1 and h and not l2:
                diff = h["value"]**2 - l1["value"]**2
                if simplify(diff) > 0:
                    val = simplify(sqrt(diff))
                    if add_derived(facts,
                        {"type": "length",
                         "line": foot+other, "value": val},
                        f"피타고라스_{foot+other}"):
                        changed = True

            if l2 and h and not l1:
                diff = h["value"]**2 - l2["value"]**2
                if simplify(diff) > 0:
                    val = simplify(sqrt(diff))
                    if add_derived(facts,
                        {"type": "length",
                         "line": frm+foot, "value": val},
                        f"피타고라스_{frm+foot}"):
                        changed = True
    return changed

# ===========================
# 규칙 7: 방멱정리
# ===========================
def rule_power_of_point(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    circles = [f for f in all_facts if f["type"] == "circumcircle"]

    for circle in circles:
        circle_name = circle["name"]
        on_circle = get_circle_points(facts, circle_name)
        all_pts = facts["entities"]["points"]

        # 원 밖의 점
        ext_pts = [p for p in all_pts if p not in on_circle]

        collinears = [f for f in all_facts if f["type"] == "collinear"]

        for ext in ext_pts:
            # ext를 포함하는 collinear 중
            # 원 위의 점 2개를 지나는 할선 찾기
            secants = []
            for col in collinears:
                pts = col["points"]
                if ext not in pts:
                    continue
                on_cir_in_col = [p for p in pts
                                 if p in on_circle]
                if len(on_cir_in_col) >= 2:
                    secants.append(on_cir_in_col[:2])
                elif len(on_cir_in_col) == 1:
                    # 원 위의 점 1개 + 외부점
                    ext_in_col = [p for p in pts
                                  if p not in on_circle
                                  and p != ext]
                    if ext_in_col:
                        secants.append(
                            (on_cir_in_col[0], ext_in_col[0])
                        )

            # 두 할선이 있으면 방멱 적용
            if len(secants) >= 2:
                for i in range(len(secants)):
                    for j in range(i+1, len(secants)):
                        s1 = secants[i]
                        s2 = secants[j]

                        # ext→s1[0], ext→s1[1]
                        ep1 = get_length(facts, ext, s1[0])
                        ep2 = get_length(facts, ext, s1[1])
                        # ext→s2[0], ext→s2[1]
                        ep3 = get_length(facts, ext, s2[0])
                        ep4 = get_length(facts, ext, s2[1])

                        # ep1×ep2 = ep3×ep4
                        if ep1 and ep2 and ep3 and not ep4:
                            val = simplify(
                                ep1["value"] * ep2["value"]
                                / ep3["value"]
                            )
                            line = ext+s2[1]
                            if add_derived(facts,
                                {"type": "length",
                                 "line": line, "value": val},
                                f"방멱정리_{line}"):
                                changed = True

                        if ep1 and ep2 and ep4 and not ep3:
                            val = simplify(
                                ep1["value"] * ep2["value"]
                                / ep4["value"]
                            )
                            line = ext+s2[0]
                            if add_derived(facts,
                                {"type": "length",
                                 "line": line, "value": val},
                                f"방멱정리_{line}"):
                                changed = True

                        if ep3 and ep4 and ep1 and not ep2:
                            val = simplify(
                                ep3["value"] * ep4["value"]
                                / ep1["value"]
                            )
                            line = ext+s1[1]
                            if add_derived(facts,
                                {"type": "length",
                                 "line": line, "value": val},
                                f"방멱정리_{line}"):
                                changed = True

                        if ep3 and ep4 and ep2 and not ep1:
                            val = simplify(
                                ep3["value"] * ep4["value"]
                                / ep2["value"]
                            )
                            line = ext+s1[0]
                            if add_derived(facts,
                                {"type": "length",
                                 "line": line, "value": val},
                                f"방멱정리_{line}"):
                                changed = True
    return changed

# ===========================
# 규칙 8: 톨레미
# ===========================
def rule_ptolemy(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    circles = [f for f in all_facts if f["type"] == "circumcircle"]

    for circle in circles:
        circle_name = circle["name"]
        on_circle = get_circle_points(facts, circle_name)

        if len(on_circle) < 4:
            continue

        for four_pts in combinations(on_circle, 4):
            p1, p2, p3, p4 = four_pts

            # 톨레미: p1p3·p2p4 = p1p2·p3p4 + p2p3·p1p4
            diag1 = get_length(facts, p1, p3)
            diag2 = get_length(facts, p2, p4)
            s12   = get_length(facts, p1, p2)
            s23   = get_length(facts, p2, p3)
            s34   = get_length(facts, p3, p4)
            s14   = get_length(facts, p1, p4)

            if s12 and s23 and s34 and s14:
                # diag1 구하기
                if diag2 and not diag1:
                    val = simplify(
                        (s12["value"]*s34["value"]
                         + s23["value"]*s14["value"])
                        / diag2["value"]
                    )
                    if add_derived(facts,
                        {"type": "length",
                         "line": p1+p3, "value": val},
                        f"톨레미_{p1+p3}"):
                        changed = True

                # diag2 구하기
                if diag1 and not diag2:
                    val = simplify(
                        (s12["value"]*s34["value"]
                         + s23["value"]*s14["value"])
                        / diag1["value"]
                    )
                    if add_derived(facts,
                        {"type": "length",
                         "line": p2+p4, "value": val},
                        f"톨레미_{p2+p4}"):
                        changed = True
    return changed

# ===========================
# 목표 확인
# ===========================
def try_answer(facts):
    target = facts["target"]
    if target["type"] == "length":
        result = get_length(facts,
                           target["line"][0],
                           target["line"][1])
        if result:
            val = simplify(result["value"])
            print(f"\n  ✅ {target['line']} = {val}")
            if hasattr(val, 'p'):
                print(f"  ✅ m+n = {val.p}+{val.q} = {val.p+val.q}")
            return val
    elif target["type"] == "area":
        result = get_constraint(facts, "area",
                               triangle=target["triangle"])
        if result:
            val = simplify(result["value"])
            print(f"\n  ✅ [{target['triangle']}] = {val}")
            return val
    return None

# ===========================
# 규칙 DB
# ===========================
rule_db = [
    {
        "name": "선분분할레마",
        "can_apply": lambda f:
            any(c["type"] == "collinear"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_segment_break
    },
    {
        "name": "중선정리",
        "can_apply": lambda f:
            any(c["type"] == "midpoint"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_median
    },
    {
        "name": "헤론공식",
        "can_apply": lambda f:
            len(f["entities"]["triangles"]) > 0,
        "apply": rule_heron
    },
    {
        "name": "중점넓이",
        "can_apply": lambda f:
            any(c["type"] == "midpoint"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_midpoint_area
    },
    {
        "name": "수선의발",
        "can_apply": lambda f:
            any(c["type"] == "perpendicular"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_altitude_from_area
    },
    {
        "name": "피타고라스",
        "can_apply": lambda f:
            any(c["type"] == "perpendicular"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_pythagorean
    },
    {
        "name": "방멱정리",
        "can_apply": lambda f:
            any(c["type"] == "circumcircle"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_power_of_point
    },
    {
        "name": "톨레미",
        "can_apply": lambda f:
            any(c["type"] == "circumcircle"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_ptolemy
    },
]

# ===========================
# 추론 엔진
# ===========================
def solve_problem(facts):
    print("=" * 40)
    print("추론 시작!")
    print("=" * 40)

    max_steps = 50
    step = 0

    while step < max_steps:
        print(f"\n--- {step}단계 ---")
        prev_derived = facts["derived"].copy()

        answer = try_answer(facts)
        if answer:
            print(f"\n{'='*40}")
            print(f"✅ 정답: {answer}")
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

    print(f"\n⚠️ 최대 스텝({max_steps}) 초과!")
    return None

# ===========================
# 문제 1: BP 구하기
# ===========================
facts1 = {
    "entities": {
        "points": ["A", "B", "C", "P", "Q"],
        "lines": ["AB", "BC", "CA"],
        "triangles": ["APC"],
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

# ===========================
# 문제 2: EF 구하기
# ===========================
facts2 = {
    "entities": {
        "points": ["A", "B", "C", "D", "E", "F"],
        "lines": ["AB", "BC", "CA", "AD", "DE", "DF", "EF"],
        "triangles": ["ABC", "ABD", "ACD"],
        "circles": ["Ω"]
    },
    "constraints": [
        {"type": "length", "line": "AB", "value": Rational(8)},
        {"type": "length", "line": "AC", "value": Rational(10)},
        {"type": "length", "line": "AD", "value": sqrt(33)},
        {"type": "midpoint", "point": "D", "line": "BC"},
        {"type": "collinear", "points": ["B", "D", "C"]},
        {"type": "perpendicular", "from": "D", "to": "AB", "foot": "E"},
        {"type": "perpendicular", "from": "D", "to": "AC", "foot": "F"},
        {"type": "collinear", "points": ["A", "E", "B"]},
        {"type": "collinear", "points": ["A", "F", "C"]},
        {"type": "circumcircle", "triangle": "AED", "name": "Ω"},
        {"type": "on_circle", "point": "F", "circle": "Ω"},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length", "line": "EF"}
}

# ===========================
# 실행
# ===========================
print("\n" + "="*40)
print("문제 1: BP 구하기")
print("="*40)
init_facts(facts1)
solve_problem(facts1)

print("\n" + "="*40)
print("문제 2: EF 구하기")
print("="*40)
init_facts(facts2)
solve_problem(facts2)
