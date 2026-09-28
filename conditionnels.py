# SPDX-License-Identifier: GPL-3.0-or-later
"""Paragraphes conditionnels, calculés à partir de la collecte (onglet ONU) :

  - ratifications.csv (Collection des traités) : ratifié, adhéré, signé sans ratifier, ni signé ni ratifié ;
    réserves ou déclarations ;
  - procedures_de_plaintes_HCDH.csv : plaintes individuelles, procédure d'enquête, communications entre États ;
  - etat_des_rapports.csv : rapports remis en retard (retard calculé), rapports toujours attendus ;
  - documents collectés : courriers de suivi des comités sans réponse de l'État, dernières observations finales.

Chaque paragraphe porte ses repères de notes [[…]] et est rangé sous une rubrique du plan (début du titre).
Les données de départ peuvent être incomplètes : tout ce qui est incertain est signalé entre crochets.
"""
import csv
import datetime as dt
import os
import re

import redaction as R

# ---------------------------------------------------------------------------
# Dates et durées
# ---------------------------------------------------------------------------
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
           "novembre", "décembre"]
_MOIS = {}
for i, (fr, en) in enumerate(zip(MOIS_FR, ["january", "february", "march", "april", "may", "june", "july",
                                            "august", "september", "october", "november", "december"]), 1):
    for x in (fr, en, fr[:3], en[:3], fr[:4], en[:4], fr.replace("é", "e").replace("û", "u")):
        _MOIS[x] = i
_MOIS.update({"févr": 2, "fevr": 2, "juil": 7, "sept": 9, "déc": 12, "dec": 12, "aout": 8})
RE_D1 = re.compile(r"\b(\d{1,2})(?:er)?\s+([A-Za-zéèêûôà]{3,9})\.?\s+((?:19|20)\d\d)\b")
RE_D2 = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.]((?:19|20)\d\d)\b")
RE_D3 = re.compile(r"\b((?:19|20)\d\d)-(\d{1,2})-(\d{1,2})\b")
RE_D4 = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+((?:19|20)\d\d)\b")


def dates_dans(txt):
    """Toutes les dates d'un texte, dans l'ordre (formats anglais, français, 23/07/2017, 2017-07-23)."""
    out = []
    t = txt or ""
    for rx, f in ((RE_D1, lambda m: (int(m.group(3)), _MOIS.get(m.group(2).lower()), int(m.group(1)))),
                  (RE_D2, lambda m: (int(m.group(3)), int(m.group(2)), int(m.group(1)))),
                  (RE_D3, lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
                  (RE_D4, lambda m: (int(m.group(3)), _MOIS.get(m.group(1).lower()), int(m.group(2))))):
        for m in rx.finditer(t):
            a, mo, j = f(m)
            if not mo:
                continue
            try:
                out.append((m.start(), dt.date(a, mo, j)))
            except ValueError:
                pass
    vus, res = set(), []
    for pos, d in sorted(out):
        if pos not in vus:
            vus.add(pos)
            res.append(d)
    return res


def une_date(txt):
    d = dates_dans(txt)
    return d[0] if d else None


def date_fr(d):
    return "%s %s %d" % ("1er" if d.day == 1 else d.day, MOIS_FR[d.month - 1], d.year)


_U = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize",
      "quatorze", "quinze", "seize"]
_D = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def en_lettres(n):
    if n < 17:
        return _U[n]
    if n < 20:
        return "dix-" + _U[n - 10]
    if n < 70:
        d, u = divmod(n, 10)
        return _D[d] + ("" if u == 0 else " et un" if u == 1 else "-" + _U[u])
    if n < 80:
        return "soixante" + (" et onze" if n == 71 else "-" + en_lettres(n - 60))
    if n < 100:
        return "quatre-vingt" + ("s" if n == 80 else "-" + en_lettres(n - 80))
    return str(n)


def ecart(d1, d2):
    """(années, mois, jours) de d1 à d2 (d2 >= d1)."""
    a, m, j = d2.year - d1.year, d2.month - d1.month, d2.day - d1.day
    if j < 0:
        m -= 1
        prec = (d2.replace(day=1) - dt.timedelta(days=1))
        j += prec.day
    if m < 0:
        a -= 1
        m += 12
    return a, m, j


def duree(d1, d2):
    """« plus de quatre ans et sept mois », « deux mois », « douze jours »."""
    a, m, j = ecart(d1, d2)
    parts = []
    if a:
        parts.append("%s an%s" % (en_lettres(a), "s" if a > 1 else ""))
    if m:
        parts.append("%s mois" % en_lettres(m))
    if not parts:
        return "%s jour%s" % (en_lettres(j), "s" if j > 1 else "")
    txt = " et ".join(parts)
    if not j:
        return txt
    return ("plus d’" if txt[0] in "aeiouhé" else "plus de ") + txt


def ordinal(n):
    return {1: "premier", 2: "deuxième", 3: "troisième", 4: "quatrième", 5: "cinquième", 6: "sixième",
            7: "septième", 8: "huitième", 9: "neuvième", 10: "dixième"}.get(n, "%de" % n)


