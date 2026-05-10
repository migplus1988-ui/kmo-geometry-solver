from sympy import Rational, sqrt, simplify, symbols, solve

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
# 레마 1: 기본 닮음 (완전판)
# D가 AC위
# ⇔ ∠ABD = ∠ACB
# ⇔ △ABD ∽ △ACB
# ⇔ AB² = AD × AC
# ⇔ AB는 △BDC 외접원에 접선
# ===========================
def _apply_basic_sim(facts, a, b, c, d, reason):
    changed = False

    ab = get_length(facts, a, b)
    ad = get_length(facts, a, d)
    ac = get_length(facts, a, c)

    # AC = AB²/AD
    if ab and ad and not ac:
        val = simplify(ab["value"]**2 / ad["value"])
        if add_derived(facts,
            {"type": "length", "line": a+c, "value": val},
            f"{reason}_{a+c}=AB²/AD"):
            changed = True

    # AD = AB²/AC
    if ab and ac and not ad:
        val = simplify(ab["value"]**2 / ac["value"])
        if add_derived(facts,
            {"type": "length", "line": a+d, "value": val},
            f"{reason}_{a+d}=AB²/AC"):
            changed = True

    # AB = √(AD×AC)
    if ad and ac and not ab:
        val = simplify(sqrt(ad["value"] * ac["value"]))
        if add_derived(facts,
            {"type": "length", "line": a+b, "value": val},
            f"{reason}_{a+b}=√(AD×AC)"):
            changed = True

    # AB² = AD×AC 성립하면 접선 추론
    if ab and ad and ac:
        if simplify(ab["value"]**2
                   - ad["value"]*ac["value"]) == 0:
            circle_name = f"circumcircle_{b}{d}{c}"
            fact = {
                "type": "tangent_from_point",
                "from": a,
                "line": a+b,
                "circle": circle_name,
                "point": b
            }
            if add_derived(facts, fact,
                f"{reason}→접선_{a+b}은△{b}{d}{c}외접원접선"):
                changed = True

            fact2 = {
                "type": "equal_angle",
                "angle1": a+b+d,
                "angle2": a+c+b
            }
            if add_derived(facts, fact2,
                f"{reason}→각도_∠{a+b+d}=∠{a+c+b}"):
                changed = True

    return changed

def rule_basic_similarity(facts):
    all_facts = facts["constraints"] + facts["derived"]
    changed = False

    # 경로 1: equal_angle → AB² = AD×AC
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
            facts, a, b, c, d, "각도→기본닮음")

    # 경로 2: 접선 → AB² = AD×AC
    tangents = [f for f in all_facts
                if f["type"] == "tangent_from_point"]

    for tan in tangents:
        a = tan["from"]
        b = tan["point"]
        circ = tan.get("circle", "")

        if not circ.startswith("circumcircle_"):
            continue
        tri_pts = list(circ.replace("circumcircle_", ""))
        if len(tri_pts) != 3:
            continue
        if b not in tri_pts:
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
# 레마 2: 내접원 접선 길이
# BF=BD=(AB+BC-AC)/2
# AF=AE=(AB+AC-BC)/2
# CD=CE=(BC+AC-AB)/2
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
            pt   = tp["point"]

            # BD = BF = (AB+BC-AC)/2
            if b in line and c in line:
                val = simplify(
                    (ab["value"]+bc["value"]-ac["value"])/2)
                if add_derived(facts,
                    {"type": "length",
                     "line": b+pt, "value": val},
                    f"내접원접선_{b+pt}"):
                    changed = True
                if add_derived(facts,
                    {"type": "length",
                     "line": pt+b, "value": val},
                    f"내접원접선_{pt+b}"):
                    changed = True

            # AF = AE = (AB+AC-BC)/2
            elif a in line and b in line:
                val = simplify(
                    (ab["value"]+ac["value"]-bc["value"])/2)
                if add_derived(facts,
                    {"type": "length",
                     "line": a+pt, "value": val},
                    f"내접원접선_{a+pt}"):
                    changed = True
                if add_derived(facts,
                    {"type": "length",
                     "line": pt+a, "value": val},
                    f"내접원접선_{pt+a}"):
                    changed = True

            # CD = CE = (BC+AC-AB)/2
            elif a in line and c in line:
                val = simplify(
                    (bc["value"]+ac["value"]-ab["value"])/2)
                if add_derived(facts,
                    {"type": "length",
                     "line": c+pt, "value": val},
                    f"내접원접선_{c+pt}"):
                    changed = True
                if add_derived(facts,
                    {"type": "length",
                     "line": pt+c, "value": val},
                    f"내접원접선_{pt+c}"):
                    changed = True

    return changed

