# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""Format Word (.docx) pour la rédaction, sans Word ni LibreOffice.

1. odt_vers_docx() : convertit un document .odt créé par Probasile (plan type, aperçu) en .docx :
                     titres, paragraphes, gras/italique/souligné/couleur, listes, tableaux, table des matières.
2. generer_docx()  : même traitement que redaction.generer() sur un texte .docx : chaque repère [[…]]
                     devient une vraie note de bas de page Word, les blocs [[BLOC …]] sont développés,
                     l'index des annexes est écrit et le PDF des annexes assemblé.
L'original n'est jamais modifié : le résultat est « …_notes.docx ».
"""

import copy
import datetime as dt
import os
import re
import zipfile

from lxml import etree

import redaction as R

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
W = "{%s}" % W_NS
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
REL_FOOTNOTES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
REL_HYPERLINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
CT_FOOTNOTES = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"

ODT_T = R.T
ODT_STYLE = "{%s}" % R.NS["style"]
ODT_FO = "{%s}" % R.NS["fo"]
ODT_TABLE = "{%s}" % R.NS["table"]


def w(tag, attrs=None, parent=None, text=None):
    el = etree.SubElement(parent, W + tag) if parent is not None else etree.Element(W + tag, nsmap={"w": W_NS})
    for k, v in (attrs or {}).items():
        el.set(W + k, str(v))
    if text is not None:
        el.text = text
        if text[:1].isspace() or text[-1:].isspace():
            el.set(XML_SPACE, "preserve")
    return el


# ---------------------------------------------------------------------------
# Propriétés de mise en forme (ODT -> Word)
# ---------------------------------------------------------------------------
def _longueur_twips(v):
    m = re.match(r"\s*(-?[\d.]+)\s*(in|cm|mm|pt)?", v or "")
    if not m:
        return 0
    x, u = float(m.group(1)), m.group(2) or "in"
    return int(round(x * {"in": 1440, "cm": 566.93, "mm": 56.693, "pt": 20}[u]))


def _props_style(style_el):
    """Propriétés utiles d'un style ODT : (texte, paragraphe)."""
    t, p = {}, {}
    if style_el is None:
        return t, p
    tp = style_el.find(ODT_STYLE + "text-properties")
    if tp is not None:
        if tp.get(ODT_FO + "font-style") == "italic":
            t["i"] = True
        if tp.get(ODT_FO + "font-weight") in ("bold", "700", "800", "900"):
            t["b"] = True
        u = tp.get(ODT_STYLE + "text-underline-style")
        if u and u != "none":
            t["u"] = True
        c = tp.get(ODT_FO + "color")
        if c and re.fullmatch(r"#[0-9a-fA-F]{6}", c) and c.lower() != "#000000":
            t["color"] = c[1:].upper()
        sz = tp.get(ODT_FO + "font-size")
        if sz and sz.endswith("pt"):
            try:
                t["sz"] = int(round(float(sz[:-2]) * 2))
            except ValueError:
                pass
    pp = style_el.find(ODT_STYLE + "paragraph-properties")
    if pp is not None:
        al = pp.get(ODT_FO + "text-align")
        if al in ("justify", "center", "end", "right"):
            p["jc"] = {"justify": "both", "center": "center", "end": "right", "right": "right"}[al]
        if pp.get(ODT_FO + "margin-left"):
            p["ind"] = _longueur_twips(pp.get(ODT_FO + "margin-left"))
        if pp.get(ODT_FO + "margin-bottom"):
            p["after"] = _longueur_twips(pp.get(ODT_FO + "margin-bottom"))
        if pp.get(ODT_FO + "break-before") == "page":
            p["page"] = True
    return t, p


def _rpr(props, parent):
    """w:rPr dans l'ordre exigé par Word (rStyle, b, i, color, sz, u, vertAlign)."""
    if not props:
        return None
    r = w("rPr", parent=parent)
    if props.get("rStyle"):
        w("rStyle", {"val": props["rStyle"]}, r)
    if props.get("b"):
        w("b", parent=r)
    if props.get("i"):
        w("i", parent=r)
    if props.get("color"):
        w("color", {"val": props["color"]}, r)
    if props.get("sz"):
        w("sz", {"val": props["sz"]}, r)
        w("szCs", {"val": props["sz"]}, r)
    if props.get("u"):
        w("u", {"val": "single"}, r)
    if props.get("sup"):
        w("vertAlign", {"val": "superscript"}, r)
    return r


