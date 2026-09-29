# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module jurisprudence de collecte.py

- Cour eur. D.H. (HUDOC) : recherche automatique filtrée par articles de la Convention
  (tous / au moins un), État défendeur, mots-clés, type (arrêts, décisions), période.
- C.J.U.E. (Cellar / EUR-Lex) : arrêts qui citent ou interprètent un ou plusieurs actes
  (directive qualification, règlement 2024/1347, Charte…), filtrés par articles.
- Cour constitutionnelle : parcours des arrêts d'une ou plusieurs années, filtrés par
  articles (et texte de référence) dans le texte.
- Import par référence : ECLI, « req. n° 30696/09 », « C-391/16 », « C. const. 23/2021 »,
  « C.E. 248.270 », « C.C.E. 212 381 », ECLI de la Cour de cassation, lien ou fichier.
- Chaque arrêt reçoit une fiche avec une citation mise en forme :
  Cour eur. D.H. (Gde Ch.), arrêt M.S.S. c. Belgique et Grèce, 21 janvier 2011, req. n° 30696/09
  C.J.U.E. (Gde Ch.), arrêt M c. Ministerstvo vnitra…, 14 mai 2019, aff. jointes C-391/16…, EU:C:2019:403
  C. const., 18 février 2021, n° 23/2021      C.E., 12 mai 2020, n° 248.270
  C.C.E., 16 novembre 2018, n° 212 381         Cass., 14 mai 2019, P.19.0123.N
"""
import csv
import datetime as dt
import json
import os
import re
import time
import urllib.parse

import collecte as C

CAT = "Jurisprudence"
SOUS = {"Cour européenne des droits de l’homme": "CEDH", "Cour de justice de l’Union européenne": "CJUE",
        "Cour constitutionnelle": "Cour_constitutionnelle", "Conseil d’État": "Conseil_d_Etat",
        "Conseil du contentieux des étrangers": "CCE", "Cour de cassation": "Cour_de_cassation",
        "Cour internationale de Justice": "CIJ"}
for _c in ("Comité contre la torture", "Comité des droits de l’homme"):
    SOUS["ONU, " + _c] = "Comites_ONU"

# ---------------------------------------------------------------------------
# Articles : saisie et filtres
# ---------------------------------------------------------------------------


# Textes de référence : code -> (libellé, formulations reconnues dans les décisions).
# Les formulations sont comparées après normalisation (minuscules, sans accents ni ponctuation).
TEXTES = {
    "CEDH": ("Convention européenne des droits de l’homme",
             ["convention europeenne des droits de l homme", "convention europeenne de sauvegarde",
              "convention de sauvegarde des droits de l homme", "cedh", "convention europeenne", "c e d h",
              "european convention on human rights", "echr"]),
    "CAT": ("Convention contre la torture",
            ["convention contre la torture", "convention des nations unies contre la torture",
             "convention against torture", "cat"]),
    "GENEVE": ("Convention de Genève (statut des réfugiés)",
               ["convention relative au statut des refugies", "convention de geneve", "convention de 1951",
                "refugee convention", "convention relating to the status of refugees"]),
    "PIDCP": ("Pacte international relatif aux droits civils et politiques",
              ["pacte international relatif aux droits civils et politiques", "pidcp", "pacte relatif aux droits civils",
               "covenant on civil and political rights", "iccpr", "du pacte"]),
    "PIDESC": ("Pacte international relatif aux droits économiques, sociaux et culturels",
               ["pacte international relatif aux droits economiques", "pidesc", "icescr"]),
    "CIDE": ("Convention relative aux droits de l’enfant",
             ["convention relative aux droits de l enfant", "convention internationale relative aux droits de l enfant",
              "convention internationale des droits de l enfant", "cide", "convention on the rights of the child"]),
    "CEDAW": ("Convention sur l’élimination de la discrimination à l’égard des femmes",
              ["discrimination a l egard des femmes", "cedaw"]),
    "CERD": ("Convention sur l’élimination de la discrimination raciale",
             ["discrimination raciale", "cerd"]),
    "CRPD": ("Convention relative aux droits des personnes handicapées",
             ["droits des personnes handicapees", "crpd"]),
    "CHARTE": ("Charte des droits fondamentaux de l’UE",
               ["charte des droits fondamentaux", "de la charte", "charter of fundamental rights"]),
    "CONST": ("Constitution belge", ["de la constitution", "constitution"]),
    "LOI1980": ("Loi du 15 décembre 1980", ["loi du 15 decembre 1980", "loi sur les etrangers"]),
    "DIR2011/95": ("Directive 2011/95/UE (qualification)", ["directive 2011 95", "2011 95 ue", "directive qualification"]),
    "REG2024/1347": ("Règlement (UE) 2024/1347 (qualification)", ["2024 1347", "reglement qualification"]),
    "DIR2013/32": ("Directive 2013/32/UE (procédures)", ["directive 2013 32", "2013 32 ue", "directive procedures"]),
    "REG2024/1348": ("Règlement (UE) 2024/1348 (procédure)", ["2024 1348"]),
    "DIR2008/115": ("Directive 2008/115/CE (retour)", ["directive 2008 115", "2008 115 ce", "directive retour"]),
    "DUBLIN": ("Règlement Dublin III (604/2013)", ["604 2013", "dublin iii", "reglement dublin"]),
    "REG2024/1351": ("Règlement (UE) 2024/1351 (gestion de l’asile et de la migration)", ["2024 1351"]),
    "REG2026/463": ("Règlement (UE) 2026/463 (pays tiers sûr)", ["2026 463"]),
    "REG2026/464": ("Règlement (UE) 2026/464 (pays d’origine sûrs de l’Union)", ["2026 464"]),
    "DIR2024/1346": ("Directive (UE) 2024/1346 (accueil)", ["2024 1346"]),
    "REG2024/1349": ("Règlement (UE) 2024/1349 (retour à la frontière)", ["2024 1349"]),
    "REG2024/1356": ("Règlement (UE) 2024/1356 (filtrage)", ["2024 1356", "reglement filtrage"]),
    "REG2024/1359": ("Règlement (UE) 2024/1359 (crise et force majeure)", ["2024 1359"]),
    "LOI-CCE-2026": ("Loi du 17 juin 2026 relative au Conseil du contentieux des étrangers",
                     ["loi du 17 juin 2026", "loi relative au conseil du contentieux des etrangers"]),
}
# mots courts reconnus après un numéro d'article : « 3 CEDH », « 33 Genève », « 3 torture »…
ALIAS = [("cedh", "CEDH"), ("echr", "CEDH"), ("europeenne", "CEDH"), ("cat", "CAT"), ("torture", "CAT"),
         ("geneve", "GENEVE"), ("refugies", "GENEVE"), ("pidcp", "PIDCP"), ("pacte", "PIDCP"), ("iccpr", "PIDCP"),
         ("pidesc", "PIDESC"), ("cide", "CIDE"), ("enfant", "CIDE"), ("cedaw", "CEDAW"), ("femmes", "CEDAW"),
         ("cerd", "CERD"), ("crpd", "CRPD"), ("charte", "CHARTE"), ("constitution", "CONST"), ("const", "CONST"),
         ("loi", "LOI1980"), ("1980", "LOI1980"), ("2011 95", "DIR2011/95"), ("qualification", "DIR2011/95"),
         ("2024 1347", "REG2024/1347"), ("2013 32", "DIR2013/32"), ("2024 1348", "REG2024/1348"),
         ("2008 115", "DIR2008/115"), ("retour", "DIR2008/115"), ("dublin", "DUBLIN"), ("604", "DUBLIN"),
         ("filtrage", "REG2024/1356")]
# numéros d'actes récents : reconnus avant les mots courts (« retour », « loi »…) de la liste ci-dessus
ALIAS[:0] = [("2024 1351", "REG2024/1351"), ("2026 463", "REG2026/463"), ("2026 464", "REG2026/464"),
             ("2024 1346", "DIR2024/1346"), ("2024 1349", "REG2024/1349"), ("2024 1356", "REG2024/1356"),
             ("2024 1359", "REG2024/1359"), ("17 juin 2026", "LOI-CCE-2026")]


def code_texte(s):
    """« Convention européenne » / « CEDH » / « DIR2011/95 » -> code ; sinon texte libre (inchangé)."""
    if not s:
        return ""
    if s in TEXTES:
        return s
    for code, (lib, _) in TEXTES.items():
        if s == lib:
            return code
    n = C.norm(s)
    for al, code in ALIAS:
        if re.search(r"(^|\s)%s(\s|$)" % re.escape(al), n):
            return code
    return s


def lire_articles(s):
    """« 3, 13 » -> ['3', '13'] ; « 3 CEDH, 33 Genève ; P1-1 » -> ['3 CEDH', '33 GENEVE', 'P1-1'].
    Le texte indiqué après un numéro l'emporte sur le texte choisi dans la liste."""
    out = []
    for morceau in re.split(r"[,;]| et ", s or ""):
        morceau = morceau.strip()
        m = re.search(r"(P\d+-\d+|\d+(?:/\d+)*(?:bis|ter|quater)?)", morceau, re.I)
        if not m:
            continue
        v = m.group(1)
        v = v.upper() if v.upper().startswith("P") else v.lower()
        reste = morceau[m.end():].strip(" .§()-")
        reste = re.sub(r"^(?:§|par\.?|paragraphe|al\.?)\s*\d+\S*\s*", "", reste, flags=re.I).strip()
        reste = re.sub(r"^(de la|du|de l.|des|de)\s+", "", reste, flags=re.I)
        code = code_texte(reste) if reste else ""
        item = ("%s %s" % (v, code)).strip() if code else v
        if item not in out:
            out.append(item)
    return out