# ---------------------------------------------------------------------------
# Traités et comités
# ---------------------------------------------------------------------------
TRAITES = {  # n° de la Collection des traités : (nom avec article, genre, comité)
    "IV-4": ("le Pacte international relatif aux droits civils et politiques", "m", "CCPR"),
    "IV-5": ("le Protocole facultatif se rapportant au Pacte international relatif aux droits civils et politiques",
             "m", "CCPR"),
    "IV-12": ("le deuxième Protocole facultatif se rapportant au Pacte international relatif aux droits civils et "
              "politiques, visant à abolir la peine de mort", "m", "CCPR"),
    "IV-3": ("le Pacte international relatif aux droits économiques, sociaux et culturels", "m", "CESCR"),
    "IV-3-a": ("le Protocole facultatif se rapportant au Pacte international relatif aux droits économiques, sociaux "
               "et culturels", "m", "CESCR"),
    "IV-9": ("la Convention contre la torture et autres peines ou traitements cruels, inhumains ou dégradants", "f",
             "CAT"),
    "IV-9-b": ("le Protocole facultatif se rapportant à la Convention contre la torture", "m", "CAT"),
    "IV-8": ("la Convention sur l’élimination de toutes les formes de discrimination à l’égard des femmes", "f",
             "CEDAW"),
    "IV-8-b": ("le Protocole facultatif à la Convention sur l’élimination de toutes les formes de discrimination à "
               "l’égard des femmes", "m", "CEDAW"),
    "IV-11": ("la Convention relative aux droits de l’enfant", "f", "CRC"),
    "IV-11-b": ("le Protocole facultatif à la Convention relative aux droits de l’enfant, concernant l’implication "
                "d’enfants dans les conflits armés", "m", "CRC"),
    "IV-11-c": ("le Protocole facultatif à la Convention relative aux droits de l’enfant, concernant la vente "
                "d’enfants, la prostitution des enfants et la pornographie mettant en scène des enfants", "m", "CRC"),
    "IV-11-d": ("le Protocole facultatif à la Convention relative aux droits de l’enfant établissant une procédure "
                "de présentation de communications", "m", "CRC"),
    "IV-2": ("la Convention internationale sur l’élimination de toutes les formes de discrimination raciale", "f",
             "CERD"),
    "IV-13": ("la Convention internationale sur la protection des droits de tous les travailleurs migrants et des "
              "membres de leur famille", "f", "CMW"),
    "IV-15": ("la Convention relative aux droits des personnes handicapées", "f", "CRPD"),
    "IV-15-a": ("le Protocole facultatif se rapportant à la Convention relative aux droits des personnes handicapées",
                "m", "CRPD"),
    "IV-16": ("la Convention internationale pour la protection de toutes les personnes contre les disparitions "
              "forcées", "f", "CED"),
    "IV-1": ("la Convention pour la prévention et la répression du crime de génocide", "f", ""),
    "V-2": ("la Convention relative au statut des réfugiés", "f", ""),
    "V-5": ("le Protocole relatif au statut des réfugiés", "m", ""),
    "V-3": ("la Convention relative au statut des apatrides", "f", ""),
    "V-4": ("la Convention sur la réduction des cas d’apatridie", "f", ""),
    "XVIII-10": ("le Statut de Rome de la Cour pénale internationale", "m", ""),
    "XVIII-12": ("la Convention des Nations Unies contre la criminalité transnationale organisée", "f", ""),
    "XVIII-12-a": ("le Protocole visant à prévenir, réprimer et punir la traite des personnes", "m", ""),
}
# repères des textes de référence (plus lisibles) pour les traités cités dans les blocs
LEX_TRAITES = {"IV-9": "TRAITE-CAT", "IV-4": "TRAITE-PIDCP"}

COMITES = {
    "CCPR": ("le Comité des droits de l’homme", "a. Le Pacte international relatif aux droits civils"),
    "CAT": ("le Comité contre la torture", "b. La Convention contre la torture"),
    "CESCR": ("le Comité des droits économiques, sociaux et culturels",
              "c. Le Pacte international relatif aux droits économiques"),
    "CEDAW": ("le Comité pour l’élimination de la discrimination à l’égard des femmes", "d. Autres instruments"),
    "CRC": ("le Comité des droits de l’enfant", "d. Autres instruments"),
    "CERD": ("le Comité pour l’élimination de la discrimination raciale", "d. Autres instruments"),
    "CRPD": ("le Comité des droits des personnes handicapées", "d. Autres instruments"),
    "CED": ("le Comité des disparitions forcées", "d. Autres instruments"),
    "CMW": ("le Comité des travailleurs migrants", "d. Autres instruments"),
}
INTRO = "A. Introduction"
# délai du premier rapport (années après l'entrée en vigueur à l'égard de l'État)
DELAI_INITIAL = {"CCPR": 1, "CAT": 1, "CERD": 1, "CEDAW": 1, "CMW": 1, "CESCR": 2, "CRC": 2, "CRPD": 2, "CED": 2}
T_PRINC = {"CCPR": "IV-4", "CAT": "IV-9", "CERD": "IV-2", "CEDAW": "IV-8", "CMW": "IV-13", "CESCR": "IV-3",
           "CRC": "IV-11", "CRPD": "IV-15", "CED": "IV-16"}
ARTICLE_RAPPORT = {"CCPR": "PIDCP, art. 40, §1, a)", "CAT": "CAT, art. 19, §1", "CESCR": "PIDESC, art. 16 et 17"}
RE_RAPPORT_ETAT = re.compile(r"^(?:(CCPR|CAT|CEDAW|CERD|CRC|CRPD|CED|CMW)/C|E/C\.12)/([A-Z]{3})/(\d{1,2})(?:-(\d{1,2}))?$")
RE_ANCIEN = re.compile(r"^(?:(CCPR|CAT|CEDAW|CERD|CRC|CRPD|CED|CMW)/C|E/C\.12)/\d+/Add\.\d+$")
RE_CO = re.compile(r"^(?:(CCPR|CAT|CEDAW|CERD|CRC|CRPD|CED|CMW)/C|E/C\.12)/([A-Z]{3})/CO/(\d{1,2})(?:-(\d{1,2}))?$")
ORDINAUX = {"premier": 1, "initial": 1, "deuxième": 2, "second": 2, "troisième": 3, "third": 3, "quatrième": 4,
            "fourth": 4, "cinquième": 5, "fifth": 5, "sixième": 6, "sixth": 6, "septième": 7, "seventh": 7,
            "huitième": 8, "eighth": 8, "neuvième": 9, "ninth": 9, "dixième": 10, "tenth": 10, "onzième": 11,
            "eleventh": 11, "douzième": 12, "twelfth": 12}
MANUEL = "etat_des_rapports_a_remplir.csv"
RE_SIGLE = re.compile(r"\b(CCPR|CESCR|CAT|CEDAW|CERD|CRC|CRPD|CED|CMW)\b")


def maj(s):
    return s[:1].upper() + s[1:]


def a_art(nom):
    """« le Pacte » -> « au Pacte » ; « la Convention » -> « à la Convention »."""
    if nom.startswith("le "):
        return "au " + nom[3:]
    if nom.startswith("les "):
        return "aux " + nom[4:]
    return "à " + nom


def sigle(txt):
    t = (txt or "").upper()
    if re.search(r"\bE/C\.12\b|\bCESCR\b", t):
        return "CESCR"
    m = RE_SIGLE.search(t)
    return m.group(1) if m else ""


def _lire_csv(chemin):
    if not chemin or not os.path.exists(chemin):
        return []
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f, delimiter=";")]


def texte_document(chemin, pages=None):
    """Texte d'un PDF, d'un Word (.docx) ou d'un ODT ; "" si illisible."""
    if not chemin or not os.path.exists(chemin):
        return ""
    low = chemin.lower()
    try:
        if low.endswith(".pdf"):
            if R.C.PdfReader is None:
                return ""
            rd = R.C.PdfReader(chemin)
            n = len(rd.pages) if pages is None else min(pages, len(rd.pages))
            return "\n".join((rd.pages[i].extract_text() or "") for i in range(n))
        if low.endswith((".docx", ".odt")):
            import zipfile
            with zipfile.ZipFile(chemin) as z:
                xml = z.read("word/document.xml" if low.endswith(".docx") else "content.xml").decode("utf-8", "ignore")
            txt = re.sub(r"</w:p>|</text:p>|</text:h>", "\n", xml)
            txt = re.sub(r"<[^>]+>", "", txt)
            import html as _h
            txt = _h.unescape(txt)
            return txt if pages is None else txt[:6000 * pages]
    except Exception:
        return ""
    return ""


