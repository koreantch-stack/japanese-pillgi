"""N5 한자만 남기고 나머지 한자를 히라가나로 바꿔 poems.json과 검수표를 만든다.

사용법: python3 build_n5.py            (기본 N5 80자)
        python3 build_n5.py 分私       (인수로 준 한자를 N5에 추가)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data_daily  # noqa: E402
import data_poems  # noqa: E402
import data_prose  # noqa: E402

N5_BASE = set(
    "日一国人年大十二本中長出三時行見月後前生五間上東四今金九入学高円子外八六下来気小七山話女北午百書先名川千水半男"
    "西電校語土木聞食車何南万毎白天母火右読友左休父雨"
    "分"  # 목록마다 갈리지만 시각·분 표현에 쓰이는 N5 기본 한자라 포함
)
assert len(N5_BASE) == 80, len(N5_BASE)
EXTRA = set(sys.argv[1]) if len(sys.argv) > 1 else set()
ALLOWED = N5_BASE | EXTRA

KANJI = re.compile(r"[一-鿿々]")
RUNS = re.compile(r"[一-鿿々]+|[^一-鿿々]+")
KANA = re.compile(r"^[ぁ-ゖァ-ヺー]+$")
PUNCT = {"。", "、"}

OUT = Path(__file__).resolve().parent.parent
OUT.mkdir(exist_ok=True)
CAT_LABEL = {"daily": "일상 문장", "haiku": "하이쿠", "waka": "와카", "classic": "고전 산문", "modern": "근현대 문학"}


def to_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def to_kata(s):
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)


def convert_word(surface, reading, force_kata=False):
    """N5 밖 한자가 든 한자 덩어리만 히라가나로 바꾼다. 정렬에 실패하면 단어 전체를 읽는 법으로 바꾼다.
    송가나가 가타카나인 단어(예: 暑サ)는 바꾼 부분도 가타카나로 쓴다."""
    kanji = [c for c in surface if KANJI.match(c)]
    if not kanji or all(c in ALLOWED for c in kanji):
        return surface, False
    parts = RUNS.findall(surface)
    kata = force_kata or any(re.search(r"[ァ-ヺ]", p) for p in parts if not KANJI.match(p[0]))
    conv = to_kata if kata else (lambda x: x)
    pos, out = 0, []
    for i, p in enumerate(parts):
        if KANJI.match(p[0]):
            if i + 1 < len(parts):
                idx = reading.find(to_hira(parts[i + 1]), pos + 1)
                if idx == -1:
                    return conv(reading), True
                run_reading = reading[pos:idx]
            else:
                run_reading = reading[pos:]
            pos += len(run_reading)
            out.append(p if all(c in ALLOWED for c in p) else conv(run_reading))
        else:
            if reading[pos:pos + len(p)] != to_hira(p):
                return conv(reading), True
            pos += len(p)
            out.append(p)
    if pos != len(reading):
        return conv(reading), True
    return "".join(out), False


items = data_daily.ITEMS + data_poems.ITEMS + data_prose.ITEMS
errors, out = [], []
counters = Counter()
converted_kanji = Counter()
fallbacks = []

for cat, level, author, source, text, ko, words in items:
    counters[cat] += 1
    item_id = f"{cat}-{counters[cat]:03d}"

    if "".join(w[0] for w in words if w[0] != "\n") != text:
        errors.append(f"[{item_id}] 원문과 단어 합이 다름")

    lines, cur = [], []
    new_text = []
    for s, r, m in words:
        if s == "\n":
            lines.append(cur)
            cur = []
            continue
        if s in PUNCT:
            cur.append({"s": s, "r": "", "m": ""})
            new_text.append(s)
            continue
        if not r or not KANA.match(r):
            errors.append(f"[{item_id}] 읽는 법 오류: {s!r} -> {r!r}")
        # 히라가나가 하나도 없는 가타카나 작품(雨ニモマケズ)은 바꾼 한자도 가타카나로 쓴다
        ns, fb = convert_word(s, r, force_kata=not re.search(r"[ぁ-ゖ]", text))
        if fb:
            fallbacks.append(f"{item_id}: {s} -> {ns}")
        for c in s:
            if KANJI.match(c) and c not in ALLOWED:
                converted_kanji[c] += 1
        word = {"s": ns, "r": r, "m": m}
        if ns != s:
            word["k"] = s  # 원래 한자 표기
        cur.append(word)
        new_text.append(ns)
    lines.append(cur)

    text_new = "".join(new_text)
    left = [c for c in text_new if KANJI.match(c) and c not in ALLOWED]
    if left:
        errors.append(f"[{item_id}] N5 밖 한자가 남음: {left}")

    reading = "".join(w[1] if w[1] else w[0] for w in words if w[0] != "\n")
    out.append({
        "id": item_id, "cat": cat, "level": level, "author": author, "source": source,
        "text": text_new, "text_orig": text, "reading": reading, "ko": ko,
        "lines": lines, "status": "검수전",
    })

if errors:
    print("오류", len(errors), "건")
    print("\n".join(errors))
    sys.exit(1)

(OUT / "poems.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

md = ["일본어 따라쓰기 데이터 검수표 (1차분, N5 한자만 사용)", "",
      "N5 밖 한자는 히라가나로 바꿨습니다. 상태는 모두 검수 전입니다.", ""]
for cat in CAT_LABEL:
    md += [f"## {CAT_LABEL[cat]}", ""]
    for it in [i for i in out if i["cat"] == cat]:
        head = f"{it['id']} (난이도 {it['level']})"
        if it["author"]:
            head += f" {it['author']}『{it['source']}』"
        md.append(head)
        md.append(f"따라쓸 글: {it['text']}")
        if it["text"] != it["text_orig"]:
            md.append(f"원래 표기: {it['text_orig']}")
        md.append(f"번역: {it['ko']}")
        glosses = []
        for ln in it["lines"]:
            for w in ln:
                if not (w["r"] or w["m"]):
                    continue
                glosses.append(f"{w['s']} {w['m']}" if w["s"] == w["r"] else f"{w['s']}({w['r']}) {w['m']}")
        md.append("단어: " + " / ".join(glosses))
        md.append("")
(OUT / "tools" / "검수표.md").write_text("\n".join(md), encoding="utf-8")

kept = Counter(c for it in out for c in it["text"] if KANJI.match(c))
print("OK", len(out), "건", dict(counters))
print("추가 허용 한자:", "".join(sorted(EXTRA)) or "없음")
print("남은 한자(전부 N5):", len(kept), "종", "".join(sorted(kept)))
print("히라가나로 바뀐 한자 종류:", len(converted_kanji))
print("바뀐 한자 빈도 상위:", " ".join(f"{k}{v}" for k, v in converted_kanji.most_common(30)))
print("읽는 법 전체 대체(옛 가나 표기 등):", len(fallbacks))
for f in fallbacks:
    print("  ", f)
