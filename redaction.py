# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rédaction : plans types par procédure, notes de bas de page automatiques, annexes.

1. creer_plan()      : un document LibreOffice (.odt) avec le plan type d'une procédure
                       (non-délivrance d'OQT, protection internationale, 9ter), des indications
                       de rédaction et, sous chaque rubrique, les repères des sources collectées.
2. generer()         : dans un texte .odt, remplace chaque repère [[…]] par une vraie note de bas
                       de page (référence complète à la première citation, puis « op.cit. », et
                       « Ibid. » quand la note précédente cite la même source), numérote les annexes
                       dans l'ordre de première citation, écrit l'index des annexes et assemble
                       un PDF unique des annexes (page intercalaire « Annexe n° X » avant chacune).

Syntaxe des repères (dans le texte, là où la note doit apparaître) :
    [[CCPR/C/IDN/CO/2]]                     source seule
    [[CCPR/C/IDN/CO/2, §24, p.8]]           avec la précision (paragraphe, page…)
    [[CCPR/C/IDN/CO/2, §24 +trad]]          « Traduction libre de : … »
    [[… +souligne]]                         « … ; nous soulignons. »
    [[… +annexe]] / [[… +sansannexe]]       forcer ou empêcher la mise en annexe
    [[CCPR/C/IDN/CO/2, §24 ; CAT/C/IDN/CO/2, §10]]   plusieurs sources dans une même note
    [[= texte libre de la note]]            note écrite telle quelle
    [[INDEX DES ANNEXES]]                   endroit où écrire l'index des annexes
"""

import csv
import datetime as dt
import io
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    etree = None

import collecte as C

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
}
T = "{%s}" % NS["text"]
ICI = os.path.dirname(os.path.abspath(__file__))

# Conventions de citation (reprises des dossiers types)
IBID, OPCIT = "Ibid.", "op.cit."
ANNEXE = "voir l’annexe n° %d au présent courrier"
CONSULTE = "(consulté le %s)"

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
DOSSIER_PIECES = "00_Pieces_du_dossier"
EXT_PIECES = (".pdf", ".doc", ".docx", ".odt", ".jpg", ".jpeg", ".png")


def charger_sources(dossier_pays, dossier_base=None):
    """Toutes les sources utilisables : sources.csv du pays, jurisprudence commune,
    et pièces personnelles déposées dans 00_Pieces_du_dossier."""
    out = []
    racines = [dossier_pays]
    if dossier_base:
        racines.append(os.path.join(dossier_base, "Jurisprudence (dossier commun)"))
    for rac in racines:
        chemin = os.path.join(rac, "sources.csv")
        if not os.path.exists(chemin):
            continue
        with open(chemin, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                r = {k: (v or "").strip() for k, v in r.items() if k}
                r["_racine"] = rac
                out.append(r)
    if dossier_base:
        try:
            import bibliotheque as B
            with open(B.chemin_references(dossier_base), encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f, delimiter=";"):
                    rep_ = (r.get("repere") or "").strip()
                    if not rep_:
                        continue
                    out.append({"id": "LEX-" + rep_, "categorie": "Textes de référence", "auteur": "",
                                "titre": (r.get("reference_courte") or "").strip(),
                                "citation": (r.get("reference_complete") or "").strip(),
                                "court": (r.get("reference_courte") or "").strip(),
                                "url": (r.get("url") or "").strip(), "consulte_le": (r.get("consulte_le") or "").strip(),
                                "cote": "", "annexe": "", "remarques": (r.get("a_verifier") or "").strip(),
                                "_lex": True, "_repere": rep_, "_racine": dossier_base})
        except Exception:
            pass
    pieces = os.path.join(dossier_pays, DOSSIER_PIECES)
    if os.path.isdir(pieces):
        for nom in sorted(os.listdir(pieces)):
            if nom.lower().endswith(EXT_PIECES) and not nom.startswith("."):
                base = os.path.splitext(nom)[0]
                out.append({"id": "PIECE-" + base, "categorie": "Pièces du dossier", "auteur": "",
                            "titre": re.sub(r"[_]+", " ", re.sub(r"^\d+[\s._-]*", "", base)).strip(),
                            "cote": "", "date": "", "url": "", "consulte_le": "", "fichier": nom,
                            "annexe": "oui", "citation": "", "_racine": pieces})
    return out


def repere(s, sources=None):
    """Repère le plus court et le plus lisible pour une source."""
    cote = s.get("cote", "")
    if s.get("_lex"):
        return s["_repere"]
    if s.get("id", "").startswith("PIECE-"):
        return "PIECE " + s["id"][6:]
    if cote and (sources is None or sum(1 for x in sources if x.get("cote", "").lower() == cote.lower()) == 1):
        return cote
    return s.get("id", "")


def _cle(x):
    return re.sub(r"\s+", "", (x or "").lower())


def trouver(sources, cle):
    """Renvoie (source, candidats). source = None si introuvable ou ambigu."""
    k = cle.strip()
    if not k:
        return None, []
    kk = _cle(k)
    if k.upper().startswith("PIECE "):
        k2 = "PIECE-" + k[6:].strip()
        c = [s for s in sources if _cle(s.get("id")) == _cle(k2)]
        if c:
            return c[0], c
    for champ, val in (("id", kk), ("id", _cle("LEX-" + k)), ("id", _cle("ONU-" + k)), ("cote", kk)):
        c = [s for s in sources if _cle(s.get(champ)) == val]
        if len(c) == 1:
            return c[0], c
        if len(c) > 1:  # même document en double (ex. pays et dossier commun) : on prend le premier
            return c[0], c
    # numéro de requête, affaire C-…, ECLI : dans la cote ou la citation
    m = re.fullmatch(r"(?:req\.?\s*n°\s*)?(\d{1,6}/\d{2})", k, re.I) or re.fullmatch(r"([CT]-\d+/\d{2})", k, re.I) \
        or re.fullmatch(r"(ECLI:[\w:.\-]+)", k, re.I)
    if m:
        v = _cle(m.group(1))
        c = [s for s in sources if v in _cle(s.get("cote")) or v in _cle(s.get("citation"))]
        if len(c) >= 1:
            return (c[0] if len(c) == 1 else None), c
    # mots : tous présents dans auteur + titre + cote + citation
    mots = [m_ for m_ in C.norm(k).split() if len(m_) > 1]
    if mots:
        c = [s for s in sources if all(m_ in C.norm(" ".join(s.get(x, "") for x in ("auteur", "titre", "cote", "citation", "id")))
                                       for m_ in mots)]
        if len(c) == 1:
            return c[0], c
        return None, c
    return None, []


# ---------------------------------------------------------------------------
# Repères
# ---------------------------------------------------------------------------
RE_REPERE = re.compile(r"\[\[(.+?)\]\]")
DRAPEAUX = ("+trad", "+souligne", "+soulignons", "+annexe", "+sansannexe")


def analyser_repere(contenu):
    """« CCPR/C/IDN/CO/2, §24 +trad ; CAT/C/IDN/CO/2 » -> liste de dict(cle, precision, drapeaux)."""
    contenu = contenu.strip()
    if contenu.startswith("="):
        return [{"libre": contenu[1:].strip()}]
    if C.norm(contenu) in ("index des annexes", "index annexes"):
        return [{"index": True}]
    out = []
    for morceau in [m for m in re.split(r"\s;\s|;(?=\s*[A-Za-zÀ-ÿ\[=])", contenu) if m.strip()]:
        if morceau.strip().startswith("="):  # texte libre au milieu d'une note à plusieurs sources
            out.append({"libre": morceau.strip()[1:].strip()})
            continue
        drap = set()
        for d in DRAPEAUX:
            if d in morceau.lower():
                drap.add(d.lstrip("+").replace("soulignons", "souligne"))
                morceau = re.sub(re.escape(d), "", morceau, flags=re.I)
        morceau = morceau.strip()
        if "," in morceau:
            cle, precision = morceau.split(",", 1)
        else:
            m = re.search(r"\s(?=§|pp?\.\s?\d|art\.|al\.|point\s)", morceau)
            cle, precision = (morceau[:m.start()], morceau[m.start():]) if m else (morceau, "")
        out.append({"cle": cle.strip(), "precision": precision.strip().strip(","), "drapeaux": drap})
    return out


# ---------------------------------------------------------------------------
# Mise en forme des références (liste de morceaux : (texte, "it"|None) ou ("lien", url))
# ---------------------------------------------------------------------------
def _cote_affichee(s):
    """Les numéros de la Collection des traités (IV-9…) ne sont pas des cotes à citer."""
    return "" if s.get("categorie") == "Ratifications" else s.get("cote", "")


def _titre_propre(t, cote=""):
    """Titres repris d'une ligne de tableau du HCDH : on ne garde que le type de document."""
    if " – " in t and re.search(r" – Voir document| – [ESACRF](?: – |$)|\.pdf|\.docx?", t):
        premier = t.split(" – ")[0].strip()
        return premier[:1].lower() + premier[1:] if premier else t
    return t


def _titre(s):
    t = _titre_propre(s.get("titre", ""), s.get("cote", ""))
    if (s.get("id") or "").startswith("TRAITE-"):
        try:
            import conditionnels as K
            nom = K.TRAITES.get(s["id"][7:], (None,))[0]
            if nom:
                return nom.split(" ", 1)[1][:1].upper() + nom.split(" ", 1)[1][1:]
        except Exception:
            pass
    if s.get("categorie") == "Presse" and t and not t.startswith("«"):
        return "« %s »" % t
    return t


def _court_juris(citation):
    """« Cour eur. D.H. (Gde Ch.), arrêt X c. Y, 23 août 2016, req. n° … » -> « Cour eur. D.H. (Gde Ch.), arrêt X c. Y »."""
    m = re.search(r",\s*(\d{1,2}(?:er)?\s+\w+\s+\d{4}|req\.|aff\.|n°)", citation)
    return citation[:m.start()] if m else citation


def reference_complete(s, precision, annexe_no):
    if s.get("citation"):
        mm = [(s["citation"].rstrip(". "), None)]
        if s.get("_lex") and s.get("url") and not annexe_no:  # texte en ligne : précision avant le lien
            if precision:
                mm.append((", " + precision, None))
                precision = ""
            mm += [(", ", None), ("lien", s["url"])]
            if s.get("consulte_le"):
                mm.append((" " + CONSULTE % s["consulte_le"], None))
        if annexe_no:
            mm.append((", " + ANNEXE % annexe_no, None))
    else:
        champs = [x for x in (s.get("auteur"), _titre(s), _cote_affichee(s), s.get("date")) if x]
        if precision:  # la précision suit l'identification du document, avant le lien
            champs.append(precision)
            precision = ""
        mm = [(", ".join(champs), None)]
        url = s.get("url", "")
        consulte = s.get("consulte_le", "")
        if annexe_no:  # document annexé : le renvoi à l'annexe remplace le lien
            mm.append((", " + ANNEXE % annexe_no, None))
        elif url:
            mm += [(", ", None), ("lien", url)]
            if consulte:
                mm.append((" " + CONSULTE % consulte, None))
    if precision:
        mm.append((", " + precision, None))
    return mm


def reference_courte(s, precision):
    if s.get("court"):
        base = s["court"]
    elif s.get("citation"):
        base = _court_juris(s["citation"])
    else:
        base = ", ".join(x for x in (s.get("auteur"), _titre(s), _cote_affichee(s)) if x)
    mm = [(base + ", ", None), (OPCIT, "it")]
    if precision:
        mm.append((", " + precision, None))
    return mm


def entree_index(s):
    if s.get("citation"):
        return s["citation"].rstrip(". ") + "."
    champs = [x for x in (s.get("auteur"), _titre(s), _cote_affichee(s), s.get("date")) if x]
    return (", ".join(champs) or s.get("id", "")).rstrip(". ") + "."


# ---------------------------------------------------------------------------
# Lecture et écriture du document
# ---------------------------------------------------------------------------
PETITS = {T + "s", T + "tab", T + "line-break", T + "soft-page-break", T + "bookmark", T + "bookmark-start",
          T + "bookmark-end", T + "reference-mark", T + "change", T + "change-start", T + "change-end"}


def _car(el):
    if el.tag == T + "s":
        return " " * int(el.get(T + "c", "1") or 1)
    if el.tag in (T + "tab",):
        return "\t"
    if el.tag == T + "line-break":
        return "\n"
    return ""


def _morceaux(p):
    """Découpe le contenu d'un paragraphe en morceaux adressables :
    ('texte', élément, 'text'|'tail', chaîne) ; ('petit', élément, chaîne équivalente) ; ('note', élément)."""
    out = []

    def visiter(el):
        if el.text:
            out.append(("texte", el, "text", el.text))
        for ch in el:
            if ch.tag == T + "note":
                out.append(("note", ch))
            elif ch.tag in PETITS or len(ch) == 0 and ch.tag.startswith(T) and ch.tag not in (T + "span", T + "a"):
                out.append(("petit", ch, _car(ch)))
            elif ch.tag.startswith("{%s}" % NS["draw"]) or ch.tag.startswith("{%s}" % NS["office"]):
                out.append(("petit", ch, ""))
            else:
                visiter(ch)
            if ch.tail:
                out.append(("texte", ch, "tail", ch.tail))
    visiter(p)
    return out


def _texte(morceaux):
    return "".join(m[3] if m[0] == "texte" else (m[2] if m[0] == "petit" else "") for m in morceaux)


def _supprimer(p, debut, fin):
    """Retire les caractères [debut, fin) du paragraphe (texte réparti dans des balises, espaces codés…)."""
    reste = fin - debut
    while reste > 0:
        pos, fait = 0, False
        for m in _morceaux(p):
            if m[0] == "note":
                continue
            s_ = m[3] if m[0] == "texte" else m[2]
            a, b = pos, pos + len(s_)
            pos = b
            if b <= debut:
                continue
            if m[0] == "petit":
                el = m[1]
                parent = el.getparent()
                if el.tail:
                    prev = el.getprevious()
                    if prev is not None:
                        prev.tail = (prev.tail or "") + el.tail
                    else:
                        parent.text = (parent.text or "") + el.tail
                parent.remove(el)
                reste -= len(s_)
            else:
                i = debut - a
                j = min(len(s_), i + reste)
                nouveau = s_[:i] + s_[j:]
                if m[2] == "text":
                    m[1].text = nouveau
                else:
                    m[1].tail = nouveau
                reste -= (j - i)
            fait = True
            break
        if not fait:
            break


def _inserer(p, offset, el):
    """Insère l'élément el à la position offset du paragraphe."""
    pos = 0
    for m in _morceaux(p):
        if m[0] == "note":
            continue
        s = m[3] if m[0] == "texte" else m[2]
        if m[0] == "texte" and pos <= offset <= pos + len(s):
            i = offset - pos
            avant, apres = s[:i], s[i:]
            if m[2] == "text":
                m[1].text = avant
                el.tail = apres
                m[1].insert(0, el)
            else:
                m[1].tail = avant
                el.tail = apres
                parent = m[1].getparent()
                parent.insert(parent.index(m[1]) + 1, el)
            return
        pos += len(s)
    el.tail = None
    p.append(el)


def _paragraphes(body):
    """Paragraphes et titres du corps, dans l'ordre, hors notes existantes et index générés."""
    out = []
    for el in body.iter(T + "p", T + "h"):
        anc = el.getparent()
        dans_note = False
        while anc is not None:
            if anc.tag in (T + "note-body", T + "table-of-content", T + "index-body"):
                dans_note = True
                break
            anc = anc.getparent()
        if not dans_note:
            out.append(el)
    return out


def _style_italique(root):
    auto = root.find("office:automatic-styles", NS)
    if auto is None:
        auto = etree.SubElement(root, "{%s}automatic-styles" % NS["office"])
    nom = "Tred_it"
    if not any(s.get("{%s}name" % NS["style"]) == nom for s in auto):
        st = etree.SubElement(auto, "{%s}style" % NS["style"])
        st.set("{%s}name" % NS["style"], nom)
        st.set("{%s}family" % NS["style"], "text")
        tp = etree.SubElement(st, "{%s}text-properties" % NS["style"])
        for a in ("{%s}font-style" % NS["fo"], "{%s}font-style-asian" % NS["style"], "{%s}font-style-complex" % NS["style"]):
            tp.set(a, "italic")
    return nom


def _remplir(p, morceaux, style_it):
    """Écrit une liste de morceaux (texte, style) dans le paragraphe p."""
    dernier = None
    for txt, st in morceaux:
        if not txt:
            continue
        if txt == "lien":
            a = etree.SubElement(p, T + "a")
            a.set("{%s}type" % NS["xlink"], "simple")
            a.set("{%s}href" % NS["xlink"], st)
            a.text = st
            dernier = a
        elif st == "it":
            sp = etree.SubElement(p, T + "span")
            sp.set(T + "style-name", style_it)
            sp.text = txt
            dernier = sp
        else:
            if dernier is None:
                p.text = (p.text or "") + txt
            else:
                dernier.tail = (dernier.tail or "") + txt


_LOT = dt.datetime.now().strftime("%H%M%S")  # identifiants uniques même si le document est retraité


def _nouvelle_note(morceaux, style_it, n):
    note = etree.Element(T + "note")
    note.set(T + "id", "ftnR%s_%d" % (_LOT, n))
    note.set(T + "note-class", "footnote")
    cit = etree.SubElement(note, T + "note-citation")
    cit.text = str(n)
    corps = etree.SubElement(note, T + "note-body")
    p = etree.SubElement(corps, T + "p")
    p.set(T + "style-name", "Footnote")
    _remplir(p, morceaux, style_it)
    return note


# ---------------------------------------------------------------------------
# Génération des notes et des annexes
# ---------------------------------------------------------------------------
class Resultat:
    def __init__(self):
        self.notes = 0
        self.annexes = []          # [(n°, source)]
        self.problemes = []        # messages
        self.odt = self.pdf = self.rapport = ""


def generer(chemin_odt, sources, dossier_sortie=None, pdf_annexes=True, tampon=True, log=print,
            bibliotheque=None, variables=None, tout_annexer=True):
    """Traite le document ; ne modifie jamais l'original. Renvoie un Resultat.
    tout_annexer : toute source citée est annexée (sauf textes de référence, +sansannexe ou colonne annexe = non)."""
    if etree is None:
        raise RuntimeError("Le module lxml manque : relancez l’installateur.")
    res = Resultat()
    base = os.path.splitext(os.path.basename(chemin_odt))[0]
    dossier_sortie = dossier_sortie or os.path.dirname(os.path.abspath(chemin_odt))
    os.makedirs(dossier_sortie, exist_ok=True)
    with zipfile.ZipFile(chemin_odt) as z:
        fichiers = {n: z.read(n) for n in z.namelist()}
    root = etree.fromstring(fichiers["content.xml"])
    body = root.find("office:body/office:text", NS)
    if bibliotheque and os.path.exists(bibliotheque):
        import bibliotheque as B
        n_b, manquants = B.developper_blocs(root, B.Bibliotheque(bibliotheque), variables or {})
        if n_b:
            log("  %d bloc(s) de la bibliothèque inséré(s)" % n_b)
        for m_ in manquants:
            res.problemes.append("Bloc introuvable dans la bibliothèque : « %s »." % m_)
    style_it = _style_italique(root)
    # lignes bleues de suggestion du plan (« [[repère]]  –  titre ») : aide à la rédaction, retirées du résultat
    n_sugg = 0
    for p in list(_paragraphes(body)):
        t = "".join(p.itertext())
        if re.match(r"^\s*\[\[(?!\s*BLOC\s)[^\]]+\]\]\s+–\s", t) or \
                re.match(r"^… et \d+ autre\(s\) : voir la liste complète", t.strip()) or \
                t.strip().startswith("Mode d’emploi de ce plan (à supprimer ensuite)"):
            if p.getparent() is not None:
                p.getparent().remove(p)
                n_sugg += 1
    if n_sugg:
        log("  %d ligne(s) d’aide du plan retirée(s) (suggestions bleues, mode d’emploi)" % n_sugg)
    paras = _paragraphes(body)

    # 1er passage : événements (repères et notes existantes) dans l'ordre du document
    evenements = []   # (p, debut, fin, analyse | None pour note existante)
    for p in paras:
        ms = _morceaux(p)
        texte, pos = "", 0
        notes_ex = []
        for m in ms:
            if m[0] == "note":
                notes_ex.append(pos)
            else:
                s = m[3] if m[0] == "texte" else m[2]
                texte += s
                pos += len(s)
        evs = [(o, o, o, None) for o in notes_ex]
        for m in RE_REPERE.finditer(texte):
            if re.match(r"\s*BLOC\s", m.group(1)):
                continue  # bloc introuvable : laissé tel quel (signalé plus haut)
            evs.append((m.start(), m.start(), m.end(), analyser_repere(m.group(1))))
        for o, a, b, an in sorted(evs, key=lambda e: e[0]):
            evenements.append((p, a, b, an))

    # résolution des sources et annexes (ordre de première citation)
    annexe_de = {}
    for p, a, b, an in evenements:
        if not an:
            continue
        for r in an:
            if "cle" not in r:
                continue
            s, cands = trouver(sources, r["cle"])
            r["source"] = s
            if s is None:
                if cands:
                    res.problemes.append("Repère ambigu « %s » : %d sources possibles (%s…). Précisez-le (cote ou "
                                         "identifiant)." % (r["cle"], len(cands), " | ".join(repere(c) for c in cands[:3])))
                else:
                    res.problemes.append("Repère introuvable « %s » : aucune source ne correspond." % r["cle"])
                continue
            col = (s.get("annexe", "") or "").strip().lower()
            if tout_annexer:
                fich = (s.get("fichier") or "").lower()
                document = fich and not fich.endswith((".csv", ".html", ".htm", ".xml", ".json", ".txt"))
                veut = "annexe" in r["drapeaux"] or col not in ("", "non", "0", "n") or \
                    (not s.get("_lex") and document and col not in ("non", "0", "n"))
            else:
                veut = "annexe" in r["drapeaux"] or col not in ("", "non", "0", "n")
            veut = veut and "sansannexe" not in r["drapeaux"]
            if veut and s["id"] not in annexe_de:
                annexe_de[s["id"]] = len(annexe_de) + 1
                res.annexes.append((annexe_de[s["id"]], s))

    # 2e passage : texte de chaque note (première citation, op.cit., Ibid.)
    deja, precedent = set(), None
    contenus = []
    for p, a, b, an in evenements:
        if an is None:
            precedent = None  # note existante : on ne sait pas ce qu'elle cite
            contenus.append(None)
            continue
        if an and "index" in an[0]:
            contenus.append("INDEX")
            continue
        if len(an) == 1 and "libre" in an[0]:
            contenus.append([(an[0]["libre"].rstrip(".") + ".", None)])
            precedent = None
            continue
        parties, sources_note = [], []
        for r in an:
            if "libre" in r:
                parties.append([(r["libre"].rstrip("."), None)])
                sources_note.append(None)
                continue
            s = r.get("source")
            if s is None:
                parties.append([("[" + r["cle"] + (", " + r["precision"] if r["precision"] else "") + " : SOURCE INTROUVABLE]",
                                 None)])
                sources_note.append(None)
                continue
            if len(an) == 1 and precedent is not None and precedent[0] == s["id"]:
                mm = [(IBID, "it")] + ([(", " + r["precision"], None)] if r["precision"] and r["precision"] != precedent[1] else [])
            elif s["id"] in deja:
                mm = reference_courte(s, r["precision"])
            else:
                mm = reference_complete(s, r["precision"], annexe_de.get(s["id"]))
                deja.add(s["id"])
            if "trad" in r["drapeaux"]:
                mm = [("Traduction libre de : ", None)] + mm
            if "souligne" in r["drapeaux"]:
                mm = mm + [(" ; nous soulignons", None)]
            parties.append(mm)
            sources_note.append((s["id"], r["precision"]))
        note = []
        for i, mm in enumerate(parties):
            if i:
                note.append((" ; ", None))
            note += mm
        # point final (sans doubler)
        if note and note[-1][0] != "lien" and not str(note[-1][0]).rstrip().endswith("."):
            note.append((".", None))
        elif note and note[-1][0] == "lien":
            note.append((".", None))
        contenus.append(note)
        precedent = sources_note[0] if len(sources_note) == 1 and sources_note[0] else None

    # 3e passage : insertion, du dernier repère au premier dans chaque paragraphe
    index_para = None
    par_para = {}
    for (p, a, b, an), c in zip(evenements, contenus):
        par_para.setdefault(id(p), (p, []))[1].append((a, b, an, c))
    n = 0
    for p, evs in par_para.values():
        for a, b, an, c in sorted(evs, key=lambda e: -e[0]):
            if an is None:
                continue
            if c == "INDEX":
                _supprimer(p, a, b)
                index_para = p
                continue
            _supprimer(p, a, b)
            n += 1
            _inserer(p, a, _nouvelle_note(c, style_it, n))
            res.notes += 1

    # numérotation de toutes les notes dans l'ordre du document
    for i, note in enumerate([x for x in body.iter(T + "note") if x.get(T + "note-class", "footnote") == "footnote"], 1):
        cit = note.find(T + "note-citation")
        if cit is not None:
            cit.text = str(i)

    # index des annexes
    if res.annexes:
        lignes = ["Annexe %d : %s" % (no, entree_index(s)) for no, s in res.annexes]
        if index_para is None:
            h = etree.SubElement(body, T + "h")
            h.set(T + "style-name", "Heading_20_1")
            h.set(T + "outline-level", "1")
            h.text = "Index des annexes"
            ancre, parent = h, body
        else:
            ancre, parent = index_para, index_para.getparent()
        style_p = index_para.get(T + "style-name") if index_para is not None else "Text_20_body"
        pos = parent.index(ancre) + 1
        for l in lignes:
            np_ = etree.Element(T + "p")
            np_.set(T + "style-name", style_p or "Text_20_body")
            np_.text = l
            parent.insert(pos, np_)
            pos += 1
        if index_para is not None and not "".join(index_para.itertext()).strip():
            parent.remove(index_para)

    # écriture du nouveau document
    res.odt = os.path.join(dossier_sortie, base + "_notes.odt")
    fichiers["content.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    _ecrire_odt(res.odt, fichiers)
    log("  Document avec notes : %s (%d note(s) créée(s), %d annexe(s))" % (res.odt, res.notes, len(res.annexes)))

    if pdf_annexes and res.annexes:
        res.pdf = os.path.join(dossier_sortie, base + "_annexes.pdf")
        manques = assembler_annexes(res.annexes, res.pdf, tampon=tampon, log=log)
        res.problemes += manques

    res.rapport = os.path.join(dossier_sortie, base + "_rapport.txt")
    with open(res.rapport, "w", encoding="utf-8") as f:
        f.write("Traitement de %s – %s\n\n" % (os.path.basename(chemin_odt), dt.datetime.now().strftime("%d/%m/%Y %H:%M")))
        f.write("%d note(s) créée(s) ; %d annexe(s).\n\n" % (res.notes, len(res.annexes)))
        if res.annexes:
            f.write("Annexes :\n")
            for no, s in res.annexes:
                f.write("  %d. %s  [%s]\n" % (no, entree_index(s), s.get("fichier") or "pas de fichier"))
            f.write("\n")
        f.write("Points à vérifier :\n" if res.problemes else "Aucun problème relevé.\n")
        for pb in res.problemes:
            f.write("  - %s\n" % pb)
    return res


def _ecrire_odt(chemin, fichiers):
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), fichiers.get("mimetype", b"application/vnd.oasis.opendocument.text"),
                   compress_type=zipfile.ZIP_STORED)
        for nom, contenu in fichiers.items():
            if nom != "mimetype":
                z.writestr(nom, contenu, compress_type=zipfile.ZIP_DEFLATED)