def _ppr(p_el, pstyle=None, pp=None):
    pp = pp or {}
    if not (pstyle or pp):
        return None
    r = w("pPr", parent=p_el)
    if pstyle:
        w("pStyle", {"val": pstyle}, r)
    if pp.get("page"):
        w("pageBreakBefore", parent=r)
    if pp.get("after") is not None:
        w("spacing", {"after": pp["after"]}, r)
    if pp.get("ind"):
        w("ind", {"left": pp["ind"]}, r)
    if pp.get("jc"):
        w("jc", {"val": pp["jc"]}, r)
    return r


def _run(parent, texte, props=None):
    r = w("r", parent=parent)
    _rpr(props, r)
    morceaux = re.split(r"(\t|\n)", texte)
    for m in morceaux:
        if m == "\t":
            w("tab", parent=r)
        elif m == "\n":
            w("br", parent=r)
        elif m:
            w("t", parent=r, text=m)
    return r


class Convertisseur:
    """Éléments d'un document ODT -> éléments Word (w:p, w:tbl)."""

    # styles de paragraphe nommés dans les plans de Probasile -> styles du modèle Word
    STYLES_PLAN = {"Ptitre": "TitrePlan", "Paide": "Aide", "Psrc": "Repere"}

    def __init__(self, styles_auto, styles_word=None):
        self.styles_auto = styles_auto          # nom -> élément style:style (ODT)
        self.word = styles_word or {}           # « heading 1 »… -> styleId du document Word cible
        self.ids = set(self.word.values())

    def _st(self, nom):
        return self.styles_auto.get(nom)

    def titre(self, niveau):
        return self.word.get("heading %d" % niveau) or ("Heading%d" % niveau if "Heading%d" % niveau in self.ids else None)

    def elements(self, el):
        tag = el.tag
        if tag == ODT_T + "h":
            return [self.paragraphe(el, titre=int(el.get(ODT_T + "outline-level", "1") or 1))]
        if tag == ODT_T + "p":
            return [self.paragraphe(el)]
        if tag == ODT_T + "list":
            out = []
            for item in el:
                premier = True
                for ch in item:
                    for x in self.elements(ch):
                        if premier and x.tag == W + "p":
                            texte = "".join(t.text or "" for t in x.iter(W + "t")).lstrip()
                            if texte and not texte.startswith(("–", "-", "•", "—")):
                                self._prefixer(x, "– ")
                            premier = False
                        out.append(x)
            return out
        if tag == ODT_TABLE + "table":
            return [self.tableau(el)]
        if tag == ODT_T + "table-of-content":
            return self.table_des_matieres()
        if tag == ODT_T + "section":
            out = []
            for ch in el:
                out += self.elements(ch)
            return out
        return []

    def _prefixer(self, p, prefixe):
        premier_run = p.find(W + "r")
        r = etree.Element(W + "r")
        w("t", parent=r, text=prefixe)
        if premier_run is not None:
            premier_run.addprevious(r)
        else:
            p.append(r)

    def paragraphe(self, el, titre=None):
        nom = el.get(ODT_T + "style-name") or ""
        t0, pp = _props_style(self._st(nom))
        p = w("p")
        pstyle = None
        if titre:
            pstyle = self.titre(titre)
            if not pstyle:
                t0 = dict(t0, b=True, sz=t0.get("sz") or {1: 32, 2: 28, 3: 26}.get(titre, 24))
        elif nom in self.STYLES_PLAN and self.STYLES_PLAN[nom] in self.ids:
            pstyle, t0, pp = self.STYLES_PLAN[nom], {}, {}
        _ppr(p, pstyle, pp)
        self._contenu(el, t0, p)
        return p

    def _contenu(self, el, props, p):
        if el.text:
            _run(p, el.text, props)
        for ch in el:
            tag = ch.tag
            if tag == ODT_T + "span":
                t_, _ = _props_style(self._st(ch.get(ODT_T + "style-name") or ""))
                self._contenu(ch, dict(props, **t_), p)
            elif tag == ODT_T + "a":
                self._contenu(ch, props, p)
            elif tag == ODT_T + "s":
                _run(p, " " * int(ch.get(ODT_T + "c", "1") or 1), props)
            elif tag == ODT_T + "tab":
                _run(p, "\t", props)
            elif tag == ODT_T + "line-break":
                _run(p, "\n", props)
            elif tag in (ODT_T + "note", ODT_T + "soft-page-break", ODT_T + "bookmark", ODT_T + "bookmark-start",
                         ODT_T + "bookmark-end") or not tag.startswith(ODT_T):
                pass
            else:
                self._contenu(ch, props, p)
            if ch.tail:
                _run(p, ch.tail, props)

    def tableau(self, el):
        tbl = w("tbl")
        pr = w("tblPr", parent=tbl)
        w("tblW", {"w": 0, "type": "auto"}, pr)
        b = w("tblBorders", parent=pr)
        for cote in ("top", "left", "bottom", "right", "insideH", "insideV"):
            w(cote, {"val": "single", "sz": 4, "space": 0, "color": "808080"}, b)
        lignes = [r for r in el.iter(ODT_TABLE + "table-row")]
        ncol = max([len([c for c in r if c.tag == ODT_TABLE + "table-cell"]) for r in lignes] or [1])
        grille = w("tblGrid", parent=tbl)
        for _ in range(ncol):
            w("gridCol", {"w": int(9000 / ncol)}, grille)
        for r in lignes:
            tr = w("tr", parent=tbl)
            for c in r:
                if c.tag != ODT_TABLE + "table-cell":
                    continue
                tc = w("tc", parent=tr)
                tcpr = w("tcPr", parent=tc)
                w("tcW", {"w": int(9000 / ncol), "type": "dxa"}, tcpr)
                contenu = []
                for ch in c:
                    contenu += self.elements(ch)
                for x in contenu or [w("p")]:
                    tc.append(x)
        return tbl

    def table_des_matieres(self):
        t = w("p")
        _ppr(t, self.word.get("toc heading") or ("TOCHeading" if "TOCHeading" in self.ids else None))
        _run(t, "Table des matières", None if "TOCHeading" in self.ids else {"b": True, "sz": 28})
        p = w("p")
        r = w("r", parent=p)
        w("fldChar", {"fldCharType": "begin", "dirty": "true"}, r)
        r = w("r", parent=p)
        w("instrText", parent=r, text=' TOC \\o "1-4" \\h \\z \\u ')
        r = w("r", parent=p)
        w("fldChar", {"fldCharType": "separate"}, r)
        _run(p, "Pour afficher la table des matières : clic droit ici, puis « Mettre à jour les champs ».",
             {"i": True, "color": "7A7A7A"})
        r = w("r", parent=p)
        w("fldChar", {"fldCharType": "end"}, r)
        return [t, p]


