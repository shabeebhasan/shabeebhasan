"""Generate the stats card shown on the profile README, from live GitHub API data."""
import json, os, ssl, urllib.request, collections
from PIL import Image, ImageDraw, ImageFont

USER = "shabeebhasan"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
FONTS = "/System/Library/Fonts/Supplemental/"
if not os.path.isdir(FONTS):  # CI (Linux)
    FONTS = "/usr/share/fonts/truetype/dejavu/"
FMAP = {"bold": "Trebuchet MS Bold.ttf", "reg": "Trebuchet MS.ttf", "serif": "Georgia Bold.ttf"}
if "dejavu" in FONTS:
    FMAP = {"bold": "DejaVuSans-Bold.ttf", "reg": "DejaVuSans.ttf", "serif": "DejaVuSerif-Bold.ttf"}


def font(kind, size):
    return ImageFont.truetype(FONTS + FMAP[kind], size)


try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()


def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": USER,
                                          **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    return json.load(urllib.request.urlopen(req, context=CTX))


def collect():
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    langs = collections.Counter()
    for r in own:
        if r.get("language"):
            langs[r["language"]] += 1
    import datetime
    since = int(user["created_at"][:4])
    return {
        "repos": len(own),
        "all_langs": len(langs),
        "years": datetime.date.today().year - since,
        "since": since,
        "langs": langs.most_common(6),
    }


def grad(w, h, c1, c2):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for x in range(w):
        t = x / w
        d.line([(x, 0), (x, h)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return im


def build(s, out):
    W, H = 900, 320
    im = grad(W, H, (11, 17, 32), (14, 70, 100))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([700, -120, 1020, 200], fill=(56, 189, 248, 22))
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 8))

    d.text((40, 34), "GitHub at a glance", font=font("serif", 30), fill="#ffffff")
    d.text((42, 78), f"building in the open since {s['since']}", font=font("reg", 18), fill="#94a3b8")

    x = 42
    for big, small in [(str(s["repos"]), "public repositories"), (str(s["years"]), "years on GitHub"),
                       (str(s["all_langs"]), "languages shipped")]:
        d.text((x, 126), big, font=font("bold", 40), fill="#ffffff")
        d.text((x, 176), small, font=font("reg", 17), fill="#94a3b8")
        x += max(d.textlength(small, font=font("reg", 17)), 90) + 70

    d.text((42, 226), "Most used languages", font=font("bold", 17), fill="#7dd3fc")
    total = sum(c for _, c in s["langs"]) or 1
    bx, bw = 42, W - 84
    colors = ["#38bdf8", "#818cf8", "#f472b6", "#facc15", "#34d399", "#fb923c"]
    for i, (lang, count) in enumerate(s["langs"]):
        seg = bw * count / total
        d.rounded_rectangle([bx, 254, bx + max(seg - 3, 6), 268], radius=6, fill=colors[i % len(colors)])
        bx += seg
    lx = 42
    for i, (lang, count) in enumerate(s["langs"]):
        d.ellipse([lx, 285, lx + 10, 295], fill=colors[i % len(colors)])
        label = "Jupyter" if lang.startswith("Jupyter") else lang
        d.text((lx + 16, 282), label, font=font("reg", 16), fill="#cbd5e1")
        lx += 26 + d.textlength(label, font=font("reg", 16)) + 22
    im.save(out, optimize=True)
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(build(collect(), os.path.join(here, "assets", "stats.png")))
