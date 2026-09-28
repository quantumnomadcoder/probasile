# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""Veille législative : repère les modifications des textes suivis (Justel, EUR-Lex, arrêté royal
« pays d'origine sûrs ») depuis l'état connu, signale les blocs de la bibliothèque qui citent un
article modifié, et lit le bulletin de veille publié sur GitHub.

Trois sources d'état, de la plus récente à la plus ancienne :
  1. l'état « vu » enregistré par l'utilisateur (dossier de base / veille / etat.json) ;
  2. l'état de référence livré avec le programme (veille_reference.json) : l'état du droit
     sur lequel les blocs par défaut ont été écrits ;
  3. à défaut, rien : la première vérification enregistre l'état actuel.

Le programme ne comprend pas le droit : il détecte qu'un texte a changé, dit quels articles et quels
blocs sont concernés, et montre le texte avant / après quand il le connaît. L'analyse reste humaine
(c'est le rôle du bulletin de veille).
"""
import csv
import datetime as dt
import difflib
import hashlib
import html
import json
import os
import re
import time
import unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(ICI, "veille_reference.json")
TEXTES_NOM = "veille_textes.csv"
BULLETIN_URL = "https://raw.githubusercontent.com/quantumnomadcoder/probasile/main/BULLETIN.md"
BULLETIN_PAGE = "https://github.com/quantumnomadcoder/probasile/blob/main/BULLETIN.md"
PAUSE = 2.0  # secondes entre deux pages d'un même site

TEXTES_DEFAUT = [
    # id ; type ; adresse ; nom ; repère utilisé dans les blocs
    ("LOI1980", "justel", "https://www.ejustice.just.fgov.be/eli/loi/1980/12/15/1980121550/justel",
     "Loi du 15 décembre 1980 sur l'accès au territoire, le séjour, l'établissement et l'éloignement des étrangers",
     "LOI1980"),
    ("AR1981", "justel", "https://www.ejustice.just.fgov.be/eli/arrete/1981/10/08/1981001949/justel",
     "Arrêté royal du 8 octobre 1981 sur l'accès au territoire, le séjour, l'établissement et l'éloignement des "
     "étrangers", "AR1981"),
    ("REG2024-1347", "eurlex", "32024R1347", "Règlement (UE) 2024/1347 (qualification)", "REG2024-1347"),
    ("REG2024-1348", "eurlex", "32024R1348", "Règlement (UE) 2024/1348 (procédure commune)", "REG2024-1348"),
    ("DIR2011-95", "eurlex", "32011L0095", "Directive 2011/95/UE (qualification, refonte)", "DIR2011-95"),
    ("PAYS-SURS", "pays_surs", "LOI1980",
     "Arrêté royal établissant la liste des pays d'origine sûrs (art. 57/6/1, § 3, de la loi du 15 décembre 1980)", ""),
]
EURLEX_URL = "https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX:{celex}"
EURLEX_TXT = "https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:{celex}"


# ---------------------------------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------------------------------
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def cle_texte(s):
    """Clé de comparaison insensible aux accents mal enregistrés (« abrogé » = « abrog? ») et à la mise en page."""
    s = re.sub(r"[^\x00-\x7f]", "", s or "").lower()
    s = re.sub(r"\[\s*\d+\s*|\]\s*\d+", " ", s)       # repères de modification [1 … ]1
    return re.sub(r"[^a-z0-9]+", "", s)


def decoder(contenu, entete=""):
    """Octets -> texte, selon le charset annoncé (Justel : windows-1252 ; EUR-Lex : UTF-8)."""
    if isinstance(contenu, str):
        return contenu
    try:  # page enregistrée par le navigateur : souvent réécrite en UTF-8 malgré l'en-tête d'origine
        return contenu.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = re.search(r"charset=([\w-]+)", entete or "", re.I) or \
        re.search(rb"charset=[\"']?([\w-]+)", contenu[:3000], re.I)
    cs = m.group(1) if m else "utf-8"
    cs = cs.decode() if isinstance(cs, bytes) else cs
    try:
        return contenu.decode(cs, errors="replace")
    except LookupError:
        return contenu.decode("utf-8", errors="replace")


def texte_html(fragment):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", fragment)
    t = re.sub(r"\s+", " ", t)  # retours à la ligne du code source : de simples espaces
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\xa0", " ")
    lignes = [" ".join(l.split()) for l in t.split("\n")]
    return "\n".join(l for l in lignes if l)


MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12}


def date_iso(s):
    """« 12-06-2026 », « 12/06/2026 », « 12 juin 2026 » -> « 2026-06-12 » (ou "")."""
    s = s or ""
    m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", s)
    if m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    m = re.search(r"\b(\d{1,2})(?:er)?\s+([A-Za-zÀ-ÿ�?]+)\s+(\d{4})\b", s)
    if m:
        mo = norm(m.group(2)).replace(" ", "")
        for nom, n in MOIS.items():
            if mo == nom or (len(mo) >= 3 and nom.startswith(mo[:3]) and len(mo) >= len(nom) - 2):
                return "%s-%02d-%02d" % (m.group(3), n, int(m.group(1)))
    return ""


def date_fr(iso):
    try:
        d = dt.date.fromisoformat(iso)
    except Exception:
        return iso or "?"
    noms = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
            "novembre", "décembre"]
    return "%s %s %d" % ("1er" if d.day == 1 else d.day, noms[d.month - 1], d.year)


# --- numéros d'articles : « 57/6/1 », « 9bis », « 1er/1 », plages « 48/2-48/9 » ---------------------
SUFFIXES = ["", "bis", "ter", "quater", "quinquies", "sexies", "septies", "octies", "nonies", "decies",
            "undecies", "duodecies", "terdecies", "quaterdecies", "quindecies", "sexdecies", "septdecies",
            "octodecies", "novodecies", "vicies"]


def cle_article(a):
    a = norm(a).replace(" ", "")
    a = a.replace("1er", "1").replace("quarter", "quater")
    parts = []
    for p in re.split(r"/", re.sub(r"[^0-9a-z/.]", "", (a or "").replace(" ", ""))):
        m = re.fullmatch(r"(\d+)([a-z]*)(?:\.(\d+))?", p)
        if not m:
            return None
        suf = SUFFIXES.index(m.group(2)) if m.group(2) in SUFFIXES else 50
        parts.append((int(m.group(1)), suf, int(m.group(3) or 0)))
    return tuple(parts) if parts else None


def article_dans(article, liste):
    """Vrai si l'article figure dans « 1; 2/2; 48/2-48/9; 57/5ter-57/5sexies »."""
    k = cle_article(article)
    if k is None:
        return False
    for item in re.split(r"[;,]", liste or ""):
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            a, b = item.split("-", 1)
            ka, kb = cle_article(a), cle_article(b)
            if ka and kb and ka <= kb:
                if ka <= k <= kb:
                    return True
                continue
            item = a  # « 39/68-1 » : pas une plage
        if cle_article(item) == k:
            return True
    return False


# ---------------------------------------------------------------------------------------------------
# Lecteurs de pages
# ---------------------------------------------------------------------------------------------------
ANNOT = re.compile(r"<\s*((?:[^\s<>,;]+\s+par)\s+)?(L|AR|A\.R\.|LS|Loi|Decr|DCFR|ORD)?\.?\s*"
                   r"(\d{4}-\d{2}-\d{2}/\d+)\s*,\s*art\.?\s*([^,;>]+)[^;>]*;\s*En vigueur\s*:\s*([^>]*?)\s*>")


def nom_acte(type_, ident):
    """(« L », « 2026-06-16/01 ») -> « loi du 16 juin 2026 »."""
    d = ident.split("/")[0]
    t = {"L": "loi", "AR": "arrêté royal", "A.R.": "arrêté royal", "LS": "loi spéciale", "Loi": "loi"}.get(type_ or "", "acte")
    return "%s du %s" % (t, date_fr(d))


def lire_justel(texte):
    """Page Justel (version consolidée) -> dict."""
    out = {"type": "justel", "titre": "", "numac": "", "maj": "", "versions": 0, "arrexec": 0, "lien_arrexec": "",
           "modifications": [], "articles": {}}
    m = re.search(r'class="list-item--title">\s*(.*?)</p>', texte, re.S)
    if m:
        out["titre"] = " ".join(texte_html(m.group(1)).split())
    m = re.search(r'<span class="tag">\s*(\d{10})\s*</span>', texte)
    if m:
        out["numac"] = m.group(1)
    m = re.search(r"jour au\s*(\d{2}-\d{2}-\d{4})", texte)
    if m:
        out["maj"] = date_iso(m.group(1))
    m = re.search(r"(\d+)\s+versions\s+archiv", texte)
    if m:
        out["versions"] = int(m.group(1))
    m = re.search(r'href="([^"]*arrexec=1[^"]*)"[^>]*>\s*(\d+)\s', texte)
    if m:
        out["lien_arrexec"], out["arrexec"] = html.unescape(m.group(1)), int(m.group(2))
    # Fiche des modifications
    i = texte.find('id="sw_ad"')
    if i >= 0:
        j = texte.find('<div id="list-', i + 10)
        seg = texte[i:j if j > 0 else len(texte)]
        for m in re.finditer(r'<li>\s*<a href="([^"]*)"[^>]*>\s*(.*?)\s*</a>\s*</li>\s*<p>(.*?)</p>', seg, re.S):
            lib = reparer(" ".join(texte_html(m.group(2)).split()))
            arts = texte_html(m.group(3))
            indetermine = bool(re.search(r"(?i)vigueur.{0,4}d.terminer", arts))
            arts = re.sub(r"(?i)articles?\s+modifi\S*\s*:?", ";", arts)
            arts = re.sub(r"(?i)entr\S*e en vigueur.*$", "", arts, flags=re.S)
            arts = ";".join(dict.fromkeys(x.strip() for x in re.split(r"[;\n]", arts) if x.strip()))
            mm = re.match(r"(.*?)\s+du\s+(\d{2}-\d{2}-\d{4})\s+publi\S*\s+le\s+(\d{2}-\d{2}-\d{4})", lib)
            out["modifications"].append({
                "acte": lib, "type": mm.group(1) if mm else "", "date": date_iso(mm.group(2)) if mm else "",
                "publie": date_iso(mm.group(3)) if mm else "", "lien": html.unescape(m.group(1)),
                "articles": arts, "vigueur_indeterminee": indetermine})
    # Articles
    ancres = list(re.finditer(r'<a name="Art\.([^"]+)"', texte))
    fin_texte = texte.find('id="sw_t"')
    if fin_texte < 0:
        fin_texte = texte.find('id="sw_sign"')
    for k, a in enumerate(ancres):
        debut = a.start()
        fin = ancres[k + 1].start() if k + 1 < len(ancres) else (fin_texte if fin_texte > debut else len(texte))
        t = texte_html(texte[debut:fin])
        corps, _, notes = t.partition("----------")
        num = html.unescape(a.group(1)).strip()
        annots = []
        for mm in ANNOT.finditer(t):
            nature = norm(mm.group(1) or "")
            quoi = "insertion" if nature.startswith("ins") else "abrogation" if nature.startswith("abrog") else \
                "rétablissement" if nature.startswith("r") and "tabli" in nature else "modification"
            annots.append({"acte": mm.group(3), "type": mm.group(2) or "", "art": mm.group(4).strip(),
                           "vigueur": date_iso(mm.group(5)) or mm.group(5).strip(), "nature": quoi})
        vus, uniq = set(), []
        for x in annots:
            c = (x["acte"], x["art"], x["nature"])
            if c not in vus:
                vus.add(c)
                uniq.append(x)
        corps = re.sub(r"^\s*Art\.\s*" + re.escape(num) + r"\s*\.\s*", "", corps.strip())
        abroge = bool(re.match(r"\s*[<(]\s*Abrog", corps)) and len(cle_texte(corps)) < 160
        out["articles"][num] = {"texte": corps.strip(),
                                "cle": hashlib.sha1(cle_texte(corps).encode()).hexdigest()[:16], "annotations": uniq,
                                "abroge": abroge}
    return out


def lire_eurlex(texte):
    out = {"type": "eurlex", "celex": "", "titre": "", "statut": "", "versions": [], "fin_validite": ""}
    m = re.search(r"CELEX[:%3A]+(\d{4}[A-Z]\d{4})", texte)
    if m:
        out["celex"] = "3" + m.group(1) if len(m.group(1)) == 9 else m.group(1)
    m = re.search(r'id="title"[^>]*>(.*?)</p>', texte, re.S)
    if m:
        out["titre"] = " ".join(texte_html(m.group(1)).split())
    plat = texte_html(texte)
    m = re.search(r"((?:Plus en vigueur|En vigueur)\s*:?[^\n]{0,160})", plat)
    if m:
        out["statut"] = " ".join(m.group(1).split())
    m = re.search(r"Date de fin de validit\S*\s*:?\s*(\d{2}/\d{2}/\d{4})", plat)
    if m:
        out["fin_validite"] = date_iso(m.group(1))
    vers = set()
    for m in re.finditer(r'data-celex="0\d{4}[A-Z]\d{4}-(\d{8})"', texte):
        d = m.group(1)
        vers.add("%s-%s-%s" % (d[:4], d[4:6], d[6:]))
    out["versions"] = sorted(vers)
    return out


def lire_arrexec(texte):
    """Liste des arrêtés d'exécution (Justel) -> arrêtés « pays d'origine sûrs » [{date, titre, lien}].
    Chaque arrêté y commence par sa date suivie de « . - » (« 8 DECEMBRE 2025. - Arrêté royal … »)."""
    out = []
    t = re.sub(r"\s+", " ", texte or "")
    debuts = list(re.finditer(r"(\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ\ufffd?]{3,12}\s+\d{4})\s*\.\s*-", t))
    for k, m in enumerate(debuts):
        fin = debuts[k + 1].start() if k + 1 < len(debuts) else len(t)
        morceau = t[m.start():fin]
        if not re.search(r"pays d.{0,2}origine s.{0,6}rs", morceau, re.I):
            continue
        d = date_iso(m.group(1))
        avant = re.findall(r'href="([^"]+)"', t[max(0, m.start() - 600):m.start()])
        dedans = re.findall(r'href="([^"]+)"', morceau)
        lien = html.unescape(avant[-1] if avant else (dedans[0] if dedans else ""))
        titre = " ".join(texte_html(morceau).split())[:400]
        if d and not any(x["date"] == d for x in out):
            out.append({"date": d, "titre": titre, "lien": lien})
    return sorted(out, key=lambda x: x["date"])


def noms_pays_fr():
    """Noms français (normalisés) -> nom d'affichage, pour repérer les pays dans l'arrêté « pays sûrs »."""
    noms = {}
    try:
        import gettext
        import pycountry
        tr = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"])
        for c in pycountry.countries:
            for a in ("name", "common_name"):
                v = getattr(c, a, None)
                if v:
                    fr = tr.gettext(v)
                    noms[norm(fr)] = fr
    except Exception:
        pass
    for fr in ["Albanie", "Bosnie-Herzégovine", "Géorgie", "Inde", "Kosovo", "Macédoine du Nord", "Moldavie",
               "Monténégro", "Serbie", "Brésil", "Maroc", "Tunisie", "Sénégal", "Égypte", "Bangladesh", "Colombie"]:
        noms[norm(fr)] = fr
    return noms


def pays_de_texte(texte):
    """Pays cités dans le dispositif d'un arrêté « pays d'origine sûrs »."""
    t = " " + norm(texte_html(texte) if "<" in (texte or "") else texte) + " "
    trouves = set()
    for n, fr in noms_pays_fr().items():
        if len(n) >= 4 and (" %s " % n) in t:
            trouves.add(fr)
    return sorted(trouves)


def reconnaitre(texte):
    """Type d'une page enregistrée : justel, eurlex, arrexec ou ""."""
    if 'data-celex=' in texte or "eur-lex.europa.eu" in texte[:20000] and "CELEX" in texte:
        return "eurlex"
    if re.search(r"arr.t.s d.ex.cution", texte[:4000], re.I) and 'name="Art.' not in texte and "sw_ad" not in texte:
        return "arrexec"
    if "Justel" in texte[:3000] or "ejustice" in texte[:20000]:
        return "justel"
    return ""


# ---------------------------------------------------------------------------------------------------
# Textes suivis, état, articles cités
# ---------------------------------------------------------------------------------------------------
def chemin_textes(base):
    c = os.path.join(base, TEXTES_NOM)
    if not os.path.exists(c):
        os.makedirs(base, exist_ok=True)
        with open(c, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["id", "type", "adresse", "nom", "repere"])
            w.writerows(TEXTES_DEFAUT)
    return c


def lire_textes(base):
    with open(chemin_textes(base), encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter=";") if (r.get("id") or "").strip()]