def date_reception(txt):
    """Couverture d'un rapport d'État : « [Date de réception : 19 janvier 2012] », « [19 January 2012] »,
    « attendu en 2007 ». Renvoie (date de réception, année d'échéance)."""
    t = " ".join((txt or "").split())
    d = None
    m = re.search(r"(?:Date de réception|Date received|Date of receipt|Reçu le|Received on)\s*:?\s*([^\]\n]{6,40})", t, re.I)
    if m:
        d = une_date(m.group(1))
    if not d:
        for m in re.finditer(r"\[\s*([^\]]{6,45})\]", t[:3000]):
            d = une_date(m.group(1))
            if d:
                break
    an = None
    m = re.search(r"(?:attendus?|due)\s+(?:en|in)\s+((?:19|20)\d\d)", t[:3000], re.I)
    if m:
        an = int(m.group(1))
    return d, an


def echeance_suivante(txt):
    """Fin des observations finales : échéance du prochain rapport. Renvoie (date, année, n° du rapport)."""
    t = " ".join((txt or "").split())
    if not t:
        return None, None, None
    # procédure simplifiée : « recevra en 2030 la liste de points … devra soumettre dans un délai d'un an ses
    # réponses …, qui constitueront son troisième rapport périodique »
    m = re.search(r"(?:recevra|will receive|lui adressera|will send)[^.]{0,60}?(?:en|in)\s+((?:20)\d\d)[^.]{0,120}?"
                  r"(?:liste de points|list of issues)[^.]{0,400}?(?:délai d[’']un an|within one year|one year)", t, re.I)
    if not m:
        m = re.search(r"(?:liste de points|list of issues)[^.]{0,120}?(?:en|in)\s+((?:20)\d\d)[^.]{0,400}?"
                      r"(?:délai d[’']un an|within one year|one year)", t, re.I)
    if m:
        fen = t[m.start(): m.end() + 250]
        mo = re.search(r"(?:son|its)\s+(%s)\s+(?:rapport|report|periodic)" % "|".join(ORDINAUX), fen, re.I)
        return None, int(m.group(1)) + 1, (ORDINAUX[mo.group(1).lower()] if mo else None)
    cles = list(re.finditer(r"prochain rapport(?! dialogue)|rapport périodique suivant|next periodic report|next report|"
                            r"constitueront son|constituera son|will constitute its|seront considérées comme son|"
                            r"(?:soumettre|présenter|submit)\s+(?:son|ses|its)\s+(?:\w+\s+){0,3}?(?:rapport|report)",
                            t, re.I))
    for m in reversed(cles):
        fen = t[max(0, m.start() - 250): m.start() + 450]
        cyc = None
        mo = re.search(r"(?:son|its)\s+(%s)\s+(?:rapport|report|periodic)" % "|".join(ORDINAUX), fen, re.I)
        if mo:
            cyc = ORDINAUX[mo.group(1).lower()]
        apres = t[m.start(): m.start() + 450]
        d = une_date(apres)
        if d:
            return d, None, cyc
        ma = re.search(r"(?:d’ici à|d'ici à|d’ici au|d'ici au|en|in|by|avant)\s+((?:20)\d\d)\b", apres)
        if ma:
            return None, int(ma.group(1)), cyc
    return None, None, None


def _chercher(dossier, *noms):
    for racine, _, fichiers in os.walk(dossier):
        for n in noms:
            if n in fichiers:
                return os.path.join(racine, n)
    return ""


