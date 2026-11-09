"""Buat ulang kartu "Featured builds" dari repo yang di-PIN di profil (urutan sama dengan pin).

Kalau tidak ada pin (atau API GraphQL gagal), dipakai 6 repo yang terakhir di-push.
Dijalankan oleh GitHub Actions (featured.yml). Hasil:
  featured/<nama-repo>.svg   -> satu kartu per repo
  README.md                  -> bagian di antara FEATURED:START dan FEATURED:END diganti

Untuk mengubah deskripsi atau label sebuah kartu tanpa mengubah repo-nya,
isi .github/scripts/featured.json (opsional).
"""
import html
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "des1susanti")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
COUNT = 6
SKIP = {USER}  # repo profil ini sendiri tidak ikut dipajang
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "featured")


def api(path):
    """Panggil GitHub API. Untuk pengujian lokal, set GH_FAKE ke file JSON."""
    fake = os.environ.get("GH_FAKE")
    if fake:
        data = json.load(open(fake))
        return data.get(path, [])
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-featured"})
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def pinned_repos():
    """Ambil repo yang di-pin lewat GitHub GraphQL API, urut sesuai urutan pin."""
    query = """
    query($login: String!) {
      user(login: $login) {
        pinnedItems(first: 6, types: REPOSITORY) {
          nodes { ... on Repository {
            name description url isPrivate isFork isArchived pushedAt
            owner { login }
          } }
        }
      }
    }"""
    fake = os.environ.get("GH_FAKE")
    if fake:
        data = json.load(open(fake)).get("graphql")
    else:
        if not TOKEN:
            return []
        body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
        req = urllib.request.Request("https://api.github.com/graphql", data=body,
                                     headers={"Authorization": "Bearer " + TOKEN, "User-Agent": "profile-featured",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    nodes = (((data or {}).get("data") or {}).get("user") or {}).get("pinnedItems", {}).get("nodes", [])
    out = []
    for n in nodes:
        if not n or n.get("isPrivate") or n.get("isArchived"):
            continue
        out.append({"name": n["name"], "description": n.get("description"), "html_url": n["url"],
                    "owner": (n.get("owner") or {}).get("login", USER)})
    return out


# ---------------------------------------------------------------- tampilan
GOLD, PURPLE, TEAL = ("#2A252E", "#D9BE94"), ("#26222E", "#C9B3E0"), ("#1F2628", "#9FC3C0")
LANG = {  # nama di GitHub -> (label, warna)
    "Python": ("Python", GOLD), "Jupyter Notebook": ("Jupyter", GOLD), "R": ("R", GOLD),
    "Dart": ("Dart", PURPLE), "Kotlin": ("Kotlin", PURPLE), "Java": ("Java", PURPLE), "Swift": ("Swift", PURPLE),
    "C++": ("C++", PURPLE), "CMake": ("CMake", PURPLE),
    "Blade": ("Laravel", TEAL), "PHP": ("PHP", TEAL), "HTML": ("HTML", TEAL), "CSS": ("CSS", TEAL),
    "JavaScript": ("JavaScript", TEAL), "TypeScript": ("TypeScript", TEAL), "Vue": ("Vue", TEAL),
    "Lua": ("Lua", GOLD), "Shell": ("Shell", TEAL),
}
CHIP_COLOR = {  # untuk label yang ditulis di featured.json
    "Flutter": PURPLE, "Firebase": PURPLE, "Android": PURPLE,
    "Laravel": TEAL, "Laravel 11": TEAL, "Three.js": TEAL, "MySQL": TEAL, "Tailwind": TEAL,
    "OpenCV": GOLD, "MediaPipe": GOLD, "Orange": GOLD, "ANN": GOLD, "SVR": TEAL,
    "YOLOv8": TEAL, "PyTorch": GOLD, "Deep learning": PURPLE,
}

ICON = {  # ikon khusus untuk repo tertentu
    "presensi-flutter": '<rect x="34" y="24" width="28" height="48" rx="5" fill="none" stroke="#D9BE94" stroke-width="1.5"/><circle cx="48" cy="44" r="7" fill="none" stroke="#D9BE94" stroke-width="1.2"/><rect x="36" y="34" width="24" height="1.6" fill="#E6CFA6"><animate attributeName="y" values="30;64;30" dur="2.4s" repeatCount="indefinite"/></rect>',
    "robot-gestur": '<g stroke="#D9BE94" stroke-width="1.5" fill="none"><line x1="30" y1="26" x2="66" y2="26"/><line x1="40" y1="26" x2="44" y2="44"/><line x1="56" y1="26" x2="52" y2="44"/></g><g><animateTransform attributeName="transform" type="rotate" values="-8 48 26;8 48 26;-8 48 26" dur="2s" repeatCount="indefinite"/><circle cx="48" cy="48" r="6" fill="#D9BE94"/><rect x="42" y="54" width="12" height="16" rx="3" fill="#D9BE94"/></g>',
    "mitologi-nusantara": '<g><animateTransform attributeName="transform" type="rotate" from="0 48 48" to="360 48 48" dur="8s" repeatCount="indefinite"/><path d="M48 30 L64 39 L64 57 L48 66 L32 57 L32 39 Z M48 30 L48 48 M32 39 L48 48 L64 39 M48 48 L48 66" fill="none" stroke="#D9BE94" stroke-width="1.4"/></g>',
    "etl-sap-icrm-supply-chain": '<g fill="none" stroke="#9FC3C0" stroke-width="1.4"><ellipse cx="34" cy="34" rx="8" ry="3"/><path d="M26 34 L26 46 Q34 50 42 46 L42 34"/><ellipse cx="62" cy="58" rx="8" ry="3"/><path d="M54 58 L54 70 Q62 74 70 70 L70 58"/><path d="M42 42 C52 42 52 58 54 62" stroke-dasharray="3 3"/></g><circle r="2.5" fill="#E6CFA6"><animateMotion dur="2s" repeatCount="indefinite" path="M42 42 C52 42 52 58 54 62"/></circle>',
    "portofolio-v2": '<path d="M24 62 L48 50 L72 62 L48 74 Z" fill="none" stroke="#9FC3C0" stroke-width="1.2"/><g><animateTransform attributeName="transform" type="translate" values="-8 0;8 0;-8 0" dur="3s" repeatCount="indefinite"/><rect x="42" y="40" width="12" height="12" rx="3" fill="#D9BE94"/><rect x="44" y="52" width="8" height="8" fill="#BFAE98"/><circle cx="46" cy="45" r="1.3" fill="#16141A"/><circle cx="50" cy="45" r="1.3" fill="#16141A"/></g>',
    "life-design-quest": '<circle cx="48" cy="48" r="20" fill="none" stroke="#D9BE94" stroke-width="1.4"/><g><animateTransform attributeName="transform" type="rotate" values="-25 48 48;25 48 48;-25 48 48" dur="3s" repeatCount="indefinite"/><path d="M48 32 L52 48 L48 64 L44 48 Z" fill="#D9BE94"/><path d="M48 48 L52 48 L48 64 L44 48 Z" fill="#8C6B4F"/></g>',
    "ftth-self-reporting": '<path d="M30 58 L48 46 L66 58 L66 72 L30 72 Z" fill="none" stroke="#9FC3C0" stroke-width="1.4"/><rect x="44" y="62" width="8" height="10" fill="#9FC3C0"/><circle cx="48" cy="38" r="2.2" fill="#D9BE94"/><path d="M42 33 Q48 27 54 33" fill="none" stroke="#D9BE94" stroke-width="1.4"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.6s" repeatCount="indefinite"/></path><path d="M37 28 Q48 18 59 28" fill="none" stroke="#D9BE94" stroke-width="1.4"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.6s" begin="0.3s" repeatCount="indefinite"/></path>',
    "rice-pest-yolov8": '<g fill="none" stroke="#9FC3C0" stroke-width="1.4"><path d="M48 24 C40 34 40 52 48 66"/><path d="M48 32 L42 28 M48 40 L41 38 M48 48 L41 48 M48 56 L42 58"/></g><g stroke="#E6CFA6" stroke-width="1.2" fill="none"><ellipse cx="54" cy="44" rx="5" ry="9"/><path d="M50 38 L45 34 M58 38 L63 34 M49 46 L44 48 M59 46 L64 48 M50 51 L46 55 M58 51 L62 55 M52 35 L50 30 M56 35 L58 30"/></g><rect x="38" y="25" width="32" height="40" rx="2" fill="none" stroke="#D9BE94" stroke-width="1.3" stroke-dasharray="4 3"><animate attributeName="stroke-dashoffset" values="0;14" dur="1.4s" repeatCount="indefinite"/></rect><rect x="38" y="19" width="26" height="7" rx="1.5" fill="#D9BE94"/><text x="40.5" y="24.6" fill="#16141A" font-size="5.2" font-weight="700">pest 0.84</text>',
    "student-achievement-ann-svr": '<g stroke="#8C7F70" stroke-width="0.8"><line x1="28" y1="72" x2="70" y2="72"/><line x1="28" y1="26" x2="28" y2="72"/></g><g fill="#8C7F70"><circle cx="34" cy="64" r="1.8"/><circle cx="40" cy="58" r="1.8"/><circle cx="46" cy="60" r="1.8"/><circle cx="52" cy="46" r="1.8"/><circle cx="58" cy="44" r="1.8"/><circle cx="64" cy="34" r="1.8"/></g><path d="M30 68 C42 60 52 46 68 30" fill="none" stroke="#D9BE94" stroke-width="2" stroke-dasharray="60" stroke-dashoffset="60"><animate attributeName="stroke-dashoffset" values="60;0;0;60" keyTimes="0;0.4;0.9;1" dur="5s" repeatCount="indefinite"/></path>',
    "simulator-mesin-3d": '<g fill="none" stroke="#D9BE94" stroke-width="1.3"><path d="M26 56 L34 46 L60 44 L70 54 L70 60 L26 60 Z"/><circle cx="36" cy="62" r="5"/><circle cx="62" cy="62" r="5"/></g><rect x="44" y="34" width="10" height="8" fill="none" stroke="#C9B3E0" stroke-width="1.2"><animateTransform attributeName="transform" type="translate" values="0 0;0 -6;0 0" dur="2s" repeatCount="indefinite"/></rect>',
    "nebula-hands": '<g fill="#D9BE94"><circle cx="48" cy="48" r="3"><animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite"/></circle><circle cx="34" cy="38" r="1.5"/><circle cx="62" cy="36" r="1.5"/><circle cx="30" cy="58" r="1.5"/><circle cx="66" cy="60" r="1.5"/><circle cx="48" cy="28" r="1.5"/><circle cx="48" cy="68" r="1.5"/></g><ellipse cx="48" cy="48" rx="20" ry="7" fill="none" stroke="#C9B3E0" stroke-width="1"><animateTransform attributeName="transform" type="rotate" from="0 48 48" to="360 48 48" dur="6s" repeatCount="indefinite"/></ellipse>',
}
ICON_BY_LANG = {  # ikon umum untuk repo baru
    "web": '<rect x="26" y="30" width="44" height="36" rx="4" fill="none" stroke="#9FC3C0" stroke-width="1.4"/><line x1="26" y1="38" x2="70" y2="38" stroke="#9FC3C0" stroke-width="1.2"/><circle cx="31" cy="34" r="1.3" fill="#9FC3C0"/><circle cx="35" cy="34" r="1.3" fill="#9FC3C0"/><text x="48" y="56" text-anchor="middle" fill="#D9BE94" font-size="12" font-family="Consolas, monospace">&lt;/&gt;</text>',
    "mobile": '<rect x="36" y="26" width="24" height="44" rx="5" fill="none" stroke="#C9B3E0" stroke-width="1.5"/><line x1="44" y1="64" x2="52" y2="64" stroke="#C9B3E0" stroke-width="1.4"/><rect x="40" y="34" width="16" height="22" rx="2" fill="#26222E" stroke="#D9BE94" stroke-width="0.8"/>',
    "data": '<g fill="none" stroke="#D9BE94" stroke-width="1.3"><circle cx="34" cy="38" r="4"/><circle cx="34" cy="58" r="4"/><circle cx="62" cy="48" r="4"/><circle cx="48" cy="30" r="4"/><circle cx="48" cy="66" r="4"/><path d="M38 38 L58 48 M38 58 L58 48 M48 34 L48 62"/></g><circle cx="62" cy="48" r="4" fill="#D9BE94"><animate attributeName="opacity" values="0.2;1;0.2" dur="2s" repeatCount="indefinite"/></circle>',
}
WEB_LANGS = {"Blade", "PHP", "HTML", "CSS", "JavaScript", "TypeScript", "Vue"}
MOBILE_LANGS = {"Dart", "Kotlin", "Java", "Swift"}


def esc(s):
    return html.escape(s, quote=True)


def short_desc(desc):
    """Ambil bagian bahasa Inggris (sebelum ' | ') dan bersihkan tanda kurung teknis."""
    d = (desc or "").split(" | ")[0].strip()
    d = re.sub(r"\s*\((?:[^()]*?(?:Python|Three\.js|OpenCV|GitHub Pages)[^()]*)\)", "", d)
    return d


def wrap(text, width=38, lines=2):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = (cur + " " + w).strip()
        else:
            out.append(cur)
            cur = w
            if len(out) == lines:
                break
    if len(out) < lines and cur:
        out.append(cur)
    used = " ".join(out)
    if len(used) < len(" ".join(words)):
        last = out[-1]
        out[-1] = (last[: width - 1].rstrip(" ,.;:") + "…") if len(last) >= width - 1 else last.rstrip(" ,.;:") + "…"
    return out[:lines]


def pick_icon(name, langs):
    if name in ICON:
        return ICON[name]
    top = langs[0] if langs else ""
    if top in MOBILE_LANGS:
        return ICON_BY_LANG["mobile"]
    if top in WEB_LANGS:
        return ICON_BY_LANG["web"]
    return ICON_BY_LANG["data"]


def chips_svg(chips):
    out, x = [], 16
    for label, (bg, fg) in chips:
        w = round(len(label) * 6.2 + 20)
        if x + w > 236:  # sisakan tempat untuk "View repo →"
            break
        out.append(f'<rect x="{x}" y="118" width="{w}" height="22" rx="11" fill="{bg}" stroke="{fg}" stroke-width="0.8"/>'
                   f'<text x="{x + w / 2:.0f}" y="133" text-anchor="middle" fill="{fg}">{esc(label)}</text>')
        x += w + 6
    return '<g font-size="10">' + "".join(out) + "</g>"


def card(name, desc_lines, chips, icon):
    title_size = 17 if len(name) <= 20 else 15 if len(name) <= 24 else 13
    lines = "".join(f'<text x="96" y="{60 + i * 15}" fill="#BFAE98" font-size="11">{esc(l)}</text>' for i, l in enumerate(desc_lines))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 336 160" width="420" height="200" font-family="'Segoe UI', Helvetica, Arial, sans-serif">
<rect x="1" y="1" width="334" height="158" rx="12" fill="#16141A" stroke="#3B3441"/>
<rect x="16" y="16" width="64" height="64" rx="10" fill="#221E26"/>
{icon}
<text x="96" y="40" fill="#F1E3CC" font-size="{title_size}" font-family="Georgia, 'Times New Roman', serif">{esc(name)}</text>
{lines}
{chips_svg(chips)}
<text x="320" y="140" text-anchor="end" fill="#D9BE94" font-size="11">View repo →</text>
</svg>
'''


def main():
    overrides = {}
    op = os.path.join(HERE, "featured.json")
    if os.path.exists(op):
        overrides = json.load(open(op))

    try:
        repos = pinned_repos()
    except Exception as e:  # GraphQL gagal: pakai cara lama
        print("Gagal membaca pin:", e)
        repos = []
    repos = [r for r in repos if r["name"] not in SKIP and r["name"] not in overrides.get("_hide", [])][:COUNT]
    source = "pin"
    if not repos:
        source = "repo terbaru"
        repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed&direction=desc&type=owner")
        repos = [r for r in repos if not r.get("fork") and not r.get("archived") and not r.get("private")
                 and r["name"] not in SKIP and r["name"] not in overrides.get("_hide", [])]
        repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
        repos = repos[:COUNT]

    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".svg"):
            os.remove(os.path.join(OUT, f))

    links = []
    for r in repos:
        name = r["name"]
        ov = overrides.get(name, {})
        owner = r.get("owner") if isinstance(r.get("owner"), str) else USER
        try:
            langs = list(api(f"/repos/{owner}/{name}/languages").keys())
        except Exception:
            langs = []
        desc = ov.get("desc") or short_desc(r.get("description")) or "A project by " + USER
        if ov.get("chips"):
            chips = [(c, CHIP_COLOR.get(c, LANG.get(c, (c, GOLD))[1])) for c in ov["chips"]]
        else:
            seen, chips = set(), []
            for l in langs:
                label, col = LANG.get(l, (l, GOLD))
                if label not in seen:
                    seen.add(label)
                    chips.append((label, col))
            chips = chips[:3]
        svg = card(ov.get("title", name), wrap(desc), chips, pick_icon(name, langs))
        open(os.path.join(OUT, f"{name}.svg"), "w").write(svg)
        links.append(f'<a href="{r["html_url"]}"><img src="featured/{name}.svg" width="49%" alt="{esc(name)}" /></a>')

    rows = "\n\n".join("\n".join(links[i:i + 2]) for i in range(0, len(links), 2))
    readme_path = os.path.join(ROOT, "README.md")
    readme = open(readme_path).read()
    new = re.sub(r"(<!-- FEATURED:START -->).*?(<!-- FEATURED:END -->)",
                 lambda m: m.group(1) + "\n" + rows + "\n" + m.group(2), readme, flags=re.S)
    open(readme_path, "w").write(new)
    print(f"Featured (dari {source}):", ", ".join(r["name"] for r in repos))


if __name__ == "__main__":
    main()