# ---------------------------------------------------------------------------
# Annexes : PDF unique avec pages intercalaires
# ---------------------------------------------------------------------------
def _pdf_texte(s):
    s = s.encode("cp1252", "replace").decode("latin-1")
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _couper(texte, n):
    lignes, cur = [], ""
    for mot in texte.split():
        if len(cur) + len(mot) + 1 > n and cur:
            lignes.append(cur)
            cur = mot
        else:
            cur = (cur + " " + mot).strip()
    if cur:
        lignes.append(cur)
    return lignes


def page_pdf(lignes, largeur=595.28, hauteur=841.89):
    """PDF d'une page. lignes = [(x, y, taille, gras, texte)]. Polices standard (pas d'installation)."""
    flux = []
    for x, y, taille, gras, txt in lignes:
        flux.append("BT /%s %d Tf %.1f %.1f Td (%s) Tj ET" % ("F2" if gras else "F1", taille, x, y, _pdf_texte(txt)))
    contenu = ("q\n" + "\n".join(flux) + "\nQ\n").encode("latin-1")  # fin de ligne : flux fusionnables
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> "
         "/Contents 6 0 R >>" % (largeur, hauteur)).encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(contenu) + contenu + b"\nendstream",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    pos = []
    for i, o in enumerate(objs, 1):
        pos.append(out.tell())
        out.write(b"%d 0 obj\n" % i + o + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for p_ in pos:
        out.write(b"%010d 00000 n \n" % p_)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref))
    return out.getvalue()