# ---------------------------------------------------------------------------
# Lecture des données
# ---------------------------------------------------------------------------
class Donnees:
    def __init__(self, dossier_pays, sources, aujourdhui=None):
        self.auj = aujourdhui or dt.date.today()
        self.sources = sources or []
        self.ids = {s.get("id"): s for s in self.sources}
        self.alertes = []
        self.traites = self._ratifications(_chercher(dossier_pays, "ratifications.csv"))
        self.procedures = self._procedures(_chercher(dossier_pays, "procedures_de_plaintes_HCDH.csv"))
        self.rapports = self._rapports_documents(dossier_pays)
        self.rapports_docs = {k: list(v) for k, v in self.rapports.items()}
        self.suivi_attendu = {}
        tableau = self._tableau_hcdh(_chercher(dossier_pays, "etat_des_rapports.csv"))
        for com, ls in tableau.items():  # le tableau du HCDH l'emporte, rapport par rapport
            par_cycle = {l["cycle"]: l for l in self.rapports.get(com, [])}
            for l in ls:
                ancien = par_cycle.get(l["cycle"], {})
                for k in ("echeance", "remis", "annee", "note_e", "note_r", "hcdh"):
                    if not l.get(k) and ancien.get(k):
                        l[k] = ancien[k]
                if l.get("echeance"):
                    l["annee"] = None
                l["examine"] = l.get("examine") or ancien.get("examine", False)
                par_cycle[l["cycle"]] = l
            self.rapports[com] = [par_cycle[k] for k in sorted(par_cycle)]
        self.manuel = os.path.join(dossier_pays, "01_ONU_organes_de_traites", MANUEL)
        manuels = self._rapports(self.manuel) if os.path.exists(self.manuel) else {}
        for com, ls in manuels.items():  # ce que vous avez rempli à la main l'emporte, rapport par rapport
            par_cycle = {l.get("cycle"): l for l in self.rapports.get(com, [])}
            for l in ls:
                l["texte"] = "rempli à la main (%s)" % MANUEL
                ancien = par_cycle.get(l.get("cycle"), {})
                for k in ("note_e", "note_r", "examine", "comb"):
                    if ancien.get(k) and not l.get(k):
                        l[k] = ancien[k]
                par_cycle[l.get("cycle")] = l
            self.rapports[com] = [par_cycle[k] for k in sorted(par_cycle, key=lambda x: x or 99)]
        self.rapports_manuels = bool(manuels)

    def rep_rapports(self):
        return self.rep("ONU-ETAT-RAPPORTS") or ("HCDH-ETAT-RAPPORTS" if "LEX-HCDH-ETAT-RAPPORTS" in self.ids else "")

    def rep(self, *ids):
        """Repère d'une source si elle existe dans les sources chargées, sinon ""."""
        for i in ids:
            if i and i in self.ids:
                s = self.ids[i]
                return R.repere(s, self.sources) if not s.get("_lex") else s["_repere"]
        return ""

    def rep_traite(self, no):
        lex = LEX_TRAITES.get(no)
        if lex and ("LEX-" + lex) in self.ids:
            return lex
        return self.rep("TRAITE-" + no)

    # -- ratifications.csv -----------------------------------------------------------------------------
    def _ratifications(self, chemin):
        out = {}
        lignes = _lire_csv(chemin)
        for r in lignes[1:]:
            if len(r) < 2 or not r[0].strip():
                continue
            nom_csv, statut = r[0].strip(), r[1].strip()
            url = r[4] if len(r) > 4 else ""
            m = re.search(r"mtdsg_no=([A-Z]+-[\w-]+)", url)
            no = m.group(1) if m else ""
            sig = rat = None
            mode = ""
            if not re.search(r"non partie", statut, re.I):
                parts = [p.split(" : ", 1) for p in statut.split(" ; ")] if " : " in statut else \
                    [["", x] for x in statut.split(" | ")]
                for i, (k, v) in enumerate(parts):
                    kn = R.C.norm(k)
                    d = une_date(v)
                    if not d:
                        continue
                    if kn.startswith("signature") or (not kn and i == 0 and len(parts) > 1):
                        sig = d
                    elif rat is None:
                        rat = d
                        suf = re.search(r"(?:19|20)\d\d\s*([a-zA-Z]{1,2})\b", v)
                        mode = (suf.group(1).lower() if suf else "")
            nom, genre, comite = TRAITES.get(no, (None, None, ""))
            if not nom:
                n0 = nom_csv[:1].lower() + nom_csv[1:]
                genre = "f" if R.C.norm(nom_csv).startswith(("convention", "charte")) else "m"
                nom = ("la " if genre == "f" else "le ") + n0
                comite = sigle(nom_csv)
            out[no or nom_csv] = {"no": no, "nom": nom, "genre": genre, "comite": comite, "sig": sig, "rat": rat,
                                  "mode": mode, "reserves": len(r) > 2 and r[2].strip().lower() == "oui",
                                  "texte_reserves": r[3] if len(r) > 3 else "", "statut": statut}
        return out

    # -- procedures_de_plaintes_HCDH.csv --------------------------------------------------------------
    def _procedures(self, chemin):
        """{(type, comité): (True/False/None, date)} ; type = individuel, enquete, interetatique.
        Valeurs du HCDH : OUI / NON ; N/A = déclaration non faite (donc non acceptée) ; « - » = sans objet
        (traité non ratifié). Lit aussi la date d'entrée en vigueur de chaque traité (self.eif)."""
        res = {}
        self.eif = {}
        entete = ""
        for r in _lire_csv(chemin):
            cells = [c.strip() for c in r]
            if not any(cells):
                entete = ""
                continue
            if R.C.norm(cells[0]) in ("traite", "treaty"):
                entete = R.C.norm(" ".join(cells))
                continue
            lab = cells[0] if sigle(cells[0]) else next((c for c in cells if sigle(c)), "")
            if not lab:
                continue
            com = sigle(lab)
            n = R.C.norm(lab)
            U = lab.upper()
            if "enquete" in n or "inquiry" in n:
                typ = "enquete"
            elif "interetat" in n or "inter state" in n or "inter-state" in lab.lower():
                typ = "interetatique"
            elif "plaintes individuelles" in n or "individual" in n or re.search(r"-OP1?\b|OP-IC", U):
                typ = "individuel"
            elif "enquete" in entete or "inquiry" in entete:
                typ = "enquete"
            elif "plainte" in entete or "complaint" in entete:
                typ = "individuel"
            else:
                typ = None
            if typ is None:  # tableau des ratifications : date d'entrée en vigueur
                if com and not re.search(r"-OP|, ?ART", U) and ("vigueur" in entete or "force" in entete):
                    d = une_date(cells[-1]) if len(cells) >= 3 else None
                    if d and com not in self.eif:
                        self.eif[com] = d
                continue
            val, d, sans_objet = None, None, False
            for c in cells:
                if c == lab:
                    continue
                cu = c.strip().upper()
                if cu in ("OUI", "YES", "ACCEPTÉ", "ACCEPTEE", "ACCEPTED"):
                    val = True
                elif cu in ("NON", "NO", "N/A", "NA", "N.A.", "NOT ACCEPTED"):
                    val = False
                elif cu in ("-", "—", "–"):
                    sans_objet = True
                dd = une_date(c)
                if dd:
                    d = dd
            if val is None and d and not sans_objet:
                val = True
            if sans_objet and val is None:
                continue
            if val is None and res.get((typ, com), (None,))[0] is not None:
                continue
            res[(typ, com)] = (val, d)
        return res

    # -- etat_des_rapports.csv -------------------------------------------------------------------------
    def _tableau_hcdh(self, chemin):
        """Tableau des documents de la page du pays (HCDH) : lignes « Rapport de l’État partie | cote |
        date d’échéance | date de réception | date de publication | … ». Le numéro du rapport est son rang
        (par date d’échéance) parmi les rapports du comité. Les rapports de suivi attendus sont gardés à part."""
        rapports, suivis = {}, {}
        for r in _lire_csv(chemin):
            cells = [c.strip() for c in r]
            if len(cells) < 4:
                continue
            typ = R.C.norm(cells[0])
            if not (typ.startswith("rapport de l etat partie") or typ.startswith("state party") or
                    typ.startswith("rapport de l'etat partie")):
                continue
            txt = " | ".join(cells)
            com = sigle(cells[1]) or sigle(txt)
            if not com:
                continue
            ech_txt = cells[2]
            ech = une_date(ech_txt)
            m_init = re.search(r"(?:initialement en|initially (?:due )?in)\s+((?:19|20)\d\d)", ech_txt, re.I)
            rec = une_date(cells[3])
            cote = cells[1] if re.search(r"/", cells[1]) and len(cells[1]) < 40 else ""
            src = next((x for x in self.sources if (x.get("cote") or "").upper() == cote.upper()), None) if cote else None
            lig = {"cycle": None, "echeance": None if m_init else ech, "annee": int(m_init.group(1)) if m_init else None,
                   "remis": rec, "note_e": "", "note_r": _note(R.repere(src, self.sources)) if src else "",
                   "comb": None, "examine": False, "cote": cote, "hcdh": True,
                   "texte": "tableau du HCDH : « %s » %s" % (cells[0], cote or "(en attente)")}
            if "suivi" in typ or "follow" in typ:
                suivis.setdefault(com, []).append(lig)
            else:
                rapports.setdefault(com, []).append(lig)
        for com, ls in rapports.items():
            m_r = [RE_RAPPORT_ETAT.match(l["cote"]) for l in ls]
            ls.sort(key=lambda l: (l["echeance"] or (dt.date(l["annee"], 12, 31) if l["annee"] else dt.date.max)))
            for i, l in enumerate(ls, 1):
                m = RE_RAPPORT_ETAT.match(l["cote"])
                l["cycle"] = int(m.group(3)) if m else i
                if m and m.group(4):
                    l["comb"] = int(m.group(4))
        self.suivi_attendu = suivis
        return rapports

    def _rapports(self, chemin):
        """{comité: [{cycle, echeance, remis, retard_mention, texte}]}."""
        out = {}
        for r in _lire_csv(chemin):
            cells = [c.strip() for c in r]
            if not cells or cells[0].startswith("#"):
                continue
            txt = " | ".join(cells)
            com = next((sigle(c) for c in cells if sigle(c) and len(c) < 40), "") or sigle(txt)
            if not com or re.search(r"CRC-OP|OP-AC|OP-SC", txt):
                continue
            cyc = next((int(c) for c in cells if re.fullmatch(r"\d{1,2}", c)), None)
            if cyc is None and re.search(r"initial", txt, re.I):
                cyc = 1
            ds = [une_date(c) for c in cells]
            ds = [d for d in ds if d]
            if not ds:
                continue
            en_retard = bool(re.search(r"retard|overdue|not received|non re[çc]u|pending|en attente", txt, re.I))
            out.setdefault(com, []).append({"cycle": cyc, "echeance": ds[0] if ds else None,
                                            "remis": ds[1] if len(ds) > 1 else None, "retard": en_retard,
                                            "texte": txt})
        for com in out:
            out[com].sort(key=lambda x: (x["cycle"] or 99, x["echeance"] or dt.date.max))
        return out

    # -- rapports reconstitués à partir des documents collectés -----------------------------------------
    def _rapports_documents(self, dossier_pays):
        """Sans tableau du HCDH : premier rapport = entrée en vigueur + délai du traité ; date de réception
        lue sur la couverture des rapports de l'État ; échéance du rapport suivant lue à la fin des
        observations finales (« soumettre son prochain rapport … d'ici au 26 juillet 2017 »)."""
        cycles = {}

        def c_(com, n):
            return cycles.setdefault(com, {}).setdefault(n, {"cycle": n, "echeance": None, "annee": None,
                                                              "remis": None, "note_e": "", "note_r": "",
                                                              "comb": None, "examine": False, "texte": ""})
        for com, eif in self.eif.items():
            if com in DELAI_INITIAL and T_PRINC.get(com) and self.traites.get(T_PRINC[com], {}).get("rat"):
                x = c_(com, 1)
                try:
                    x["echeance"] = eif.replace(year=eif.year + DELAI_INITIAL[com])
                except ValueError:
                    x["echeance"] = eif + dt.timedelta(days=365 * DELAI_INITIAL[com])
                art = ARTICLE_RAPPORT.get(com)
                x["note_e"] = _note(art if art and ("LEX-" + art.split(",")[0]) in self.ids else "",
                                    self.rep("HCDH-PROCEDURES"))
                x["texte"] = "entrée en vigueur le %s + %d an(s)" % (date_fr(eif), DELAI_INITIAL[com])
        for s in self.sources:
            cote = (s.get("cote") or "").replace("_", "/").strip()
            fich = s.get("fichier") or ""
            m_r = RE_RAPPORT_ETAT.match(cote)
            m_c = RE_CO.match(cote)
            m_a = RE_ANCIEN.match(cote) if not (m_r or m_c) else None
            if m_a:  # ancienne cote (CAT/C/72/Add.1) : numéro du rapport lu dans son titre
                tit = R.C.norm(s.get("titre", ""))
                num = 1 if "initial" in tit else next((v for k, v in ORDINAUX.items() if R.C.norm(k) in tit.split()), 0)
                if not num:
                    continue
                m_r = re.match(r"^(.*)$", cote)
                n1, n2, com = num, None, (m_a.group(1) or "CESCR")
            if not (m_r or m_c):
                continue
            if not m_a:
                com = "CESCR" if cote.startswith("E/C.12") else (m_r or m_c).group(1)
            chemin = os.path.join(s.get("_racine") or dossier_pays, fich) if fich else ""
            if m_r:
                if not m_a:
                    n1, n2 = int(m_r.group(3)), m_r.group(4)
                x = c_(com, n1)
                x["comb"] = int(n2) if n2 else None
                x["note_r"] = _note(R.repere(s, self.sources))
                txt = texte_document(chemin, pages=2)
                d, an = date_reception(txt)
                if d:
                    x["remis"] = d
                    x["texte"] = (x["texte"] + " ; " if x["texte"] else "") + "réception lue sur %s" % cote
                elif chemin:
                    x["texte"] = (x["texte"] + " ; " if x["texte"] else "") + \
                        "date de réception introuvable dans %s" % cote
                if an and not x["echeance"]:
                    x["annee"] = an
            else:
                n1 = int(m_c.group(3))
                n_fin = int(m_c.group(4)) if m_c.group(4) else n1
                for k in range(n1, n_fin + 1):
                    c_(com, k)["examine"] = True
                txt = texte_document(chemin)
                d, an, cyc = echeance_suivante(txt)
                cyc = cyc or n_fin + 1
                if d or an:
                    x = c_(com, cyc)
                    x["echeance"], x["annee"] = d, (None if d else an)
                    x["note_e"] = _note(R.repere(s, self.sources))
                    x["texte"] = (x["texte"] + " ; " if x["texte"] else "") + "échéance lue dans %s" % cote
        out = {}
        for com, cs in cycles.items():
            preuves = [k for k, x in cs.items() if x["examine"] or x["note_r"]]
            if not preuves:
                continue  # aucun document de ce comité : on ne conclut rien (pas de « jamais soumis »)
            dernier = max(preuves)
            for k, x in cs.items():
                if k < dernier:
                    x["examine"] = True  # un rapport ou un examen postérieur existe : ce rapport a été remis
            out[com] = [cs[k] for k in sorted(cs)]
        return out

    # -- documents collectés ---------------------------------------------------------------------------
    def suivi(self, com):
        """(courriers du comité, réponses de l'État) : listes de (date, source)."""
        lettres, reponses = [], []
        for s in self.sources:
            cote = (s.get("cote") or "").upper().replace("_", "/")
            if not cote or sigle(cote) != com:
                continue
            d = une_date(s.get("date", ""))
            if not d:
                continue
            if re.search(r"/FU[LR]/", cote) or s.get("titre", "") in ("courrier de suivi du Comité",
                                                                        "rappel de suivi du Comité"):
                lettres.append((d, s))
            elif re.search(r"/CO/\d+(-\d+)?/ADD\.\d+$", cote) or re.search(r"/FUI/", cote):
                reponses.append((d, s))
        return sorted(lettres, key=lambda x: x[0]), sorted(reponses, key=lambda x: x[0])

    def dernieres_observations(self, com):
        best = None
        for s in self.sources:
            cote = (s.get("cote") or "").upper()
            if sigle(cote) != com or not re.search(r"/CO/\d+(-\d+)?$", cote):
                continue
            d = une_date(s.get("date", ""))
            n = [int(x) for x in re.findall(r"\d+", cote.rsplit("/CO/", 1)[1])]
            cle = (d or dt.date.min, n)
            if best is None or cle > best[0]:
                best = (cle, s, d)
        return (best[1], best[2]) if best else (None, None)