# ---------------------------------------------------------------------------
# Modèle de document Word (pour les plans créés par Probasile)
# ---------------------------------------------------------------------------
CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="%s">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/settings.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
    '<Override PartName="/word/footnotes.xml" ContentType="%s"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    '</Types>' % (CT_NS, CT_FOOTNOTES))

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="%s">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
    'Target="docProps/core.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
    'Target="docProps/app.xml"/>'
    '</Relationships>' % PR_NS)

DOC_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="%s">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="styles.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" '
    'Target="settings.xml"/>'
    '<Relationship Id="rId3" Type="%s" Target="footnotes.xml"/>'
    '</Relationships>' % (PR_NS, REL_FOOTNOTES))

SETTINGS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="%s">'
    '<w:defaultTabStop w:val="708"/><w:hyphenationZone w:val="425"/>'
    '<w:characterSpacingControl w:val="doNotCompress"/><w:updateFields w:val="true"/>'
    '<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>'
    '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" '
    'w:val="15"/></w:compat>'
    '<w:decimalSymbol w:val=","/><w:listSeparator w:val=";"/></w:settings>' % W_NS)

FOOTNOTES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:footnotes xmlns:w="%s" xmlns:r="%s">'
    '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
    '</w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>'
    '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" '
    'w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
    '</w:footnotes>' % (W_NS, R_NS))


def _style_xml(sid, nom, typ="paragraph", base=None, ppr="", rpr="", suivant=None, qformat=True, prio=None):
    s = '<w:style w:type="%s" w:styleId="%s"><w:name w:val="%s"/>' % (typ, sid, nom)
    if base:
        s += '<w:basedOn w:val="%s"/>' % base
    if suivant:
        s += '<w:next w:val="%s"/>' % suivant
    if prio is not None:
        s += '<w:uiPriority w:val="%d"/>' % prio
    if qformat:
        s += "<w:qFormat/>"
    if ppr:
        s += "<w:pPr>%s</w:pPr>" % ppr
    if rpr:
        s += "<w:rPr>%s</w:rPr>" % rpr
    return s + "</w:style>"


