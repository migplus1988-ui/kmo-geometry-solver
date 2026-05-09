
from sympy import Rational, sqrt, simplify, symbols, solve
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

def add_derived(facts, fact, reason):
    for d in facts["derived"]:
        if d == fact:
            return False
    facts["derived"].append(fact)
    facts["proof_steps"].append({"derived": fact, "reason": reason})
    print(f"  ✅ [{reason}]: {fact}")
    return True

def get_length(facts, p1, p2):
    result = get_constraint(facts, "length", line=p1+p2)
    if not result:
        result = get_constraint(facts, "length", line=p2+p1)
    return result

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
                val = simplify(f["value"] - s1["value"])
                if val > 0:
                    if add_derived(facts,
                        {"type": "length", "line": seg2, "value": val},
                        f"선분분할레마_{seg2}={full}-{seg1}"):
                        changed = True

            if f and s2 and not s1:
                val = simplify(f["value"] - s2["value"])
                if val > 0:
                    if add_derived(facts,
                        {"type": "length", "line": seg1, "value": val},
                        f"선분분할레마_{seg1}={full}-{seg2}"):
                        changed = True

            if s1 and s2 and not f:
                val = simplify(s1["value"] + s2["value"])
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
        all_pts = facts["entities"]["points"]

        for a in all_pts:
            if a == d or a == p1 or a == p2:
                continue
            ab = get_length(facts, a, p1)
            ac = get_length(facts, a, p2)
            ad = get_length(facts, a, d)
            bc = get_length(facts, p1, p2)

            if ab and ac and ad and not bc:
                val = simplify(sqrt(
                    2*(ab["value"]**2 + ac["value"]**2)
                    - 4*ad["value"]**2))
                if add_derived(facts,
                    {"type": "length", "line": p1+p2, "value": val},
                    f"중선정리_{p1+p2}"):
                    changed = True

            if ab and ac and bc and not ad:
                val = simplify(sqrt(
                    (2*ab["value"]**2 + 2*ac["value"]**2
                     - bc["value"]**2) / 4))
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
                            {"type": "area", "triangle": sub_tri,
                             "value": val},
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

        for other in [p1, p2]:
            l1 = get_length(facts, frm, foot)
            l2 = get_length(facts, foot, other)
            h  = get_length(facts, frm, other)

            if l1 and l2 and not h:
                val = simplify(sqrt(
                    l1["value"]**2 + l2["value"]**2))
                if add_derived(facts,
                    {"type": "length", "line": frm+other, "value": val},
                    f"피타고라스_{frm+other}"):
                    changed = True

            if l1 and h and not l2:
                diff = simplify(h["value"]**2 - l1["value"]**2)
                if diff > 0:
                    val = simplify(sqrt(diff))
                    if add_derived(facts,
                        {"type": "length", "line": foot+other, "value": val},
                        f"피타고라스_{foot+other}"):
                        changed = True

            if l2 and h and not l1:
                diff = simplify(h["value"]**2 - l2["value"]**2)
                if diff > 0:
                    val = simplify(sqrt(diff))
                    if add_derived(facts,
                        {"type": "length", "line": frm+foot, "value": val},
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
        ext_pts = [p for p in all_pts if p not in on_circle]
        collinears = [f for f in all_facts if f["type"] == "collinear"]

        for ext in ext_pts:
            secants = []
            for col in collinears:
                pts = col["points"]
                if ext not in pts:
                    continue
                on_cir_in_col = [p for p in pts if p in on_circle]
                ext_in_col    = [p for p in pts
                                 if p not in on_circle and p != ext]

                if len(on_cir_in_col) >= 2:
                    secants.append((on_cir_in_col[0], on_cir_in_col[1]))
                elif len(on_cir_in_col) == 1 and len(ext_in_col) == 1:
                    secants.append((on_cir_in_col[0], ext_in_col[0]))

            if len(secants) >= 2:
                for i in range(len(secants)):
                    for j in range(i+1, len(secants)):
                        s1 = secants[i]
                        s2 = secants[j]

                        ep1 = get_length(facts, ext, s1[0])
                        ep2 = get_length(facts, ext, s1[1])
                        ep3 = get_length(facts, ext, s2[0])
                        ep4 = get_length(facts, ext, s2[1])

                        if ep1 and ep2 and ep3 and not ep4:
                            val = simplify(
                                ep1["value"]*ep2["value"]/ep3["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s2[1], "value": val},
                                f"방멱정리_{ext+s2[1]}"):
                                changed = True

                        if ep1 and ep2 and ep4 and not ep3:
                            val = simplify(
                                ep1["value"]*ep2["value"]/ep4["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s2[0], "value": val},
                                f"방멱정리_{ext+s2[0]}"):
                                changed = True

                        if ep3 and ep4 and ep1 and not ep2:
                            val = simplify(
                                ep3["value"]*ep4["value"]/ep1["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s1[1], "value": val},
                                f"방멱정리_{ext+s1[1]}"):
                                changed = True

                        if ep3 and ep4 and ep2 and not ep1:
                            val = simplify(
                                ep3["value"]*ep4["value"]/ep2["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s1[0], "value": val},
                                f"방멱정리_{ext+s1[0]}"):
                                changed = True
    return changed

# ===========================
# 규칙 8: 방정식 풀기
# D가 원 밖, DA×DE = DB×DC
# DA = DE + EA → sympy
# ===========================
def rule_solve_power_equation(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    circles = [f for f in all_facts if f["type"] == "circumcircle"]

    for circle in circles:
        circle_name = circle["name"]
        on_circle = get_circle_points(facts, circle_name)
        all_pts = facts["entities"]["points"]
        ext_pts = [p for p in all_pts if p not in on_circle]
        collinears = [f for f in all_facts if f["type"] == "collinear"]

        for ext in ext_pts:
            ext_cols = [col for col in collinears
                        if ext in col["points"]]

            # 멱(power) 계산: 값 아는 할선에서
            power = None
            for col in ext_cols:
                pts = col["points"]
                on_cir = [p for p in pts if p in on_circle]
                if len(on_cir) == 2:
                    ep1 = get_length(facts, ext, on_cir[0])
                    ep2 = get_length(facts, ext, on_cir[1])
                    if ep1 and ep2:
                        power = simplify(ep1["value"] * ep2["value"])
                        break

            if power is None:
                continue

            # 모르는 할선에서 sympy로 풀기
            for col in ext_cols:
                pts = col["points"]
                on_cir = [p for p in pts if p in on_circle]
                if len(on_cir) != 2:
                    continue

                p1, p2 = on_cir[0], on_cir[1]
                ep1 = get_length(facts, ext, p1)
                ep2 = get_length(facts, ext, p2)
                p1p2 = get_length(facts, p1, p2)

                # 둘 다 모르고 p1p2 알면 sympy!
                if not ep1 and not ep2 and p1p2:
                    t = symbols('t', positive=True)
                    # t = ext-p2 (가까운쪽)
                    # t*(t+p1p2) = power
                    eq = t * (t + p1p2["value"]) - power
                    sol = solve(eq, t)
                    pos_sol = [s for s in sol if s > 0]

                    if pos_sol:
                        near_val = simplify(pos_sol[0])
                        far_val  = simplify(near_val + p1p2["value"])

                        # p2가 ext에 가까운 점
                        if add_derived(facts,
                            {"type": "length",
                             "line": ext+p2, "value": near_val},
                            f"방정식_{ext+p2}"):
                            changed = True
                        if add_derived(facts,
                            {"type": "length",
                             "line": ext+p1, "value": far_val},
                            f"방정식_{ext+p1}"):
                            changed = True
    return changed

# ===========================
# 규칙 9: 톨레미
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

            diag1 = get_length(facts, p1, p3)
            diag2 = get_length(facts, p2, p4)
            s12   = get_length(facts, p1, p2)
            s23   = get_length(facts, p2, p3)
            s34   = get_length(facts, p3, p4)
            s14   = get_length(facts, p1, p4)

            if s12 and s23 and s34 and s14:
                if diag2 and not diag1:
                    val = simplify(
                        (s12["value"]*s34["value"]
                         + s23["value"]*s14["value"])
                        / diag2["value"])
                    if add_derived(facts,
                        {"type": "length", "line": p1+p3, "value": val},
                        f"톨레미_{p1+p3}"):
                        changed = True

                if diag1 and not diag2:
                    val = simplify(
                        (s12["value"]*s34["value"]
                         + s23["value"]*s14["value"])
                        / diag1["value"])
                    if add_derived(facts,
                        {"type": "length", "line": p2+p4, "value": val},
                        f"톨레미_{p2+p4}"):
                        changed = True
    return changed

# ===========================
# 레마 1: 호 중점
# ===========================
def rule_arc_midpoint(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False

    equals = [f for f in all_facts if f["type"] == "equal_length"]

    for eq in equals:
        s1 = eq["seg1"]
        s2 = eq["seg2"]

        common = [p for p in s1 if p in s2]
        if not common:
            continue
        a = common[0]
        b = s1.replace(a, "")
        c = s2.replace(a, "")

        circles = [f for f in all_facts if f["type"] == "circumcircle"]
        for circle in circles:
            tri = circle["triangle"]
            if a in tri and b in tri and c in tri:
                fact = {
                    "type": "arc_midpoint",
                    "point": a,
                    "arc": b+c,
                    "circle": circle["name"]
                }
                if add_derived(facts, fact,
                    f"호중점_{a}는호{b}{c}중점"):
                    changed = True
    return changed

# ===========================
# 레마 2: 우산 정리
# ===========================
def rule_umbrella(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False

    arc_mids = [f for f in all_facts if f["type"] == "arc_midpoint"]

    for am in arc_mids:
        a = am["point"]
        arc = am["arc"]
        b, c = arc[0], arc[1]
        circle_name = am["circle"]
        on_circle = get_circle_points(facts, circle_name)

        collinears = [f for f in all_facts if f["type"] == "collinear"]

        # 직선BC 위의 모든 점
        bc_pts = set()
        for col in collinears:
            pts = col["points"]
            if b in pts or c in pts:
                for p in pts:
                    bc_pts.add(p)

        for d in bc_pts:
            if d == a or d == b or d == c:
                continue

            for e in on_circle:
                if e == a or e == b or e == c:
                    continue

                ac = get_length(facts, a, c)
                ae = get_length(facts, a, e)
                ad = get_length(facts, a, d)

                if ae and ad and not ac:
                    val = simplify(sqrt(
                        ae["value"] * ad["value"]))
                    if add_derived(facts,
                        {"type": "length", "line": a+c, "value": val},
                        f"우산정리_{a+c}²={a+e}×{a+d}"):
                        changed = True

                if ac and ae and not ad:
                    val = simplify(
                        ac["value"]**2 / ae["value"])
                    if add_derived(facts,
                        {"type": "length", "line": a+d, "value": val},
                        f"우산정리_{a+d}={a+c}²/{a+e}"):
                        changed = True

                if ac and ad and not ae:
                    val = simplify(
                        ac["value"]**2 / ad["value"])
                    if add_derived(facts,
                        {"type": "length", "line": a+e, "value": val},
                        f"우산정리_{a+e}={a+c}²/{a+d}"):
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

    elif target["type"] == "length_squared":
        result = get_length(facts,
                           target["line"][0],
                           target["line"][1])
        if result:
            val = simplify(result["value"]**2)
            print(f"\n  ✅ {target['line']}² = {val}")
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
        "name": "방정식풀기",
        "can_apply": lambda f:
            any(c["type"] == "circumcircle"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_solve_power_equation
    },
    {
        "name": "톨레미",
        "can_apply": lambda f:
            any(c["type"] == "circumcircle"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_ptolemy
    },
    {
        "name": "호중점",
        "can_apply": lambda f:
            any(c["type"] == "equal_length"
                for c in f["constraints"] + f["derived"])
            and any(c["type"] == "circumcircle"
                    for c in f["constraints"] + f["derived"]),
        "apply": rule_arc_midpoint
    },
    {
        "name": "우산정리",
        "can_apply": lambda f:
            any(c["type"] == "arc_midpoint"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_umbrella
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
# 문제 3: AC² 구하기
# ===========================
facts3 = {
    "entities": {
        "points": ["A", "B", "C", "E", "D"],
        "lines": ["AB", "BC", "CE", "AE", "AC", "AD"],
        "triangles": ["ABC", "ACE", "ADC"],
        "circles": ["Ω"]
    },
    "constraints": [
        {"type": "equal_length", "seg1": "AB", "seg2": "AC"},
        {"type": "length", "line": "BC", "value": Rational(11)},
        {"type": "length", "line": "AE", "value": Rational(16)},
        {"type": "length", "line": "CD", "value": Rational(5)},
        {"type": "collinear", "points": ["B", "C", "D"]},
        {"type": "collinear", "points": ["A", "E", "D"]},
        {"type": "circumcircle", "triangle": "ABC", "name": "Ω"},
        {"type": "on_circle", "point": "E", "circle": "Ω"},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length_squared", "line": "AC"}
}

# ===========================
# 실행
# ===========================
print("\n" + "="*40)
print("문제 3: AC² 구하기")
print("="*40)
init_facts(facts3)
solve_problem(facts3)
