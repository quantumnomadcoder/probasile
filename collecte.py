#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Probasile – collecte de sources sur la situation des droits humains (et de la santé) par pays,
pour les dossiers de protection internationale, de non-délivrance d'OQT, 9bis et 9ter.

Modules
- ONU, organes de traités : documents retrouvés par leur cote (observations finales,
  listes de points, rapports de l'État), en français si disponible, sinon en anglais.
- ONU, base des organes de traités : état des rapports (retards) et tous les documents
  listés pour le pays (courriers de suivi, anciennes cotes d'avant 2008...).
- ONU, Examen périodique universel (EPU) : rapport national, compilation de l'ONU,
  résumé des parties prenantes, pour chaque session.
- Ratifications : état des traités (Collection des traités de l'ONU).
- ReliefWeb : rapports d'ONG et d'agences (HRW, Amnesty, HCDH, OMS...).
- Veille presse / sources nationales : flux RSS et recherches Google Actualités.
- Import : fichiers déjà téléchargés ou liste de liens (ex. communications des
  procédures spéciales « AL IDN 5/2026 »), avec fiche automatique.

Chaque document est rangé dans un dossier par pays et décrit dans une fiche
(sources.csv). Un journal horodaté liste les nouveautés de chaque collecte.
Mode « liens seulement » : rien n'est téléchargé, une page HTML liste les liens directs.

Lancement :
    python collecte.py                  -> interface graphique
    python collecte.py --pays IDN ...   -> ligne de commande (voir --help)
"""
import argparse
import csv
import datetime as dt
import email.utils
import gettext
import html
import io
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

if __name__ == "__main__":  # pour que le module jurisprudence partage ce même module
    sys.modules.setdefault("collecte", sys.modules[__name__])

try:
    import requests
except ImportError:  # message clair plutôt qu'une trace Python
    print("Le module 'requests' manque. Lancez d'abord l'installation (installer_windows.bat ou installer_mac_linux.sh).")
    sys.exit(1)

try:
    import pycountry
except ImportError:
    pycountry = None

import warnings
warnings.filterwarnings("ignore")
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

VERSION = "0.9.25"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".collecte_pays.json")
USER_AGENT = "Mozilla/5.0 (collecte-pays/%s; recherche juridique non commerciale)" % VERSION
PAUSE = 0.5  # secondes entre deux requêtes, pour rester courtois avec les serveurs

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august",
             "september", "october", "november", "december"]


def date_fr(d):
    return "%s %s %d" % ("1er" if d.day == 1 else d.day, MOIS[d.month - 1], d.year)


def slug(s, n=80):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")
    return s[:n] or "document"


def norm(s):
    s = re.sub(r"[’‘`´]", " ", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def maintenant_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# Pays
# ---------------------------------------------------------------------------
def liste_pays():
    """[(iso3, nom_fr, nom_en)] triés par nom français."""
    if pycountry is None:
        return [("IDN", "Indonésie", "Indonesia")]
    try:
        tr = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"]).gettext
    except Exception:
        tr = lambda s: s
    out = [(c.alpha_3, tr(c.name), c.name) for c in pycountry.countries]
    out.sort(key=lambda t: norm(t[1]))
    return out


def forme_de(nom_fr):
    """Proposition de « de l’Indonésie » / « du Maroc » / « de la Russie » / « des Philippines ».
    Heuristique : toujours modifiable dans l'interface."""
    n = nom_fr.strip()
    masculins_e = {"mexique", "cambodge", "mozambique", "zimbabwe", "belize", "suriname"}
    if n.endswith("s") and norm(n) not in {"laos", "honduras"}:
        return "des " + n
    if norm(n)[:1] in "aeiouy" or n[:1] in "ÉÈÊÎÔÛ":
        return "de l’" + n
    if n.endswith("e") and norm(n) not in masculins_e:
        return "de la " + n
    return "du " + n


# ---------------------------------------------------------------------------
# Détection de fichiers, dates, références
# ---------------------------------------------------------------------------
def type_fichier(premiers_octets):
    if premiers_octets.startswith(b"%PDF"):
        return "pdf"
    if premiers_octets.startswith(b"PK"):
        return "docx"
    if premiers_octets.startswith(b"\xd0\xcf\x11\xe0"):
        return "doc"
    return None


DATE_RE_FR = re.compile(r"\b(\d{1,2})(?:er)?\s+(%s)\s+((?:19|20)\d\d)\b" % "|".join(MOIS), re.I)
DATE_RE_EN = re.compile(r"\b(\d{1,2})\s+(%s)\s+((?:19|20)\d\d)\b" % "|".join(MONTHS_EN), re.I)
REF_PS = re.compile(r"\b(J?(?:AL|UA|OL))\s+([A-Z]{3})\s+(\d{1,3}/\d{4})\b")


def date_dans_texte(txt):
    m = DATE_RE_FR.search(txt or "")
    if m:
        j, mois, a = int(m.group(1)), MOIS.index(m.group(2).lower()) + 1, int(m.group(3))
        try:
            return date_fr(dt.date(a, mois, j))
        except ValueError:
            return ""
    m = DATE_RE_EN.search(txt or "")
    if m:
        j, mois, a = int(m.group(1)), MONTHS_EN.index(m.group(2).lower()) + 1, int(m.group(3))
        try:
            return date_fr(dt.date(a, mois, j))
        except ValueError:
            return ""
    return ""


def texte_pdf(contenu, pages=1):
    if PdfReader is None:
        return ""
    try:
        r = PdfReader(io.BytesIO(contenu))
        return "\n".join((r.pages[i].extract_text() or "") for i in range(min(pages, len(r.pages))))
    except Exception:
        return ""


def date_depuis_pdf(contenu):
    """Date de distribution sur la première page (« Distr. générale 3 mai 2024 »)."""
    txt = texte_pdf(contenu)
    m = re.search(r"Distr\.?\s*(?:générale|generale|restreinte|general|limited|réservée)?\s*[:.]?\s*(.{0,40})", txt or "",
                  re.I | re.S)
    if m:
        d = date_dans_texte(" ".join(m.group(1).split()))
        if d:
            return d
    return date_dans_texte(txt)


# ---------------------------------------------------------------------------
# ONU : cotes des organes de traités et de l'EPU
# ---------------------------------------------------------------------------
COMITES = {
    "CCPR": ("CCPR/C", "Comité des droits de l’homme"),
    "CAT": ("CAT/C", "Comité contre la torture"),
    "CESCR": ("E/C.12", "Comité des droits économiques, sociaux et culturels"),
    "CEDAW": ("CEDAW/C", "Comité pour l’élimination de la discrimination à l’égard des femmes"),
    "CRC": ("CRC/C", "Comité des droits de l’enfant"),
    "CERD": ("CERD/C", "Comité pour l’élimination de la discrimination raciale"),
    "CED": ("CED/C", "Comité des disparitions forcées"),
    "CRPD": ("CRPD/C", "Comité des droits des personnes handicapées"),
    "CMW": ("CMW/C", "Comité des travailleurs migrants"),
}
CODES_ISO3 = {c.alpha_3 for c in pycountry.countries} if pycountry else set()


def comite_du_document(sym, texte=""):
    """Comité auquel se rattache une cote (CCPR/C/…, E/C.12/…, INT/CAT/…, CAT/OP/… puis CAT), sinon ""."""
    s_ = (sym or "").upper().replace(" ", "").replace("_", "/")  # noms de fichiers du type E_C.12_2014_SR.7_FRE
    for c, (pref, _) in COMITES.items():
        if s_.startswith(pref.upper() + "/") or s_.startswith("INT/%s/" % c):
            return c
    if s_.startswith(("CAT/OP/", "INT/SPT/")):
        return "CAT"
    return next((c for c in COMITES if re.search(r"(^|[^A-Z])%s([^A-Z]|$)" % c, (sym or "") + " " + (texte or ""))), "")


TYPES_DOC = {
    "CO": "Observations finales",
    "Q": "Listes de points",
    "QPR": "Listes de points avant rapport",
    "R": "Rapports de l’État",
}
N_MAX = 8
# Deux accès aux documents de l'ONU par cote : le Système de diffusion électronique des
# documents (ODS) et la base des organes de traités. Le premier est essayé d'abord.
ODS_URL = "https://documents.un.org/api/symbol/access?s={sym}&l={lang}&t=pdf"
TB_URL = "https://tbinternet.ohchr.org/_layouts/15/treatybodyexternal/Download.aspx?symbolno={sym}&Lang={lang}"
TB_BASE = "https://tbinternet.ohchr.org/_layouts/15/treatybodyexternal/"
TB_PAYS = TB_BASE + "Countries.aspx?CountryCode={iso}&Lang={lang}"
TB_RECHERCHE = TB_BASE + "TBSearch.aspx?Lang=en&CountryID={cid}"

ORDINAUX = ["initial", "deuxième", "troisième", "quatrième", "cinquième", "sixième", "septième",
            "huitième", "neuvième", "dixième", "onzième", "douzième"]


def cote(comite, iso, type_doc, num):
    prefixe = COMITES[comite][0]
    if type_doc == "R":
        return "%s/%s/%s" % (prefixe, iso, num)
    return "%s/%s/%s/%s" % (prefixe, iso, type_doc, num)


def libelle_rapport(num):
    parts = [int(p) for p in str(num).split("-")]
    o = lambda k: ORDINAUX[k - 1] if 0 < k <= len(ORDINAUX) else "%de" % k
    if len(parts) == 1:
        return "rapport initial" if parts[0] == 1 else "%s rapport périodique" % o(parts[0])
    if parts[0] == 1:
        return "rapport valant rapport initial et %s rapport périodique" % o(parts[-1])
    return "rapport valant %s et %s rapports périodiques" % (o(parts[0]), o(parts[-1]))


def titre_tb(type_doc, num, de_pays):
    r = libelle_rapport(num)
    if type_doc == "CO":
        return "observations finales concernant le %s %s" % (r, de_pays)
    if type_doc == "Q":
        return "liste de points concernant le %s %s" % (r, de_pays)
    if type_doc == "QPR":
        return "liste de points établie avant la soumission du %s %s" % (r, de_pays)
    return "%s %s" % (r[0].upper() + r[1:], de_pays)


EPU_DOCS = {
    "1": "Examen périodique universel (%se session), rapport national %s",
    "2": "Examen périodique universel (%se session), compilation d’informations des Nations Unies concernant %s",
    "3": "Examen périodique universel (%se session), résumé des communications des parties prenantes concernant %s",
}


def sans_de(de_pays):
    """« de l’Indonésie » -> « l’Indonésie » ; « du Maroc » -> « le Maroc » ; « des Philippines » -> « les Philippines »."""
    d = de_pays.strip()
    for a, b in (("de l’", "l’"), ("de l'", "l'"), ("de la ", "la "), ("du ", "le "), ("des ", "les "), ("de ", "")):
        if d.startswith(a):
            return b + d[len(a):]
    return d
EPU_MAX_SESSION = 3 * (dt.date.today().year - 2008) + 6  # large : environ trois sessions par an depuis 2008


UPR_PAGE = "https://www.ohchr.org/en/hr-bodies/upr/{iso2}-index"
# Langue principale de la presse (codes Google Actualités), pour les pays d'origine fréquents
LANGUE_PAYS = {"IDN": "id", "IRN": "fa", "AFG": "fa", "TUR": "tr", "RUS": "ru", "UKR": "uk", "SYR": "ar", "IRQ": "ar",
               "EGY": "ar", "MAR": "fr", "DZA": "fr", "TUN": "fr", "COD": "fr", "CMR": "fr", "GIN": "fr", "SEN": "fr",
               "CIV": "fr", "BDI": "fr", "RWA": "fr", "HTI": "fr", "ERI": "en", "SOM": "en", "ETH": "en", "NGA": "en",
               "PAK": "en", "IND": "en", "BGD": "bn", "LKA": "en", "NPL": "ne", "CHN": "zh-CN", "VNM": "vi", "PHL": "en",
               "MMR": "my", "THA": "th", "MYS": "ms", "GEO": "ka", "ARM": "hy", "AZE": "az", "ALB": "sq", "SRB": "sr",
               "VEN": "es", "COL": "es", "CUB": "es", "SLV": "es", "HND": "es", "NIC": "es", "BRA": "pt-BR",
               "AGO": "pt-PT", "PSE": "ar", "LBN": "ar", "SDN": "ar", "LBY": "ar", "YEM": "ar", "JOR": "ar"}
ISO2 = {c.alpha_3: c.alpha_2 for c in pycountry.countries} if pycountry else {}


def cote_epu(session, iso, n):
    return "A/HRC/WG.6/%d/%s/%s" % (session, iso, n)


# ---------------------------------------------------------------------------
# Ratifications (Collection des traités)
# ---------------------------------------------------------------------------
# Liste choisie des traités (numéro dans la Collection des traités de l'ONU ; nom).
# Copiée dans le dossier de base (traites.csv) à la première utilisation : modifiable.
TRAITES = [
    ("IV-4", "Pacte international relatif aux droits civils et politiques"),
    ("IV-5", "Protocole facultatif se rapportant au PIDCP (plaintes individuelles)"),
    ("IV-12", "Deuxième Protocole facultatif se rapportant au PIDCP (abolition de la peine de mort)"),
    ("IV-3", "Pacte international relatif aux droits économiques, sociaux et culturels"),
    ("IV-3-a", "Protocole facultatif se rapportant au PIDESC"),
    ("IV-9", "Convention contre la torture"),
    ("IV-9-b", "Protocole facultatif se rapportant à la Convention contre la torture"),
    ("IV-8", "Convention sur l’élimination de toutes les formes de discrimination à l’égard des femmes"),
    ("IV-8-b", "Protocole facultatif à la Convention sur l’élimination de la discrimination à l’égard des femmes"),
    ("IV-11", "Convention relative aux droits de l’enfant"),
    ("IV-11-b", "Protocole facultatif à la CIDE (implication d’enfants dans les conflits armés)"),
    ("IV-11-c", "Protocole facultatif à la CIDE (vente d’enfants, prostitution et pornographie)"),
    ("IV-11-d", "Protocole facultatif à la CIDE (procédure de présentation de communications)"),
    ("IV-2", "Convention internationale sur l’élimination de toutes les formes de discrimination raciale"),
    ("IV-13", "Convention internationale sur la protection des droits de tous les travailleurs migrants"),
    ("IV-15", "Convention relative aux droits des personnes handicapées"),
    ("IV-15-a", "Protocole facultatif se rapportant à la Convention relative aux droits des personnes handicapées"),
    ("IV-16", "Convention internationale pour la protection de toutes les personnes contre les disparitions forcées"),
    ("IV-1", "Convention pour la prévention et la répression du crime de génocide"),
    ("V-2", "Convention relative au statut des réfugiés"),
    ("V-5", "Protocole relatif au statut des réfugiés"),
    ("V-3", "Convention relative au statut des apatrides (1954)"),
    ("V-4", "Convention sur la réduction des cas d’apatridie (1961)"),
    ("XVIII-10", "Statut de Rome de la Cour pénale internationale"),
    ("XVIII-12", "Convention des Nations Unies contre la criminalité transnationale organisée"),
    ("XVIII-12-a", "Protocole visant à prévenir, réprimer et punir la traite des personnes"),
]
# Chapitres parcourus pour l'option « tous les traités des chapitres » : (numéro romain, id de page, libellé)
CHAPITRES_UNTC = [("IV", 4, "Droits de l’homme"), ("V", 5, "Réfugiés et apatrides"),
                  ("XVIII", 18, "Matières pénales")]
CHAPITRE_URL = "https://treaties.un.org/Pages/Treaties.aspx?id={id}&subid=A&clang=_en"
ROMAINS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11,
           "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
           "XXI": 21, "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25, "XXVI": 26, "XXVII": 27, "XXVIII": 28, "XXIX": 29}
TB_TRAITES_PAYS = "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/Treaty.aspx?CountryID={cid}&Lang=FR"
TB_TRAITES_LISTE = "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/Treaty.aspx?Lang=en"
COUNTRY_IDS_CONNUS = {"IDN": "80"}  # vérifiés ; les autres sont cherchés automatiquement


def liste_traites(base):
    """Liste choisie, depuis traites.csv (créé à la première utilisation)."""
    chemin = os.path.join(base, "traites.csv")
    os.makedirs(base, exist_ok=True)
    if not os.path.exists(chemin):
        with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["numero_untc", "nom"])
            for no, nom in TRAITES:
                w.writerow([no, nom])
    out = []
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if (r.get("numero_untc") or "").strip():
                out.append((r["numero_untc"].strip(), (r.get("nom") or "").strip()))
    return out, chemin


def lignes_texte(html_text):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html_text)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d|td|table)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [" ".join(l.split()) for l in t.split("\n") if l.strip()]


SECTIONS_UNTC = re.compile(r"^(Declarations? and Reservations?|Reservations? and Declarations?|Declarations? recogni[sz]ing|"
                           r"Declarations? made under|Objections?(?!\s+(?:to|by|of|concerning|made)\b)|Notes?|Territorial Application|"
                           r"D[ée]clarations? et r[ée]serves?|R[ée]serves? et d[ée]clarations?|D[ée]clarations? reconnaissant|"
                           r"D[ée]clarations? faites en vertu|Application territoriale)\b", re.I)


def _noms_pays_norm():
    noms = set()
    if pycountry:
        for c in pycountry.countries:
            for a in ("name", "official_name", "common_name"):
                v = getattr(c, a, None)
                if v:
                    noms.add(norm(v))
    noms |= {norm(x) for x in ["Bolivia (Plurinational State of)", "Iran (Islamic Republic of)", "Republic of Korea",
                               "Venezuela (Bolivarian Republic of)", "Türkiye", "Russian Federation", "Viet Nam",
                               "Republic of Moldova", "United Kingdom of Great Britain and Northern Ireland",
                               "United States of America", "Syrian Arab Republic", "Lao People's Democratic Republic",
                               "Democratic People's Republic of Korea", "Holy See", "State of Palestine",
                               "Micronesia (Federated States of)", "Côte d'Ivoire", "Czechia", "Netherlands (Kingdom of the)",
                               "European Union"]}
    # noms français (page française de la Collection des traités)
    if pycountry:
        try:
            tr = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"])
            for c in pycountry.countries:
                for a in ("name", "official_name", "common_name"):
                    v = getattr(c, a, None)
                    if v:
                        noms.add(norm(tr.gettext(v)))
        except Exception:
            pass
    noms |= {norm(x) for x in ["Royaume-Uni de Grande-Bretagne et d'Irlande du Nord", "États-Unis d'Amérique",
                               "Fédération de Russie", "République de Corée", "République de Moldova",
                               "République arabe syrienne", "République démocratique populaire lao",
                               "République populaire démocratique de Corée", "Saint-Siège", "État de Palestine",
                               "Micronésie (États fédérés de)", "Bolivie (État plurinational de)",
                               "Venezuela (République bolivarienne du)", "Iran (République islamique d')",
                               "Pays-Bas (Royaume des)", "Tchéquie", "Union européenne", "Türkiye"]}
    return noms


MOTS_NON_PAYS = {"declaration", "declarations", "reservation", "reservations", "objection", "objections", "understanding",
                 "understandings", "interpretative", "note", "notes", "the", "with", "upon", "in", "on", "for", "and",
                 "article", "articles", "see", "unless", "communication", "communications", "declarations:", "reserve",
                 # français (page française de la Collection des traités)
                 "reserves", "le", "la", "les", "l", "en", "a", "au", "aux", "de", "du", "des", "d", "et", "pour", "sur",
                 "voir", "conformement", "lors", "sous", "avec", "par", "application", "sauf", "compte", "declaration:"}


def _ressemble_pays(l):
    """Ligne courte du type « Netherlands » ou « Bolivia (Plurinational State of) 12 » : en-tête d'un État."""
    l2 = re.sub(r"[\d\s,]+$", "", l).strip()
    mots = l2.split()
    if not mots or len(mots) > 6 or l2.endswith((".", ":", ";")) or not l2[0].isupper():
        return False
    if norm(mots[0]) in MOTS_NON_PAYS:
        return False
    return bool(re.fullmatch(r"[A-Za-zÀ-ÿ'’() ,.-]+", l2))


def _passages_cible(texte, cibles):
    """Dans une objection qui vise plusieurs États, ne garde que les passages
    (« [date] With regard to … ») qui mentionnent le pays recherché."""
    debuts = [m.start() for m in re.finditer(
        r"(?:\d{1,2}(?:er)? [A-Za-zéû]+\.? \d{4} )?(?:With regard to|[ÀA] l[’']égard (?:de|des|du|d[’']))", texte)]
    if not debuts:
        return texte
    bornes = [0] + debuts + [len(texte)]
    morceaux = [texte[a:b].strip() for a, b in zip(bornes, bornes[1:]) if texte[a:b].strip()]
    garde = [m for m in morceaux if any(c and c in norm(m) for c in cibles)]
    return " […] ".join(garde) if garde else texte


def texte_en_francais(t):
    """Vrai si le texte est manifestement en français (et non l'anglais recopié sur la page française)."""
    mots = re.findall(r"[a-zà-ÿ’']+", (t or "").lower())
    fr = sum(1 for m in mots if m in {"le", "la", "les", "des", "du", "et", "que", "qui", "est", "une", "dans",
                                      "gouvernement", "conformément", "à", "réserve", "déclare", "pas", "sur"})
    en = sum(1 for m in mots if m in {"the", "and", "of", "that", "which", "is", "to", "government", "with",
                                      "shall", "not", "declares", "reservation", "by"})
    return fr > en


def reserves_pays(html_text, noms):
    """Extrait, dans la page d'un traité, les passages consacrés au pays dans les sections
    « Declarations and Reservations », « Declarations recognizing the competence… », etc.,
    ainsi que les objections d'autres États qui le mentionnent."""
    lignes = lignes_texte(html_text)
    cibles = {norm(n) for n in noms if n}
    tous = _noms_pays_norm() | cibles
    section, bloc, out = "", None, []   # bloc = [pays (texte), est_cible, section, lignes]

    def fermer():
        if not bloc or not bloc[3]:
            return
        texte = " ".join(bloc[3])
        if bloc[1]:
            # la colonne « Note » du tableau des participants ne fait que répéter les dates
            if re.match(r"notes?\b", norm(bloc[2])) and re.fullmatch(r"[\da-z ]{0,60}", norm(texte)) \
                    and re.search(r"\b(19|20)\d\d\b", texte):
                return
            out.append((bloc[2], texte))
        elif re.match(r"objection", bloc[2], re.I) and any(c and c in norm(texte) for c in cibles):
            out.append(("%s – %s" % (bloc[2], bloc[0]), _passages_cible(texte, cibles)))

    for l in lignes:
        if re.fullmatch(r"(?i)notes?\s*:?", l.strip()):  # « Notes: » / « Notes : » : fin des sections utiles
            fermer()
            bloc, section = None, ""
            continue
        if SECTIONS_UNTC.match(l) and l[:1].isupper() and not l.rstrip().endswith(":") and len(l.split()) <= 14:
            fermer()
            bloc = None
            section = l
            continue
        nl = norm(re.sub(r"[\d\s,]+$", "", l.rstrip(":")))  # « Indonesia 3 » (appel de note), « Indonesia: »
        if section and len(l) < 80 and (nl in tous or _ressemble_pays(l)):
            fermer()
            bloc = [re.sub(r"[\d\s,:]+$", "", l), nl in cibles, section, []]
            continue
        if bloc is not None:
            bloc[3].append(l)
    fermer()
    return [(sec, txt[:4000]) for sec, txt in out]


def tableaux_procedures(lignes, country_id=""):
    """Nettoie les tableaux de la page Treaty.aspx du HCDH : un tableau par en-tête « Pays … »,
    sans colonnes répétées ou vides ni lignes de décoration."""
    sections, cur = [], None
    for row in lignes:
        row = list(row)
        if country_id and row and row[-1].strip() == str(country_id):
            row = row[:-1]
        if all(c.strip() in ("", "|") for c in row):
            continue
        if norm(row[0]) in ("pays", "country"):
            cur = [row, []]
            sections.append(cur)
            continue
        if cur is None:
            cur = [[""] * len(row), []]
            sections.append(cur)
        cur[1].append(row)
    propres = []
    for entete, rows in sections:
        n = max([len(entete)] + [len(r) for r in rows])
        entete = entete + [""] * (n - len(entete))
        rows = [r + [""] * (n - len(r)) for r in rows]
        garder = []
        for i in range(n):
            if i in (0, 1, 3):  # pays (×2) et intitulé répété : superflus dans un dossier par pays
                if i == 3 or norm(entete[i]) in ("pays", "country"):
                    continue
            if i == 4 and norm(entete[i]) == "treaty name":
                continue
            if not entete[i].strip():  # colonnes sans titre : données masquées sur le site
                continue
            if norm(entete[i]) in ("date de ratification", "ratification date") and \
                    any(re.search(r"adh[ée]sion|accession", h, re.I) for h in entete):
                continue  # doublon masqué de la colonne « ratification / adhésion »
            if not any(r[i].strip() for r in rows) and i > 2:
                continue
            garder.append(i)
        propres.append(([entete[i] for i in garder], [[r[i] for i in garder] for r in rows]))
    return propres


TRAITE_URL = "https://treaties.un.org/Pages/ViewDetails.aspx?src=TREATY&mtdsg_no={no}&chapter={ch}&clang={lang}"
CHAPITRES = {"IV": "4", "V": "5"}