def page_intercalaire(no, description):
    lignes = [(72, 520, 30, True, "Annexe n° %d" % no)]
    y = 470
    for l in _couper(description, 80)[:14]:
        lignes.append((72, y, 12, False, l))
        y -= 18
    return page_pdf(lignes)


def _vers_pdf(chemin, tmp):
    """Convertit un document (Word, ODT, image…) en PDF avec LibreOffice, s'il est installé."""
    for exe in ("soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                r"C:\Program Files\LibreOffice\program\soffice.exe"):
        if shutil.which(exe) or os.path.exists(exe):
            try:
                subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", tmp, chemin],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            except Exception:
                return None
            sortie = os.path.join(tmp, os.path.splitext(os.path.basename(chemin))[0] + ".pdf")
            return sortie if os.path.exists(sortie) else None
    return None


def assembler_annexes(annexes, sortie, tampon=True, log=print):
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter()
    manques = []
    tmp = tempfile.mkdtemp(prefix="annexes_")
    try:
        for no, s in annexes:
            desc = entree_index(s)
            w.append(PdfReader(io.BytesIO(page_intercalaire(no, desc))))
            f = s.get("fichier", "")
            chemin = os.path.join(s.get("_racine", ""), f) if f else ""
            if not chemin or not os.path.exists(chemin):
                manques.append("Annexe %d : pas de fichier (%s) – seule la page intercalaire est dans le PDF." % (no, desc[:80]))
                continue
            pdf = chemin if chemin.lower().endswith(".pdf") else _vers_pdf(chemin, tmp)
            if not pdf:
                manques.append("Annexe %d : %s n’a pas pu être converti en PDF (LibreOffice introuvable ?)." % (no, f))
                continue
            try:
                r = PdfReader(pdf)
                debut = len(w.pages)
                w.append(r)
                if tampon:
                    total = len(w.pages) - debut
                    for k in range(debut, len(w.pages)):
                        pg = w.pages[k]
                        L, H = float(pg.mediabox.width), float(pg.mediabox.height)
                        texte = "Annexe n° %d – p. %d/%d" % (no, k - debut + 1, total)
                        st = PdfReader(io.BytesIO(page_pdf([(L - 190, H - 22, 9, True, texte)], L, H))).pages[0]
                        try:  # certains PDF finissent leur contenu sans retour à la ligne : on l'ajoute
                            c_ = pg.get_contents()
                            d_ = c_.get_data() if c_ is not None else b"\n"
                            if not d_[-1:].isspace():
                                c_.set_data(d_ + b"\n")
                                pg.replace_contents(c_)
                        except Exception:
                            pass
                        pg.merge_page(st)
            except Exception as e:
                manques.append("Annexe %d : PDF illisible (%s)." % (no, e))
        with open(sortie, "wb") as f:
            w.write(f)
        log("  PDF des annexes : %s" % sortie)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return manques


# ---------------------------------------------------------------------------
# Plans types
# ---------------------------------------------------------------------------
def _f(**kw):
    """Filtre de sources pour une rubrique : categories, cote (regex), texte (regex sur auteur/titre)."""
    def ok(s):
        if "categories" in kw and s.get("categorie") not in kw["categories"]:
            return False
        if "cote" in kw and not re.search(kw["cote"], s.get("cote", "") + " " + s.get("id", ""), re.I):
            return False
        if "texte" in kw and not re.search(kw["texte"], " ".join(s.get(x, "") for x in ("auteur", "titre", "citation")), re.I):
            return False
        return True
    return ok


JURI = ("Jurisprudence",)
ONG = ("ONG internationales", "Sources nationales")

PLANS = {
    "oqt": ("Demande de non-délivrance d’un ordre de quitter le territoire – principe de non-refoulement", [
        (1, "I. La situation personnelle de {demandeur}[ et de {sa} famille]",
         "Présentez chaque membre de la famille : identité, parcours, faits vécus (dates, lieux, auteurs), engagements "
         "(religieux, politiques, syndicaux…). Chaque fait important appelle une pièce ou une source.", None),
        (2, "A. {demandeur}", "Faits vécus, éventuelles violences subies, engagements.",
         _f(categories=("Pièces du dossier",))),
        (2, "B. [Conjoint·e]", "", None),
        (2, "C. Les enfants", "Scolarité, intégration, intérêt supérieur de l’enfant (attestations scolaires en annexe).", None),
        (1, "II. Pays sûr ? La situation des droits humains {en_pays}", "", None),
        (2, "A. Introduction", "Traités ratifiés, réserves, procédures de plaintes acceptées ou non par l’État.",
         _f(categories=("Ratifications",))),
        (2, "B. {Le_pays} et les normes de droit international en matière de droits humains : violations systématiques, "
            "systémiques", "", None),
        (3, "1) Violations systématiques et systémiques", "", None),
        (4, "a. Le Pacte international relatif aux droits civils et politiques",
         "Observations finales du Comité des droits de l’homme, suivi (lettres de suivi, notes attribuées), état des rapports.",
         _f(cote=r"CCPR")),
        (4, "b. La Convention contre la torture et autres peines ou traitements cruels, inhumains ou dégradants",
         "Observations finales du Comité contre la torture, listes de points, suivi.", _f(cote=r"CAT")),
        (4, "c. Le Pacte international relatif aux droits économiques, sociaux et culturels",
         "Observations finales du Comité des droits économiques, sociaux et culturels (santé, travail, éducation, "
         "discriminations).", _f(cote=r"E/C\.12|CESCR")),
        (4, "d. Autres instruments", "Autres comités (CEDAW, CRC, CERD…), OIT, etc.",
         _f(cote=r"CEDAW|CRC|CERD|CRPD|CMW|CED/")),
        (3, "2) Des violations persistantes", "", None),
        (4, "a. Les constatations des ONG", "", _f(categories=ONG)),
        (4, "b. Les constatations des gouvernements et organisations régionales",
         "Département d’État des États-Unis, EUAA…", _f(categories=("Gouvernements et organisations régionales",))),
        (4, "c. L’Examen périodique universel : recommandations acceptées et rejetées",
         "Rapport du Groupe de travail et additif (recommandations « notées » = refusées).", _f(categories=("EPU",))),
        (4, "d. Les constatations les plus récentes",
         "Haut-Commissariat, procédures spéciales, presse.",
         _f(categories=("ONU – HCDH et Conseil des droits de l’homme", "Procédures spéciales", "Presse"))),
        (3, "3) Conclusion générale sur la situation des droits humains {en_pays}", "", None),
        (1, "III. La situation {du_demandeur} au regard de la situation {en_pays}",
         "Reliez le profil de chaque personne aux constats de la partie II : qui est visé, par qui, avec quelle protection "
         "effective ?", None),
        (2, "A. {demandeur}", "", None),
        (2, "B. [Conjoint·e]", "", None),
        (2, "C. Les enfants", "", None),
        (2, "D. Conclusion", "", None),
        (1, "IV. La demande",
         "Bases : art. 3 de la Convention européenne des droits de l’homme, art. 3 de la Convention contre la torture, "
         "art. 33 de la Convention de 1951 relative au statut des réfugiés, art. 74/13 de la loi du 15 décembre 1980 "
         "(intérêt supérieur de l’enfant, vie familiale, état de santé) ; jurisprudence de la Cour eur. D.H. et du C.C.E.",
         _f(categories=JURI)),
    ]),
    "pi": ("Demande de protection internationale", [
        (1, "1. Identité", "Identité complète {du_demandeur} (pièces d’identité en annexe).",
         _f(categories=("Pièces du dossier",))),
        (1, "2. Les faits", "Récit chronologique, précis et cohérent : dates, lieux, auteurs, conséquences. Chaque "
                            "élément vérifiable appelle une pièce ou une source.", None),
        (1, "3. L’introduction de la demande dans le délai",
         "Date d’arrivée et date de présentation de la demande. Si le délai de huit jours ouvrables est dépassé : "
         "raisons du retard (langue, traumatisme, ignorance de la procédure, passeur…) et pièces qui les établissent.",
         None),
        (1, "4. Pays sûr ? La situation des droits humains {en_pays}", "", None),
        (2, "A. Introduction", "Traités ratifiés, réserves, procédures de plaintes acceptées ou non.",
         _f(categories=("Ratifications",))),
        (2, "B. {Le_pays} et les normes de droit international en matière de droits humains : violations systématiques, "
            "systémiques", "", None),
        (3, "1) Violations systématiques et systémiques", "", None),
        (4, "a. Le Pacte international relatif aux droits civils et politiques",
         "Observations finales du Comité des droits de l’homme, suivi, état des rapports.", _f(cote=r"CCPR")),
        (4, "b. La Convention contre la torture et autres peines ou traitements cruels, inhumains ou dégradants",
         "Observations finales du Comité contre la torture, listes de points, suivi.", _f(cote=r"CAT")),
        (4, "c. Le Pacte international relatif aux droits économiques, sociaux et culturels",
         "Observations finales du Comité des droits économiques, sociaux et culturels.", _f(cote=r"E/C\.12|CESCR")),
        (4, "d. Autres instruments", "Autres comités (CEDAW, CRC, CERD…), OIT, etc.",
         _f(cote=r"CEDAW|CRC|CERD|CRPD|CMW|CED/")),
        (3, "2) Des violations persistantes", "", None),
        (4, "a. Les constatations des ONG", "", _f(categories=ONG)),
        (4, "b. Les constatations des gouvernements et organisations régionales",
         "Département d’État des États-Unis, EUAA…", _f(categories=("Gouvernements et organisations régionales",))),
        (4, "c. L’Examen périodique universel : recommandations acceptées et rejetées", "", _f(categories=("EPU",))),
        (4, "d. Les constatations les plus récentes", "Haut-Commissariat, procédures spéciales, presse.",
         _f(categories=("ONU – HCDH et Conseil des droits de l’homme", "Procédures spéciales", "Presse"))),
        (2, "C. Conclusion générale sur la situation des droits humains {en_pays}", "", None),
        (1, "5. À titre principal : l’octroi du statut de réfugié",
         "Base légale depuis le 12 juin 2026 : règlement (UE) 2024/1347, directement applicable (définition du réfugié : "
         "art. 3, point 5) ; évaluation des faits : art. 4 ; acteurs : art. 6 et 7 ; protection à l’intérieur du pays : "
         "art. 8 ; actes de persécution : art. 9 ; motifs : art. 10) et Convention de Genève, art. 1er, A, 2. Les anciens "
         "articles 48/3 à 48/5 et 48/7 de la loi du 15 décembre 1980 sont abrogés et l’article 48/6 ne règle plus que "
         "la production des pièces (loi du 16 juin 2026) : la jurisprudence rendue "
         "sous leur empire reste utilisable, en signalant la nouvelle base légale.", None),
        (2, "A. Une crainte fondée de persécution", "", None),
        (3, "1) La définition du réfugié et la crainte avec raison", "", None),
        (3, "2) Les acteurs des persécutions et l’absence de protection effective", "", None),
        (3, "3) Le cas de {demandeur}", "Pour chaque motif : les faits propres {au_demandeur}, puis les constats de la "
                                        "partie 4 qui les rendent vraisemblables.", None),
        (4, "a. Persécutions en raison des opinions politiques", "", None),
        (4, "b. Persécutions en raison de la religion ou de l’appartenance à un certain groupe social", "", None),
        (5, "i. Les persécutions de groupe", "", None),
        (5, "ii. Les craintes personnelles de persécutions émanant de l’État", "", None),
        (5, "iii. Les craintes personnelles de persécutions émanant d’acteurs non étatiques", "", None),
        (1, "6. À titre subsidiaire : la protection subsidiaire et le principe de non-refoulement", "", None),
        (2, "A. La protection subsidiaire", "Règlement (UE) 2024/1347, art. 3, point 6), et art. 15 : a) peine de mort ou "
                                            "exécution ; b) torture ou traitements ou sanctions inhumains ou dégradants ; "
                                            "c) menace grave et individuelle en raison d’une violence aveugle en cas de "
                                            "conflit armé.", None),
        (3, "1) Les atteintes graves", "", None),
        (3, "2) Les acteurs des atteintes graves", "", None),
        (3, "3) Le cas de {demandeur}", "", None),
        (4, "a. La peine de mort ou l’exécution", "", None),
        (4, "b. La torture ou les traitements inhumains ou dégradants", "", None),
        (5, "i. Les atteintes émanant de l’État", "", None),
        (5, "ii. Les atteintes émanant d’acteurs non étatiques", "", None),
        (2, "B. Le principe de non-refoulement", "Art. 3 de la Convention européenne des droits de l’homme, art. 3 de la "
                                                 "Convention contre la torture, art. 33 de la Convention de 1951.",
         _f(categories=JURI)),
        (1, "7. La demande", "", None),
    ]),
    "9ter": ("Demande d’autorisation de séjour pour raisons médicales (article 9ter de la loi du 15 décembre 1980)", [
        (1, "I. Situation personnelle {du_demandeur}", "Identité, composition de la famille, parcours, intégration.",
         _f(categories=("Pièces du dossier",))),
        (1, "II. Situation {de_pays} concernant les soins de santé et leur mise en œuvre", "", None),
        (2, "A. La prise en charge de la maladie {en_pays}",
         "Disponibilité réelle des traitements, du suivi et des médicaments nécessaires (sources OMS, EUAA, études).",
         _f(categories=("ONU – agences", "Gouvernements et organisations régionales"))),
        (2, "B. L’accessibilité des soins : sécurité sociale, coût, corruption",
         "Couverture effective, coût des soins et des médicaments au regard des revenus, paiements informels.",
         _f(cote=r"E/C\.12")),
        (2, "C. Conclusions sur les soins de santé {en_pays}", "", None),
        (1, "III. Demande de régularisation fondée sur l’article 9ter de la loi du 15 décembre 1980", "", None),
        (2, "A. Récapitulatif des éléments d’identification {du_demandeur}",
         "Certificat médical type et ses annexes, pièces d’identité.", None),
        (2, "B. Le fondement de la demande", "Risque réel pour la vie ou l’intégrité physique, ou risque réel de traitement "
                                           "inhumain ou dégradant en l’absence de traitement adéquat ; Cour eur. D.H. "
                                           "(Gde Ch.), arrêt Paposhvili c. Belgique, 13 décembre 2016.",
         _f(categories=JURI)),
        (3, "1. La situation médicale de {demandeur} au regard de l’article 9ter", "", None),
        (3, "2. L’absence de traitement adéquat, disponible et accessible {en_pays}", "", None),
        (4, "a. La disponibilité des soins appropriés {en_pays}",
         "Les soins doivent être « effectivement disponibles » : examens, traitements, médicaments, personnel formé.", None),
        (4, "b. L’accessibilité des soins d’un point de vue structurel",
         "Financement du système de santé, paiements directs, corruption.", _f(cote=r"E/C\.12|CESCR")),
        (4, "c. L’accessibilité des soins au regard de la situation individuelle de {demandeur}",
         "Revenus prévisibles de la famille comparés au coût des soins (ordres de grandeur, sources chiffrées).", None),
        (2, "C. Conclusions concernant la demande", "", None),
    ]),
}
PLANS_NOM = "plans_types.odt"
PLANS_VERSION = 1


def sans_numero(titre):
    """« 4. À titre principal » -> « à titre principal » : les blocs et les paragraphes calculés restent à leur
    place même si vous renumérotez les titres du plan."""
    t = re.sub(r"^\s*(?:[IVXLCivxlc]+|\d+|[A-Za-z])\s*[.)]\s*(?:bis\b|ter\b)?\s*", "", titre or "")
    return C.norm(t).strip()


def meme_rubrique(titre_plan, rubrique):
    a, b = sans_numero(titre_plan), sans_numero(rubrique)
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


def construire_plans(chemin):
    """plans_types.odt : Titre 1 = procédure ; Titres 2 à 6 = titres du plan (niveaux 1 à 5) ; un paragraphe
    normal sous un titre = indication de rédaction (en gris dans le plan)."""
    root = etree.fromstring(_gabarit_contenu().encode("utf-8"))
    body = root.find("office:body/office:text", NS)

    def p(texte, style="Pcorps"):
        e = etree.SubElement(body, T + "p")
        e.set(T + "style-name", style)
        e.text = texte

    def h(texte, niveau):
        e = etree.SubElement(body, T + "h")
        e.set(T + "style-name", "Heading_20_%d" % niveau)
        e.set(T + "outline-level", str(niveau))
        e.text = texte
    p("Plans types", "Ptitre")
    p("Mode d’emploi (ce paragraphe gris est ignoré) : Titre 1 = la procédure (ne pas renommer). En dessous, les titres "
      "du plan : Titre 2 pour « I. », « 1. »… ; Titre 3 pour « A. » ; Titre 4 pour « 1) » ; Titre 5 pour « a. » ; "
      "Titre 6 pour « i. ». Un paragraphe normal sous un titre devient l’indication de rédaction (en gris dans le plan). "
      "Pour ajouter une section : placez le curseur à la fin du titre qui précède, Entrée, choisissez le style de titre "
      "voulu, tapez le titre. Variables possibles : {demandeur}, {du_demandeur}, {en_pays}, {Le_pays}, {de_pays}… "
      "Enregistrez au format ODT.", "Paide")
    for proc, (titre_doc, rubriques) in PLANS.items():
        h(NOMS_PROCEDURES[proc], 1)
        p("Titre du document : " + titre_doc)
        for niveau, titre, aide, filtre in rubriques:
            h(titre, niveau + 1)
            if aide:
                p(aide)
    fichiers = {
        "mimetype": b"application/vnd.oasis.opendocument.text",
        "content.xml": etree.tostring(root, xml_declaration=True, encoding="UTF-8"),
        "styles.xml": open(os.path.join(ICI, "modele_styles.xml"), "rb").read(),
        "META-INF/manifest.xml": (
            '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
            'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
            '<manifest:file-entry manifest:full-path="/" manifest:version="1.3" '
            'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
            '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
            '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
            '</manifest:manifest>').encode(),
    }
    _ecrire_odt(chemin, fichiers)
    return chemin


def chemin_plans(base):
    c = os.path.join(base, PLANS_NOM)
    if not os.path.exists(c):
        os.makedirs(base, exist_ok=True)
        construire_plans(c)
    return c


def _proc_du_titre(titre):
    n = C.norm(titre)
    if "9ter" in n or "medical" in n:
        return "9ter"
    if "protection internationale" in n or "asile" in n:
        return "pi"
    if "oqt" in n or "quitter" in n or "refoulement" in n:
        return "oqt"
    return ""


def lire_plans(chemin):
    """Renvoie {procédure: (titre du document, [(niveau, titre, aide, filtre)])}. Les filtres de sources
    suggérées sont repris des plans d'origine (même titre, sans tenir compte de la numérotation)."""
    with zipfile.ZipFile(chemin) as z:
        root = etree.fromstring(z.read("content.xml"))
    body = root.find("office:body/office:text", NS)
    out, proc, cur = {}, None, None
    for el in body:
        if el.tag == T + "h":
            niv = int(el.get(T + "outline-level", "1") or 1)
            titre = " ".join("".join(el.itertext()).split())
            if niv == 1:
                proc = _proc_du_titre(titre)
                if proc:
                    out[proc] = [PLANS[proc][0], []]
                cur = None
                continue
            if proc and titre:
                filtre = next((f for n_, t_, a_, f in PLANS[proc][1] if sans_numero(t_) == sans_numero(titre)), None)
                cur = [min(niv - 1, 5), titre, "", filtre]
                out[proc][1].append(cur)
        elif el.tag == T + "p" and proc and el.get(T + "style-name") != "Paide":
            txt = " ".join("".join(el.itertext()).split())
            if not txt:
                continue
            if txt.lower().startswith("titre du document :"):
                out[proc][0] = txt.split(":", 1)[1].strip() or out[proc][0]
            elif cur is not None:
                cur[2] = (cur[2] + " " + txt).strip()
    return {k: (v[0], [tuple(x) for x in v[1]]) for k, v in out.items() if v[1]}


NOMS_PROCEDURES = {"oqt": "Non-délivrance d’OQT (non-refoulement)", "pi": "Protection internationale", "9ter": "9ter (raisons médicales)"}


def _gabarit_contenu():
    polices = open(os.path.join(ICI, "modele_polices.xml"), encoding="utf-8").read()
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<office:document-content '
            'xmlns:office="%(office)s" xmlns:style="%(style)s" xmlns:text="%(text)s" xmlns:table="%(table)s" '
            'xmlns:draw="%(draw)s" xmlns:fo="%(fo)s" xmlns:xlink="%(xlink)s" '
            'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
            'xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" office:version="1.3">'
            % NS) + polices + (
        '<office:automatic-styles>'
        '<style:style style:name="Pcorps" style:family="paragraph" style:parent-style-name="Standard">'
        '<style:paragraph-properties fo:text-align="justify" style:justify-single-word="false"/>'
        '<style:text-properties style:font-name="Arial1" fo:language="fr" fo:country="BE"/></style:style>'
        '<style:style style:name="Paide" style:family="paragraph" style:parent-style-name="Standard">'
        '<style:paragraph-properties fo:text-align="justify" fo:margin-bottom="0.08in"/>'
        '<style:text-properties style:font-name="Arial1" fo:color="#7a7a7a" fo:font-style="italic" '
        'style:font-style-asian="italic" style:font-style-complex="italic"/></style:style>'
        '<style:style style:name="Psrc" style:family="paragraph" style:parent-style-name="Standard">'
        '<style:paragraph-properties fo:margin-left="0.4in"/>'
        '<style:text-properties style:font-name="Arial1" fo:color="#08738f" fo:font-size="9pt"/></style:style>'
        '<style:style style:name="Ptitre" style:family="paragraph" style:parent-style-name="Heading">'
        '<style:paragraph-properties fo:text-align="center"/></style:style>'
        '<style:style style:name="Tsoul" style:family="text"><style:text-properties '
        'style:text-underline-style="solid" style:text-underline-width="auto" '
        'style:text-underline-color="font-color"/></style:style>'
        '<style:style style:name="Sect1" style:family="section"><style:section-properties style:editable="false">'
        '<style:columns fo:column-count="1" fo:column-gap="0in"/></style:section-properties></style:style>'
        '</office:automatic-styles><office:body><office:text/></office:body></office:document-content>')