# ---------------------------------------------------------------------------
# Rédaction des paragraphes
# ---------------------------------------------------------------------------
def _note(*reps):
    reps = [r for r in reps if r]
    return "[[%s]]" % " ; ".join(reps) if reps else ""


def phrase_traite(t, D, sujet="{Le_pays}"):
    """Une phrase sur la participation de l'État à un traité."""
    n = _note(D.rep_traite(t["no"]))
    e = "e" if t["genre"] == "f" else ""
    if t["rat"]:
        if t["mode"] == "a":
            v = "a adhéré %s le %s" % (a_art(t["nom"]), date_fr(t["rat"]))
        elif t["mode"] == "d":
            v = "est devenu partie, par succession, %s le %s [accord de « devenu » à vérifier]" % (
                a_art(t["nom"]), date_fr(t["rat"]))
        else:
            v = "a ratifié %s le %s" % (t["nom"], date_fr(t["rat"]))
        return "%s %s%s." % (sujet, v, n)
    if t["sig"]:
        return "%s a signé %s le %s, mais ne l’a pas ratifié%s%s." % (sujet, t["nom"], date_fr(t["sig"]), e, n)
    return "%s n’a ni signé ni ratifié %s%s." % (sujet, t["nom"], n)


def _liste(xs, conj="et"):
    xs = [x for x in xs if x]
    if len(xs) < 2:
        return "".join(xs)
    return ", ".join(xs[:-1]) + " %s " % conj + xs[-1]


