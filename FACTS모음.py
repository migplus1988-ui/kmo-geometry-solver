# ===========================
# 문제 1: 내심+MN∥AB → 넓이
# 정답: 252
# ===========================
facts1 = {
    "entities": {
        "points": ["A","B","C","I","M","N"],
        "lines": ["AB","BC","CA","MN"],
        "triangles": ["ABC","MNI"],
        "circles": ["incircle"]
    },
    "constraints": [
        {"type": "length",
         "line": "AB", "value": Rational(13)},
        {"type": "length",
         "line": "BC", "value": Rational(20)},
        {"type": "length",
         "line": "CA", "value": Rational(21)},
        {"type": "incircle",
         "triangle": "ABC",
         "circle": "incircle",
         "center": "I"},
        {"type": "is_parallel",
         "line1": "MN", "line2": "AB"},
        {"type": "collinear",
         "points": ["B","M","C"],
         "ordered": True},
        {"type": "collinear",
         "points": ["A","N","C"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "area", "triangle": "ABC"}
}

# ===========================
# 문제 2: BP 길이
# 정답: 34/5
# ===========================
facts2 = {
    "entities": {
        "points": ["A","B","C","P"],
        "lines": ["AB","BC","CA","AP"],
        "triangles": ["ABC"],
        "circles": ["ω"]
    },
    "constraints": [
        {"type": "length",
         "line": "AB", "value": Rational(3)},
        {"type": "length",
         "line": "BC", "value": Rational(7)},
        {"type": "length",
         "line": "CA", "value": Rational(5)},
        {"type": "length",
         "line": "AP", "value": Rational(4)},
        {"type": "circumcircle",
         "triangle": "ABC", "name": "ω"},
        {"type": "on_circle",
         "point": "P", "circle": "ω"},
        {"type": "collinear",
         "points": ["A","P","B"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length", "line": "BP"}
}

# ===========================
# 문제 3: EF 길이 (톨레미)
# 정답: 6√22/5
# ===========================
facts3 = {
    "entities": {
        "points": ["A","B","C","D","E","F"],
        "lines": ["AB","BC","CA","EF"],
        "triangles": ["ABC"],
        "circles": ["ω"]
    },
    "constraints": [
        {"type": "length",
         "line": "AB", "value": Rational(11)},
        {"type": "length",
         "line": "BC", "value": Rational(7)},
        {"type": "length",
         "line": "CA", "value": Rational(9)},
        {"type": "circumcircle",
         "triangle": "ABC", "name": "ω"},
        {"type": "midpoint",
         "point": "D", "line": "BC"},
        {"type": "on_circle",
         "point": "E", "circle": "ω"},
        {"type": "on_circle",
         "point": "F", "circle": "ω"},
        {"type": "collinear",
         "points": ["A","D","E"],
         "ordered": True},
        {"type": "collinear",
         "points": ["B","D","F"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length", "line": "EF"}
}

# ===========================
# 문제 4: AC² (우산정리)
# 정답: 320
# ===========================
facts4 = {
    "entities": {
        "points": ["A","B","C","P","D"],
        "lines": ["AB","BC","CA","PD"],
        "triangles": ["ABC"],
        "circles": ["ω"]
    },
    "constraints": [
        {"type": "length",
         "line": "AB", "value": Rational(8)},
        {"type": "length",
         "line": "PB", "value": Rational(7)},
        {"type": "length",
         "line": "PD", "value": Rational(9)},
        {"type": "circumcircle",
         "triangle": "ABC", "name": "ω"},
        {"type": "on_circle",
         "point": "P", "circle": "ω"},
        {"type": "arc_midpoint",
         "point": "A", "arc": "BC",
         "circle": "ω"},
        {"type": "collinear",
         "points": ["P","D","B"],
         "ordered": True},
        {"type": "collinear",
         "points": ["A","D","C"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length_squared", "line": "AC"}
}

# ===========================
# 문제 5: BC² (외각이등분선+닮음)
# 정답: 126
# ===========================
facts5 = {
    "entities": {
        "points": ["A","B","C","P","K"],
        "lines": ["AB","AC","BC","PA","PB","PC","PK"],
        "triangles": ["ABC","ABP","ACP"],
        "circles": ["ω"]
    },
    "constraints": [
        {"type": "length",
         "line": "AB", "value": Rational(10)},
        {"type": "length",
         "line": "AC", "value": Rational(16)},
        {"type": "length",
         "line": "PA", "value": Rational(8)},
        {"type": "circumcircle",
         "triangle": "ABC", "name": "ω"},
        {"type": "on_circle",
         "point": "P", "circle": "ω"},
        {"type": "arc_midpoint",
         "point": "P", "arc": "BC",
         "circle": "ω"},
        {"type": "collinear",
         "points": ["K","B","C"],
         "ordered": True},
        {"type": "collinear",
         "points": ["P","A","K"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length_squared", "line": "BC"}
}

# ===========================
# 문제 6: EG (내접원+메넬라우스)
# 정답: 119
# ===========================
facts6 = {
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

# ===========================
# 문제 7: S² (SAS넓이)
# 정답: 252
# ===========================
facts7 = {
    "entities": {
        "points": ["A","B","C","M","D","E"],
        "lines": ["AB","BC","CA","DM","BC"],
        "triangles": ["ABC","AEM"],
        "circles": []
    },
    "constraints": [
        {"type": "length",
         "line": "AC", "value": Rational(8)},
        {"type": "length",
         "line": "AE", "value": Rational(5)},
        {"type": "length",
         "line": "EM", "value": Rational(6)},
        {"type": "length",
         "line": "AM", "value": Rational(4)},
        {"type": "midpoint",
         "point": "M", "line": "AC"},
        {"type": "perpendicular",
         "from": "D", "foot": "D", "to": "BC"},
        {"type": "collinear",
         "points": ["B","D","C"],
         "ordered": True},
        {"type": "collinear",
         "points": ["A","E","C"],
         "ordered": True},
        {"type": "collinear",
         "points": ["A","M","C"],
         "ordered": True},
        {"type": "collinear",
         "points": ["B","A","E"],
         "ordered": False},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "area_squared", "triangle": "ABC"}
}

# ===========================
# 문제 8: DE² (접현각+정삼각형+코사인법칙)
# 정답: 112/3 (m+n=115)
# ===========================
facts8 = {
    "entities": {
        "points": ["A","B","C","D","E"],
        "lines": ["AB","AC","BC","DA","DB","DE","AE"],
        "triangles": ["ABC","DAB","DAE"],
        "circles": ["ω"]
    },
    "constraints": [
        {"type": "length",
         "line": "AC", "value": Rational(4)},
        {"type": "length",
         "line": "BC", "value": Rational(8)},
        {"type": "length",
         "line": "AB",
         "value": simplify(sqrt(48))},
        {"type": "length",
         "line": "AE",
         "value": simplify(Rational(4)/sqrt(3))},
        {"type": "circumcircle",
         "triangle": "ABC", "name": "ω"},
        {"type": "on_circle",
         "point": "E", "circle": "ω"},
        {"type": "tangent_from_point",
         "from": "D", "line": "DA",
         "circle": "ω", "point": "A"},
        {"type": "tangent_from_point",
         "from": "D", "line": "DB",
         "circle": "ω", "point": "B"},
        {"type": "angle_val",
         "angle": "ACB", "value": 60},
        {"type": "angle_val",
         "angle": "DAB", "value": 60},
        {"type": "angle_val",
         "angle": "DBA", "value": 60},
        {"type": "angle_val",
         "angle": "DAE", "value": 60},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length_squared", "line": "DE"}
}

# ===========================
# 문제 9: PQ² (내접원+내각이등분선+cos제2법칙)
# 정답: 73
# ===========================
facts9 = {
    "entities": {
        "points": ["A","B","C","I","P","Q"],
        "lines": ["AB","BC","CA","CI","PQ"],
        "triangles": ["ABC","AQP"],
        "circles": ["incircle"]
    },
    "constraints": [
        {"type": "length",
         "line": "AB", "value": Rational(15)},
        {"type": "length",
         "line": "BC", "value": Rational(21)},
        {"type": "length",
         "line": "CA", "value": Rational(24)},
        {"type": "incircle",
         "triangle": "ABC",
         "circle": "incircle",
         "center": "I"},
        {"type": "tangent_point",
         "circle": "incircle",
         "line": "AC", "point": "P"},
        {"type": "angle_bisector",
         "vertex": "C",
         "point": "Q",
         "side1": "A",
         "side2": "B"},
        {"type": "collinear",
         "points": ["A","Q","B"],
         "ordered": True},
        {"type": "collinear",
         "points": ["A","P","C"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "length_squared", "line": "PQ"}
}

# ===========================
# 문제 10: 외접원 반지름 R
# 정답: 9/2 (p+q=11)
# ===========================
facts10 = {
    "entities": {
        "points": ["A","B","C","P","Q"],
        "lines": ["AB","BC","CA","AP","CQ","PQ"],
        "triangles": ["ABC","BPQ"],
        "circles": ["ω"]
    },
    "constraints": [
        {"type": "area",
         "triangle": "ABC",
         "value": Rational(18)},
        {"type": "area",
         "triangle": "BPQ",
         "value": Rational(2)},
        {"type": "length",
         "line": "PQ",
         "value": simplify(2*sqrt(2))},
        {"type": "perpendicular",
         "from": "A", "foot": "P", "to": "BC"},
        {"type": "perpendicular",
         "from": "C", "foot": "Q", "to": "AB"},
        {"type": "circumcircle",
         "triangle": "ABC", "name": "ω"},
        {"type": "collinear",
         "points": ["B","P","C"],
         "ordered": True},
        {"type": "collinear",
         "points": ["A","Q","B"],
         "ordered": True},
    ],
    "derived": [],
    "proof_steps": [],
    "target": {"type": "circumradius",
               "triangle": "ABC"}
}

# ===========================
# 전체 테스트 실행
# ===========================
if __name__ == "__main__":
    test_cases = [
        (facts1,  "문제1: 넓이",         "252"),
        (facts2,  "문제2: BP",           "34/5"),
        (facts3,  "문제3: EF",           "6√22/5"),
        (facts4,  "문제4: AC²",          "320"),
        (facts5,  "문제5: BC²",          "126"),
        (facts6,  "문제6: EG",           "119"),
        (facts7,  "문제7: S²",           "252"),
        (facts8,  "문제8: DE²",          "112/3"),
        (facts9,  "문제9: PQ²",          "73"),
        (facts10, "문제10: R",           "9/2"),
    ]

    results = []
    for facts, name, expected in test_cases:
        print(f"\n{'='*40}")
        print(f"{name} (정답: {expected})")
        print(f"{'='*40}")
        init_facts(facts)
        result = solve_problem(facts)
        results.append((name, expected, result))

    print(f"\n{'='*40}")
    print("전체 결과 요약")
    print(f"{'='*40}")
    for name, expected, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}: {result} "
              f"(정답: {expected})")