def _titre_xml(n, taille):
    return _style_xml("Heading%d" % n, "heading %d" % n, base="Normal", suivant="Normal", prio=9,
                      ppr='<w:keepNext/><w:keepLines/><w:spacing w:before="%d" w:after="120"/><w:jc w:val="left"/>'
                          '<w:outlineLvl w:val="%d"/>' % (360 if n == 1 else 240, n - 1),
                      rpr='<w:b/><w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (taille, taille))


STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="%s">'
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/>'
    '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="fr-BE" w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr>'
    '</w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="276" w:lineRule="auto"/></w:pPr>'
    '</w:pPrDefault></w:docDefaults>' % W_NS
    + '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
      '<w:pPr><w:jc w:val="both"/></w:pPr></w:style>'
    + '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="Default Paragraph Font"/>'
      '<w:uiPriority w:val="1"/><w:semiHidden/><w:unhideWhenUsed/></w:style>'
    + _titre_xml(1, 28) + _titre_xml(2, 26) + _titre_xml(3, 24) + _titre_xml(4, 22)
    + _style_xml("TitrePlan", "Titre du plan", base="Normal", ppr='<w:spacing w:after="240"/><w:jc w:val="center"/>',
                 rpr='<w:b/><w:sz w:val="32"/><w:szCs w:val="32"/>')
    + _style_xml("Aide", "Aide Probasile", base="Normal", ppr='<w:spacing w:after="120"/>',
                 rpr='<w:i/><w:color w:val="7A7A7A"/>')
    + _style_xml("Repere", "Repère Probasile", base="Normal", ppr='<w:ind w:left="576"/>',
                 rpr='<w:color w:val="08738F"/><w:sz w:val="18"/><w:szCs w:val="18"/>')
    + _style_xml("TOCHeading", "TOC Heading", base="Normal", suivant="Normal", prio=39,
                 ppr='<w:spacing w:before="240" w:after="120"/>', rpr='<w:b/><w:sz w:val="28"/><w:szCs w:val="28"/>')
    + "".join(_style_xml("TOC%d" % n, "toc %d" % n, base="Normal", suivant="Normal", qformat=False, prio=39,
                         ppr='<w:ind w:left="%d"/><w:jc w:val="left"/>' % (220 * (n - 1))) for n in range(1, 5))
    + _style_xml("FootnoteText", "footnote text", base="Normal", qformat=False, prio=99,
                 ppr='<w:jc w:val="both"/>', rpr='<w:sz w:val="18"/><w:szCs w:val="18"/>')
    + _style_xml("FootnoteReference", "footnote reference", typ="character", qformat=False, prio=99,
                 rpr='<w:vertAlign w:val="superscript"/>')
    + _style_xml("Hyperlink", "Hyperlink", typ="character", qformat=False, prio=99,
                 rpr='<w:color w:val="0563C1"/><w:u w:val="single"/>')
    + "</w:styles>")


def _core(titre):
    maintenant = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    esc = (titre or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties '
            'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>%s</dc:title><dc:creator>Probasile</dc:creator>'
            '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified></cp:coreProperties>'
            % (esc, maintenant, maintenant))


APP = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties '
       'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
       '<Application>Probasile</Application></Properties>')

SECTION = ('<w:sectPr xmlns:w="%s"><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1417" w:right="1417" '
           'w:bottom="1417" w:left="1417" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>' % W_NS)


def ecrire_docx(chemin, elements, titre=""):
    """Nouveau document Word : elements = liste de w:p / w:tbl."""
    doc = etree.fromstring(('<w:document xmlns:w="%s" xmlns:r="%s"><w:body/></w:document>' % (W_NS, R_NS)).encode())
    body = doc.find(W + "body")
    for e in elements:
        body.append(e)
    body.append(etree.fromstring(SECTION.encode()))
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", etree.tostring(doc, xml_declaration=True, encoding="UTF-8", standalone=True))
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/settings.xml", SETTINGS)
        z.writestr("word/footnotes.xml", FOOTNOTES)
        z.writestr("docProps/core.xml", _core(titre))
        z.writestr("docProps/app.xml", APP)
    return chemin


