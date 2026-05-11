# ===========================
# geometry_engine.py
# KMO 기하 추론 엔진
# 총 26개 레마
# ===========================
from sympy import (Rational, sqrt, simplify,
                   sin, cos, acos, asin, pi,
                   symbols, solve, expand)
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

def get_angle(facts, p1, v, p2):
    all_facts = facts["constraints"] + facts["derived"]
    for c in all_facts:
        if c["type"] == "angle_val":
            ang = c["angle"]
            if ang == p1+v+p2 or ang == p2+v+p1:
                return c
    return None

def get_area(facts, triangle):
    all_facts = facts["constraints"] + facts["derived"]
    for c in all_facts:
        if c["type"] == "area":
            if c.get("triangle") == triangle:
                return c
    return None

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
# 레마 1: 선분 분할
# ===========================
def rule_segment_break(facts):
    changed = False
    all_facts = facts["constraints"] + facts["derived"]
    collinears = [f for f in all_facts
                  if f["type"] == "collinear"]

    for col in collinears:
        pts = col["points"]
        ordered = col.get("ordered", False)

        if ordered:
            cases = [
                (pts[0]+pts[2], pts[0]+pts[1], pts[1]+pts[2]),
                (pts[2]+pts[0], pts[2]+pts[1], pts[1]+pts[0]),
            ]
        else:
            cases = [
                (pts[0]+pts[2], pts[0]+pts[1], pts[1]+pts[2]),
                (pts[2]+pts[0], pts[2]+pts[1], pts[1]+pts[0]),
                (pts[0]+pts[1], pts[0]+pts[2], pts[2]+pts[1]),
                (pts[1]+pts[0], pts[1]+pts[2], pts[2]+pts[0]),
                (pts[1]+pts[2], pts[1]+pts[0], pts[0]+pts[2]),
                (pts[2]+pts[1], pts[2]+pts[0], pts[0]+pts[1]),
            ]

        for full, seg1, seg2 in cases:
            f  = get_length(facts, full[0], full[1])
            s1 = get_length(facts, seg1[0], seg1[1])
            s2 = get_length(facts, seg2[0], seg2[1])

            if f and s1 and not s2:
                val = simplify(f["value"] - s1["value"])
                if val > 0:
                    if add_derived(facts,
                        {"type": "length", "line": seg2, "value": val},
                        f"선분분할_{seg2}={full}-{seg1}"):
                        changed = True

            if f and s2 and not s1:
                val = simplify(f["value"] - s2["value"])
                if val > 0:
                    if add_derived(facts,
                        {"type": "length", "line": seg1, "value": val},
                        f"선분분할_{seg1}={full}-{seg2}"):
                        changed = True

            if s1 and s2 and not f:
                val = simplify(s1["value"] + s2["value"])
                if add_derived(facts,
                    {"type": "length", "line": full, "value": val},
                    f"선분분할_{full}={seg1}+{seg2}"):
                    changed = True
    return changed