def numero(item):
    return item.split(" ", 1)[0]


def articles_hudoc(champ):
    """Champ « article » de HUDOC (« 3;13;35-3-a;P1-1 ») -> {'3', '13', '35', 'P1-1'}."""
    res = set()
    for t in (champ or "").split(";"):
        t = t.strip()
        if not t:
            continue
        if t.upper().startswith("P"):
            res.add("-".join(t.upper().split("-")[:2]))
        else:
            res.add(re.split(r"[-+]", t)[0].lower())
    return res


def correspond(trouves, voulus, mode):
    if not voulus:
        return True
    ok = [a in trouves for a in voulus]
    return all(ok) if mode == "tous" else any(ok)


def variantes(ref):
    """Code de TEXTES ou texte libre -> liste de formulations normalisées."""
    if not ref:
        return []
    if ref in TEXTES:
        return [C.norm(v) for v in TEXTES[ref][1]]
    return [C.norm(ref)]


def articles_dans_texte(texte, voulus, reference=""):
    """Articles cités dans un texte. Chaque article doit être suivi, dans les 250 caractères, d'une
    formulation du texte visé (celui indiqué après le numéro, sinon « reference » : code de TEXTES
    ou texte libre). Sans texte visé, la simple mention « article N » suffit."""
    t = C.norm(texte)
    trouves = set()
    for a in voulus:
        num = C.norm(numero(a))
        ref = a.split(" ", 1)[1] if " " in a else reference
        vs = variantes(code_texte(ref) if ref else "")
        for m in re.finditer(r"\b(?:article|articles|art)\s+%s\b(?!\s*[/\d])" % re.escape(num), t):
            suite = t[m.end():m.end() + 250]
            if not vs or any(re.search(r"(^|\s)%s(\s|$)" % re.escape(v), suite) for v in vs):
                trouves.add(a)
                break
    return trouves


# ---------------------------------------------------------------------------
# Mise en forme
# ---------------------------------------------------------------------------
PETITS = {"c.", "v.", "et", "and", "de", "du", "des", "la", "le", "les", "d'", "l'", "d’", "l’", "en", "of", "the"}


def casse_titre(s):
    """« M.S.S. C. BELGIQUE ET GRÈCE » -> « M.S.S. c. Belgique et Grèce »."""
    mots = []
    for i, w in enumerate(s.split()):
        lw = w.lower()
        if i and lw in PETITS:
            mots.append(lw)
        elif re.fullmatch(r"([A-Z]\.)+[A-Z]?\.?", w) or (len(w) <= 4 and "." in w and w.isupper()):
            mots.append(w)  # initiales : M.S.S., N.D.
        elif w.isupper():
            mots.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
        else:
            mots.append(w)
    return " ".join(mots)


def nom_affaire_hudoc(docname):
    n = re.sub(r"^(AFFAIRE|CASE OF|AFF\.)\s+", "", (docname or "").strip(), flags=re.I)
    n = re.sub(r"\s*\((?:no|n°)\s*\d+\)\s*$", lambda m: " " + m.group(0).strip().lower(), n)
    n = re.sub(r"\bV\.\s", "c. ", n, flags=re.I)
    n = re.sub(r"\bC\.\s", "c. ", n)
    return casse_titre(n)


def date_iso_fr(s):
    try:
        return C.date_fr(dt.date.fromisoformat((s or "")[:10]))
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# HUDOC
# ---------------------------------------------------------------------------
HUDOC_Q = "https://hudoc.echr.coe.int/app/query/results"
# HUDOC refuse (403) les requêtes qui ne ressemblent pas à celles de son propre site :
# on reprend les en-têtes qu'envoie le navigateur depuis la page de recherche.
HUDOC_ENTETES = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "fr-BE,fr;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://hudoc.echr.coe.int/fre",
}
HUDOC_ENTETES_DOC = {k: v for k, v in HUDOC_ENTETES.items() if k != "X-Requested-With"}
HUDOC_ENTETES_DOC["Accept"] = "application/pdf,application/octet-stream,*/*"
HUDOC_PDF = "https://hudoc.echr.coe.int/app/conversion/pdf/?library=ECHR&id={id}&filename={fn}.pdf"
HUDOC_DOCX = "https://hudoc.echr.coe.int/app/conversion/docx/?library=ECHR&id={id}&filename={fn}.docx"
HUDOC_PAGE = "https://hudoc.echr.coe.int/fre?i={id}"
HUDOC_SELECT = ("itemid,docname,appno,kpdate,article,respondent,languageisocode,doctype,"
                "documentcollectionid,documentcollectionid2,importance,ecli")


def requete_hudoc(articles, mode, etat="", mots="", depuis=None, types=("JUDGMENTS",), strict=True, extra=""):
    parts = ["contentsitename:ECHR", "(NOT (doctype=PR OR doctype=HFCOMOLD OR doctype=HECOMOLD))"]
    if strict:
        if types:
            parts.append("(" + " OR ".join('documentcollectionid2="%s"' % t for t in types) + ")")
        if articles:
            j = " AND " if mode == "tous" else " OR "
            parts.append("(" + j.join('article="%s"' % a for a in articles) + ")")
        if etat:
            parts.append('(respondent="%s")' % etat.upper())
        if depuis:
            parts.append('(kpdate>="%d-01-01T00:00:00.0Z")' % int(depuis))
    if mots:
        parts.append("(" + " ".join('"%s"' % m.strip('"') if " " in m else m for m in mots.split()) + ")")
    if extra:
        parts.append(extra)
    return " AND ".join(parts)