def dossier_veille(base):
    d = os.path.join(base, "veille")
    os.makedirs(d, exist_ok=True)
    return d


def lire_json(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defaut


def ecrire_json(chemin, data, compact=False):
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        if compact:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, chemin)


def etat_utilisateur(base):
    return lire_json(os.path.join(dossier_veille(base), "etat.json"), {"sources": {}, "vu_le": "", "bulletin_vu": ""})


def etat_reference():
    return lire_json(REFERENCE, {"sources": {}, "etat_du_droit": ""})


def articles_cites(chemin_biblio, textes):
    """{id du texte suivi: {article: [titres des blocs qui le citent]}} d'après les repères [[LOI1980, art. 50…]]."""
    reperes = {norm(t.get("repere", "")): t["id"] for t in textes if t.get("repere")}
    out = {}
    if not chemin_biblio or not os.path.exists(chemin_biblio):
        return out
    try:
        import bibliotheque as B
        blocs = B.Bibliotheque(chemin_biblio).blocs
    except Exception:
        return out
    for b in blocs:
        txt = " ".join("".join(el.itertext()) for el in b.elements)
        for m in re.finditer(r"\[\[(.+?)\]\]", txt):
            for part in m.group(1).split(";"):
                part = part.strip()
                tete = re.split(r"[,\s]", part, 1)[0]
                tid = reperes.get(norm(tete))
                if not tid:
                    continue
                ma = re.search(r"\bart(?:icle)?s?\.?\s*(\d+(?:er)?[a-z]*(?:/\d+[a-z]*)*)", part)
                if not ma:
                    continue
                art = ma.group(1).replace("1er", "1") if re.fullmatch(r"1er", ma.group(1)) else ma.group(1)
                lst = out.setdefault(tid, {}).setdefault(art, [])
                if b.titre not in lst:
                    lst.append(b.titre)
    return out