def styles_du_modele():
    return _noms_styles(etree.fromstring(STYLES.encode()))


def _noms_styles(styles_root):
    out = {}
    for st in styles_root.findall(W + "style"):
        n = st.find(W + "name")
        if n is not None and st.get(W + "styleId"):
            out.setdefault(n.get(W + "val", "").lower(), st.get(W + "styleId"))
    return out


def odt_vers_docx(chemin_odt, chemin_docx=None, supprimer_odt=False):
    """Convertit un .odt créé par Probasile en .docx (même nom, extension .docx par défaut)."""
    chemin_docx = chemin_docx or os.path.splitext(chemin_odt)[0] + ".docx"
    with zipfile.ZipFile(chemin_odt) as z:
        root = etree.fromstring(z.read("content.xml"))
    auto = root.find("office:automatic-styles", R.NS)
    styles_auto = {s.get(ODT_STYLE + "name"): s for s in (auto if auto is not None else [])}
    conv = Convertisseur(styles_auto, styles_du_modele())
    body = root.find("office:body/office:text", R.NS)
    elements = []
    for el in body:
        elements += conv.elements(el)
    titre = ""
    for el in body.iter(ODT_T + "p"):
        titre = "".join(el.itertext()).strip()
        if titre:
            break
    ecrire_docx(chemin_docx, elements, titre)
    if supprimer_odt:
        try:
            os.remove(chemin_odt)
        except OSError:
            pass
    return chemin_docx


# ---------------------------------------------------------------------------
# Lecture du texte d'un paragraphe Word
# ---------------------------------------------------------------------------
IGNORER = {W + t for t in ("pPr", "rPr", "del", "moveFrom", "drawing", "pict", "object", "instrText", "fldChar",
                           "delText", "txbxContent", "commentReference", "annotationRef", "lastRenderedPageBreak")}
IGNORER.add("{%s}AlternateContent" % MC_NS)


def _atomes(p):
    """[(type, élément, texte)] : type = 'texte' (w:t), 'petit' (tabulation, saut de ligne…), 'note' (appel de note)."""
    out = []

    def visiter(el):
        for ch in el:
            tag = ch.tag
            if not isinstance(tag, str) or tag in IGNORER or tag == W + "p":
                continue
            if tag == W + "t":
                out.append(("texte", ch, ch.text or ""))
            elif tag == W + "tab":
                out.append(("petit", ch, "\t"))
            elif tag in (W + "br", W + "cr"):
                out.append(("petit", ch, "\n"))
            elif tag == W + "noBreakHyphen":
                out.append(("petit", ch, "-"))
            elif tag == W + "footnoteReference":
                out.append(("note", ch, ""))
            else:
                visiter(ch)
    visiter(p)
    return out


def texte_paragraphe(p):
    return "".join(a[2] for a in _atomes(p))


def _supprimer(p, debut, fin):
    pos = 0
    for typ, el, s in _atomes(p):
        a, b = pos, pos + len(s)
        pos = b
        if b <= debut or a >= fin or typ == "note":
            continue
        if typ == "petit":
            el.getparent().remove(el)
            continue
        i, j = max(debut, a) - a, min(fin, b) - a
        el.text = s[:i] + s[j:]
        el.set(XML_SPACE, "preserve")


def _inserer(p, offset, nouveau_run):
    """Insère un run à la position offset du texte du paragraphe (en coupant le run si nécessaire)."""
    pos = 0
    for typ, el, s in _atomes(p):
        a, b = pos, pos + len(s)
        pos = b
        if typ != "texte" or not (a <= offset <= b):
            continue
        run = el.getparent()
        if run.tag != W + "r":
            continue
        i = offset - a
        enfants = [c for c in run if c.tag != W + "rPr"]
        k = enfants.index(el)
        if i == len(s) and k == len(enfants) - 1:
            run.addnext(nouveau_run)
            return
        if i == 0 and k == 0:
            run.addprevious(nouveau_run)
            return
        r2 = etree.Element(W + "r")
        rpr = run.find(W + "rPr")
        if rpr is not None:
            r2.append(copy.deepcopy(rpr))
        t2 = etree.SubElement(r2, W + "t")
        t2.text = s[i:]
        t2.set(XML_SPACE, "preserve")
        for c in enfants[k + 1:]:
            r2.append(c)
        el.text = s[:i]
        el.set(XML_SPACE, "preserve")
        run.addnext(r2)
        run.addnext(nouveau_run)
        return
    p.append(nouveau_run)