class Jurisprudence:
    def __init__(self, col):
        self.col = col  # Collecteur (réseau, journal, arrêt, mode liens seulement)
        self.log = col.log

    # -- enregistrement commun -------------------------------------------------
    def _fiche(self, depot, id_, juridiction, titre, cote, date, url, citation, articles, contenu=None, ext="pdf",
               sous_dossier="", nom=""):
        if depot.connu(id_) and (depot.a_fichier(id_) or self.col.liens_seulement or contenu is None):
            return False
        fichier = ""
        if contenu is not None and not self.col.liens_seulement:
            chemin = depot.chemin(CAT, sous_dossier or SOUS.get(juridiction) or C.slug(juridiction, 30),
                                  "%s.%s" % (C.slug(nom or cote or titre, 90), ext))
            with open(chemin, "wb") as f:
                f.write(contenu)
            fichier = C.os.path.relpath(chemin, depot.racine)
        elif self.col.liens_seulement and url:
            depot.liens.append((citation, url))
        depot.ajouter({"id": id_, "categorie": CAT, "auteur": juridiction, "titre": titre, "cote": cote,
                       "date": date, "url": url, "consulte_le": self.col.aujourdhui, "fichier": fichier,
                       "citation": citation, "articles": ", ".join(sorted(articles, key=_cle_art))})
        self.log("  + %s" % citation)
        return True

    # -- HUDOC -------------------------------------------------------------------
    def hudoc(self, depot, articles, mode, etat="", mots="", depuis=None, types=("JUDGMENTS",),
              langues=("FRE", "ENG"), grande_chambre=False, max_docs=100, extra=""):
        voulus = [numero(a) for a in articles]
        resultats = None
        self._hudoc_403 = False
        for strict in (True, False):
            q = requete_hudoc(voulus, mode, etat, mots, depuis, types, strict, extra)
            resultats = self._hudoc_pages(q, max_docs * (3 if not strict else 2))
            if resultats is None:
                if self._hudoc_403:
                    break
                continue
            if resultats or not strict:
                break
            self.log("  HUDOC : aucun résultat avec la requête complète, nouvel essai avec filtrage local…")
        if not resultats:
            if self._hudoc_403:
                url = url_hudoc_manuelle(voulus, etat, mots, types, langues, grande_chambre)
                self.log("  Recherche toute prête à ouvrir dans votre navigateur (mêmes critères) :\n    %s" % url)
                self.lien_hudoc = url
            else:
                self.log("  HUDOC : aucun résultat.")
            return 0
        # filtrage local (articles, types, langue, État, date, Grande Chambre)
        retenus = {}
        for c in resultats:
            coll = (c.get("documentcollectionid2") or c.get("documentcollectionid") or "").upper()
            if types and not any(t in coll for t in types):
                continue
            if grande_chambre and "GRANDCHAMBER" not in coll:
                continue
            if not correspond(articles_hudoc(c.get("article")), voulus, mode):
                continue
            if etat and etat.upper() not in (c.get("respondent") or "").upper():
                continue
            if depuis and (c.get("kpdate") or "0")[:4] < str(depuis):
                continue
            lang = (c.get("languageisocode") or "").upper()
            if langues and lang not in langues:
                continue
            cle = ((c.get("appno") or c.get("docname") or ""), (c.get("kpdate") or "")[:10])
            if cle not in retenus or (lang == "FRE" and retenus[cle].get("languageisocode", "").upper() != "FRE"):
                retenus[cle] = c
        self.log("  HUDOC : %d affaire(s) retenue(s) après filtrage" % len(retenus))
        n = 0
        for i, c in enumerate(sorted(retenus.values(), key=lambda c: c.get("kpdate", ""), reverse=True), 1):
            if i > max_docs:
                self.log("  (limite de %d atteinte)" % max_docs)
                break
            self.col.progres(i, min(len(retenus), max_docs))
            if self._doc_hudoc(depot, c, voulus):
                n += 1
        return n

    def _hudoc_get(self, url):
        """Requête HUDOC avec les en-têtes d'un navigateur ; au premier appel, visite de la page
        d'accueil pour obtenir les cookies de session."""
        if not getattr(self, "_hudoc_pret", False):
            self._hudoc_pret = True
            try:
                self.col._verif()
                self.col.s.get("https://hudoc.echr.coe.int/fre", timeout=60,
                               headers={k: v for k, v in HUDOC_ENTETES.items() if k in ("User-Agent", "Accept-Language")})
            except Exception:
                pass
        self.col._verif()
        time.sleep(C.PAUSE)
        return self.col.s.get(url, timeout=60, headers=HUDOC_ENTETES)

    def _hudoc_pages(self, q, maximum):
        out, start = [], 0
        while start < maximum:
            params = {"query": q, "select": HUDOC_SELECT, "sort": "kpdate Descending",
                      "start": start, "length": min(500, maximum - start)}
            try:
                r = self._hudoc_get(HUDOC_Q + "?" + urllib.parse.urlencode(params))
            except C.Arret:
                raise
            except Exception as e:
                self.log("  ! HUDOC : %s" % e)
                return None
            if r.status_code != 200:
                self._hudoc_403 = r.status_code == 403
                self.log("  ! HUDOC a répondu %s%s" % (r.status_code, " (accès refusé au programme : utilisez le bouton "
                         "« HUDOC » des recherches manuelles, puis importez le PDF téléchargé)" if r.status_code == 403 else ""))
                return None
            try:
                data = r.json() if hasattr(r, "json") else json.loads(r.text)
            except Exception:
                self.log("  ! HUDOC : réponse illisible")
                return None
            res = [x.get("columns", {}) for x in data.get("results", [])]
            out.extend(res)
            total = int(data.get("resultcount", len(out)) or 0)
            start += len(res)
            if not res or start >= total:
                break
        return out

    def _doc_hudoc(self, depot, c, voulus):
        itemid = c.get("itemid", "")
        coll = (c.get("documentcollectionid2") or c.get("documentcollectionid") or "").upper()
        gc = "GRANDCHAMBER" in coll
        genre = "décision" if "DECISIONS" in coll and "JUDGMENTS" not in coll else "arrêt"
        nom = nom_affaire_hudoc(c.get("docname", ""))
        date = date_iso_fr(c.get("kpdate"))
        appnos = [a for a in (c.get("appno") or "").split(";") if a]
        req = ("req. n° " + appnos[0]) if len(appnos) == 1 else ("req. n°s " + ", ".join(appnos[:4]) + (" et al." if len(appnos) > 4 else "")) if appnos else ""
        citation = "Cour eur. D.H.%s, %s %s, %s%s" % (" (Gde Ch.)" if gc else "", genre, nom, date, (", " + req) if req else "")
        id_ = "JUR-ECHR-" + (appnos[0].replace("/", "-") if appnos else itemid) + "-" + (c.get("kpdate") or "")[:10]
        contenu, ext = None, "pdf"
        if not self.col.liens_seulement and not depot.a_fichier(id_):
            fn = urllib.parse.quote(C.slug(nom, 60))
            res = self.col._fichier(HUDOC_PDF.format(id=itemid, fn=fn), headers=HUDOC_ENTETES_DOC) or \
                self.col._fichier(HUDOC_DOCX.format(id=itemid, fn=fn), headers=HUDOC_ENTETES_DOC)
            if res:
                ext, contenu = res
        return self._fiche(depot, id_, "Cour européenne des droits de l’homme", nom, c.get("ecli") or ", ".join(appnos),
                           date, HUDOC_PAGE.format(id=itemid), citation,
                           articles_hudoc(c.get("article")) & set(voulus) if voulus else articles_hudoc(c.get("article")),
                           contenu, ext, "CEDH", "%s_%s" % ((c.get("kpdate") or "")[:10], nom))

    # -- CJUE ------------------------------------------------------------------------
    def cjue(self, depot, actes, articles, mode, reference="", mots="", depuis=None, max_docs=50,
             relation="cite"):
        if not actes:
            self.log("  C.J.U.E. : aucun acte choisi (ex. directive 2011/95 = 32011L0095).")
            return 0
        rel = "cdm:work_cites_work|cdm:case-law_interpretes_resource_legal" if relation == "cite" else "cdm:case-law_interpretes_resource_legal"
        filtre_actes = " || ".join('str(?ac) = "%s"' % a for a in actes)
        q = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?celex ?date ?ecli ?titre WHERE {
  ?w cdm:resource_legal_id_celex ?celex .
  FILTER(regex(str(?celex), "^6[0-9]{4}CJ"))
  ?w cdm:work_date_document ?date .
  %s
  ?w %s ?a .
  ?a cdm:resource_legal_id_celex ?ac .
  FILTER(%s)
  OPTIONAL { ?w cdm:case-law_ecli ?ecli }
  OPTIONAL { ?e cdm:expression_belongs_to_work ?w ;
                cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/FRA> ;
                cdm:expression_title ?titre }
} ORDER BY DESC(?date) LIMIT %d""" % (
            ('FILTER(?date >= "%d-01-01"^^xsd:date)' % int(depuis)) if depuis else "", rel, filtre_actes,
            max(200, max_docs * 6))
        try:
            r = self.col._get(SPARQL + "?" + urllib.parse.urlencode({"query": q, "format": "application/sparql-results+json"}))
        except C.Arret:
            raise
        except Exception as e:
            self.log("  ! Cellar (C.J.U.E.) : %s" % e)
            return 0
        if r.status_code != 200:
            self.log("  ! Cellar a répondu %s" % r.status_code)
            return 0
        try:
            rows = (r.json() if hasattr(r, "json") else json.loads(r.text))["results"]["bindings"]
        except Exception:
            self.log("  ! Cellar : réponse illisible")
            return 0
        vus, candidats = set(), []
        for b in rows:
            celex = b.get("celex", {}).get("value", "")
            if celex in vus:
                continue
            vus.add(celex)
            candidats.append({k: b.get(k, {}).get("value", "") for k in ("celex", "date", "ecli", "titre")})
        self.log("  C.J.U.E. : %d arrêt(s) citent ou interprètent le(s) acte(s) choisi(s)" % len(candidats))
        n = 0
        for i, c in enumerate(candidats, 1):
            if n >= max_docs:
                self.log("  (limite de %d atteinte)" % max_docs)
                break
            self.col.progres(i, len(candidats))
            if mots and not all(C.norm(m) in C.norm(c["titre"]) for m in mots.split()):
                texte_mots = True  # vérifié plus bas sur le texte
            else:
                texte_mots = False
            trouves = set()
            if articles or texte_mots:
                texte = self._texte_eurlex(c["celex"])
                if texte is None:
                    continue
                if texte_mots and not all(C.norm(m) in C.norm(texte) for m in mots.split()):
                    continue
                trouves = articles_dans_texte(texte, articles, reference)
                if not correspond(trouves, articles, mode):
                    continue
            if self._doc_cjue(depot, c, trouves):
                n += 1
        return n

    def _texte_eurlex(self, celex):
        try:
            r = self.col._get(EURLEX_HTML.format(celex=celex))
        except C.Arret:
            raise
        except Exception:
            return None
        if r.status_code != 200:
            return None
        return re.sub(r"<[^>]+>", " ", r.text)

    def _doc_cjue(self, depot, c, articles, id_force=None):
        celex = c["celex"]
        titre = c.get("titre", "") or ""
        chambre = " (Gde Ch.)" if re.search(r"grande chambre", titre, re.I) else ""
        affaires = re.findall(r"\b([CT]-\d+/\d+(?:\s*P)?)", titre)
        if not affaires:
            m = re.match(r"6(\d{4})CJ0*(\d+)", celex)
            if m:
                affaires = ["C-%s/%s" % (m.group(2), m.group(1)[2:])]
        parties = ""
        morceaux = [p.strip() for p in re.split(r"\s*#\s*|\.\s+(?=[A-Z0-9«])", titre) if p.strip()]
        if len(morceaux) > 1:
            parties = morceaux[1].replace(" contre ", " c. ")
            parties = re.sub(r"\s*\.$", "", parties)
            if len(parties) > 160:
                parties = parties[:157].rsplit(" ", 1)[0] + "…"
        date = date_iso_fr(c.get("date"))
        ecli = (c.get("ecli") or "").replace("ECLI:", "")
        aff = ("aff. jointes " + ", ".join(affaires[:-1]) + " et " + affaires[-1]) if len(affaires) > 1 else \
              ("aff. " + affaires[0] if affaires else "")
        cour = "C.J.C.E." if (c.get("date") or "9999")[:10] < "2009-12-01" else "C.J.U.E."  # avant Lisbonne
        citation = cour + "%s, arrêt %s%s, %s%s%s" % (chambre, parties or "", "" if parties else "", date,
                                                       (", " + aff) if aff else "", (", " + ecli) if ecli else "")
        citation = citation.replace("arrêt , ", "arrêt du ")
        id_ = id_force or "JUR-CJUE-" + celex
        contenu = None
        if not self.col.liens_seulement and not depot.a_fichier(id_):
            res = self.col._fichier(EURLEX_PDF.format(celex=celex))
            if res:
                contenu = res[1]
        return self._fiche(depot, id_, "Cour de justice de l’Union européenne", parties or titre[:150],
                           ecli or celex, date, EURLEX_PAGE.format(celex=celex), citation, articles, contenu, "pdf",
                           "CJUE", "%s_%s" % ((c.get("date") or "")[:10], "_".join(affaires) or celex))

    # -- Cour constitutionnelle -------------------------------------------------------
    def cour_constitutionnelle(self, depot, annees, articles, mode, reference="", mots="", max_docs=50):
        n = 0
        for annee in annees:
            manques, num = 0, 0
            cle_vu = "cc_vu_%d_%s" % (annee, C.slug("%s_%s_%s_%s" % ("-".join(articles), mode, reference, mots), 60))
            vus = set(depot.etat.get(cle_vu, []))
            self.log("  Cour constitutionnelle, %d : parcours des arrêts…" % annee)
            while manques < 3 and num < 400:
                num += 1
                self.col.progres(num, 250)
                id_ = "JUR-CC-%d-%03d" % (annee, num)
                if num in vus and not depot.connu(id_):
                    continue  # déjà examiné lors d'une collecte précédente, ne correspondait pas
                if depot.connu(id_):
                    manques = 0
                    continue
                url = CC_PDF.format(y=annee, n=num)
                res = self.col._fichier(url)
                if not res:
                    manques += 1
                    continue
                manques = 0
                ext, contenu = res
                texte = C.texte_pdf(contenu, pages=200)
                vus.add(num)
                depot.etat[cle_vu] = sorted(vus)
                if mots and not all(C.norm(m) in C.norm(texte) for m in mots.split()):
                    continue
                trouves = articles_dans_texte(texte, articles, reference)
                if not correspond(trouves, articles, mode):
                    continue
                date = C.date_dans_texte(texte[:1500])
                citation = "C. const., %s, n° %d/%d" % (date or "[date]", num, annee)
                objet = _objet_cc(texte)
                if self._fiche(depot, id_, "Cour constitutionnelle", objet, "ECLI:BE:GHCC:%d:ARR.%03d" % (annee, num),
                               date, url, citation, trouves, contenu, ext, "Cour_constitutionnelle",
                               "%d-%03d" % (annee, num)):
                    n += 1
                if n >= max_docs:
                    self.log("  (limite de %d atteinte)" % max_docs)
                    return n
        return n

    # -- import par référence -----------------------------------------------------------
    def importer_references(self, depot, lignes):
        self.depot_courant = depot
        n = 0
        for i, ligne in enumerate([l.strip() for l in lignes if l.strip()], 1):
            self.col.progres(i, len(lignes))
            try:
                ok = self._reference(depot, ligne)
            except C.Arret:
                raise
            except Exception as e:
                self.log("  ! %s : %s" % (ligne, e))
                ok = False
            if ok:
                n += 1
            elif ok is None:
                self.log("  ? référence non reconnue : %s" % ligne)
        return n

    def _reference(self, depot, ref):
        r = ref.strip()
        u = r.upper().replace(" ", "")
        m = SYM_COMITE.search(r.replace(" ", ""))
        if m:
            return self._comite_symbole(depot, m.group(0))
        # ECLI
        m = re.search(r"ECLI:[A-Z]{2}:[A-Z0-9]+:\d{4}:[A-Z0-9.\-]+", r, re.I)
        if m:
            e = m.group(0).upper()
            if e.startswith("ECLI:CE:ECHR"):
                return self._hudoc_ref('ecli="%s"' % e)
            if e.startswith("ECLI:EU:"):
                return self._cjue_ecli(depot, e)
            mm = re.match(r"ECLI:BE:GHCC:(\d{4}):ARR\.0*(\d+)", e)
            if mm:
                return self._cc_num(depot, int(mm.group(1)), int(mm.group(2)))
            mm = re.match(r"ECLI:BE:RVSCE:(\d{4}):ARR\.([\d.]+)", e)
            if mm:
                return self._ce_num(depot, re.sub(r"\D", "", mm.group(2)))
            mm = re.match(r"ECLI:BE:RVV:(\d{4}):ARR\.([\d.]+)", e)
            if mm:
                return self._cce_num(depot, re.sub(r"\D", "", mm.group(2)))
            if e.startswith("ECLI:BE:"):
                return self._juportal(depot, e)
        # Cour eur. D.H. : numéro de requête
        m = re.search(r"\b(\d{1,6}/\d{2})\b", r)
        if m and (re.search(r"(req|requ|cedh|d\.\s*h|echr|appl)", r, re.I) or re.fullmatch(r"\d{1,6}/\d{2}", r)):
            return self._hudoc_ref('appno:"%s"' % m.group(1))
        # C.J.U.E. : C-391/16
        m = re.search(r"\b([CT])-\s*(\d+)/(\d{2})\b", r, re.I)
        if m:
            annee = int(m.group(3))
            annee = 2000 + annee if annee < 50 else 1900 + annee
            celex = "6%d%sJ%04d" % (annee, "C" if m.group(1).upper() == "C" else "T", int(m.group(2)))
            return self._cjue_celex(depot, celex)
        # Cour constitutionnelle : 23/2021
        m = re.search(r"(c\.?\s*const|constitutionnelle|arr[eê]t)\D*(\d{1,3})\s*/\s*(\d{4})", r, re.I)
        if m:
            return self._cc_num(depot, int(m.group(3)), int(m.group(2)))
        # C.C.E. : 212 381
        m = re.search(r"(c\.?\s*c\.?\s*e|contentieux|rvv)\D*(\d{2,3}[.\s]?\d{3})", r, re.I)
        if m:
            return self._cce_num(depot, re.sub(r"\D", "", m.group(2)))
        # Conseil d'État : 248.270
        m = re.search(r"((?<![a-z.])c\.?\s*e\.|conseil d.?[ée]tat|raad van state)\D*(\d{3}[.\s]?\d{3})", r, re.I)
        if m:
            return self._ce_num(depot, re.sub(r"\D", "", m.group(2)))
        if r.lower().startswith("http"):
            return self._url(depot, r)
        return None

    def _comite_symbole(self, depot, sym):
        res = self.col._doc_onu(sym, ("fr", "en"))
        if not res:
            self.log("  ! document %s introuvable" % sym)
            return False
        url, lang, ext, contenu = res
        texte = C.texte_pdf(contenu, pages=3) if ext == "pdf" else ""
        info = reconnaitre_comite(texte, sym)
        tout = C.texte_pdf(contenu, pages=60) if ext == "pdf" else ""
        arts = articles_cites_traite(tout, info["traite"]) if tout else set()
        return self._fiche(depot, info["id"], info["juridiction"], info["titre"], sym, info["date"], url,
                           info["citation"], arts, contenu, ext, "Comites_ONU", sym.replace("/", "_"))

    def _hudoc_ref(self, clause):
        q = requete_hudoc([], "tous", strict=False, extra=clause)
        self._hudoc_403 = False
        res = self._hudoc_pages(q, 50) or []
        if not res:
            m = re.search(r'appno:"([^"]+)"', clause)
            if self._hudoc_403 and m:
                self.log("  Ouvrez l’affaire dans votre navigateur, téléchargez le PDF et importez-le :\n    %s"
                         % ("https://hudoc.echr.coe.int/fre#" + urllib.parse.quote(json.dumps({"appno": [m.group(1)]}, separators=(",", ":")),
                                                                                   safe='{}[]:,"/')))
            return False
        # une seule affaire : on garde l'arrêt (ou la décision) en français de préférence
        res.sort(key=lambda c: ((c.get("languageisocode") or "").upper() != "FRE",
                                "JUDGMENTS" not in (c.get("documentcollectionid2") or c.get("documentcollectionid") or "").upper()))
        return self._doc_hudoc(self.depot_courant, res[0], [])

    def _cjue_celex(self, depot, celex):
        q = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?date ?ecli ?titre WHERE {
  ?w cdm:resource_legal_id_celex ?c . FILTER(str(?c) = "%s")
  OPTIONAL { ?w cdm:work_date_document ?date }
  OPTIONAL { ?w cdm:case-law_ecli ?ecli }
  OPTIONAL { ?e cdm:expression_belongs_to_work ?w ;
                cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/FRA> ;
                cdm:expression_title ?titre }
} LIMIT 5""" % celex
        info = {"celex": celex, "date": "", "ecli": "", "titre": ""}
        try:
            r = self.col._get(SPARQL + "?" + urllib.parse.urlencode({"query": q, "format": "application/sparql-results+json"}))
            b = (r.json() if hasattr(r, "json") else json.loads(r.text))["results"]["bindings"]
            if b:
                info.update({k: b[0].get(k, {}).get("value", "") for k in ("date", "ecli", "titre")})
        except C.Arret:
            raise
        except Exception as e:
            self.log("  ! Cellar : %s (fiche créée sans métadonnées)" % e)
        return self._doc_cjue(depot, info, set())

    def _cjue_ecli(self, depot, ecli):
        q = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex WHERE { ?w cdm:case-law_ecli ?e . FILTER(str(?e) = "%s") ?w cdm:resource_legal_id_celex ?celex } LIMIT 1""" % ecli
        try:
            r = self.col._get(SPARQL + "?" + urllib.parse.urlencode({"query": q, "format": "application/sparql-results+json"}))
            b = (r.json() if hasattr(r, "json") else json.loads(r.text))["results"]["bindings"]
            if b:
                return self._cjue_celex(depot, b[0]["celex"]["value"])
        except C.Arret:
            raise
        except Exception as e:
            self.log("  ! Cellar : %s" % e)
        return False

    def _cc_num(self, depot, annee, num):
        url = CC_PDF.format(y=annee, n=num)
        res = self.col._fichier(url)
        if not res:
            self.log("  ! arrêt %d/%d introuvable à l’adresse %s" % (num, annee, url))
            return False
        texte = C.texte_pdf(res[1], pages=2)
        date = C.date_dans_texte(texte[:1500])
        return self._fiche(depot, "JUR-CC-%d-%03d" % (annee, num), "Cour constitutionnelle", _objet_cc(texte),
                           "ECLI:BE:GHCC:%d:ARR.%03d" % (annee, num), date, url,
                           "C. const., %s, n° %d/%d" % (date or "[date]", num, annee), set(), res[1], res[0],
                           "Cour_constitutionnelle", "%d-%03d" % (annee, num))

    def _ce_num(self, depot, num):
        url = CE_PDF.format(n=num)
        res = self.col._fichier(url)
        if not res:
            self.log("  ! arrêt du Conseil d’État n° %s introuvable" % num)
            return False
        texte = C.texte_pdf(res[1], pages=2)
        date = C.date_dans_texte(texte[:2500])
        n_aff = "%s.%s" % (num[:-3], num[-3:]) if len(num) > 3 else num
        return self._fiche(depot, "JUR-CE-" + num, "Conseil d’État", "", "n° " + n_aff, date, url,
                           "C.E., %s, n° %s" % (date or "[date]", n_aff), set(), res[1], res[0], "Conseil_d_Etat", num)

    def _cce_num(self, depot, num):
        for gabarit in CCE_PDF:
            url = gabarit.format(n=num)
            res = self.col._fichier(url)
            if res:
                break
        else:
            self.log("  ! arrêt du C.C.E. n° %s introuvable" % num)
            return False
        texte = C.texte_pdf(res[1], pages=2)
        date = C.date_dans_texte(texte[:2500])
        n_aff = "%s %s" % (num[:-3], num[-3:]) if len(num) > 3 else num
        return self._fiche(depot, "JUR-CCE-" + num, "Conseil du contentieux des étrangers", "", "n° " + n_aff, date,
                           url, "C.C.E., %s, n° %s" % (date or "[date]", n_aff), set(), res[1], res[0], "CCE", num)

    def _juportal(self, depot, ecli):
        url = JUPORTAL.format(ecli=ecli)
        juridiction = {"CASS": "Cour de cassation"}.get(ecli.split(":")[2], "Juridiction belge (%s)" % ecli.split(":")[2])
        m = re.search(r"ARR\.(\d{4})(\d{2})(\d{2})", ecli)
        date = C.date_fr(dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))) if m else ""
        abr = "Cass." if juridiction == "Cour de cassation" else juridiction
        return self._fiche(depot, "JUR-" + C.slug(ecli, 80), juridiction, "", ecli, date, url,
                           "%s, %s, %s" % (abr, date or "[date]", ecli), set(), None)

    def _url(self, depot, url):
        res = self.col._fichier(url)
        if not res:
            return False
        return self.fichier(depot, "document." + res[0], res[1], url)

    def fichier(self, depot, nom, contenu, url=""):
        """Reconnaît un arrêt importé (PDF) : juridiction, numéro, date, ECLI -> citation."""
        texte = C.texte_pdf(contenu, pages=3) if contenu[:4] == b"%PDF" else ""
        m = SYM_COMITE.search(texte.replace(" ", ""))
        if m:
            info = reconnaitre_comite(texte, m.group(0))
            tout = C.texte_pdf(contenu, pages=60)
            return self._fiche(depot, info["id"], info["juridiction"], info["titre"], m.group(0), info["date"], url,
                               info["citation"], articles_cites_traite(tout, info["traite"]), contenu,
                               C.type_fichier(contenu[:8]) or "pdf", "Comites_ONU", m.group(0).replace("/", "_"))
        info = reconnaitre(texte)
        ext = C.type_fichier(contenu[:8]) or "pdf"
        if not info:
            return None
        return self._fiche(depot, info["id"], info["juridiction"], info.get("titre", ""), info.get("cote", ""),
                           info.get("date", ""), url, info["citation"], set(), contenu, ext,
                           "", info.get("nom", C.os.path.splitext(nom)[0]))


def reconnaitre(texte):
    """Identifie un arrêt d'après le texte de ses premières pages."""
    t = texte or ""
    date = C.date_dans_texte(t[:3000])
    m = re.search(r"ECLI:[A-Z]{2}:[A-Z0-9]+:\d{4}:[A-Z0-9.\-]+", t)
    ecli = m.group(0) if m else ""
    m = re.search(r"Arr[êe]t n°\s*(\d{1,3})/(\d{4})", t)
    if "GHCC" in ecli or (m and re.search(r"Cour constitutionnelle", t, re.I)):
        if m:
            num, annee = int(m.group(1)), int(m.group(2))
            return {"id": "JUR-CC-%d-%03d" % (annee, num), "juridiction": "Cour constitutionnelle", "cote": ecli,
                    "date": date, "citation": "C. const., %s, n° %d/%d" % (date or "[date]", num, annee),
                    "nom": "%d-%03d" % (annee, num), "titre": _objet_cc(t)}
    m = re.search(r"n°\s*(\d{2,3})[ .](\d{3})\s+du\s+", t)
    if re.search(r"CONTENTIEUX DES [ÉE]TRANGERS", t, re.I) and m:
        num = m.group(1) + m.group(2)
        return {"id": "JUR-CCE-" + num, "juridiction": "Conseil du contentieux des étrangers", "cote": "n° %s %s" % m.groups(),
                "date": date, "citation": "C.C.E., %s, n° %s %s" % ((date or "[date]",) + m.groups()), "nom": num}
    m = re.search(r"n°\s*(\d{3})\.(\d{3})", t)
    if re.search(r"CONSEIL D.[ÉE]TAT", t, re.I) and m:
        num = m.group(1) + m.group(2)
        return {"id": "JUR-CE-" + num, "juridiction": "Conseil d’État", "cote": "n° %s.%s" % m.groups(), "date": date,
                "citation": "C.E., %s, n° %s.%s" % ((date or "[date]",) + m.groups()), "nom": num}
    if re.search(r"COUR DE CASSATION", t, re.I):
        m = re.search(r"\b([A-Z]\.\d{2}\.\d{4}\.[A-Z])\b", t)
        role = m.group(1) if m else ecli
        return {"id": "JUR-CASS-" + C.slug(role or date, 40), "juridiction": "Cour de cassation", "cote": role,
                "date": date, "citation": "Cass., %s, %s" % (date or "[date]", role or "[n° de rôle]"), "nom": role}
    if re.search(r"COUR INTERNATIONALE DE JUSTICE|INTERNATIONAL COURT OF JUSTICE", t, re.I):
        titre = ""
        m = re.search(r"\n([^\n]*\(([^\n]*)c\.[^\n]*\))", t)
        if m:
            titre = m.group(1).strip()
        return {"id": "JUR-CIJ-" + C.slug(titre or date, 60), "juridiction": "Cour internationale de Justice",
                "date": date, "titre": titre,
                "citation": "C.I.J., %s, %s" % (titre or "[intitulé de l’affaire, type de décision]", date or "[date]"),
                "nom": titre or "CIJ"}
    if ecli.startswith("ECLI:CE:ECHR") or re.search(r"COUR EUROP[ÉE]ENNE DES DROITS DE L.HOMME", t, re.I):
        m = re.search(r"(AFFAIRE [^\n]+)", t)
        nom = nom_affaire_hudoc(m.group(1)) if m else ""
        m2 = re.search(r"[Rr]equ[êe]te n°\s*([\d/]+)", t)
        gc = " (Gde Ch.)" if re.search(r"GRANDE CHAMBRE", t) else ""
        return {"id": "JUR-ECHR-" + (m2.group(1).replace("/", "-") if m2 else C.slug(nom, 40)),
                "juridiction": "Cour européenne des droits de l’homme", "cote": ecli, "date": date, "titre": nom,
                "citation": "Cour eur. D.H.%s, arrêt %s, %s%s" % (gc, nom or "[intitulé]", date or "[date]",
                                                                 (", req. n° " + m2.group(1)) if m2 else ""), "nom": nom}
    if ecli.startswith("ECLI:EU:") or re.search(r"ARR[ÊE]T DE LA COUR", t):
        aff = re.findall(r"\b(C-\d+/\d{2})\b", t[:3000])
        return {"id": "JUR-CJUE-" + C.slug(ecli or "_".join(aff) or date, 40),
                "juridiction": "Cour de justice de l’Union européenne", "cote": ecli, "date": date,
                "citation": "C.J.U.E., arrêt [parties], %s%s%s" % (date or "[date]", (", aff. " + ", ".join(dict.fromkeys(aff))) if aff else "",
                                                                 (", " + ecli.replace("ECLI:", "")) if ecli else ""),
                "nom": "_".join(dict.fromkeys(aff)) or "arret"}
    return None