class _Tables(HTMLParser):
    """Extrait les lignes de tableaux : texte des cellules et liens de chaque ligne."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.links = [], []
        self._row, self._cell, self._in, self._rowlinks = None, None, False, []
        self.all_links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self._row, self._rowlinks = [], []
        elif tag in ("td", "th") and self._row is not None:
            self._cell, self._in = [], True
        elif tag == "a" and a.get("href"):
            self.all_links.append(a["href"])
            if self._row is not None:
                self._rowlinks.append(a["href"])

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in:
            self._row.append(" ".join("".join(self._cell).split()))
            self._in = False
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
                self.links.append(self._rowlinks)
            self._row = None

    def handle_data(self, data):
        if self._in:
            self._cell.append(data)


def formulaire_page_suivante(html_text, n):
    """Pages ASP.NET/Telerik dont l'adresse ne change pas : prépare les données à renvoyer (POST)
    pour afficher la page n. Renvoie (action, données) ou None s'il n'y a pas de page n."""
    if not html_text:
        return None
    donnees = {}
    for tag in re.findall(r"<input\b[^>]*>", html_text, re.I):
        nom = re.search(r'\bname="([^"]+)"', tag)
        typ = (re.search(r'\btype="([^"]+)"', tag, re.I) or [None, "text"])[1].lower()
        if not nom or typ not in ("hidden", "text"):
            continue
        val = re.search(r'\bvalue="([^"]*)"', tag)
        donnees[html.unescape(nom.group(1))] = html.unescape(val.group(1)) if val else ""
    for sel in re.findall(r"<select\b.*?</select>", html_text, re.I | re.S):
        nom = re.search(r'\bname="([^"]+)"', sel)
        opt = re.search(r'<option[^>]*selected[^>]*value="([^"]*)"|<option[^>]*value="([^"]*)"[^>]*selected', sel, re.I)
        if nom and opt:
            donnees[html.unescape(nom.group(1))] = html.unescape(opt.group(1) or opt.group(2) or "")
    cible = None
    # 1) lien de pagination « n » : href="javascript:__doPostBack('…','…')"
    for href, texte in re.findall(r"<a\b[^>]*href=\"([^\"]*__doPostBack[^\"]*)\"[^>]*>(.*?)</a>", html_text, re.I | re.S):
        if re.sub(r"<[^>]+>", "", texte).strip() == str(n):
            m = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", html.unescape(href))
            if m:
                cible = ("evt", m.group(1), m.group(2))
                break
    # 2) bouton « page suivante » de Telerik
    if not cible:
        for tag in re.findall(r"<input\b[^>]*>", html_text, re.I):
            if re.search(r'(rgPageNext|title="Next Page"|title="Page suivante")', tag, re.I) and \
                    not re.search(r"disabled|onclick=\"return false", tag, re.I):
                nom = re.search(r'\bname="([^"]+)"', tag)
                if nom:
                    val = re.search(r'\bvalue="([^"]*)"', tag)
                    cible = ("btn", html.unescape(nom.group(1)), html.unescape(val.group(1)) if val else " ")
                    break
    if not cible:
        return None
    if cible[0] == "evt":
        donnees["__EVENTTARGET"], donnees["__EVENTARGUMENT"] = cible[1], cible[2]
    else:
        donnees["__EVENTTARGET"], donnees["__EVENTARGUMENT"] = "", ""
        donnees[cible[1]] = cible[2]
    m = re.search(r"<form\b[^>]*action=\"([^\"]*)\"", html_text, re.I)
    action = html.unescape(m.group(1)) if m else ""
    return action, donnees


SIGLES_TRAITES = r"\b(CCPR|CESCR|CAT|SPT|CEDAW|CERD|CRC|CRC-OP-AC|CRC-OP-SC|CMW|CRPD|CED)\b"


def filtrer_etat_rapports(rows):
    """Garde les lignes du tableau d'état des rapports (sigle de comité + date ou année),
    sans doublons ni lignes de menu."""
    garde, vus = [], set()
    for row in rows:
        txt = " | ".join(row)
        if len(row) < 3 or len(txt) > 1500:
            continue
        if not re.search(SIGLES_TRAITES, txt):
            continue
        if not re.search(r"\b(19|20)\d{2}\b", txt):
            continue
        cle = tuple(row)
        if cle in vus:
            continue
        vus.add(cle)
        garde.append(row)
    return garde


def ligne_pays(html_text, noms):
    """Renvoie « Signature : … ; Ratification, Adhésion(a) : … » pour le pays, ou None."""
    p = _Tables()
    p.feed(html_text)
    cibles = [norm(n) for n in noms if n]
    entetes = None
    for r in p.rows:
        if r and norm(r[0]).startswith("participant"):
            entetes = r
            continue
        if r and any(norm(r[0]) == c or norm(r[0]).startswith(c + " ") for c in cibles):
            vals = r[1:]
            if entetes and len(entetes) == len(r):
                return " ; ".join("%s : %s" % (h, v or "—") for h, v in zip(entetes[1:], vals))
            return " | ".join(v or "—" for v in vals)
    return None


# ---------------------------------------------------------------------------
# ReliefWeb et veille
# ---------------------------------------------------------------------------
RW_URL = "https://api.reliefweb.int/v2/reports?appname={app}"
PRESETS = {
    "Droits humains (PI, OQT)": {"code": "droits", "theme": "Protection and Human Rights"},
    "Santé (9ter)": {"code": "sante", "theme": "Health"},
    "Personnalisé": {"code": "", "theme": ""},
}
GNEWS_URL = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
# ---------------------------------------------------------------------------
# Catégories et catalogue des sources
# ---------------------------------------------------------------------------
# Chaque document reçoit une catégorie, qui détermine aussi son dossier de rangement.
CATEGORIES = [
    ("Organes de traités", "01_ONU_organes_de_traites",
     "Comités de l’ONU : observations finales, listes de points, rapports de l’État, courriers de suivi, état des rapports"),
    ("Ratifications", "02_Ratifications", "État des ratifications (Collection des traités de l’ONU)"),
    ("EPU", "03_ONU_EPU", "Examen périodique universel : rapport national, compilation ONU, parties prenantes"),
    ("Procédures spéciales", "04_ONU_procedures_speciales", "Rapporteurs spéciaux et groupes de travail : communications (AL, UA, OL), rapports de visite"),
    ("ONU – HCDH et Conseil des droits de l’homme", "05_ONU_HCDH", "Haut-Commissariat aux droits de l’homme : communiqués, rapports ; Conseil des droits de l’homme"),
    ("ONU – agences", "06_ONU_agences", "HCR, OMS, UNICEF, OCHA, PNUD… (y compris les données de santé pour le 9ter)"),
    ("ONG internationales", "07_ONG_internationales", "Human Rights Watch, Amnesty International, Crisis Group, FIDH, OMCT…"),
    ("Sources nationales", "08_Sources_nationales", "ONG et institutions nationales du pays (ex. KontraS, SETARA, Komnas HAM)"),
    ("Gouvernements et organisations régionales", "09_Gouvernements_et_org_regionales",
     "Rapports d’États et d’organisations régionales (ex. Département d’État, EUAA, Union européenne, Conseil de l’Europe)"),
    ("Presse", "10_Presse", "Articles de presse"),
    ("Jurisprudence", "11_Jurisprudence", "Décisions de justice (CCE, Cour eur. D.H., CJUE, juridictions nationales)"),
    ("À classer", "12_A_classer", "Source absente du catalogue : à classer à la main (puis ajouter la source au catalogue)"),
]
DOSSIERS = {c: d for c, d, _ in CATEGORIES}
CATEGORIES_IMPORT = ["Automatique"] + [c for c, _, _ in CATEGORIES if c not in ("Ratifications",)]

# Catalogue par défaut. Il est copié dans le dossier de base (catalogue_sources.csv) à la
# première utilisation : c'est ce fichier-là qu'il faut modifier pour ajouter une source,
# corriger un nom ou changer une catégorie.
# nom affiché ; nom exact sur ReliefWeb ; catégorie ; domaines web (séparés par des espaces) ; préréglages
CATALOGUE_DEFAUT = [
    ("HCDH", "Office of the United Nations High Commissioner for Human Rights", "ONU – HCDH et Conseil des droits de l’homme", "ohchr.org", "droits"),
    ("Conseil des droits de l’homme", "UN Human Rights Council", "ONU – HCDH et Conseil des droits de l’homme", "", ""),
    ("HCR", "UN High Commissioner for Refugees", "ONU – agences", "unhcr.org refworld.org", "droits"),
    ("OMS", "World Health Organization", "ONU – agences", "who.int", "sante"),
    ("UNICEF", "UN Children's Fund", "ONU – agences", "unicef.org", "sante"),
    ("OCHA", "UN Office for the Coordination of Humanitarian Affairs", "ONU – agences", "unocha.org", ""),
    ("PNUD", "UN Development Programme", "ONU – agences", "undp.org", ""),
    ("ONUSIDA", "Joint United Nations Programme on HIV/AIDS", "ONU – agences", "unaids.org", "sante"),
    ("Human Rights Watch", "Human Rights Watch", "ONG internationales", "hrw.org", "droits"),
    ("Amnesty International", "Amnesty International", "ONG internationales", "amnesty.org amnesty.be", "droits"),
    ("International Crisis Group", "International Crisis Group", "ONG internationales", "crisisgroup.org", "droits"),
    ("FIDH", "International Federation for Human Rights", "ONG internationales", "fidh.org", "droits"),
    ("OMCT", "World Organisation Against Torture", "ONG internationales", "omct.org", "droits"),
    ("Minority Rights Group", "Minority Rights Group", "ONG internationales", "minorityrights.org", "droits"),
    ("Christian Solidarity Worldwide", "Christian Solidarity Worldwide", "ONG internationales", "csw.org.uk", "droits"),
    ("Médecins Sans Frontières", "Médecins Sans Frontières", "ONG internationales", "msf.org", "sante"),
    ("Freedom House", "Freedom House", "ONG internationales", "freedomhouse.org", ""),
    ("Département d’État des États-Unis", "US Department of State", "Gouvernements et organisations régionales", "state.gov", ""),
    ("EUAA (Agence de l’UE pour l’asile)", "European Union Agency for Asylum", "Gouvernements et organisations régionales", "euaa.europa.eu", "droits"),
    ("Union européenne", "European Union", "Gouvernements et organisations régionales", "europa.eu", ""),
    ("Conseil de l’Europe", "Council of Europe", "Gouvernements et organisations régionales", "coe.int", ""),
    ("CGRA (Belgique) – COI Focus", "", "Gouvernements et organisations régionales", "cgra.be cgvs.be", ""),
    ("KontraS (Indonésie)", "", "Sources nationales", "kontras.org", ""),
    ("SETARA Institute (Indonésie)", "", "Sources nationales", "setara-institute.org", ""),
    ("Komnas HAM (Indonésie)", "", "Sources nationales", "komnasham.go.id", ""),
    ("Komnas Perempuan (Indonésie)", "", "Sources nationales", "komnasperempuan.go.id", ""),
    ("YLBHI (Indonésie)", "", "Sources nationales", "ylbhi.or.id", ""),
    ("Human Rights Monitor (Papouasie)", "", "Sources nationales", "humanrightsmonitor.org", ""),
    ("Hukumonline", "", "Presse", "hukumonline.com", ""),
    ("ANTARA", "", "Presse", "antaranews.com", ""),
    ("CNN Indonesia", "", "Presse", "cnnindonesia.com", ""),
    ("Tempo", "", "Presse", "tempo.co", ""),
    ("Kompas", "", "Presse", "kompas.com kompas.id", ""),
    ("The Jakarta Post", "", "Presse", "thejakartapost.com", ""),
    ("Reuters", "", "Presse", "reuters.com", ""),
    ("AFP", "Agence France-Presse", "Presse", "afp.com", ""),
    ("The New Humanitarian", "The New Humanitarian", "Presse", "thenewhumanitarian.org", ""),
    ("Conseil du contentieux des étrangers", "", "Jurisprudence", "rvv-cce.be", ""),
    ("Cour européenne des droits de l’homme", "", "Jurisprudence", "hudoc.echr.coe.int echr.coe.int", ""),
    ("Cour de justice de l’Union européenne", "", "Jurisprudence", "curia.europa.eu", ""),
]
CHAMPS_CATALOGUE = ["nom", "nom_reliefweb", "categorie", "domaines", "prereglages"]


class Catalogue:
    def __init__(self, base):
        self.chemin = os.path.join(base, "catalogue_sources.csv")
        os.makedirs(base, exist_ok=True)
        if not os.path.exists(self.chemin):
            with open(self.chemin, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(CHAMPS_CATALOGUE)
                for row in CATALOGUE_DEFAUT:
                    w.writerow(row)
        self.lignes = []
        with open(self.chemin, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                if (r.get("nom") or "").strip():
                    self.lignes.append({k: (r.get(k) or "").strip() for k in CHAMPS_CATALOGUE})

    def classer(self, auteur="", url=""):
        """Renvoie (categorie, nom) d'après le nom de la source ou le domaine du lien."""
        a = norm(auteur)
        if a:
            for l in self.lignes:
                for n in (l["nom_reliefweb"], l["nom"]):
                    nn = norm(n)
                    if nn and (a == nn or nn in a or (len(a) > 6 and a in nn)):
                        return l["categorie"] or "À classer", l["nom"]
        host = urllib.parse.urlparse(url or "").netloc.lower().replace("www.", "")
        if host:
            for l in self.lignes:
                for d in l["domaines"].split():
                    d = d.lower()
                    if host == d or host.endswith("." + d):
                        return l["categorie"] or "À classer", l["nom"]
        return "À classer", ""

    def reliefweb(self, prereglage=""):
        return [l for l in self.lignes if l["nom_reliefweb"] and (not prereglage or prereglage in l["prereglages"].split())]


RW_RSS_PAYS = "https://reliefweb.int/updates/rss.xml?search=country.exact:%22{nom}%22"


def flux_reliefweb_normalises(flux, nom_en=""):
    """Transforme une adresse de page ReliefWeb en adresse de flux RSS ; sans flux, flux du pays."""
    out = []
    for u in flux or []:
        u = u.strip()
        if not u:
            continue
        if "reliefweb.int" in u and "rss.xml" not in u:
            if "/updates?" in u:
                u = u.replace("/updates?", "/updates/rss.xml?")
            elif re.search(r"/country/[a-z]{3}\b", u) and nom_en:
                u = RW_RSS_PAYS.format(nom=urllib.parse.quote(nom_en))
        out.append(u)
    if not out and nom_en:
        out.append(RW_RSS_PAYS.format(nom=urllib.parse.quote(nom_en)))
    return list(dict.fromkeys(out))


def lire_flux(xml_bytes):
    """RSS 2.0 ou Atom -> [(titre, lien, date datetime|None, source)]."""
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in root.iter("item"):
        t = (it.findtext("title") or "").strip()
        l = (it.findtext("link") or "").strip()
        d = it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")
        src = it.findtext("source") or ""
        out.append((t, l, _date_flux(d), src.strip()))
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
        t = (e.findtext("a:title", namespaces=ns) or "").strip()
        le = e.find("a:link", ns)
        l = le.get("href") if le is not None else ""
        d = e.findtext("a:updated", namespaces=ns) or e.findtext("a:published", namespaces=ns)
        out.append((t, l, _date_flux(d), ""))
    return out


def lire_flux_detail(xml_bytes):
    """RSS 2.0 -> liste de dict : titre, lien, date, auteur, pieces (URLs de PDF joints), categories."""
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    dc = "{http://purl.org/dc/elements/1.1/}"
    for it in root.iter("item"):
        pieces = []
        for enc in it.findall("enclosure"):
            u, t = enc.get("url", ""), (enc.get("type") or "").lower()
            if u and ("pdf" in t or u.lower().split("?")[0].endswith(".pdf")):
                pieces.append(u)
        desc = it.findtext("description") or ""
        for u in re.findall(r'href=["\']([^"\']+\.pdf)["\']', html.unescape(desc), re.I):
            if u not in pieces:
                pieces.append(u)
        auteurs = [(a.text or "").strip() for a in it.findall("author") + it.findall(dc + "creator") if (a.text or "").strip()]
        source = (it.findtext("source") or "").strip()
        if not auteurs and source and not re.search(r"reliefweb|updates", source, re.I):  # <source> = nom du flux
            auteurs = [source]
        auteur = ", ".join(dict.fromkeys(auteurs))
        out.append({"titre": (it.findtext("title") or "").strip(), "lien": (it.findtext("link") or "").strip(),
                    "date": _date_flux(it.findtext("pubDate") or it.findtext(dc + "date")),
                    "auteur": auteur, "pieces": pieces,
                    "categories": [(c.text or "").strip() for c in it.findall("category") if c.text]})
    return out


def id_reliefweb(url):
    """Identifiant commun à l'API et aux flux : le chemin de la page ReliefWeb."""
    p = urllib.parse.urlparse(url or "")
    return "RW-" + slug(p.path.strip("/"), 150) if p.path.strip("/") else ""


def _date_flux(s):
    if not s:
        return None
    s = s.strip()
    try:
        return email.utils.parsedate_to_datetime(s)
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Fiches et état
# ---------------------------------------------------------------------------
CHAMPS = ["id", "categorie", "auteur", "titre", "cote", "date", "url", "consulte_le",
          "fichier", "langue", "annexe", "remarques", "citation", "articles"]


class Depot:
    """Dossier d'un pays : fichiers, sources.csv, état des collectes et journal."""

    def __init__(self, base, iso, nom_fr, nom_dossier=None):
        self.racine = os.path.join(base, nom_dossier or "%s (%s)" % (nom_fr, iso))
        os.makedirs(self.racine, exist_ok=True)
        self.csv_path = os.path.join(self.racine, "sources.csv")
        self.etat_path = os.path.join(self.racine, ".etat.json")
        self.fiches = {}
        if os.path.exists(self.csv_path):
            with open(self.csv_path, encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f, delimiter=";"):
                    self.fiches[row["id"]] = row
        self.etat = {}
        if os.path.exists(self.etat_path):
            try:
                with open(self.etat_path, encoding="utf-8") as f:
                    self.etat = json.load(f)
            except Exception:
                self.etat = {}
        self.etat.setdefault("derniere_collecte", {})
        self.nouveautes = []
        self.liens = []  # mode « liens seulement »

    def connu(self, id_):
        return id_ in self.fiches

    def a_fichier(self, id_):
        f = self.fiches.get(id_, {}).get("fichier")
        return bool(f) and os.path.exists(os.path.join(self.racine, f))

    def ajouter(self, fiche):
        fiche = {k: fiche.get(k, "") for k in CHAMPS}
        ancien = self.fiches.get(fiche["id"])
        if ancien:  # on ne touche jamais aux colonnes remplies à la main
            for k in ("annexe", "remarques"):
                if ancien.get(k):
                    fiche[k] = ancien[k]
            if not fiche["fichier"]:
                fiche["fichier"] = ancien.get("fichier", "")
        else:
            self.nouveautes.append(fiche)
        self.fiches[fiche["id"]] = fiche

    def chemin(self, categorie, *parties):
        p = os.path.join(self.racine, DOSSIERS.get(categorie, DOSSIERS["À classer"]), *parties)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    def marquer(self, module):
        self.etat["derniere_collecte"][module] = maintenant_iso()

    def derniere(self, module):
        s = self.etat["derniere_collecte"].get(module)
        try:
            return dt.datetime.fromisoformat(s) if s else None
        except Exception:
            return None

    def enregistrer(self):
        with open(self.csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CHAMPS, delimiter=";")
            w.writeheader()
            for fi in sorted(self.fiches.values(), key=lambda r: (r["categorie"], r["id"])):
                w.writerow(fi)
        with open(self.etat_path, "w", encoding="utf-8") as f:
            json.dump(self.etat, f, ensure_ascii=False, indent=1)
        now = dt.datetime.now()
        stamp = now.strftime("%Y-%m-%d_%H%M%S")
        journal = os.path.join(self.racine, "journal_%s.txt" % stamp)
        with open(journal, "w", encoding="utf-8") as f:
            f.write("Collecte du %s à %s\n" % (date_fr(now.date()), now.strftime("%H:%M")))
            f.write("%d nouveau(x) document(s)\n\n" % len(self.nouveautes))
            for n in self.nouveautes:
                f.write("- [%s] %s, %s%s (%s)\n  %s\n" % (
                    n["categorie"], n["auteur"], n["titre"],
                    (", " + n["cote"]) if n["cote"] else "", n["date"] or "date ?",
                    n["fichier"] or n["url"]))
        if self.liens:
            page = os.path.join(self.racine, "liens_a_telecharger_%s.html" % stamp)
            with open(page, "w", encoding="utf-8") as f:
                f.write("<!doctype html><meta charset='utf-8'><title>Liens à télécharger</title>"
                        "<style>body{font-family:Arial;max-width:900px;margin:2em auto}li{margin:.4em 0}</style>"
                        "<h1>Liens à télécharger – %s</h1><p>Cliquez sur chaque lien, puis enregistrez le "
                        "fichier ; vous pourrez ensuite l’importer dans l’onglet « Importer » pour créer la fiche.</p><ol>"
                        % date_fr(now.date()))
                for titre, url in self.liens:
                    f.write("<li><a href='%s'>%s</a><br><small>%s</small></li>" % (
                        html.escape(url), html.escape(titre), html.escape(url)))
                f.write("</ol>")
            self.page_liens = page
        return journal


# ---------------------------------------------------------------------------
# Collecteur
# ---------------------------------------------------------------------------
class Arret(Exception):
    pass