# ---------------------------------------------------------------------------------------------------
# Comparaison
# ---------------------------------------------------------------------------------------------------
def _cle_modif(m):
    """Clé d'un acte modificatif, insensible aux accents perdus à l'enregistrement de la page."""
    arts = ";".join(sorted({cle_texte(x) for x in re.split(r"[;,]", m.get("articles", "")) if x.strip()}))
    return (m.get("date", ""), m.get("publie", ""), cle_texte(m.get("type", "")), arts)


def reparer(s):
    """Accents perdus (« publi? », « Arr?t? ») dans les pages enregistrées par le navigateur."""
    s = s or ""
    for a, b in (("publi\ufffd", "publié"), ("Arr\ufffdt\ufffd", "Arrêté"), ("arr\ufffdt\ufffd", "arrêté"),
                 ("D\ufffdcret", "Décret"), ("\ufffd", "é")):
        s = s.replace(a, b)
    return s


def majuscule(s):
    return s[:1].upper() + s[1:]


def de_(nom):
    """« de la loi du… », « de l'arrêté royal… », « du règlement… »."""
    c = court(nom)
    n = norm(c)
    if n.startswith(("reglement", "traite")):
        return "du " + c
    if re.match(r"[aeiouéèêh]", n):
        return "de l'" + c
    return "de la " + c