SYM_COMITE = re.compile(r"\b((?:CAT|CCPR|CERD|CEDAW|CRC|CRPD|CED|CMW)/C/\d+/D/\d+/\d{4}|E/C\.12/\d+/D/\d+/\d{4})")
COMITES_TRAITE = {"CAT": ("Comité contre la torture", "CAT"), "CCPR": ("Comité des droits de l’homme", "PIDCP"),
                  "CERD": ("Comité pour l’élimination de la discrimination raciale", "CERD"),
                  "CEDAW": ("Comité pour l’élimination de la discrimination à l’égard des femmes", "CEDAW"),
                  "CRC": ("Comité des droits de l’enfant", "CIDE"), "CRPD": ("Comité des droits des personnes handicapées", "CRPD"),
                  "CED": ("Comité des disparitions forcées", ""), "CMW": ("Comité des travailleurs migrants", ""),
                  "E": ("Comité des droits économiques, sociaux et culturels", "PIDESC")}


def _champ(texte, etiquettes):
    for e in etiquettes:
        m = re.search(e + r"\s*:?\s*([^\n]{2,120})", texte, re.I)
        if m:
            return " ".join(m.group(1).split()).strip(" .;")
    return ""


def reconnaitre_comite(texte, sym):
    """Décision ou constatations d'un comité de l'ONU -> fiche et citation."""
    code = sym.split("/")[0]
    nom, traite = COMITES_TRAITE.get(code, ("Comité de l’ONU", ""))
    t = texte or ""
    auteur = _champ(t, [r"Pr[ée]sent[ée]e? par", r"Submitted by"])
    auteur = re.sub(r"\s*\((?:repr[ée]sent|represented)[^)]*\)?", "", auteur).strip()
    etat = _champ(t, [r"[ÉE]tat partie", r"State party"])
    etat = re.split(r"\s{2,}|\s+Date\b", etat)[0]
    m = re.search(r"[Cc]ommunication\s+n[o°º]\.?\s*(\d+/\d{4})", t)
    num = m.group(1) if m else "/".join(sym.split("/")[-2:])
    constat = re.search(r"Constatations|Views adopted|Views under", t)
    d = _champ(t, [r"Date (?:de l.adoption )?(?:des constatations|de la (?:pr[ée]sente )?d[ée]cision|d.adoption de la d[ée]cision)",
                   r"Date of adoption of (?:Views|decision)", r"Date of (?:the )?decision"])
    date = C.date_dans_texte(d) or C.date_dans_texte(t[:2500])
    genre = "constatations" if constat else "décision"
    parties = ("%s c. %s" % (auteur, etat)) if auteur and etat else (auteur or etat)
    citation = "%s, %s%scommunication n° %s, %s du %s, %s" % (nom, parties, ", " if parties else "", num, genre,
                                                           date or "[date]", sym)
    return {"id": "JUR-" + sym.replace("/", "-"), "juridiction": "ONU, " + nom, "titre": parties, "date": date,
            "citation": citation, "traite": traite}