class Collecteur:
    def __init__(self, log=print, progres=None, stop_event=None, session=None, liens_seulement=False, catalogue=None):
        self.cat = catalogue
        self.log = log
        self.progres = progres or (lambda *a: None)
        self.stop = stop_event or threading.Event()
        self.s = session or requests.Session()
        try:
            self.s.headers["User-Agent"] = USER_AGENT
        except Exception:
            pass
        self.liens_seulement = liens_seulement
        self.aujourdhui = date_fr(dt.date.today())

    def classer(self, auteur="", url="", defaut="À classer"):
        if self.cat is None:
            return defaut, ""
        c, nom = self.cat.classer(auteur, url)
        if c == "À classer" and re.search(r"\bUnited Nations\b|\bUN (Office|Women|Development|Children)|\bUN[A-Z]{2,6}\b|"
                                          r"^World (Health|Food|Meteorological)|International Organization for Migration",
                                          auteur or ""):
            c = "ONU – agences"  # agence de l’ONU absente du catalogue
        return (defaut if c == "À classer" and defaut != "À classer" else c), nom

    def _verif(self):
        if self.stop.is_set():
            raise Arret()

    def _get(self, url, **kw):
        self._verif()
        time.sleep(PAUSE)
        return self.s.get(url, timeout=60, **kw)

    def _fichier(self, url, profondeur=0, headers=None):
        """Télécharge ; renvoie (ext, contenu) si c'est un PDF/DOC(X), sinon None."""
        try:
            r = self._get(url, headers=headers) if headers else self._get(url)
        except Arret:
            raise
        except Exception as e:
            self.log("  ! réseau : %s" % e)
            return None
        if r.status_code == 200:
            ext = type_fichier(r.content[:8])
            if ext:
                return ext, r.content
            # page HTML intermédiaire : on suit une redirection ou un lien direct vers le fichier
            entetes = getattr(r, "headers", None) or {}
            if profondeur < 2 and "html" in entetes.get("Content-Type", "").lower():
                t = r.text or ""
                m = (re.search(r'http-equiv=["\']?refresh["\']?[^>]*url=([^"\'>]+)', t, re.I)
                     or re.search(r'(?:window\.)?location(?:\.href)?\s*=\s*["\']([^"\']+)', t, re.I)
                     or re.search(r'href=["\']([^"\']+\.(?:pdf|docx?)(?:\?[^"\']*)?)["\']', t, re.I))
                if m:
                    suivant = urllib.parse.urljoin(getattr(r, "url", url) or url, html.unescape(m.group(1).strip()))
                    if suivant != url:
                        return self._fichier(suivant, profondeur + 1)
        self._echecs = getattr(self, "_echecs", 0) + 1
        if self._echecs <= 3:  # diagnostic, limité aux premiers échecs
            self.log("  ? pas de fichier : %s\n    -> code %s, type « %s », adresse finale %s, début : %r"
                     % (url, r.status_code, (getattr(r, "headers", None) or {}).get("Content-Type", "?"),
                        getattr(r, "url", url), (getattr(r, "content", b"") or b"")[:60]))
        return None

    # -- documents ONU par cote ---------------------------------------------
    def _doc_onu(self, sym, langues):
        """Cherche une cote : d'abord l'existence en anglais (toujours publiée), puis le
        français ; ODS puis base des organes de traités. Renvoie (url, lang, ext, contenu)."""
        for gabarit in (ODS_URL, TB_URL):
            url_en = gabarit.format(sym=urllib.parse.quote(sym, safe=""), lang="en")
            en = self._fichier(url_en)
            if not en:
                continue
            if "fr" in langues:
                url_fr = gabarit.format(sym=urllib.parse.quote(sym, safe=""), lang="fr")
                fr = self._fichier(url_fr)
                if fr:
                    return (url_fr, "fr") + fr
            return (url_en, "en") + en
        return None

    def _enregistrer_onu(self, depot, categorie, sous_dossier, id_, sym, auteur, titre, res):
        url, lang, ext, contenu = res
        if self.liens_seulement:
            depot.liens.append(("%s – %s" % (sym, titre), url))
            fichier = ""
            date = ""
        else:
            nom = "%s_%s.%s" % (slug(sym.replace("/", "_")), lang, ext)
            chemin = depot.chemin(categorie, sous_dossier, nom)
            with open(chemin, "wb") as f:
                f.write(contenu)
            fichier = os.path.relpath(chemin, depot.racine)
            date = date_depuis_pdf(contenu) if ext == "pdf" else ""
        depot.ajouter({"id": id_, "categorie": categorie, "auteur": auteur, "titre": titre,
                       "cote": sym, "date": date, "url": url, "consulte_le": self.aujourdhui,
                       "fichier": fichier, "langue": lang})
        self.log("  + %s (%s, %s)%s" % (sym, lang, ext, "" if lang == "fr" else "  [pas de version française]"))

    def organes(self, depot, iso, de_pays, comites, types, langues=("fr", "en"), maj=False):
        numeros = [str(n) for n in range(1, N_MAX + 1)] + ["%d-%d" % (n, n + 1) for n in range(1, N_MAX)]
        total, k = len(comites) * len(types), 0
        for c in comites:
            for t in types:
                k += 1
                self.progres(k, total)
                cle = "tb_max_%s_%s" % (c, t)
                deja = depot.etat.get(cle, 0)
                a_sonder = [n for n in numeros if int(n.split("-")[-1]) >= deja] if (maj and deja) else numeros
                self.log("%s – %s : %d cote(s) à vérifier" % (c, TYPES_DOC[t], len(a_sonder)))
                for num in a_sonder:
                    sym = cote(c, iso, t, num)
                    id_ = "ONU-" + sym
                    if depot.a_fichier(id_) or (self.liens_seulement and depot.connu(id_)):
                        continue
                    res = self._doc_onu(sym, langues)
                    if not res:
                        continue
                    self._enregistrer_onu(depot, "Organes de traités", c, id_, sym,
                                          "ONU, " + COMITES[c][1], titre_tb(t, num, de_pays), res)
                    depot.etat[cle] = max(depot.etat.get(cle, 0), int(num.split("-")[-1]))
        depot.marquer("organes")

    def epu(self, depot, iso, de_pays, langues=("fr", "en"), maj=False, resultats=True):
        """Documents de l'EPU. D'abord la page du pays sur le site du HCDH (qui donne toutes les cotes :
        documents de base, rapport du Groupe de travail, additif, décision, liste des recommandations) ;
        à défaut, recherche des documents de base session par session."""
        page = self._page_epu(iso)
        if page is None:
            self.log("  Page EPU du HCDH inaccessible : recherche des documents de base session par session.")
            self._epu_sondage(depot, iso, de_pays, langues, maj)
            depot.marquer("epu")
            return
        wg = sorted({int(m) for m in re.findall(r"A/HRC/WG\.6/(\d+)/%s/[123]\b" % iso, page)})
        self.log("EPU : %d examen(s) trouvé(s) sur la page du HCDH (sessions %s)"
                 % (len(wg), ", ".join(map(str, wg)) or "—"))
        for i, s_ in enumerate(wg, 1):
            self.progres(i, len(wg) * 2)
            for n in ("1", "2", "3"):
                self._epu_doc(depot, cote_epu(s_, iso, n), "session_%02d" % s_,
                              EPU_DOCS[n] % (s_, de_pays if n == "1" else sans_de(de_pays)), langues)
            depot.etat["epu_derniere_session"] = max(depot.etat.get("epu_derniere_session", 0), s_)
        if resultats:
            self._epu_resultats(depot, iso, de_pays, page, wg, langues)
        depot.marquer("epu")

    def _page_epu(self, iso):
        iso2 = ISO2.get(iso, "")
        if not iso2:
            return None
        url = UPR_PAGE.format(iso2=iso2.lower())
        try:
            r = self._get(url)
        except Arret:
            raise
        except Exception as e:
            self.log("  ! %s : %s" % (url, e))
            return None
        if r.status_code != 200 or "A/HRC/" not in (r.text or ""):
            self.log("  ! %s : réponse %s" % (url, r.status_code))
            return None
        self._url_page_epu = url
        return html.unescape(urllib.parse.unquote(r.text))

    def _epu_doc(self, depot, sym, sous_dossier, titre, langues, verifier=None,
                 auteur="ONU, Conseil des droits de l’homme, Groupe de travail sur l’Examen périodique universel"):
        id_ = "ONU-" + sym
        if depot.a_fichier(id_) or (self.liens_seulement and depot.connu(id_)) or id_ in depot.etat.get("epu_ecartes", []):
            return
        res = self._doc_onu(sym, langues)
        if not res:
            self.log("  ? %s introuvable" % sym)
            return
        if verifier and res[2] == "pdf" and not verifier(texte_pdf(res[3], pages=2)):
            depot.etat.setdefault("epu_ecartes", []).append(id_)  # autre document (ex. rapport de session du Conseil)
            return
        self._enregistrer_onu(depot, "EPU", sous_dossier, id_, sym, auteur, titre, res)

    def _epu_resultats(self, depot, iso, de_pays, page, wg, langues):
        """Rapport du Groupe de travail, additif (position de l'État sur chaque recommandation),
        décision du Conseil et liste thématique des recommandations."""
        pays = sans_de(de_pays)
        cotes = sorted(set(re.findall(r"A/HRC/(?:DEC/)?\d+/\d+(?:/Add\.\d+)?", page)),
                       key=lambda c: [int(x) if x.isdigit() else 0 for x in re.split(r"[/.]", c)])
        # rattachement à l'examen : la n-ième session du Conseil citée correspond au n-ième examen
        sessions_cdh = sorted({int(re.match(r"A/HRC/(?:DEC/)?(\d+)/", c).group(1)) for c in cotes})
        examen = {sc: (wg[i] if i < len(wg) else None) for i, sc in enumerate(sessions_cdh)}
        nom_fr, noms_en = noms_pays(iso)
        cibles = [norm(x) for x in [nom_fr] + list(noms_en) if x]

        def est_rapport_gt(t):
            """Page de titre « Rapport du Groupe de travail sur l'EPU – [pays] » (et non rapport de session du Conseil)."""
            t = norm(t)[:4000]
            if re.search(r"(on its \w+ session|travaux de sa \w+ session)", t):
                return False
            m = re.search(r"(report of the working group on the universal periodic review|"
                          r"rapport du groupe de travail sur l ?examen periodique universel)", t)
            return bool(m) and any(c_ in t[m.end():m.end() + 300] for c_ in cibles)
        n = 0
        for c in cotes:
            sc = int(re.match(r"A/HRC/(?:DEC/)?(\d+)/", c).group(1))
            dossier = "session_%02d" % examen[sc] if examen.get(sc) else "resultats"
            if "/DEC/" in c:
                titre = "décision %s du Conseil des droits de l’homme : document final de l’Examen périodique universel – %s" \
                        % (c.split("/", 2)[2], pays)
                self._epu_doc(depot, c, dossier, titre, langues, auteur="ONU, Conseil des droits de l’homme")
            elif "/Add." in c:
                titre = ("rapport du Groupe de travail sur l’Examen périodique universel – %s, additif : observations sur "
                         "les conclusions et/ou recommandations, engagements exprimés et réponses de l’État examiné" % pays)
                self._epu_doc(depot, c, dossier, titre, langues)
            else:
                if c.endswith("/2"):
                    continue  # rapport de session du Conseil (très volumineux)
                titre = "rapport du Groupe de travail sur l’Examen périodique universel – %s" % pays
                self._epu_doc(depot, c, dossier, titre, langues, verifier=est_rapport_gt)
            n += 1
        # listes (« matrices ») des recommandations, publiées en .doc(x) ou .xlsx sur le site du HCDH
        for href in sorted(set(re.findall(r'href="([^"]+\.(?:docx?|xlsx?))"', page, re.I))):
            if not re.search(r"(recommend|matric|matrix|upr)", href, re.I):
                continue
            url = urllib.parse.urljoin(getattr(self, "_url_page_epu", "https://www.ohchr.org/"), href)
            id_ = "UPR-MATRICE-" + slug(os.path.basename(url), 80)
            if depot.a_fichier(id_) or (self.liens_seulement and depot.connu(id_)):
                continue
            m = re.search(r"session(\d+)", url, re.I)
            s_ = int(m.group(1)) if m else None
            ext = url.rsplit(".", 1)[-1].lower()
            titre = "liste thématique des recommandations adressées à %s%s" % (pays, (" (%de session)" % s_) if s_ else "")
            if self.liens_seulement:
                depot.liens.append((titre, url))
                depot.ajouter({"id": id_, "categorie": "EPU", "auteur": "ONU, HCDH", "titre": titre, "url": url,
                               "consulte_le": self.aujourdhui})
                continue
            res = self._fichier(url)
            if not res:
                self.log("  ? liste des recommandations non téléchargée : %s" % url)
                continue
            chemin = depot.chemin("EPU", "session_%02d" % s_ if s_ else "resultats", os.path.basename(urllib.parse.unquote(url)))
            with open(chemin, "wb") as f:
                f.write(res[1])
            depot.ajouter({"id": id_, "categorie": "EPU", "auteur": "ONU, HCDH", "titre": titre, "url": url,
                           "consulte_le": self.aujourdhui, "fichier": os.path.relpath(chemin, depot.racine),
                           "remarques": "format %s" % ext})
            self.log("  + liste des recommandations (%s)" % os.path.basename(chemin))

    def _epu_sondage(self, depot, iso, de_pays, langues=("fr", "en"), maj=False):
        debut = depot.etat.get("epu_derniere_session", 0) + 1 if maj else 1
        sessions = list(range(max(1, debut), EPU_MAX_SESSION + 1))
        self.log("EPU : sessions %d à %d" % (sessions[0] if sessions else 0, EPU_MAX_SESSION))
        self._echecs = 99  # sessions sans examen du pays : échecs attendus, pas de diagnostic
        for i, s in enumerate(sessions, 1):
            self.progres(i, len(sessions))
            trouve = False
            for n in ("1", "2", "3"):
                sym = cote_epu(s, iso, n)
                id_ = "ONU-" + sym
                if depot.a_fichier(id_) or (self.liens_seulement and depot.connu(id_)):
                    trouve = True
                    continue
                if n != "1" and not trouve:
                    break  # pas de rapport national à cette session : inutile de chercher /2 et /3
                res = self._doc_onu(sym, langues)
                if not res:
                    if n == "1":
                        break
                    continue
                trouve = True
                titre = EPU_DOCS[n] % (s, de_pays if n == "1" else sans_de(de_pays))
                self._enregistrer_onu(depot, "EPU", "session_%02d" % s, id_, sym,
                                      "ONU, Conseil des droits de l’homme, Groupe de travail sur l’Examen périodique universel",
                                      titre, res)
            if trouve:
                depot.etat["epu_derniere_session"] = max(depot.etat.get("epu_derniere_session", 0), s)

    # -- base des organes de traités : état des rapports, courriers de suivi --
    def chercher_country_id(self, noms_en):
        """Identifiant OHCHR du pays, lu dans la liste déroulante de la page « état des ratifications »."""
        try:
            r = self._get(TB_TRAITES_LISTE)
        except Arret:
            raise
        except Exception as e:
            self.log("  ! recherche de l’identifiant OHCHR : %s" % e)
            return ""
        cibles = {norm(n) for n in noms_en if n}
        for val, nom in re.findall(r'<option[^>]*value="(\d+)"[^>]*>\s*([^<]+?)\s*</option>', r.text or "", re.I):
            if norm(html.unescape(nom)) in cibles:
                self.log("  Identifiant OHCHR du pays trouvé : %s" % val)
                return val
        m = re.search(r"CountryID=(\d+)[^\"'<>]*[\"'][^>]*>\s*(?:%s)\s*<" % "|".join(re.escape(n) for n in noms_en if n),
                      r.text or "", re.I)
        return m.group(1) if m else ""

    def base_organes(self, depot, iso, country_id="", comites=None, communs=True, sans_sr=False):
        """comites : None = tous ; sinon liste de sigles (CCPR, CAT…). communs : garder aussi les documents
        sans comité identifiable (document de base HRI/CORE…). sans_sr : écarter les comptes rendus de séance."""
        self._base_comites = set(comites) if comites is not None else None
        self._base_communs, self._base_sans_sr = communs, sans_sr
        if self._base_comites is not None:
            self.log("  Comités retenus : %s%s%s" % (", ".join(sorted(self._base_comites)) or "aucun",
                                                   " + documents communs" if communs else "",
                                                   " ; sans comptes rendus de séance" if sans_sr else ""))
        elif sans_sr:
            self.log("  Tous les comités ; sans comptes rendus de séance")
        self._bilan = {k: 0 for k in ("téléchargé(s)", "déjà présent(s)", "sans fichier téléchargeable", "lien(s) noté(s)",
                                      "écarté(s) par les filtres", "écarté(s) : autre pays")}
        self._echecs = 0
        self._tentes = set()
        url = TB_PAYS.format(iso=iso, lang="FR")
        try:
            r = self._get(url)
            page = r.text if r.status_code == 200 else ""
        except Arret:
            raise
        except Exception as e:
            self.log("  ! base des organes de traités inaccessible : %s" % e)
            page = ""
        if page:
            p = _Tables()
            p.feed(page)
            brutes = [row for row in p.rows if len(row) >= 3]
            lignes = filtrer_etat_rapports(brutes)
            if self._base_comites is not None:
                lignes = [row for row in lignes
                          if any(re.search(r"\b%s\b" % c, " ".join(row)) for c in self._base_comites)]
            self.log("  (tableaux de la page : %d ligne(s), dont %d retenue(s) pour l’état des rapports)"
                     % (len(brutes), len(lignes)))
            if lignes:
                chemin = depot.chemin("Organes de traités", "etat_des_rapports.csv")
                with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.writer(f, delimiter=";")
                    for row in lignes:
                        w.writerow(row)
                self.log("  État des rapports : %d ligne(s) -> %s" % (len(lignes), os.path.relpath(chemin, depot.racine)))
                depot.ajouter({"id": "ONU-ETAT-RAPPORTS", "categorie": "Organes de traités",
                               "auteur": "ONU, Haut-Commissariat des Nations Unies aux droits de l’homme",
                               "titre": "état des rapports", "url": url, "consulte_le": self.aujourdhui,
                               "fichier": os.path.relpath(chemin, depot.racine)})
            else:
                self.log("  État des rapports : tableau introuvable (page probablement générée par JavaScript) ; lien : %s" % url)
            # documents liés depuis la page du pays (dont les courriers de suivi)
            vus_pays, n_pays = set(), 0
            for row, liens in zip(p.rows, p.links):
                for href in liens:
                    abs_url = urllib.parse.urljoin(TB_BASE, html.unescape(href))
                    if re.search(r"(symbolno=|/Treaties/.+\.(pdf|docx?)$|Download\.aspx)", abs_url, re.I) and abs_url not in vus_pays:
                        vus_pays.add(abs_url)
                        n_pays += 1
                        self._doc_base(depot, iso, abs_url, row)
            for href in p.all_links:  # liens hors tableaux
                abs_url = urllib.parse.urljoin(TB_BASE, html.unescape(href))
                if re.search(r"(symbolno=|/Treaties/.+\.(pdf|docx?)$)", abs_url, re.I) and abs_url not in vus_pays:
                    vus_pays.add(abs_url)
                    n_pays += 1
                    self._doc_base(depot, iso, abs_url, [])
            self.log("  Page du pays : %d lien(s) vers des documents" % n_pays)
            if not country_id:
                m = re.search(r"CountryID=(\d+)", page)
                country_id = m.group(1) if m else ""
        if not country_id:
            self.log("  Documents de la base : identifiant OHCHR du pays inconnu. Voir le mode d’emploi "
                     "(champ « CountryID ») ; en attendant, lien de recherche : %s" % (TB_BASE + "TBSearch.aspx?Lang=en"))
            depot.marquer("base_organes")
            return
        depot.etat["country_id"] = country_id
        vus, page_n = set(), 1
        url_p = TB_RECHERCHE.format(cid=country_id)
        texte_prec = ""
        while page_n <= 60:
            try:
                if page_n == 1:
                    r = self._get(url_p)
                else:
                    # l'adresse ne change pas d'une page à l'autre : il faut renvoyer le formulaire
                    form = formulaire_page_suivante(texte_prec, page_n)
                    if not form:
                        self.log("  (pas de page %d)" % page_n)
                        break
                    action, donnees = form
                    cible = urllib.parse.urljoin(url_p, action) if action else url_p
                    self._verif()
                    time.sleep(PAUSE)
                    r = self.s.post(cible, data=donnees, timeout=60,
                                    headers={"Referer": url_p, "Content-Type": "application/x-www-form-urlencoded"})
            except Arret:
                raise
            except Exception as e:
                self.log("  ! %s" % e)
                break
            texte_prec = r.text if r.status_code == 200 else ""
            p = _Tables()
            p.feed(texte_prec)
            nouveaux = 0
            for row, liens in zip(p.rows, p.links):
                for href in liens:
                    abs_url = urllib.parse.urljoin(TB_BASE, html.unescape(href))
                    if not re.search(r"(symbolno=|/Treaties/.+\.(pdf|docx?)$)", abs_url, re.I):
                        continue
                    if abs_url in vus:
                        continue
                    vus.add(abs_url)
                    nouveaux += 1
                    self._doc_base(depot, iso, abs_url, row)
            self.log("  page %d : %d lien(s)" % (page_n, nouveaux))
            if not nouveaux:
                break
            page_n += 1
        self.log("  Documents : " + ", ".join("%d %s" % (v, k) for k, v in self._bilan.items() if v))
        self.rapports_examines(depot, iso)
        depot.marquer("base_organes")

    def rapports_examines(self, depot, iso):
        """Les observations finales citent le rapport examiné (« le rapport initial de l’Indonésie
        (CCPR/C/IDN/1) ») : on télécharge ces rapports s'ils manquent, pour lire leur date de réception
        (calcul des retards dans l'onglet Rédaction)."""
        cotes = set()
        for f in list(depot.fiches.values()):
            cote = (f.get("cote") or "").replace("_", "/")
            if not re.search(r"/CO/\d", cote) or not f.get("fichier"):
                continue
            chemin = os.path.join(depot.racine, f["fichier"])
            if not chemin.lower().endswith(".pdf") or not os.path.exists(chemin):
                continue
            try:
                contenu_ = open(chemin, "rb").read()
                txt = texte_pdf(contenu_, pages=2)
            except Exception:
                continue
            d_off = date_depuis_pdf(contenu_)
            if d_off and d_off != f.get("date"):  # date officielle de la couverture
                f["date"] = d_off
                depot.fiches[f["id"]] = f
            t1 = " ".join(txt.split())
            # cote actuelle, dans le texte ou en note : CCPR/C/IDN/2, CEDAW/C/IDN/8-9, E/C.12/IDN/1
            for m in re.finditer(r"\b((?:CCPR|CAT|CEDAW|CERD|CRC|CRPD|CED|CMW)/C/%s/\d{1,2}(?:-\d{1,2})?|"
                                 r"E/C\.12/%s/\d{1,2}(?:-\d{1,2})?)(?![/\w])" % (iso, iso), t1):
                cotes.add((m.group(1), ""))
            # ancienne cote : « a examiné le deuxième rapport périodique de l’Indonésie (CAT/C/72/Add.1) »
            m = re.search(r"a examiné (?:le |les )?(.{0,160}?)\(\s*((?:CCPR|CAT|CEDAW|CERD|CRC|CRPD|CED|CMW)/C/"
                          r"\d+/Add\.\s?\d+|E/C\.12/\d+/Add\.\s?\d+|E/\d{4}/\d+/Add\.\s?\d+)\s*\)", t1)
            if m:
                quoi = re.sub(r"\s+(de l[’']|du |des |de la ).*$", "", m.group(1)).strip()
                cotes.add((m.group(2).replace(" ", ""), quoi))
        manquants = [(c, q) for c, q in sorted(cotes) if not depot.a_fichier("ONU-" + c)]
        if not manquants:
            return
        self.log("  Rapports de l’État examinés à télécharger (date de réception) : %s"
                 % ", ".join(c for c, q in manquants))
        for sym, quoi_lu in manquants:
            comite = comite_du_document(sym, "")
            res = None
            for lg in ("fr", "en"):
                res = self._fichier(ODS_URL.format(sym=urllib.parse.quote(sym, safe=""), lang=lg))
                if res:
                    break
            if not res:
                self.log("  ? %s : pas de fichier" % sym)
                continue
            ext, contenu = res
            chemin = depot.chemin("Organes de traités", comite or "divers", "%s.%s" % (slug(sym.replace("/", "_"))[:90], ext))
            with open(chemin, "wb") as fh:
                fh.write(contenu)
            n = re.search(r"/(\d{1,2})(?:-(\d{1,2}))?$", sym)
            num = int(n.group(1)) if n else 0
            ords = re.search(r"\b(initial|premier|deuxième|troisième|quatrième|cinquième|sixième|septième|huitième|"
                             r"neuvième|dixième|second|third|fourth|fifth)\b", quoi_lu or "", re.I)
            if ords:
                o = ords.group(1).lower()
                quoi = "rapport initial" if o in ("initial", "premier") else "%s rapport périodique" % o
            elif quoi_lu:
                quoi = quoi_lu
            else:
                quoi = ("rapport initial" if num == 1 else "rapport périodique n° %s" % n.group(0)[1:]) if n else "rapport"
            depot.ajouter({"id": "ONU-" + sym, "categorie": "Organes de traités",
                           "auteur": "ONU, " + (COMITES[comite][1] if comite else "organes de traités"),
                           "titre": "%s de l’État partie" % quoi, "cote": sym,
                           "date": date_depuis_pdf(contenu) if ext == "pdf" else "",
                           "url": ODS_URL.format(sym=urllib.parse.quote(sym, safe=""), lang="fr"),
                           "consulte_le": self.aujourdhui, "fichier": os.path.relpath(chemin, depot.racine)})
            self.log("  + %s (rapport de l’État)" % sym)

    def _fichier_tb(self, url, sym=""):
        """Download.aspx du HCDH renvoie une page de choix (langues × formats) : on y prend
        de préférence le français, puis l'anglais, puis toute autre langue ; le PDF avant le Word.
        En dernier recours, pour une cote officielle, on essaie le système de documents de l'ONU."""
        try:
            r = self._get(url)
        except Arret:
            raise
        except Exception as e:
            self.log("  ! réseau : %s" % e)
            return None
        contenu = getattr(r, "content", b"") or b""
        if r.status_code == 200 and type_fichier(contenu[:8]):
            return type_fichier(contenu[:8]), contenu
        page = r.text if r.status_code == 200 else ""
        base = getattr(r, "url", url) or url
        p = _Tables()
        p.feed(page)
        LANG = {"fr": r"\b(french|fran[cç]ais)\b", "en": r"\b(english|anglais)\b"}

        def cands(lignes_liens):
            out = []
            for txt, liens in lignes_liens:
                for h in liens:
                    a = urllib.parse.urljoin(base, html.unescape(h))
                    if a.startswith("javascript") or a.split("#")[0] == url or "Download.aspx" in a:
                        continue
                    if re.search(r"(FilesHandler|DownloadDraft|\.pdf|\.docx?|documents\.un\.org|undocs\.org|/api/symbol|"
                                 r"docstore|daccess|Shared%20Documents|Shared Documents)", a, re.I):
                        out.append((txt, a))
            return out

        tous = cands([(" ".join(row), liens) for row, liens in zip(p.rows, p.links)])
        if not tous:
            tous = cands([("", p.all_links)])
        # l'attribut title de chaque lien dit « French pdf », « English docx »… : plus fiable que la ligne
        titres = {}
        for tag in re.findall(r"<a\b[^>]*>", page, re.I):
            h = re.search(r'\bhref="([^"]+)"', tag)
            t = re.search(r'\btitle="([^"]*)"', tag)
            if h and t:
                titres[urllib.parse.urljoin(base, html.unescape(h.group(1)))] = html.unescape(t.group(1))

        def rang(txt, a):
            t = titres.get(a, "")
            ref = t or txt
            lg = 0 if re.search(LANG["fr"], ref, re.I) else 1 if re.search(LANG["en"], ref, re.I) else 2
            fmt = t or a
            return (lg, 0 if re.search(r"pdf", fmt, re.I) else 1)
        essais = [(rg[0], a) for rg, _, a in sorted((rang(t, a), i, a) for i, (t, a) in enumerate(tous))]
        vus, garde_word, lg_word = set(), None, None
        for lg, a in essais:
            if garde_word and lg != lg_word:
                break  # un Word en français vaut mieux qu'un PDF en anglais
            if a in vus:
                continue
            vus.add(a)
            if len(vus) > 8:
                break
            res = self._fichier(a)
            if res:
                if res[0] == "pdf":
                    return res
                if not garde_word:
                    garde_word, lg_word = res, lg
        if garde_word:
            return garde_word
        if sym and not sym.upper().startswith("INT/"):
            for lg in ("fr", "en"):
                res = self._fichier(ODS_URL.format(sym=urllib.parse.quote(sym, safe=""), lang=lg))
                if res:
                    return res
        self._echecs = getattr(self, "_echecs", 0) + 1
        if self._echecs <= 2:
            self.log("  ? pas de fichier sur la page de choix : %s (%d lien(s) candidat(s) : %s)"
                     % (url, len(tous), ", ".join(a for _, a in tous[:4]) or "aucun"))
        return None

    def _doc_base(self, depot, iso, url, row):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        sym = (q.get("symbolno") or [""])[0] or os.path.basename(urllib.parse.urlparse(url).path)
        id_ = "ONU-" + sym
        if id_ in self._tentes:  # même document lié depuis la page du pays et depuis la recherche
            return
        self._tentes.add(id_)
        texte_ligne = " – ".join(c for c in row if c)
        comite = comite_du_document(sym, texte_ligne)
        filtre = getattr(self, "_base_comites", None)
        if (filtre is not None and ((comite and comite not in filtre) or (not comite and not self._base_communs))) \
                or (getattr(self, "_base_sans_sr", False) and re.search(r"/SR[./\s]", sym.replace("_", "/"))):
            self._bilan["écarté(s) par les filtres"] += 1
            return
        codes = set(re.findall(r"(?<![A-Z])([A-Z]{3})(?![A-Z])", sym.replace("_", "/")))
        if iso not in codes and codes & CODES_ISO3:  # document d'un autre pays listé par erreur sur la page
            self._bilan["écarté(s) : autre pays"] += 1
            self.log("  (écarté, autre pays : %s)" % sym)
            return
        if depot.connu(id_) and (depot.a_fichier(id_) or self.liens_seulement):
            self._bilan["déjà présent(s)"] += 1
            return
        auteur = "ONU, " + COMITES[comite][1] if comite else "ONU, organes de traités"
        m = re.search(r"[_/](FU[A-Z]?)[_/]", sym)
        types_suivi = {"FUL": "courrier de suivi du Comité", "FUR": "rappel de suivi du Comité",
                       "FUI": "informations de suivi"}
        premier = (texte_ligne.split(" – ")[0].strip() if texte_ligne else "")
        titre = types_suivi.get(m.group(1), "document de suivi") if m else (
            (premier[:1].lower() + premier[1:]) if premier and premier != sym else sym)
        date = date_dans_texte(texte_ligne)
        if self.liens_seulement:
            depot.liens.append(("%s – %s" % (sym, titre), url))
            depot.ajouter({"id": id_, "categorie": "Organes de traités", "auteur": auteur, "titre": titre,
                           "cote": sym, "date": date, "url": url, "consulte_le": self.aujourdhui,
                           "remarques": texte_ligne[:300]})
            self._bilan["lien(s) noté(s)"] += 1
            return
        res = self._fichier_tb(url, sym)
        if not res:
            self._bilan["sans fichier téléchargeable"] += 1
            return
        ext, contenu = res
        base_nom = re.sub(r"\.(pdf|docx?)$", "", sym, flags=re.I)
        chemin = depot.chemin("Organes de traités", comite or "divers", "%s.%s" % (slug(base_nom.replace("/", "_"))[:90], ext))
        with open(chemin, "wb") as f:
            f.write(contenu)
        if ext == "pdf":  # la date officielle est celle de la couverture (« Distr. générale 21 août 2013 »)
            date = date_depuis_pdf(contenu) or date
        depot.ajouter({"id": id_, "categorie": "Organes de traités", "auteur": auteur, "titre": titre,
                       "cote": sym, "date": date, "url": url, "consulte_le": self.aujourdhui,
                       "fichier": os.path.relpath(chemin, depot.racine), "remarques": texte_ligne[:300]})
        self._bilan["téléchargé(s)"] += 1
        self.log("  + %s" % sym)

    # -- ratifications ------------------------------------------------------
    def ratifications(self, depot, noms_en, base, chapitres=False, country_id="", selection=None, noms_fr=None):
        choisis, chemin_liste = liste_traites(base)
        traites = [(no, nom, "liste") for no, nom in choisis]
        if selection:
            sel = set(selection)
            traites = [t for t in traites if t[0] in sel]
            chapitres = False
            self.log("  Traités choisis : %d sur %d" % (len(traites), len(choisis)))
        if chapitres:
            deja = {no for no, _, _ in traites}
            for rom, pid, lib in CHAPITRES_UNTC:
                try:
                    r = self._get(CHAPITRE_URL.format(id=pid))
                except Arret:
                    raise
                except Exception as e:
                    self.log("  ! chapitre %s : %s" % (rom, e))
                    continue
                p = _Tables()
                p.feed(r.text if r.status_code == 200 else "")
                n = 0
                for row, liens in zip(p.rows, p.links):
                    for h in liens:
                        m = re.search(r"mtdsg_no=([A-Z]+-[\w-]+)", html.unescape(h))
                        if m and m.group(1) not in deja:
                            deja.add(m.group(1))
                            nom = max(row, key=len) if row else m.group(1)
                            traites.append((m.group(1), nom[:250], "chapitre " + rom))
                            n += 1
                self.log("  chapitre %s (%s) : %d traité(s) supplémentaire(s)" % (rom, lib, n))
        lignes = []
        for i, (no, nom, origine) in enumerate(traites, 1):
            self.progres(i, len(traites))
            rom = no.split("-")[0]
            ch = str(ROMAINS.get(rom, CHAPITRES.get(rom, "4")))
            url_en = TRAITE_URL.format(no=no, ch=ch, lang="_en")
            url_fr = TRAITE_URL.format(no=no, ch=ch, lang="_fr")
            row, reserves, langue = None, [], ""
            try:
                r = self._get(url_en)
                if r.status_code == 200:
                    row = ligne_pays(r.text, noms_en)
                    if row:
                        reserves = reserves_pays(r.text, noms_en)
                        langue = "anglais" if reserves else ""
            except Arret:
                raise
            except Exception as e:
                self.log("  ! %s : %s" % (nom, e))
            if reserves:
                # texte français quand la page française de la Collection le donne ; sinon l'anglais
                try:
                    rf = self._get(url_fr)
                    if rf.status_code == 200:
                        res_fr = reserves_pays(rf.text, list(noms_fr or []) + list(noms_en))
                        if res_fr and texte_en_francais(" ".join(t for _, t in res_fr)):
                            reserves, langue = res_fr, "français"
                except Arret:
                    raise
                except Exception as e:
                    self.log("  ! %s (page française) : %s" % (nom, e))
            if not row and origine != "liste":
                continue  # option « chapitres » : on ne garde que les traités auxquels l'État participe
            statut = row or "non partie (ou pays introuvable dans le tableau : à vérifier)"
            txt_res = " || ".join("%s : %s" % (sec, t) for sec, t in reserves)
            if reserves and langue == "anglais":
                txt_res = "[texte anglais : pas de version française sur la Collection des traités] " + txt_res
            lignes.append((nom, statut, "oui" if reserves else "", txt_res, url_fr, origine))
            self.log("  %s : %s%s" % (nom, statut, ("  [réserves / déclarations, en %s]" % langue) if reserves else ""))
            depot.ajouter({"id": "TRAITE-" + no, "categorie": "Ratifications",
                           "auteur": "ONU, Collection des Traités, état des traités", "titre": nom,
                           "cote": no, "url": url_fr, "consulte_le": self.aujourdhui,
                           "remarques": statut + ((" ; réserves / déclarations : voir ratifications.html") if reserves else "")})
        chemin = depot.chemin("Ratifications", "ratifications.csv")
        with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Traité", "Signature / ratification / adhésion", "Réserves ou déclarations",
                        "Texte des réserves et déclarations (français, sinon anglais ; extrait)", "Source", "Liste", "Consulté le"])
            for l in lignes:
                w.writerow(list(l) + [self.aujourdhui])
        page = depot.chemin("Ratifications", "ratifications.html")
        with open(page, "w", encoding="utf-8") as f:
            f.write("<!doctype html><meta charset='utf-8'><title>Ratifications</title><style>body{font-family:Arial;"
                    "max-width:950px;margin:2em auto;line-height:1.4}h2{font-size:1.05em;margin-top:1.6em}"
                    ".s{color:#08738f}.r{background:#f4f7f7;padding:.6em;border-left:3px solid #08a19f}"
                    ".en{color:#9a5b00;font-style:italic;margin:.3em 0}</style>"
                    "<h1>Ratifications, réserves et déclarations</h1><p>Collection des traités de l’ONU, consultée le %s. "
                    "Textes des réserves et déclarations repris de la page française de la Collection des traités ; "
                    "lorsqu’elle ne les donne pas, le texte anglais est repris et signalé. À vérifier sur la page "
                    "officielle (lien sous chaque traité), qui fait foi.</p>" % self.aujourdhui)
            for nom, statut, a_res, txt, url, origine in lignes:
                f.write("<h2>%s</h2><p class='s'>%s</p><p><a href='%s'>%s</a></p>" % (
                    html.escape(nom), html.escape(statut), html.escape(url), html.escape(url)))
                m_en = re.match(r"(\[texte anglais[^\]]*\] )", txt)
                if m_en:
                    e_ = m_en.group(1).strip(" []")
                    f.write("<p class='en'>%s</p>" % html.escape(e_[:1].upper() + e_[1:]))
                    txt = txt[len(m_en.group(1)):]
                for part in [x for x in txt.split(" || ") if x]:
                    f.write("<div class='r'>%s</div>" % html.escape(part))
        self.log("  -> %s et %s" % (os.path.relpath(chemin, depot.racine), os.path.relpath(page, depot.racine)))
        if country_id:
            self.procedures_plaintes(depot, country_id)
        depot.marquer("ratifications")

    def procedures_plaintes(self, depot, country_id):
        """Tableau du HCDH : ratifications et acceptation des procédures de plaintes / d'enquête."""
        url = TB_TRAITES_PAYS.format(cid=country_id)
        try:
            r = self._get(url)
        except Arret:
            raise
        except Exception as e:
            self.log("  ! HCDH (procédures de plaintes) : %s" % e)
            return
        p = _Tables()
        p.feed(r.text if r.status_code == 200 else "")
        lignes = [row for row in p.rows if len(row) >= 2]
        if not lignes:
            self.log("  HCDH : tableau des procédures de plaintes introuvable ; lien : %s" % url)
            return
        sections = tableaux_procedures(lignes, country_id)
        chemin = depot.chemin("Ratifications", "procedures_de_plaintes_HCDH.csv")
        with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            for i, (entete, rows) in enumerate(sections):
                if i:
                    w.writerow([])
                w.writerow(entete)
                w.writerows(rows)
        titres = {0: "Ratifications", 1: "Procédures de plaintes individuelles", 2: "Procédures d’enquête",
                  3: "Communications interétatiques"}
        h = ["<!doctype html><meta charset='utf-8'><title>Procédures de plaintes</title>"
             "<style>body{font-family:Arial;max-width:1000px;margin:2em auto}table{border-collapse:collapse;width:100%}"
             "td,th{border:1px solid #ccc;padding:.3em .5em;text-align:left;vertical-align:top}th{background:#eef5f5}"
             ".oui{color:#08738f;font-weight:bold}</style>",
             "<h1>Ratifications et procédures de plaintes (HCDH)</h1><p>Source : <a href='%s'>%s</a>, consultée le %s.</p>"
             % (html.escape(url), html.escape(url), self.aujourdhui)]
        for i, (entete, rows) in enumerate(sections):
            h.append("<h2>%s</h2><table><tr>%s</tr>" % (titres.get(i, "Tableau %d" % (i + 1)),
                                                     "".join("<th>%s</th>" % html.escape(c) for c in entete)))
            for r_ in rows:
                h.append("<tr>%s</tr>" % "".join("<td%s>%s</td>" % (" class='oui'" if c.strip().upper() == "OUI" else "",
                                                                   html.escape(c)) for c in r_))
            h.append("</table>")
        with open(chemin[:-4] + ".html", "w", encoding="utf-8") as f:
            f.write("".join(h))
        acceptees = [r_[0] for entete, rows in sections[1:2] for r_ in rows if any(c.strip().upper() == "OUI" for c in r_)]
        self.log("  Plaintes individuelles acceptées : %s" % (", ".join(acceptees) if acceptees else "aucune"))
        depot.ajouter({"id": "HCDH-PROCEDURES", "categorie": "Ratifications",
                       "auteur": "ONU, Haut-Commissariat des Nations Unies aux droits de l’homme",
                       "titre": "état des ratifications et acceptation des procédures de plaintes et d’enquête",
                       "url": url, "consulte_le": self.aujourdhui, "fichier": os.path.relpath(chemin, depot.racine)})
        self.log("  HCDH : procédures de plaintes -> %s" % os.path.relpath(chemin, depot.racine))

    # -- ReliefWeb ----------------------------------------------------------
    def requete_reliefweb(self, iso, depuis, sources, theme, mots, langues, offset=0, apres=None):
        conds = [{"field": "primary_country.iso3", "value": iso.lower()},
                 {"field": "date.original", "value": {"from": "%d-01-01T00:00:00+00:00" % depuis}}]
        if apres:
            conds.append({"field": "date.created", "value": {"from": apres.isoformat()}})
        if sources:
            conds.append({"field": "source.name", "value": list(sources), "operator": "OR"})
        if theme:
            conds.append({"field": "theme.name", "value": theme})
        if langues:
            conds.append({"field": "language.code", "value": list(langues), "operator": "OR"})
        q = {"filter": {"operator": "AND", "conditions": conds},
             "fields": {"include": ["title", "date.original", "source.name", "source.shortname",
                                    "url", "url_alias", "origin", "file.url", "file.filename", "file.mimetype",
                                    "language.code", "body-html"]},
             "sort": ["date.original:desc"], "limit": 200, "offset": offset}
        if mots:
            q["query"] = {"value": mots, "operator": "OR"}
        return q

    def reliefweb(self, depot, iso, appname, depuis, sources, theme, mots, langues, max_docs=300, maj=False,
                  flux_secours=None):
        """API ReliefWeb ; si pas d'appname ou si l'API refuse, bascule sur les flux RSS de secours."""
        ok = False
        if appname:
            ok = self._reliefweb_api(depot, iso, appname, depuis, sources, theme, mots, langues, max_docs, maj)
        else:
            self.log("ReliefWeb : pas de nom d’application (appname).")
        if not ok:
            if flux_secours:
                self.log("ReliefWeb : utilisation des flux RSS de secours (%d flux)" % len(flux_secours))
                self.reliefweb_rss(depot, flux_secours, depuis, maj, max_docs)
            else:
                self.log("ReliefWeb : aucun flux RSS de secours renseigné (voir le mode d’emploi).")

    def reliefweb_rss(self, depot, flux, depuis, maj=False, max_docs=300):
        apres = depot.derniere("reliefweb_rss") if maj else None
        seuil = apres or dt.datetime(int(depuis), 1, 1, tzinfo=dt.timezone.utc)
        n = 0
        for i, u in enumerate(flux, 1):
            try:
                r = self._get(u)
            except Arret:
                raise
            except Exception as e:
                self.log("  ! flux %s : %s" % (u, e))
                continue
            if r.status_code != 200:
                self.log("  ! flux %s : réponse %s%s" % (u, r.status_code, " (le site filtre les robots : ouvrez le flux dans "
                         "votre navigateur pour vérifier qu’il s’affiche)" if r.status_code in (202, 403) else ""))
                continue
            self.log("  flux : %s" % u)
            items = lire_flux_detail(r.content)
            self.log("  flux %d : %d élément(s)" % (i, len(items)))
            for k, it in enumerate(items, 1):
                self.progres(k, len(items))
                if it["date"] and it["date"] < seuil:
                    continue
                self._doc_reliefweb_rss(depot, it)
                n += 1
                if n >= max_docs:
                    self.log("  (limite de %d documents atteinte)" % max_docs)
                    depot.marquer("reliefweb_rss")
                    return
        depot.marquer("reliefweb_rss")

    def _doc_reliefweb_rss(self, depot, it):
        lien = it["lien"]
        id_ = id_reliefweb(lien) or "RW-" + slug(it["titre"], 100)
        if depot.connu(id_) and (depot.a_fichier(id_) or self.liens_seulement or not it["pieces"]):
            return
        d = it["date"]
        date_iso = d.date().isoformat() if d else ""
        auteur = it["auteur"]
        if not auteur:
            m = re.match(r"^([^:]{2,60}):\s", it["titre"])  # certains flux préfixent le titre par la source
            auteur = m.group(1) if m and m.group(1).lower() not in ("indonesia", "indonésie") else ""
        categorie, nom_cat = self.classer(auteur, "")
        court = slug(nom_cat or auteur, 40) if (nom_cat or auteur) else "ReliefWeb"
        fichier, url_doc = "", lien
        if it["pieces"]:
            url_doc = it["pieces"][0]
            if self.liens_seulement:
                depot.liens.append(("%s – %s" % (auteur or "ReliefWeb", it["titre"]), url_doc))
            else:
                res = self._fichier(url_doc)
                if res:
                    ext, contenu = res
                    chemin = depot.chemin(categorie, court,
                                          "%s_%s.%s" % (date_iso or "sans-date", slug(it["titre"], 70), ext))
                    with open(chemin, "wb") as fh:
                        fh.write(contenu)
                    fichier = os.path.relpath(chemin, depot.racine)
                else:  # site qui refuse les programmes : lien à ouvrir à la main
                    depot.liens.append(("%s – %s" % (auteur or "ReliefWeb", it["titre"]), url_doc))
        depot.ajouter({"id": id_, "categorie": categorie,
                       "auteur": auteur or "à compléter (voir la page ReliefWeb)", "titre": it["titre"],
                       "date": date_fr(d.date()) if d else "", "url": lien, "consulte_le": self.aujourdhui,
                       "fichier": fichier,
                       "remarques": ("PDF : " + url_doc) if it["pieces"] else "pas de PDF joint (page web)"})
        self.log("  + %s – %s%s" % (date_iso or "?", it["titre"][:85], "" if fichier or self.liens_seulement else
                                    ("  [PDF non téléchargé]" if it["pieces"] else "  [page web]")))

    def _reliefweb_api(self, depot, iso, appname, depuis, sources, theme, mots, langues, max_docs, maj):
        """Renvoie True si l'API a répondu normalement."""
        apres = depot.derniere("reliefweb") if maj else None
        if apres:
            self.log("ReliefWeb : documents ajoutés depuis la dernière collecte (%s)" % apres.date())
        offset, total, vus = 0, None, 0
        while True:
            q = self.requete_reliefweb(iso, depuis, sources, theme, mots, langues, offset, apres)
            self._verif()
            try:
                r = self.s.post(RW_URL.format(app=urllib.parse.quote(appname)), json=q, timeout=60)
            except Exception as e:
                self.log("  ! ReliefWeb : %s" % e)
                return False
            if r.status_code != 200:
                self.log("  ! L’API ReliefWeb a répondu %s : %s" % (r.status_code, r.text[:200]))
                return False
            data = r.json()
            if total is None:
                total = data.get("totalCount", 0)
                self.log("ReliefWeb : %d document(s) correspondent aux critères" % total)
            items = data.get("data", [])
            for it in items:
                vus += 1
                self.progres(vus, min(total, max_docs) or 1)
                self._doc_reliefweb(depot, it)
                if vus >= max_docs:
                    self.log("  (limite de %d documents atteinte : affinez les critères si besoin)" % max_docs)
                    depot.marquer("reliefweb")
                    return True
            offset += len(items)
            if not items or offset >= total:
                break
        depot.marquer("reliefweb")
        return True

    def _doc_reliefweb(self, depot, it):
        f = it.get("fields", {})
        id_ = id_reliefweb(f.get("url_alias") or f.get("url")) or "RW-%s" % it.get("id")
        if depot.connu(id_):
            return
        titre = f.get("title", "")
        date_iso = ((f.get("date") or {}).get("original") or "")[:10]
        try:
            date_txt = date_fr(dt.date.fromisoformat(date_iso))
        except Exception:
            date_txt = ""
        srcs = f.get("source") or []
        auteur = ", ".join(s.get("name", "") for s in srcs) or "Source inconnue"
        categorie, nom_cat = self.classer(srcs[0].get("name", "") if srcs else "", f.get("origin", ""))
        court = slug(nom_cat or ((srcs[0].get("shortname") or srcs[0].get("name")) if srcs else "autres"), 40)
        langue = ",".join(l.get("code", "") for l in (f.get("language") or []))
        url = f.get("origin") or f.get("url", "")
        prefixe = "%s_%s" % (date_iso or "sans-date", slug(titre, 70))
        fichier = ""
        pdfs = [x for x in (f.get("file") or []) if x.get("url")]
        if self.liens_seulement:
            depot.liens.append(("%s – %s" % (auteur, titre), pdfs[0]["url"] if pdfs else url))
        elif pdfs:
            res = self._fichier(pdfs[0]["url"])
            if res:
                ext, contenu = res
                chemin = depot.chemin(categorie, court, prefixe + "." + ext)
                with open(chemin, "wb") as fh:
                    fh.write(contenu)
                fichier = os.path.relpath(chemin, depot.racine)
        elif f.get("body-html"):
            chemin = depot.chemin(categorie, court, prefixe + ".html")
            with open(chemin, "w", encoding="utf-8") as fh:
                fh.write("<!doctype html><meta charset='utf-8'><title>%s</title><h1>%s</h1><p>%s – %s</p>"
                         "<p><a href='%s'>%s</a></p>%s" % (html.escape(titre), html.escape(titre),
                                                          html.escape(auteur), date_txt, html.escape(url),
                                                          html.escape(url), f["body-html"]))
            fichier = os.path.relpath(chemin, depot.racine)
        depot.ajouter({"id": id_, "categorie": categorie, "auteur": auteur, "titre": titre,
                       "date": date_txt, "url": url, "consulte_le": self.aujourdhui,
                       "fichier": fichier, "langue": langue})
        self.log("  + %s – %s" % (date_iso, titre[:90]))

    # -- veille presse / sources nationales ---------------------------------
    def veille(self, depot, flux, recherches, mots_filtre, hl="fr", gl="BE", depuis=None, maj=False):
        """flux : URLs RSS/Atom ; recherches : requêtes Google Actualités (ex. « site:kontras.org penyiksaan »).
        Rien n'est téléchargé : chaque article devient une fiche (titre, source, date, lien)."""
        # pas de seuil « dernière collecte » : une nouvelle recherche doit ramener aussi les articles
        # antérieurs ; les doublons sont évités par l'identifiant (lien) de chaque article
        seuil = dt.datetime(depuis, 1, 1, tzinfo=dt.timezone.utc) if depuis else None
        mots = [norm(m) for m in (mots_filtre or []) if m.strip()]
        urls = [(u, u) for u in flux] + [(GNEWS_URL.format(q=urllib.parse.quote(q), hl=hl, gl=gl), "Google Actualités : " + q)
                                         for q in recherches]
        lignes, total = [], 0
        for i, (u, lib) in enumerate(urls, 1):
            self.progres(i, len(urls))
            try:
                r = self._get(u)
            except Arret:
                raise
            except Exception as e:
                self.log("  ! %s : %s" % (lib, e))
                continue
            items = lire_flux(r.content) if r.status_code == 200 else []
            self.log("  %s : %d article(s) dans le flux" % (lib, len(items)))
            ecartes = {"antérieur(s) à %s" % depuis: 0, "écarté(s) par le filtre de mots": 0, "déjà connu(s)": 0}
            for titre, lien, d, src in items:
                if seuil and d and d < seuil:
                    ecartes["antérieur(s) à %s" % depuis] += 1
                    continue
                if mots and not any(m in norm(titre) for m in mots):
                    ecartes["écarté(s) par le filtre de mots"] += 1
                    continue
                id_ = "WEB-" + slug(lien, 150)
                if depot.connu(id_):
                    ecartes["déjà connu(s)"] += 1
                    continue
                total += 1
                host = src or urllib.parse.urlparse(lien).netloc.replace("www.", "")
                categorie, nom_cat = self.classer(src, lien, defaut="Presse")
                depot.ajouter({"id": id_, "categorie": categorie, "auteur": nom_cat or host,
                               "titre": titre, "date": date_fr(d.date()) if d else "", "url": lien,
                               "consulte_le": self.aujourdhui, "remarques": "flux : " + lib})
                lignes.append((d.date().isoformat() if d else "", host, titre, lien))
                self.log("  + %s – %s" % (d.date() if d else "?", titre[:90]))
            if any(ecartes.values()):
                self.log("    (" + ", ".join("%d %s" % (v, k) for k, v in ecartes.items() if v) + ")")
        if lignes:
            chemin = depot.chemin("Presse",
                                  "veille_%s.csv" % dt.datetime.now().strftime("%Y-%m-%d_%H%M%S"))
            with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Date", "Source", "Titre", "Lien"])
                for l in sorted(lignes, reverse=True):
                    w.writerow(l)
        self.log("Veille : %d nouvel(le)s article(s)" % total)
        depot.marquer("veille")

    # -- import de fichiers et de liens -------------------------------------
    def importer_fichier(self, depot, chemin_src, categorie, url=""):
        with open(chemin_src, "rb") as f:
            contenu = f.read()
        if b"<rss" in contenu[:600] or b"<feed" in contenu[:600]:
            return self.importer_flux_enregistre(depot, contenu, os.path.basename(chemin_src))
        return self._importer(depot, os.path.basename(chemin_src), contenu, categorie, url)

    def importer_flux_enregistre(self, depot, contenu, nom):
        """Flux RSS enregistré depuis le navigateur (ex. ReliefWeb, qui refuse les programmes) :
        une fiche par publication ; les PDF joints sont téléchargés si le site l'accepte, sinon
        ils sont listés dans la page « liens à télécharger »."""
        items = lire_flux_detail(contenu)
        self.log("  Flux enregistré %s : %d publication(s)" % (nom, len(items)))
        n0 = len(depot.nouveautes)
        for k, it in enumerate(items, 1):
            self.progres(k, len(items))
            self._doc_reliefweb_rss(depot, it)
        self.log("  -> %d nouvelle(s) fiche(s)" % (len(depot.nouveautes) - n0))
        return True

    def importer_liens(self, depot, liens, categorie):
        for i, url in enumerate(liens, 1):
            self.progres(i, len(liens))
            url = url.strip()
            if not url:
                continue
            if depot.connu("IMP-" + slug(url, 150)):
                continue
            if "hudoc.echr.coe.int" in url.lower():
                self.log("  ! %s\n    HUDOC n’accepte pas les accès par programme : ouvrez ce lien dans votre navigateur,\n"
                         "    téléchargez le PDF de l’arrêt, puis ajoutez ce PDF avec « Choisir des fichiers… » (onglet Importer)." % url)
                continue
            try:
                r = self._get(url)
            except Arret:
                raise
            except Exception as e:
                self.log("  ! %s : %s" % (url, e))
                continue
            if r.status_code != 200:
                self.log("  ! %s : réponse %s" % (url, r.status_code))
                continue
            ext = type_fichier(r.content[:8])
            nom = os.path.basename(urllib.parse.urlparse(url).path) or "document"
            if not ext:
                m = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I | re.S)
                titre = html.unescape(m.group(1)).strip() if m else nom
                cat_url, nom_cat = self.classer("", url, defaut=categorie) if categorie == "Automatique" else (categorie, "")
                depot.ajouter({"id": "IMP-" + slug(url, 150), "categorie": cat_url if cat_url != "Automatique" else "À classer",
                               "auteur": nom_cat or urllib.parse.urlparse(url).netloc.replace("www.", ""),
                               "titre": titre, "url": url, "consulte_le": self.aujourdhui})
                self.log("  + page web : %s" % titre[:90])
                continue
            self._importer(depot, nom if nom.lower().endswith("." + ext) else nom + "." + ext, r.content, categorie, url)

    def _importer(self, depot, nom, contenu, categorie, url=""):
        if categorie in ("Jurisprudence", "Automatique") and contenu[:4] == b"%PDF":
            import jurisprudence as J
            texte = texte_pdf(contenu, pages=3)
            if categorie == "Jurisprudence" or (J.reconnaitre(texte) and not REF_PS.search(texte)):
                res = J.Jurisprudence(self).fichier(depot, nom, contenu, url)
                if res is not None:
                    return res
        ext = type_fichier(contenu[:8]) or os.path.splitext(nom)[1].strip(".").lower() or "bin"
        texte = texte_pdf(contenu, pages=2) if ext == "pdf" else ""
        ref = REF_PS.search(texte)
        auteur, titre, cote_ = "", os.path.splitext(nom)[0], ""
        if ref:
            categorie = "Procédures spéciales"
            cote_ = "%s %s %s" % ref.groups()
            auteur = "ONU, Procédures spéciales du Conseil des droits de l’homme"
            titre = "communication %s" % cote_
        date = date_dans_texte(texte)
        if categorie == "Automatique":
            categorie, nom_cat = self.classer("", url)
            auteur = auteur or nom_cat
        id_ = "PS-" + cote_.replace(" ", "_") if cote_ else "IMP-" + slug(url or nom, 150)
        if depot.a_fichier(id_):
            if url and not depot.fiches[id_].get("url"):
                depot.fiches[id_]["url"] = url  # on complète le lien d'un document importé sans URL
            self.log("  = déjà présent : %s" % (cote_ or nom))
            return None
        base = "%s_%s" % (slug(cote_.replace("/", "-")) if cote_ else slug(os.path.splitext(nom)[0], 70), "")
        chemin = depot.chemin(categorie, base.strip("_") + "." + ext)
        with open(chemin, "wb") as f:
            f.write(contenu)
        depot.ajouter({"id": id_, "categorie": categorie, "auteur": auteur, "titre": titre, "cote": cote_,
                       "date": date, "url": url, "consulte_le": self.aujourdhui,
                       "fichier": os.path.relpath(chemin, depot.racine),
                       "remarques": "" if auteur else "auteur et titre à compléter"})
        self.log("  + importé : %s%s" % (cote_ or nom, (" (%s)" % date) if date else ""))
        return id_