def formes_pays(de_pays, nom):
    """« de l’Indonésie », « Indonésie » -> en Indonésie / L’Indonésie / de l’Indonésie (au Maroc, aux Philippines…)."""
    d = (de_pays or "").strip()
    if d.startswith("du "):
        en, le = "au " + nom, "Le " + nom
    elif d.startswith("des "):
        en, le = "aux " + nom, "Les " + nom
    elif d.startswith(("de l’", "de l'")):
        en, le = "en " + nom, "L’" + nom
    elif d.startswith("de la "):
        en, le = "en " + nom, "La " + nom
    else:
        en, le = "en " + nom, nom
    le_min = le if le == nom else le[0].lower() + le[1:]
    a_ = {"le ": "au ", "les ": "aux "}
    a_pays = next((a_[k] + le_min[len(k):] for k in a_ if le_min.startswith(k)), "à " + le_min)
    return {"en_pays": en, "Le_pays": le, "le_pays": le_min, "a_pays": a_pays, "de_pays": d or "de " + nom}


PERSONNES = {"m": "un homme (Monsieur)", "f": "une femme (Madame)",
             "mp": "plusieurs personnes / une famille", "fp": "plusieurs femmes"}


def formes_personne(code="m"):
    """Accords selon la personne qui demande : m, f, mp (plusieurs, dont au moins un homme), fp (plusieurs femmes)."""
    i = {"m": 0, "f": 1, "mp": 2, "fp": 3}.get(code or "m", 0)
    t = {
        "le_demandeur": ("le demandeur", "la demanderesse", "les demandeurs", "les demanderesses"),
        "du_demandeur": ("du demandeur", "de la demanderesse", "des demandeurs", "des demanderesses"),
        "au_demandeur": ("au demandeur", "à la demanderesse", "aux demandeurs", "aux demanderesses"),
        "il": ("il", "elle", "ils", "elles"),
        "le": ("le", "la", "les", "les"),
        "lui": ("lui", "lui", "leur", "leur"),
        "eux": ("lui", "elle", "eux", "elles"),
        "e": ("", "e", "s", "es"),
        "s": ("", "", "s", "s"),
        "son": ("son", "son", "leur", "leur"),
        "sa": ("sa", "sa", "leur", "leur"),
        "ses": ("ses", "ses", "leurs", "leurs"),
        "est": ("est", "est", "sont", "sont"),
        "a": ("a", "a", "ont", "ont"),
    }
    v = {k: x[i] for k, x in t.items()}
    for k in ("le_demandeur", "il"):
        v[k[0].upper() + k[1:]] = v[k][0].upper() + v[k][1:]
    v["_pluriel"], v["_feminin"] = i >= 2, i in (1, 3)
    return v