def articles_cites_traite(texte, traite):
    """Articles du traité du comité mentionnés dans la décision (ex. article 3 de la Convention)."""
    t = C.norm(texte)
    trouves = set()
    for m in re.finditer(r"\b(?:article|articles|art)\s+(\d+)\b", t):
        suite = t[m.end():m.end() + 120]
        if re.match(r"\s*(?:paragraphe|par|§)?\s*\d*\s*(?:de la convention|du pacte|de la charte|of the convention|of the covenant)", suite):
            trouves.add(m.group(1))
    return set(sorted(trouves, key=int)[:15])


def _objet_cc(texte):
    m = re.search(r"En cause\s*:\s*(.{20,400}?)(?:\n\s*\n|La Cour constitutionnelle)", texte or "", re.S)
    return " ".join(m.group(1).split())[:300] if m else ""


def _cle_art(a):
    m = re.match(r"(\d+)", a)
    return (0, int(m.group(1)), a) if m else (1, 0, a)


# ---------------------------------------------------------------------------
# Adresses
# ---------------------------------------------------------------------------
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
EURLEX_HTML = "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:{celex}"
EURLEX_PDF = "https://eur-lex.europa.eu/legal-content/FR/TXT/PDF/?uri=CELEX:{celex}"
EURLEX_PAGE = "https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:{celex}"
CC_PDF = "https://www.const-court.be/public/f/{y}/{y}-{n:03d}f.pdf"
CE_PDF = "https://www.raadvst-consetat.be/arr.php?nr={n}&l=fr"
CCE_PDF = ["https://www.rvv-cce.be/sites/default/files/arr/a{n}.an_.pdf",
           "https://www.rvv-cce.be/sites/default/files/arr/A{n}.AN.pdf"]
