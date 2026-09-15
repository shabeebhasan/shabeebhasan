"""Generate the banner and stats card on the profile README, from live GitHub API data."""
import json, os, ssl, urllib.request, collections, datetime
from PIL import Image, ImageDraw, ImageFont

USER = "shabeebhasan"
FIRST_LINE = "Shabeeb Hasan"
ROLE = "Senior AI & Full-Stack Software Engineer"
FOCUS = "LLM apps  ·  RAG  ·  AI agents  ·  SaaS platforms  ·  Cloud & mobile"
YEARS_SHIPPING = "12+"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

FONTS = "/System/Library/Fonts/Supplemental/"
FMAP = {"bold": "Trebuchet MS Bold.ttf", "reg": "Trebuchet MS.ttf", "serif": "Georgia Bold.ttf"}
if not os.path.isdir(FONTS):  # CI (Linux)
    FONTS = "/usr/share/fonts/truetype/dejavu/"
    FMAP = {"bold": "DejaVuSans-Bold.ttf", "reg": "DejaVuSans.ttf", "serif": "DejaVuSerif-Bold.ttf"}

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()


def font(kind, size):
    return ImageFont.truetype(FONTS + FMAP[kind], size)


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
    langs = collections.Counter(r["language"] for r in own if r.get("language"))
    since = int(user["created_at"][:4])
    return {"repos": len(own), "all_langs": len(langs), "since": since,
            "years": datetime.date.today().year - since, "langs": langs.most_common(6)}


def grad(w, h, c1, c2):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for x in range(w):
        t = x / w
        d.line([(x, 0), (x, h)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return im


def stat_row(d, x, y, stats, big_size=34, small_size=21, gap=52):
    for big, small in stats:
        d.text((x, y), big, font=font("bold", big_size), fill="#ffffff")
        d.text((x, y + big_size + 10), small, font=font("reg", small_size), fill="#94a3b8")
        w = max(d.textlength(big, font=font("bold", big_size)),
                d.textlength(small, font=font("reg", small_size)))
        x += w + gap


def banner(s, out):
    W, H = 1280, 400
    im = grad(W, H, (11, 17, 32), (14, 80, 110))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([980, -160, 1420, 280], fill=(56, 189, 248, 26))
    d.ellipse([-120, 240, 320, 680], fill=(125, 211, 252, 20))
    for y in range(0, H, 50):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 10))
    for x in range(0, W, 50):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 8))

    d.text((70, 86), FIRST_LINE, font=font("serif", 64), fill="#ffffff")
    d.text((72, 172), ROLE, font=font("reg", 32), fill="#7dd3fc")
    d.text((72, 220), FOCUS, font=font("reg", 25), fill="#cbd5e1")
    stat_row(d, 72, 296, [(YEARS_SHIPPING, "years shipping software"),
                          (str(s["repos"]), "public repositories"),
                          (str(s["all_langs"]), "languages shipped"),
                          ("PhD", "computer science, in progress")])
    im.save(out, optimize=True)
    return out


def stats_card(s, out):
    W, H = 900, 320
    im = grad(W, H, (11, 17, 32), (14, 70, 100))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([700, -120, 1020, 200], fill=(56, 189, 248, 22))
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 8))

    d.text((40, 34), "GitHub at a glance", font=font("serif", 30), fill="#ffffff")
    d.text((42, 78), f"building in the open since {s['since']}", font=font("reg", 18), fill="#94a3b8")
    stat_row(d, 42, 126, [(str(s["repos"]), "public repositories"),
                          (str(s["years"]), "years on GitHub"),
                          (str(s["all_langs"]), "languages shipped")],
             big_size=40, small_size=17, gap=70)

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
        label = "Jupyter" if lang.startswith("Jupyter") else lang
        d.ellipse([lx, 285, lx + 10, 295], fill=colors[i % len(colors)])
        d.text((lx + 16, 282), label, font=font("reg", 16), fill="#cbd5e1")
        lx += 26 + d.textlength(label, font=font("reg", 16)) + 22
    im.save(out, optimize=True)
    return out


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = collect()
    print(banner(data, os.path.join(root, "assets", "banner.png")))
    print(stats_card(data, os.path.join(root, "assets", "stats.png")))