def remplacer(texte, variables):
    """{nom} = variable ; {singulier|pluriel} et {masculin/féminin} (combinables : {il/elle|ils/elles})."""
    if not texte or "{" not in texte:
        return texte
    pl, fe = variables.get("_pluriel", False), variables.get("_feminin", False)

    def r(m):
        x = m.group(1)
        if re.fullmatch(r"\w+", x):
            v = variables.get(x)
            return v if isinstance(v, str) else m.group(0)
        if "|" not in x and "/" not in x:
            return m.group(0)
        if "|" in x:
            a, _, b = x.partition("|")
            x = b if pl else a
        if "/" in x:
            a, _, b = x.partition("/")
            x = b if fe else a
        return x
    return re.sub(r"\{([^{}\n]{1,80})\}", r, texte)


def creer_plan(procedure, chemin_sortie, de_pays="", nom_pays="[pays]", demandeur="[nom du demandeur]", sources=None,
               bibliotheque=None, blocs=None, log=print, personne="m", dossier_pays=None, aujourdhui=None,
               plans=None):
    """blocs : titres des blocs de la bibliothèque à recopier (None = ceux « par défaut »)."""
    if etree is None:
        raise RuntimeError("Le module lxml manque : relancez l’installateur.")
    titre_doc, rubriques = PLANS[procedure]
    if plans and os.path.exists(plans):
        try:
            perso = lire_plans(plans).get(procedure)
            if perso:
                titre_doc, rubriques = perso
        except Exception as e:
            log("  ! plans_types.odt illisible (%s) : plan d’origine utilisé." % e)
    root = etree.fromstring(_gabarit_contenu().encode("utf-8"))
    body = root.find("office:body/office:text", NS)

    def p(texte, style="Pcorps"):
        e = etree.SubElement(body, T + "p")
        e.set(T + "style-name", style)
        e.text = texte
        return e

    p(titre_doc, "Ptitre")
    p("")
    p("Mode d’emploi de ce plan (à supprimer ensuite) : remplacez les passages entre crochets, rédigez sous chaque titre et "
      "supprimez les paragraphes gris. Là où une note de bas de page est nécessaire, tapez un repère, par exemple "
      "[[CCPR/C/IDN/CO/2, §24, p.8]]. Les repères disponibles sont listés en bleu sous chaque titre et dans l’onglet "
      "« Rédaction » (double-clic pour copier) ; le bouton « Comment écrire une note ? » donne tous les exemples (pages, paragraphes, articles) et les abréviations. Enfin, onglet « Rédaction » puis « Générer les notes et les annexes ». "
      "Pour la table des matières : clic droit dessus puis « Mettre à jour l’index ».", "Paide")
    tdm = etree.SubElement(body, T + "table-of-content")
    tdm.set(T + "style-name", "Sect1")
    tdm.set(T + "protected", "true")
    tdm.set(T + "name", "Table des matières")
    src = etree.fromstring(open(os.path.join(ICI, "modele_tdm.xml"), encoding="utf-8").read().replace(
        "<text:table-of-content-source", '<text:table-of-content-source xmlns:text="%s" xmlns:style="%s"' % (NS["text"], NS["style"]), 1))
    tdm.append(src)
    ib = etree.SubElement(tdm, T + "index-body")
    it_ = etree.SubElement(ib, T + "index-title")
    it_.set(T + "style-name", "Sect1")
    it_.set(T + "name", "Table des matières_Head")
    pt = etree.SubElement(it_, T + "p")
    pt.set(T + "style-name", "Contents_20_Heading")
    pt.text = "Table des matières"
    utilises = set()
    variables = dict(formes_pays(de_pays, nom_pays), **formes_personne(personne))
    variables.update({"pays": nom_pays, "demandeur": demandeur or "[nom du demandeur]"})
    biblio, a_placer, styles_copies = None, [], {}
    if bibliotheque and os.path.exists(bibliotheque):
        import bibliotheque as B
        biblio = B.Bibliotheque(bibliotheque)
        a_placer = [b for b in biblio.de_procedure(procedure) if (b.defaut if blocs is None else b.titre in blocs)]
    auto = []
    if dossier_pays and procedure in ("oqt", "pi"):
        import conditionnels as K
        try:
            auto, alertes = K.paragraphes(dossier_pays, sources or [], variables, aujourdhui)
        except Exception as e:  # jamais bloquant
            auto, alertes = [], ["calcul impossible : %s" % e]
        for a_ in alertes:
            log("  ! Paragraphes calculés : " + a_)
    auj = aujourdhui or dt.date.today()
    for niveau, titre, aide, filtre in rubriques:
        titre = remplacer(titre, variables)
        h = etree.SubElement(body, T + "h")
        h.set(T + "style-name", "Heading_20_%d" % niveau)
        h.set(T + "outline-level", str(niveau))
        h.text = titre
        if aide:
            p("[" + remplacer(aide, variables) + "]", "Paide")
        nt = C.norm(titre)
        calcules = []
        for rub_, ps_ in auto:
            if meme_rubrique(titre, rub_) and ps_:
                calcules += ps_
        if calcules:
            p("[Paragraphes calculés automatiquement le %s à partir de la collecte (ratifications, procédures de "
              "plaintes, état des rapports, documents de suivi). Vérifiez chaque date et chaque durée, complétez les "
              "passages entre crochets, puis supprimez ce paragraphe gris.]" % C.date_fr(auj), "Paide")
            for x in calcules:
                p(x)
                p("")
        for b in [b for b in a_placer if calcules and "a completer a la main" in C.norm(b.titre)
                  and meme_rubrique(titre, b.rubrique)]:
            a_placer.remove(b)
            log("  Bloc « %s » remplacé par les paragraphes calculés." % b.titre)
        for b in [b for b in a_placer if meme_rubrique(titre, b.rubrique)]:
            a_placer.remove(b)
            styles_copies.setdefault("__blocs__", set()).add(b.titre)
            for c in biblio.copier(b, root, variables, styles_copies):
                body.append(c)
        if filtre and sources:
            choisies = [s for s in sources if not s.get("_lex") and filtre(s)]
            for s in choisies[:25]:
                utilises.add(s["id"])
                p("[[%s]]  –  %s" % (repere(s, sources), entree_index(s)[:160]), "Psrc")
            if len(choisies) > 25:
                p("… et %d autre(s) : voir la liste complète dans l’onglet « Rédaction »." % (len(choisies) - 25), "Psrc")
        p("")
    for b in a_placer:
        log("  ! Bloc « %s » : rubrique « %s » absente du plan, bloc non inséré." % (b.titre, b.rubrique))
    h = etree.SubElement(body, T + "h")
    h.set(T + "style-name", "Heading_20_1")
    h.set(T + "outline-level", "1")
    h.text = "Index des annexes"
    p("[[INDEX DES ANNEXES]]")
    fichiers = {
        "mimetype": b"application/vnd.oasis.opendocument.text",
        "content.xml": etree.tostring(root, xml_declaration=True, encoding="UTF-8"),
        "styles.xml": open(os.path.join(ICI, "modele_styles.xml"), "rb").read(),
        "meta.xml": ('<?xml version="1.0" encoding="UTF-8"?><office:document-meta xmlns:office="%s" '
                     'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.3"><office:meta>'
                     '<meta:generator>Probasile</meta:generator></office:meta></office:document-meta>' % NS["office"]).encode(),
        "META-INF/manifest.xml": (
            '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
            'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
            '<manifest:file-entry manifest:full-path="/" manifest:version="1.3" '
            'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
            '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
            '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
            '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>'
            '</manifest:manifest>').encode(),
    }
    os.makedirs(os.path.dirname(os.path.abspath(chemin_sortie)), exist_ok=True)
    _ecrire_odt(chemin_sortie, fichiers)
    return chemin_sortie