JUPORTAL = "https://juportal.be/content/{ecli}/FR"

# Actes proposés pour la recherche C.J.U.E. (CELEX, libellé complet, libellé court affiché)
ACTES_UE = [
    ("32011L0095", "Directive 2011/95/UE (qualification, refonte)"),
    ("32024R1347", "Règlement (UE) 2024/1347 (qualification)"),
    ("32013L0032", "Directive 2013/32/UE (procédures)"),
    ("32024R1348", "Règlement (UE) 2024/1348 (procédure d’asile)"),
    ("32026R0463", "Règlement (UE) 2026/463 (pays tiers sûr)"),
    ("32026R0464", "Règlement (UE) 2026/464 (pays d’origine sûrs de l’Union)"),
    ("32013L0033", "Directive 2013/33/UE (accueil)"),
    ("32024L1346", "Directive (UE) 2024/1346 (accueil, refonte)"),
    ("32008L0115", "Directive 2008/115/CE (retour)"),
    ("32024R1349", "Règlement (UE) 2024/1349 (retour à la frontière)"),
    ("32013R0604", "Règlement (UE) n° 604/2013 (Dublin III)"),
    ("32024R1351", "Règlement (UE) 2024/1351 (gestion de l’asile et de la migration)"),
    ("32024R1356", "Règlement (UE) 2024/1356 (filtrage)"),
    ("32024R1359", "Règlement (UE) 2024/1359 (crise et force majeure)"),
    ("12016P/TXT", "Charte des droits fondamentaux de l’UE"),
    ("32003L0086", "Directive 2003/86/CE (regroupement familial)"),
]