# ===========================
# 레마 3: 메넬라우스 정리
# △ABC와 직선 l
# BF/FA × AG/GC × CD/DB = 1
# ===========================
def _find_on_side(facts, line_pts, p1, p2):
    """직선 위의 점 중 p1p2 변 위의 점 찾기"""
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

            # 각 변 위의 교점 찾기
            d_list = _find_on_side(facts, line_pts, b, c)
            g_list = _find_on_side(facts, line_pts, c, a)
            f_list = _find_on_side(facts, line_pts, a, b)

            if not (d_list and g_list and f_list):
                continue

            for d in d_list:
                for g in g_list:
                    for f in f_list:
                        # BF/FA × AG/GC × CD/DB = 1
                        bf = get_length(facts, b, f)
                        fa = get_length(facts, f, a)
                        ag = get_length(facts, a, g)
                        gc = get_length(facts, g, c)
                        cd = get_length(facts, c, d)
                        db = get_length(facts, d, b)

                        knowns = [bf, fa, ag, gc, cd, db]
                        known_count = sum(
                            1 for k in knowns if k)

                        if known_count < 5:
                            continue

                        # 5개 알면 나머지 1개 계산
                        # BF/FA × AG/GC × CD/DB = 1

                        if bf and fa and cd and db:
                            ratio = simplify(
                                bf["value"]*cd["value"]
                                /(fa["value"]*db["value"]))

                            # AG/GC = FA×DB/(BF×CD)
                            inv_ratio = simplify(
                                1/ratio)

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
# 레마 4: SAS 넓이 공식
# X가 AB위, Y가 AC위
# △AXY/△ABC = AX·AY/AB·AC
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

            # 공통 꼭짓점 A 찾기
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

            # X가 AB위, Y가 AC위 확인
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

            area1 = get_constraint(facts, "area",
                                   triangle=tri1)
            area2 = get_constraint(facts, "area",
                                   triangle=tri2)

            # △ABC = △AXY × AB·AC / AX·AY
            if area1 and ax and ay and ab and ac \
                    and not area2:
                val = simplify(
                    area1["value"] *
                    ab["value"] * ac["value"] /
                    (ax["value"] * ay["value"]))
                if add_derived(facts,
                    {"type": "area",
                     "triangle": tri2, "value": val},
                    f"SAS넓이_{tri2}={tri1}×AB·AC/AX·AY"):
                    changed = True

            # △AXY = △ABC × AX·AY / AB·AC
            if area2 and ax and ay and ab and ac \
                    and not area1:
                val = simplify(
                    area2["value"] *
                    ax["value"] * ay["value"] /
                    (ab["value"] * ac["value"]))
                if add_derived(facts,
                    {"type": "area",
                     "triangle": tri1, "value": val},
                    f"SAS넓이_{tri1}={tri2}×AX·AY/AB·AC"):
                    changed = True

            if area1 and area2:
                ratio = simplify(
                    area1["value"] / area2["value"])

                if ab and ac and ay and not ax:
                    val = simplify(
                        ratio * ab["value"] * ac["value"]
                        / ay["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+x, "value": val},
                        f"SAS넓이_{a+x}"):
                        changed = True

                if ab and ac and ax and not ay:
                    val = simplify(
                        ratio * ab["value"] * ac["value"]
                        / ax["value"])
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+y, "value": val},
                        f"SAS넓이_{a+y}"):
                        changed = True

                if ax and ay and ac and not ab:
                    val = simplify(
                        ax["value"] * ay["value"]
                        / (ratio * ac["value"]))
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+b, "value": val},
                        f"SAS넓이_{a+b}"):
                        changed = True

                if ax and ay and ab and not ac:
                    val = simplify(
                        ax["value"] * ay["value"]
                        / (ratio * ab["value"]))
                    if add_derived(facts,
                        {"type": "length",
                         "line": a+c, "value": val},
                        f"SAS넓이_{a+c}"):
                        changed = True

    return changed

# ===========================
# 규칙 DB (4개 레마만)
# ===========================
rule_db_new = [
    {
        "name": "기본닮음",
        "can_apply": lambda f:
            any(c["type"] in
                ["equal_angle", "tangent_from_point"]
                for c in f["constraints"] + f["derived"]),
        "apply": rule_basic_similarity
    },
    {
        "name": "내접원접선길이",
        "can_apply": lambda f:
            any(c["type"] == "incircle"
                for c in f["constraints"] + f["derived"]),
        "apply": rule_incircle_tangent_length
    },
    {
        "name": "메넬라우스",
        "can_apply": lambda f:
            len(f["entities"]["triangles"]) > 0
            and any(c["type"] == "collinear"
                    for c in f["constraints"] + f["derived"]),
        "apply": rule_menelaus
    },
    {
        "name": "SAS넓이",
        "can_apply": lambda f:
            len(f["entities"]["triangles"]) >= 2
            and any(c["type"] == "collinear"
                    for c in f["constraints"] + f["derived"]),
        "apply": rule_sas_area
    },
]

# ===========================
# 테스트: 문제 7 (EG=119)
# ===========================
def test_problem7():
    print("="*40)
    print("문제 7: EG 구하기")
    print("AB=73, BC=123, AC=120")
    print("="*40)

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
            # G,A,C 순서 (G는 AC 연장선)
            {"type": "collinear",
             "points": ["G","A","C"],
             "ordered": True},
            # D,F,G 직선
            {"type": "collinear",
             "points": ["D","F","G"],
             "ordered": False},
            # 각 변위 점
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

    init_facts(facts)

    # 내접원 접선 길이 적용
    rule_incircle_tangent_length(facts)

    # 메넬라우스 적용
    rule_menelaus(facts)

    # 선분분할로 EG 계산
    # EG = GA + AE (G,A,E,C 순서)
    ga = get_length(facts, "G", "A")
    ae = get_length(facts, "A", "E")

    if ga and ae:
        eg = simplify(ga["value"] + ae["value"])
        print(f"\n✅ GA = {ga['value']}")
        print(f"✅ AE = {ae['value']}")
        print(f"✅ EG = GA + AE = {eg}")

test_problem7()