def paragraphes(dossier_pays, sources, variables=None, aujourdhui=None):
    """Renvoie (liste de (rubrique, [paragraphes]), alertes). Les variables ({Le_pays}…) sont remplacées."""
    global DERNIER
    D = Donnees(dossier_pays, sources, aujourdhui)
    DERNIER = D
    v = variables or {}
    par = {}

    def ajoute(rub, txt):
        if txt:
            par.setdefault(rub, []).append(R.remplacer(txt, v))

    T = D.traites
    # --- A. Introduction : vue d'ensemble -----------------------------------------------------------
    if T:
        parties = [t for t in T.values() if t["rat"]]
        signes = [t for t in T.values() if not t["rat"] and t["sig"]]
        aucun = [t for t in T.values() if not t["rat"] and not t["sig"]]
        if parties:
            ajoute(INTRO, "{Le_pays} est partie %s%s." % (_liste([a_art(t["nom"]) + " (%s le %s)" % (
                "adhésion" if t["mode"] == "a" else "succession" if t["mode"] == "d" else "ratification",
                date_fr(t["rat"])) for t in parties]), _note(*[D.rep_traite(t["no"]) for t in parties])))
        if signes:
            ajoute(INTRO, "{Le_pays} a signé, sans les ratifier, %s%s." % (_liste(["%s (signature le %s)" % (
                t["nom"], date_fr(t["sig"])) for t in signes]), _note(*[D.rep_traite(t["no"]) for t in signes])))
        if aucun:
            ajoute(INTRO, "En revanche, {le_pays} n’a ni signé ni ratifié %s%s." % (
                _liste([t["nom"] for t in aucun], "ni"), _note(*[D.rep_traite(t["no"]) for t in aucun])))
        res = [t for t in T.values() if t["reserves"] and (t["rat"] or t["sig"])]
        if res:
            ajoute(INTRO, "{Le_pays} a assorti sa participation %s de réserves ou de déclarations%s [à analyser : "
                          "voir le texte sur la page de la Collection des traités et le bloc « Notion de réserve »]."
                   % (_liste([a_art(t["nom"]) for t in res]),
                      _note(*[D.rep_traite(t["no"]) for t in res])))
    P = D.procedures
    n_hcdh = _note(D.rep("HCDH-PROCEDURES"))
    if P:
        acc = sorted({c for (typ, c), (val, d) in P.items() if typ == "individuel" and val})
        ref = sorted({c for (typ, c), (val, d) in P.items() if typ == "individuel" and val is False})
        inconnus = sorted({c for (typ, c), (val, d) in P.items() if typ == "individuel" and val is None})
        if inconnus and (acc or ref):
            ajoute(INTRO, "%s%s [À compléter pour %s : le tableau du HCDH (procedures_de_plaintes_HCDH.html) ne "
                          "permet pas au programme de savoir si la procédure de plaintes individuelles est acceptée.]"
                   % ("{Le_pays} a accepté la procédure de plaintes individuelles devant %s. " % _liste(
                       [COMITES[c][0] for c in acc if c in COMITES]) if acc else "",
                      ("{Le_pays} n’a pas accepté la procédure de plaintes individuelles devant %s%s." % (
                          _liste([COMITES[c][0] for c in ref if c in COMITES]), n_hcdh)) if ref else "",
                      _liste([COMITES[c][0] for c in inconnus if c in COMITES])))
        elif not acc and ref:
            ajoute(INTRO, "{Le_pays} n’a accepté aucune des procédures de plaintes individuelles prévues par les "
                          "traités des Nations Unies relatifs aux droits de l’homme : aucune victime relevant de sa "
                          "juridiction ne peut saisir les comités%s." % n_hcdh)
        elif acc:
            ajoute(INTRO, "{Le_pays} n’a accepté la procédure de plaintes individuelles que devant %s%s%s." % (
                _liste([COMITES[c][0] for c in acc if c in COMITES]),
                (" ; elle n’est pas ouverte devant %s" % _liste([COMITES[c][0] for c in ref if c in COMITES]))
                if ref else "", n_hcdh))

    # --- Par comité ----------------------------------------------------------------------------------
    for com, (nom_com, rub) in COMITES.items():
        principaux = [t for t in T.values() if t["comite"] == com and t["nom"].startswith(("la Convention", "le Pacte"))]
        protocoles = [t for t in T.values() if t["comite"] == com and t not in principaux]
        partie = any(t["rat"] for t in principaux)
        if com in ("CEDAW", "CRC", "CERD", "CRPD", "CED", "CMW") and not (partie or D.rapports.get(com)):
            continue  # « autres instruments » : on ne parle que de ce qui existe
        for t in principaux:
            ajoute(rub, phrase_traite(t, D))
        for t in protocoles:
            if t["rat"]:
                ajoute(rub, phrase_traite(t, D, "{Le_pays}"))
            elif t["no"] == "IV-5":
                ajoute(rub, phrase_traite(t, D, "En revanche, {le_pays}")[:-1] + ", de sorte que le Comité des "
                       "droits de l’homme ne peut pas recevoir de plaintes émanant de particuliers relevant de sa "
                       "juridiction.")
            elif t["no"] == "IV-12":
                ajoute(rub, phrase_traite(t, D, "{Le_pays}"))
            elif t["no"] == "IV-9-b":
                ajoute(rub, phrase_traite(t, D, "{Le_pays}")[:-1] + " : aucun mécanisme international de visite "
                       "des lieux de détention (Sous-comité pour la prévention de la torture) n’est donc prévu.")
            else:
                ajoute(rub, phrase_traite(t, D, "{Le_pays}"))
        if not partie and principaux:
            continue
        # procédures de plaintes et d'enquête (surtout la Convention contre la torture)
        ind = P.get(("individuel", com))
        enq = P.get(("enquete", com))
        inter = P.get(("interetatique", com))
        if com == "CAT":
            if ind and ind[0] is False and inter and inter[0] is False:
                ajoute(rub, "Toutefois, {le_pays} n’a pas fait les déclarations prévues aux articles 21 et 22 de la "
                            "Convention%s, de sorte que l’État ne reconnaît pas la compétence du Comité contre la torture "
                            "pour connaître de plaintes déposées par d’autres États parties à la Convention (art. 21 "
                            "de la Convention contre la torture) ou par des individus relevant de sa juridiction "
                            "(art. 22 de la Convention contre la torture)%s. Autrement dit, une personne victime de "
                            "torture {en_pays} ne peut pas saisir le Comité." % (n_hcdh, n_hcdh))
            elif ind and ind[0] is False:
                ajoute(rub, "Toutefois, {le_pays} n’a pas fait la déclaration prévue à l’article 22 de la Convention, "
                            "de sorte que le Comité contre la torture ne peut pas recevoir de plaintes émanant de "
                            "particuliers relevant de sa juridiction%s. Autrement dit, une personne victime de torture "
                            "{en_pays} ne peut pas saisir le Comité." % n_hcdh)
            elif (not ind or ind[0] is None) and T.get("IV-9", {}).get("rat"):
                ajoute(rub, "[À compléter : l’État a-t-il fait les déclarations prévues aux articles 21 et 22 de "
                            "la Convention ? Voir procedures_de_plaintes_HCDH.html (dossier 02_Ratifications) : le programme n’a pas pu le lire.]")
            if enq and enq[0] is False:
                ajoute(rub, "En outre, {le_pays} ne reconnaît pas la compétence du Comité contre la torture pour "
                            "mener une enquête en vertu de l’article 20 de la Convention%s." % n_hcdh)
        elif com in ("CERD", "CED", "CMW") and ind and ind[0] is False and partie:
            art = {"CERD": "14", "CED": "31", "CMW": "77"}[com]
            ajoute(rub, "{Le_pays} n’a pas fait la déclaration prévue à l’article %s de %s : %s ne peut pas "
                        "recevoir de plaintes émanant de particuliers%s." % (
                            art, next((t["nom"] for t in principaux), "la Convention"), nom_com, n_hcdh))
        # rapports
        for p in rapports_paragraphes(com, D):
            ajoute(rub, p)
        # suivi
        for p in suivi_paragraphes(com, D):
            ajoute(rub, p)
        # dernières observations finales
        s, d = D.dernieres_observations(com)
        if s is not None and d:
            a, m, j = ecart(d, D.auj)
            phr = "Les observations finales les plus récentes du %s datent du %s%s" % (
                nom_com[3:], date_fr(d), _note(R.repere(s, D.sources)))
            if a >= 5:
                phr += " : la situation {de_pays} n’a donc plus été examinée par ce Comité depuis %s" % duree(d, D.auj)
            ajoute(rub, phr + ".")
    if not T:
        D.alertes.append("ratifications.csv introuvable : relancez l’étape « Ratifications » de l’onglet ONU.")
    if not any(l.get("echeance") or l.get("annee") for ls in D.rapports.values() for l in ls):
        modele_rapports(D.manuel, D)
        D.alertes.append("État des rapports absent : la collecte n’a pas pu lire le tableau du HCDH (il est souvent "
                         "affiché par JavaScript). Remplissez le fichier « %s » (dossier 01_ONU_organes_de_traites du "
                         "pays, créé pour vous) avec les dates de la page du HCDH : les retards seront alors calculés."
                         % MANUEL)
    if not P:
        D.alertes.append("procedures_de_plaintes_HCDH.csv introuvable : les procédures de plaintes (articles 21 et "
                         "22 de la Convention contre la torture…) ne sont pas calculées.")
    return [(rub, ps) for rub, ps in par.items()], D.alertes