# Libellés courts affichés dans l'onglet (deux colonnes) ; le libellé complet apparaît dans la bulle d'aide.
COURTS = {"32011L0095": "Dir. 2011/95 (qualification)", "32024R1347": "Règl. 2024/1347 (qualification)",
          "32013L0032": "Dir. 2013/32 (procédures)", "32024R1348": "Règl. 2024/1348 (procédure)",
          "32026R0463": "Règl. 2026/463 (tiers sûr)", "32026R0464": "Règl. 2026/464 (liste UE)",
          "32013L0033": "Dir. 2013/33 (accueil)", "32024L1346": "Dir. 2024/1346 (accueil)",
          "32008L0115": "Dir. 2008/115 (retour)", "32024R1349": "Règl. 2024/1349 (frontière)",
          "32013R0604": "Règl. 604/2013 (Dublin III)", "32024R1351": "Règl. 2024/1351 (gestion)",
          "32024R1356": "Règl. 2024/1356 (filtrage)", "32024R1359": "Règl. 2024/1359 (crise)",
          "12016P/TXT": "Charte des droits fond.", "32003L0086": "Dir. 2003/86 (regroupement)"}


def libelle_court(lib, celex="", maxi=30):
    """« Règlement (UE) 2024/1358 (Eurodac) » -> « Règl. 2024/1358 (Eurodac) » (coupé à « maxi » caractères)."""
    if celex in COURTS:
        return COURTS[celex]
    lib = re.sub(r"^Règlement \(UE\) (n° )?", "Règl. ", lib)
    lib = re.sub(r"^Directive (\(UE\) )?", "Dir. ", lib)
    lib = re.sub(r"(\d{4}/\d+)/(UE|CE)\b", r"\1", lib)
    return lib if len(lib) <= maxi else lib[:maxi - 1].rstrip() + "…"