def avec_article(acte):
    """« loi du 16 juin 2026 » -> « la loi du 16 juin 2026 » ; « arrêté royal… » -> « l'arrêté royal… »."""
    n = norm(acte)
    if re.match(r"[aeiouh]", n):
        return "l'" + acte
    if n.startswith(("loi", "directive", "decision", "ordonnance")):
        return "la " + acte
    return "le " + acte


def court(nom):
    """« Loi du 15 décembre 1980 sur l'accès… » -> « loi du 15 décembre 1980 »."""
    c = re.split(r"\s+(?:sur|relatif|relative|établissant|portant|instituant)\s+|\s+\(", nom or "", 1)[0]
    return c[:1].lower() + c[1:] if not re.match(r"(?:Règlement|Directive)\b", c) else c


def comparer_justel(tid, nom, ancien, nouveau, cites):
    """Liste de changements (dict) entre deux lectures Justel ; ancien peut être None."""
    ch = []
    if not ancien:
        return ch
    connus = {_cle_modif(m) for m in ancien.get("modifications", [])}
    nouvelles = [m for m in nouveau.get("modifications", []) if _cle_modif(m) not in connus]
    cites = cites or {}
    for m in nouvelles:
        touches = [a for a in cites if article_dans(a, m.get("articles", ""))]
        ch.append({"genre": "nouvel_acte", "texte": tid, "nom": nom, "acte": m["acte"], "date": m.get("date", ""),
                   "type_acte": reparer(m.get("type", "")),
                   "publie": m.get("publie", ""), "lien": m.get("lien", ""), "articles": m.get("articles", ""),
                   "indetermine": m.get("vigueur_indeterminee", False),
                   "cites": {a: cites[a] for a in touches}, "priorite": bool(touches)})
    # articles cités : nouvelles annotations, abrogation, texte différent
    anc_arts, nouv_arts = ancien.get("articles", {}), nouveau.get("articles", {})
    for art, blocs in cites.items():
        cand = [k for k in nouv_arts if cle_article(k) == cle_article(art)]
        n = nouv_arts.get(cand[0]) if cand else None
        candA = [k for k in anc_arts if cle_article(k) == cle_article(art)]
        a = anc_arts.get(candA[0]) if candA else None
        if n is None:
            if a is not None:
                ch.append({"genre": "article_disparu", "texte": tid, "nom": nom, "article": art, "blocs": blocs,
                           "priorite": True})
            continue
        if a is None:
            continue
        cles_a = {(x["acte"], x["art"], x["nature"]) for x in a.get("annotations", [])}
        neuves = [x for x in n.get("annotations", []) if (x["acte"], x["art"], x["nature"]) not in cles_a]
        texte_change = a.get("cle") and n.get("cle") and a["cle"] != n["cle"]
        if neuves or texte_change or (n.get("abroge") and not a.get("abroge")):
            ch.append({"genre": "article", "texte": tid, "nom": nom, "article": art, "blocs": blocs,
                       "annotations": neuves, "abroge": n.get("abroge") and not a.get("abroge"),
                       "avant": a.get("texte", ""), "apres": n.get("texte", ""), "priorite": True})
    if nouveau.get("maj") and ancien.get("maj") and nouveau["maj"] != ancien["maj"] and not ch:
        ch.append({"genre": "info", "texte": tid, "nom": nom, "priorite": False,
                   "message": "Justel a été mis à jour (%s), sans modification des articles suivis."
                              % date_fr(nouveau["maj"])})
    return ch


def comparer_eurlex(tid, nom, ancien, nouveau, cites):
    ch = []
    if not ancien:
        return ch
    connues = set(ancien.get("versions", []))
    ref = max(connues) if connues else ""
    for v in nouveau.get("versions", []):
        if v not in connues and v > ref:
            ch.append({"genre": "ue_version", "texte": tid, "nom": nom, "date": v, "celex": nouveau.get("celex", ""),
                       "cites": cites or {}, "priorite": bool(cites)})
    if nouveau.get("fin_validite") and nouveau["fin_validite"] != ancien.get("fin_validite"):
        ch.append({"genre": "ue_fin", "texte": tid, "nom": nom, "date": nouveau["fin_validite"],
                   "celex": nouveau.get("celex", ""), "cites": cites or {}, "priorite": True})
    elif nouveau.get("statut", "").lower().startswith("plus en vigueur") and \
            not ancien.get("statut", "").lower().startswith("plus en vigueur"):
        ch.append({"genre": "ue_fin", "texte": tid, "nom": nom, "date": "", "celex": nouveau.get("celex", ""),
                   "cites": cites or {}, "priorite": True})
    return ch