def rapports_paragraphes(com, D):
    lignes = D.rapports.get(com, [])
    if not lignes:
        return []
    n_etat = _note(D.rep_rapports())
    out = []
    auj = D.auj
    for l in lignes:
        e, r, an = l.get("echeance"), l.get("remis"), l.get("annee")
        ne = l.get("note_e") or ""
        nr = l.get("note_r") or ""
        if not (ne or nr):
            ne = n_etat
        cyc = l.get("cycle")
        comb = l.get("comb")
        if comb:
            quoi = "ses %s à %s rapports périodiques (présentés en un seul document)" % (ordinal(cyc), ordinal(comb))
        else:
            quoi = ("son premier rapport" if cyc == 1 else "son %s rapport périodique" % ordinal(cyc) if cyc else
                    "son rapport [numéro à vérifier]")
        le_ = "les" if comb else "l’"
        if not e and an:  # échéance connue à l'année près : on compte à partir du 31 décembre
            e_fin = dt.date(an, 12, 31)
            if r and r > e_fin:
                out.append("{Le_pays} devait transmettre %s en %d%s et ne %sa soumis que le %s%s, soit au moins %s "
                           "après l’échéance." % (quoi, an, ne, le_, date_fr(r), nr, duree(e_fin, r).replace(
                               "plus de ", "").replace("plus d’", "")))
            elif not r and not l.get("examine") and e_fin < auj:
                out.append("{Le_pays} devait transmettre %s en %d%s ; aucun rapport correspondant ne figure parmi les "
                           "documents collectés, soit un retard d’au moins %s [à vérifier dans la base des organes "
                           "de traités]." % (quoi, an, ne, duree(e_fin, auj).replace("plus de ", "").replace(
                               "plus d’", "")))
            elif not r and e_fin >= auj:
                out.append("Le prochain rapport {de_pays} (%s) est attendu en %d%s." % (
                    quoi.replace("son ", "").replace("ses ", ""), an, ne))
            continue
        if not e:
            continue
        if r:
            if r > e and (r - e).days > 31:
                out.append("{Le_pays} avait jusqu’au %s pour transmettre %s%s et ne %sa soumis que le %s%s, soit %s "
                           "après l’échéance du délai." % (date_fr(e), quoi, ne, le_, date_fr(r), nr, duree(e, r)))
            else:
                out.append("{Le_pays} a transmis %s le %s%s, dans le délai qui expirait le %s%s." % (
                    quoi, date_fr(r), nr, date_fr(e), ne))
        elif l.get("examine"):
            out.append("%s, attendu pour le %s%s, a été examiné par le Comité [date de réception à vérifier : la "
                       "couverture du rapport n’a pas pu être lue]." % (maj(quoi.replace("son ", "le ").replace(
                           "ses ", "les ")), date_fr(e), ne))
        elif e < auj and l.get("hcdh"):
            out.append("{Le_pays} devait transmettre %s au plus tard le %s%s ; à la date du présent courrier, l’État ne "
                       "%sa toujours pas soumis%s, soit un retard de %s." % (quoi, date_fr(e), ne, le_, n_etat,
                                                                           duree(e, auj)))
        elif e < auj:
            out.append("{Le_pays} devait transmettre %s au plus tard le %s%s ; à la date du présent courrier, l’État ne "
                       "%sa toujours pas soumis, soit un retard de %s [à vérifier : le rapport peut avoir été reçu "
                       "sans figurer parmi les documents collectés]." % (quoi, date_fr(e), ne, le_, duree(e, auj)))
        else:
            out.append("Le prochain rapport {de_pays} (%s) est attendu pour le %s%s." % (
                quoi.replace("son ", "").replace("ses ", ""), date_fr(e), ne))
    return out


