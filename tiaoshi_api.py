"""流年取数：POST /interface/ai/tiaoshi

用法:
    python tiaoshi_api.py 1988-8-6 男 2026              # 不给时辰: 打 13 档表
    python tiaoshi_api.py 1988-8-6-9 男 2026            # 给了时辰: 只取 key "0" 那一档
    python tiaoshi_api.py 1988-8-6 男 2025 2026 2027    # 多年并排
    python tiaoshi_api.py 1988-8-6 男 2026 --sexcheck   # 查后端这一版是否按性别区分

birth 含小时 (YYYY-M-D-H) 时后端按该时辰算，13 档返回同值 -> 取 msg["0"]。
"""
import json
import sys
import urllib.request

BASE = "https://online.miaoxingjundd.com/api"
PATH = "/interface/ai/tiaoshi"
NUM2LETTER = {str(i): c for i, c in enumerate("abcdefghi")}
DIMS = ["感情", "财", "印", "官", "比", "食"]
SHICHEN = {"23": "子(晚)", "1": "丑", "3": "寅", "5": "卯", "7": "辰", "9": "巳",
           "11": "午", "13": "未", "15": "申", "17": "酉", "19": "戌", "21": "亥",
           "0": "子(早/0点)"}


def raw(birth, sex, year, timeout=60):
    """接口原始 msg: {时点: {维度: 数字}}"""
    payload = {"birth": str(birth), "sex": str(sex), "year": str(year)}
    req = urllib.request.Request(BASE + PATH,
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read().decode("utf-8"))
    if body.get("code") != 200:
        raise RuntimeError("code=%s msg=%s" % (body.get("code"), body.get("msg")))
    return body["msg"]


def has_hour(birth):
    return len(str(birth).split("-")) >= 4


def pick(msg, birth):
    """birth 含时辰 -> 只留 key "0"（13 档同值）；否则留全部档。"""
    return {"0": msg["0"]} if has_hour(birth) else msg


def letters(birth, sex, year, timeout=60):
    """{时点: {维度: a-i 字母}}；birth 含时辰时只有 "0" 一档。"""
    msg = pick(raw(birth, sex, year, timeout), birth)
    return {h: {d: NUM2LETTER.get(str(v), "?") for d, v in dims.items()}
            for h, dims in msg.items()}


def order(msg):
    return sorted(msg, key=lambda x: (int(x) != 23, int(x)))


def sexcheck(birth, year, timeout=60):
    """后端版本本应区分男女；线上实测同值即为接口异常。"""
    date = "-".join(str(birth).split("-")[:3])
    m, f = raw(date, "男", year, timeout), raw(date, "女", year, timeout)
    diff = [h for h in m if m[h] != f.get(h)]
    print("birth=%s year=%s 男 vs 女" % (date, year))
    if diff:
        print("  不同 -> 后端已按性别区分；不同的档: " + ",".join(diff))
    else:
        print("  完全相同 -> 线上这一版未按性别区分（接口异常）")


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        print(__doc__)
        return 1
    birth, sex, years = args[0], args[1], args[2:]
    if "--sexcheck" in argv:
        sexcheck(birth, years[0])
    got = {y: letters(birth, sex, y) for y in years}
    print("birth=%s sex=%s%s" % (birth, sex,
                                  "  (含时辰 -> 取 key 0)" if has_hour(birth) else ""))
    for y in years:
        msg = got[y]
        print("\n== %s年 ==" % y)
        print("时点 时辰     " + "  ".join(DIMS))
        for h in order(msg):
            print("%-4s %-8s " % (h, SHICHEN.get(h, "?")) +
                  "  ".join(msg[h].get(d, "?") for d in DIMS))
    if len(years) > 1 and not has_hour(birth):
        print("\n== 各时辰多年字母串(顺序: %s) ==" % "+".join(years))
        for h in order(got[years[0]]):
            print("%-4s %-8s %s" % (h, SHICHEN.get(h, "?"),
                                    " ".join("".join(got[y][h].get(d, "?") for d in DIMS)
                                             for y in years)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