def odt_simple(chemin, elements, titre=""):
    """Petit document LibreOffice : elements = [(niveau de titre 1-4 ou 0 pour un paragraphe, texte, gris?)]."""
    root = etree.fromstring(_gabarit_contenu().encode("utf-8"))
    body = root.find("office:body/office:text", NS)
    if titre:
        e = etree.SubElement(body, T + "p")
        e.set(T + "style-name", "Ptitre")
        e.text = titre
    for niv, txt, gris in elements:
        if niv:
            e = etree.SubElement(body, T + "h")
            e.set(T + "style-name", "Heading_20_%d" % niv)
            e.set(T + "outline-level", str(niv))
        else:
            e = etree.SubElement(body, T + "p")
            e.set(T + "style-name", "Paide" if gris else "Pcorps")
        e.text = txt
        if not niv and not gris:
            v = etree.SubElement(body, T + "p")
            v.set(T + "style-name", "Pcorps")
    fichiers = {
        "mimetype": b"application/vnd.oasis.opendocument.text",
        "content.xml": etree.tostring(root, xml_declaration=True, encoding="UTF-8"),
        "styles.xml": open(os.path.join(ICI, "modele_styles.xml"), "rb").read(),
        "META-INF/manifest.xml": (
            '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
            'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
            '<manifest:file-entry manifest:full-path="/" manifest:version="1.3" '
            'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
            '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
            '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
            '</manifest:manifest>').encode(),
    }
    _ecrire_odt(chemin, fichiers)
    return chemin