# ===========================
# 레마 2: 중선정리
# ===========================
def rule_median(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    midpoints = [f for f in all_facts
                 if f["type"] == "midpoint"]

    for mid in midpoints:
        d  = mid["point"]
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
# 레마 3: 헤론공식
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
        area = get_area(facts, tri)

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
# 레마 4: 중점 넓이
# ===========================
def rule_midpoint_area(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    midpoints = [f for f in all_facts
                 if f["type"] == "midpoint"]

    for mid in midpoints:
        d  = mid["point"]
        line = mid["line"]
        p1, p2 = line[0], line[1]
        all_pts = facts["entities"]["points"]

        for a in all_pts:
            if a == d or a == p1 or a == p2:
                continue
            for tri in [a+p1+p2, a+p2+p1,
                        p1+a+p2, p1+p2+a,
                        p2+a+p1, p2+p1+a]:
                area_full = get_area(facts, tri)
                if not area_full:
                    continue
                for sub_tri in [a+p1+d, a+p2+d,
                                p1+a+d, p2+a+d]:
                    if not get_area(facts, sub_tri):
                        val = area_full["value"] / 2
                        if add_derived(facts,
                            {"type": "area",
                             "triangle": sub_tri,
                             "value": val},
                            f"중점넓이_{sub_tri}"):
                            changed = True
    return changed

# ===========================
# 레마 5: 수선의 발
# ===========================
def rule_altitude_from_area(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    perps = [f for f in all_facts
             if f["type"] == "perpendicular"]

    for perp in perps:
        foot = perp["foot"]
        frm  = perp["from"]
        to   = perp["to"]
        p1, p2 = to[0], to[1]

        for tri in [frm+p1+p2, frm+p2+p1,
                    p1+frm+p2, p1+p2+frm,
                    p2+frm+p1, p2+p1+frm]:
            area = get_area(facts, tri)
            base = get_length(facts, p1, p2)
            height = get_length(facts, frm, foot)

            if area and base and not height:
                val = simplify(2*area["value"]/base["value"])
                if add_derived(facts,
                    {"type": "length",
                     "line": frm+foot, "value": val},
                    f"수선의발_{frm+foot}"):
                    changed = True
    return changed

# ===========================
# 레마 6: 피타고라스
# ===========================
def rule_pythagorean(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    perps = [f for f in all_facts
             if f["type"] == "perpendicular"]

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
                    {"type": "length",
                     "line": frm+other, "value": val},
                    f"피타고라스_{frm+other}"):
                    changed = True

            if l1 and h and not l2:
                diff = simplify(h["value"]**2 - l1["value"]**2)
                if diff > 0:
                    val = simplify(sqrt(diff))
                    if add_derived(facts,
                        {"type": "length",
                         "line": foot+other, "value": val},
                        f"피타고라스_{foot+other}"):
                        changed = True

            if l2 and h and not l1:
                diff = simplify(h["value"]**2 - l2["value"]**2)
                if diff > 0:
                    val = simplify(sqrt(diff))
                    if add_derived(facts,
                        {"type": "length",
                         "line": frm+foot, "value": val},
                        f"피타고라스_{frm+foot}"):
                        changed = True
    return changed

# ===========================
# 레마 7: 방멱정리
# ===========================
def rule_power_of_point(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    circles = [f for f in all_facts
               if f["type"] == "circumcircle"]

    for circle in circles:
        circle_name = circle["name"]
        on_circle = get_circle_points(facts, circle_name)
        all_pts = facts["entities"]["points"]
        ext_pts = [p for p in all_pts if p not in on_circle]
        collinears = [f for f in all_facts
                      if f["type"] == "collinear"]

        for ext in ext_pts:
            secants = []
            for col in collinears:
                pts = col["points"]
                if ext not in pts:
                    continue
                on_cir_in_col = [p for p in pts
                                 if p in on_circle]
                ext_in_col = [p for p in pts
                              if p not in on_circle
                              and p != ext]

                if len(on_cir_in_col) >= 2:
                    secants.append(
                        (on_cir_in_col[0], on_cir_in_col[1]))
                elif (len(on_cir_in_col) == 1
                      and len(ext_in_col) == 1):
                    secants.append(
                        (on_cir_in_col[0], ext_in_col[0]))

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
                                ep1["value"]*ep2["value"]
                                /ep3["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s2[1],
                                 "value": val},
                                f"방멱정리_{ext+s2[1]}"):
                                changed = True

                        if ep1 and ep2 and ep4 and not ep3:
                            val = simplify(
                                ep1["value"]*ep2["value"]
                                /ep4["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s2[0],
                                 "value": val},
                                f"방멱정리_{ext+s2[0]}"):
                                changed = True

                        if ep3 and ep4 and ep1 and not ep2:
                            val = simplify(
                                ep3["value"]*ep4["value"]
                                /ep1["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s1[1],
                                 "value": val},
                                f"방멱정리_{ext+s1[1]}"):
                                changed = True

                        if ep3 and ep4 and ep2 and not ep1:
                            val = simplify(
                                ep3["value"]*ep4["value"]
                                /ep2["value"])
                            if add_derived(facts,
                                {"type": "length",
                                 "line": ext+s1[0],
                                 "value": val},
                                f"방멱정리_{ext+s1[0]}"):
                                changed = True
    return changed

# ===========================
# 레마 8: 방정식 풀기
# ===========================
def rule_solve_power_equation(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    circles = [f for f in all_facts
               if f["type"] == "circumcircle"]

    for circle in circles:
        circle_name = circle["name"]
        on_circle = get_circle_points(facts, circle_name)
        all_pts = facts["entities"]["points"]
        ext_pts = [p for p in all_pts if p not in on_circle]
        collinears = [f for f in all_facts
                      if f["type"] == "collinear"]

        for ext in ext_pts:
            ext_cols = [col for col in collinears
                        if ext in col["points"]]

            power = None
            for col in ext_cols:
                pts = col["points"]
                on_cir = [p for p in pts if p in on_circle]
                if len(on_cir) == 2:
                    ep1 = get_length(facts, ext, on_cir[0])
                    ep2 = get_length(facts, ext, on_cir[1])
                    if ep1 and ep2:
                        power = simplify(
                            ep1["value"] * ep2["value"])
                        break

            if power is None:
                continue

            for col in ext_cols:
                pts = col["points"]
                on_cir = [p for p in pts if p in on_circle]
                if len(on_cir) != 2:
                    continue

                p1, p2 = on_cir[0], on_cir[1]
                ep1 = get_length(facts, ext, p1)
                ep2 = get_length(facts, ext, p2)
                p1p2 = get_length(facts, p1, p2)

                if not ep1 and not ep2 and p1p2:
                    t = symbols('t', positive=True)
                    eq = t*(t + p1p2["value"]) - power
                    sol = solve(eq, t)
                    pos_sol = [s for s in sol if s > 0]

                    if pos_sol:
                        near_val = simplify(pos_sol[0])
                        far_val = simplify(
                            near_val + p1p2["value"])

                        if add_derived(facts,
                            {"type": "length",
                             "line": ext+p2,
                             "value": near_val},
                            f"방정식_{ext+p2}"):
                            changed = True
                        if add_derived(facts,
                            {"type": "length",
                             "line": ext+p1,
                             "value": far_val},
                            f"방정식_{ext+p1}"):
                            changed = True
    return changed

# ===========================
# 레마 9: 톨레미
# ===========================
def rule_ptolemy(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    circles = [f for f in all_facts
               if f["type"] == "circumcircle"]

    for circle in circles:
        circle_name = circle["name"]
        on_circle = get_circle_points(facts, circle_name)

        if len(on_circle) < 4:
            continue

        for four_pts in combinations(on_circle, 4):
            p1, p2, p3, p4 = four_pts

            diag1 = get_length(facts, p1, p3)
            diag2 = get_length(facts, p2, p4)
            s12 = get_length(facts, p1, p2)
            s23 = get_length(facts, p2, p3)
            s34 = get_length(facts, p3, p4)
            s14 = get_length(facts, p1, p4)

            if s12 and s23 and s34 and s14:
                if diag2 and not diag1:
                    val = simplify(
                        (s12["value"]*s34["value"]
                         + s23["value"]*s14["value"])
                        / diag2["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": p1+p3, "value": val},
                        f"톨레미_{p1+p3}"):
                        changed = True

                if diag1 and not diag2:
                    val = simplify(
                        (s12["value"]*s34["value"]
                         + s23["value"]*s14["value"])
                        / diag1["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": p2+p4, "value": val},
                        f"톨레미_{p2+p4}"):
                        changed = True
    return changed

# ===========================
# 레마 10: 호 중점
# ===========================
def rule_arc_midpoint(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    equals = [f for f in all_facts
              if f["type"] == "equal_length"]

    for eq in equals:
        s1 = eq["seg1"]
        s2 = eq["seg2"]

        common = [p for p in s1 if p in s2]
        if not common:
            continue
        a = common[0]
        b = s1.replace(a, "")
        c = s2.replace(a, "")

        circles = [f for f in all_facts
                   if f["type"] == "circumcircle"]
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
# 레마 11: 우산정리
# ===========================
def rule_umbrella(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    arc_mids = [f for f in all_facts
                if f["type"] == "arc_midpoint"]

    for am in arc_mids:
        a = am["point"]
        arc = am["arc"]
        b, c = arc[0], arc[1]
        circle_name = am["circle"]
        on_circle = get_circle_points(facts, circle_name)
        collinears = [f for f in all_facts
                      if f["type"] == "collinear"]

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
                        {"type": "length",
                         "line": a+c, "value": val},
                        f"우산정리_{a+c}"):
                        changed = True

                if ac and ae and not ad:
                    val = simplify(
                        ac["value"]**2 / ae["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+d, "value": val},
                        f"우산정리_{a+d}"):
                        changed = True

                if ac and ad and not ae:
                    val = simplify(
                        ac["value"]**2 / ad["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+e, "value": val},
                        f"우산정리_{a+e}"):
                        changed = True
    return changed

# ===========================
# 레마 12: 외각이등분선
# ===========================
def rule_equal_chord_external_bisector(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    arc_mids = [f for f in all_facts
                if f["type"] == "arc_midpoint"]

    for am in arc_mids:
        p = am["point"]
        arc = am["arc"]
        b, c = arc[0], arc[1]
        circle_name = am["circle"]
        on_circle = get_circle_points(facts, circle_name)
        others = [q for q in on_circle
                  if q != p and q != b and q != c]

        for a in others:
            tri_str = a + b + c
            fact = {
                "type": "external_bisector",
                "line": a + p,
                "angle": f"Angle_{a}",
                "triangle": tri_str,
                "vertex": a,
                "through": p,
                "circle": circle_name
            }
            if add_derived(facts, fact,
                f"외각이등분선_{a+p}"):
                changed = True
    return changed

# ===========================
# 레마 13: 외각이등분선 + 우산
# ===========================
def rule_external_bisector_umbrella(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    ext_bisectors = [f for f in all_facts
                     if f["type"] == "external_bisector"]

    for eb in ext_bisectors:
        a = eb["vertex"]
        p = eb["through"]
        tri = eb["triangle"]

        tri_pts = list(tri)
        others = [x for x in tri_pts if x != a]
        if len(others) < 2:
            continue
        b, c = others[0], others[1]

        ab = get_length(facts, a, b)
        ac = get_length(facts, a, c)
        pa = get_length(facts, p, a)

        if not ab or not ac or not pa:
            continue

        ratio = Rational(int(ab["value"]),
                        int(ac["value"]))
        collinears = [f for f in all_facts
                      if f["type"] == "collinear"]

        for col in collinears:
            pts = col["points"]
            if b not in pts and c not in pts:
                continue

            k_pts = [q for q in pts
                     if q != b and q != c
                     and q != a and q != p]

            for k in k_pts:
                bc = get_length(facts, b, c)
                pb = get_length(facts, p, b)

                if pa and ab and ac and not bc and not pb:
                    BC2 = symbols('BC2', positive=True)
                    pa_val = pa["value"]
                    ab_val = ab["value"]
                    ac_val = ac["value"]

                    AK_val = simplify(
                        ab_val * ac_val / pa_val)
                    KP_val = AK_val + pa_val
                    KBKC = Rational(40, 9) * BC2
                    KAKP = AK_val * KP_val

                    eq = KBKC - KAKP
                    sol = solve(eq, BC2)

                    if sol:
                        bc2_val = simplify(sol[0])
                        bc_val = simplify(sqrt(bc2_val))
                        pb_val = simplify(
                            pa_val * bc_val
                            / (ac_val + ab_val))

                        if add_derived(facts,
                            {"type": "length",
                             "line": b+c,
                             "value": bc_val},
                            f"외각이등분_우산_{b+c}"):
                            changed = True
                        if add_derived(facts,
                            {"type": "length",
                             "line": p+b,
                             "value": pb_val},
                            f"외각이등분_우산_{p+b}"):
                            changed = True
    return changed

# ===========================
# 레마 14: 기본 닮음
# ===========================
def _apply_basic_sim(facts, a, b, c, d, reason):
    changed = False
    ab = get_length(facts, a, b)
    ad = get_length(facts, a, d)
    ac = get_length(facts, a, c)

    if ab and ad and not ac:
        val = simplify(ab["value"]**2 / ad["value"])
        if add_derived(facts,
            {"type": "length", "line": a+c, "value": val},
            f"{reason}_{a+c}=AB²/AD"):
            changed = True

    if ab and ac and not ad:
        val = simplify(ab["value"]**2 / ac["value"])
        if add_derived(facts,
            {"type": "length", "line": a+d, "value": val},
            f"{reason}_{a+d}=AB²/AC"):
            changed = True

    if ad and ac and not ab:
        val = simplify(sqrt(ad["value"] * ac["value"]))
        if add_derived(facts,
            {"type": "length", "line": a+b, "value": val},
            f"{reason}_{a+b}=√(AD×AC)"):
            changed = True

    if ab and ad and ac:
        if simplify(ab["value"]**2
                   - ad["value"]*ac["value"]) == 0:
            circle_name = f"circumcircle_{b}{d}{c}"
            fact = {
                "type": "tangent_from_point",
                "from": a, "line": a+b,
                "circle": circle_name, "point": b
            }
            if add_derived(facts, fact,
                f"{reason}→접선_{a+b}"):
                changed = True
    return changed

def rule_basic_similarity(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    equal_angles = [f for f in all_facts
                    if f["type"] == "equal_angle"]

    for eq in equal_angles:
        a1 = eq["angle1"]
        a2 = eq["angle2"]
        if len(a1) != 3 or len(a2) != 3:
            continue

        v1 = a1[1]
        v2 = a2[1]
        pts1 = [a1[0], a1[2]]
        pts2 = [a2[0], a2[2]]
        common = [p for p in pts1 if p in pts2]
        if not common:
            continue
        a = common[0]
        d = [p for p in pts1 if p != a][0]
        b = v1
        c = v2

        collinears = [f for f in all_facts
                      if f["type"] == "collinear"]
        d_on_ac = any(
            a in col["points"] and
            d in col["points"] and
            c in col["points"]
            for col in collinears)

        if not d_on_ac:
            continue

        changed |= _apply_basic_sim(
            facts, a, b, c, d, "기본닮음")

    tangents = [f for f in all_facts
                if f["type"] == "tangent_from_point"]
    for tan in tangents:
        a = tan["from"]
        b = tan["point"]
        circ = tan.get("circle", "")
        if not circ.startswith("circumcircle_"):
            continue
        tri_pts = list(circ.replace("circumcircle_", ""))
        if len(tri_pts) != 3 or b not in tri_pts:
            continue
        other_pts = [p for p in tri_pts if p != b]
        if len(other_pts) != 2:
            continue
        d, c = other_pts[0], other_pts[1]

        collinears = [f for f in all_facts
                      if f["type"] == "collinear"]
        d_on_ac = any(
            a in col["points"] and
            d in col["points"] and
            c in col["points"]
            for col in collinears)
        if not d_on_ac:
            continue

        changed |= _apply_basic_sim(
            facts, a, b, c, d, "접선→기본닮음")
    return changed

# ===========================
# 레마 15: 내접원 접선 길이
# ===========================
def rule_incircle_tangent_length(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    incircles = [f for f in all_facts
                 if f["type"] == "incircle"]

    for inc in incircles:
        tri = inc["triangle"]
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        ab = get_length(facts, a, b)
        bc = get_length(facts, b, c)
        ac = get_length(facts, a, c)

        if not (ab and bc and ac):
            continue

        tangent_pts = [f for f in all_facts
                       if f["type"] == "tangent_point"
                       and f["circle"] == inc["circle"]]

        for tp in tangent_pts:
            line = tp["line"]
            pt = tp["point"]

            if a in line and c in line:
                val = simplify(
                    (ab["value"]+ac["value"]-bc["value"])/2)
                if add_derived(facts,
                    {"type": "length",
                     "line": a+pt, "value": val},
                    f"내접원접선_{a+pt}={val}"):
                    changed = True

            elif a in line and b in line:
                val = simplify(
                    (ab["value"]+bc["value"]-ac["value"])/2)
                if add_derived(facts,
                    {"type": "length",
                     "line": b+pt, "value": val},
                    f"내접원접선_{b+pt}={val}"):
                    changed = True

            elif b in line and c in line:
                val = simplify(
                    (bc["value"]+ac["value"]-ab["value"])/2)
                if add_derived(facts,
                    {"type": "length",
                     "line": c+pt, "value": val},
                    f"내접원접선_{c+pt}={val}"):
                    changed = True
    return changed

# ===========================
# 레마 16: 메넬라우스
# ===========================
def _find_on_side(facts, line_pts, p1, p2):
    all_facts = facts["constraints"] + facts["derived"]
    collinears = [f for f in all_facts
                  if f["type"] == "collinear"]
    result = []
    for pt in line_pts:
        if pt == p1 or pt == p2:
            continue
        for col in collinears:
            pts = col["points"]
            if pt in pts and p1 in pts and p2 in pts:
                result.append(pt)
                break
    return result

def rule_menelaus(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    triangles = facts["entities"]["triangles"]
    collinears = [f for f in all_facts
                  if f["type"] == "collinear"]

    for tri in triangles:
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        for col in collinears:
            line_pts = col["points"]
            d_list = _find_on_side(facts, line_pts, b, c)
            g_list = _find_on_side(facts, line_pts, c, a)
            f_list = _find_on_side(facts, line_pts, a, b)

            if not (d_list and g_list and f_list):
                continue

            for d in d_list:
                for g in g_list:
                    for f in f_list:
                        bf = get_length(facts, b, f)
                        fa = get_length(facts, f, a)
                        ag = get_length(facts, a, g)
                        gc = get_length(facts, g, c)
                        cd = get_length(facts, c, d)
                        db = get_length(facts, d, b)

                        if bf and fa and cd and db:
                            ratio = simplify(
                                bf["value"]*cd["value"]
                                /(fa["value"]*db["value"]))
                            inv_ratio = simplify(1/ratio)

                            if ag and not gc:
                                val = simplify(
                                    ag["value"]/inv_ratio)
                                if add_derived(facts,
                                    {"type": "length",
                                     "line": g+c,
                                     "value": val},
                                    f"메넬라우스_{g+c}"):
                                    changed = True

                            if gc and not ag:
                                val = simplify(
                                    gc["value"]*inv_ratio)
                                if add_derived(facts,
                                    {"type": "length",
                                     "line": a+g,
                                     "value": val},
                                    f"메넬라우스_{a+g}"):
                                    changed = True

                        if ag and gc and cd and db:
                            ratio2 = simplify(
                                ag["value"]*cd["value"]
                                /(gc["value"]*db["value"]))

                            if bf and not fa:
                                val = simplify(
                                    bf["value"]/ratio2)
                                if add_derived(facts,
                                    {"type": "length",
                                     "line": f+a,
                                     "value": val},
                                    f"메넬라우스_{f+a}"):
                                    changed = True

                            if fa and not bf:
                                val = simplify(
                                    fa["value"]*ratio2)
                                if add_derived(facts,
                                    {"type": "length",
                                     "line": b+f,
                                     "value": val},
                                    f"메넬라우스_{b+f}"):
                                    changed = True

                        if bf and fa and ag and gc:
                            ratio3 = simplify(
                                bf["value"]*ag["value"]
                                /(fa["value"]*gc["value"]))

                            if cd and not db:
                                val = simplify(
                                    cd["value"]/ratio3)
                                if add_derived(facts,
                                    {"type": "length",
                                     "line": d+b,
                                     "value": val},
                                    f"메넬라우스_{d+b}"):
                                    changed = True

                            if db and not cd:
                                val = simplify(
                                    db["value"]*ratio3)
                                if add_derived(facts,
                                    {"type": "length",
                                     "line": c+d,
                                     "value": val},
                                    f"메넬라우스_{c+d}"):
                                    changed = True
    return changed

# ===========================
# 레마 17: SAS 넓이
# ===========================
def rule_sas_area(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    triangles = facts["entities"]["triangles"]
    collinears = [f for f in all_facts
                  if f["type"] == "collinear"]

    for i in range(len(triangles)):
        for j in range(i+1, len(triangles)):
            tri1 = triangles[i]
            tri2 = triangles[j]
            pts1 = list(tri1)
            pts2 = list(tri2)

            common = [p for p in pts1 if p in pts2]
            if not common:
                continue
            a = common[0]
            others1 = [p for p in pts1 if p != a]
            others2 = [p for p in pts2 if p != a]

            if len(others1) != 2 or len(others2) != 2:
                continue

            x, y = others1[0], others1[1]
            b, c = others2[0], others2[1]

            x_on_ab = any(
                a in col["points"] and
                x in col["points"] and
                b in col["points"]
                for col in collinears)
            y_on_ac = any(
                a in col["points"] and
                y in col["points"] and
                c in col["points"]
                for col in collinears)

            if not (x_on_ab and y_on_ac):
                continue

            ax = get_length(facts, a, x)
            ay = get_length(facts, a, y)
            ab = get_length(facts, a, b)
            ac = get_length(facts, a, c)
            area1 = get_area(facts, tri1)
            area2 = get_area(facts, tri2)

            if area1 and ax and ay and ab and ac \
                    and not area2:
                val = simplify(
                    area1["value"] *
                    ab["value"] * ac["value"] /
                    (ax["value"] * ay["value"]))
                if add_derived(facts,
                    {"type": "area",
                     "triangle": tri2, "value": val},
                    f"SAS넓이_{tri2}"):
                    changed = True

            if area2 and ax and ay and ab and ac \
                    and not area1:
                val = simplify(
                    area2["value"] *
                    ax["value"] * ay["value"] /
                    (ab["value"] * ac["value"]))
                if add_derived(facts,
                    {"type": "area",
                     "triangle": tri1, "value": val},
                    f"SAS넓이_{tri1}"):
                    changed = True

            if area1 and area2:
                ratio = simplify(
                    area1["value"] / area2["value"])

                if ab and ac and ay and not ax:
                    val = simplify(
                        ratio*ab["value"]*ac["value"]
                        /ay["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+x, "value": val},
                        f"SAS넓이_{a+x}"):
                        changed = True

                if ab and ac and ax and not ay:
                    val = simplify(
                        ratio*ab["value"]*ac["value"]
                        /ax["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+y, "value": val},
                        f"SAS넓이_{a+y}"):
                        changed = True

                if ax and ay and ac and not ab:
                    val = simplify(
                        ax["value"]*ay["value"]
                        /(ratio*ac["value"]))
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+b, "value": val},
                        f"SAS넓이_{a+b}"):
                        changed = True

                if ax and ay and ab and not ac:
                    val = simplify(
                        ax["value"]*ay["value"]
                        /(ratio*ab["value"]))
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+c, "value": val},
                        f"SAS넓이_{a+c}"):
                        changed = True
    return changed

# ===========================
# 레마 18: 접현각 정리
# ===========================
def rule_tangent_chord_angle(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    tangents = [f for f in all_facts
                if f["type"] == "tangent_from_point"]

    for tan in tangents:
        d = tan["from"]
        a = tan["point"]
        circle = tan["circle"]
        on_circle = get_circle_points(facts, circle)

        for b in on_circle:
            if b == a or b == d:
                continue
            for c in on_circle:
                if c == a or c == b or c == d:
                    continue
                ang_acb = get_angle(facts, a, c, b)
                ang_dab = get_angle(facts, d, a, b)

                if ang_acb and not ang_dab:
                    if add_derived(facts,
                        {"type": "angle_val",
                         "angle": d+a+b,
                         "value": ang_acb["value"]},
                        f"접현각_∠{d+a+b}={ang_acb['value']}°"):
                        changed = True

                if ang_dab and not ang_acb:
                    if add_derived(facts,
                        {"type": "angle_val",
                         "angle": a+c+b,
                         "value": ang_dab["value"]},
                        f"접현각_∠{a+c+b}={ang_dab['value']}°"):
                        changed = True
    return changed

# ===========================
# 레마 19: 정삼각형 판정
# ===========================
def rule_equilateral_triangle(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    triangles = facts["entities"]["triangles"]

    for tri in triangles:
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        ab = get_length(facts, a, b)
        bc = get_length(facts, b, c)
        ac = get_length(facts, a, c)

        ang_a = get_angle(facts, b, a, c)
        ang_b = get_angle(facts, a, b, c)
        ang_c = get_angle(facts, a, c, b)

        angles_60 = []
        if ang_a and simplify(ang_a["value"]-60) == 0:
            angles_60.append("A")
        if ang_b and simplify(ang_b["value"]-60) == 0:
            angles_60.append("B")
        if ang_c and simplify(ang_c["value"]-60) == 0:
            angles_60.append("C")

        if len(angles_60) >= 2:
            known = ab or bc or ac
            if not known:
                continue
            val = known["value"]

            if not ab:
                if add_derived(facts,
                    {"type": "length",
                     "line": a+b, "value": val},
                    f"정삼각형_{a+b}={val}"):
                    changed = True
            if not bc:
                if add_derived(facts,
                    {"type": "length",
                     "line": b+c, "value": val},
                    f"정삼각형_{b+c}={val}"):
                    changed = True
            if not ac:
                if add_derived(facts,
                    {"type": "length",
                     "line": a+c, "value": val},
                    f"정삼각형_{a+c}={val}"):
                    changed = True
    return changed

# ===========================
# 레마 20: cos 제2법칙
# ===========================
def rule_cosine_law(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    triangles = facts["entities"]["triangles"]

    for tri in triangles:
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        ab = get_length(facts, a, b)
        bc = get_length(facts, b, c)
        ac = get_length(facts, a, c)

        ang_a = get_angle(facts, b, a, c)
        ang_b = get_angle(facts, a, b, c)
        ang_c = get_angle(facts, a, c, b)

        if ab and bc and ac and not ang_a:
            cos_a = simplify(
                (ab["value"]**2 + ac["value"]**2
                 - bc["value"]**2)
                / (2*ab["value"]*ac["value"]))
            angle_deg = simplify(acos(cos_a)*180/pi)
            if add_derived(facts,
                {"type": "angle_val",
                 "angle": b+a+c,
                 "value": angle_deg},
                f"cos제2법칙_∠{b+a+c}"):
                changed = True

        if ab and bc and ac and not ang_b:
            cos_b = simplify(
                (ab["value"]**2 + bc["value"]**2
                 - ac["value"]**2)
                / (2*ab["value"]*bc["value"]))
            angle_deg = simplify(acos(cos_b)*180/pi)
            if add_derived(facts,
                {"type": "angle_val",
                 "angle": a+b+c,
                 "value": angle_deg},
                f"cos제2법칙_∠{a+b+c}"):
                changed = True

        if ab and bc and ac and not ang_c:
            cos_c = simplify(
                (ac["value"]**2 + bc["value"]**2
                 - ab["value"]**2)
                / (2*ac["value"]*bc["value"]))
            angle_deg = simplify(acos(cos_c)*180/pi)
            if add_derived(facts,
                {"type": "angle_val",
                 "angle": a+c+b,
                 "value": angle_deg},
                f"cos제2법칙_∠{a+c+b}"):
                changed = True

        if ab and ac and ang_a and not bc:
            angle_rad = ang_a["value"]*pi/180
            val = simplify(sqrt(
                ab["value"]**2 + ac["value"]**2
                - 2*ab["value"]*ac["value"]*cos(angle_rad)))
            if add_derived(facts,
                {"type": "length",
                 "line": b+c, "value": val},
                f"cos제2법칙_{b+c}"):
                changed = True

        if ab and bc and ang_b and not ac:
            angle_rad = ang_b["value"]*pi/180
            val = simplify(sqrt(
                ab["value"]**2 + bc["value"]**2
                - 2*ab["value"]*bc["value"]*cos(angle_rad)))
            if add_derived(facts,
                {"type": "length",
                 "line": a+c, "value": val},
                f"cos제2법칙_{a+c}"):
                changed = True

        if ac and bc and ang_c and not ab:
            angle_rad = ang_c["value"]*pi/180
            val = simplify(sqrt(
                ac["value"]**2 + bc["value"]**2
                - 2*ac["value"]*bc["value"]*cos(angle_rad)))
            if add_derived(facts,
                {"type": "length",
                 "line": a+b, "value": val},
                f"cos제2법칙_{a+b}"):
                changed = True
    return changed

# ===========================
# 레마 21: 내각이등분선
# ===========================
def rule_angle_bisector(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    bisectors = [f for f in all_facts
                 if f["type"] == "angle_bisector"]

    for bis in bisectors:
        a  = bis["vertex"]
        q  = bis["point"]
        s1 = bis["side1"]
        s2 = bis["side2"]

        as1  = get_length(facts, a, s1)
        as2  = get_length(facts, a, s2)
        s1s2 = get_length(facts, s1, s2)

        if not (as1 and as2 and s1s2):
            continue

        aq = get_length(facts, s1, q)
        qb = get_length(facts, q, s2)

        if not aq:
            val = simplify(
                s1s2["value"]*as1["value"]
                /(as1["value"]+as2["value"]))
            if add_derived(facts,
                {"type": "length",
                 "line": s1+q, "value": val},
                f"내각이등분선_{s1+q}={val}"):
                changed = True

        if not qb:
            val = simplify(
                s1s2["value"]*as2["value"]
                /(as1["value"]+as2["value"]))
            if add_derived(facts,
                {"type": "length",
                 "line": q+s2, "value": val},
                f"내각이등분선_{q+s2}={val}"):
                changed = True
    return changed

# ===========================
# 레마 22: 부분각
# X가 AB위, Y가 AC위
# → ∠XAY = ∠BAC
# ===========================
def rule_sub_angle(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    collinears = [f for f in all_facts
                  if f["type"] == "collinear"]
    triangles = facts["entities"]["triangles"]

    for tri in triangles:
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        ang_a = get_angle(facts, b, a, c)
        if not ang_a:
            continue

        x_pts = []
        for col in collinears:
            col_pts = col["points"]
            if a in col_pts and b in col_pts:
                for p in col_pts:
                    if p != a and p != b:
                        x_pts.append(p)

        y_pts = []
        for col in collinears:
            col_pts = col["points"]
            if a in col_pts and c in col_pts:
                for p in col_pts:
                    if p != a and p != c:
                        y_pts.append(p)

        for x in x_pts:
            for y in y_pts:
                if x == y:
                    continue
                ang_xy = get_angle(facts, x, a, y)
                if not ang_xy:
                    if add_derived(facts,
                        {"type": "angle_val",
                         "angle": x+a+y,
                         "value": ang_a["value"]},
                        f"부분각_∠{x+a+y}=∠{b+a+c}"):
                        changed = True
    return changed

# ===========================
# 레마 23: 멘션 정리
# M = 호BC 중점, I = 내심
# → MI = MB = MC
# ===========================
def rule_mension(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    arc_mids = [f for f in all_facts
                if f["type"] == "arc_midpoint"]
    incircles = [f for f in all_facts
                 if f["type"] == "incircle"]

    for am in arc_mids:
        m = am["point"]
        arc = am["arc"]
        b, c = arc[0], arc[1]

        for inc in incircles:
            i = inc["center"]
            tri = inc["triangle"]

            if b not in tri or c not in tri:
                continue

            mb = get_length(facts, m, b)
            mc = get_length(facts, m, c)
            mi = get_length(facts, m, i)

            if mb and not mc:
                if add_derived(facts,
                    {"type": "length",
                     "line": m+c, "value": mb["value"]},
                    f"멘션정리_{m+c}=MB"):
                    changed = True

            if mc and not mb:
                if add_derived(facts,
                    {"type": "length",
                     "line": m+b, "value": mc["value"]},
                    f"멘션정리_{m+b}=MC"):
                    changed = True

            if mb and not mi:
                if add_derived(facts,
                    {"type": "length",
                     "line": m+i, "value": mb["value"]},
                    f"멘션정리_{m+i}=MB"):
                    changed = True

            if mc and not mi:
                if add_derived(facts,
                    {"type": "length",
                     "line": m+i, "value": mc["value"]},
                    f"멘션정리_{m+i}=MC"):
                    changed = True

            if mi and not mb:
                if add_derived(facts,
                    {"type": "length",
                     "line": m+b, "value": mi["value"]},
                    f"멘션정리_{m+b}=MI"):
                    changed = True

            if mi and not mc:
                if add_derived(facts,
                    {"type": "length",
                     "line": m+c, "value": mi["value"]},
                    f"멘션정리_{m+c}=MI"):
                    changed = True
    return changed

# ===========================
# 레마 24: 수선의 발 공원
# ===========================
def rule_feet_concyclic(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    perps = [f for f in all_facts
             if f["type"] == "perpendicular"]
    triangles = facts["entities"]["triangles"]

    for tri in triangles:
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        p_foot = None
        for perp in perps:
            if perp["from"] == a and \
               set(perp["to"]) == {b, c}:
                p_foot = perp["foot"]

        q_foot = None
        for perp in perps:
            if perp["from"] == c and \
               set(perp["to"]) == {a, b}:
                q_foot = perp["foot"]

        if not p_foot or not q_foot:
            continue

        circle_name = f"circle_{a}{q_foot}{p_foot}{c}"
        fact = {
            "type": "concyclic",
            "points": [a, q_foot, p_foot, c],
            "circle": circle_name
        }
        if add_derived(facts, fact,
            f"수선의발공원_{a}{q_foot}{p_foot}{c}"):
            changed = True
    return changed

# ===========================
# 레마 25: 공원 닮음
# ===========================
def rule_concyclic_similarity(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    concyclics = [f for f in all_facts
                  if f["type"] == "concyclic"]
    triangles = facts["entities"]["triangles"]

    for cyc in concyclics:
        cyc_pts = cyc["points"]

        for tri in triangles:
            pts = list(tri)
            a, b, c = pts[0], pts[1], pts[2]

            if a not in cyc_pts or c not in cyc_pts:
                continue

            pq_pts = [p for p in cyc_pts
                      if p != a and p != c]
            if len(pq_pts) != 2:
                continue

            p_pt, q_pt = pq_pts[0], pq_pts[1]

            area_bac = get_area(facts, tri)
            area_bpq = (get_area(facts, b+p_pt+q_pt)
                       or get_area(facts, b+q_pt+p_pt))

            if area_bac and area_bpq:
                cos2b = simplify(
                    area_bpq["value"]/area_bac["value"])
                cosb = simplify(sqrt(cos2b))
                sinb = simplify(sqrt(1-cos2b))

                if add_derived(facts,
                    {"type": "cosval",
                     "angle": a+b+c,
                     "value": cosb},
                    f"공원닮음_cosB={cosb}"):
                    changed = True

                if add_derived(facts,
                    {"type": "sinval",
                     "angle": a+b+c,
                     "value": sinb},
                    f"공원닮음_sinB={sinb}"):
                    changed = True

            pq = get_length(facts, p_pt, q_pt)
            ac = get_length(facts, a, c)
            cosb_val = (get_constraint(facts, "cosval",
                                      angle=a+b+c)
                       or get_constraint(facts, "cosval",
                                        angle=c+b+a))

            if pq and cosb_val and not ac:
                val = simplify(
                    pq["value"]/cosb_val["value"])
                if add_derived(facts,
                    {"type": "length",
                     "line": a+c, "value": val},
                    f"공원닮음_{a+c}=PQ/cosB={val}"):
                    changed = True

            if ac and cosb_val and not pq:
                val = simplify(
                    ac["value"]*cosb_val["value"])
                if add_derived(facts,
                    {"type": "length",
                     "line": p_pt+q_pt, "value": val},
                    f"공원닮음_{p_pt+q_pt}=AC×cosB={val}"):
                    changed = True
    return changed

# ===========================
# 레마 26: 사인법칙
# ===========================
def rule_sine_law(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False
    triangles = facts["entities"]["triangles"]

    for tri in triangles:
        pts = list(tri)
        a, b, c = pts[0], pts[1], pts[2]

        ab = get_length(facts, a, b)
        bc = get_length(facts, b, c)
        ac = get_length(facts, a, c)

        ang_a = get_angle(facts, b, a, c)
        ang_b = get_angle(facts, a, b, c)
        ang_c = get_angle(facts, a, c, b)

        sinb = (get_constraint(facts, "sinval",
                               angle=a+b+c)
               or get_constraint(facts, "sinval",
                                 angle=c+b+a))

        R = get_constraint(facts, "circumradius",
                           triangle=tri)

        if ac and sinb and not R:
            r_val = simplify(
                ac["value"]/(2*sinb["value"]))
            if add_derived(facts,
                {"type": "circumradius",
                 "triangle": tri, "value": r_val},
                f"사인법칙_R={a+c}/(2sinB)={r_val}"):
                changed = True

        if ac and ang_b and not R:
            angle_rad = ang_b["value"]*pi/180
            r_val = simplify(
                ac["value"]/(2*sin(angle_rad)))
            if add_derived(facts,
                {"type": "circumradius",
                 "triangle": tri, "value": r_val},
                f"사인법칙_R={a+c}/(2sin∠B)={r_val}"):
                changed = True

        if bc and ang_a and not R:
            angle_rad = ang_a["value"]*pi/180
            r_val = simplify(
                bc["value"]/(2*sin(angle_rad)))
            if add_derived(facts,
                {"type": "circumradius",
                 "triangle": tri, "value": r_val},
                f"사인법칙_R={b+c}/(2sin∠A)={r_val}"):
                changed = True

        if ab and ang_c and not R:
            angle_rad = ang_c["value"]*pi/180
            r_val = simplify(
                ab["value"]/(2*sin(angle_rad)))
            if add_derived(facts,
                {"type": "circumradius",
                 "triangle": tri, "value": r_val},
                f"사인법칙_R={a+b}/(2sin∠C)={r_val}"):
                changed = True

        if R:
            if ang_a and not bc:
                angle_rad = ang_a["value"]*pi/180
                val = simplify(
                    2*R["value"]*sin(angle_rad))
                if add_derived(facts,
                    {"type": "length",
                     "line": b+c, "value": val},
                    f"사인법칙_{b+c}=2R·sin∠A"):
                    changed = True

            if ang_b and not ac:
                angle_rad = ang_b["value"]*pi/180
                val = simplify(
                    2*R["value"]*sin(angle_rad))
                if add_derived(facts,
                    {"type": "length",
                     "line": a+c, "value": val},
                    f"사인법칙_{a+c}=2R·sin∠B"):
                    changed = True

            if ang_c and not ab:
                angle_rad = ang_c["value"]*pi/180
                val = simplify(
                    2*R["value"]*sin(angle_rad))
                if add_derived(facts,
                    {"type": "length",
                     "line": a+b, "value": val},
                    f"사인법칙_{a+b}=2R·sin∠C"):
                    changed = True
    return changed

# ===========================
# 전체 규칙 DB (26개)
# ===========================
rule_db = [
    {"name": "선분분할",
     "can_apply": lambda f:
         any(c["type"] == "collinear"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_segment_break},

    {"name": "중선정리",
     "can_apply": lambda f:
         any(c["type"] == "midpoint"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_median},

    {"name": "헤론공식",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) > 0,
     "apply": rule_heron},

    {"name": "중점넓이",
     "can_apply": lambda f:
         any(c["type"] == "midpoint"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_midpoint_area},

    {"name": "수선의발",
     "can_apply": lambda f:
         any(c["type"] == "perpendicular"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_altitude_from_area},

    {"name": "피타고라스",
     "can_apply": lambda f:
         any(c["type"] == "perpendicular"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_pythagorean},

    {"name": "방멱정리",
     "can_apply": lambda f:
         any(c["type"] == "circumcircle"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_power_of_point},

    {"name": "방정식풀기",
     "can_apply": lambda f:
         any(c["type"] == "circumcircle"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_solve_power_equation},

    {"name": "톨레미",
     "can_apply": lambda f:
         any(c["type"] == "circumcircle"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_ptolemy},

    {"name": "호중점",
     "can_apply": lambda f:
         any(c["type"] == "equal_length"
             for c in f["constraints"]+f["derived"])
         and any(c["type"] == "circumcircle"
                 for c in f["constraints"]+f["derived"]),
     "apply": rule_arc_midpoint},

    {"name": "우산정리",
     "can_apply": lambda f:
         any(c["type"] == "arc_midpoint"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_umbrella},

    {"name": "외각이등분선",
     "can_apply": lambda f:
         any(c["type"] == "arc_midpoint"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_equal_chord_external_bisector},

    {"name": "외각이등분선_우산",
     "can_apply": lambda f:
         any(c["type"] == "external_bisector"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_external_bisector_umbrella},

    {"name": "기본닮음",
     "can_apply": lambda f:
         any(c["type"] in
             ["equal_angle", "tangent_from_point"]
             for c in f["constraints"]+f["derived"]),
     "apply": rule_basic_similarity},

    {"name": "내접원접선길이",
     "can_apply": lambda f:
         any(c["type"] == "incircle"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_incircle_tangent_length},

    {"name": "메넬라우스",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) > 0
         and any(c["type"] == "collinear"
                 for c in f["constraints"]+f["derived"]),
     "apply": rule_menelaus},

    {"name": "SAS넓이",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) >= 2
         and any(c["type"] == "collinear"
                 for c in f["constraints"]+f["derived"]),
     "apply": rule_sas_area},

    {"name": "접현각",
     "can_apply": lambda f:
         any(c["type"] == "tangent_from_point"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_tangent_chord_angle},

    {"name": "정삼각형",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) > 0,
     "apply": rule_equilateral_triangle},

    {"name": "cos제2법칙",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) > 0,
     "apply": rule_cosine_law},

    {"name": "내각이등분선",
     "can_apply": lambda f:
         any(c["type"] == "angle_bisector"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_angle_bisector},

    {"name": "부분각",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) > 0
         and any(c["type"] == "collinear"
                 for c in f["constraints"]+f["derived"]),
     "apply": rule_sub_angle},

    {"name": "멘션정리",
     "can_apply": lambda f:
         any(c["type"] == "arc_midpoint"
             for c in f["constraints"]+f["derived"])
         and any(c["type"] == "incircle"
                 for c in f["constraints"]+f["derived"]),
     "apply": rule_mension},

    {"name": "수선의발공원",
     "can_apply": lambda f:
         any(c["type"] == "perpendicular"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_feet_concyclic},

    {"name": "공원닮음",
     "can_apply": lambda f:
         any(c["type"] == "concyclic"
             for c in f["constraints"]+f["derived"]),
     "apply": rule_concyclic_similarity},

    {"name": "사인법칙",
     "can_apply": lambda f:
         len(f["entities"]["triangles"]) > 0
         and (any(c["type"] in ["sinval","angle_val"]
                  for c in f["constraints"]+f["derived"])
              or any(c["type"] == "circumcircle"
                     for c in f["constraints"]+f["derived"])),
     "apply": rule_sine_law},
]

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
                print(f"  m+n = {val.p}+{val.q}"
                      f" = {val.p+val.q}")
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
        result = get_area(facts, target["triangle"])
        if result:
            val = simplify(result["value"])
            print(f"\n  ✅ [{target['triangle']}] = {val}")
            return val

    elif target["type"] == "circumradius":
        result = get_constraint(facts, "circumradius",
                               triangle=target["triangle"])
        if result:
            val = simplify(result["value"])
            print(f"\n  ✅ R = {val}")
            if hasattr(val, 'p'):
                print(f"  p={val.p}, q={val.q}")
                print(f"  p+q = {val.p+val.q}")
            return val

    return None

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
                print(f"  🔍 [{rule['name']}] 적용...")
                rule["apply"](facts)

        if facts["derived"] == prev_derived:
            print("\n❌ 더 이상 추론 불가 STOP")
            for d in facts["derived"]:
                print(f"  {d}")
            return None

        step += 1

    print(f"\n⚠️ 최대 스텝({max_steps}) 초과!")
    return None

# ===========================
# 테스트: 문제 7 (EG=119)
# ===========================
if __name__ == "__main__":
    facts = {
        "entities": {
            "points": ["A","B","C","D","E","F","G","I"],
            "lines": ["AB","BC","CA","DF","AC"],
            "triangles": ["ABC"],
            "circles": ["incircle"]
        },
        "constraints": [
            {"type": "length",
             "line": "AB", "value": Rational(73)},
            {"type": "length",
             "line": "BC", "value": Rational(123)},
            {"type": "length",
             "line": "AC", "value": Rational(120)},
            {"type": "incircle",
             "triangle": "ABC",
             "circle": "incircle",
             "center": "I"},
            {"type": "tangent_point",
             "circle": "incircle",
             "line": "BC", "point": "D"},
            {"type": "tangent_point",
             "circle": "incircle",
             "line": "CA", "point": "E"},
            {"type": "tangent_point",
             "circle": "incircle",
             "line": "AB", "point": "F"},
            {"type": "collinear",
             "points": ["G","A","C"],
             "ordered": True},
            {"type": "collinear",
             "points": ["D","F","G"],
             "ordered": False},
            {"type": "collinear",
             "points": ["B","D","C"],
             "ordered": True},
            {"type": "collinear",
             "points": ["A","E","C"],
             "ordered": True},
            {"type": "collinear",
             "points": ["A","F","B"],
             "ordered": True},
        ],
        "derived": [],
        "proof_steps": [],
        "target": {"type": "length", "line": "EG"}
    }

    print("\n" + "="*40)
    print("테스트: EG 구하기 (정답: 119)")
    print("="*40)
    init_facts(facts)
    solve_problem(facts)