# ---------------------------------------------------------------------------
# Configuration et lancement
# ---------------------------------------------------------------------------
def charger_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sauver_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def noms_pays_fr(iso, nom_fr):
    """Noms français possibles du pays (tels que la page française de la Collection des traités peut les écrire)."""
    noms = [nom_fr]
    if pycountry:
        try:
            tr = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"])
            c = pycountry.countries.get(alpha_3=iso)
            for a in ("name", "official_name", "common_name"):
                v = getattr(c, a, None) if c is not None else None
                if v:
                    noms.append(tr.gettext(v))
        except Exception:
            pass
    out = []
    for n in noms:
        for v in (n, re.sub(r"^(?:la|le|les|l[’'])\s*", "", n, flags=re.I)):
            if v and v not in out:
                out.append(v)
    return out


def noms_pays(iso):
    pays = {i: (fr, en) for i, fr, en in liste_pays()}
    nom_fr, nom_en = pays.get(iso, (iso, iso))
    noms = [nom_en]
    if pycountry:
        c = pycountry.countries.get(alpha_3=iso)
        for a in ("official_name", "common_name"):
            if c is not None and getattr(c, a, None):
                noms.append(getattr(c, a))
    return nom_fr, noms


def lancer_collecte(p, log=print, progres=None, stop_event=None, session=None):
    """p : dict de paramètres (voir interface / ligne de commande). Renvoie le chemin du journal."""
    iso = p["iso"].upper()
    nom_fr, noms_en = noms_pays(iso)
    depot = Depot(p["dossier"], iso, nom_fr)
    try:
        catalogue = Catalogue(p["dossier"])
    except Exception as e:
        log("  ! catalogue des sources illisible (%s) : classement par défaut" % e)
        catalogue = None
    col = Collecteur(log, progres, stop_event, session, p.get("liens_seulement", False), catalogue)
    de_pays = p.get("de_pays") or forme_de(nom_fr)
    maj = p.get("maj", False)
    log("Dossier : %s%s" % (depot.racine, "   [mode liens seulement]" if col.liens_seulement else ""))
    try:
        if (p.get("base_organes") or p.get("ratifications")) and not (p.get("country_id") or depot.etat.get("country_id")):
            cid = COUNTRY_IDS_CONNUS.get(iso) or col.chercher_country_id(noms_en)
            if cid:
                p["country_id"] = cid
                depot.etat["country_id"] = cid
        if p.get("comites") and p.get("types"):
            log("\n=== ONU : organes de traités (par cote) ===")
            col.organes(depot, iso, de_pays, p["comites"], p["types"], maj=maj)
        if p.get("base_organes"):
            log("\n=== ONU : base des organes de traités (état des rapports, courriers de suivi) ===")
            col.base_organes(depot, iso, p.get("country_id", "") or depot.etat.get("country_id", ""),
                             None if p.get("base_tous", True) else p.get("comites", []),
                             p.get("base_communs", True), p.get("base_sans_sr", False))
        if p.get("epu"):
            log("\n=== ONU : Examen périodique universel ===")
            col.epu(depot, iso, de_pays, maj=maj, resultats=p.get("epu_resultats", True))
        if p.get("ratifications"):
            log("\n=== Ratifications ===")
            col.ratifications(depot, noms_en + p.get("noms_onu", []), p["dossier"], p.get("ratif_chapitres", False),
                              p.get("country_id", "") or depot.etat.get("country_id", ""), p.get("ratif_selection") or None,
                              noms_fr=noms_pays_fr(iso, nom_fr))
        if p.get("reliefweb"):
            log("\n=== Rapports d’ONG et d’agences (ReliefWeb) ===")
            col.reliefweb(depot, iso, p.get("appname", ""), int(p.get("depuis", 2016)),
                          p.get("sources", []), p.get("theme", ""), p.get("mots", ""),
                          p.get("langues", ["fr", "en"]), int(p.get("max_docs", 300)), maj,
                          flux_reliefweb_normalises(p.get("flux_reliefweb", []), noms_en[0] if noms_en else ""))
        # une ligne qui n'est pas une adresse, mise dans les flux, est une recherche Google Actualités
        flux_v = [u for u in p.get("flux", []) if u.strip().lower().startswith("http")]
        p["recherches"] = list(p.get("recherches", [])) + [u for u in p.get("flux", []) if u.strip() and u not in flux_v]
        p["flux"] = flux_v
        if p.get("veille") and (p.get("flux") or p.get("recherches")):
            log("\n=== Veille presse et sources nationales ===")
            col.veille(depot, p.get("flux", []), p.get("recherches", []), p.get("filtre_veille", []),
                       p.get("hl", "fr"), p.get("gl", "BE"), int(p.get("depuis", 2016)), maj)
        if p.get("jur_hudoc") or p.get("jur_cjue") or p.get("jur_cc") or p.get("jur_refs"):
            log("\n=== Jurisprudence ===")
            import jurisprudence as J
            dj = depot if not p.get("jur_commun", True) else Depot(p["dossier"], "", "", "Jurisprudence (dossier commun)")
            if dj is not depot:
                log("Rangement : %s" % dj.racine)
            jur = J.Jurisprudence(col)

            def arts_de(section):
                a = J.lire_articles(p.get("jur_articles_" + section, p.get("jur_articles", "")))
                m = p.get("jur_mode_" + section, p.get("jur_mode", "tous"))
                if a:
                    log("   articles : %s (%s)" % (", ".join(a), "tous" if m == "tous" else "au moins un"))
                return a, m
            depuis_j = int(p.get("jur_depuis") or p.get("depuis") or 0) or None
            try:
                if p.get("jur_hudoc"):
                    log("-- Cour eur. D.H. (HUDOC)")
                    a, m = arts_de("hudoc")
                    jur.hudoc(dj, a, m, p.get("jur_etat", ""), p.get("jur_mots_hudoc", ""), depuis_j,
                              tuple(p.get("jur_types", ["JUDGMENTS"])), tuple(p.get("jur_langues", ["FRE", "ENG"])),
                              p.get("jur_gc", False), int(p.get("jur_max", 100)))
                if p.get("jur_cjue"):
                    log("-- C.J.U.E. (Cellar / EUR-Lex)")
                    a, m = arts_de("cjue")
                    jur.cjue(dj, p.get("jur_actes", []), a, m, p.get("jur_ref_cjue", p.get("jur_reference", "")),
                             p.get("jur_mots_cjue", ""), depuis_j, int(p.get("jur_max", 100)))
                if p.get("jur_cc"):
                    log("-- Cour constitutionnelle")
                    a, m = arts_de("cc")
                    a1, a2 = int(p.get("jur_cc_de", dt.date.today().year)), int(p.get("jur_cc_a", dt.date.today().year))
                    jur.cour_constitutionnelle(dj, list(range(min(a1, a2), max(a1, a2) + 1)), a, m,
                                               p.get("jur_ref_cc", p.get("jur_reference", "")), p.get("jur_mots_cc", ""),
                                               int(p.get("jur_max", 100)))
                if p.get("jur_refs"):
                    log("-- Import par référence")
                    jur.importer_references(dj, p["jur_refs"])
            finally:
                if dj is not depot:
                    j2 = dj.enregistrer()
                    log("Jurisprudence : %d nouvel(le)s décision(s). Journal : %s" % (len(dj.nouveautes), j2))
                    if getattr(dj, "page_liens", None):
                        log("Page des liens à télécharger : %s" % dj.page_liens)
        if p.get("importer_fichiers") or p.get("importer_liens"):
            log("\n=== Import ===")
            cat = p.get("categorie_import", "Automatique")
            for fch in p.get("importer_fichiers", []):
                col.importer_fichier(depot, fch, cat)
            if p.get("importer_liens"):
                col.importer_liens(depot, p["importer_liens"], cat)
    except Arret:
        log("\nCollecte interrompue : ce qui a déjà été téléchargé est conservé.")
    cid = p.get("country_id", "") or depot.etat.get("country_id", "")
    p["_country_id"] = cid
    p["_country_id_manquant"] = bool((p.get("base_organes") or p.get("ratifications")) and not cid)
    if p["_country_id_manquant"]:
        log("\nIdentifiant OHCHR du pays (CountryID) introuvable : voir la marche à suivre (fenêtre ou mode d’emploi).")
    journal = depot.enregistrer()
    log("\nTerminé : %d nouveau(x) document(s). Journal : %s" % (len(depot.nouveautes), journal))
    if getattr(depot, "page_liens", None):
        log("Page des liens à télécharger : %s" % depot.page_liens)
    return journal