# ---------------------------------------------------------------------------
# Liste des sources : annexe prévue, modification, ajout, suppression
# ---------------------------------------------------------------------------
DOSSIER_AJOUTS = "12_Sources_ajoutees"
CHAMPS_SOURCES = ["id", "categorie", "auteur", "titre", "cote", "date", "url", "consulte_le", "fichier", "langue",
                  "annexe", "remarques", "citation", "articles"]


ORDRE_CATEGORIES = ["Pièces du dossier", "Organes de traités", "Ratifications", "EPU", "Procédures spéciales",
                    "ONU – HCDH et Conseil des droits de l’homme", "ONU – agences", "ONG internationales",
                    "Sources nationales", "Gouvernements et organisations régionales", "Presse", "Jurisprudence",
                    "Sources ajoutées", "À classer", "Textes de référence"]


def categorie_affichee(s):
    c = s.get("categorie") or "À classer"
    return "Textes de référence (lois, conventions, arrêts)" if c == "Textes de référence" else c


def cle_tri_categorie(c):
    c0 = "Textes de référence" if c.startswith("Textes de référence") else c
    return ORDRE_CATEGORIES.index(c0) if c0 in ORDRE_CATEGORIES else len(ORDRE_CATEGORIES) - 2


def description_courte(s):
    """Ce qui distingue la source dans la liste : titre (ou référence courte), cote, date — sans l'auteur."""
    if s.get("_lex"):
        return s.get("citation") or s.get("court") or s.get("titre", "")
    t = _titre(s) or s.get("titre", "")
    auteur = s.get("auteur", "")
    if auteur and not auteur.startswith("ONU"):
        t = "%s – %s" % (auteur, t)
    morceaux = [t]
    if _cote_affichee(s) and _cote_affichee(s) not in t:
        morceaux.append(_cote_affichee(s))
    if s.get("date"):
        morceaux.append(s["date"])
    return ", ".join(x for x in morceaux if x)