def comparer_pays(tid, nom, ancien, nouveau):
    ch = []
    if not ancien:
        return ch
    connus = {a["date"] for a in ancien.get("arretes", [])}
    for a in nouveau.get("arretes", []):
        if a["date"] not in connus and a["date"] > (max(connus) if connus else ""):
            avant = set(ancien.get("pays", []))
            apres = set(nouveau.get("pays", [])) if nouveau.get("pays_de") == a["date"] else set()
            ch.append({"genre": "pays_surs", "texte": tid, "nom": nom, "date": a["date"], "lien": a.get("lien", ""),
                       "ajoutes": sorted(apres - avant) if apres and avant else [],
                       "retires": sorted(avant - apres) if apres and avant else [],
                       "liste": sorted(apres), "priorite": True})
    return ch


# ---------------------------------------------------------------------------------------------------
# Vérification
# ---------------------------------------------------------------------------------------------------
class Verification:
    def __init__(self, base, chemin_biblio=None, session=None, log=print, user_agent=None):
        self.base = base
        self.textes = lire_textes(base)
        self.cites = articles_cites(chemin_biblio, self.textes)
        self.session = session
        self.log = log
        self.ua = user_agent
        self.lectures = {}     # id -> lecture actuelle
        self.erreurs = {}      # id -> message
        self._dernier_hote = {}

    def _get(self, url):
        import requests
        from urllib.parse import urlparse
        hote = urlparse(url).netloc
        attente = PAUSE - (time.time() - self._dernier_hote.get(hote, 0))
        if attente > 0:
            time.sleep(attente)
        s = self.session or requests.Session()
        if self.ua:
            s.headers["User-Agent"] = self.ua
        r = s.get(url, timeout=60)
        self._dernier_hote[hote] = time.time()
        r.raise_for_status()
        return decoder(r.content, r.headers.get("Content-Type", ""))

    def url_de(self, t):
        if t["type"] == "eurlex":
            return EURLEX_URL.format(celex=t["adresse"])
        return t["adresse"]

    def en_ligne(self):
        """Lit toutes les pages en ligne (une par texte, plus la liste des arrêtés d'exécution)."""
        for t in self.textes:
            if t["type"] == "pays_surs":
                continue
            url = self.url_de(t)
            self.log("  %s…" % t["nom"][:70])
            try:
                self.analyser(t, self._get(url))
            except Exception as e:
                self.erreurs[t["id"]] = "page non lue (%s) : %s" % (e.__class__.__name__, url)
        for t in self.textes:
            if t["type"] != "pays_surs":
                continue
            mere = self.lectures.get(t["adresse"]) or {}
            lien = mere.get("lien_arrexec")
            if not lien:
                self.erreurs[t["id"]] = "liste des arrêtés d'exécution introuvable (la page de la loi n'a pas été lue)"
                continue
            try:
                self.log("  Arrêtés d'exécution (pays d'origine sûrs)…")
                lec = {"type": "pays_surs", "arretes": lire_arrexec(self._get(lien))}
                if lec["arretes"]:
                    dernier = lec["arretes"][-1]
                    if dernier.get("lien"):
                        try:
                            lec["pays"] = pays_de_texte(self._get(dernier["lien"]))
                            lec["pays_de"] = dernier["date"]
                        except Exception:
                            pass
                self.lectures[t["id"]] = lec
            except Exception as e:
                self.erreurs[t["id"]] = "liste des arrêtés d'exécution non lue (%s)" % e.__class__.__name__

    def analyser(self, t, texte):
        if t["type"] == "justel":
            self.lectures[t["id"]] = lire_justel(texte)
        elif t["type"] == "eurlex":
            self.lectures[t["id"]] = lire_eurlex(texte)

    def pages_enregistrees(self, chemins):
        """Analyse des pages enregistrées à la main (mode « liens seulement »)."""
        par_numac = {}
        for t in self.textes:
            m = re.search(r"/(\d{10})/justel", t.get("adresse", ""))
            if m:
                par_numac[m.group(1)] = t
        for c in chemins:
            with open(c, "rb") as f:
                texte = decoder(f.read())
            genre = reconnaitre(texte)
            if genre == "justel":
                lec = lire_justel(texte)
                t = par_numac.get(lec.get("numac"))
                if t:
                    self.lectures[t["id"]] = lec
                    self.log("  %s : %s" % (os.path.basename(c), t["nom"][:60]))
                else:
                    self.log("  %s : page Justel d'un texte non suivi (numac %s)" % (os.path.basename(c), lec.get("numac")))
            elif genre == "eurlex":
                lec = lire_eurlex(texte)
                t = next((x for x in self.textes if x["type"] == "eurlex" and x["adresse"] == lec.get("celex")), None)
                if t:
                    self.lectures[t["id"]] = lec
                    self.log("  %s : %s" % (os.path.basename(c), t["nom"][:60]))
                else:
                    self.log("  %s : page EUR-Lex d'un acte non suivi (%s)" % (os.path.basename(c), lec.get("celex")))
            elif genre == "arrexec":
                t = next((x for x in self.textes if x["type"] == "pays_surs"), None)
                if t:
                    self.lectures[t["id"]] = {"type": "pays_surs", "arretes": lire_arrexec(texte)}
                    self.log("  %s : liste des arrêtés d'exécution" % os.path.basename(c))
            else:
                self.log("  %s : page non reconnue" % os.path.basename(c))

    def liens(self):
        out = [(t["nom"], self.url_de(t)) for t in self.textes if t["type"] != "pays_surs"]
        for t in self.textes:
            if t["type"] == "pays_surs":
                out.append((t["nom"] + " : liste des arrêtés d'exécution de la loi (page de la loi → « arrêtés "
                            "d'exécution »)", next((x["adresse"] for x in self.textes if x["id"] == t["adresse"]), "")))
        return out

    def comparer(self):
        """-> (changements, base de comparaison par texte)."""
        user = etat_utilisateur(self.base).get("sources", {})
        ref = etat_reference().get("sources", {})
        changements, bases = [], {}
        for t in self.textes:
            lec = self.lectures.get(t["id"])
            if not lec:
                continue
            if t["id"] in user:
                ancien, bases[t["id"]] = user[t["id"]], "votre dernière vérification (%s)" % \
                    date_fr(user[t["id"]].get("_vu_le", ""))
            elif t["id"] in ref:
                ancien, bases[t["id"]] = ref[t["id"]], "l'état du droit dans le programme (%s)" % \
                    date_fr(ref[t["id"]].get("_vu_le", ""))
            else:
                ancien, bases[t["id"]] = None, "première vérification : état enregistré"
            cites = self.cites.get(t["id"], {})
            if t["type"] == "justel":
                changements += comparer_justel(t["id"], t["nom"], ancien, lec, cites)
            elif t["type"] == "eurlex":
                changements += comparer_eurlex(t["id"], t["nom"], ancien, lec, cites)
            elif t["type"] == "pays_surs":
                changements += comparer_pays(t["id"], t["nom"], ancien, lec)
        changements.sort(key=lambda c: (not c.get("priorite"), c.get("texte", "")))
        return changements, bases

    def marquer_vu(self, aujourdhui=None):
        """Enregistre la lecture actuelle comme état connu (les prochaines vérifications partent d'ici)."""
        aujourdhui = aujourdhui or dt.date.today().isoformat()
        chemin = os.path.join(dossier_veille(self.base), "etat.json")
        etat = etat_utilisateur(self.base)
        for tid, lec in self.lectures.items():
            lec = dict(lec)
            lec["_vu_le"] = aujourdhui
            if lec.get("type") == "justel":
                # on garde le texte des articles cités (pour montrer « avant / après » la prochaine fois),
                # et seulement la clé et les annotations des autres (fichier léger)
                cites = self.cites.get(tid, {})
                arts = {}
                for k, v in lec.get("articles", {}).items():
                    garde = any(cle_article(k) == cle_article(a) for a in cites)
                    arts[k] = v if garde else {"cle": v.get("cle"), "annotations": v.get("annotations"),
                                               "abroge": v.get("abroge")}
                lec["articles"] = arts
            ancien = etat["sources"].get(tid, {})
            if lec.get("type") == "pays_surs" and not lec.get("pays") and ancien.get("pays"):
                lec["pays"], lec["pays_de"] = ancien["pays"], ancien.get("pays_de")
            etat["sources"][tid] = lec
        etat["vu_le"] = aujourdhui
        ecrire_json(chemin, etat)
        return chemin