def _paragraphes(body):
    return [p for p in body.iter(W + "p")]


# ---------------------------------------------------------------------------
# Paquet Word existant : notes, styles, relations
# ---------------------------------------------------------------------------
class Paquet:
    def __init__(self, chemin):
        with zipfile.ZipFile(chemin) as z:
            self.fichiers = {n: z.read(n) for n in z.namelist()}
        self.doc = etree.fromstring(self.fichiers["word/document.xml"])
        self.body = self.doc.find(W + "body")
        self.styles = etree.fromstring(self.fichiers["word/styles.xml"]) if "word/styles.xml" in self.fichiers else None
        self.rels = etree.fromstring(self.fichiers.get("word/_rels/document.xml.rels") or
                                     ('<Relationships xmlns="%s"/>' % PR_NS).encode())
        self.ct = etree.fromstring(self.fichiers["[Content_Types].xml"])
        self._notes()
        self.noms = _noms_styles(self.styles) if self.styles is not None else {}

    # --- notes de bas de page ------------------------------------------------------------------
    def _notes(self):
        cible = None
        for r in self.rels:
            if r.get("Type") == REL_FOOTNOTES:
                cible = r.get("Target")
        if cible:
            cible = cible.lstrip("/")
            self.chemin_notes = cible if cible.startswith("word/") else "word/" + cible
        else:
            self.chemin_notes = "word/footnotes.xml"
            ids = {r.get("Id") for r in self.rels}
            n = 1
            while "rId%d" % n in ids:
                n += 1
            r = etree.SubElement(self.rels, "{%s}Relationship" % PR_NS)
            r.set("Id", "rId%d" % n)
            r.set("Type", REL_FOOTNOTES)
            r.set("Target", "footnotes.xml")
        if self.chemin_notes in self.fichiers:
            self.notes = etree.fromstring(self.fichiers[self.chemin_notes])
        else:
            self.notes = etree.fromstring(FOOTNOTES.encode())
            self._parametres_notes()
        if not any(o.get("PartName") == "/" + self.chemin_notes for o in self.ct):
            o = etree.SubElement(self.ct, "{%s}Override" % CT_NS)
            o.set("PartName", "/" + self.chemin_notes)
            o.set("ContentType", CT_FOOTNOTES)
        rels_notes = os.path.dirname(self.chemin_notes) + "/_rels/" + os.path.basename(self.chemin_notes) + ".rels"
        self.chemin_rels_notes = rels_notes
        self.rels_notes = etree.fromstring(self.fichiers.get(rels_notes) or ('<Relationships xmlns="%s"/>' % PR_NS).encode())
        ids = [int(n.get(W + "id")) for n in self.notes.findall(W + "footnote") if (n.get(W + "id") or "").lstrip("-").isdigit()]
        self.prochain_id = max([0] + ids) + 1

    def _parametres_notes(self):
        """Nouvelles notes : déclare les séparateurs dans settings.xml, à la place exigée par Word."""
        if "word/settings.xml" not in self.fichiers:
            return
        st = etree.fromstring(self.fichiers["word/settings.xml"])
        if st.find(W + "footnotePr") is not None:
            return
        fp = etree.Element(W + "footnotePr")
        for i in ("-1", "0"):
            etree.SubElement(fp, W + "footnote").set(W + "id", i)
        apres = ("endnotePr", "compat", "docVars", "rsids", "mathPr", "attachedSchema", "themeFontLang",
                 "clrSchemeMapping", "doNotIncludeSubdocsInStats", "doNotAutoCompressPictures", "forceUpgrade",
                 "captions", "readModeInkLockDown", "smartTagType", "schemaLibrary", "shapeDefaults",
                 "doNotEmbedSmartTags", "decimalSymbol", "listSeparator")
        for ch in st:
            local = etree.QName(ch).localname
            if local in apres:
                ch.addprevious(fp)
                break
        else:
            st.append(fp)
        self.fichiers["word/settings.xml"] = etree.tostring(st, xml_declaration=True, encoding="UTF-8", standalone=True)

    def style(self, nom, defaut_xml):
        """styleId du style Word portant ce nom (« footnote text »…) ; créé s'il manque."""
        if nom in self.noms:
            return self.noms[nom]
        if self.styles is None:
            return None
        el = etree.fromstring(('<w:root xmlns:w="%s">%s</w:root>' % (W_NS, defaut_xml)).encode())[0]
        sid = el.get(W + "styleId")
        if sid in set(self.noms.values()):
            sid = sid + "Probasile"
            el.set(W + "styleId", sid)
        self.styles.append(el)
        self.noms[nom] = sid
        return sid

    def lien(self, url):
        ids = {r.get("Id") for r in self.rels_notes}
        n = 1
        while "rId%d" % n in ids:
            n += 1
        r = etree.SubElement(self.rels_notes, "{%s}Relationship" % PR_NS)
        r.set("Id", "rId%d" % n)
        r.set("Type", REL_HYPERLINK)
        r.set("Target", url)
        r.set("TargetMode", "External")
        return "rId%d" % n

    def nouvelle_note(self, morceaux):
        sid_texte = self.style("footnote text", _style_xml("FootnoteText", "footnote text", base="Normal",
                                                            qformat=False, rpr='<w:sz w:val="18"/><w:szCs w:val="18"/>'))
        sid_appel = self.style("footnote reference", _style_xml("FootnoteReference", "footnote reference",
                                                                 typ="character", qformat=False,
                                                                 rpr='<w:vertAlign w:val="superscript"/>'))
        sid_lien = self.style("hyperlink", _style_xml("Hyperlink", "Hyperlink", typ="character", qformat=False,
                                                       rpr='<w:color w:val="0563C1"/><w:u w:val="single"/>'))
        i = self.prochain_id
        self.prochain_id += 1
        note = w("footnote", {"id": i}, self.notes)
        p = w("p", parent=note)
        _ppr(p, sid_texte)
        r = w("r", parent=p)
        _rpr({"rStyle": sid_appel} if sid_appel else {"sup": True}, r)
        w("footnoteRef", parent=r)
        _run(p, " ")
        for txt, st in morceaux:
            if not txt:
                continue
            if txt == "lien":
                h = w("hyperlink", parent=p)
                h.set("{%s}id" % R_NS, self.lien(st))
                _run(h, st, {"rStyle": sid_lien} if sid_lien else {"color": "0563C1", "u": True})
            else:
                _run(p, txt, {"i": True} if st == "it" else None)
        appel = etree.Element(W + "r")
        _rpr({"rStyle": sid_appel} if sid_appel else {"sup": True}, appel)
        w("footnoteReference", {"id": i}, appel)
        return appel

    def ecrire(self, chemin):
        f = dict(self.fichiers)
        f["word/document.xml"] = etree.tostring(self.doc, xml_declaration=True, encoding="UTF-8", standalone=True)
        f[self.chemin_notes] = etree.tostring(self.notes, xml_declaration=True, encoding="UTF-8", standalone=True)
        if len(self.rels_notes):
            f[self.chemin_rels_notes] = etree.tostring(self.rels_notes, xml_declaration=True, encoding="UTF-8",
                                                       standalone=True)
        f["word/_rels/document.xml.rels"] = etree.tostring(self.rels, xml_declaration=True, encoding="UTF-8",
                                                           standalone=True)
        f["[Content_Types].xml"] = etree.tostring(self.ct, xml_declaration=True, encoding="UTF-8", standalone=True)
        if self.styles is not None:
            f["word/styles.xml"] = etree.tostring(self.styles, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
            for nom in ["[Content_Types].xml"] + [n for n in f if n != "[Content_Types].xml"]:
                z.writestr(nom, f[nom])


# ---------------------------------------------------------------------------
# Blocs de la bibliothèque dans un texte Word
# ---------------------------------------------------------------------------
def developper_blocs(paquet, chemin_biblio, variables):
    import bibliotheque as B
    biblio = B.Bibliotheque(chemin_biblio)
    tmp = etree.fromstring(R._gabarit_contenu().encode("utf-8"))
    n, manquants, deja = 0, [], {}
    conv = None
    for p in list(_paragraphes(paquet.body)):
        m = re.fullmatch(r"\s*\[\[\s*BLOC\s+(.+?)\s*\]\]\s*", texte_paragraphe(p))
        if not m:
            continue
        b = biblio.trouver(m.group(1))
        if b is None:
            manquants.append(m.group(1))
            continue
        elements_odt = biblio.copier(b, tmp, variables, deja)
        auto = tmp.find("office:automatic-styles", R.NS)
        conv = Convertisseur({s.get(ODT_STYLE + "name"): s for s in auto}, paquet.noms)
        for el in elements_odt:
            for x in conv.elements(el):
                p.addprevious(x)
        p.getparent().remove(p)
        n += 1
    return n, manquants


# ---------------------------------------------------------------------------
# Génération des notes et des annexes
# ---------------------------------------------------------------------------
def generer_docx(chemin, sources, dossier_sortie=None, pdf_annexes=True, tampon=True, log=print, bibliotheque=None,
                 variables=None, tout_annexer=True):
    res = R.Resultat()
    base = os.path.splitext(os.path.basename(chemin))[0]
    dossier_sortie = dossier_sortie or os.path.dirname(os.path.abspath(chemin))
    os.makedirs(dossier_sortie, exist_ok=True)
    pq = Paquet(chemin)
    if bibliotheque and os.path.exists(bibliotheque):
        n_b, manquants = developper_blocs(pq, bibliotheque, variables or {})
        if n_b:
            log("  %d bloc(s) de la bibliothèque inséré(s)" % n_b)
        for m_ in manquants:
            res.problemes.append("Bloc introuvable dans la bibliothèque : « %s »." % m_)
    n_sugg = 0
    for p in list(_paragraphes(pq.body)):
        if R.ligne_d_aide(texte_paragraphe(p)) and p.getparent() is not None:
            p.getparent().remove(p)
            n_sugg += 1
    if n_sugg:
        log("  %d ligne(s) d’aide du plan retirée(s) (suggestions bleues, mode d’emploi)" % n_sugg)

    evenements = []
    for p in _paragraphes(pq.body):
        texte, pos, evs = "", 0, []
        for typ, el, s in _atomes(p):
            if typ == "note":
                evs.append((pos, pos, pos, None))
            texte += s
            pos += len(s)
        for m in R.RE_REPERE.finditer(texte):
            if re.match(r"\s*BLOC\s", m.group(1)):
                continue
            evs.append((m.start(), m.start(), m.end(), R.analyser_repere(m.group(1))))
        for o, a, b, an in sorted(evs, key=lambda e: e[0]):
            evenements.append((p, a, b, an))

    contenus = R.calculer_notes(evenements, sources, tout_annexer, res)

    index_para = None
    par_para = {}
    for (p, a, b, an), c in zip(evenements, contenus):
        par_para.setdefault(id(p), (p, []))[1].append((a, b, an, c))
    # numéros attribués dans l'ordre du document : on crée les notes dans cet ordre, puis on insère à rebours
    appels = {}
    for (p, a, b, an), c in zip(evenements, contenus):
        if an is not None and c != "INDEX":
            appels[(id(p), a)] = pq.nouvelle_note(c)
            res.notes += 1
    for p, evs in par_para.values():
        for a, b, an, c in sorted(evs, key=lambda e: -e[0]):
            if an is None:
                continue
            _supprimer(p, a, b)
            if c == "INDEX":
                index_para = p
                continue
            _inserer(p, a, appels[(id(p), a)])

    if res.annexes:
        lignes = ["Annexe %d : %s" % (no, R.entree_index(s)) for no, s in res.annexes]
        if index_para is None:
            ancre = etree.Element(W + "p")
            _ppr(ancre, pq.noms.get("heading 1"))
            _run(ancre, "Index des annexes", None if pq.noms.get("heading 1") else {"b": True})
            sect = pq.body.find(W + "sectPr")
            if sect is not None:
                sect.addprevious(ancre)
            else:
                pq.body.append(ancre)
            ppr = None
        else:
            ancre = index_para
            ppr = index_para.find(W + "pPr")
        for l in lignes:
            np_ = etree.Element(W + "p")
            if ppr is not None:
                np_.append(copy.deepcopy(ppr))
            _run(np_, l)
            ancre.addnext(np_)
            ancre = np_
        if index_para is not None and not texte_paragraphe(index_para).strip():
            index_para.getparent().remove(index_para)

    res.odt = os.path.join(dossier_sortie, base + "_notes.docx")
    pq.ecrire(res.odt)
    log("  Document avec notes : %s (%d note(s) créée(s), %d annexe(s))" % (res.odt, res.notes, len(res.annexes)))
    R.finir(res, chemin, dossier_sortie, base, pdf_annexes, tampon, log)
    return res