def annexe_prevue(s, tout_annexer=True):
    """« oui » (annexée), « non » (citée avec son lien), « loi » (texte de référence, jamais annexé)."""
    if s.get("_lex"):
        return "loi"
    col = (s.get("annexe") or "").strip().lower()
    if col in ("non", "0", "n"):
        return "non"
    if col:
        return "oui"
    fich = (s.get("fichier") or "").lower()
    doc = fich and not fich.endswith((".csv", ".html", ".htm", ".xml", ".json", ".txt"))
    return "oui" if (tout_annexer and doc) else "non"


def _lire_sources_csv(chemin):
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f, delimiter=";")
        return list(rd.fieldnames or CHAMPS_SOURCES), list(rd)


def _ecrire_sources_csv(chemin, champs, lignes):
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for l in lignes:
            w.writerow({k: l.get(k, "") or "" for k in champs})
    os.replace(tmp, chemin)


def modifier_source(s, changements):
    """Modifie une ligne de sources.csv (du pays ou du dossier commun). Renvoie "" ou un message d'erreur."""
    chemin = os.path.join(s.get("_racine") or "", "sources.csv")
    if s.get("_lex") or not os.path.exists(chemin):
        return "Cette source n’est pas dans un fichier sources.csv."
    champs, lignes = _lire_sources_csv(chemin)
    for k in changements:
        if k not in champs:
            champs.append(k)
    n = 0
    for l in lignes:
        if l.get("id") == s.get("id"):
            l.update(changements)
            n += 1
    if not n:
        return "Source introuvable dans %s." % chemin
    _ecrire_sources_csv(chemin, champs, lignes)
    return ""


def ajouter_source(dossier_pays, champs_src, fichier=None):
    """Ajoute une source saisie à la main (document hors collecte). Le fichier éventuel est copié dans
    12_Sources_ajoutees. Renvoie (id, message d'erreur)."""
    titre = (champs_src.get("titre") or "").strip()
    if not titre:
        return "", "Le titre est obligatoire."
    chemin = os.path.join(dossier_pays, "sources.csv")
    champs, lignes = (_lire_sources_csv(chemin) if os.path.exists(chemin) else (list(CHAMPS_SOURCES), []))
    base = "AJOUT-" + (re.sub(r"[^A-Za-z0-9]+", "-", C.norm(champs_src.get("cote") or titre)).strip("-")[:40] or "source")
    ids = {l.get("id") for l in lignes}
    id_, i = base, 2
    while id_ in ids:
        id_, i = "%s-%d" % (base, i), i + 1
    ligne = {k: (champs_src.get(k) or "").strip() for k in champs}
    ligne["id"] = id_
    ligne["categorie"] = ligne.get("categorie") or "Sources ajoutées"
    if fichier:
        d = os.path.join(dossier_pays, DOSSIER_AJOUTS)
        os.makedirs(d, exist_ok=True)
        nom = os.path.basename(fichier)
        dest = os.path.join(d, nom)
        if os.path.abspath(dest) != os.path.abspath(fichier):
            shutil.copy(fichier, dest)
        ligne["fichier"] = os.path.join(DOSSIER_AJOUTS, nom)
    lignes.append(ligne)
    for k in CHAMPS_SOURCES:
        if k not in champs:
            champs.append(k)
    _ecrire_sources_csv(chemin, champs, lignes)
    return id_, ""


def supprimer_source(s):
    """Seules les sources ajoutées à la main (AJOUT-…) peuvent être retirées de la liste."""
    if not (s.get("id") or "").startswith("AJOUT-"):
        return "Seules les sources ajoutées à la main peuvent être supprimées ; pour une source collectée, mettez « non » " \
               "dans la colonne annexe ou ne la citez pas."
    chemin = os.path.join(s.get("_racine") or "", "sources.csv")
    champs, lignes = _lire_sources_csv(chemin)
    _ecrire_sources_csv(chemin, champs, [l for l in lignes if l.get("id") != s["id"]])
    return ""


def liste_html(sources, chemin):
    """Page HTML : toutes les sources avec leur repère, triées par catégorie."""
    import html as H
    lignes = ["<!doctype html><meta charset='utf-8'><title>Repères</title><style>body{font-family:Arial;margin:2em}"
              "td,th{border-bottom:1px solid #ddd;padding:.3em .6em;vertical-align:top;text-align:left}"
              "code{background:#eef5f5;padding:1px 4px}</style><h1>Repères des sources</h1>"
              "<p>Copiez le repère (avec les doubles crochets) à l’endroit de la note. Ajoutez la précision après une "
              "virgule : <code>[[CCPR/C/IDN/CO/2, §24, p.8]]</code>.</p><table><tr><th>Repère</th><th>Catégorie</th>"
              "<th>Référence</th><th>Annexe</th></tr>"]
    for s in sorted(sources, key=lambda x: (x.get("categorie", ""), x.get("date", ""))):
        lignes.append("<tr><td><code>[[%s]]</code></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            H.escape(repere(s, sources)), H.escape(s.get("categorie", "")), H.escape(entree_index(s)),
            H.escape(s.get("annexe", ""))))
    lignes.append("</table>")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("".join(lignes))
    return chemin
