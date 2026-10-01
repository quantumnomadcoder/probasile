# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""Textes d'aide de l'interface (fenêtres « Mode d'emploi ») et petits outils d'affichage :
fenêtre d'information défilante, bulles d'aide au survol, fenêtre de bienvenue.

Conventions des textes : une ligne qui commence par « ## » est un titre ; « - » une puce ;
les autres lignes sont du texte courant (les retours à la ligne sont conservés)."""

AIDE = {}

AIDE["general"] = """## À quoi sert ce programme
Il rassemble, pour un pays, les sources utiles à un dossier (protection internationale, non-délivrance d'un ordre de quitter le territoire, 9bis, 9ter…) : documents de l'ONU, ratifications, rapports d'ONG et d'agences, presse, jurisprudence. Chaque document est téléchargé, rangé dans un dossier numéroté et décrit dans un tableau (sources.csv) avec sa référence complète et sa date de consultation.

## Deux usages
- Collecter : onglets ONU, ReliefWeb, Veille, Jurisprudence, Importer.
- Rédiger : onglet Rédaction (plan type, notes de bas de page automatiques, annexes).

## Démarrage rapide
1. En haut : choisissez le pays (tapez les premières lettres) et le dossier de base où tout sera rangé.
2. Parcourez les onglets et cochez ce que vous voulez collecter. Chaque onglet a un bouton « Mode d’emploi de l’onglet ».
3. Cliquez sur « Lancer la collecte ». Les messages défilent en bas ; « Arrêter » interrompt proprement (ce qui est téléchargé est conservé).
4. « Ouvrir le dossier » montre le résultat ; « Ouvrir le journal » liste les nouveautés du dernier lancement.

## Les options du bas de la fenêtre
- Nouveautés seulement : ne cherche que ce qui est paru depuis la dernière collecte (plus rapide). Les documents déjà présents ne sont jamais retéléchargés, même sans cette option.
- Liens seulement : ne télécharge rien ; crée les fiches et une page de liens à ouvrir vous-même.
- Depuis l'année : limite ReliefWeb et la presse aux publications à partir de cette année.
- Tout réinitialiser : remet toutes les cases et tous les champs à leur valeur de départ (vos documents, votre dossier, vos identifiants de pays et vos listes de veille sont conservés).

## Où sont les fichiers ?
Dans le dossier de base, un dossier par pays, par ex. « Indonésie (IDN) », qui contient :
- 01_ONU_organes_de_traites … 12_A_classer : les documents, rangés par catégorie (voir « Voir les catégories » dans l'onglet ReliefWeb).
- sources.csv : le tableau de toutes les sources (voir ci-dessous). S'ouvre avec LibreOffice Calc ou Excel (séparateur : point-virgule).
- journal_AAAA-MM-JJ_HHMMSS.txt : la liste des nouveaux documents de chaque lancement.
- liens_a_telecharger_… .html : les documents que le programme n'a pas pu (ou pas dû) télécharger ; cliquez pour les ouvrir, puis importez-les.
- .etat.json (fichier caché) : la mémoire du programme pour ce pays (dates des dernières collectes, CountryID, dernière session de l'EPU…). Le supprimer fait « oublier » les dates : la collecte suivante revérifie tout, sans rien retélécharger de ce qui est déjà présent.
Dans le dossier de base lui-même :
- catalogue_sources.csv : la liste des organisations reconnues et leur catégorie (onglet ReliefWeb).
- traites.csv : la liste des traités dont on vérifie la ratification (onglet ONU).
- Jurisprudence (dossier commun) : la jurisprudence, commune à tous les pays (onglet Jurisprudence).
Dans votre dossier personnel : .collecte_pays.json garde vos réglages d'une ouverture à l'autre.

## Le tableau sources.csv, colonne par colonne
- id : identifiant interne (ne pas modifier).
- categorie : la catégorie (et donc le dossier) du document.
- auteur : l'organisation ou la juridiction, sous la forme utilisée dans les notes.
- titre : le titre du document.
- cote : la cote ONU (ex. CCPR/C/IDN/CO/2), le numéro de requête, l'ECLI…
- date : la date du document (lue dans le document quand c'est possible).
- url : l'adresse d'origine.
- consulte_le : la date de consultation, à reprendre dans les notes.
- fichier : le chemin du fichier téléchargé, dans le dossier du pays.
- langue : fr ou en (quand une version française n'existe pas).
- annexe : à remplir vous-même (numéro d'annexe) ; jamais écrasée par le programme.
- remarques : à remplir vous-même ou informations utiles ; vos remarques ne sont jamais écrasées.
- citation : la référence prête à l'emploi (jurisprudence).
- articles : les articles invoqués (jurisprudence), pour le futur programme de notes.

## Repartir de zéro
- Pour les réglages : bouton « Tout réinitialiser ».
- Pour les données d'un pays : fermez le programme et supprimez (ou renommez) le dossier du pays.
"""

AIDE["onu"] = """## L'onglet ONU en bref
Il réunit ce que l'ONU publie sur le pays : documents des comités, état des rapports, Examen périodique universel (EPU), ratifications. Chaque cadre numéroté est indépendant : cochez « Inclure » dans ceux qui vous intéressent.

## Comités concernés
Les comités cochés servent aux cadres 1 et 2. Pour un dossier d'asile ou de non-refoulement, CCPR (Comité des droits de l'homme) et CAT (Comité contre la torture) sont en général l'essentiel ; ajoutez CEDAW (femmes), CRC (enfants), CESCR (droits économiques et sociaux, utile pour la santé) selon le cas.

## 1. Documents principaux des comités
Le programme devine les cotes (ex. CCPR/C/IDN/CO/2) et télécharge les documents en français quand ils existent, sinon en anglais.
- Observations finales : l'évaluation du comité (le document le plus cité).
- Listes de points (avant rapport) : les questions posées à l'État.
- Rapports de l'État : la version de l'État (utile pour montrer ce qu'il reconnaît).
Rangement : 01_ONU_organes_de_traites/<COMITÉ>/.

## 2. Base des organes de traités (HCDH)
Tout ce que le site du HCDH liste pour le pays : lettres de suivi (ex. la lettre du Comité des droits de l'homme sur le suivi), contributions des ONG, informations de suivi de l'État, anciennes cotes.
- « seulement les comités cochés » évite de télécharger des centaines de documents inutiles.
- « documents communs » : le document de base de l'État (HRI/CORE/…), qui décrit ses institutions et son droit.
- « sans les comptes rendus de séance » : écarte les procès-verbaux (…/SR.…), nombreux et rarement utiles.
- CountryID : numéro du pays au HCDH (Indonésie = 80). Le programme le trouve seul la plupart du temps ; sinon une fenêtre explique comment le lire.
Fichier produit : 01_ONU_organes_de_traites/etat_des_rapports.csv — une ligne par rapport attendu ou remis : comité, rapport, date d'échéance, date de réception, session… Utile pour montrer les retards de l'État.

## 3. Examen périodique universel (EPU)
Pour chaque examen du pays devant le Conseil des droits de l'homme :
- les trois documents de base : rapport national (…/1), compilation des Nations Unies (…/2), résumé des communications des parties prenantes, surtout des ONG (…/3) ;
- avec l'option « résultats » : le rapport du Groupe de travail (la liste de toutes les recommandations faites au pays), l'additif (la réponse de l'État : recommandations acceptées ou seulement « notées », c'est-à-dire refusées), la décision du Conseil et la liste thématique des recommandations (.doc ou .xlsx).
Rangement : 03_ONU_EPU/session_NN/.

## 4. Ratifications
Pour chaque traité de votre liste : dates de signature et de ratification ou d'adhésion, texte des réserves et déclarations du pays, objections d'autres États qui le visent. Source : Collection des traités de l'ONU. Le programme lit aussi, au HCDH, quelles procédures de plaintes individuelles le pays accepte.
- « Choisir les traités… » : ne vérifier que certains traités de la liste pour ce lancement.
- « Modifier la liste… » : ajouter ou retirer des traités de façon durable (fichier traites.csv).
- « Élargir » : en plus de votre liste, le programme parcourt trois chapitres entiers de la Collection des traités (IV Droits de l'homme, V Réfugiés et apatrides, XVIII Matières pénales) et ajoute tous les traités de ces chapitres auxquels le pays participe. Plus long ; utile pour ne rien oublier.
Fichiers produits (02_Ratifications/) :
- ratifications.csv et ratifications.html (plus lisible) : traité ; signature / ratification / adhésion ; réserves ou déclarations (oui/non) ; texte des réserves et déclarations (en français, sinon en anglais) ; lien officiel ; origine (liste ou chapitre) ; date de consultation.
- procedures_de_plaintes_HCDH.csv et .html : quatre tableaux — ratifications (avec l'entrée en vigueur), plaintes individuelles (OUI / NON), procédures d'enquête, communications entre États.
À savoir : les textes des réserves sont repris de la page française de la Collection des traités ; si elle ne les donne pas, le texte anglais est repris et signalé. La page officielle (lien sous chaque traité) fait foi.

## 5. Procédures spéciales
Les lettres des rapporteurs spéciaux au gouvernement (« AL IDN 5/2026 »…) ne se téléchargent pas automatiquement : le bouton ouvre leur moteur de recherche ; téléchargez les PDF puis importez-les (onglet Importer), la référence est reconnue automatiquement.
"""

AIDE["reliefweb"] = """## L'onglet ReliefWeb en bref
ReliefWeb (Bureau de la coordination des affaires humanitaires de l'ONU) rassemble les rapports publiés sur chaque pays par les agences de l'ONU, les ONG, les gouvernements. Le programme y prend les rapports des organisations cochées, les télécharge et les range par catégorie.

## Comment l'utiliser
1. Cochez « Inclure » (les options restent grisées sinon).
2. Cadre 1 : choisissez un préréglage (« Droits humains » pour une demande de protection ou un OQT ; « Santé » pour un 9ter) : il coche les sources adaptées. Vous pouvez ensuite cocher ou décocher à la main.
3. Cadre 2 : thème, mots-clés, langues, nombre maximal de documents (facultatif).
4. Cadre 3 : nom d'application (appname) : c'est la clé d'accès officielle à ReliefWeb. Avec elle, tout est automatique. Sans elle, le programme essaie le flux RSS.

## Si ReliefWeb refuse le programme (réponse « 202 »)
ReliefWeb bloque parfois les programmes mais pas les navigateurs. Alors :
1. Cliquez sur « Ouvrir le flux du pays » (cadre 3) : le flux s'ouvre dans votre navigateur. Pour un flux plus ciblé, « Construire un flux filtré » ouvre ReliefWeb : filtrez (organisation, thème, type de document) puis copiez l'adresse du bouton RSS.
2. Enregistrez la page (Ctrl+S) : vous obtenez un fichier .xml.
3. Onglet Importer puis « Choisir des fichiers… » puis ce fichier .xml puis Lancer.
Une fiche est créée par publication ; les PDF que ReliefWeb refuse de donner au programme sont listés dans liens_a_telecharger_… .html.

## Le catalogue des sources
« Modifier le catalogue… » ouvre catalogue_sources.csv (explications dans la fenêtre qui s'affiche avant). « Recharger » relit le fichier après modification. « Voir les catégories » liste les catégories et leurs dossiers.

## Fichiers produits
- Les rapports, rangés dans le dossier de leur catégorie puis de leur organisation, nommés « AAAA-MM-JJ_titre.pdf ».
- Une ligne par rapport dans sources.csv (auteur = organisation, date, lien ReliefWeb, fichier).
"""

AIDE["veille"] = """## L'onglet Veille en bref
Suivre l'actualité du pays : presse, ONG locales, institutions nationales. Rien n'est téléchargé : chaque article devient une fiche (titre, source, date, lien) que vous consultez ensuite. Les listes sont mémorisées pour chaque pays.

## Deux façons de suivre
- Flux RSS : l'adresse du flux d'un site (souvent un lien « RSS » en bas de page, ou …/feed/ ou …/rss.xml). Une adresse par ligne.
- Recherches Google Actualités : une recherche par ligne, comme dans Google. Exemples :
  Indonesia blasphemy law
  site:kontras.org penyiksaan   (seulement le site de KontraS, mot indonésien « torture »)
  "Ahmadiyya" Indonesia
Astuce : une ligne mise par erreur dans le mauvais champ est comprise quand même (tout ce qui ne commence pas par http est traité comme une recherche).

## Réglages
- Ne garder que les titres contenant : filtre facultatif ; laissez vide au début (un mot français écarte tous les titres anglais…).
- Langue / pays de Google : les boutons « Presse du pays » (langue et édition du pays choisi : id / ID pour l'Indonésie), « Internationale » (en / US) et « Belge » (fr / BE) remplissent les deux cases ; pour un autre pays, tapez sa langue et son code (ex. fa / IR pour l'Iran).
- « Depuis l'année » (en bas de la fenêtre) écarte les articles plus anciens.
Sous chaque recherche, le programme indique combien d'articles il a écartés et pourquoi (trop anciens, filtre de mots, déjà connus).

## Fichiers produits
- 10_Presse/veille_AAAA-MM-JJ_HHMMSS.csv : les nouveaux articles de ce lancement (colonnes Date ; Source ; Titre ; Lien), du plus récent au plus ancien.
- Une ligne par article dans sources.csv, classée d'après le catalogue (Presse, ONG, institutions…).
"""

AIDE["jurisprudence"] = """## L'onglet Jurisprudence en bref
Trouver et ranger les décisions utiles, avec leur référence prête à citer : Cour européenne des droits de l'homme, Cour de justice de l'Union, Cour constitutionnelle, Conseil d'État, Conseil du contentieux des étrangers, Cour de cassation, Cour internationale de Justice, comités de l'ONU.

## Filtrer par article
Tapez « 3 » (article 3 de la Convention pour la Cour européenne), ou précisez le texte : « 3 CEDH, 33 Genève, 3 CAT ». « tous ces articles » = les décisions doivent citer chacun ; « au moins un » = l'un ou l'autre.

## Chaque juridiction
- Cour eur. D.H. (HUDOC) : HUDOC refuse les programmes. Le programme affiche un lien de recherche déjà rempli avec vos critères : ouvrez-le dans le navigateur, téléchargez les PDF, importez-les (onglet Importer). La référence est lue dans le PDF.
- C.J.U.E. : arrêts qui citent ou interprètent l'acte coché (directive qualification, règlements 2024/1347 et 2024/1348, règlements 2026/463 et 2026/464 sur les pays sûrs, actes du pacte sur la migration et l'asile…), filtrés sur ses articles. Automatique. Un acte trop récent peut ne pas encore avoir d'arrêt : le programme l'indique simplement.
- Cour constitutionnelle : parcourt les arrêts des années choisies et garde ceux qui citent les articles demandés. Automatique.
- Importer par référence : une référence par ligne (ECLI, « req. n° 59166/12 », « C-465/07 », « C. const. 23/2021 », « C.E. 248.270 », « C.C.E. 212 381 », cote d'une décision d'un comité de l'ONU, lien). Automatique, sauf HUDOC (voir plus haut).
- Recherche à la main : boutons qui ouvrent les moteurs de recherche officiels.
- Vos sources : « Ajouter des sources… » ouvre sources_jurisprudence.csv (dossier de base). Une ligne par source : acte_ue + numéro CELEX (l'acte s'ajoute au cadre C.J.U.E.), site + adresse (un bouton s'ajoute à « Recherche à la main »), texte + abréviation + façons de le citer séparées par | (il s'ajoute aux listes « de : »). Enregistrez, puis « Recharger ».

## Références produites
Exemples :
Cour eur. D.H. (Gde Ch.), arrêt J.K. et autres c. Suède, 23 août 2016, req. n° 59166/12
C.J.C.E. (Gde Ch.), arrêt Meki Elgafaji et Noor Elgafaji c. Staatssecretaris van Justitie, 17 février 2009, aff. C-465/07, EU:C:2009:94
(C.J.C.E. pour les arrêts d'avant le 1er décembre 2009, C.J.U.E. ensuite.)

## Fichiers produits
- Dossier « Jurisprudence (dossier commun) » dans le dossier de base (ou 11_Jurisprudence dans le dossier du pays si vous décochez l'option), avec un sous-dossier par juridiction : CEDH, CJUE, Cour_constitutionnelle, Conseil_d_Etat, CCE, Cour_de_cassation, CIJ, Comites_ONU.
- Son propre sources.csv : les colonnes « citation » (référence complète) et « articles » (articles trouvés dans la décision) y sont remplies.
"""

AIDE["importer"] = """## L'onglet Importer en bref
Ajouter à la collecte ce que vous avez trouvé vous-même : PDF téléchargés, liens, flux RSS enregistrés. Le document est rangé, décrit dans sources.csv et, quand c'est possible, reconnu automatiquement.

## Ce qui est reconnu automatiquement
- Décisions de justice (PDF) : Cour européenne des droits de l'homme, Cour constitutionnelle, Conseil d'État, C.C.E., Cour de cassation, C.I.J. puis rangées avec la jurisprudence, référence complète.
- Communications des procédures spéciales (« AL IDN 5/2026 ») : cote, date et titre remplis.
- Flux RSS enregistré (.xml), par exemple de ReliefWeb : une fiche par publication.
Pour les autres documents, l'auteur et le titre sont à vérifier ou compléter dans sources.csv.

## Liens
Un lien par ligne. Le programme télécharge le PDF s'il y en a un, sinon il crée une fiche avec le titre de la page. Exception : les liens HUDOC (le site refuse les programmes) — téléchargez le PDF dans votre navigateur puis importez le fichier.

## Catégorie
« Automatique » : le programme classe d'après l'organisation (catalogue) ou le type de document. Choisissez une catégorie pour forcer le rangement.
"""

AIDE["catalogue"] = """## Le catalogue des sources (catalogue_sources.csv)
C'est la liste des organisations que le programme reconnaît, avec la catégorie (et donc le dossier) où ranger leurs documents. Elle sert à ReliefWeb (sources à cocher), à la veille (classement des articles) et à l'import (classement automatique).

## Ouvrir et modifier
Le fichier va s'ouvrir dans votre tableur (LibreOffice Calc). À l'ouverture, choisissez :
- jeu de caractères : Unicode (UTF-8) ;
- séparateur : point-virgule uniquement.
Une ligne = une organisation. Ajoutez, corrigez ou supprimez des lignes, puis enregistrez au format CSV (« Conserver le format actuel »). Revenez ensuite ici et cliquez sur « Recharger ».

## Les colonnes
- nom : le nom affiché et utilisé comme auteur (ex. Amnesty International, HCR, KontraS).
- nom_reliefweb : le nom exact de l'organisation sur ReliefWeb (ex. « Office of the United Nations High Commissioner for Human Rights »). Laissez vide si l'organisation n'est pas sur ReliefWeb : elle ne sera pas proposée dans la liste à cocher mais servira quand même au classement.
- categorie : une des catégories exactes (bouton « Voir les catégories »), ex. « ONG internationales », « ONU – agences », « Sources nationales », « Presse ».
- domaines : les adresses de ses sites, séparées par des espaces (ex. amnesty.org amnesty.be). C'est ce qui permet de classer un article ou un lien.
- prereglages : « droits », « sante » ou les deux (séparés par un espace) : les préréglages qui cochent cette source.

## Exemple de ligne ajoutée
KontraS;;Sources nationales;kontras.org;droits
(ONG indonésienne contre les disparitions et la violence : absente de ReliefWeb, mais ses articles seront rangés dans « Sources nationales ».)

## En cas de problème
Si le catalogue devient illisible, renommez-le (ex. catalogue_ancien.csv) : le programme en recrée un propre au prochain lancement.
"""

AIDE["traites"] = """## La liste des traités (traites.csv)
C'est la liste des traités dont le programme vérifie la ratification par le pays. Elle est commune à tous les pays.

## Ouvrir et modifier
Le fichier va s'ouvrir dans votre tableur (LibreOffice Calc). À l'ouverture : jeu de caractères Unicode (UTF-8), séparateur point-virgule. Enregistrez ensuite au format CSV.

## Les colonnes
- numero_untc : le numéro du traité dans la Collection des traités de l'ONU, ex. IV-4 (Pacte international relatif aux droits civils et politiques), IV-9 (Convention contre la torture), V-2 (Convention relative au statut des réfugiés).
- nom : le nom affiché dans les résultats.

## Trouver le numéro d'un traité
Sur treaties.un.org, ouvrez la page du traité (« État des traités » puis chapitre puis traité) : le numéro figure dans l'adresse, après « mtdsg_no= » (ex. mtdsg_no=IV-4).

## Pour un seul lancement
Inutile de modifier la liste : le bouton « Choisir les traités… » permet de ne vérifier que certains traités, cette fois-ci.
"""

AIDE["redaction"] = """## L'onglet Rédaction en bref
Il aide à écrire le dossier à partir des sources collectées, en trois temps :
1. créer un plan type pour la procédure ;
2. écrire le texte dans Word ou LibreOffice en plaçant des repères [[…]] là où il faut une note ;
3. générer : chaque repère devient une vraie note de bas de page, les annexes sont numérotées, leur index est écrit et un PDF unique des annexes est assemblé.

## 1. Créer un plan type
Choisissez la procédure (non-délivrance d'OQT, protection internationale, 9ter) le nom (ex. Monsieur A. Exemple, Madame X, Monsieur et Madame Y et leurs enfants) et « Qui demande ? » : un homme, une femme, plusieurs personnes ou une famille, plusieurs femmes. Les titres du plan et les blocs s'accordent automatiquement (le demandeur / la demanderesse / les demandeurs, il / elle / ils, exposé / exposée / exposés…). « Choisir les blocs… » : cochez les passages juridiques types à recopier dans le plan (ceux marqués « par défaut » sont cochés d'office). « Modifier la bibliothèque… » et « Textes de référence… » : pour mettre à jour ces passages et les lois ou arrêts qu'ils citent (explications dans la fenêtre qui s'ouvre). « Modifier les plans… » : pour ajouter, renommer, déplacer ou supprimer des sections des plans types. « Format » : Word (.docx) ou LibreOffice (.odt) ; le plan s'ouvre dans le traitement de texte correspondant. Il contient :
- les titres de la procédure (repris des dossiers déjà rédigés), avec vos styles (Arial, titres, notes) ;
- sous chaque titre, en gris, des indications de rédaction (à supprimer ensuite) ;
- en bleu, les repères des sources déjà collectées qui correspondent à la rubrique (par ex. les documents du Comité des droits de l'homme sous « Le Pacte ») ;
- les blocs de texte choisis, déjà rédigés, avec leurs repères de notes (passages entre [crochets] à adapter) ;
- une table des matières (LibreOffice : clic droit puis « Mettre à jour l'index » ; Word : clic droit puis « Mettre à jour les champs ») et, à la fin, le repère [[INDEX DES ANNEXES]].
Le plan est enregistré dans le dossier du pays, sous-dossier « Redaction ». Enregistrez votre texte sous le nom de votre choix.

## 2. Les repères
Tapez le repère à l'endroit exact de l'appel de note, sans espace avant, comme une note : « …violations systématiques[[CCPR/C/IDN/CO/2, §24, p.8]]. »
- [[CCPR/C/IDN/CO/2]] : la source seule. Le repère est la cote pour les documents de l'ONU, sinon l'identifiant affiché dans la liste (cadre 2) ; quelques mots suffisent aussi s'ils ne désignent qu'une source ([[Human Rights Watch 2026]]).
- [[CCPR/C/IDN/CO/2, §24, p.8]] : avec la précision, après une virgule.
- [[… +trad]] : « Traduction libre de : … ».
- [[… +souligne]] : ajoute « ; nous soulignons ».
- [[… +annexe]] ou [[… +sansannexe]] : force ou empêche la mise en annexe de cette source.
- [[A, §3 ; B, p.2]] : plusieurs sources dans la même note, séparées par un point-virgule.
- [[= texte]] : une note écrite telle quelle (commentaire, renvoi…).
- [[PIECE nom]] : une pièce personnelle (voir ci-dessous).
- [[14038/88, §88]] ou [[C-465/07]] : la jurisprudence se retrouve aussi par numéro de requête ou d'affaire.
- [[LOI1980, art. 74/13]], [[SOERING, §88]] : les lois, conventions et arrêts des « Textes de référence ».
- [[BLOC nom du bloc]] seul dans un paragraphe : insère, au moment de générer, la dernière version d'un bloc de la bibliothèque.
- [[INDEX DES ANNEXES]] : l'endroit où l'index sera écrit (sinon, il est ajouté à la fin).
Cadre 2 : tapez un mot pour filtrer, puis double-cliquez sur une ligne : le repère est copié avec ses crochets, il n'y a plus qu'à le coller (Ctrl+V) et à ajouter la précision (, §24, p.8). La colonne « Annexe » dit si la source sera jointe (oui), citée avec son lien (non) ou si c'est un texte de référence (loi).
Bouton « Gérer… » (ou « Liste des repères et des annexes… » sous le cadre 3) : la même liste en grand, avec des boutons pour annexer ou non une source, corriger sa référence (auteur, titre, date, lien), ajouter un document qui n'a pas été collecté (avec son fichier, rangé dans 12_Sources_ajoutees) et supprimer une source ajoutée à la main. « Actualiser » relit la liste après une collecte, un import ou une modification.

## Les paragraphes calculés (plans OQT et protection internationale)
Case « Paragraphes calculés » (cadre 1) : le plan reçoit des paragraphes écrits à partir de la collecte de l'onglet ONU, avec leurs notes :
- A. Introduction : traités auxquels l'État est partie (avec la date de ratification ou d'adhésion), traités signés sans être ratifiés, traités ni signés ni ratifiés, réserves ou déclarations, procédures de plaintes individuelles acceptées ou non ;
- sous chaque comité (Pacte, Convention contre la torture, Pacte économique, autres) : ratification ou adhésion, protocoles non ratifiés (plaintes individuelles, peine de mort, prévention de la torture), articles 21 et 22 de la Convention contre la torture, rapports remis en retard avec le retard calculé (« soit plus de quatre ans et sept mois après l'échéance »), rapports toujours attendus (« soit un retard de plus de quatorze ans »), courriers de suivi sans réponse de l'État, date des dernières observations finales et temps écoulé.
Les fichiers utilisés : 02_Ratifications/ratifications.csv, 02_Ratifications/procedures_de_plaintes_HCDH.csv et les documents des comités collectés (rapports de l'État, observations finales, courriers de suivi). S'il en manque un, la partie correspondante n'est pas écrite (le journal le signale).
Les retards de rapports sont reconstitués sans intervention :
- échéance du premier rapport : date d'entrée en vigueur (tableau du HCDH) + délai du traité (un an pour le Pacte civil et politique et la Convention contre la torture, deux ans pour le Pacte économique…) ;
- date de remise : lue sur la couverture du rapport de l'État (« [Date de réception : 19 janvier 2012] ») ;
- échéance des rapports suivants : lue à la fin des observations finales (« soumettre son prochain rapport … d'ici au 26 juillet 2017 »).
Le programme ne conclut jamais qu'un rapport n'a pas été remis s'il n'a aucun document de ce comité. Si une date est fausse ou manque : bouton « Corriger les dates… » (à côté d'« Aperçu… ») ; il crée le fichier 01_ONU_organes_de_traites/etat_des_rapports_a_remplir.csv et explique comment le remplir (une ligne par rapport : comité ; numéro ; date limite ; date de remise). Ce que vous y écrivez l'emporte, rapport par rapport.
Bouton « Exporter… » : enregistre l'aperçu dans un document Word ou LibreOffice, selon le format choisi (dossier « Redaction » du pays), avec les paragraphes et leurs repères, prêts à copier dans votre texte.
Les blocs « à compléter à la main » (ratification du Pacte, articles 21 et 22) sont alors remplacés par ces paragraphes ; les blocs d'analyse (article 40, article 20, notion de réserve) restent.
Bouton « Aperçu… » : montre les paragraphes et, en dessous, ce que le programme a lu dans chaque fichier. Vérifiez-y les dates : les tableaux du Haut-Commissariat changent parfois de présentation.
Chaque paragraphe calculé est précédé d'un paragraphe gris « Paragraphes calculés automatiquement… » : vérifiez, complétez les passages entre crochets, puis supprimez-le.

## Les notes produites
- Première citation d'une source : référence complète (auteur, titre, cote, date, précision, lien et date de consultation, renvoi à l'annexe).
- Citations suivantes : référence courte suivie de « op.cit. » (en italique).
- Même source que la note juste avant : « Ibid. » (en italique), avec la nouvelle précision si elle change.
- Les notes que vous avez tapées vous-même restent en place ; après l'une d'elles, le programme n'écrit jamais « Ibid. » (il ne sait pas ce qu'elle cite).
La mise en forme suit les usages habituels des courriers (Ibid., op.cit. en italique). Une source annexée est citée sans lien, avec « voir l’annexe n° X au présent courrier » ; une source non annexée est citée avec son lien et sa date de consultation.

## Les annexes
Case « Annexer toutes les sources citées » cochée (par défaut) : chaque document cité dont on a le fichier (PDF, Word… : observations finales, rapports, pièces) devient une annexe, cité sans lien avec « voir l'annexe n° X au présent courrier ». Les pages web sans fichier (état des traités, état des rapports, articles en ligne) sont citées avec leur lien, et les lois, conventions et arrêts des textes de référence ne sont pas annexés. Pour ne pas annexer une source : [[repère +sansannexe]], ou « non » dans sa colonne « annexe » de sources.csv.
Case décochée : seules les sources dont la colonne « annexe » est remplie (oui, x…) ou dont un repère porte +annexe sont annexées. Les pièces personnelles sont toujours annexées. Les annexes sont numérotées dans l'ordre de leur première citation dans le texte.
Pièces personnelles (attestations, témoignages, passeports, certificats…), deux façons :
- bouton « Ajouter une pièce… » (cadre 2) : choisissez le fichier, décrivez-le (auteur, titre, date ; ex. « Athénée Exemple », « Attestation de scolarité de B. Exemple », « 12 septembre 2026 »). Le fichier est copié dans 00_Pieces_du_dossier et son repère est copié dans le presse-papiers : collez-le dans le texte ;
- ou déposez directement les fichiers (PDF, Word, ODT, images) dans le dossier (« Ouvrir le dossier des pièces ») : le nom du fichier devient le libellé (« 03_Attestation_scolaire_B_Exemple.pdf » donne [[PIECE 03_Attestation_scolaire_B_Exemple]] et « Attestation scolaire B Exemple ») ; « Gérer… » puis « Modifier… » permet ensuite d'ajouter l'auteur et la date (enregistrés dans 00_Pieces_du_dossier/pieces.csv).
Une pièce n'est annexée que si elle est citée dans le texte : déposer le fichier ne suffit pas, il faut placer son repère [[PIECE …]] à l'endroit où vous l'invoquez. Les annexes sont numérotées dans l'ordre de la première citation ; la note dit « voir l'annexe n° X au présent courrier » et l'index des annexes reprend la description.

## Fichiers produits (dossier « Redaction » du pays)
- Plan_<procédure>_<date>.docx (ou .odt) : le plan type.
- <votre texte>_notes.docx (ou .odt, même format que votre texte) : votre texte avec les notes et l'index des annexes. Votre fichier d'origine n'est jamais modifié : gardez-le pour les corrections, et régénérez.
- <votre texte>_annexes.pdf : toutes les annexes dans l'ordre, chacune précédée d'une page « Annexe n° X » avec sa description ; en option, chaque page porte « Annexe n° X – p. 1/5 ». Les images (JPEG, PNG) sont converties directement ; les fichiers Word ou ODT avec LibreOffice ou, sous Windows, avec Microsoft Word s'il est installé. À défaut, enregistrez la pièce en PDF.
- <votre texte>_rapport.txt : le nombre de notes, la liste des annexes avec leur fichier, et les points à vérifier (repère introuvable ou ambigu, annexe sans fichier…).
- reperes.html : la liste complète des repères (bouton « Liste complète »).
Dans le dossier de base : bibliotheque_blocs.odt (les blocs) et references_juridiques.csv (les textes de référence), communs à tous les pays.

## Bonnes pratiques
- Les lignes bleues de suggestion du plan (« [[repère]]  –  titre ») et le paragraphe gris « Mode d’emploi de ce plan » sont retirés automatiquement du fichier « _notes » : ils ne créent pas de notes. Vous pouvez les laisser dans votre texte de travail.
- Gardez votre texte « avec repères » comme document de travail ; ne retravaillez pas le fichier « _notes » (sinon, les repères ayant disparu, il faudrait tout refaire).
- Relisez toujours les notes générées : titres trop longs, date manquante… se corrigent dans sources.csv (colonnes auteur, titre, date), puis on régénère.
"""

AIDE["bibliotheque"] = """## La bibliothèque de blocs (bibliotheque_blocs.odt)
Des passages juridiques types, par procédure, avec leurs notes : ratification de la Convention contre la torture, article 33 de la Convention de Genève, jurisprudence Soering, article 74/13 de la loi du 15 décembre 1980, dispositif de la demande… Quand la loi ou la jurisprudence change, vous modifiez le bloc une seule fois ici.

## Comment elle est organisée
Le document s'ouvre dans LibreOffice. Les niveaux de titre servent de repères au programme :
- Titre 1 : la procédure (« Non-délivrance d’OQT », « Protection internationale », « 9ter »).
- Titre 2 : la rubrique du plan où le bloc sera inséré, écrite comme dans le plan (ex. « IV. La demande »).
- Titre 3 : le nom du bloc ; ajoutez « (par défaut) » à la fin pour qu'il soit coché d'office.
- Sous le Titre 3 : le texte du bloc, en paragraphes normaux. Mettez-le en forme comme vous voulez (gras, italique) : la mise en forme est reprise.
Les paragraphes gris d'explication sont ignorés.

## Les notes dans un bloc
Elles s'écrivent avec des repères, comme dans votre texte : [[LOI1980, art. 74/13]], [[SOERING, §88]], [[GENEVE, art. 33]]. Les repères des lois, conventions et arrêts sont définis dans « Textes de référence » (references_juridiques.csv). Les repères des sources collectées (comités de l'ONU…) fonctionnent aussi.

## Les variables
Remplacées automatiquement par le pays, le nom et la personne (« Qui demande ? ») choisis dans l'onglet :
- {demandeur} : le nom tapé dans l'onglet (ex. Monsieur A. Exemple, Madame X, Monsieur et Madame Y) ;
- {pays} : Indonésie ; {en_pays} : en Indonésie ; {Le_pays} : L’Indonésie (début de phrase) ; {le_pays} : l’Indonésie (en cours de phrase) ; {a_pays} : à l’Indonésie, au Maroc ; {de_pays} : de l’Indonésie.

## Les accords : Monsieur, Madame ou plusieurs personnes
Les blocs sont écrits une seule fois ; les mots qui changent sont entre accolades. Selon le choix « Qui demande ? » (un homme, une femme, plusieurs personnes ou une famille, plusieurs femmes) :
- {le_demandeur} : le demandeur, la demanderesse, les demandeurs, les demanderesses ; {Le_demandeur} en début de phrase ;
- {du_demandeur} : du demandeur, de la demanderesse, des demandeurs… ; {au_demandeur} : au demandeur, à la demanderesse, aux demandeurs… ;
- {il} : il, elle, ils, elles ; {Il} en début de phrase ;
- {le} : le, la, les (« ne {le} renvoie pas ») ; {lui} : lui, leur (« de {lui} accorder ») ; {eux} : lui, elle, eux, elles (« pour {eux} ») ;
- {son}, {sa}, {ses} : son, sa, ses, ou leur, leur, leurs ;
- {est} : est, sont ; {a} : a, ont ;
- {e} : exposé{e} donne exposé, exposée, exposés, exposées ; {s} : éligible{s} donne éligible ou éligibles.
Pour tout autre mot, deux formes séparées par une barre verticale (singulier|pluriel) : {craint|craignent}, {bénéficie|bénéficient}. Et avec une barre oblique pour masculin/féminin : {soumis/soumise|soumis/soumises}.
Exemple : « {demandeur} {craint|craignent} d'être {persécuté/persécutée|persécutés/persécutées} {en_pays} » donne « Madame X craint d'être persécutée en Indonésie ».
Les passages entre [crochets] sont à adapter à chaque dossier (ex. « [ et de {sa} famille] » : gardez-le ou supprimez-le).

## Un bloc dans un autre
Un paragraphe qui ne contient que [[BLOC nom d’un autre bloc]] insère cet autre bloc. Exemple : la protection internationale reprend les blocs de non-refoulement de la procédure OQT, sans les recopier. Modifier le bloc d'origine suffit.

## Deux façons d'utiliser un bloc
- Recopié dans le plan (« Choisir les blocs… », puis « Créer le plan ») : le texte est copié et vous l'adaptez au dossier. Une modification ultérieure de la bibliothèque ne touche pas ce plan.
- « Vivant » : tapez [[BLOC nom du bloc]] seul dans un paragraphe de votre texte. Au moment de « Générer », il est remplacé par la dernière version du bloc, avec ses notes.

## Ajouter ou modifier un bloc
Copiez un Titre 3 et son texte, collez-les sous la bonne rubrique, modifiez, puis enregistrez au format ODT (« Conserver le format actuel »). Le changement est pris en compte au prochain plan ou à la prochaine génération.
Les blocs de protection internationale et de 9ter commencent par « [À VÉRIFIER…] » : ce sont des textes de départ, antérieurs à la réforme de 2026, à relire avant usage.

## Nouvelle version du programme
Quand une nouvelle version apporte des blocs améliorés : si vous n'aviez pas modifié votre bibliothèque, elle est remplacée automatiquement (l'ancienne est gardée en copie, « bibliotheque_blocs_ancienne_<date>.odt ») ; si vous l'aviez modifiée, elle est conservée et la nouvelle est posée à côté (« bibliotheque_blocs_nouvelle_version.odt »). Un message vous le signale.

## En cas de problème
Si la bibliothèque devient illisible, renommez-la (ex. bibliotheque_ancienne.odt) : le programme en recrée une neuve au prochain usage, et vous pourrez y recopier vos blocs.
"""

AIDE["references"] = """## Les textes de référence (references_juridiques.csv)
La liste des lois, conventions, règlements et arrêts cités dans les blocs et dans vos textes, avec leur repère. Exemple : le repère LOI1980 donne, à la première citation, « Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980, art. 74/13. » et ensuite « Loi du 15 décembre 1980, op.cit., art. 9ter. »

## Ouvrir et modifier
Le fichier s'ouvre dans LibreOffice Calc : jeu de caractères Unicode (UTF-8), séparateur point-virgule uniquement. Enregistrez au format CSV.

## Les colonnes
- repere : le nom court à mettre entre doubles crochets (sans espace, ex. LOI1980, REG2024-1347, SOERING).
- reference_complete : la référence à la première citation.
- reference_courte : la forme reprise ensuite, suivie de « op.cit. ».
- url et consulte_le : facultatifs ; s'ils sont remplis, le lien et la date de consultation sont ajoutés à la première citation.
- a_verifier : une note pour vous-même (ex. « modifiée par la loi du 16 juin 2026 ») ; non reprise dans les notes.

## Après une réforme
Modifiez la ligne concernée (ou ajoutez-en une, ex. LOI2026) puis, si besoin, les blocs qui la citent. Tous les nouveaux plans et toutes les générations suivantes utiliseront la nouvelle version.
"""

AIDE["reperes"] = """## Écrire une note : le repère
Le repère se tape à l'endroit exact de l'appel de note, collé au mot ou au guillemet, avant le point :
  …des violations systématiques[[CCPR/C/IDN/CO/2, §24, p.8]].
  …« traitements inhumains »[[SOERING, §88]].
Il se compose de trois parties, dans cet ordre :
1. la source : la cote (CCPR/C/IDN/CO/2), le repère d'un texte de référence (LOI1980, SOERING), l'identifiant affiché dans la liste, ou quelques mots qui ne désignent qu'une source ;
2. une virgule, puis la précision (paragraphe, page, article…), écrite exactement comme elle doit apparaître dans la note ;
3. éventuellement, des options précédées de « + ».
Double-cliquez sur une ligne de la liste (cadre 2) pour copier le début du repère, puis ajoutez la précision avant les crochets fermants.

## La précision : exemples
- Un paragraphe : [[CCPR/C/IDN/CO/2, §24]] donne « …, §24. »
- Paragraphe et page : [[CCPR/C/IDN/CO/2, §24, p.8]] donne « …, §24, p.8. »
- Plusieurs paragraphes qui se suivent : [[CCPR/C/IDN/CO/2, §§2 à 4, pp.1-2]] ou [[CJUE-M, §§85-92]]
- Des paragraphes séparés : [[CAT/C/IDN/CO/2, §§32 et 35]]
- Une page : [[Human Rights Watch 2026, p.14]] ; plusieurs pages : [[…, pp.8 et 12]] ou [[…, pp.22-23]]
- Un article : [[GENEVE, art. 33]] ; un article et ses subdivisions : [[GENEVE, art. 1er, A, 2]], [[LOI1980, art. 9ter, §1er, al. 1er]]
- Plusieurs articles : [[REG2024-1347, art. 9 et 10]]
- Un point : [[REG2024-1347, art. 3, point 5)]]
- Un considérant : [[REG2024-1347, considérant 22]]
- Une note de bas de page du document cité : [[…, note p.101]]
Sans précision : [[CCPR/C/IDN/CO/2]] (renvoi au document entier).
La même source, citée juste avant, devient « Ibid. » : si la précision change, elle est reprise (« Ibid., §27, p.9. ») ; si elle est identique, seul « Ibid. » est écrit.

## Les options
- +trad : ajoute « Traduction libre de : » devant la référence (citation traduite par vous).
- +souligne : ajoute « ; nous soulignons » (passage mis en gras ou souligné par vous).
- +annexe : met la source en annexe même si sa colonne « annexe » est vide ; +sansannexe : l'inverse.
Exemple : [[CCPR/C/IDN/CO/2, §30 +trad]]

## Plusieurs sources dans une note
Séparez-les par un point-virgule : [[SOERING, §88 ; X-SUEDE-2018, §§52-56 ; X-PAYSBAS-2018, §71 +souligne]]
donne : « Cour eur. D.H., arrêt Soering c. Royaume-Uni, 7 juillet 1989, §88 ; Cour eur. D.H., arrêt X. c. Suède, 9 janvier 2018, §§52-56 ; Cour eur. D.H., arrêt X. c. Pays-Bas, 10 juillet 2018, §71 ; nous soulignons. »

## Autres repères
- [[= texte]] : note écrite telle quelle (commentaire, « Voir supra. »…).
- [[PIECE 03_Attestation_scolaire]] : une pièce du dossier (bouton « Pièces du dossier »).
- [[BLOC nom du bloc]] seul dans un paragraphe : un bloc de la bibliothèque, dans sa dernière version.
- [[INDEX DES ANNEXES]] : l'endroit de l'index des annexes.

## Conventions d'écriture (celles de vos dossiers)
- Pas d'espace entre « § » ou « p. » et le nombre : §24, §§2 à 4, p.8, pp.1-2.
- Une espace après « art. », « al. », « n° » : art. 33, al. 1er, n° 212 381.
- « 1er » pour premier (art. 1er, §1er, al. 1er).
- Les numéros d'arrêts du C.C.E. s'écrivent avec une espace (n° 212 381), ceux du Conseil d'État avec un point (n° 228.778).

## Abréviations
Dans les précisions :
- § : paragraphe ; §§ : paragraphes
- p. : page ; pp. : pages
- art. : article ; al. : alinéa ; point : point d'un article (point 5))
- considérant : considérant d'un acte de l'Union européenne
- n° : numéro ; note : note de bas de page du document cité
- s. ou et s. : et suivants (ex. §§12 et s.)
Dans les notes :
- Ibid. (en italique) : même source que la note précédente
- op.cit. (en italique) : source déjà citée plus haut, en entier
- supra : plus haut dans le texte ; infra : plus bas
- cf. : se reporter à ; voy. ou voir : renvoi
- nous soulignons ; traduction libre
Juridictions et décisions :
- Cour eur. D.H. : Cour européenne des droits de l'homme ; Gde Ch. : Grande Chambre ; req. : requête
- C.J.U.E. : Cour de justice de l'Union européenne (depuis le 1er décembre 2009) ; C.J.C.E. : Cour de justice des Communautés européennes (avant) ; aff. : affaire ; aff. jointes : affaires jointes
- C.I.J. : Cour internationale de Justice
- C. const. : Cour constitutionnelle ; C.E. : Conseil d'État ; C.C.E. : Conseil du contentieux des étrangers ; Cass. : Cour de cassation
- ECLI : identifiant européen de la jurisprudence
Publications :
- M.B. : Moniteur belge ; Doc. parl. : documents parlementaires ; Ch. repr. : Chambre des représentants ; sess. ord. : session ordinaire
- J.O.U.E. : Journal officiel de l'Union européenne ; J.O.C.E. : Journal officiel des Communautés européennes (avant 2003)
- C.I.J. Recueil : recueil des arrêts de la Cour internationale de Justice
Textes :
- CEDH : Convention européenne des droits de l'homme ; PIDCP : Pacte international relatif aux droits civils et politiques ; PIDESC : Pacte international relatif aux droits économiques, sociaux et culturels ; CAT : Convention contre la torture ; CIDE : Convention relative aux droits de l'enfant ; CEDAW : Convention sur l'élimination de toutes les formes de discrimination à l'égard des femmes
Organes et organisations :
- ONU ; HCDH : Haut-Commissariat des Nations Unies aux droits de l'homme ; HCR : Haut-Commissariat des Nations Unies pour les réfugiés ; OMS ; OIT ; CEACR : Commission d'experts pour l'application des conventions et recommandations (OIT)
- CCPR : Comité des droits de l'homme ; CAT : Comité contre la torture ; CESCR : Comité des droits économiques, sociaux et culturels ; CEDAW, CRC, CERD, CRPD, CMW, CED : les autres comités
- EPU : Examen périodique universel ; EUAA : Agence de l'Union européenne pour l'asile ; FRA : Agence des droits fondamentaux de l'Union européenne
- CGRA : Commissariat général aux réfugiés et aux apatrides ; OE : Office des étrangers ; OQT : ordre de quitter le territoire
"""

AIDE["veille_intro"] = """## Vérifier la législation
Cliquez sur « Vérifier en ligne ». Probasile lit la version à jour de chaque texte suivi et le bulletin de veille, puis vous dit en langage simple :
- quels textes ont été modifiés depuis l'état connu, par quel acte, et à partir de quand ;
- quels articles cités dans vos blocs sont touchés, et donc quels blocs relire ;
- s'il y a un nouvel arrêté royal « pays d'origine sûrs », et quels pays ont été ajoutés ou retirés ;
- ce que disent les juristes dans le bulletin de veille, et si une nouvelle version du programme existe.

Le programme repère les changements ; il n'en tire pas de conclusion juridique. Le bouton « Aide » explique tout en détail.
"""

AIDE["veille"] = """## À quoi sert la veille législative ?
Les blocs de la bibliothèque citent des articles de loi (par exemple [[LOI1980, art. 50]]). Quand une loi change, un bloc peut devenir faux sans que rien ne le signale. La veille compare les textes en vigueur avec l'état connu et vous dit quels blocs relire.

## Avec quoi compare-t-on ?
- La première fois : avec l'état du droit sur lequel les blocs du programme ont été écrits (indiqué dans le rapport).
- Ensuite : avec votre dernière vérification « marquée comme vue ».
Cliquez sur « Marquer comme vu » seulement après avoir relu (et si nécessaire corrigé) les blocs signalés : les changements ne seront plus signalés ensuite.

## Les textes suivis
- Loi du 15 décembre 1980 et arrêté royal du 8 octobre 1981 : version consolidée de la banque de données Justel (Moniteur belge). Justel indique, sous chaque article, l'acte qui l'a modifié et la date d'entrée en vigueur. Attention : Justel est mis à jour avec un certain retard (la date de mise à jour figure dans le rapport).
- Règlements (UE) 2024/1347 et 2024/1348, directive 2011/95/UE : EUR-Lex. Une nouvelle « version consolidée » signifie que l'acte a été modifié ; le rapport donne le lien pour voir quoi.
- Arrêté royal établissant la liste des pays d'origine sûrs (article 57/6/1, § 3, de la loi) : un nouvel arrêté chaque année environ, repéré dans la liste des arrêtés d'exécution de la loi.
La liste se modifie (bouton « Textes suivis… », fichier veille_textes.csv du dossier de base) : une ligne par texte, avec son adresse Justel (…/justel) ou son numéro CELEX, et le repère utilisé dans vos blocs.

## Lire le rapport
- « À relire en priorité » : un article cité par vos blocs a été modifié ou abrogé (supprimé), ou un acte européen cité a changé. Le rapport nomme les blocs concernés.
- « Autres changements » : le texte a changé, mais pas les articles que vos blocs citent.
- « Rapport détaillé » : s'ouvre dans le navigateur, avec le texte de l'article avant et après (supprimé en rouge, ajouté en vert) quand il est connu, et les liens officiels, qui font foi.

## Le bulletin de veille
Des juristes y expliquent en langage courant ce qui change (réforme, arrêt important, nouvelle liste de pays sûrs), quels blocs relire, et annoncent les nouvelles versions de Probasile. Il est publié sur la page GitHub du projet (fichier BULLETIN.md) et se lit aussi sans le programme.

## Si la vérification en ligne échoue, ou pour vérifier vous-même
Certains sites refusent les programmes, ou la connexion est coupée. Cliquez sur « Ouvrir les pages dans le navigateur », enregistrez chaque page (Ctrl+S, « Page web complète »), puis « Analyser des pages enregistrées… » et choisissez les fichiers (plusieurs à la fois). Le programme reconnaît :
- la page Justel du texte consolidé (loi, arrêté royal) : enregistrez la page entière (adresse …/justel) ;
- la page Justel d'un arrêté « pays d'origine sûrs » : il lit la liste des pays de l'article 1er et la compare avec la précédente ;
- la page EUR-Lex d'un règlement ou d'une directive ;
- la version consolidée d'EUR-Lex, en page web ou en PDF : il dit alors quels règlements l'ont modifiée et quels articles ils touchent, et si les articles cités dans vos blocs sont concernés.
Une page incomplète (sommaire seul, texte non chargé) est signalée comme telle : le programme n'en tire aucune conclusion.
Les pages lues en ligne sont gardées dans le dossier « veille/pages » du dossier de base : joignez-les à un signalement si un résultat vous semble faux.
Le même bouton ouvre aussi, sans qu'il faille les enregistrer, les sources de référence citées dans le bulletin : les deux listes de pays d'origine sûrs (belge et de l'Union), les règlements (UE) 2026/463 et 2026/464, les arrêts CV, Alace et Canpelli, LH et Ilias et Ahmed, la liste Eurostat des nationalités dont le taux de reconnaissance est de 20 % ou moins, les décisions sur recours (Eurostat), les notes d'orientation de l'Agence de l'Union européenne pour l'asile et les statistiques du CGRA.

## Respect des sites
Probasile n'est pas un robot : c'est vous qui lancez la vérification, pour quelques pages seulement, avec une pause entre chaque page et en s'identifiant clairement. Si vous préférez ne rien faire lire au programme, utilisez « Ouvrir les pages dans le navigateur ».
"""

AIDE["bienvenue"] = """## Bienvenue dans Probasile
Probasile rassemble les sources sur un pays et les range, avec leur référence complète, dans un dossier prêt à être annexé.

## Pour commencer
1. Choisissez le pays et le dossier de base (en haut).
2. Dans chaque onglet, cochez ce que vous voulez ; le bouton « Mode d’emploi de l’onglet » explique chaque option et les fichiers produits.
3. Survolez une case ou un bouton avec la souris : une bulle d'aide apparaît.
4. Cliquez sur « Lancer la collecte ».

## Bon à savoir
- Rien n'est jamais téléchargé deux fois ; vous pouvez relancer autant de fois que vous voulez.
- « Arrêter » interrompt proprement : ce qui est téléchargé est conservé.
- Les réglages sont mémorisés ; « Tout réinitialiser » les remet à zéro d'un coup.
- Le mode d'emploi général reste accessible par le bouton « Aide générale ».
"""


# ---------------------------------------------------------------------------
# Outils d'affichage (tkinter est importé à l'appel, pour que le module reste utilisable sans écran)
# ---------------------------------------------------------------------------
def fenetre_info(root, titre, texte, bouton=None, case_ne_plus=None):
    """Fenêtre défilante. bouton = (libellé, fonction) ajoute un bouton d'action ;
    case_ne_plus = variable booléenne tk pour une case « Ne plus afficher »."""
    import tkinter as tk
    from tkinter import ttk
    w = tk.Toplevel(root)
    w.title(titre)
    w.transient(root)
    haut_ecran = w.winfo_screenheight()
    w.geometry("760x%d" % max(360, min(580, haut_ecran - 160)))
    bas = ttk.Frame(w, padding=10)
    bas.pack(side="bottom", fill="x")  # réservé d'abord : les boutons restent toujours visibles
    w.bas = bas
    cadre = ttk.Frame(w, padding=(12, 10, 12, 0))
    cadre.pack(fill="both", expand=True)
    txt = tk.Text(cadre, wrap="word", relief="flat", padx=10, pady=8, font=("Arial", 11),
                  spacing1=2, spacing3=2, background="#fbfbfa")
    sb = ttk.Scrollbar(cadre, orient="vertical", command=txt.yview)
    txt.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)
    txt.tag_configure("titre", font=("Arial", 13, "bold"), foreground="#08738f", spacing1=12, spacing3=4)
    txt.tag_configure("puce", lmargin1=12, lmargin2=28)
    for ligne in texte.strip("\n").split("\n"):
        if ligne.startswith("## "):
            txt.insert("end", ligne[3:] + "\n", "titre")
        elif ligne.startswith("- "):
            txt.insert("end", "•  " + ligne[2:] + "\n", "puce")
        else:
            txt.insert("end", ligne + "\n")
    txt.configure(state="disabled")
    # molette de la souris (Linux : boutons 4 et 5)
    txt.bind("<Button-4>", lambda e: txt.yview_scroll(-3, "units"))
    txt.bind("<Button-5>", lambda e: txt.yview_scroll(3, "units"))
    if case_ne_plus is not None:
        ttk.Checkbutton(bas, text="Ne plus afficher au démarrage", variable=case_ne_plus).pack(side="left")
    ttk.Button(bas, text="Fermer", command=w.destroy).pack(side="right")
    if bouton:
        lib, fn = bouton
        ttk.Button(bas, text=lib, command=lambda: (w.destroy(), fn())).pack(side="right", padx=6)
    w.bind("<Escape>", lambda e: w.destroy())
    return w


class Bulle:
    """Bulle d'aide qui apparaît après un court survol d'un élément de l'interface."""

    def __init__(self, widget, texte, delai=600):
        self.widget, self.texte, self.delai = widget, texte, delai
        self._id, self._w = None, None
        widget.bind("<Enter>", self._programmer, add="+")
        widget.bind("<Leave>", self._cacher, add="+")
        widget.bind("<ButtonPress>", self._cacher, add="+")

    def _programmer(self, _e=None):
        self._annuler()
        self._id = self.widget.after(self.delai, self._montrer)

    def _annuler(self):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None

    def _montrer(self):
        import tkinter as tk
        if self._w or not self.texte:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._w = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        tk.Label(tw, text=self.texte, justify="left", background="#fffbe6", foreground="#222",
                 relief="solid", borderwidth=1, wraplength=440, padx=8, pady=5, font=("Arial", 10)).pack()

    def _cacher(self, _e=None):
        self._annuler()
        if self._w:
            self._w.destroy()
            self._w = None


def bulle(widget, texte):
    Bulle(widget, texte)
    return widget


# Assistant « Mettre à jour un arrêt ou un bloc » : une fiche par tâche
TACHES_MAJ = [
    ("Remplacer un arrêt par un plus récent", """## Remplacer un arrêt par un plus récent
Exemple : le bloc « Conseil du contentieux des étrangers » cite [[CCE-212381]] et vous voulez citer un arrêt de 2026.
- 1. Cliquez sur « Ajouter une référence… » ci-dessous et remplissez la fiche du nouvel arrêt (repère, par ex. CCE-310000 ; référence complète ; référence courte). Le programme l'écrit correctement dans references_juridiques.csv, même si le texte contient des points-virgules.
- 2. Cliquez sur « Où ce repère est-il utilisé ? » et tapez l'ancien repère (CCE-212381) : la liste des blocs qui le citent s'affiche.
- 3. Cliquez sur « Ouvrir la bibliothèque », allez à ces blocs (Ctrl+H pour chercher), remplacez [[CCE-212381]] par [[CCE-310000]] et, si besoin, le texte qui présente l'arrêt.
- 4. Enregistrez au format ODT (« Conserver le format actuel »).
Ne supprimez pas l'ancienne ligne du fichier des références : d'anciens dossiers la citent peut-être encore.
Les plans déjà créés ne changent pas (le texte y est recopié). Les blocs « vivants » [[BLOC nom]] prendront le nouvel arrêt à la prochaine génération."""),
    ("Corriger ou supprimer une référence", """## Corriger ou supprimer une référence
Exemple : la date d'un arrêt est fausse, le lien a changé, ou vous voulez retirer une référence de test.
- 1. Cliquez sur « Modifier / supprimer… » ci-dessous : la liste des textes de référence s'affiche (tapez un mot pour filtrer).
- 2. Double-cliquez sur la référence : un formulaire s'ouvre, déjà rempli.
- 3. Corrigez et cliquez sur « Enregistrer », ou cliquez sur « Supprimer cette référence ».
Les références fournies avec le programme ne peuvent pas être supprimées (elles seraient recréées) : corrigez-les plutôt. Celles que vous avez ajoutées peuvent l'être.
Vous pouvez aussi tout faire dans LibreOffice Calc (« Ouvrir les textes de référence », séparateur point-virgule, enregistrer au format CSV).
Ne changez pas le repère lui-même (première colonne) : les blocs et vos textes le citent. Pour changer de repère, suivez plutôt « Remplacer un arrêt par un plus récent ».
La correction vaut pour toutes les prochaines générations de notes, dans tous les dossiers."""),
    ("Modifier le texte d'un bloc", """## Modifier le texte d'un bloc
Exemple : reformuler un paragraphe, ajouter une phrase, retirer un argument devenu inutile.
- 1. Cliquez sur « Ouvrir la bibliothèque ».
- 2. Dans le Navigateur de LibreOffice (F5), les Titres 3 sont les blocs : double-cliquez sur celui à modifier.
- 3. Modifiez le texte. Gardez les repères [[…]] (ce sont les notes) et les mots entre accolades comme {demandeur}, {il}, {en_pays} (ce sont les accords automatiques).
- 4. Enregistrez au format ODT.
Pour qu'un bloc soit coché ou non d'office, ajoutez ou retirez « (par défaut) » à la fin de son titre."""),
    ("Ajouter un nouveau bloc", """## Ajouter un nouveau bloc
- 1. Cliquez sur « Ouvrir la bibliothèque ».
- 2. Sous la bonne procédure (Titre 1), trouvez la rubrique du plan (Titre 2) : son texte doit être le début du titre du plan où le bloc doit aller, par ex. « b. La Convention contre la torture ». Au besoin, créez un Titre 2.
- 3. Tapez le nom du bloc en Titre 3 (style « Titre 3 »), puis le texte en paragraphes normaux, avec ses repères [[…]].
- 4. Les lois ou arrêts cités doivent exister dans les textes de référence : sinon, ajoutez-les avec « Ajouter une référence… ».
- 5. Enregistrez au format ODT. Le bloc apparaît aussitôt dans « Choisir les blocs… ».
Pour réutiliser un bloc dans une autre procédure sans le recopier : créez-y un bloc qui ne contient que [[BLOC nom du bloc d'origine]]."""),
    ("Ajouter une section au plan", """## Ajouter une section au plan (et y mettre un bloc)
Exemple : une section sur le délai d'introduction de la demande de protection internationale.
- 1. Onglet « Rédaction », bouton « Modifier les plans… », puis « Ouvrir les plans types ».
- 2. Sous « Protection internationale », à l'endroit voulu, ajoutez un titre (Titre 2 pour une grande partie comme « 3. », Titre 3 pour « A. », Titre 4 pour « 1) »…) et, dessous, l'indication de rédaction. Enregistrez (ODT).
- 3. Bouton « Ouvrir la bibliothèque » : sous « Protection internationale », ajoutez un Titre 2 avec le titre de la nouvelle section (le numéro n'est pas nécessaire), puis le bloc en Titre 3 et son texte. Enregistrez (ODT).
- 4. Créez un plan : la section apparaît, avec le bloc.
Le programme ne tient pas compte des numéros des titres : vous pouvez renuméroter les sections suivantes sans que les blocs ne se perdent."""),
    ("Faire un essai sans rien garder", """## Faire un essai sans rien garder
Pour tester sans risque, ajoutez une référence clairement fictive, puis supprimez-la.
- 1. « Ajouter une référence… » et remplissez :
- Repère : TEST-ARRET
- Référence complète : C.C.E., 1er janvier 2026, n° 999 999 ; arrêt fictif pour essai
- Référence courte : C.C.E., n° 999 999
- Lien et Consulté le : laissez vides
- Remarque : test à supprimer
- 2. Dans votre texte d'essai, tapez [[TEST-ARRET, p.3]] puis générez : la note doit afficher la référence complète, avec le point-virgule.
- 3. « Où ce repère est-il utilisé ? » avec TEST-ARRET : aucun bloc (normal, il n'est dans aucun bloc).
- 4. « Modifier / supprimer… », double-clic sur TEST-ARRET, puis « Supprimer cette référence ». Il n'en reste aucune trace."""),
    ("Ajouter une loi, une convention ou un arrêt", """## Ajouter une loi, une convention ou un arrêt
- 1. Cliquez sur « Ajouter une référence… ».
- 2. Repère : un nom court, sans espace, par ex. CCE-310000, CEDH-GUERGUEB, LOI2027. Il sert ensuite dans vos textes : [[CCE-310000, p.7]].
- 3. Référence complète : telle qu'elle doit apparaître à la première citation, sans la page ni le paragraphe (ils vont dans le repère).
- 4. Référence courte : pour les citations suivantes (suivie de op.cit.).
- 5. Lien et date de consultation : seulement pour un texte en ligne non annexé.
La nouvelle référence est utilisable immédiatement ; elle apparaît aussi dans la liste des repères de l'onglet (bouton « Actualiser »)."""),
    ("Après une réforme législative", """## Après une réforme législative
Exemple : un article de la loi du 15 décembre 1980 est abrogé ou renuméroté.
- 1. Ajoutez la loi modificative avec « Ajouter une référence… » (comme LOI2026 pour la loi du 16 juin 2026).
- 2. « Où ce repère est-il utilisé ? » : tapez LOI1980 pour voir tous les blocs qui citent la loi.
- 3. Dans la bibliothèque, corrigez chaque bloc concerné : nouvel article dans le repère ([[LOI1980, art. 57/6]]), texte adapté. Vous pouvez garder l'ancienne base en note libre : [[REG2024-1347, art. 4 ; = anciennement art. 48/7, abrogé]].
- 4. Si le bloc commence par « [À VÉRIFIER…] », retirez cette mention une fois relu.
- 5. Dans les textes de référence, la colonne a_verifier peut garder une trace (« modifiée par la loi du … »)."""),
]

AIDE["dates_rapports"] = """## Corriger ou compléter les dates des rapports
Le programme reconstitue lui-même les dates (entrée en vigueur du traité, couverture des rapports de l'État, fin des observations finales). Si l'aperçu montre une date fausse ou « remis non » alors que vous connaissez la date, complétez ce fichier :
%(fichier)s

## Comment le remplir
- 1. Cliquez sur « Ouvrir le fichier » : il s'ouvre dans LibreOffice Calc. À l'ouverture, choisissez « Unicode (UTF-8) » et le séparateur « Point-virgule » uniquement.
- 2. Une ligne par rapport, quatre colonnes : le comité (CCPR, CAT, CESCR, CEDAW, CRC, CERD, CRPD, CED, CMW), le numéro du rapport (1 = premier rapport, 2 = deuxième…), la date limite, la date de remise. Laissez la date de remise vide si le rapport n'a pas été remis.
- 3. Dates au format 23/05/2007 (ou 23 mai 2007).
- 4. Les lignes qui commencent par # sont ignorées (mode d'emploi, exemple).
- 5. Enregistrez au format CSV (« Utiliser le format CSV »), puis refaites « Aperçu… ».

## Exemple
CCPR ; 1 ; 23/05/2007 ; 19/01/2012
CCPR ; 2 ; 26/07/2017 ; 29/07/2021
CAT ; 3 ; 30/06/2012 ; (vide : pas remis)

## Où trouver les dates
- La date limite du premier rapport : un an (Pacte civil et politique, Convention contre la torture, discrimination raciale, femmes, travailleurs migrants) ou deux ans (Pacte économique, enfants, handicap, disparitions forcées) après l'entrée en vigueur du traité pour l'État.
- La date limite des rapports suivants : dernier paragraphe des observations finales précédentes.
- La date de remise : sur la couverture du rapport de l'État (« [Date de réception : …] »), ou sur la page « état des rapports » du pays sur le site du Haut-Commissariat.

## Ce qui se passe ensuite
Une ligne remplie à la main remplace, pour ce rapport seulement, ce que le programme avait trouvé ; les autres rapports restent calculés. Dans l'aperçu, ces lignes portent la mention « rempli à la main ». La note de bas de page renvoie alors à l'état des rapports du HCDH (repère HCDH-ETAT-RAPPORTS dans les textes de référence : complétez-y l'adresse de la page du pays et la date de consultation)."""

AIDE["plans"] = """## Les plans types (plans_types.odt)
Les titres des plans OQT, protection internationale et 9ter sont dans ce document, dans le dossier de base. Vous pouvez y ajouter une section, en renommer, en déplacer ou en supprimer, sans toucher au programme. Le changement vaut pour tous les plans créés ensuite.

## Comment il est organisé
- Titre 1 : la procédure (« Non-délivrance d’OQT », « Protection internationale », « 9ter »). Ne les renommez pas.
- Juste dessous : « Titre du document : … » (le grand titre en tête du plan).
- Puis les titres du plan : Titre 2 pour le premier niveau (« I. », « 1. »), Titre 3 pour « A. », Titre 4 pour « 1) », Titre 5 pour « a. », Titre 6 pour « i. ».
- Un paragraphe normal sous un titre : l'indication de rédaction, qui apparaîtra en gris et entre crochets dans le plan.
Astuce : le Navigateur de LibreOffice (F5) montre tout le plan et permet de déplacer une section avec ses sous-sections.

## Ajouter une section (exemple)
(Depuis la version 0.9.16, le plan d'origine de protection internationale contient déjà « 3. L’introduction de la demande dans le délai », avec ses blocs. L'exemple ci-dessous montre comment ajouter une section de ce type vous-même.)
Pour la protection internationale, une section sur le délai d'introduction de la demande, entre « 2. Les faits » et « 3. Pays sûr ? » :
- 1. Cliquez sur « Ouvrir les plans types ».
- 2. Placez le curseur à la fin du dernier paragraphe de « 2. Les faits », appuyez sur Entrée.
- 3. Choisissez le style « Titre 2 » (même niveau que « 2. Les faits ») et tapez par exemple « 3. L’introduction de la demande dans le délai ».
- 4. Entrée, style « Corps de texte » ou « Par défaut », et tapez l'indication de rédaction (facultatif).
- 5. Renumérotez les sections suivantes si vous le souhaitez (4., 5.…) : les blocs et les paragraphes calculés restent à leur place, car le programme ne tient pas compte des numéros.
- 6. Enregistrez au format ODT.

## Mettre un bloc dans la nouvelle section
Dans la bibliothèque de blocs (« Modifier la bibliothèque… »), sous « Protection internationale » (Titre 1), créez un Titre 2 avec le titre de la section, sans le numéro si vous préférez (« L’introduction de la demande dans le délai »), puis votre bloc en Titre 3, suivi de « (par défaut) » s'il doit être coché d'office, et son texte avec ses repères. Le bloc sera inséré sous la nouvelle section.

## Revenir aux plans d'origine
Renommez ou supprimez plans_types.odt : il est recréé tel qu'à l'origine au prochain plan."""