# ---------------------------------------------------------------------------
# Interface graphique
# ---------------------------------------------------------------------------
def ouvrir(chemin):
    try:
        if sys.platform.startswith("win"):
            os.startfile(chemin)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", chemin])
        else:
            subprocess.Popen(["xdg-open", chemin])
    except Exception:
        webbrowser.open("file://" + os.path.abspath(chemin))


def interface():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from aide import AIDE, fenetre_info, bulle

    cfg = charger_config()
    pays = liste_pays()
    libelles = ["%s (%s)" % (fr, iso) for iso, fr, en in pays]

    root = tk.Tk(className="Probasile")  # nom de classe = lien avec le raccourci du menu (Linux)
    from tkinter import font as tkfont
    for nom_police in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont",
                       "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        try:
            tkfont.nametofont(nom_police).configure(family="Arial")
        except Exception:
            pass
    root.option_add("*Font", "TkDefaultFont")
    try:
        ttk.Style(root).theme_use("clam")  # thème plus lisible que le thème par défaut sous Linux
    except Exception:
        pass
    root.title("Probasile – v%s" % VERSION)
    try:  # icône de la fenêtre et de la barre des tâches
        _ici = os.path.dirname(os.path.abspath(__file__))
        root._icone = tk.PhotoImage(file=os.path.join(_ici, "icone.png"))
        root.iconphoto(True, root._icone)
        if sys.platform.startswith("win"):
            root.iconbitmap(default=os.path.join(_ici, "icone.ico"))
    except Exception:
        pass
    root.geometry("1080x900")
    q = queue.Queue()
    stop = threading.Event()
    etat = {"fichiers": [], "journal": None}

    main = ttk.Frame(root, padding=8)
    main.pack(fill="both", expand=True)

    # --- pays et dossier --------------------------------------------------
    top = ttk.LabelFrame(main, text="Pays et dossier", padding=6)
    top.pack(fill="x")
    ttk.Label(top, text="Pays :").grid(row=0, column=0, sticky="w")
    v_pays = tk.StringVar(value=cfg.get("pays_libelle", "Indonésie (IDN)"))
    cb_pays = bulle(ttk.Combobox(top, textvariable=v_pays, values=libelles, width=40),
                    "Tapez les premières lettres du pays puis choisissez-le dans la liste.")
    cb_pays.grid(row=0, column=1, sticky="w", padx=4)
    ttk.Label(top, text="Dans une phrase :").grid(row=0, column=2, sticky="e")
    v_de = tk.StringVar(value=cfg.get("de_pays", "de l’Indonésie"))
    bulle(ttk.Entry(top, textvariable=v_de, width=26),
          "Forme utilisée dans les titres des documents (« rapport national de l’Indonésie »). Remplie automatiquement ; "
          "corrigez-la si besoin.").grid(row=0, column=3, sticky="w", padx=4)
    ttk.Label(top, text="Dossier de base :").grid(row=1, column=0, sticky="w", pady=(4, 0))
    v_dossier = tk.StringVar(value=cfg.get("dossier", os.path.join(os.path.expanduser("~"), "Probasile")))
    ttk.Label(top, textvariable=v_dossier, foreground="#08738f").grid(row=1, column=1, columnspan=2, sticky="w", pady=(4, 0))

    def choisir():
        d = filedialog.askdirectory(initialdir=v_dossier.get() or os.path.expanduser("~"))
        if d:
            v_dossier.set(d)
            charger_catalogue()
    bulle(ttk.Button(top, text="Choisir…", command=choisir),
          "Le dossier où tout sera rangé : un sous-dossier par pays y sera créé.").grid(row=1, column=3, sticky="w", pady=(4, 0))
    top.columnconfigure(4, weight=1)
    ttk.Button(top, text="Aide générale", command=lambda: fenetre_info(root, "Aide générale", AIDE["general"])).grid(
        row=0, column=4, rowspan=2, sticky="e")

    def iso_choisi():
        m = re.search(r"\(([A-Z]{3})\)\s*$", v_pays.get().strip())
        if m:
            return m.group(1)
        t = norm(v_pays.get())
        for i, fr, en in pays:
            if norm(fr) == t or norm(en) == t:
                return i
        return None

    def filtrer(_e=None):
        t = norm(v_pays.get())
        cb_pays["values"] = [l for l in libelles if t in norm(l)] or libelles

    veille_cfg = cfg.setdefault("veille_par_pays", {})

    def maj_pays(_e=None):
        iso = iso_choisi()
        for i, fr, en in pays:
            if i == iso:
                v_de.set(forme_de(fr))
        vc = veille_cfg.get(iso or "", {})
        t_flux.delete("1.0", "end"); t_flux.insert("1.0", "\n".join(vc.get("flux", [])))
        t_rech.delete("1.0", "end"); t_rech.insert("1.0", "\n".join(vc.get("recherches", [])))
        v_filtre.set(" ".join(vc.get("filtre", [])))
        t_rwflux.delete("1.0", "end"); t_rwflux.insert("1.0", "\n".join(vc.get("flux_rw", [])))
        v_cid.set(cfg.get("country_ids", {}).get(iso or "", ""))
    cb_pays.bind("<KeyRelease>", filtrer)
    cb_pays.bind("<<ComboboxSelected>>", maj_pays)

    nb = ttk.Notebook(main)
    nb.pack(fill="x", pady=6)

    # --- onglet ONU -------------------------------------------------------
    # Mise en page : cadres numérotés sur deux colonnes ; les options d'un cadre sont grisées
    # tant que sa case « Inclure » n'est pas cochée (divulgation progressive).
    t1 = ttk.Frame(nb, padding=(8, 4, 8, 8))
    nb.add(t1, text="ONU")
    t1.columnconfigure(0, weight=1, uniform="col")
    t1.columnconfigure(1, weight=1, uniform="col")
    GRIS = "#666"

    def lier(var, widgets):
        """Active les widgets quand la case est cochée, les grise sinon."""
        def maj(*_):
            for w_ in widgets:
                try:
                    w_.state(["!disabled"] if var.get() else ["disabled"])
                except Exception:
                    pass
        var.trace_add("write", maj)
        maj()

    # Comités concernés (servent aux cadres 1 et 2)
    f_com = ttk.LabelFrame(t1, text="Comités concernés (cadres 1 et 2)", padding=(8, 4))
    f_com.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
    v_com = {c: tk.BooleanVar(value=c in cfg.get("comites", ["CCPR", "CAT"])) for c in COMITES}
    for i, c in enumerate(COMITES):
        bulle(ttk.Checkbutton(f_com, text=c, variable=v_com[c]), COMITES[c][1]).grid(row=0, column=i, sticky="w", padx=(0, 8))
    ttk.Button(f_com, text="Tout", width=5, command=lambda: [v.set(True) for v in v_com.values()]).grid(
        row=0, column=len(COMITES), padx=(8, 2))
    ttk.Button(f_com, text="Aucun", width=6, command=lambda: [v.set(False) for v in v_com.values()]).grid(
        row=0, column=len(COMITES) + 1)

    gauche = ttk.Frame(t1)
    gauche.grid(row=1, column=0, sticky="nwe", padx=(0, 6))
    droite = ttk.Frame(t1)
    droite.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
    gauche.columnconfigure(0, weight=1)
    droite.columnconfigure(0, weight=1)

    # 1. Documents principaux
    f1 = ttk.LabelFrame(gauche, text="1. Documents principaux des comités (par cote)", padding=(8, 4))
    f1.grid(row=0, column=0, sticky="we")
    v_typ = {t: tk.BooleanVar(value=t in cfg.get("types", ["CO", "Q", "QPR"])) for t in TYPES_DOC}
    v_org = tk.BooleanVar(value=cfg.get("organes_actif", bool(cfg.get("types", ["CO"]))))
    bulle(ttk.Checkbutton(f1, text="Inclure", variable=v_org),
          "Cherche les documents des comités cochés par leur cote (ex. CCPR/C/IDN/CO/2), en français si possible.").grid(
        row=0, column=0, sticky="w")
    w_typ = []
    for i, t in enumerate(TYPES_DOC):
        cb = ttk.Checkbutton(f1, text=TYPES_DOC[t], variable=v_typ[t])
        cb.grid(row=1 + i // 2, column=i % 2, sticky="w", padx=(18, 8))
        w_typ.append(cb)
    lier(v_org, w_typ)

    # 2. Base des organes de traités
    f2 = ttk.LabelFrame(gauche, text="2. Base des organes de traités (HCDH)", padding=(8, 4))
    f2.grid(row=1, column=0, sticky="we", pady=(6, 0))
    v_base = tk.BooleanVar(value=cfg.get("base_organes", True))
    bulle(ttk.Checkbutton(f2, text="Inclure : état des rapports, lettres de suivi, contributions, anciennes cotes",
                          variable=v_base),
          "Tout ce que le site du HCDH liste pour le pays, filtré selon les options ci-dessous.").grid(
        row=0, column=0, columnspan=2, sticky="w")
    v_btous = tk.BooleanVar(value=cfg.get("base_tous", False))
    r1 = ttk.Radiobutton(f2, text="seulement les comités cochés en haut", variable=v_btous, value=False)
    r2 = ttk.Radiobutton(f2, text="tous les comités (plusieurs centaines de documents)", variable=v_btous, value=True)
    r1.grid(row=1, column=0, columnspan=2, sticky="w", padx=(18, 0))
    r2.grid(row=2, column=0, columnspan=2, sticky="w", padx=(18, 0))
    v_bcom = tk.BooleanVar(value=cfg.get("base_communs", True))
    c1 = bulle(ttk.Checkbutton(f2, text="+ documents communs (document de base HRI/CORE)", variable=v_bcom),
               "Le document de base décrit les institutions et le droit du pays ; il ne relève d'aucun comité.")
    c1.grid(row=3, column=0, columnspan=2, sticky="w", padx=(18, 0))
    v_bsr = tk.BooleanVar(value=cfg.get("base_sans_sr", True))
    c2 = bulle(ttk.Checkbutton(f2, text="sans les comptes rendus de séance (…/SR.…)", variable=v_bsr),
               "Procès-verbaux des séances : nombreux et rarement utiles dans un dossier.")
    c2.grid(row=4, column=0, columnspan=2, sticky="w", padx=(18, 0))
    fcid = ttk.Frame(f2)
    fcid.grid(row=5, column=0, columnspan=2, sticky="w", padx=(18, 0), pady=(4, 0))
    ttk.Label(fcid, text="CountryID (facultatif) :").pack(side="left")
    v_cid = tk.StringVar(value=cfg.get("country_ids", {}).get(iso_choisi() or "", ""))
    e_cid = bulle(ttk.Entry(fcid, textvariable=v_cid, width=7),
                  "Numéro du pays sur le site du HCDH (Indonésie = 80). Trouvé seul en général ; sinon une fenêtre explique "
                  "comment le lire.")
    e_cid.pack(side="left", padx=4)
    lier(v_base, [r1, r2, c1, c2, e_cid])

    # 5. Procédures spéciales (colonne de gauche, en bas)
    f5 = ttk.LabelFrame(gauche, text="5. Procédures spéciales (rapporteurs spéciaux)", padding=(8, 4))
    f5.grid(row=2, column=0, sticky="we", pady=(6, 0))
    bulle(ttk.Button(f5, text="Ouvrir la recherche des communications",
                     command=lambda: webbrowser.open("https://spcommreports.ohchr.org/Tmsearch/TMDocuments")),
          "Téléchargez les lettres (« AL IDN 5/2026 »…) puis importez-les : la référence est reconnue.").grid(
        row=0, column=0, sticky="w")
    ttk.Label(f5, text="puis importer les PDF (onglet « Importer »)", foreground=GRIS).grid(row=1, column=0, sticky="w")

    # 3. EPU
    f3 = ttk.LabelFrame(droite, text="3. Examen périodique universel (EPU)", padding=(8, 4))
    f3.grid(row=0, column=0, sticky="we")
    v_epu = tk.BooleanVar(value=cfg.get("epu", True))
    bulle(ttk.Checkbutton(f3, text="Inclure : rapport national, compilation ONU, parties prenantes", variable=v_epu),
          "Les trois documents de base de chaque examen du pays.").grid(row=0, column=0, sticky="w")
    v_epu_res = tk.BooleanVar(value=cfg.get("epu_resultats", True))
    c3 = bulle(ttk.Checkbutton(f3, text="+ résultats : recommandations faites au pays et\n   recommandations acceptées ou refusées",
                               variable=v_epu_res),
               "Rapport du Groupe de travail, additif (réponse de l'État : acceptées / « notées »), décision du Conseil et "
               "liste thématique des recommandations.")
    c3.grid(row=1, column=0, sticky="w", padx=(18, 0))
    lier(v_epu, [c3])

    # 4. Ratifications
    f4 = ttk.LabelFrame(droite, text="4. Ratifications, réserves, plaintes individuelles", padding=(8, 4))
    f4.grid(row=1, column=0, sticky="we", pady=(6, 0))
    v_ratif = tk.BooleanVar(value=cfg.get("ratifications", True))
    bulle(ttk.Checkbutton(f4, text="Inclure", variable=v_ratif),
          "Dates de signature et de ratification, réserves et déclarations, objections d'autres États, "
          "procédures de plaintes acceptées.").grid(row=0, column=0, columnspan=3, sticky="w")
    ratif_sel = list(cfg.get("ratif_selection", []))
    v_ratsel = tk.StringVar()

    def maj_ratsel():
        v_ratsel.set("tous les traités de ma liste" if not ratif_sel else "%d traité(s) choisi(s)" % len(ratif_sel))

    def choisir_traites():
        liste = liste_traites(v_dossier.get())[0]
        w = tk.Toplevel(root)
        w.title("Traités à vérifier")
        w.transient(root)
        ttk.Label(w, text="Cochez les traités à vérifier pour ce lancement (rien de coché = toute la liste) :",
                  padding=(10, 8)).pack(anchor="w")
        cadre = ttk.Frame(w, padding=(10, 0))
        cadre.pack(fill="both", expand=True)
        vs = {}
        for i, (no, nom) in enumerate(liste):
            vs[no] = tk.BooleanVar(value=no in ratif_sel)
            ttk.Checkbutton(cadre, text="%s  (%s)" % (nom or no, no), variable=vs[no]).grid(
                row=i % 16, column=i // 16, sticky="w", padx=(0, 16))
        bas = ttk.Frame(w, padding=10)
        bas.pack(fill="x")
        ttk.Button(bas, text="Tout cocher", command=lambda: [v.set(True) for v in vs.values()]).pack(side="left")
        ttk.Button(bas, text="Tout décocher", command=lambda: [v.set(False) for v in vs.values()]).pack(side="left", padx=4)

        def valider():
            ratif_sel[:] = [no for no, v in vs.items() if v.get()]
            if len(ratif_sel) == len(vs):
                ratif_sel[:] = []
            maj_ratsel()
            w.destroy()
        ttk.Button(bas, text="Valider", command=valider).pack(side="right")
        ttk.Button(bas, text="Annuler", command=w.destroy).pack(side="right", padx=4)
        w.grab_set()

    ttk.Label(f4, text="Traités vérifiés :").grid(row=1, column=0, sticky="w", padx=(18, 4))
    l_rs = ttk.Label(f4, textvariable=v_ratsel, foreground="#08738f")
    l_rs.grid(row=1, column=1, columnspan=2, sticky="w")
    b_ch = bulle(ttk.Button(f4, text="Choisir les traités…", command=choisir_traites),
                 "Pour ce lancement seulement : ne vérifier que certains traités de votre liste.")
    b_ch.grid(row=2, column=0, sticky="w", padx=(18, 4), pady=(2, 0))
    b_ml = bulle(ttk.Button(f4, text="Modifier ma liste…",
                            command=lambda: fenetre_info(root, "Modifier la liste des traités", AIDE["traites"],
                                                         bouton=("Ouvrir traites.csv",
                                                                 lambda: ouvrir(liste_traites(v_dossier.get())[1])))),
                 "Ajouter ou retirer des traités de façon durable (fichier traites.csv).")
    b_ml.grid(row=2, column=1, sticky="w", pady=(2, 0))
    v_chap = tk.BooleanVar(value=cfg.get("ratif_chapitres", False))
    c4 = bulle(ttk.Checkbutton(f4, text="Élargir : ajouter tous les autres traités ratifiés ou signés par\n"
                                        "   le pays dans les chapitres « droits de l’homme », « réfugiés et\n"
                                        "   apatrides » et « matières pénales » de la Collection de l’ONU",
                               variable=v_chap),
               "En plus de votre liste, le programme parcourt ces trois chapitres de la Collection des traités de l'ONU "
               "(IV, V et XVIII) et ajoute chaque traité auquel le pays participe. Plus long ; ignoré si vous avez choisi "
               "des traités pour ce lancement.")
    c4.grid(row=3, column=0, columnspan=3, sticky="w", padx=(18, 0), pady=(4, 0))
    lier(v_ratif, [b_ch, b_ml, c4])
    maj_ratsel()

    def nom_en_courant():
        iso = iso_choisi()
        return next((en for i, fr, en in pays if i == iso), "")

    def cadre(parent, texte, row, column, **kw):
        f = ttk.LabelFrame(parent, text=texte, padding=(8, 4))
        f.grid(row=row, column=column, sticky=kw.pop("sticky", "nwe"), **kw)
        return f

    # --- onglet ReliefWeb -------------------------------------------------
    t2 = ttk.Frame(nb, padding=(8, 4, 8, 8))
    nb.add(t2, text="Rapports ONU, ONG, États (ReliefWeb)")
    t2.columnconfigure(0, weight=1, uniform="col")
    t2.columnconfigure(1, weight=1, uniform="col")
    v_rw = tk.BooleanVar(value=cfg.get("reliefweb", False))
    bulle(ttk.Checkbutton(t2, text="Inclure les rapports publiés sur ReliefWeb", variable=v_rw),
          "Rapports des organisations cochées ci-dessous (agences de l’ONU, ONG, gouvernements).").grid(
        row=0, column=0, sticky="w", pady=(0, 6))

    f_rs = cadre(t2, "1. Organisations suivies", 1, 0, padx=(0, 6))
    fp = ttk.Frame(f_rs)
    fp.grid(row=0, column=0, sticky="w")
    ttk.Label(fp, text="Préréglage :").pack(side="left")
    v_preset = tk.StringVar(value=cfg.get("preset", list(PRESETS)[0]))
    cb_pre = bulle(ttk.Combobox(fp, textvariable=v_preset, values=list(PRESETS), width=26, state="readonly"),
                   "Coche d’un coup les sources adaptées : droits humains (asile, OQT) ou santé (9ter).")
    cb_pre.pack(side="left", padx=4)
    f_src = ttk.Frame(f_rs, relief="sunken", borderwidth=1)
    f_src.grid(row=1, column=0, sticky="we", pady=(6, 0))
    can = tk.Canvas(f_src, width=470, height=250, highlightthickness=0)
    sb = ttk.Scrollbar(f_src, orient="vertical", command=can.yview)
    inner = ttk.Frame(can)
    inner.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))
    can.create_window((0, 0), window=inner, anchor="nw")
    can.configure(yscrollcommand=sb.set)
    can.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    can.bind_all("<Button-4>", lambda e: e.widget.winfo_toplevel() is root and str(e.widget).startswith(str(can))
                 and can.yview_scroll(-2, "units"), add="+")
    can.bind_all("<Button-5>", lambda e: e.widget.winfo_toplevel() is root and str(e.widget).startswith(str(can))
                 and can.yview_scroll(2, "units"), add="+")
    v_srcs = {}

    def charger_catalogue():
        for w in inner.winfo_children():
            w.destroy()
        v_srcs.clear()
        try:
            cat = Catalogue(v_dossier.get())
        except Exception as e:
            ttk.Label(inner, text="Catalogue illisible : %s" % e).pack(anchor="w")
            return
        choisies = set(cfg.get("sources", []))
        par_cat = {}
        for l in cat.reliefweb():
            par_cat.setdefault(l["categorie"], []).append(l)
        for c, _, _ in CATEGORIES:
            if c not in par_cat:
                continue
            ttk.Label(inner, text=c, font=("Arial", 9, "bold")).pack(anchor="w", pady=(3, 0), padx=4)
            ligne = ttk.Frame(inner)
            ligne.pack(anchor="w", padx=14)
            for i, l in enumerate(par_cat[c]):
                v = tk.BooleanVar(value=l["nom_reliefweb"] in choisies)
                v_srcs[l["nom_reliefweb"]] = (v, l)
                bulle(ttk.Checkbutton(ligne, text=l["nom"], variable=v), l["nom_reliefweb"]).grid(
                    row=i // 3, column=i % 3, sticky="w", padx=(0, 10))
    f_btn = ttk.Frame(f_rs)
    f_btn.grid(row=2, column=0, sticky="w", pady=(6, 0))
    bulle(ttk.Button(f_btn, text="Modifier le catalogue…",
                     command=lambda: fenetre_info(root, "Modifier le catalogue des sources", AIDE["catalogue"],
                                                  bouton=("Ouvrir catalogue_sources.csv",
                                                          lambda: ouvrir(Catalogue(v_dossier.get()).chemin)))),
          "Ajouter une organisation (ONG locale, média…) ou changer sa catégorie. Explications avant ouverture.").pack(side="left")
    bulle(ttk.Button(f_btn, text="Recharger", command=charger_catalogue),
          "Relire le catalogue après l’avoir modifié et enregistré.").pack(side="left", padx=4)
    bulle(ttk.Button(f_btn, text="Voir les catégories", command=lambda: fenetre_info(
        root, "Catégories et dossiers", "\n".join("## %s\nDossier %s — %s" % (c, d, t) for c, d, t in CATEGORIES))),
        "Les catégories et le dossier où chacune est rangée.").pack(side="left")

    droite2 = ttk.Frame(t2)
    droite2.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
    droite2.columnconfigure(0, weight=1)
    f_rf = cadre(droite2, "2. Filtres", 0, 0)
    ttk.Label(f_rf, text="Thème ReliefWeb :").grid(row=0, column=0, sticky="w")
    v_theme = tk.StringVar(value=cfg.get("theme", PRESETS[list(PRESETS)[0]]["theme"]))
    e_theme = bulle(ttk.Entry(f_rf, textvariable=v_theme, width=30),
                    "Thème ReliefWeb en anglais (ex. Protection and Human Rights, Health). Rempli par le préréglage.")
    e_theme.grid(row=0, column=1, sticky="w", padx=4)
    ttk.Label(f_rf, text="Mots-clés :").grid(row=1, column=0, sticky="w", pady=(4, 0))
    v_mots = tk.StringVar(value=cfg.get("mots", ""))
    e_mots = bulle(ttk.Entry(f_rf, textvariable=v_mots, width=30),
                   "Facultatif, en anglais de préférence (ex. religious minorities).")
    e_mots.grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))
    ttk.Label(f_rf, text="Langues :").grid(row=2, column=0, sticky="w", pady=(4, 0))
    fl = ttk.Frame(f_rf)
    fl.grid(row=2, column=1, sticky="w", pady=(4, 0))
    v_fr, v_en = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
    c_fr = ttk.Checkbutton(fl, text="français", variable=v_fr)
    c_en = ttk.Checkbutton(fl, text="anglais", variable=v_en)
    c_fr.pack(side="left", padx=4)
    c_en.pack(side="left")
    ttk.Label(f_rf, text="Max. documents :").grid(row=3, column=0, sticky="w", pady=(4, 0))
    v_max = tk.IntVar(value=cfg.get("max_docs", 300))
    s_max = ttk.Spinbox(f_rf, from_=10, to=1000, increment=50, textvariable=v_max, width=6)
    s_max.grid(row=3, column=1, sticky="w", padx=4, pady=(4, 0))

    f_ra = cadre(droite2, "3. Accès à ReliefWeb", 1, 0, pady=(6, 0))
    ttk.Label(f_ra, text="Nom d’application :").grid(row=0, column=0, sticky="w")
    v_app = tk.StringVar(value=cfg.get("appname", ""))
    e_app = bulle(ttk.Entry(f_ra, textvariable=v_app, width=26),
                  "Clé d’accès officielle (« appname »). Avec elle, tout est automatique. Sans elle, le programme essaie "
                  "le flux RSS, que ReliefWeb refuse souvent (voir le mode d’emploi).")
    e_app.grid(row=0, column=1, sticky="w", padx=4)
    ttk.Label(f_ra, text="Flux RSS de secours\n(une adresse par ligne ;\nvide = flux du pays)", foreground=GRIS).grid(
        row=1, column=0, sticky="nw", pady=(6, 0))
    t_rwflux = bulle(tk.Text(f_ra, height=3, width=34),
                     "Vide = flux du pays construit automatiquement. Vous pouvez coller l’adresse d’une liste filtrée "
                     "de ReliefWeb.")
    t_rwflux.grid(row=1, column=1, sticky="we", padx=4, pady=(6, 0))
    f_ra.columnconfigure(1, weight=1)
    fb3 = ttk.Frame(f_ra)
    fb3.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
    b_fp = bulle(ttk.Button(fb3, text="Ouvrir le flux du pays",
                            command=lambda: webbrowser.open(RW_RSS_PAYS.format(nom=urllib.parse.quote(nom_en_courant())))),
                 "Si ReliefWeb refuse le programme : ouvrez le flux, enregistrez-le (Ctrl+S, .xml) et importez ce fichier "
                 "dans l’onglet « Importer ».")
    b_fp.pack(side="left")
    b_ff = bulle(ttk.Button(fb3, text="Construire un flux filtré",
                            command=lambda: webbrowser.open("https://reliefweb.int/updates")),
                 "Filtrez la liste sur ReliefWeb (pays, organisation, thème) puis copiez l’adresse du bouton RSS.")
    b_ff.pack(side="left", padx=4)
    lier(v_rw, [cb_pre, e_theme, e_mots, c_fr, c_en, s_max, e_app, b_fp, b_ff])

    def appliquer_preset(_e=None):
        pr = PRESETS[v_preset.get()]
        if pr["code"]:
            for nom_rw, (v, l) in v_srcs.items():
                v.set(pr["code"] in l["prereglages"].split())
        if pr["theme"] or pr["code"]:
            v_theme.set(pr["theme"])
    cb_pre.bind("<<ComboboxSelected>>", appliquer_preset)
    charger_catalogue()
    if not cfg.get("sources"):
        appliquer_preset()

    # --- onglet veille ----------------------------------------------------
    t3 = ttk.Frame(nb, padding=(8, 4, 8, 8))
    nb.add(t3, text="Presse et sources nationales (veille)")
    t3.columnconfigure(0, weight=1, uniform="col")
    t3.columnconfigure(1, weight=1, uniform="col")
    v_veille = tk.BooleanVar(value=cfg.get("veille", False))
    bulle(ttk.Checkbutton(t3, text="Inclure la veille (listes mémorisées pour chaque pays)", variable=v_veille),
          "Crée une fiche par article (titre, source, date, lien) ; rien n’est téléchargé.").grid(
        row=0, column=0, sticky="w", pady=(0, 6))
    f_v1 = cadre(t3, "1. Recherches Google Actualités (une par ligne)", 1, 0, padx=(0, 6))
    t_rech = bulle(tk.Text(f_v1, height=7, width=52),
                   "Une recherche par ligne, comme dans Google : Indonesia blasphemy law  |  site:kontras.org penyiksaan")
    t_rech.grid(row=0, column=0, columnspan=2, sticky="we")
    ttk.Label(f_v1, text="ex. : Indonesia blasphemy law  •  site:kontras.org penyiksaan  •  \"Ahmadiyya\" Indonesia",
              foreground=GRIS).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 6))
    fz = ttk.Frame(f_v1)
    fz.grid(row=2, column=0, columnspan=2, sticky="w")
    ttk.Label(fz, text="Langue / pays de Google :").pack(side="left")
    v_hl = tk.StringVar(value=cfg.get("hl", "id"))
    v_gl = tk.StringVar(value=cfg.get("gl", "ID"))
    e_hl = bulle(ttk.Entry(fz, textvariable=v_hl, width=4), "Langue (id, en, fr…)")
    e_gl = bulle(ttk.Entry(fz, textvariable=v_gl, width=4), "Pays (ID, US, BE…)")
    e_hl.pack(side="left", padx=(4, 2))
    e_gl.pack(side="left")
    fz2 = ttk.Frame(f_v1)
    fz2.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
    boutons_z = []
    def presse_du_pays():
        iso = iso_choisi() or ""
        v_hl.set(LANGUE_PAYS.get(iso, "en"))
        v_gl.set(ISO2.get(iso, "US"))
    for lib, fn, aide_ in (("Presse du pays", presse_du_pays,
                            "Langue principale et édition Google du pays choisi (ex. id / ID pour l’Indonésie)."),
                           ("Internationale", lambda: (v_hl.set("en"), v_gl.set("US")), "Google Actualités en anglais"),
                           ("Belge", lambda: (v_hl.set("fr"), v_gl.set("BE")), "Google Actualités en français, édition Belgique")):
        b_ = bulle(ttk.Button(fz2, text=lib, command=fn), aide_)
        b_.pack(side="left", padx=(0, 4))
        boutons_z.append(b_)

    droite3 = ttk.Frame(t3)
    droite3.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
    droite3.columnconfigure(0, weight=1)
    f_v2 = cadre(droite3, "2. Flux RSS de sites (une adresse par ligne)", 0, 0)
    t_flux = bulle(tk.Text(f_v2, height=5, width=46),
                   "Adresse du flux d’un site : souvent un lien « RSS » en bas de page, ou …/feed/ ou …/rss.xml.")
    t_flux.grid(row=0, column=0, sticky="we")
    f_v3 = cadre(droite3, "3. Filtre (facultatif)", 1, 0, pady=(6, 0))
    ttk.Label(f_v3, text="Ne garder que les titres contenant :").grid(row=0, column=0, sticky="w")
    v_filtre = tk.StringVar()
    e_filtre = bulle(ttk.Entry(f_v3, textvariable=v_filtre, width=44),
                     "Mots séparés par des espaces. Laisser vide au début : un mot français écarte les titres anglais.")
    e_filtre.grid(row=1, column=0, sticky="we", pady=(2, 0))
    ttk.Label(t3, text="Seules des fiches sont créées (titre, source, date, lien) : les pages ne sont pas téléchargées. "
                       "« Depuis l’année » (en bas) écarte les articles plus anciens.",
              foreground=GRIS).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
    lier(v_veille, [e_hl, e_gl, e_filtre] + boutons_z)
    for f_ in (f_v1, f_v2, f_v3):
        f_.columnconfigure(0, weight=1)

    # --- onglet jurisprudence ---------------------------------------------
    import jurisprudence as J
    t5 = ttk.Frame(nb, padding=(8, 4, 8, 8))
    nb.add(t5, text="Jurisprudence")
    t5.columnconfigure(0, weight=1, uniform="col")
    t5.columnconfigure(1, weight=1, uniform="col")
    f_art = ttk.Frame(t5)
    f_art.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
    ttk.Label(f_art, text="Décisions depuis :").pack(side="left")
    v_jdep = tk.IntVar(value=cfg.get("jur_depuis", 2010))
    ttk.Spinbox(f_art, from_=1959, to=dt.date.today().year, textvariable=v_jdep, width=6).pack(side="left", padx=4)
    ttk.Label(f_art, text="   Max. par juridiction :").pack(side="left")
    v_jmax = tk.IntVar(value=cfg.get("jur_max", 50))
    ttk.Spinbox(f_art, from_=5, to=500, increment=5, textvariable=v_jmax, width=5).pack(side="left", padx=4)
    v_commun = tk.BooleanVar(value=cfg.get("jur_commun", True))
    bulle(ttk.Checkbutton(f_art, text="Dossier commun « Jurisprudence »", variable=v_commun),
          "Coché : la jurisprudence est rangée dans un dossier commun à tous les pays (dans le dossier de base). "
          "Décoché : dans 11_Jurisprudence du pays.").pack(side="left", padx=(14, 0))

    def ligne_articles(parent, row, cle, defaut, avec_ref=False, ex_ref=""):
        f = ttk.Frame(parent)
        f.grid(row=row, column=0, columnspan=8, sticky="w", pady=(4, 0))
        ttk.Label(f, text="Articles :").grid(row=0, column=0, sticky="w")
        va = tk.StringVar(value=cfg.get("jur_articles_" + cle, defaut))
        e_ = bulle(ttk.Entry(f, textvariable=va, width=14),
                   "Ex. « 3 » ou « 3, 13 » ; avec le texte : « 3 CEDH, 33 Genève, 3 CAT ». Vide = pas de filtre.")
        e_.grid(row=0, column=1, sticky="w", padx=4)
        vm = tk.StringVar(value=cfg.get("jur_mode_" + cle, "un"))
        r_1 = ttk.Radiobutton(f, text="tous", value="tous", variable=vm)
        r_2 = ttk.Radiobutton(f, text="au moins un", value="un", variable=vm)
        r_1.grid(row=0, column=2, sticky="w")
        r_2.grid(row=0, column=3, sticky="w", padx=(4, 0))
        bulle(r_1, "Les décisions doivent citer chacun des articles.")
        bulle(r_2, "Les décisions doivent citer l’un ou l’autre des articles.")
        vr = tk.StringVar(value=cfg.get("jur_ref_" + cle, ""))
        ws = [e_, r_1, r_2]
        if avec_ref:
            ttk.Label(f, text="de :").grid(row=1, column=0, sticky="w", pady=(2, 0))
            cbr = bulle(ttk.Combobox(f, textvariable=vr, width=38, values=[""] + [lib for lib, _ in J.TEXTES.values()]),
                        "Texte dont les articles sont cités " + ex_ref + ". Vide = l’acte ou le texte choisi ci-dessus.")
            cbr.grid(row=1, column=1, columnspan=3, sticky="w", padx=4, pady=(2, 0))
            ws.append(cbr)
        return va, vm, vr, ws

    gauche5 = ttk.Frame(t5)
    gauche5.grid(row=1, column=0, sticky="nwe", padx=(0, 6))
    gauche5.columnconfigure(0, weight=1)
    droite5 = ttk.Frame(t5)
    droite5.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
    droite5.columnconfigure(0, weight=1)

    # 1. HUDOC
    f_h = cadre(gauche5, "1. Cour eur. D.H. (HUDOC)", 0, 0)
    v_hud = tk.BooleanVar(value=cfg.get("jur_hudoc", False))
    bulle(ttk.Checkbutton(f_h, text="Inclure", variable=v_hud),
          "HUDOC refuse les programmes : le programme affiche une recherche toute prête à ouvrir dans le navigateur ; "
          "importez ensuite les PDF.").grid(row=0, column=0, sticky="w")
    fh1 = ttk.Frame(f_h)
    fh1.grid(row=1, column=0, columnspan=8, sticky="w", pady=(2, 0))
    ttk.Label(fh1, text="Mots-clés :").pack(side="left")
    v_hmots = tk.StringVar(value=cfg.get("jur_mots_hudoc", "Indonesia"))
    e_hm = ttk.Entry(fh1, textvariable=v_hmots, width=16)
    e_hm.pack(side="left", padx=4)
    ttk.Label(fh1, text="État défendeur :").pack(side="left")
    v_etat = tk.StringVar(value=cfg.get("jur_etat", ""))
    e_et = bulle(ttk.Entry(fh1, textvariable=v_etat, width=5), "Code à 3 lettres, ex. BEL (vide = tous les États).")
    e_et.pack(side="left", padx=4)
    fh2 = ttk.Frame(f_h)
    fh2.grid(row=2, column=0, columnspan=8, sticky="w", pady=(2, 0))
    v_arr, v_dec = tk.BooleanVar(value="JUDGMENTS" in cfg.get("jur_types", ["JUDGMENTS"])), tk.BooleanVar(value="DECISIONS" in cfg.get("jur_types", []))
    v_gc = tk.BooleanVar(value=cfg.get("jur_gc", False))
    v_hfr, v_hen = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
    ws_h = [e_hm, e_et]
    for lib, var in (("arrêts", v_arr), ("décisions", v_dec), ("Grande Chambre", v_gc), ("fr", v_hfr), ("en", v_hen)):
        cb_ = ttk.Checkbutton(fh2, text=lib, variable=var)
        cb_.pack(side="left", padx=(0, 6))
        ws_h.append(cb_)
    va_h, vm_h, _, ws_ = ligne_articles(f_h, 3, "hudoc", "3")
    lier(v_hud, ws_h + ws_)

    # 3. Cour constitutionnelle
    f_cc = cadre(gauche5, "3. Cour constitutionnelle", 1, 0, pady=(6, 0))
    v_cc = tk.BooleanVar(value=cfg.get("jur_cc", False))
    bulle(ttk.Checkbutton(f_cc, text="Inclure", variable=v_cc),
          "Parcourt les arrêts des années choisies et garde ceux qui citent les articles demandés.").grid(row=0, column=0, sticky="w")
    fc1 = ttk.Frame(f_cc)
    fc1.grid(row=1, column=0, columnspan=8, sticky="w", pady=(2, 0))
    ttk.Label(fc1, text="Années de").pack(side="left")
    v_cc1 = tk.IntVar(value=cfg.get("jur_cc_de", dt.date.today().year - 1))
    v_cc2 = tk.IntVar(value=cfg.get("jur_cc_a", dt.date.today().year))
    s_c1 = ttk.Spinbox(fc1, from_=1985, to=dt.date.today().year, textvariable=v_cc1, width=6)
    s_c1.pack(side="left", padx=4)
    ttk.Label(fc1, text="à").pack(side="left")
    s_c2 = ttk.Spinbox(fc1, from_=1985, to=dt.date.today().year, textvariable=v_cc2, width=6)
    s_c2.pack(side="left", padx=4)
    ttk.Label(fc1, text="Mots-clés :").pack(side="left", padx=(8, 0))
    v_ccmots = tk.StringVar(value=cfg.get("jur_mots_cc", "étrangers"))
    e_cm = ttk.Entry(fc1, textvariable=v_ccmots, width=12)
    e_cm.pack(side="left", padx=4)
    va_cc, vm_cc, vr_cc, ws_ = ligne_articles(f_cc, 2, "cc", "3", True, "(ou texte libre)")
    lier(v_cc, [s_c1, s_c2, e_cm] + ws_)

    # 4. Import par référence
    f_ref = cadre(gauche5, "4. Importer par référence (une par ligne)", 2, 0, pady=(6, 0))
    t_refs = bulle(tk.Text(f_ref, height=4, width=48),
                   "Une référence par ligne. HUDOC refuse les programmes : pour la Cour européenne, importez le PDF.")
    t_refs.grid(row=0, column=0, sticky="we")
    f_ref.columnconfigure(0, weight=1)
    ttk.Label(f_ref, text="ECLI • req. n° 59166/12 • C-465/07 • C. const. 23/2021 • C.E. 248.270 •\n"
                          "C.C.E. 212 381 • CAT/C/66/D/832/2017 • lien", foreground=GRIS).grid(row=1, column=0, sticky="w")

    # 2. C.J.U.E.
    f_c = cadre(droite5, "2. C.J.U.E. – arrêts qui citent ou interprètent un acte", 0, 0)
    v_cj = tk.BooleanVar(value=cfg.get("jur_cjue", False))
    bulle(ttk.Checkbutton(f_c, text="Inclure", variable=v_cj),
          "Arrêts qui citent ou interprètent les actes cochés, filtrés sur leurs articles.").grid(row=0, column=0, sticky="w")
    v_actes = {}
    f_act = ttk.Frame(f_c)
    f_act.grid(row=1, column=0, columnspan=4, sticky="w", padx=(18, 0))
    ws_c = []
    for i, (celex, lib) in enumerate(J.ACTES_UE):
        v = tk.BooleanVar(value=celex in cfg.get("jur_actes", ["32011L0095", "32024R1347"]))
        v_actes[celex] = v
        cb_ = bulle(ttk.Checkbutton(f_act, text=lib, variable=v), "CELEX " + celex)
        cb_.grid(row=i, column=0, sticky="w")
        ws_c.append(cb_)
    fc2 = ttk.Frame(f_c)
    fc2.grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
    ttk.Label(fc2, text="Autres actes (CELEX) :").pack(side="left")
    v_celex = tk.StringVar(value=cfg.get("jur_celex_libre", ""))
    e_cx = bulle(ttk.Entry(fc2, textvariable=v_celex, width=16), "Numéros CELEX séparés par des espaces, ex. 32013L0032.")
    e_cx.pack(side="left", padx=4)
    ttk.Label(fc2, text="Mots-clés :").pack(side="left")
    v_cmots = tk.StringVar(value=cfg.get("jur_mots_cjue", ""))
    e_cjm = ttk.Entry(fc2, textvariable=v_cmots, width=12)
    e_cjm.pack(side="left", padx=4)
    va_c, vm_c, vr_c, ws_ = ligne_articles(f_c, 3, "cjue", "", True, "(ou texte libre)")
    lier(v_cj, ws_c + [e_cx, e_cjm] + ws_)

    # 5. Recherche à la main
    f_man = cadre(droite5, "5. Recherche à la main (ouvre le site dans le navigateur)", 1, 0, pady=(6, 0))
    for i, (lib, url) in enumerate(J.RECHERCHES_MANUELLES):
        bulle(ttk.Button(f_man, text=lib.split(" (")[0], command=lambda u=url: webbrowser.open(u)), lib).grid(
            row=i // 4, column=i % 4, sticky="we", padx=2, pady=2)

    # --- onglet import ----------------------------------------------------
    t4 = ttk.Frame(nb, padding=(8, 4, 8, 8))
    nb.add(t4, text="Importer")
    t4.columnconfigure(0, weight=1, uniform="col")
    t4.columnconfigure(1, weight=1, uniform="col")
    f_i1 = cadre(t4, "1. Fichiers (PDF, Word, flux RSS enregistré .xml)", 0, 0, padx=(0, 6), pady=(34, 0))
    l_fich = ttk.Label(f_i1, text="Aucun fichier choisi", foreground="#08738f")

    def choisir_fichiers():
        fs = filedialog.askopenfilenames(title="Fichiers à importer",
                                         filetypes=[("Documents et flux RSS", "*.pdf *.doc *.docx *.xml *.rss"), ("Tous", "*.*")])
        etat["fichiers"] = list(fs)
        l_fich["text"] = "%d fichier(s) choisi(s)" % len(fs) if fs else "Aucun fichier choisi"
    bulle(ttk.Button(f_i1, text="Choisir des fichiers…", command=choisir_fichiers),
          "PDF, Word ou flux RSS enregistré (.xml). Les décisions de justice et les lettres des rapporteurs spéciaux "
          "sont reconnues automatiquement.").grid(row=0, column=0, sticky="w")
    l_fich.grid(row=0, column=1, sticky="w", padx=8)
    ttk.Label(f_i1, text="Reconnus automatiquement : arrêts (Cour eur. D.H., Cour const., C.E., C.C.E., Cass., C.I.J.),\n"
                         "lettres des procédures spéciales (« AL IDN 5/2026 »), flux RSS enregistrés (ReliefWeb…).",
              foreground=GRIS).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
    f_i2 = cadre(t4, "2. Liens (un par ligne)", 0, 1, padx=(6, 0), pady=(34, 0))
    t_liens = bulle(tk.Text(f_i2, height=5, width=48),
                    "Le PDF est téléchargé s’il y en a un ; sinon une fiche est créée avec le titre de la page. "
                    "Pas de liens HUDOC : téléchargez le PDF dans le navigateur.")
    t_liens.grid(row=0, column=0, sticky="we")
    f_i2.columnconfigure(0, weight=1)
    f_i3 = cadre(t4, "3. Rangement", 1, 0, columnspan=2, pady=(6, 0))
    ttk.Label(f_i3, text="Catégorie :").grid(row=0, column=0, sticky="w")
    v_cat = tk.StringVar(value=CATEGORIES_IMPORT[0])
    bulle(ttk.Combobox(f_i3, textvariable=v_cat, values=CATEGORIES_IMPORT, state="readonly", width=34),
          "« Automatique » : classement d’après l’organisation (catalogue) ou le type de document.").grid(
        row=0, column=1, sticky="w", padx=4)
    ttk.Label(f_i3, text="Pour les documents non reconnus, vérifiez l’auteur et le titre dans sources.csv.",
              foreground=GRIS).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    # --- onglet rédaction -------------------------------------------------
    import redaction as RD
    import bibliotheque as BB
    t6 = ttk.Frame(nb, padding=(8, 4, 8, 8))
    nb.add(t6, text="Rédaction")
    t6.columnconfigure(0, weight=1, uniform="col")
    t6.columnconfigure(1, weight=1, uniform="col")
    gauche6 = ttk.Frame(t6)
    gauche6.grid(row=0, column=0, sticky="nwe", padx=(0, 6), pady=(34, 0))
    gauche6.columnconfigure(0, weight=1)
    droite6 = ttk.Frame(t6)
    droite6.grid(row=0, column=1, sticky="nwe", padx=(6, 0), pady=(34, 0))
    droite6.columnconfigure(0, weight=1)

    def sources_redaction():
        try:
            return RD.charger_sources(dossier_pays(), v_dossier.get())
        except Exception as e:
            messagebox.showerror("Sources", "Lecture des sources impossible : %s" % e)
            return []

    def dossier_redaction():
        d = os.path.join(dossier_pays(), "Redaction")
        os.makedirs(d, exist_ok=True)
        return d

    # 1. Plan
    f_r1 = cadre(gauche6, "1. Créer un plan type", 0, 0)
    v_proc = tk.StringVar(value=cfg.get("red_procedure", "oqt"))
    for i, (cle, lib) in enumerate(RD.NOMS_PROCEDURES.items()):
        ttk.Radiobutton(f_r1, text=lib, value=cle, variable=v_proc).grid(row=i, column=0, columnspan=2, sticky="w")
    ttk.Label(f_r1, text="Nom(s) :").grid(row=3, column=0, sticky="w", pady=(6, 0))
    v_dem = tk.StringVar(value=cfg.get("red_demandeur", ""))
    bulle(ttk.Entry(f_r1, textvariable=v_dem, width=28),
          "Nom utilisé dans les titres du plan et les blocs (ex. Monsieur A. Exemple, Madame X, "
          "Monsieur et Madame Y et leurs enfants). Facultatif.").grid(row=3, column=1, sticky="w", padx=4, pady=(6, 0))
    ttk.Label(f_r1, text="Qui demande ?").grid(row=4, column=0, sticky="w", pady=(4, 0))
    _pers = list(RD.PERSONNES.items())
    v_pers = tk.StringVar(value=dict(_pers).get(cfg.get("red_personne", "m"), _pers[0][1]))
    bulle(ttk.Combobox(f_r1, textvariable=v_pers, values=[l for _, l in _pers], state="readonly", width=32),
          "Accorde le plan et les blocs : le demandeur / la demanderesse / les demandeurs, il / elle / ils, "
          "exposé / exposée / exposés… Pour une famille (homme et femme), choisissez « plusieurs personnes ».").grid(
        row=4, column=1, sticky="w", padx=4, pady=(4, 0))

    def personne():
        return next((k for k, l in _pers if l == v_pers.get()), "m")

    def biblio():
        c = BB.chemin_bibliotheque(v_dossier.get())
        while BB.AVIS:
            m = BB.AVIS.pop(0)
            ecrire(m)
            messagebox.showinfo("Bibliothèque de blocs", m)
        return c

    def creer_plan():
        iso = iso_choisi()
        if not iso:
            messagebox.showerror("Pays", "Choisissez un pays dans la liste.")
            return
        nom_fr = next((fr for i, fr, en in pays if i == iso), iso)
        cfg["red_procedure"], cfg["red_demandeur"] = v_proc.get(), v_dem.get().strip()
        cfg["red_personne"] = personne()
        cfg["red_calcules"] = v_calc.get()
        sauver_config(cfg)
        chemin = os.path.join(dossier_redaction(), "Plan_%s_%s.odt" % (v_proc.get(), dt.date.today().isoformat()))
        try:
            sel = cfg.get("red_blocs", {}).get(v_proc.get())
            RD.creer_plan(v_proc.get(), chemin, v_de.get().strip(), nom_fr,
                          v_dem.get().strip() or "[nom du demandeur]", sources_redaction(),
                          bibliotheque=biblio(), blocs=sel, log=ecrire, personne=personne(),
                          dossier_pays=dossier_pays() if v_calc.get() else None,
                          plans=RD.chemin_plans(v_dossier.get()))
        except Exception as e:
            messagebox.showerror("Plan", "Création impossible : %s" % e)
            return
        ecrire("Plan créé : %s" % chemin)
        ouvrir(chemin)
    fbl = ttk.Frame(f_r1)
    fbl.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
    v_nbl = tk.StringVar()

    def maj_nbl(*_):
        sel = cfg.get("red_blocs", {}).get(v_proc.get())
        v_nbl.set("blocs par défaut" if sel is None else "%d bloc(s) choisi(s)" % len(sel))
    v_proc.trace_add("write", maj_nbl)
    maj_nbl()

    def choisir_blocs():
        try:
            bib = BB.Bibliotheque(biblio())
        except Exception as e:
            messagebox.showerror("Bibliothèque", "Bibliothèque illisible : %s" % e)
            return
        blocs_ = bib.de_procedure(v_proc.get())
        sel = cfg.get("red_blocs", {}).get(v_proc.get())
        w = tk.Toplevel(root)
        w.title("Blocs de texte – " + RD.NOMS_PROCEDURES[v_proc.get()])
        w.transient(root)
        ttk.Label(w, text="Blocs à recopier dans le plan (vous pourrez les adapter au dossier) :",
                  padding=(10, 8)).pack(anchor="w")
        fr = ttk.Frame(w, padding=(10, 0))
        fr.pack(fill="both", expand=True)
        vs, rub, ligne = {}, None, 0
        for b in blocs_:
            if b.rubrique != rub:
                rub = b.rubrique
                ttk.Label(fr, text=rub, font=("Arial", 10, "bold")).grid(row=ligne, column=0, sticky="w", pady=(6, 0))
                ligne += 1
            vs[b.titre] = tk.BooleanVar(value=b.defaut if sel is None else b.titre in sel)
            ttk.Checkbutton(fr, text=b.titre + ("  (par défaut)" if b.defaut else ""), variable=vs[b.titre]).grid(
                row=ligne, column=0, sticky="w", padx=(14, 0))
            ligne += 1
        if not blocs_:
            ttk.Label(fr, text="Aucun bloc pour cette procédure dans la bibliothèque.").grid(row=0, column=0)
        bas = ttk.Frame(w, padding=10)
        bas.pack(fill="x")

        def valider():
            cfg.setdefault("red_blocs", {})[v_proc.get()] = [t_ for t_, v in vs.items() if v.get()]
            sauver_config(cfg)
            maj_nbl()
            w.destroy()

        def defaut():
            cfg.setdefault("red_blocs", {}).pop(v_proc.get(), None)
            sauver_config(cfg)
            maj_nbl()
            w.destroy()
        ttk.Button(bas, text="Revenir aux blocs par défaut", command=defaut).pack(side="left")
        ttk.Button(bas, text="Valider", command=valider).pack(side="right")
        ttk.Button(bas, text="Annuler", command=w.destroy).pack(side="right", padx=4)
        w.grab_set()
    bulle(ttk.Button(fbl, text="Choisir les blocs…", command=choisir_blocs),
          "Passages juridiques types (avec leurs notes) recopiés dans le plan : cochez ceux qui conviennent au dossier.").pack(
        side="left")
    ttk.Label(fbl, textvariable=v_nbl, foreground="#08738f").pack(side="left", padx=6)
    fbl2 = ttk.Frame(f_r1)
    fbl2.grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 0))
    bulle(ttk.Button(fbl2, text="Modifier la bibliothèque…", command=lambda: fenetre_info(
        root, "Modifier la bibliothèque de blocs", AIDE["bibliotheque"],
        bouton=("Ouvrir la bibliothèque", lambda: ouvrir(biblio())))),
        "Modifier ou ajouter des passages types (par ex. après une réforme). Explications avant ouverture.").pack(side="left")
    bulle(ttk.Button(fbl2, text="Modifier les plans…", command=lambda: fenetre_info(
        root, "Modifier les plans types", AIDE["plans"],
        bouton=("Ouvrir les plans types", lambda: ouvrir(RD.chemin_plans(v_dossier.get()))))),
        "Ajouter, renommer, déplacer ou supprimer des sections des plans (OQT, protection internationale, 9ter). "
        "Explications avant ouverture.").pack(side="left", padx=(4, 0))
    bulle(ttk.Button(fbl2, text="Textes de référence…", command=lambda: fenetre_info(
        root, "Modifier les textes de référence", AIDE["references"],
        bouton=("Ouvrir references_juridiques.csv", lambda: ouvrir(BB.chemin_references(v_dossier.get()))))),
        "Lois, conventions et arrêts cités dans les blocs (repères LOI1980, SOERING…) : référence complète et courte.").pack(
        side="left", padx=4)
    def fenetre_maj():
        from aide import TACHES_MAJ
        w = tk.Toplevel(root)
        w.title("Mettre à jour un arrêt ou un bloc")
        w.transient(root)
        w.geometry("980x600")
        haut = ttk.Frame(w, padding=(12, 10, 12, 0))
        haut.pack(fill="both", expand=True)
        ttk.Label(haut, text="Que voulez-vous faire ?", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
        lb = tk.Listbox(haut, width=38, height=10, exportselection=False, font=("Arial", 11), activestyle="none")
        for t, _ in TACHES_MAJ:
            lb.insert("end", t)
        lb.grid(row=1, column=0, sticky="nsw", padx=(0, 10))
        txt = tk.Text(haut, wrap="word", relief="flat", padx=10, pady=8, font=("Arial", 11), background="#fbfbfa")
        txt.grid(row=0, column=1, rowspan=2, sticky="nsew")
        sb = ttk.Scrollbar(haut, orient="vertical", command=txt.yview)
        sb.grid(row=0, column=2, rowspan=2, sticky="ns")
        txt.configure(yscrollcommand=sb.set)
        haut.columnconfigure(1, weight=1)
        haut.rowconfigure(1, weight=1)
        txt.tag_configure("titre", font=("Arial", 13, "bold"), foreground="#08738f", spacing1=4, spacing3=6)
        txt.tag_configure("puce", lmargin1=12, lmargin2=30, spacing1=3)

        def montrer(*_):
            i = (lb.curselection() or (0,))[0]
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            for ligne in TACHES_MAJ[i][1].split("\n"):
                if ligne.startswith("## "):
                    txt.insert("end", ligne[3:] + "\n", "titre")
                elif ligne.startswith("- "):
                    txt.insert("end", ligne[2:] + "\n", "puce")
                else:
                    txt.insert("end", ligne + "\n")
            txt.configure(state="disabled")
        lb.bind("<<ListboxSelect>>", montrer)
        lb.selection_set(0)
        montrer()
        bas = ttk.Frame(w, padding=10)
        bas.pack(fill="x")
        bulle(ttk.Button(bas, text="Ajouter une référence…", command=lambda: formulaire_reference(w)),
              "Formulaire pour ajouter une loi, une convention ou un arrêt aux textes de référence.").pack(side="left")
        bulle(ttk.Button(bas, text="Modifier / supprimer…", command=lambda: choisir_reference(w)),
              "Corriger une référence existante, ou supprimer une référence que vous avez ajoutée (par ex. un test).").pack(
            side="left", padx=4)
        bulle(ttk.Button(bas, text="Où ce repère est-il utilisé ?", command=lambda: chercher_repere(w)),
              "Liste des blocs de la bibliothèque qui citent un repère (ex. CCE-212381, LOI1980).").pack(
            side="left", padx=4)
        ttk.Button(bas, text="Ouvrir la bibliothèque", command=lambda: ouvrir(biblio())).pack(side="left", padx=4)
        ttk.Button(bas, text="Ouvrir les textes de référence",
                   command=lambda: ouvrir(BB.chemin_references(v_dossier.get()))).pack(side="left", padx=4)
        ttk.Button(bas, text="Fermer", command=w.destroy).pack(side="right")
        w.bind("<Escape>", lambda e: w.destroy())

    def formulaire_reference(parent, repere=None):
        """Ajouter une référence, ou (repere donné) la modifier ou la supprimer."""
        existante = None
        if repere:
            existante = next((r for r in BB.lire_references(v_dossier.get())
                              if (r.get("repere") or "").strip() == repere), None)
        f = tk.Toplevel(parent)
        f.title("Modifier la référence %s" % repere if existante else "Ajouter une référence")
        f.transient(parent)
        c = ttk.Frame(f, padding=12)
        c.pack(fill="both", expand=True)
        champs = [("repere", "Repère (court, sans espace)", "ex. CCE-310000"),
                  ("reference_complete", "Référence complète (1re citation)",
                   "ex. C.C.E., 5 mars 2026, n° 310 000 — juridiction, date, numéro ; sans page ni paragraphe"),
                  ("reference_courte", "Référence courte (après op.cit.)",
                   "ex. C.C.E., 5 mars 2026, n° 310 000 — vide = identique à la référence complète"),
                  ("url", "Lien", "seulement si le texte est en ligne (sinon vide)"),
                  ("consulte_le", "Consulté le", "ex. 28 septembre 2026 (seulement s’il y a un lien)"),
                  ("a_verifier", "Remarque", "facultatif, pour vous (ex. « à vérifier », « test à supprimer »)")]
        vars_ = {}
        for i, (k, lib, ex) in enumerate(champs):
            ttk.Label(c, text=lib + " :").grid(row=2 * i, column=0, sticky="w", pady=(6 if i else 0, 0))
            vars_[k] = tk.StringVar(value=(existante or {}).get(k, "") or "")
            e_ = ttk.Entry(c, textvariable=vars_[k], width=80)
            e_.grid(row=2 * i, column=1, sticky="we", padx=6, pady=(6 if i else 0, 0))
            if existante and k == "repere":
                e_.configure(state="readonly")
            ttk.Label(c, text=ex, foreground=GRIS).grid(row=2 * i + 1, column=1, sticky="w", padx=6)

        def ok():
            ligne = {k: v.get() for k, v in vars_.items()}
            if not ligne["reference_courte"].strip():
                ligne["reference_courte"] = ligne["reference_complete"]
            if existante:
                err = BB.modifier_reference(v_dossier.get(), repere, ligne)
            else:
                err = BB.ajouter_reference(v_dossier.get(), ligne)
            if err:
                messagebox.showerror("Référence", err, parent=f)
                return
            rep_ = ligne["repere"].strip()
            ecrire("Référence %s : %s" % ("modifiée" if existante else "ajoutée", rep_))
            messagebox.showinfo("Référence", "Référence %s %s. Utilisez-la ainsi : [[%s, p.3]] ou [[%s, §12]]."
                                % (rep_, "modifiée" if existante else "ajoutée", rep_, rep_), parent=f)
            f.destroy()
            actualiser()

        def supprimer_ref():
            if not messagebox.askyesno("Supprimer", "Supprimer définitivement la référence %s ?" % repere, parent=f):
                return
            err = BB.supprimer_reference(v_dossier.get(), repere)
            if err:
                messagebox.showinfo("Supprimer", err, parent=f)
                return
            ecrire("Référence supprimée : %s" % repere)
            f.destroy()
            actualiser()
        b = ttk.Frame(c)
        b.grid(row=2 * len(champs), column=0, columnspan=2, sticky="we", pady=(10, 0))
        if existante:
            ttk.Button(b, text="Supprimer cette référence", command=supprimer_ref).pack(side="left")
        ttk.Button(b, text="Annuler", command=f.destroy).pack(side="right")
        ttk.Button(b, text="Enregistrer" if existante else "Ajouter", command=ok).pack(side="right", padx=4)
        f.grab_set()

    def choisir_reference(parent):
        """Liste des textes de référence : choisir celle à modifier ou supprimer."""
        w = tk.Toplevel(parent)
        w.title("Modifier ou supprimer une référence")
        w.transient(parent)
        w.geometry("900x480")
        c = ttk.Frame(w, padding=12)
        c.pack(fill="both", expand=True)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(1, weight=1)
        v_f = tk.StringVar()
        bulle(ttk.Entry(c, textvariable=v_f), "Filtrer : CCE, Soering, loi…").grid(row=0, column=0, sticky="we")
        t = ttk.Treeview(c, columns=("rep", "ref"), show="headings", selectmode="browse")
        t.heading("rep", text="Repère")
        t.heading("ref", text="Référence complète")
        t.column("rep", width=190, stretch=False)
        t.column("ref", width=660)
        t.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        def remplir(*_):
            t.delete(*t.get_children())
            mots = norm(v_f.get()).split()
            for r in BB.lire_references(v_dossier.get()):
                txt = "%s %s" % (r.get("repere", ""), r.get("reference_complete", ""))
                if mots and not all(m_ in norm(txt) for m_ in mots):
                    continue
                t.insert("", "end", values=(r.get("repere", ""), r.get("reference_complete", "")))

        def ouvrir_sel(_e=None):
            sel = t.selection()
            if sel:
                formulaire_reference(w, t.item(sel[0], "values")[0])
                w.after(300, remplir)
        t.bind("<Double-1>", ouvrir_sel)
        v_f.trace_add("write", remplir)
        b = ttk.Frame(c)
        b.grid(row=2, column=0, sticky="we", pady=(8, 0))
        ttk.Button(b, text="Modifier / supprimer…", command=ouvrir_sel).pack(side="left")
        ttk.Button(b, text="Actualiser", command=remplir).pack(side="left", padx=4)
        ttk.Button(b, text="Fermer", command=w.destroy).pack(side="right")
        remplir()

    def chercher_repere(parent):
        from tkinter import simpledialog
        rep = simpledialog.askstring("Où ce repère est-il utilisé ?", "Repère (ex. CCE-212381, LOI1980, SOERING) :",
                                     parent=parent)
        if not rep or not rep.strip():
            return
        try:
            res = BB.blocs_citant(biblio(), rep.strip())
        except Exception as e:
            messagebox.showerror("Bibliothèque", str(e), parent=parent)
            return
        if not res:
            messagebox.showinfo("Où ce repère est-il utilisé ?", "Aucun bloc de la bibliothèque ne cite %s." % rep,
                                parent=parent)
            return
        lignes = ["## %d bloc(s) citent %s" % (len(res), rep.strip())]
        for proc, rub, titre, ex in res:
            lignes.append("- %s  puis  %s  puis  « %s »  (%s)" % (proc, rub, titre, ex))
        lignes.append("")
        lignes.append("Dans LibreOffice : Ctrl+H, cherchez %s et remplacez-le dans chacun de ces blocs." % rep.strip())
        fenetre_info(parent, "Où ce repère est-il utilisé ?", "\n".join(lignes),
                     bouton=("Ouvrir la bibliothèque", lambda: ouvrir(biblio())))

    bulle(ttk.Button(f_r1, text="Mettre à jour un arrêt ou un bloc…", command=fenetre_maj),
          "Assistant pas à pas : remplacer un arrêt, corriger une référence, modifier ou ajouter un bloc, "
          "après une réforme.").grid(row=7, column=0, columnspan=2, sticky="w", pady=(4, 0))
    v_calc = tk.BooleanVar(value=cfg.get("red_calcules", True))
    fcalc = ttk.Frame(f_r1)
    fcalc.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))
    bulle(ttk.Checkbutton(fcalc, text="Ajouter les paragraphes calculés", variable=v_calc),
          "Plans OQT et protection internationale : paragraphes écrits à partir de la collecte de l’onglet ONU "
          "(traités ratifiés, signés ou non ; plaintes individuelles et articles 20 à 22 de la Convention contre la "
          "torture ; rapports remis en retard avec calcul du retard ; courriers de suivi sans réponse ; ancienneté "
          "des dernières observations finales), avec leurs notes. Ils remplacent les blocs « à compléter à la "
          "main ».").pack(side="left")

    def calculer_apercu():
        iso = iso_choisi()
        if not iso:
            messagebox.showerror("Pays", "Choisissez un pays dans la liste.")
            return None
        import conditionnels as K
        nom_fr = next((fr for i, fr, en in pays if i == iso), iso)
        var = BB.variables_pays(v_de.get().strip(), nom_fr, v_dem.get().strip(), personne())
        try:
            res, alertes = K.paragraphes(dossier_pays(), sources_redaction(), var)
        except Exception as e:
            messagebox.showerror("Paragraphes calculés", str(e))
            return None
        return res, alertes, K.lecture(), nom_fr

    def exporter_apercu(parent=None):
        r_ = calculer_apercu()
        if not r_:
            return
        res, alertes, lect, nom_fr = r_
        el = []
        if alertes:
            el.append((1, "Données manquantes", False))
            el += [(0, a_, True) for a_ in alertes]
        el.append((1, "Paragraphes calculés", False))
        el.append((0, "Chaque paragraphe peut être copié dans votre texte : ses repères [[…]] deviendront des notes "
                      "à la génération.", True))
        for rub, ps in res:
            el.append((2, rub, False))
            el += [(0, p_, False) for p_ in ps]
        el.append((1, "Ce que le programme a lu", False))
        el += [(0, l_[2:] if l_.startswith("- ") else l_, True) for l_ in lect if not l_.startswith("## ")]
        chemin = os.path.join(dossier_redaction(), "Apercu_paragraphes_calcules_%s.odt" % dt.date.today().isoformat())
        try:
            RD.odt_simple(chemin, el, "Paragraphes calculés – %s" % nom_fr)
        except Exception as e:
            messagebox.showerror("Exporter", "Export impossible : %s" % e, parent=parent)
            return
        ecrire("Aperçu exporté : %s" % chemin)
        messagebox.showinfo("Exporter l’aperçu", "L’aperçu est enregistré dans le dossier « Redaction » du pays :\n%s"
                            "\n\nIl s’ouvre dans LibreOffice." % os.path.basename(chemin), parent=parent)
        ouvrir(chemin)

    def corriger_dates():
        import conditionnels as K
        if not iso_choisi():
            messagebox.showerror("Pays", "Choisissez un pays dans la liste.")
            return
        chemin = os.path.join(dossier_pays(), "01_ONU_organes_de_traites", K.MANUEL)
        try:
            r_ = calculer_apercu()
            K.modele_rapports(chemin, K.DERNIER)
        except Exception as e:
            messagebox.showerror("Dates des rapports", str(e))
            return
        fenetre_info(root, "Corriger les dates des rapports", AIDE["dates_rapports"] % {"fichier": chemin},
                     bouton=("Ouvrir le fichier", lambda: ouvrir(chemin)))

    def apercu_calcules():
        r_ = calculer_apercu()
        if not r_:
            return
        res, alertes, lect, nom_fr = r_
        import conditionnels as K
        lignes = []
        if alertes:
            lignes.append("## Données manquantes")
            lignes += ["- " + a_ for a_ in alertes]
        for rub, ps in res:
            lignes.append("## " + rub)
            lignes += ps
            lignes.append("")
        lignes.append("")
        lignes += lect
        if not res:
            lignes.append("Aucun paragraphe : lancez d’abord la collecte ONU (ratifications, base des organes de "
                          "traités) pour ce pays.")
        w_ = fenetre_info(root, "Aperçu des paragraphes calculés", "\n".join(lignes),
                          bouton=("Corriger les dates…", corriger_dates))
        bas_ = w_.bas
        ttk.Button(bas_, text="Exporter (LibreOffice)", command=lambda: exporter_apercu(w_)).pack(side="right", padx=6)
    bulle(ttk.Button(fcalc, text="Aperçu…", command=apercu_calcules),
          "Montre les paragraphes qui seront ajoutés, sans créer le plan.").pack(side="left", padx=6)
    bulle(ttk.Button(fcalc, text="Exporter…", command=exporter_apercu),
          "Enregistre l’aperçu dans un document LibreOffice (dossier « Redaction » du pays) : paragraphes avec "
          "leurs repères, prêts à copier, et ce que le programme a lu.").pack(side="left")
    bulle(ttk.Button(fcalc, text="Corriger les dates…", command=corriger_dates),
          "Si une date de rapport est fausse ou manque : fichier à compléter, avec le mode d’emploi.").pack(
        side="left", padx=6)
    bulle(ttk.Button(f_r1, text="Créer le plan et l’ouvrir", command=creer_plan),
          "Crée un document LibreOffice avec les titres de la procédure, des indications de rédaction et, sous chaque "
          "titre, les repères des sources déjà collectées. Enregistré dans le dossier « Redaction » du pays.").grid(
        row=9, column=0, columnspan=2, sticky="w", pady=(8, 0))

    # 3. Notes et annexes
    f_r3 = cadre(gauche6, "3. Générer les notes et les annexes", 1, 0, pady=(6, 0))
    etat["texte_odt"] = cfg.get("red_texte", "")
    l_txt = ttk.Label(f_r3, text=os.path.basename(etat["texte_odt"]) or "Aucun texte choisi", foreground="#08738f")

    def choisir_texte():
        f_ = filedialog.askopenfilename(title="Texte à traiter", initialdir=dossier_redaction(),
                                        filetypes=[("Documents LibreOffice", "*.odt")])
        if f_:
            etat["texte_odt"] = f_
            l_txt["text"] = os.path.basename(f_)
            cfg["red_texte"] = f_
            sauver_config(cfg)
    bulle(ttk.Button(f_r3, text="Choisir le texte (.odt)…", command=choisir_texte),
          "Votre texte avec les repères [[…]]. L’original n’est jamais modifié : le résultat est un nouveau fichier "
          "« …_notes.odt ».").grid(row=0, column=0, sticky="w")
    l_txt.grid(row=0, column=1, sticky="w", padx=8)
    v_rpdf = tk.BooleanVar(value=cfg.get("red_pdf", True))
    v_rtamp = tk.BooleanVar(value=cfg.get("red_tampon", True))
    v_rtout = tk.BooleanVar(value=cfg.get("red_tout_annexer", True))
    bulle(ttk.Checkbutton(f_r3, text="Annexer toutes les sources citées", variable=v_rtout),
          "Coché : chaque document cité dont on a le fichier (observations finales, rapports, pièces…) devient une "
          "annexe, citée sans lien avec « voir l’annexe n° X ». Les pages web sans fichier (état des traités, état des "
          "rapports) gardent leur lien ; les lois, conventions et arrêts ne sont pas annexés. Exceptions : "
          "[[repère +sansannexe]] ou « non » dans la colonne annexe de sources.csv. Décoché : seules les sources "
          "marquées dans la colonne annexe, ou avec +annexe, sont annexées.").grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
    bulle(ttk.Checkbutton(f_r3, text="Assembler le PDF des annexes", variable=v_rpdf),
          "Un seul PDF, dans l’ordre des annexes, avec une page « Annexe n° X » avant chacune. Les fichiers Word ou "
          "ODT sont convertis avec LibreOffice.").grid(row=2, column=0, columnspan=2, sticky="w")
    bulle(ttk.Checkbutton(f_r3, text="Numéroter chaque page (« Annexe n° X – p. 1/5 »)", variable=v_rtamp),
          "Ajoute en haut à droite de chaque page le numéro de l’annexe et de la page.").grid(
        row=3, column=0, columnspan=2, sticky="w")

    def generer_notes():
        chemin = etat.get("texte_odt", "")
        if not chemin or not os.path.exists(chemin):
            messagebox.showerror("Texte", "Choisissez d’abord le texte à traiter (.odt).")
            return
        cfg["red_pdf"], cfg["red_tampon"] = v_rpdf.get(), v_rtamp.get()
        cfg["red_tout_annexer"] = v_rtout.get()
        sauver_config(cfg)
        srcs = sources_redaction()
        log.delete("1.0", "end")
        ecrire("=== Rédaction : notes et annexes ===")
        ecrire("  %d source(s) disponible(s)" % len(srcs))
        bib_, pers_, tout_ = biblio(), personne(), v_rtout.get()

        def run():
            try:
                iso_ = iso_choisi() or ""
                nom_fr_ = next((fr for i, fr, en in pays if i == iso_), iso_)
                res = RD.generer(chemin, srcs, dossier_redaction(), v_rpdf.get(), v_rtamp.get(), log=ecrire,
                                 bibliotheque=bib_,
                                 variables=BB.variables_pays(v_de.get().strip(), nom_fr_, v_dem.get().strip(), pers_),
                                 tout_annexer=tout_)
                for pb in res.problemes:
                    ecrire("  ! " + pb)
                q.put(("redaction", res))
            except Exception as e:
                ecrire("ERREUR : %s" % e)
        threading.Thread(target=run, daemon=True).start()
    bulle(ttk.Button(f_r3, text="Générer", command=generer_notes),
          "Remplace chaque repère par une note (référence complète, puis op.cit., Ibid.), numérote les annexes, "
          "écrit leur index et assemble le PDF.").grid(row=4, column=0, sticky="w", pady=(6, 0))
    f_aide6 = ttk.Frame(gauche6)
    f_aide6.grid(row=2, column=0, sticky="w", pady=(8, 0))
    bulle(ttk.Button(f_aide6, text="Comment écrire une note ? (repères, pages, abréviations)",
                     command=lambda: fenetre_info(root, "Écrire les notes : repères et abréviations", AIDE["reperes"])),
          "Exemples de repères avec paragraphes, pages, articles, options, et la liste complète des abréviations.").pack(
        anchor="w")
    bulle(ttk.Button(f_aide6, text="Liste des repères et des annexes…", command=lambda: fenetre_reperes()),
          "Tous les repères à coller dans le texte, avec ce que la note citera et si la source sera annexée ; "
          "annexer ou non, corriger, ajouter une source.").pack(anchor="w", pady=(4, 0))
    ttk.Label(f_aide6, text="[[cote, §24, p.8]]  [[LOI1980, art. 74/13]]  [[A ; B]]  [[… +trad]]  [[BLOC nom]]",
              foreground=GRIS).pack(anchor="w", pady=(4, 0))

    def arbre_reperes(tree, lst, filtre_txt):
        """Remplit un Treeview : une branche par catégorie (ouverte), une ligne par source. Renvoie {iid: source}."""
        tree.delete(*tree.get_children())
        mots = norm(filtre_txt).split()
        groupes = {}
        for s_ in lst:
            texte_ = RD.entree_index(s_) + " " + s_.get("id", "") + " " + (s_.get("titre") or "")
            if mots and not all(m_ in norm(texte_) for m_ in mots):
                continue
            groupes.setdefault(RD.categorie_affichee(s_), []).append(s_)
        corr = {}
        tree.tag_configure("cat", font=("Arial", 10, "bold"), background="#e6f0f0")
        for cat in sorted(groupes, key=RD.cle_tri_categorie):
            parent = tree.insert("", "end", text="", open=True, tags=("cat",),
                                 values=("%s (%d)" % (cat, len(groupes[cat])), "", ""))
            for s_ in groupes[cat]:
                iid = tree.insert(parent, "end", values=("[[%s]]" % RD.repere(s_, lst),
                                                         RD.annexe_prevue(s_, cfg.get("red_tout_annexer", True)),
                                                         RD.description_courte(s_)))
                corr[iid] = s_
        return corr

    # 2. Repères
    f_r2 = cadre(droite6, "2. Trouver un repère (double-clic = copier)", 0, 0)
    f_r2.columnconfigure(0, weight=1)
    v_cher = tk.StringVar()
    e_cher = bulle(ttk.Entry(f_r2, textvariable=v_cher), "Tapez un mot : comité, organisation, cote, année…")
    e_cher.grid(row=0, column=0, sticky="we")
    tv = ttk.Treeview(f_r2, columns=("rep", "ann", "ref"), show="tree headings", height=11)
    tv.heading("#0", text="")
    tv.heading("rep", text="Repère à coller")
    tv.heading("ann", text="Annexe")
    tv.heading("ref", text="Document")
    tv.column("#0", width=28, stretch=False)
    tv.column("rep", width=170, stretch=False)
    tv.column("ann", width=55, stretch=False, anchor="center")
    tv.column("ref", width=260)
    tv.grid(row=1, column=0, sticky="we", pady=(4, 0))
    sbt = ttk.Scrollbar(f_r2, orient="vertical", command=tv.yview)
    sbt.grid(row=1, column=1, sticky="ns", pady=(4, 0))
    tv.configure(yscrollcommand=sbt.set)
    l_copie = ttk.Label(f_r2, text="", foreground="#08738f", wraplength=880, justify="left")
    l_copie.grid(row=2, column=0, sticky="w")
    cache_src = []
    corr_tv = {}

    def remplir_liste(*_):
        if not cache_src:
            cache_src.extend(sources_redaction())
            iso_ = iso_choisi() or "?"
            nom_ = next((fr for i, fr, en in pays if i == iso_), iso_)
            n_pays = sum(1 for x in cache_src if os.path.normpath(x.get("_racine", "")) == os.path.normpath(dossier_pays())
                         or x.get("categorie") == "Pièces du dossier")
            f_r2["text"] = "2. Repères – %s (%d sources du pays)" % (nom_, n_pays)
        corr_tv.clear()
        corr_tv.update(arbre_reperes(tv, cache_src, v_cher.get()))

    def actualiser():
        cache_src.clear()
        remplir_liste()

    def copier(_e=None):
        sel = tv.selection()
        if not sel or sel[0] not in corr_tv:
            return
        rep = tv.item(sel[0], "values")[0]
        root.clipboard_clear()
        root.clipboard_append(rep)
        l_copie["text"] = "Copié : %s — collez-le dans le texte (Ctrl+V)" % rep

    def detail(_e=None):
        sel = tv.selection()
        if sel and sel[0] in corr_tv:
            l_copie["text"] = "Note : " + RD.entree_index(corr_tv[sel[0]])
    tv.bind("<<TreeviewSelect>>", detail)
    tv.bind("<Double-1>", copier)
    v_cher.trace_add("write", remplir_liste)
    attente = {"id": None, "iso": iso_choisi()}

    def pays_change(*_):
        """Changement de pays ou de dossier de base : la liste des repères suit."""
        if attente["id"]:
            root.after_cancel(attente["id"])

        def go():
            attente["id"] = None
            iso_ = iso_choisi()
            if iso_:
                if attente.get("iso") and attente["iso"] != iso_:
                    maj_pays()  # « Dans une phrase », veille… suivent aussi quand le pays est tapé au clavier
                attente["iso"] = iso_
                cache_src.clear()
                l_copie["text"] = ""
                remplir_liste()
        attente["id"] = root.after(500, go)
    v_pays.trace_add("write", pays_change)
    v_dossier.trace_add("write", pays_change)
    fb6 = ttk.Frame(f_r2)
    fb6.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
    bulle(ttk.Button(fb6, text="Actualiser", command=actualiser),
          "Relit les sources du pays choisi en haut (la liste suit aussi automatiquement le changement de pays).").pack(
        side="left")
    bulle(ttk.Button(fb6, text="Liste complète", command=lambda: ouvrir(RD.liste_html(
        sources_redaction(), os.path.join(dossier_redaction(), "reperes.html")))),
          "Page web avec toutes les sources et leur repère.").pack(side="left", padx=4)

    def ouvrir_pieces():
        d = os.path.join(dossier_pays(), RD.DOSSIER_PIECES)
        os.makedirs(d, exist_ok=True)
        ouvrir(d)
    bulle(ttk.Button(fb6, text="Pièces du dossier", command=ouvrir_pieces),
          "Dossier où déposer les pièces personnelles (attestations, passeports…) : elles deviennent des repères "
          "[[PIECE nom]] et sont mises en annexe. Préfixez-les d’un numéro pour l’ordre (01_…).").pack(side="left")
    bulle(ttk.Button(fb6, text="Gérer…", command=lambda: fenetre_reperes()),
          "Annexer ou non une source, corriger sa référence, ajouter un document qui n’a pas été collecté.").pack(
        side="left", padx=4)

    def fenetre_reperes():
        w = tk.Toplevel(root)
        w.title("Repères, sources et annexes")
        w.transient(root)
        w.geometry("1080x620")
        c = ttk.Frame(w, padding=12)
        c.pack(fill="both", expand=True)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(2, weight=1)
        ttk.Label(c, wraplength=1040, justify="left", text=(
            "Chaque ligne est une source que vous pouvez citer. Copiez son repère (double-clic ou « Copier ») et "
            "collez-le dans votre texte à l’endroit de la note, en ajoutant la précision après une virgule : "
            "[[CCPR/C/IDN/CO/2, §24, p.8]]. Colonne « Annexe » : oui = jointe au courrier et citée « voir l’annexe "
            "n° X » ; non = citée avec son lien ; loi = texte de référence (jamais annexé). Les sources sont rangées par "
            "catégorie ; cliquez sur une ligne pour voir, en bas, la référence complète que la note citera.")).grid(
            row=0, column=0, columnspan=2, sticky="w")
        v_f = tk.StringVar()
        bulle(ttk.Entry(c, textvariable=v_f), "Filtrer : comité, organisation, cote, année…").grid(
            row=1, column=0, sticky="we", pady=(8, 4))
        t = ttk.Treeview(c, columns=("rep", "ann", "ref"), show="tree headings", selectmode="browse")
        t.heading("#0", text="")
        t.column("#0", width=40, stretch=False)
        for col, lib, lg in (("rep", "Repère à coller", 220), ("ann", "Annexe", 70), ("ref", "Document", 700)):
            t.heading(col, text=lib)
            t.column(col, width=lg, stretch=(col == "ref"), anchor="center" if col == "ann" else "w")
        t.grid(row=2, column=0, sticky="nsew")
        sb_ = ttk.Scrollbar(c, orient="vertical", command=t.yview)
        sb_.grid(row=2, column=1, sticky="ns")
        t.configure(yscrollcommand=sb_.set)
        msg = ttk.Label(c, text="", foreground="#08738f", wraplength=1040, justify="left")
        msg.grid(row=3, column=0, sticky="w", pady=(4, 0))
        srcs = {}

        def remplir(*_):
            srcs.clear()
            srcs.update(arbre_reperes(t, sources_redaction(), v_f.get()))

        def choisie():
            sel = t.selection()
            if not sel or sel[0] not in srcs:
                messagebox.showinfo("Repères", "Cliquez d’abord sur une ligne (pas sur un titre de catégorie).",
                                    parent=w)
                return None
            return srcs[sel[0]]

        def detail_(_e=None):
            sel = t.selection()
            if sel and sel[0] in srcs:
                msg["text"] = "La note citera : " + RD.entree_index(srcs[sel[0]])
        t.bind("<<TreeviewSelect>>", detail_)

        def copier_(_e=None):
            s_ = choisie()
            if s_:
                rep = t.item(t.selection()[0], "values")[0]
                root.clipboard_clear()
                root.clipboard_append(rep)
                msg["text"] = "Copié : %s — collez-le dans le texte (Ctrl+V)" % rep

        def annexer(val):
            s_ = choisie()
            if not s_:
                return
            if s_.get("_lex"):
                messagebox.showinfo("Annexe", "Les lois, conventions et arrêts des textes de référence ne sont pas "
                                    "annexés. Pour en joindre un exceptionnellement, ajoutez +annexe dans le repère : "
                                    "[[%s +annexe]]." % s_["_repere"], parent=w)
                return
            if val == "oui" and not s_.get("fichier"):
                if not messagebox.askyesno("Annexe", "Cette source n’a pas de fichier (page web) : elle sera annoncée "
                                           "comme annexe, mais il faudra joindre le document vous-même. Continuer ?",
                                           parent=w):
                    return
            err = RD.modifier_source(s_, {"annexe": val})
            if err:
                messagebox.showerror("Annexe", err, parent=w)
                return
            msg["text"] = "Annexe : %s pour %s" % (val, RD.repere(s_))
            remplir()
            actualiser()

        def formulaire(s_=None):
            if s_ is not None and s_.get("_lex"):
                formulaire_reference(w, s_["_repere"])
                return
            f = tk.Toplevel(w)
            f.title("Modifier la source" if s_ else "Ajouter une source")
            f.transient(w)
            cc = ttk.Frame(f, padding=12)
            cc.pack(fill="both", expand=True)
            champs = [("auteur", "Auteur", "ex. Amnesty International ; ONU, Comité contre la torture"),
                      ("titre", "Titre", "ex. Rapport annuel 2025 – Indonésie (obligatoire)"),
                      ("cote", "Cote", "ex. CAT/C/IDN/CO/3 (facultatif)"),
                      ("date", "Date", "ex. 3 mai 2024"),
                      ("url", "Lien", "si le document est en ligne"),
                      ("consulte_le", "Consulté le", "ex. 28 septembre 2026 (si lien)")]
            vs = {}
            for i, (k, lib, ex) in enumerate(champs):
                ttk.Label(cc, text=lib + " :").grid(row=2 * i, column=0, sticky="w", pady=(6 if i else 0, 0))
                vs[k] = tk.StringVar(value=(s_ or {}).get(k, ""))
                ttk.Entry(cc, textvariable=vs[k], width=80).grid(row=2 * i, column=1, sticky="we", padx=6,
                                                                pady=(6 if i else 0, 0))
                ttk.Label(cc, text=ex, foreground=GRIS).grid(row=2 * i + 1, column=1, sticky="w", padx=6)
            n = len(champs)
            ttk.Label(cc, text="Annexe :").grid(row=2 * n, column=0, sticky="w", pady=(8, 0))
            v_a = tk.StringVar(value=(s_ or {}).get("annexe", "") or ("oui" if s_ is None else ""))
            fa = ttk.Frame(cc)
            fa.grid(row=2 * n, column=1, sticky="w", padx=6, pady=(8, 0))
            for val, lib in (("oui", "oui"), ("non", "non (citée avec son lien)"), ("", "automatique")):
                ttk.Radiobutton(fa, text=lib, value=val, variable=v_a).pack(side="left", padx=(0, 10))
            v_fich = tk.StringVar()
            if s_ is None:
                ttk.Label(cc, text="Fichier :").grid(row=2 * n + 1, column=0, sticky="w", pady=(8, 0))
                ff = ttk.Frame(cc)
                ff.grid(row=2 * n + 1, column=1, sticky="w", padx=6, pady=(8, 0))
                l_f = ttk.Label(ff, text="aucun (facultatif : PDF, Word…)", foreground=GRIS)

                def choisir_f():
                    p = filedialog.askopenfilename(parent=f, title="Document à joindre")
                    if p:
                        v_fich.set(p)
                        l_f["text"] = os.path.basename(p)
                ttk.Button(ff, text="Choisir…", command=choisir_f).pack(side="left")
                l_f.pack(side="left", padx=6)

            def ok():
                ch = {k: v.get().strip() for k, v in vs.items()}
                ch["annexe"] = v_a.get()
                if s_ is None:
                    id_, err = RD.ajouter_source(dossier_pays(), ch, v_fich.get() or None)
                else:
                    err = RD.modifier_source(s_, ch)
                if err:
                    messagebox.showerror("Source", err, parent=f)
                    return
                f.destroy()
                remplir()
                actualiser()
                msg["text"] = "Source enregistrée."
            bb = ttk.Frame(cc)
            bb.grid(row=2 * n + 2, column=0, columnspan=2, sticky="e", pady=(12, 0))
            ttk.Button(bb, text="Annuler", command=f.destroy).pack(side="right")
            ttk.Button(bb, text="Enregistrer", command=ok).pack(side="right", padx=4)
            f.grab_set()

        def supprimer_():
            s_ = choisie()
            if not s_:
                return
            if s_.get("_lex"):
                formulaire_reference(w, s_["_repere"])
                return
            if not messagebox.askyesno("Supprimer", "Retirer %s de la liste ?" % RD.repere(s_), parent=w):
                return
            err = RD.supprimer_source(s_)
            if err:
                messagebox.showinfo("Supprimer", err, parent=w)
                return
            remplir()
            actualiser()
        t.bind("<Double-1>", lambda e: copier_() if t.selection() and t.selection()[0] in srcs else None)
        v_f.trace_add("write", remplir)
        bas = ttk.Frame(c)
        bas.grid(row=4, column=0, columnspan=2, sticky="we", pady=(8, 0))
        for lib, fn, aide_ in (
                ("Copier le repère", copier_, "Copie [[repère]] : collez-le dans le texte (Ctrl+V)."),
                ("Annexer", lambda: annexer("oui"), "Cette source sera jointe au courrier (« voir l’annexe n° X »)."),
                ("Ne pas annexer", lambda: annexer("non"), "Cette source sera citée avec son lien, sans annexe."),
                ("Modifier…", lambda: (lambda s_: s_ and formulaire(s_))(choisie()),
                 "Corriger l’auteur, le titre, la date, le lien… de la source choisie."),
                ("Ajouter une source…", lambda: formulaire(None),
                 "Un document qui n’a pas été collecté (rapport d’ONG, article, décision…), avec son fichier."),
                ("Supprimer", supprimer_, "Seulement pour une source que vous avez ajoutée vous-même."),
                ("Actualiser", remplir, "Relit les sources (après une collecte ou un import).")):
            bulle(ttk.Button(bas, text=lib, command=fn), aide_).pack(side="left", padx=(0, 4))
        ttk.Button(bas, text="Fermer", command=w.destroy).pack(side="right")
        remplir()
    nb.bind("<<NotebookTabChanged>>", lambda e: nb.index(nb.select()) == nb.index(t6) and not cache_src and remplir_liste(),
            add="+")

    def popup_redaction(res):
        w = tk.Toplevel(root)
        w.title("Notes et annexes générées")
        w.transient(root)
        f_ = ttk.Frame(w, padding=14)
        f_.pack(fill="both", expand=True)
        ttk.Label(f_, text="%d note(s) créée(s), %d annexe(s)." % (res.notes, len(res.annexes)),
                  font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(f_, text=("%d point(s) à vérifier : voir le rapport." % len(res.problemes)) if res.problemes
                  else "Aucun problème relevé.", foreground="#b00020" if res.problemes else "#08738f").pack(anchor="w", pady=(4, 8))
        b_ = ttk.Frame(f_)
        b_.pack(fill="x")
        ttk.Button(b_, text="Ouvrir le texte avec notes", command=lambda: ouvrir(res.odt)).pack(side="left")
        if res.pdf:
            ttk.Button(b_, text="Ouvrir le PDF des annexes", command=lambda: ouvrir(res.pdf)).pack(side="left", padx=4)
        ttk.Button(b_, text="Ouvrir le rapport", command=lambda: ouvrir(res.rapport)).pack(side="left")
        ttk.Button(b_, text="Fermer", command=w.destroy).pack(side="right")

    # --- boutons « mode d'emploi » de chaque onglet ------------------------
    titres_aide = {"onu": "Mode d’emploi – ONU", "reliefweb": "Mode d’emploi – ReliefWeb",
                   "veille": "Mode d’emploi – Veille presse et sources nationales",
                   "jurisprudence": "Mode d’emploi – Jurisprudence", "importer": "Mode d’emploi – Importer",
                   "redaction": "Mode d’emploi – Rédaction"}
    for t_, cle_ in ((t1, "onu"), (t2, "reliefweb"), (t3, "veille"), (t5, "jurisprudence"), (t4, "importer"),
                     (t6, "redaction")):
        ttk.Button(t_, text="Mode d’emploi de l’onglet", command=lambda c=cle_: fenetre_info(root, titres_aide[c], AIDE[c])).place(
            relx=1.0, x=-2, y=0, anchor="ne")

    # --- actions ----------------------------------------------------------
    act0 = ttk.Frame(main)
    act0.pack(fill="x", pady=(4, 0))
    act = ttk.Frame(main)
    act.pack(fill="x", pady=4)
    v_maj = tk.BooleanVar(value=cfg.get("maj", True))
    bulle(ttk.Checkbutton(act0, text="Nouveautés seulement", variable=v_maj),
          "Plus rapide : ne cherche que ce qui est paru depuis la dernière collecte. Rien n’est jamais retéléchargé, "
          "même sans cette option.").pack(side="left")
    v_liens = tk.BooleanVar(value=cfg.get("liens_seulement", False))
    bulle(ttk.Checkbutton(act0, text="Liens seulement (ne rien télécharger)", variable=v_liens),
          "Crée les fiches et une page « liens_a_telecharger » à ouvrir vous-même, sans rien télécharger.").pack(side="left", padx=8)
    ttk.Label(act0, text="Depuis l’année (ReliefWeb, presse) :").pack(side="left")
    v_depuis = tk.IntVar(value=cfg.get("depuis", dt.date.today().year - 3))
    ttk.Spinbox(act0, from_=1990, to=dt.date.today().year, textvariable=v_depuis, width=6).pack(side="left")
    b_go = bulle(ttk.Button(act, text="Lancer la collecte"), "Lance tout ce qui est coché dans les onglets.")
    b_go.pack(side="right", padx=4)
    b_stop = bulle(ttk.Button(act, text="Arrêter", state="disabled", command=lambda: stop.set()),
                   "Interrompt proprement : ce qui est déjà téléchargé est conservé.")
    b_stop.pack(side="right", padx=4)

    def dossier_pays():
        iso, d = iso_choisi(), v_dossier.get()
        for i, fr, en in pays:
            if i == iso:
                d = os.path.join(d, "%s (%s)" % (fr, i))
        os.makedirs(d, exist_ok=True)
        return d
    ttk.Button(act, text="Ouvrir le dossier", command=lambda: ouvrir(dossier_pays())).pack(side="right", padx=4)
    b_journal = ttk.Button(act, text="Ouvrir le journal", state="disabled",
                           command=lambda: etat["journal"] and ouvrir(etat["journal"]))
    b_journal.pack(side="right", padx=4)

    GARDER = ("dossier", "country_ids", "veille_par_pays", "appname", "pays_libelle", "de_pays", "aide_vue")

    def reinitialiser():
        if str(b_go["state"]) == "disabled":
            messagebox.showinfo("Tout réinitialiser", "Attendez la fin de la collecte (ou cliquez sur « Arrêter »).")
            return
        if not messagebox.askyesno(
                "Tout réinitialiser",
                "Remettre toutes les cases et tous les champs à leur valeur de départ ?\n\n"
                "Conservés : vos documents et sources.csv, le dossier de base, le pays choisi, les CountryID, "
                "le nom d’application ReliefWeb et vos listes de veille par pays.\n\n"
                "La fenêtre va se rouvrir."):
            return
        for k in list(cfg):
            if k not in GARDER:
                del cfg[k]
        sauver_config(cfg)
        etat["relancer"] = True
        root.destroy()
    bulle(ttk.Button(act, text="Tout réinitialiser", command=reinitialiser),
          "Remet toutes les cases et tous les champs à leur valeur de départ (vos documents ne sont pas touchés).").pack(
        side="left", padx=4)

    pb = ttk.Progressbar(main, mode="determinate")
    pb.pack(fill="x")
    log = tk.Text(main, height=12, wrap="word")
    log.pack(fill="both", expand=True, pady=(4, 0))

    def ecrire(msg):
        q.put(("log", msg))

    def progres(k, n):
        q.put(("pb", (k, max(n, 1))))

    def boucle():
        try:
            while True:
                kind, val = q.get_nowait()
                if kind == "log":
                    log.insert("end", val + "\n")
                    log.see("end")
                elif kind == "pb":
                    pb["maximum"], pb["value"] = val[1], val[0]
                elif kind == "cid":
                    popup_country_id(val)
                elif kind == "redaction":
                    popup_redaction(val)
                elif kind == "fin":
                    b_go["state"], b_stop["state"] = "normal", "disabled"
                    if val:
                        etat["journal"] = val
                        b_journal["state"] = "normal"
                    popup_fin(val)
        except queue.Empty:
            pass
        root.after(150, boucle)

    def popup_fin(journal):
        """Petit bilan à la fin de chaque collecte (désactivable)."""
        if cfg.get("popup_fin_off"):
            return
        n = "?"
        try:
            with open(journal, encoding="utf-8") as f:
                f.readline()
                n = f.readline().split()[0]
        except Exception:
            pass
        w = tk.Toplevel(root)
        w.title("Collecte terminée")
        w.transient(root)
        f = ttk.Frame(w, padding=14)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Collecte terminée : %s nouveau(x) document(s)." % n, font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(f, text="• Les documents sont rangés dans le dossier du pays, par catégorie (01_…, 02_…).\n"
                          "• sources.csv décrit chaque document (auteur, titre, date, lien, date de consultation).\n"
                          "• Le journal liste les nouveautés de ce lancement.\n"
                          "• S’il existe un fichier « liens_a_telecharger_… .html », il contient des documents\n"
                          "   à ouvrir et télécharger vous-même (sites qui refusent les programmes).\n"
                          "• Les messages en bas de la fenêtre détaillent ce qui a été fait ou écarté.",
                  justify="left").pack(anchor="w", pady=(8, 8))
        v_off = tk.BooleanVar(value=False)
        bas = ttk.Frame(f)
        bas.pack(fill="x")
        ttk.Checkbutton(bas, text="Ne plus afficher ce bilan", variable=v_off).pack(side="left")

        def fermer():
            if v_off.get():
                cfg["popup_fin_off"] = True
                sauver_config(cfg)
            w.destroy()
        ttk.Button(bas, text="Fermer", command=fermer).pack(side="right")
        ttk.Button(bas, text="Ouvrir le journal", command=lambda: journal and ouvrir(journal)).pack(side="right", padx=4)
        ttk.Button(bas, text="Ouvrir le dossier", command=lambda: ouvrir(dossier_pays())).pack(side="right")
        w.protocol("WM_DELETE_WINDOW", fermer)

    def popup_country_id(iso):
        w = tk.Toplevel(root)
        w.title("Identifiant OHCHR du pays introuvable")
        w.transient(root)
        f = ttk.Frame(w, padding=14)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Le programme n’a pas trouvé l’identifiant du pays au HCDH (« CountryID »).\n"
                          "Il sert à récupérer l’état des rapports, les courriers de suivi et le tableau\n"
                          "des plaintes individuelles. Marche à suivre (une seule fois par pays) :",
                  justify="left").pack(anchor="w")
        etapes = ("1. Ouvrez la page « état des ratifications » du HCDH (bouton ci-dessous).\n"
                  "2. Choisissez le pays dans la liste : la page du pays s’affiche.\n"
                  "3. Dans l’adresse de cette page, repérez « CountryID= » suivi d’un nombre\n"
                  "    (ex. …/Treaty.aspx?CountryID=80&Lang=en pour l’Indonésie).\n"
                  "4. Collez ce nombre ci-dessous (ou dans le champ « CountryID OHCHR » de l’onglet ONU).")
        ttk.Label(f, text=etapes, justify="left").pack(anchor="w", pady=(8, 8))
        url = TB_TRAITES_LISTE
        ttk.Button(f, text="Ouvrir la page « état des ratifications » du HCDH", command=lambda: webbrowser.open(url)).pack(anchor="w")
        l = ttk.Label(f, text=url, foreground="#08738f", cursor="hand2")
        l.pack(anchor="w", pady=(2, 8))
        l.bind("<Button-1>", lambda e: webbrowser.open(url))
        fe = ttk.Frame(f)
        fe.pack(anchor="w")
        ttk.Label(fe, text="CountryID :").pack(side="left")
        v = tk.StringVar()
        ttk.Entry(fe, textvariable=v, width=10).pack(side="left", padx=4)

        def ok():
            n = re.sub(r"\D", "", v.get())
            if n:
                v_cid.set(n)
                cfg.setdefault("country_ids", {})[iso] = n
                sauver_config(cfg)
                ecrire("CountryID %s enregistré pour ce pays : relancez la collecte pour en profiter." % n)
            w.destroy()
        ttk.Button(fe, text="Enregistrer", command=ok).pack(side="left", padx=4)
        ttk.Button(fe, text="Plus tard", command=w.destroy).pack(side="left")

    def lancer():
        iso = iso_choisi()
        if not iso:
            messagebox.showerror("Pays", "Choisissez un pays dans la liste.")
            return
        lignes = lambda t: [s.strip() for s in t.get("1.0", "end").splitlines() if s.strip()]
        veille_cfg[iso] = {"flux": lignes(t_flux), "recherches": lignes(t_rech), "filtre": v_filtre.get().split(),
                           "flux_rw": lignes(t_rwflux)}
        cfg.setdefault("country_ids", {})[iso] = v_cid.get().strip()
        p = {
            "iso": iso, "de_pays": v_de.get().strip(), "dossier": v_dossier.get(),
            "comites": [c for c, v in v_com.items() if v.get()],
            "types": [t for t, v in v_typ.items() if v.get()] if v_org.get() else [],
            "organes_actif": v_org.get(), "epu_resultats": v_epu_res.get(),
            "base_organes": v_base.get(), "country_id": v_cid.get().strip(), "epu": v_epu.get(),
            "base_tous": v_btous.get(), "base_communs": v_bcom.get(), "base_sans_sr": v_bsr.get(),
            "ratifications": v_ratif.get(), "ratif_chapitres": v_chap.get(), "reliefweb": v_rw.get(),
            "ratif_selection": list(ratif_sel),
            "sources": [n for n, (v, l) in v_srcs.items() if v.get()], "theme": v_theme.get().strip(), "mots": v_mots.get().strip(),
            "langues": [l for l, v in (("fr", v_fr), ("en", v_en)) if v.get()],
            "appname": v_app.get().strip(), "depuis": v_depuis.get(), "max_docs": v_max.get(),
            "flux_reliefweb": lignes(t_rwflux),
            "veille": v_veille.get(), "flux": lignes(t_flux), "recherches": lignes(t_rech),
            "filtre_veille": v_filtre.get().split(), "hl": v_hl.get().strip() or "fr", "gl": v_gl.get().strip() or "BE",
            "importer_fichiers": list(etat["fichiers"]), "importer_liens": lignes(t_liens),
            "categorie_import": v_cat.get(), "maj": v_maj.get(), "liens_seulement": v_liens.get(),
            "jur_depuis": v_jdep.get(), "jur_max": v_jmax.get(),
            "jur_articles_hudoc": va_h.get(), "jur_mode_hudoc": vm_h.get(),
            "jur_articles_cjue": va_c.get(), "jur_mode_cjue": vm_c.get(), "jur_ref_cjue": vr_c.get().strip(),
            "jur_articles_cc": va_cc.get(), "jur_mode_cc": vm_cc.get(), "jur_ref_cc": vr_cc.get().strip(),
            "jur_hudoc": v_hud.get(), "jur_mots_hudoc": v_hmots.get().strip(), "jur_etat": v_etat.get().strip(),
            "jur_types": [t for t, v in (("JUDGMENTS", v_arr), ("DECISIONS", v_dec)) if v.get()],
            "jur_gc": v_gc.get(), "jur_langues": [l for l, v in (("FRE", v_hfr), ("ENG", v_hen)) if v.get()],
            "jur_cjue": v_cj.get(),
            "jur_actes": [c for c, v in v_actes.items() if v.get()] + [x.strip() for x in re.split(r"[,;\s]+", v_celex.get()) if x.strip()],
            "jur_celex_libre": v_celex.get(), "jur_mots_cjue": v_cmots.get().strip(),
            "jur_cc": v_cc.get(), "jur_cc_de": v_cc1.get(), "jur_cc_a": v_cc2.get(), "jur_mots_cc": v_ccmots.get().strip(),
            "jur_refs": lignes(t_refs), "jur_commun": v_commun.get(),
        }
        for k in ("organes_actif", "epu_resultats"):
            cfg[k] = p[k]
        cfg["types"] = [t for t, v in v_typ.items() if v.get()]
        for k in ("de_pays", "dossier", "comites", "base_organes", "base_tous", "base_communs", "base_sans_sr", "epu", "ratifications", "ratif_chapitres", "ratif_selection", "reliefweb",
                  "sources", "theme", "mots", "appname", "depuis", "max_docs", "veille", "hl", "gl", "maj",
                  "liens_seulement"):
            cfg[k] = p[k]
        cfg["pays_libelle"], cfg["preset"] = v_pays.get(), v_preset.get()
        for k, v in p.items():
            if k.startswith("jur_") and k != "jur_refs":
                cfg[k] = v
        sauver_config(cfg)
        stop.clear()
        b_go["state"], b_stop["state"] = "disabled", "normal"
        log.delete("1.0", "end")

        def run():
            j = None
            try:
                j = lancer_collecte(p, ecrire, progres, stop)
                if p.get("_country_id") and not v_cid.get().strip():
                    cfg.setdefault("country_ids", {})[iso] = p["_country_id"]
                    sauver_config(cfg)
                    root.after(0, lambda: v_cid.set(p["_country_id"]))
                if p.get("_country_id_manquant"):
                    q.put(("cid", iso))
            except Exception as e:
                ecrire("ERREUR : %s" % e)
            etat["fichiers"] = []
            q.put(("fin", j))
        threading.Thread(target=run, daemon=True).start()

    b_go["command"] = lancer
    maj_pays()
    v_de.set(cfg.get("de_pays", v_de.get()))
    boucle()
    if not cfg.get("aide_vue"):
        v_nplus = tk.BooleanVar(value=True)
        wb = fenetre_info(root, "Bienvenue", AIDE["bienvenue"], case_ne_plus=v_nplus,
                          bouton=("Lire l’aide générale", lambda: fenetre_info(root, "Aide générale", AIDE["general"])))

        def _vu(e):
            if e.widget is wb:
                cfg["aide_vue"] = v_nplus.get()
                sauver_config(cfg)
        wb.bind("<Destroy>", _vu)
    root.mainloop()
    if etat.get("relancer"):
        return interface()