# ---------------------------------------------------------------------------------------------------
# Bulletin de veille (BULLETIN.md sur GitHub)
# ---------------------------------------------------------------------------------------------------
def lire_bulletin(texte):
    """BULLETIN.md -> {"version": "1.0.1", "entrees": [{date, titre, textes, blocs, importance, liens, texte}]}.

    Format (voir BULLETIN.md) :
        Version du programme : 1.0.1
        ## 2026-09-29 | Titre de l'information
        Textes : LOI1980 art. 50 ; REG2024-1348 art. 42
        Blocs : Délai dépassé : ni irrecevabilité ni rejet automatique
        Importance : haute
        Lien : https://…
        Explication en langage simple, sur autant de lignes que nécessaire.
    """
    out = {"version": "", "entrees": []}
    texte = re.sub(r"(?s)<!--.*?-->", "", texte or "")  # mode d'emploi en commentaire : ignoré
    m = re.search(r"(?im)^\s*version du programme\s*:\s*([\d.]+)", texte)
    if m:
        out["version"] = m.group(1)
    for bloc in re.split(r"(?m)^##\s+", texte)[1:]:
        lignes = bloc.strip("\n").split("\n")
        tete = lignes[0]
        mm = re.match(r"\s*(\d{4}-\d{2}-\d{2})\s*[|–—-]\s*(.+)", tete)
        if not mm:
            continue
        e = {"date": mm.group(1), "titre": mm.group(2).strip(), "textes": "", "blocs": "", "importance": "",
             "liens": [], "texte": ""}
        corps = []
        for l in lignes[1:]:
            mc = re.match(r"\s*(Textes?|Blocs?|Importance|Liens?)\s*:\s*(.*)", l, re.I)
            if mc and not corps:
                cle = norm(mc.group(1)).rstrip("s")
                val = mc.group(2).strip()
                if cle == "lien":
                    e["liens"].append(val)
                elif cle == "texte":
                    e["textes"] = val
                elif cle == "bloc":
                    e["blocs"] = val
                else:
                    e["importance"] = val
            else:
                corps.append(l)
        e["texte"] = "\n".join(corps).strip()
        out["entrees"].append(e)
    out["entrees"].sort(key=lambda e: e["date"], reverse=True)
    return out


def telecharger_bulletin(url=BULLETIN_URL, session=None, user_agent=None):
    import requests
    s = session or requests.Session()
    if user_agent:
        s.headers["User-Agent"] = user_agent
    r = s.get(url, timeout=30)
    r.raise_for_status()
    return lire_bulletin(decoder(r.content, r.headers.get("Content-Type", "")))


def version_plus_recente(a, b):
    """Vrai si la version a est plus récente que b (« 1.0.1 » > « 1.0 »)."""
    def t(v):
        return tuple(int(x) for x in re.findall(r"\d+", v or "0"))
    return t(a) > t(b)


# ---------------------------------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------------------------------
def _diff_html(avant, apres):
    a, b = re.findall(r"\S+|\s+", avant or ""), re.findall(r"\S+|\s+", apres or "")
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(html.escape("".join(a[i1:i2])))
        if op in ("delete", "replace"):
            out.append("<del>%s</del>" % html.escape("".join(a[i1:i2])))
        if op in ("insert", "replace"):
            out.append("<ins>%s</ins>" % html.escape("".join(b[j1:j2])))
    return "".join(out).replace("\n", "<br>")


def _blocs_txt(blocs):
    if not blocs:
        return ""
    if len(blocs) == 1:
        return "Il est cité dans le bloc « %s »." % blocs[0]
    return "Il est cité dans %d blocs : %s." % (len(blocs), " ; ".join("« %s »" % b for b in blocs))