# Sources ajoutées par l'utilisateur : fichier sources_jurisprudence.csv du dossier de base.
SOURCES_NOM = "sources_jurisprudence.csv"
SOURCES_ENTETE = ["type", "code", "libelle", "formulations"]
SOURCES_MODELE = [
    ["# type = acte_ue (code = numéro CELEX : l’acte apparaît dans « C.J.U.E. »)", "", "", ""],
    ["# type = site (code = adresse : un bouton apparaît dans « Recherche à la main »)", "", "", ""],
    ["# type = texte (code = abréviation ; formulations = façons de citer le texte, séparées par |) : "
     "le texte apparaît dans les listes « de : » pour filtrer les articles", "", "", ""],
    ["# Les lignes qui commencent par # sont ignorées. Exemples :", "", "", ""],
    ["#acte_ue", "32024R1358", "Règlement (UE) 2024/1358 (Eurodac)", ""],
    ["#site", "https://www.refworld.org/", "Refworld (HCR)", ""],
    ["#texte", "LOI-CCE-2026", "Loi du 17 juin 2026 relative au Conseil du contentieux des étrangers",
     "loi du 17 juin 2026|conseil du contentieux des etrangers"],
]


def chemin_sources(base):
    c = os.path.join(base, SOURCES_NOM)
    if not os.path.exists(c):
        os.makedirs(base, exist_ok=True)
        with open(c, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(SOURCES_ENTETE)
            w.writerows(SOURCES_MODELE)
    return c


def sources_utilisateur(base):
    """-> {"acte_ue": [(celex, libellé)], "site": [(libellé, url)], "texte": [(code, libellé, [formulations])]}"""
    out = {"acte_ue": [], "site": [], "texte": []}
    if not base:
        return out
    try:
        with open(chemin_sources(base), encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                typ = (r.get("type") or "").strip().lower()
                code, lib = (r.get("code") or "").strip(), (r.get("libelle") or "").strip()
                if not typ or typ.startswith("#") or not code:
                    continue
                if typ in ("acte_ue", "acte", "celex"):
                    out["acte_ue"].append((code.upper(), lib or code.upper()))
                elif typ in ("site", "url", "lien"):
                    out["site"].append((lib or code, code))
                elif typ == "texte":
                    forms = [x.strip() for x in (r.get("formulations") or "").split("|") if x.strip()]
                    out["texte"].append((code, lib or code, forms or [lib or code]))
    except Exception:
        pass
    return out


def actes_ue(base=None):
    vus, out = set(), []
    for celex, lib in ACTES_UE + sources_utilisateur(base)["acte_ue"]:
        if celex not in vus:
            vus.add(celex)
            out.append((celex, lib))
    return out


def recherches_manuelles(base=None):
    urls = {u for _, u in RECHERCHES_MANUELLES}
    return RECHERCHES_MANUELLES + [(l, u) for l, u in sources_utilisateur(base)["site"] if u not in urls]


def charger_textes_utilisateur(base=None):
    """Ajoute à TEXTES les textes du fichier de l'utilisateur (sans jamais remplacer un texte du programme)."""
    for code, lib, forms in sources_utilisateur(base)["texte"]:
        if code not in TEXTES:
            TEXTES[code] = (lib, forms)
            for f_ in [code] + forms:
                if C.norm(f_):
                    ALIAS.insert(0, (C.norm(f_), code))

def url_hudoc_manuelle(articles=(), etat="", mots="", types=("JUDGMENTS",), langues=("FRE", "ENG"), gc=False):
    """Adresse de recherche HUDOC pré-remplie (critères dans le fragment « #{…} » de l'URL)."""
    crit = {}
    if mots:
        crit["fulltext"] = [mots]
    if articles:
        crit["article"] = [str(a) for a in articles]
    if etat:
        crit["respondent"] = [etat.upper()]
    if gc:
        crit["documentcollectionid2"] = ["GRANDCHAMBER"]
    elif types:
        crit["documentcollectionid2"] = list(types)
    if langues:
        crit["languageisocode"] = list(langues)
    return "https://hudoc.echr.coe.int/fre#" + urllib.parse.quote(json.dumps(crit, ensure_ascii=False, separators=(",", ":")),
                                                                  safe='{}[]:,"')


RECHERCHES_MANUELLES = [
    ("HUDOC (Cour eur. D.H.)", "https://hudoc.echr.coe.int/fre"),
    ("Comités ONU (base « Juris »)", "https://juris.ohchr.org/search/documents"),
    ("CURIA (C.J.U.E.)", "https://curia.europa.eu/juris/recherche.jsf?language=fr"),
    ("C.I.J.", "https://www.icj-cij.org/fr/decisions"),
    ("Cour constitutionnelle", "https://www.const-court.be/fr/judgments"),
    ("Juportal (Cass. et juridictions judiciaires)", "https://juportal.be/home/accueil"),
    ("Conseil d’État", "https://www.raadvst-consetat.be/"),
    ("C.C.E.", "https://www.rvv-cce.be/fr"),
]