def suivi_paragraphes(com, D):
    lettres, reponses = D.suivi(com)
    out = []
    n_etat = _note(D.rep_rapports())
    for l in getattr(D, "suivi_attendu", {}).get(com, []):
        e, r = l.get("echeance"), l.get("remis")
        if r:
            out.append("{Le_pays} a transmis au %s des informations sur la suite donnée à ses observations "
                       "finales le %s%s%s." % (COMITES[com][0][3:], date_fr(r), (", alors qu’elles étaient "
                       "attendues pour le %s" % date_fr(e)) if e and r > e else "", l.get("note_r") or n_etat))
        elif e and e < D.auj:
            out.append("Le %s attendait {de_pays}, au plus tard le %s, des informations sur la suite donnée à ses "
                       "observations finales ; à la date du présent courrier, elles n’ont jamais été transmises%s, "
                       "soit un retard de %s." % (COMITES[com][0][3:], date_fr(e), n_etat, duree(e, D.auj)))
    if not lettres:
        return out
    dates = _liste(["le %s%s" % (date_fr(d), _note(R.repere(s, D.sources))) for d, s in lettres])
    out.append("Dans le cadre de la procédure de suivi des observations finales, %s a adressé {a_pays} des "
               "courriers %s [vérifiez dans le dernier courrier la note attribuée par le Comité et la clôture "
               "éventuelle de la procédure de suivi]." % (COMITES[com][0], dates)
               if len(lettres) > 1 else
               "Dans le cadre de la procédure de suivi des observations finales, %s a adressé {a_pays} un "
               "courrier %s [vérifiez dans ce courrier la note attribuée par le Comité]." % (COMITES[com][0], dates))
    dern = lettres[-1][0]
    rep_apres = [x for x in reponses if x[0] > dern]
    if not rep_apres:
        out.append("Aucune réponse {de_pays} postérieure au dernier courrier du Comité, du %s, ne figure parmi les "
                   "documents collectés, soit depuis %s%s [à vérifier dans l’état des rapports]." % (
                       date_fr(dern), duree(dern, D.auj), _note(D.rep_rapports())))
    return out


DERNIER = None


def lecture(D=None):
    """Ce que le programme a compris des fichiers (pour vérifier dans l'aperçu)."""
    D = D or DERNIER
    if D is None:
        return []
    L = ["## Ce que le programme a lu"]
    for t in D.traites.values():
        etat = ("adhésion" if t["mode"] == "a" else "succession" if t["mode"] == "d" else "ratification") + \
            " le " + date_fr(t["rat"]) if t["rat"] else ("signature seule le " + date_fr(t["sig"]) if t["sig"]
                                                        else "ni signature ni ratification")
        L.append("- %s : %s%s   (colonne lue : %s)" % (maj(t["nom"]), etat, " ; réserves" if t["reserves"] else "",
                                                       t["statut"]))
    for (typ, com), (val, d) in sorted(D.procedures.items(), key=lambda x: (x[0][1], x[0][0])):
        L.append("- %s, %s : %s" % (com, {"individuel": "plaintes individuelles", "enquete": "procédure d’enquête",
                                           "interetatique": "communications entre États"}[typ],
                                    "acceptée" if val else "non acceptée" if val is False else "inconnu"))
    for com, ls in D.rapports.items():
        for l in ls:
            ech = date_fr(l["echeance"]) if l.get("echeance") else ("en %d" % l["annee"] if l.get("annee") else "?")
            L.append("- %s, rapport n° %s%s : échéance %s ; remis %s%s   (%s)" % (
                com, l.get("cycle") or "?", ("-%s" % l["comb"]) if l.get("comb") else "", ech,
                date_fr(l["remis"]) if l.get("remis") else "non", " ; examiné" if l.get("examine") else "",
                l.get("texte") or "?"))
    return L


def modele_rapports(chemin, D=None):
    """Crée le fichier à remplir à la main (une ligne par rapport), s'il n'existe pas."""
    if os.path.exists(chemin):
        return chemin
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    comites = sorted({t["comite"] for t in (D.traites.values() if D else []) if t["comite"] and t["rat"]
                      and t["nom"].startswith(("la Convention", "le Pacte"))}) or ["CCPR", "CAT"]
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Comité", "Cycle (1 = premier rapport)", "Date limite (échéance)", "Date de remise (vide si pas remis)"])
        w.writerow(["# Mode d’emploi : ouvrez la page « état des rapports » du pays sur le site du HCDH (base des "
                    "organes de traités, onglet du pays) et recopiez une ligne par rapport. Dates au format 23/05/2007. "
                    "Complétez les lignes ci-dessous (ajoutez-en une par cycle) ; les lignes qui commencent par # sont "
                    "ignorées. Exemple :"])
        w.writerow(["# CCPR", "1", "23/05/2007", "19/01/2012"])
        for c in comites:
            w.writerow([c, "1", "", ""])
    return chemin