# ---------------------------------------------------------------------------
# Ligne de commande
# ---------------------------------------------------------------------------
def cli(argv):
    cfg = charger_config()
    ap = argparse.ArgumentParser(description="Probasile : sources par pays et aide à la rédaction (droits humains / santé).")
    ap.add_argument("--pays", help="code ISO à 3 lettres (ex. IDN)")
    ap.add_argument("--dossier", default=cfg.get("dossier"), help="dossier de base (mémorisé)")
    ap.add_argument("--de-pays", help="forme « de l’Indonésie » utilisée dans les titres")
    ap.add_argument("--comites", default="CCPR,CAT,CESCR,CEDAW,CRC,CERD", help="ex. CCPR,CAT ou 'aucun'")
    ap.add_argument("--types", default="CO,Q,QPR", help="CO (observations finales), Q, QPR, R (rapports de l’État)")
    ap.add_argument("--base-organes", action="store_true", help="état des rapports, courriers de suivi, anciennes cotes")
    ap.add_argument("--country-id", default="", help="identifiant OHCHR du pays (facultatif)")
    ap.add_argument("--base-tous", action="store_true", help="base des organes : tous les comités (sinon ceux de --comites)")
    ap.add_argument("--base-sans-communs", action="store_true", help="base des organes : sans les documents communs")
    ap.add_argument("--sans-sr", action="store_true", help="base des organes : sans les comptes rendus de séance")
    ap.add_argument("--epu", action="store_true", help="Examen périodique universel")
    ap.add_argument("--ratifications", action="store_true", help="liste choisie (traites.csv), réserves et déclarations")
    ap.add_argument("--ratifications-chapitres", action="store_true", help="+ tous les traités des chapitres IV, V et XVIII")
    ap.add_argument("--traites", default="", help="ratifications : seulement ces numéros UNTC, ex. IV-4,IV-9")
    ap.add_argument("--reliefweb", action="store_true")
    ap.add_argument("--preset", choices=list(PRESETS), default=list(PRESETS)[0])
    ap.add_argument("--depuis", type=int, default=dt.date.today().year - 3)
    ap.add_argument("--mots", default="")
    ap.add_argument("--appname", default=cfg.get("appname", ""))
    ap.add_argument("--max-docs", type=int, default=300)
    ap.add_argument("--flux-reliefweb", nargs="*", default=None, help="flux RSS ReliefWeb de secours (sinon ceux mémorisés)")
    ap.add_argument("--veille", action="store_true", help="flux et recherches mémorisés pour ce pays dans l’interface")
    ap.add_argument("--flux", nargs="*", default=None, help="URL de flux RSS")
    ap.add_argument("--recherche", nargs="*", default=None, help="requêtes Google Actualités")
    ap.add_argument("--importer", nargs="*", default=[], help="fichiers à importer")
    ap.add_argument("--liens", help="fichier texte : un lien à importer par ligne")
    ap.add_argument("--categorie", default="Automatique", choices=CATEGORIES_IMPORT)
    ap.add_argument("--hudoc", action="store_true", help="jurisprudence de la Cour eur. D.H.")
    ap.add_argument("--cjue", nargs="*", default=None, help="C.J.U.E. : actes CELEX (ex. 32011L0095 32024R1347)")
    ap.add_argument("--cour-const", nargs=2, type=int, metavar=("DE", "A"), help="Cour constitutionnelle : années")
    ap.add_argument("--articles", default="", help="HUDOC : articles de la Convention, ex. '3, 13'")
    ap.add_argument("--articles-cjue", default="", help="C.J.U.E. : articles de l’acte, ex. '4, 9'")
    ap.add_argument("--articles-cc", default="", help="Cour constitutionnelle : articles, ex. '3'")
    ap.add_argument("--au-moins-un", action="store_true", help="au moins un des articles (par défaut : tous)")
    ap.add_argument("--reference", default="", help="texte de référence après l’article (ex. 'Convention européenne')")
    ap.add_argument("--mots-jur", default="", help="mots-clés pour la jurisprudence (ex. Indonesia)")
    ap.add_argument("--etat", default="", help="HUDOC : État défendeur (ex. BEL)")
    ap.add_argument("--refs", help="fichier texte : une référence d’arrêt par ligne")
    ap.add_argument("--jur-pays", action="store_true", help="ranger la jurisprudence dans le dossier du pays")
    ap.add_argument("--maj", action="store_true", help="nouveautés seulement")
    ap.add_argument("--liens-seulement", action="store_true", help="ne rien télécharger : page de liens")
    ap.add_argument("--liste-pays", action="store_true", help="affiche les codes pays")
    a = ap.parse_args(argv)
    if a.liste_pays:
        for iso, fr, en in liste_pays():
            print(iso, fr)
        return
    if not a.pays:
        ap.error("--pays est obligatoire (ou lancez sans argument pour l’interface)")
    iso = a.pays.upper()
    dossier = a.dossier or os.path.join(os.path.expanduser("~"), "Probasile")
    comites = [] if a.comites.lower() == "aucun" else [c.strip().upper() for c in a.comites.split(",") if c.strip()]
    inconnus = [c for c in comites if c not in COMITES]
    if inconnus:
        ap.error("comité(s) inconnu(s) : %s" % ", ".join(inconnus))
    vc = cfg.get("veille_par_pays", {}).get(iso, {})
    liens = []
    if a.liens:
        with open(a.liens, encoding="utf-8") as f:
            liens = [l.strip() for l in f if l.strip()]
    refs = []
    if a.refs:
        with open(a.refs, encoding="utf-8") as f:
            refs = [l.strip() for l in f if l.strip()]
    pr = PRESETS[a.preset]
    try:
        cat = Catalogue(dossier)
        src_cli = [l["nom_reliefweb"] for l in cat.reliefweb(pr["code"])] if pr["code"] else cfg.get("sources", [])
    except Exception:
        src_cli = cfg.get("sources", [])
    p = {"iso": iso, "dossier": dossier, "de_pays": a.de_pays, "comites": comites,
         "types": [t.strip().upper() for t in a.types.split(",") if t.strip()],
         "ratif_selection": [x.strip() for x in a.traites.split(",") if x.strip()],
         "base_organes": a.base_organes, "base_tous": a.base_tous, "base_communs": not a.base_sans_communs,
         "base_sans_sr": a.sans_sr, "country_id": a.country_id or cfg.get("country_ids", {}).get(iso, ""),
         "epu": a.epu, "ratifications": a.ratifications or a.ratifications_chapitres,
         "ratif_chapitres": a.ratifications_chapitres, "reliefweb": a.reliefweb,
         "sources": src_cli, "theme": pr["theme"], "mots": a.mots,
         "langues": ["fr", "en"], "appname": a.appname, "depuis": a.depuis, "max_docs": a.max_docs,
         "veille": a.veille or bool(a.flux or a.recherche),
         "flux": a.flux if a.flux is not None else vc.get("flux", []),
         "recherches": a.recherche if a.recherche is not None else vc.get("recherches", []),
         "filtre_veille": vc.get("filtre", []), "flux_reliefweb": a.flux_reliefweb if a.flux_reliefweb is not None else vc.get("flux_rw", []), "hl": cfg.get("hl", "fr"), "gl": cfg.get("gl", "BE"),
         "importer_fichiers": a.importer, "importer_liens": liens, "categorie_import": a.categorie,
         "maj": a.maj, "liens_seulement": a.liens_seulement,
         "jur_hudoc": a.hudoc, "jur_cjue": a.cjue is not None, "jur_actes": a.cjue or ["32011L0095", "32024R1347"],
         "jur_cc": bool(a.cour_const), "jur_cc_de": (a.cour_const or [0, 0])[0], "jur_cc_a": (a.cour_const or [0, 0])[1],
         "jur_articles_hudoc": a.articles, "jur_articles_cjue": a.articles_cjue, "jur_articles_cc": a.articles_cc,
         "jur_mode": "un" if a.au_moins_un else "tous", "jur_reference": a.reference,
         "jur_mots_hudoc": a.mots_jur, "jur_mots_cjue": "", "jur_mots_cc": a.mots_jur, "jur_etat": a.etat,
         "jur_refs": refs, "jur_commun": not a.jur_pays, "jur_depuis": a.depuis, "jur_max": a.max_docs}
    cfg["dossier"] = dossier
    if a.appname:
        cfg["appname"] = a.appname
    sauver_config(cfg)
    lancer_collecte(p)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli(sys.argv[1:])
    else:
        interface()