def phrase(c):
    """Phrase en langage courant pour un changement."""
    g = c["genre"]
    if g == "nouvel_acte":
        typ = (c.get("type_acte") or "").strip().lower() or "acte"
        acte = ("%s du %s" % (typ, date_fr(c["date"]))) if c.get("date") else c["acte"]
        s = "%s : modification par %s%s." % (majuscule(court(c["nom"])), avec_article(acte),
                                           (" (Moniteur belge du %s)" % date_fr(c["publie"])) if c.get("publie") else "")
        arts = [x for x in (c.get("articles") or "").split(";") if x]
        if arts:
            s += " Articles touchés : %s." % ("; ".join(arts) if len(arts) <= 15 else
                                            "%s… (%d au total)" % ("; ".join(arts[:12]), len(arts)))
        if c.get("indetermine"):
            s += " Entrée en vigueur encore à déterminer."
        for a, blocs in (c.get("cites") or {}).items():
            s += " L'article %s est cité dans vos blocs : %s." % (a, " ; ".join("« %s »" % b for b in blocs))
        return s
    if g == "article":
        acts = c.get("annotations") or []
        if c.get("abroge"):
            s = "L'article %s %s a été abrogé, c'est-à-dire supprimé" % (c["article"], de_(c["nom"]))
        else:
            s = "L'article %s %s a été modifié" % (c["article"], de_(c["nom"]))
        if acts:
            s += " par " + " ; ".join("%s (article %s), en vigueur le %s" % (
                avec_article(nom_acte(x["type"], x["acte"])), x["art"], date_fr(x["vigueur"]) if re.match(r"\d{4}-", x["vigueur"])
                else x["vigueur"]) for x in acts)
        s += ". " + _blocs_txt(c.get("blocs"))
        s += " Relisez ces blocs : ils se fondent peut-être sur l'ancien texte."
        return s
    if g == "article_disparu":
        return "L'article %s %s ne figure plus dans le texte consolidé. %s À vérifier." % (
            c["article"], de_(c["nom"]), _blocs_txt(c.get("blocs")))
    if g == "ue_version":
        s = "%s : nouvelle version consolidée au %s, ce qui signifie que l'acte a été modifié." % (
            c["nom"], date_fr(c["date"]))
        if c.get("cites"):
            s += " Vos blocs citent les articles %s : vérifiez s'ils sont touchés." % ", ".join(sorted(c["cites"]))
        return s
    if g == "ue_fin":
        return "%s : n'est plus en vigueur%s. %s" % (
            c["nom"], (" depuis le " + date_fr(c["date"])) if c.get("date") else "",
            "Vos blocs le citent : remplacez les références." if c.get("cites") else "")
    if g == "pays_surs":
        s = "Nouvel arrêté royal établissant la liste des pays d'origine sûrs (%s)." % date_fr(c["date"])
        if c.get("ajoutes"):
            s += " Pays ajoutés : %s." % ", ".join(c["ajoutes"])
        if c.get("retires"):
            s += " Pays retirés : %s." % ", ".join(c["retires"])
        if c.get("liste") and not (c.get("ajoutes") or c.get("retires")):
            s += " Liste : %s." % ", ".join(c["liste"])
        return s
    return c.get("message", "")


def rapport_texte(changements, bases, erreurs, bulletin=None, bulletin_vu="", version="", textes_verifies=True):
    L = []
    prio = [c for c in changements if c.get("priorite")]
    autres = [c for c in changements if not c.get("priorite")]
    if textes_verifies and not bases:
        L.append("## Vérification impossible")
        L.append("Aucun texte n'a pu être lu (connexion refusée ou coupée). Cliquez sur « Ouvrir les pages dans le "
                 "navigateur », enregistrez chaque page (Ctrl+S), puis « Analyser des pages enregistrées… ».")
    elif not changements and textes_verifies:
        L.append("## Aucun changement repéré")
        L.append("Les textes vérifiés n'ont pas changé depuis la dernière référence.")
    if prio:
        L.append("## À relire en priorité (%d)" % len(prio))
        L += ["- " + phrase(c) for c in prio]
    if autres:
        L.append("## Autres changements (%d)" % len(autres))
        L += ["- " + phrase(c) for c in autres]
    if bulletin and bulletin.get("entrees"):
        neuves = [e for e in bulletin["entrees"] if e["date"] > (bulletin_vu or "")]
        L.append("## Bulletin de veille (%s)" % ("%d nouvelle(s) information(s)" % len(neuves) if neuves
                                                 else "rien de nouveau"))
        for e in (neuves or bulletin["entrees"][:2]):
            L.append("- %s – %s" % (date_fr(e["date"]), e["titre"]))
            if e["texte"]:
                L.append("  " + e["texte"].replace("\n", "\n  "))
    if bulletin and bulletin.get("version") and version and version_plus_recente(bulletin["version"], version):
        L.append("## Nouvelle version du programme : %s (vous avez la %s)" % (bulletin["version"], version))
    if erreurs:
        L.append("## Textes non vérifiés")
        L += ["- %s" % m for m in erreurs.values()]
    if bases:
        L.append("## Base de comparaison")
        L += ["- %s : %s" % (k, v) for k, v in bases.items()]
    return "\n".join(L)


def rapport_html(chemin, changements, bases, erreurs, textes, lectures, bulletin=None, bulletin_vu=""):
    noms = {t["id"]: t["nom"] for t in textes}
    h = ["<!doctype html><meta charset='utf-8'><title>Veille législative</title><style>"
         "body{font-family:Arial,sans-serif;max-width:980px;margin:2em auto;line-height:1.45;color:#222;padding:0 1em}"
         "h1{color:#1c2440}h2{color:#1c2440;border-bottom:2px solid #ff7a30;padding-bottom:.2em;margin-top:1.8em}"
         ".c{border-left:4px solid #ff7a30;background:#fff7f1;padding:.6em .9em;margin:.8em 0}"
         ".c.b{border-color:#9aa3b5;background:#f5f6f8}.meta{color:#666;font-size:.9em}"
         "del{background:#ffd7d7;text-decoration:line-through}ins{background:#d6f5d6;text-decoration:none}"
         "details{margin:.4em 0}.diff{font-family:Georgia,serif;background:#fff;border:1px solid #ddd;padding:.7em}"
         "table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:.3em .6em;text-align:left}</style>",
         "<h1>Veille législative</h1><p class='meta'>Vérification du %s. Le programme repère les modifications ; "
         "il n'en tire pas de conclusion juridique. Les textes officiels (liens) font foi.</p>"
         % date_fr(dt.date.today().isoformat())]
    prio = [c for c in changements if c.get("priorite")]
    autres = [c for c in changements if not c.get("priorite")]
    if not bases:
        h.append("<h2>Vérification impossible</h2><p>Aucun texte n'a pu être lu. Dans Probasile : « Ouvrir les pages "
                 "dans le navigateur », enregistrez chaque page, puis « Analyser des pages enregistrées… ».</p>")
    elif not changements:
        h.append("<h2>Aucun changement repéré</h2><p>Les textes vérifiés n'ont pas changé depuis la dernière "
                 "référence.</p>")

    def carte(c, cls=""):
        s = ["<div class='c %s'><p>%s</p>" % (cls, html.escape(phrase(c)))]
        if c["genre"] == "article" and c.get("avant") and c.get("apres"):
            s.append("<details open><summary>Texte avant / après (supprimé en rouge, ajouté en vert)</summary>"
                     "<div class='diff'>%s</div></details>" % _diff_html(c["avant"], c["apres"]))
        elif c["genre"] == "article" and c.get("apres"):
            s.append("<details><summary>Texte actuel de l'article</summary><div class='diff'>%s</div></details>"
                     % html.escape(c["apres"]).replace("\n", "<br>"))
        lien = c.get("lien") or ""
        if c["genre"].startswith("ue_") and c.get("celex"):
            lien = EURLEX_TXT.format(celex=c["celex"])
        if c["genre"] in ("article", "article_disparu"):
            t = next((x for x in textes if x["id"] == c["texte"]), None)
            lien = (t["adresse"] + "#Art." + c["article"]) if t else ""
        if lien:
            s.append("<p class='meta'><a href='%s'>%s</a></p>" % (html.escape(lien), html.escape(lien)))
        s.append("</div>")
        return "".join(s)

    if prio:
        h.append("<h2>À relire en priorité (%d)</h2>" % len(prio))
        h += [carte(c) for c in prio]
    if autres:
        h.append("<h2>Autres changements (%d)</h2>" % len(autres))
        h += [carte(c, "b") for c in autres]
    if bulletin and bulletin.get("entrees"):
        h.append("<h2>Bulletin de veille</h2><p class='meta'>Rédigé par des juristes : "
                 "<a href='%s'>%s</a></p>" % (BULLETIN_PAGE, BULLETIN_PAGE))
        for e in bulletin["entrees"][:12]:
            neuf = e["date"] > (bulletin_vu or "")
            h.append("<div class='c%s'><p><b>%s%s – %s</b></p>%s%s%s%s</div>" % (
                "" if neuf else " b", "🆕 " if neuf else "", html.escape(date_fr(e["date"])), html.escape(e["titre"]),
                "<p>%s</p>" % html.escape(e["texte"]).replace("\n\n", "</p><p>").replace("\n", "<br>") if e["texte"] else "",
                "<p class='meta'>Textes : %s</p>" % html.escape(e["textes"]) if e["textes"] else "",
                "<p class='meta'>Blocs à relire : %s</p>" % html.escape(e["blocs"]) if e["blocs"] else "",
                "".join("<p class='meta'><a href='%s'>%s</a></p>" % (html.escape(u), html.escape(u)) for u in e["liens"])))
    h.append("<h2>État des textes suivis</h2><table><tr><th>Texte</th><th>Situation lue</th><th>Comparé à</th></tr>")
    for t in textes:
        lec = lectures.get(t["id"])
        if lec is None:
            sit = erreurs.get(t["id"], "non vérifié")
        elif lec.get("type") == "justel":
            sit = "Justel mis à jour au %s ; %d modifications recensées" % (
                date_fr(lec.get("maj", "")), len(lec.get("modifications", [])))
        elif lec.get("type") == "eurlex":
            sit = (lec.get("statut") or "") + (" ; dernière version consolidée : %s" % date_fr(lec["versions"][-1])
                                               if lec.get("versions") else "")
        else:
            arr = lec.get("arretes", [])
            sit = ("dernier arrêté : %s" % date_fr(arr[-1]["date"])) if arr else "aucun arrêté trouvé"
            if lec.get("pays"):
                sit += " ; pays : " + ", ".join(lec["pays"])
        h.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (html.escape(t["nom"]), html.escape(sit),
                                                                 html.escape(bases.get(t["id"], "—"))))
    h.append("</table>")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("".join(h))
    return chemin


# ---------------------------------------------------------------------------------------------------
# Construction de l'état de référence livré avec le programme (outil du mainteneur)
# ---------------------------------------------------------------------------------------------------
def construire_reference(pages, date_etat, sortie=REFERENCE, eu_connues=None):
    """pages : {id: chemin d'une page enregistrée} ; eu_connues : {id: [dates de versions consolidées déjà
    prises en compte dans les blocs]} pour les actes UE sans page enregistrée."""
    ref = {"etat_du_droit": date_etat, "sources": {}}
    for tid, chemin in (pages or {}).items():
        with open(chemin, "rb") as f:
            texte = decoder(f.read())
        genre = reconnaitre(texte)
        lec = lire_justel(texte) if genre == "justel" else lire_eurlex(texte) if genre == "eurlex" else None
        if lec is None:
            continue
        if genre == "justel":   # pas de texte (accents parfois perdus à l'enregistrement) : clés et annotations
            lec["articles"] = {k: {"cle": v["cle"], "annotations": v["annotations"], "abroge": v["abroge"]}
                               for k, v in lec["articles"].items()}
        lec["_vu_le"] = date_etat
        ref["sources"][tid] = lec
    for tid, versions in (eu_connues or {}).items():
        ref["sources"].setdefault(tid, {"type": "eurlex", "versions": versions, "statut": "", "fin_validite": "",
                                        "_vu_le": date_etat})
    ecrire_json(sortie, ref, compact=True)
    return ref
