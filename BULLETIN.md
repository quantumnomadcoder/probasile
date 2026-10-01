<!--
MODE D'EMPLOI (ce passage n'apparaît pas sur la page GitHub)

Probasile lit ce fichier quand on clique sur « Lire le bulletin » ou « Vérifier en ligne ».
Pour ajouter une information : sur GitHub, ouvrir BULLETIN.md → crayon ✏️ → ajouter un bloc
EN HAUT de la liste (sous « Version du programme »), puis « Commit changes ».

Chaque information commence par une ligne « ## date | titre » (date AAAA-MM-JJ), suivie de
lignes facultatives « Textes : », « Blocs : », « Importance : », « Lien : » (une par lien),
sans ligne vide entre elles et terminées par deux espaces (pour qu'elles s'affichent l'une sous
l'autre sur GitHub), puis d'une ligne vide et de l'explication en langage courant (autant de
paragraphes que nécessaire). Dans « Textes : », donner le nom officiel du texte (tel qu'il
apparaît dans les notes de bas de page) suivi de son repère Probasile entre parenthèses.

Exemple :

## 2027-01-15 | Nouvelle liste des pays d'origine sûrs
Textes : Arrêté royal du … établissant la liste des pays d'origine sûrs, M.B., … ; Loi du 15 décembre 1980 sur l'accès au territoire, le séjour, l'établissement et l'éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 57/6/1  
Blocs : Procédure accélérée pour tardiveté  
Importance : haute  
Lien : https://www.ejustice.just.fgov.be/…

Le nouvel arrêté royal ajoute … et retire …. Concrètement, pour une personne originaire de … :

Mettre à jour « Version du programme » à chaque nouvelle Release : Probasile signale alors
aux utilisateurs qu'une nouvelle version existe.
-->

# Bulletin de veille de Probasile

Une version néerlandaise et une version allemande de ce bulletin suivent ci-dessous, après la version française : [Nederlandse versie](#nederlandse-versie) · [Deutsche Fassung](#deutsche-fassung).

Version du programme : 1.1.0

Ce bulletin est rédigé par des juristes. Il explique en langage courant ce qui change dans le droit des étrangers et quels blocs de Probasile relire. Dans le programme : onglet **Rédaction → Vérifier la législation… → Lire le bulletin**. Les textes officiels font foi ; les textes sont désignés par leur nom officiel, suivi entre parenthèses de leur repère dans Probasile. Les repères entre doubles crochets (par exemple, pour l'article 61, § 5, c), du règlement (UE) 2024/1348 : `[[REG2024-1348, art. 61, §5, c)]]`) se collent tels quels dans un texte Probasile.

## 2026-10-01 | Probasile 1.1 : Word, pièces du dossier et installation Windows
Importance : information

**Word.** Le plan type peut être créé au format Word (.docx) ou LibreOffice (.odt), au choix (onglet Rédaction, « Format »). Un texte écrit dans Word reçoit, à la génération, de vraies notes de bas de page Word, l'index des annexes et le PDF des annexes, comme avec LibreOffice.

**Pièces du dossier.** Nouveau bouton « Ajouter une pièce… » : on choisit le fichier (attestation, témoignage, certificat, photo…) et on le décrit (auteur, titre, date). Le repère [[PIECE …]] est copié pour être collé dans le texte. Rappel : une pièce n'est annexée que si elle est citée ; les annexes sont numérotées dans l'ordre de la première citation.

**Annexes.** Les photos (JPEG, PNG) sont converties en PDF directement ; sous Windows, les fichiers Word peuvent l'être par Microsoft Word si LibreOffice manque.

**Installation sous Windows.** installer_windows.bat installe Python lui-même s'il manque (pour votre compte, sans droits d'administrateur), puis les modules et les raccourcis.

**Présenter Probasile.** Le fichier GUIDE_DEMO.md propose une démonstration de 5 ou 25 minutes, les questions fréquentes et un aide-mémoire sur les annexes.

## 2026-09-29 | Conseil du contentieux des étrangers : les nouveaux délais de recours
Textes : Loi du 17 juin 2026 relative au Conseil du contentieux des étrangers, M.B., 19 juin 2026 (LOI-CCE-2026) ; Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 67, § 7, et 68  
Blocs : Procédure accélérée : quand, pourquoi, et comment en sortir  
Importance : haute  
Lien : https://www.ejustice.just.fgov.be/eli/loi/2026/06/17/2026004052/justel  
Lien : https://dofi.ibz.be/fr/themes/faq/appeal/le-conseil-du-contentieux-des-etrangers  
Lien : https://www.fedasil.be/fr/actualites/accueil-des-demandeurs-dasile/entree-en-vigueur-du-pacte-migratoire-europeen

La loi du 17 juin 2026 relative au Conseil du contentieux des étrangers (Moniteur belge du 19 juin 2026) remplace les articles 39/1 et suivants de la loi du 15 décembre 1980. Elle s'applique aux décisions notifiées à partir du 12 juin 2026, date d'application du pacte européen sur la migration et l'asile. Elle organise trois procédures :

- procédure ordinaire : recours dans les 30 jours de la notification (c'est le délai général) ;
- procédure accélérée : 10 jours ;
- procédure urgente : 5 ou 10 jours (notamment procédure à la frontière et certaines décisions accompagnées d'une détention).

Ces délais s'inscrivent dans le cadre du règlement (UE) 2024/1348 : 5 à 10 jours contre un rejet en procédure accélérée, une irrecevabilité ou un retrait implicite, et deux semaines à un mois dans les autres cas (article 67, § 7). Quand le recours n'est pas suspensif, il faut demander au juge l'autorisation de rester, dans un délai d'au moins cinq jours ; aucun éloignement n'est possible entre-temps (article 68, §§ 4 et 5).

Autres changements : l'audience devient l'exception (il faut la demander), la requête est limitée en longueur, et le juge peut accéder à des pièces confidentielles.

À vérifier : les chiffres ci-dessus viennent de sources secondaires (Office des étrangers, presse, cabinets d'avocats). Le texte de la loi n'a pas pu être relu ici, en particulier la répartition exacte des décisions entre les trois procédures. Le délai qui fait foi est celui indiqué dans la décision notifiée, qui doit mentionner les voies de recours (règlement (UE) 2024/1348, article 36, § 3). La veille de Probasile suit désormais cette loi.

## 2026-09-29 | Probasile 1.0.4 : l'onglet Jurisprudence s'enrichit
Importance : information

L'onglet Jurisprudence propose maintenant, pour la recherche C.J.U.E., les règlements (UE) 2026/463 (pays tiers sûr) et 2026/464 (liste de l'Union), ainsi que les actes du pacte : directive (UE) 2024/1346 (accueil), règlements (UE) 2024/1349 (retour à la frontière), 2024/1351 (gestion de l'asile et de la migration), 2024/1356 (filtrage) et 2024/1359 (crise). Ces textes figurent aussi dans les listes « de : », pour filtrer les articles, avec la loi du 17 juin 2026 relative au C.C.E.

Nouveau cadre 6, « Vos sources » : « Ajouter des sources… » ouvre le fichier sources_jurisprudence.csv du dossier de base. On y ajoute un acte européen (numéro CELEX), un site de recherche (adresse) ou un texte (abréviation et façons de le citer), puis on clique sur « Recharger ».

## 2026-09-29 | Pays d'origine sûrs : les deux listes et où les trouver
Textes : Arrêté royal du 3 décembre 2025 portant exécution de l’article 57/6/1, § 3, alinéa 4, de la loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, établissant la liste des pays d’origine sûrs, M.B., 15 décembre 2025 (AR-PAYS-SURS-2025) ; Liste des pays d’origine sûrs au niveau de l’Union : règlement (UE) 2024/1348, annexe II, insérée par le règlement (UE) 2026/464 (version consolidée au 27 février 2026) (UE-LISTE-PAYS-SURS) ; Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 57/6/1 ; Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 61, 62 et annexe II  
Blocs : Pays d’origine sûr : une présomption qui se renverse au cas par cas ; Pays d’origine sûr : les personnes exposées malgré la désignation ; Pays d’origine sûr : une désignation fragile (Maroc)  
Importance : haute  
Lien : https://www.ejustice.just.fgov.be/eli/arrete/2025/12/03/2025009368/justel  
Lien : https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02024R1348-20260227

Deux listes coexistent depuis 2026.

La liste belge est fixée chaque année par arrêté royal (article 57/6/1, § 3, de la loi du 15 décembre 1980). L'arrêté royal du 3 décembre 2025 (Moniteur belge du 15 décembre 2025) désigne : Albanie, Bosnie-Herzégovine, Kosovo, Maroc, Monténégro, Macédoine du Nord et Serbie. À citer : arrêté royal du 3 décembre 2025, article 1er (repère Probasile : `[[AR-PAYS-SURS-2025, art. 1er]]`).

La liste de l'Union figure à l'annexe II du règlement (UE) 2024/1348, insérée par le règlement (UE) 2026/464 : Bangladesh, Colombie, Égypte, Inde, Kosovo, Maroc et Tunisie. Un pays candidat à l'adhésion à l'Union est en principe aussi désigné, sauf conflit armé, mesures restrictives de l'Union liées aux droits fondamentaux, ou taux de reconnaissance supérieur à 20 % à l'échelle de l'Union (article 62, § 1er ter). À citer : règlement (UE) 2024/1348, annexe II (repère Probasile : `[[UE-LISTE-PAYS-SURS]]`).

Où les trouver : dans Probasile, Vérifier la législation… → Ouvrir les pages dans le navigateur ouvre le dernier arrêté belge (la liste est à l'article 1er), la liste des arrêtés d'exécution de la loi (un nouvel arrêté y apparaît en tête) et la version consolidée du règlement (annexe II). La veille signale tout pays ajouté ou retiré de l'une ou l'autre liste.

## 2026-09-29 | Pays d'origine sûr : on peut toujours demander la protection
Textes : Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 26, 28, 34, 38, 42 et 61 ; Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 57/6/1, § 3 ; Convention relative au statut des réfugiés, signée à Genève le 28 juillet 1951 (GENEVE), art. 3  
Blocs : Pays d’origine sûr : une présomption qui se renverse au cas par cas ; Pays d’origine sûr : les personnes exposées malgré la désignation  
Importance : haute

Oui : une personne originaire d'un pays d'origine sûr peut toujours demander et obtenir une protection. Le raisonnement tient en cinq temps.

1. Le droit de demander est ouvert à tous. Toute personne peut présenter une demande de protection internationale, qui est ensuite introduite auprès de l'autorité compétente (règlement (UE) 2024/1348, articles 26 et 28). Aucune disposition n'écarte les ressortissants d'un pays d'origine sûr.

2. Le pays d'origine sûr n'est pas un motif d'irrecevabilité. L'article 38 du règlement énumère les cas où une demande peut être déclarée irrecevable (premier pays d'asile, pays tiers sûr, protection déjà accordée dans un autre État membre, relocalisation par une juridiction pénale internationale, demande tardive après une décision de retour, demande ultérieure sans élément nouveau). Le pays d'origine sûr n'y figure pas : la demande doit être examinée au fond.

3. Il n'entraîne qu'un examen accéléré (article 42, § 1er, e)), qui respecte « les principes de base et les garanties fondamentales » et reste une évaluation individuelle (article 34, § 2).

4. La désignation n'est qu'une présomption, qui se renverse au cas par cas. Le concept « ne peut s'appliquer » que si le demandeur « ne peut fournir d'éléments justifiant pourquoi le concept de pays d'origine sûr ne lui est pas applicable, dans le cadre d'une évaluation individuelle » (article 61, § 5, c)), et il ne s'applique pas à une catégorie de personnes exclue de la désignation (article 61, § 5, b)). En droit belge, le Commissaire général ne peut refuser la protection que « lorsque l'étranger n'a pas fait valoir de raisons sérieuses permettant de penser qu'il ne s'agit pas d'un pays d'origine sûr en raison de sa situation personnelle » (loi du 15 décembre 1980, article 57/6/1, § 3). Le rapport au Roi de l'arrêté du 3 décembre 2025 l'écrit en toutes lettres : « Le simple fait pour un demandeur de protection internationale d'être originaire d'un pays d'origine sûr n'aura en aucun cas pour conséquence automatique que sa demande de protection internationale sera refusée ».

5. La Convention de Genève s'applique « sans discrimination quant à la race, la religion ou le pays d'origine » (article 3), et l'interdiction du renvoi vers un risque de torture ou de traitements inhumains est absolue (article 3 de la Convention européenne des droits de l'homme ; article 19, § 2, de la Charte). La Cour de justice qualifie la désignation de « présomption réfragable » que la personne peut renverser par des raisons sérieuses tenant à sa situation personnelle (arrêt CV, 4 octobre 2024, C-406/22, point 47), car « même dans un pays généralement sûr pour toute sa population, il n'existe aucune garantie absolue de sécurité pour chaque individu » (arrêt Alace et Canpelli, 1er août 2025, C-758/24 et C-759/24, point 97). Le juge doit soulever d'office une méconnaissance des conditions de la désignation (CV, point 98). La personne et le juge doivent avoir « un accès suffisant et adéquat » aux sources sur lesquelles la désignation repose (Alace et Canpelli, points 73 et 87). Ces arrêts ont été rendus sous l'empire de la directive 2013/32/UE, mais ils reposent sur le droit à un recours effectif (article 47 de la Charte).

En pratique : exposer dès le début les raisons sérieuses propres à la personne (persécutions déjà subies, profil exposé, absence de protection), avec des pièces et des sources sur le pays.

## 2026-09-29 | Procédure accélérée : ce que c'est, quand elle s'applique, comment en sortir
Textes : Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 12, 20, 21, 34, 35, 39, 42, 53, 67, 68 et considérant 56 ; Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 57/6/1, §§ 1er et 2 ; C.J.U.E. (gde ch.), arrêt Alace et Canpelli, 1er août 2025, aff. jointes C-758/24 et C-759/24, EU:C:2025:591 (CJUE-ALACE-2025) ; C. const., 25 février 2021, n° 23/2021 (CC-23-2021)  
Blocs : Procédure accélérée : quand, pourquoi, et comment en sortir ; Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité ; Procédure accélérée pour tardiveté  
Importance : haute  
Lien : https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02024R1348-20260227

**Ce que c'est.** La procédure accélérée n'est pas une procédure de rejet ni un examen « au rabais ». C'est un examen complet de la demande au fond (la personne a-t-elle besoin d'une protection ?), mais mené plus vite et avec un recours plus difficile. Depuis le 12 juin 2026, elle est réglée par le règlement (UE) 2024/1348, directement applicable en Belgique ; l'article 57/6/1 de la loi du 15 décembre 1980 la complète.

**Quand elle s'applique.** Seulement dans les cas énumérés par l'article 42, § 1er, du règlement. Le règlement dit que l'autorité « accélère » : dans ces cas, ce n'est plus une simple faculté.

- a) la personne n'a soulevé que des questions sans pertinence pour la protection ;
- b) déclarations manifestement incohérentes, contradictoires, fausses ou peu plausibles, ou qui contredisent les informations disponibles sur le pays d'origine ;
- c) tromperie intentionnelle sur l'identité ou la nationalité (faux documents, destruction de papiers de mauvaise foi) ;
- d) demande présentée uniquement pour retarder ou empêcher un éloignement ;
- e) pays d'origine sûr (liste belge ou liste de l'Union) ;
- f) danger pour la sécurité nationale ou l'ordre public ;
- g) demande ultérieure qui n'est pas irrecevable ;
- h) et i) demande qui n'a pas été présentée « le plus rapidement possible », sans motif valable ;
- j) nationalité d'un pays dont le taux de reconnaissance à l'échelle de l'Union est de 20 % ou moins (voir l'entrée suivante).
Pour les mineurs non accompagnés, la liste est plus courte (article 42, § 3) : pays d'origine sûr, danger pour la sécurité, demande ultérieure, tromperie sur l'identité, seuil de 20 %.

**Pourquoi.** Le législateur veut traiter plus vite les demandes qu'il présume moins susceptibles d'aboutir (considérant 56). Mais la Cour de justice rappelle que l'accélération se fait « sans préjudice de la réalisation d'un examen approprié et exhaustif et de l'accès effectif du demandeur aux garanties et aux principes fondamentaux » (Alace et Canpelli, 1er août 2025, point 102).

**Ce qui ne change pas.** L'examen se fait « dans le respect des principes de base et des garanties fondamentales » (article 42, § 1er). Il reste objectif, impartial et individualisé, sur la base d'informations précises et actualisées sur le pays (article 34, § 2). La personne a la possibilité d'un entretien sur le fond (article 12). Elle garde droit à l'interprète, à l'assistance juridique et à l'évaluation de ses besoins particuliers.

**Ce qui change.**

- Délai d'examen : trois mois au plus à compter de l'introduction de la demande (article 35, § 3), contre six mois en procédure ordinaire (article 35, § 4).
- Délai de recours : entre cinq et dix jours (article 67, § 7, a)), contre deux semaines à un mois en procédure ordinaire (article 67, § 7, b)).
- « Manifestement infondée » : un rejet peut recevoir cette qualification si le droit national le prévoit (article 39, § 4). En Belgique, c'est possible dans les cas de l'article 57/6/1, § 1er, a) à j), mais jamais pour un mineur non accompagné (article 57/6/1, § 2).
- Pas d'effet suspensif automatique du recours (article 68, § 3, a), i)). Il faut demander au juge l'autorisation de rester pendant le recours, dans un délai d'au moins cinq jours après la notification. Aucun éloignement n'est possible tant que ce délai court ou que le juge n'a pas statué, et l'assistance juridique gratuite est due sur demande (article 68, §§ 4 et 5).
- En Belgique, le recours devant le Conseil du contentieux des étrangers suit désormais la loi du 17 juin 2026 : 30 jours en procédure ordinaire, 10 jours en procédure accélérée, 5 ou 10 jours en procédure urgente (voir l'entrée « Conseil du contentieux des étrangers : les nouveaux délais de recours »). Le délai applicable est indiqué dans la décision notifiée : vérifiez-le toujours.

**Comment l'éviter ou en sortir.**

- Vulnérabilité : si le soutien nécessaire ne peut être fourni dans la procédure accélérée, l'autorité « n'applique pas, ou cesse d'appliquer » cette procédure, en particulier pour les victimes de torture, de viol ou d'autres formes graves de violence (article 21, § 2). L'évaluation des besoins de garanties procédurales spéciales commence dès la présentation de la demande et se termine dans les 30 jours (article 20). Il faut donc signaler tôt et produire des attestations médicales ou psychologiques.
- Complexité : des questions de fait ou de droit trop complexes justifient le passage à la procédure ordinaire (article 42, § 2). La personne en est informée.
- Mineurs non accompagnés : seulement dans les cas de l'article 42, § 3. La Cour constitutionnelle avait déjà annulé l'application plus large de la procédure accélérée à ces mineurs (arrêt n° 23/2021 du 25 février 2021).
- Seuil de 20 % : voir l'entrée suivante.
- Retard : invoquer les motifs valables (voir la section « délai » de Probasile).
- Pays d'origine sûr : renverser la présomption par des raisons sérieuses personnelles (voir l'entrée « on peut toujours demander la protection »).
- Procédure à la frontière : elle n'est pas appliquée, ou cesse de l'être, notamment pour des raisons médicales, y compris de santé mentale, ou lorsque le soutien nécessaire ne peut être fourni aux personnes ayant des besoins particuliers (article 53, § 2).

## 2026-09-29 | Seuil de 20 % : où trouver le taux et comment le contester
Textes : Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 34, 39, 42, § 1er, j), 42, § 3, e), 45 et considérant 56 ; Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 57/6/1, § 2 ; Eurostat, « Countries of citizenship with an asylum recognition rate for international protection of 20% or lower », année de référence 2025, données extraites le 21 mai 2026 (Union sans le Danemark, décisions de première instance, base migr_asydec1pc) (EUROSTAT-20) ; Eurostat, base de données migr_asydcfina, « Final decisions in appeal or review on applications by type of decision, citizenship, age and sex – annual data » (EUROSTAT-FINALES) ; Agence de l’Union européenne pour l’asile, Latest Asylum Trends – Annual Analysis, « Recognition rates » (EUAA-TAUX) ; Agence de l’Union européenne pour l’asile, notes d’orientation par pays (Country Guidance), article 11 du règlement (UE) 2021/2303 (EUAA-ORIENTATION) ; Commissariat général aux réfugiés et aux apatrides, statistiques d’asile mensuelles et rapports annuels (CGRA-CHIFFRES)  
Blocs : Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité  
Importance : haute  
Lien : https://ec.europa.eu/eurostat/documents/d/migration-asylum/countries-of-citizenship-with-an-asylum-recognition-rate-of-20-or-lower-1  
Lien : https://ec.europa.eu/eurostat/databrowser/view/migr_asydcfina/default/table?lang=fr  
Lien : https://www.euaa.europa.eu/asylum-knowledge/country-guidance  
Lien : https://www.cgra.be/fr/chiffres

**La règle.** L'examen est accéléré lorsque la personne a la nationalité d'un pays pour lequel « la proportion de décisions prises par l'autorité responsable de la détermination qui octroient une protection internationale est, selon les dernières données disponibles d'Eurostat concernant la moyenne annuelle à l'échelle de l'Union, de 20 % ou moins » (règlement (UE) 2024/1348, article 42, § 1er, j) ; pour les mineurs non accompagnés, article 42, § 3, e)). Ce critère ne vise que la procédure : il ne permet jamais, à lui seul, de refuser la protection, et l'examen reste individuel (article 34, § 2). À la frontière, il rend aussi la procédure à la frontière obligatoire (article 45, § 1er).

**Où trouver le taux.** Eurostat publie une liste établie « solely for the purpose » du règlement : « Countries of citizenship with an asylum recognition rate for international protection of 20% or lower ». La version actuelle porte sur l'année 2025, avec des données extraites le 21 mai 2026. Le calcul :

- au numérateur, les décisions qui octroient le statut de réfugié ou la protection subsidiaire (les statuts humanitaires nationaux ne comptent pas) ;
- au dénominateur, toutes les décisions de première instance ;
- pour l'Union sans le Danemark, et uniquement les décisions de première instance, donc sans les recours.
La base de données correspondante s'appelle migr_asydec1pc. Un taux marqué « (u) » est peu fiable : il repose sur moins de 30 décisions. Les liens s'ouvrent depuis Probasile : Vérifier la législation… → Ouvrir les pages dans le navigateur.

**Comment le contester.**

0. Avant tout : le cas par cas s'applique toujours. Quel que soit le motif d'accélération, l'autorité examine chaque demande « de manière objective, impartiale et individualisée », avec les déclarations et documents de la personne et des informations précises et actualisées sur son pays (règlement (UE) 2024/1348, article 34, § 2). L'examen accéléré respecte « les principes de base et les garanties fondamentales » (article 42, § 1er). Le seuil de 20 % ne règle que le rythme de la procédure, jamais son issue : il ne figure pas parmi les motifs d'irrecevabilité (article 38), et aucune disposition ne permet de rejeter une demande à cause de ce seul taux. La Cour de justice rappelle qu'il n'existe « aucune garantie absolue de sécurité pour chaque individu », même dans un pays généralement sûr (Alace et Canpelli, 1er août 2025, C-758/24 et C-759/24, point 97). Un taux statistique, qui ne décrit que des décisions passées, peut encore moins préjuger de la situation d'une personne. Enfin, l'interdiction de renvoyer quelqu'un vers un risque de torture ou de traitements inhumains est absolue (article 3 de la Convention européenne des droits de l'homme ; article 19, § 2, de la Charte).
1. Vérifier le chiffre. Seul compte le dernier taux annuel d'Eurostat, pour l'ensemble de l'Union. Ni le taux belge, ni un taux qui inclut les statuts humanitaires, ni une année plus ancienne ne correspondent au critère. Un taux marqué « (u) » ne peut pas fonder sérieusement l'accélération.
2. Changement important dans le pays depuis la publication des données (article 42, § 1er, j)). Exemples : coup d'État, conflit, vague de répression, nouvelle loi pénale. Si l'Agence de l'Union européenne pour l'asile (AUEA) a constaté un tel changement dans une note d'orientation, les États doivent s'y référer (article 42, § 1er, alinéa 2).
3. Catégorie de personnes pour qui le taux n'est pas représentatif. Le texte vise « une catégorie de personnes pour lesquelles la proportion de 20 % ou moins ne peut être considérée comme représentative de leurs besoins en matière de protection, compte tenu, entre autres, des différences importantes entre les décisions prises en première instance et les décisions finales ». Le considérant 56 précise qu'il s'agit notamment d'un « motif spécifique de persécution ». Exemples : opposants politiques, personnes LGBTIQ, femmes exposées à des violences de genre, minorités. Les notes d'orientation de l'AUEA identifient souvent ces profils à risque.
4. Première instance contre décisions finales. Le taux ignore les recours gagnés. Eurostat publie séparément les décisions finales (base migr_asydcfina). L'AUEA souligne que ses taux « do not account for cases decided by the judiciary », et que le taux de reconnaissance en recours était de 19 % en 2024 pour l'ensemble des nationalités (fiche EUAA/2025/37). Pour une nationalité donnée, un écart important entre la première instance et les décisions finales montre que le taux n'est pas représentatif. Le taux de protection du CGRA pour cette nationalité (statistiques mensuelles) peut aussi aider.
5. Le considérant 56 est clair : dans ces deux cas d'exception, « l'examen de la demande ne devrait pas être accéléré ». Demandez au CGRA de ne pas appliquer la procédure accélérée ou de cesser de l'appliquer, et à tout le moins de motiver sa décision sur ces exceptions.
6. Pas de « manifestement infondée » sur ce seul motif. Le règlement ne permet cette qualification que si le droit national l'autorise (article 39, § 4). Or l'article 57/6/1, § 2, ne l'autorise que dans les situations a) à j) de son § 1er, parmi lesquelles le seuil de 20 % ne figure pas.
   ⚠ Point d'attention : c'est une interprétation, que le Conseil du contentieux des étrangers n'a pas encore tranchée. Elle repose sur l'article 57/6/1, § 2, tel qu'il était rédigé le 29 septembre 2026 : vérifiez qu'une loi n'a pas, depuis, ajouté le seuil de 20 % à la liste belge (la veille de Probasile le signalera). Le CGRA pourrait objecter que le règlement est directement applicable et que son article 39, § 4, vise tous les cas de l'article 42. Réponse : cette disposition exige une autorisation donnée « en vertu du droit national », et le législateur belge ne l'a donnée que pour les cas qu'il énumère. Même si l'argument est écarté, le point 0 reste entier.
7. Les autres voies restent ouvertes : vulnérabilité (article 21, § 2), complexité (article 42, § 2), raisons médicales à la frontière (article 53, § 2).

## 2026-09-29 | Pays tiers sûr : ce qui change avec le règlement (UE) 2026/463
Textes : Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 38, 57, 59 et 68 ; Règlement (UE) 2026/463 du Parlement européen et du Conseil du 24 février 2026 modifiant le règlement (UE) 2024/1348 en ce qui concerne l’application du concept de pays tiers sûr, J.O.U.E., L 463, 26 février 2026 (REG2026-463) ; C.J.U.E., arrêt LH c. Bevándorlási és Menekültügyi Hivatal, 19 mars 2020, aff. C-564/18 (CJUE-LH-2020) ; Cour eur. D.H. (Gde Ch.), arrêt Ilias et Ahmed c. Hongrie, 21 novembre 2019, req. n° 47287/15 (ILIAS-AHMED)  
Blocs : Pays tiers sûr : conditions strictes et évaluation individuelle  
Importance : haute  
Lien : https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02024R1348-20260227

De quoi s'agit-il ? Le concept de pays tiers sûr permet de déclarer une demande irrecevable, sans l'examiner au fond, parce que la personne pourrait obtenir une protection dans un autre pays que le sien, hors de l'Union (article 38, § 1er, b)).

Les conditions de base n'ont pas changé : dans ce pays, les non-ressortissants ne doivent craindre ni pour leur vie ni pour leur liberté, ne courir aucun risque réel d'atteintes graves, être protégés contre le refoulement, et pouvoir demander et recevoir une « protection effective » (article 59, § 1er). Si le pays n'a pas ratifié et ne respecte pas la Convention de Genève, cette protection suppose au minimum le droit d'y rester, des moyens de subsistance suffisants, l'accès aux soins et à l'éducation, et une protection jusqu'à une solution durable (article 57).

Ce qui change : le lien exigé entre la personne et le pays tiers. Depuis le règlement (UE) 2026/463, il suffit de l'une de ces trois situations (article 59, § 5, b)) :

- un « lien de connexion » rendant raisonnable que la personne s'y rende (par exemple de la famille ou un séjour antérieur) ;
- un simple transit par ce pays « sur le trajet vers l'Union » ;
- un accord ou un arrangement avec ce pays, qui l'oblige à examiner le bien-fondé des demandes de protection des personnes concernées.
C'est un élargissement important. Sous la directive 2013/32/UE, la Cour de justice avait jugé contraire au droit de l'Union une réglementation déclarant irrecevable une demande au seul motif que la personne était arrivée par un État où elle n'était pas exposée à la persécution ou dans lequel était assuré un degré de protection adéquat (arrêt LH, 19 mars 2020, C-564/18, dispositif, point 1).

Ce qui ne change pas, et qu'il faut invoquer :

- l'évaluation individuelle : le concept ne s'applique pas si la personne apporte des éléments montrant qu'il ne lui est pas applicable (article 59, § 5, a)) — transit bref ou forcé, violences subies dans ce pays, absence réelle d'accès à l'asile, risque de renvoi en chaîne ;
- les mineurs non accompagnés : seulement si c'est conforme à leur intérêt supérieur, après assurance de prise en charge et de protection effective immédiate, et jamais sur la base d'un accord (article 59, § 6) ;
- la réadmission : pas d'irrecevabilité s'il est clair que le pays ne réadmettra pas la personne (article 38, § 1er, b)), et accès à la procédure s'il ne l'admet pas (article 59, § 9) ;
- l'information : un document doit informer le pays tiers, dans sa langue, que la demande n'a pas été examinée au fond (article 59, § 8, b)) ;
- la Convention européenne des droits de l'homme : l'État qui renvoie doit apprécier de manière approfondie si la personne aura accès à une procédure d'asile adéquate dans le pays tiers (Cour eur. D.H., Ilias et Ahmed c. Hongrie, 21 novembre 2019, §§ 137-141 et 152-154) ;
- le recours : pas d'effet suspensif automatique contre une décision d'irrecevabilité (article 68, § 3, b)) ; demander au juge l'autorisation de rester (article 68, §§ 4 et 5).

Le règlement (UE) 2024/1348 s'applique depuis le 12 juin 2026 ; certaines dispositions relatives aux pays sûrs s'appliquaient dès le 27 février 2026 (article 79).

## 2026-09-29 | Règlement (UE) 2024/1348 modifié le 24 février 2026
Textes : Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 59, 60, 61, 62, 64, 68, 79 et annexe II ; Règlement (UE) 2026/463 du Parlement européen et du Conseil du 24 février 2026 modifiant le règlement (UE) 2024/1348 en ce qui concerne l’application du concept de pays tiers sûr, J.O.U.E., L 463, 26 février 2026 (REG2026-463) ; Règlement (UE) 2026/464 du Parlement européen et du Conseil du 24 février 2026 modifiant le règlement (UE) 2024/1348 en ce qui concerne l’établissement d’une liste des pays d’origine sûrs au niveau de l’Union, J.O.U.E., L 464, 26 février 2026 (REG2026-464)  
Blocs : aucun des articles 26, 34 et 42 cités dans les blocs d'origine n'est modifié  
Importance : information  
Lien : https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02024R1348-20260227

Deux règlements du 24 février 2026 modifient le règlement (UE) 2024/1348 (version consolidée au 27 février 2026) : le règlement (UE) 2026/464 (pays d'origine sûrs au niveau de l'Union) et le règlement (UE) 2026/463 (pays tiers sûr). Voir les deux informations détaillées ci-dessus. Un rectificatif du 25 novembre 2025 corrige par ailleurs la rédaction des articles 7, 28, 39, 48 et 50.

## 2026-09-29 | Probasile 1.0 : la veille législative
Importance : information

Nouveau bouton « Vérifier la législation… » (onglet Rédaction). Il compare la version à jour de la loi du 15 décembre 1980, de l'arrêté royal du 8 octobre 1981, des règlements (UE) 2024/1347 et 2024/1348 et de l'arrêté royal « pays d'origine sûrs » avec l'état du droit sur lequel les blocs ont été écrits, et signale les articles modifiés et les blocs à relire. Il accepte aussi les pages enregistrées depuis le navigateur (HTML) et les versions consolidées d'EUR-Lex en PDF.

## 2026-06-19 | Réforme de l'asile : ce qui change pour le délai de huit jours
Textes : Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 48/6, 50 et 50/1 ; Règlement (UE) 2024/1348 du Parlement européen et du Conseil du 14 mai 2024 instituant une procédure commune en matière de protection internationale dans l’Union et abrogeant la directive 2013/32/UE, J.O.U.E., L, 2024/1348, 22 mai 2024 (REG2024-1348), art. 26, 28 et 42  
Blocs : Délai dépassé : ni irrecevabilité ni rejet automatique ; Procédure accélérée pour tardiveté ; Demande présentée dans le délai de huit jours  
Importance : haute  
Lien : https://www.ejustice.just.fgov.be/eli/loi/1980/12/15/1980121550/justel#Art.50

La loi du 16 juin 2026 (Moniteur belge du 19 juin 2026), en vigueur le 12 juin 2026, adapte la loi du 15 décembre 1980 aux règlements européens de 2024 sur l'asile.

Le délai de huit jours existe toujours : l'article 50, § 1er, prévoit encore que la personne entrée sans remplir les conditions présente sa demande dans les huit jours ouvrables. En revanche, les paragraphes 2 à 5 de l'article 50 sont abrogés, et le règlement (UE) 2024/1348 ne prévoit ni le rejet ni l'irrecevabilité d'une demande au seul motif qu'elle est tardive. Le retard peut seulement, à certaines conditions et sans motif valable, conduire à une procédure accélérée (article 42 du règlement).

Les articles 48/3, 48/4, 48/5 et 48/7 de la loi sont abrogés (la matière relève désormais du règlement (UE) 2024/1347). L'article 48/6 ne règle plus que la production des éléments et pièces à l'appui de la demande, à présenter « le plus rapidement possible » ; ses paragraphes 4 et 5 sont abrogés. Un nouvel article 50/1 organise l'introduction de la demande.

Les blocs de Probasile tiennent compte de cette réforme depuis la version 0.9.

## 2025-12-15 | Liste belge des pays d'origine sûrs : arrêté royal du 3 décembre 2025
Textes : Loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, M.B., 31 décembre 1980 (LOI1980), art. 57/6/1 ; Arrêté royal du 3 décembre 2025 portant exécution de l’article 57/6/1, § 3, alinéa 4, de la loi du 15 décembre 1980 sur l’accès au territoire, le séjour, l’établissement et l’éloignement des étrangers, établissant la liste des pays d’origine sûrs, M.B., 15 décembre 2025 (AR-PAYS-SURS-2025)  
Importance : haute  
Lien : https://www.ejustice.just.fgov.be/eli/arrete/2025/12/03/2025009368/justel

L'arrêté royal du 3 décembre 2025 (Moniteur belge du 15 décembre 2025), en vigueur le jour de sa publication, désigne comme pays d'origine sûrs : l'Albanie, la Bosnie-Herzégovine, le Kosovo, le Maroc, le Monténégro, la Macédoine du Nord et la Serbie.

Selon le rapport au Roi, le Maroc a été ajouté en s'écartant de l'avis du Commissaire général aux réfugiés et aux apatrides, dont la dernière analyse de fond datait de 2021 ; le gouvernement invoque la baisse du taux de protection et la proposition de la Commission européenne (COM/2025/186).

Le rapport au Roi rappelle aussi qu'être originaire d'un pays d'origine sûr n'entraîne pas un refus automatique : la demande fait l'objet d'un examen individuel, et le demandeur peut montrer que, dans sa situation particulière, son pays ne peut pas être considéré comme sûr.

## Nederlandse versie

Deze Nederlandse versie is een vertaling ter informatie; de Franse versie hierboven en de officiële teksten zijn authentiek. Het programma Probasile werkt in het Frans: de namen van knoppen en blokken staan daarom in het Frans, soms met een vertaling tussen haakjes. Citaten uit Franstalige bronnen (koninklijk besluit, verslag aan de Koning, arresten) en uit Europese verordeningen zijn vrij vertaald: controleer de officiële Nederlandse tekst (Belgisch Staatsblad, Publicatieblad van de Europese Unie) voordat u ze citeert. De teksten worden aangeduid met hun officiële naam, gevolgd door hun kenmerk in Probasile tussen haakjes.

### 2026-10-01 | Probasile 1.1: Word, stukken van het dossier en installatie onder Windows
Belang: informatie

**Word.** Het modelplan kan in Word (.docx) of LibreOffice (.odt) worden aangemaakt (tabblad « Rédaction », « Format »). Een tekst die in Word is geschreven, krijgt bij het genereren echte Word-voetnoten, de index van de bijlagen en de pdf van de bijlagen, net als met LibreOffice.

**Stukken van het dossier.** Nieuwe knop « Ajouter une pièce… » (stuk toevoegen): je kiest het bestand (attest, getuigenis, certificaat, foto…) en beschrijft het (auteur, titel, datum). De verwijzing [[PIECE …]] wordt gekopieerd om in de tekst te plakken. Let op: een stuk wordt alleen als bijlage toegevoegd als het in de tekst wordt aangehaald; de bijlagen worden genummerd in de volgorde van de eerste vermelding.

**Bijlagen.** Foto's (JPEG, PNG) worden rechtstreeks naar pdf omgezet; onder Windows kan Microsoft Word de Word-bestanden omzetten als LibreOffice ontbreekt.

**Installatie onder Windows.** installer_windows.bat installeert zelf Python als het ontbreekt (voor jouw account, zonder beheerdersrechten), daarna de modules en de snelkoppelingen.

**Probasile voorstellen.** Het bestand GUIDE_DEMO.md (in het Frans) bevat een demo van 5 of 25 minuten, veelgestelde vragen en een geheugensteun over bijlagen.

### 2026-09-29 | Raad voor Vreemdelingenbetwistingen: de nieuwe beroepstermijnen
Teksten: Wet van 17 juni 2026 betreffende de Raad voor Vreemdelingenbetwistingen, B.S. 19 juni 2026 (LOI-CCE-2026) ; Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 67, § 7, en 68  
Blokken: Procédure accélérée : quand, pourquoi, et comment en sortir  
Belang: hoog  
Link: https://www.ejustice.just.fgov.be/eli/loi/2026/06/17/2026004052/justel  
Link: https://dofi.ibz.be/fr/themes/faq/appeal/le-conseil-du-contentieux-des-etrangers  
Link: https://www.fedasil.be/fr/actualites/accueil-des-demandeurs-dasile/entree-en-vigueur-du-pacte-migratoire-europeen

De wet van 17 juni 2026 betreffende de Raad voor Vreemdelingenbetwistingen (Belgisch Staatsblad van 19 juni 2026) vervangt de artikelen 39/1 en volgende van de wet van 15 december 1980. Ze geldt voor beslissingen die vanaf 12 juni 2026 ter kennis zijn gebracht, de datum waarop het Europees migratie- en asielpact van toepassing werd. Ze voorziet in drie procedures:

- gewone procedure: beroep binnen 30 dagen na de kennisgeving (de algemene termijn);
- versnelde procedure: 10 dagen;
- dringende procedure: 5 of 10 dagen (met name de grensprocedure en bepaalde beslissingen die gepaard gaan met een vasthouding).

Deze termijnen passen in het kader van Verordening (EU) 2024/1348: 5 tot 10 dagen tegen een afwijzing in de versnelde procedure, een niet-ontvankelijkheid of een impliciete intrekking, en twee weken tot een maand in de andere gevallen (artikel 67, § 7). Als het beroep niet schorsend is, moet de rechter gevraagd worden om te mogen blijven, binnen een termijn van ten minste vijf dagen; intussen is geen verwijdering mogelijk (artikel 68, §§ 4 en 5).

Andere wijzigingen: de terechtzitting wordt de uitzondering (ze moet worden gevraagd), het verzoekschrift wordt beperkt in lengte, en de rechter kan vertrouwelijke stukken inzien.

Na te gaan: de cijfers hierboven komen uit secundaire bronnen (Dienst Vreemdelingenzaken, pers, advocatenkantoren). De tekst van de wet kon hier niet worden nagelezen, in het bijzonder de precieze verdeling van de beslissingen over de drie procedures. De termijn die geldt, is de termijn die vermeld staat in de ter kennis gebrachte beslissing, die de rechtsmiddelen moet vermelden (Verordening (EU) 2024/1348, artikel 36, § 3). De wetgevingsopvolging van Probasile volgt deze wet voortaan.

### 2026-09-29 | Probasile 1.0.4: het tabblad Jurisprudence wordt uitgebreid
Belang: informatie

Het tabblad « Jurisprudence » (rechtspraak) biedt voor de zoekopdracht bij het Hof van Justitie nu ook de Verordeningen (EU) 2026/463 (veilig derde land) en 2026/464 (lijst van de Unie) aan, evenals de handelingen van het pact: Richtlijn (EU) 2024/1346 (opvang), Verordeningen (EU) 2024/1349 (terugkeer aan de grens), 2024/1351 (asiel- en migratiebeheer), 2024/1356 (screening) en 2024/1359 (crisis). Deze teksten staan ook in de lijsten « de : » (van:) om op artikelen te filteren, samen met de wet van 17 juni 2026 betreffende de Raad voor Vreemdelingenbetwistingen.

Nieuw kader 6, « Vos sources » (uw bronnen): « Ajouter des sources… » (bronnen toevoegen) opent het bestand sources_jurisprudence.csv in de basismap. Daarin voegt u een Europese handeling (CELEX-nummer), een zoeksite (adres) of een tekst (afkorting en manieren om hem te citeren) toe, en klikt u daarna op « Recharger » (herladen).

### 2026-09-29 | Veilige landen van herkomst: de twee lijsten en waar u ze vindt
Teksten: Koninklijk besluit van 3 december 2025 tot uitvoering van artikel 57/6/1, § 3, vierde lid, van de wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, tot vaststelling van de lijst van veilige landen van herkomst, B.S. 15 december 2025 (AR-PAYS-SURS-2025) ; Lijst van veilige landen van herkomst op Unieniveau: Verordening (EU) 2024/1348, bijlage II, ingevoegd bij Verordening (EU) 2026/464 (geconsolideerde versie van 27 februari 2026) (UE-LISTE-PAYS-SURS) ; Wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, B.S. 31 december 1980 (LOI1980), art. 57/6/1 ; Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 61, 62 en bijlage II  
Blokken: Pays d’origine sûr : une présomption qui se renverse au cas par cas ; Pays d’origine sûr : les personnes exposées malgré la désignation ; Pays d’origine sûr : une désignation fragile (Maroc)  
Belang: hoog  
Link: https://www.ejustice.just.fgov.be/eli/arrete/2025/12/03/2025009368/justel  
Link: https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:02024R1348-20260227

Sinds 2026 bestaan er twee lijsten naast elkaar.

De Belgische lijst wordt elk jaar vastgesteld bij koninklijk besluit (artikel 57/6/1, § 3, van de wet van 15 december 1980). Het koninklijk besluit van 3 december 2025 (Belgisch Staatsblad van 15 december 2025) wijst aan: Albanië, Bosnië en Herzegovina, Kosovo, Marokko, Montenegro, Noord-Macedonië en Servië. Te citeren: koninklijk besluit van 3 december 2025, artikel 1 (kenmerk in Probasile: `[[AR-PAYS-SURS-2025, art. 1er]]`).

De lijst van de Unie staat in bijlage II bij Verordening (EU) 2024/1348, ingevoegd bij Verordening (EU) 2026/464: Bangladesh, Colombia, Egypte, India, Kosovo, Marokko en Tunesië. Een kandidaat-lidstaat van de Unie wordt in principe ook aangewezen, behalve bij een gewapend conflict, beperkende maatregelen van de Unie die verband houden met de grondrechten, of een erkenningsgraad van meer dan 20 % op het niveau van de Unie (artikel 62, § 1ter). Te citeren: Verordening (EU) 2024/1348, bijlage II (kenmerk in Probasile: `[[UE-LISTE-PAYS-SURS]]`).

Waar u ze vindt: in Probasile opent « Vérifier la législation… » (wetgeving controleren) → « Ouvrir les pages dans le navigateur » (pagina's openen in de browser) het laatste Belgische besluit (de lijst staat in artikel 1), de lijst van uitvoeringsbesluiten van de wet (een nieuw besluit verschijnt bovenaan) en de geconsolideerde versie van de verordening (bijlage II). De wetgevingsopvolging meldt elk land dat aan een van beide lijsten wordt toegevoegd of eruit wordt geschrapt.

### 2026-09-29 | Veilig land van herkomst: u kunt altijd bescherming vragen
Teksten: Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 26, 28, 34, 38, 42 en 61 ; Wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, B.S. 31 december 1980 (LOI1980), art. 57/6/1, § 3 ; Verdrag betreffende de status van vluchtelingen, ondertekend te Genève op 28 juli 1951 (GENEVE), art. 3  
Blokken: Pays d’origine sûr : une présomption qui se renverse au cas par cas ; Pays d’origine sûr : les personnes exposées malgré la désignation  
Belang: hoog

Ja: iemand die afkomstig is uit een veilig land van herkomst kan altijd bescherming vragen en krijgen. De redenering verloopt in vijf stappen.

1. Het recht om een verzoek in te dienen staat open voor iedereen. Iedereen kan een verzoek om internationale bescherming doen, dat vervolgens wordt ingediend bij de bevoegde autoriteit (Verordening (EU) 2024/1348, artikelen 26 en 28). Geen enkele bepaling sluit onderdanen van een veilig land van herkomst uit.

2. Het veilige land van herkomst is geen grond van niet-ontvankelijkheid. Artikel 38 van de verordening somt de gevallen op waarin een verzoek niet-ontvankelijk kan worden verklaard (eerste land van asiel, veilig derde land, bescherming al verleend in een andere lidstaat, overbrenging door een internationaal strafhof, laattijdig verzoek na een terugkeerbesluit, volgend verzoek zonder nieuw element). Het veilige land van herkomst staat daar niet bij: het verzoek moet ten gronde worden onderzocht.

3. Het leidt alleen tot een versneld onderzoek (artikel 42, § 1, e)), dat « de basisbeginselen en fundamentele waarborgen » eerbiedigt en een individuele beoordeling blijft (artikel 34, § 2).

4. De aanwijzing is slechts een vermoeden, dat geval per geval kan worden weerlegd. Het begrip « kan alleen worden toegepast » als de verzoeker « geen elementen kan aanvoeren die rechtvaardigen waarom het begrip veilig land van herkomst in het kader van een individuele beoordeling niet op hem van toepassing is » (artikel 61, § 5, c)), en het is niet van toepassing op een categorie personen die van de aanwijzing is uitgesloten (artikel 61, § 5, b)). Naar Belgisch recht kan de Commissaris-generaal de bescherming alleen weigeren « wanneer de vreemdeling geen ernstige redenen heeft aangevoerd om aan te nemen dat het, gelet op zijn persoonlijke situatie, niet om een veilig land van herkomst gaat » (wet van 15 december 1980, artikel 57/6/1, § 3). Het verslag aan de Koning bij het besluit van 3 december 2025 zegt het uitdrukkelijk: « Het loutere feit dat een verzoeker om internationale bescherming afkomstig is uit een veilig land van herkomst, zal in geen geval automatisch tot gevolg hebben dat zijn verzoek om internationale bescherming wordt geweigerd ».

5. Het Vluchtelingenverdrag van Genève geldt « zonder onderscheid naar ras, godsdienst of land van herkomst » (artikel 3), en het verbod op terugzending naar een risico van foltering of onmenselijke behandeling is absoluut (artikel 3 van het Europees Verdrag voor de Rechten van de Mens; artikel 19, § 2, van het Handvest). Het Hof van Justitie noemt de aanwijzing een « weerlegbaar vermoeden » dat de betrokkene kan weerleggen met ernstige redenen die verband houden met zijn persoonlijke situatie (arrest CV, 4 oktober 2024, C-406/22, punt 47), want « zelfs in een land dat over het algemeen veilig is voor de hele bevolking, bestaat er voor geen enkel individu een absolute veiligheidsgarantie » (arrest Alace en Canpelli, 1 augustus 2025, C-758/24 en C-759/24, punt 97). De rechter moet ambtshalve opwerpen dat de voorwaarden voor de aanwijzing niet zijn nageleefd (CV, punt 98). De betrokkene en de rechter moeten « voldoende en adequate toegang » hebben tot de bronnen waarop de aanwijzing berust (Alace en Canpelli, punten 73 en 87). Deze arresten zijn gewezen onder Richtlijn 2013/32/EU, maar ze berusten op het recht op een doeltreffende voorziening in rechte (artikel 47 van het Handvest).

In de praktijk: zet van bij het begin de ernstige redenen uiteen die eigen zijn aan de persoon (reeds ondergane vervolging, blootgesteld profiel, gebrek aan bescherming), met stukken en bronnen over het land.

### 2026-09-29 | Versnelde procedure: wat het is, wanneer ze geldt, hoe u eruit komt
Teksten: Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 12, 20, 21, 34, 35, 39, 42, 53, 67, 68 en overweging 56 ; Wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, B.S. 31 december 1980 (LOI1980), art. 57/6/1, §§ 1 en 2 ; HvJ EU (Grote kamer), arrest Alace en Canpelli, 1 augustus 2025, gevoegde zaken C-758/24 en C-759/24, EU:C:2025:591 (CJUE-ALACE-2025) ; Grondwettelijk Hof, 25 februari 2021, nr. 23/2021 (CC-23-2021)  
Blokken: Procédure accélérée : quand, pourquoi, et comment en sortir ; Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité ; Procédure accélérée pour tardiveté  
Belang: hoog  
Link: https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:02024R1348-20260227

**Wat het is.** De versnelde procedure is geen afwijzingsprocedure en geen onderzoek « op koopjes ». Het is een volledig onderzoek ten gronde (heeft de persoon bescherming nodig?), maar sneller gevoerd en met een moeilijker beroep. Sinds 12 juni 2026 wordt ze geregeld door Verordening (EU) 2024/1348, die rechtstreeks van toepassing is in België; artikel 57/6/1 van de wet van 15 december 1980 vult haar aan.

**Wanneer ze geldt.** Alleen in de gevallen die artikel 42, § 1, van de verordening opsomt. De verordening zegt dat de autoriteit het onderzoek « versnelt »: in die gevallen is het geen loutere mogelijkheid meer.

- a) de persoon heeft alleen punten aangevoerd die niet relevant zijn voor de bescherming;
- b) kennelijk inconsistente, tegenstrijdige, valse of onwaarschijnlijke verklaringen, of verklaringen die in strijd zijn met de beschikbare informatie over het land van herkomst;
- c) opzettelijke misleiding over identiteit of nationaliteit (valse documenten, te kwader trouw vernietigde papieren);
- d) verzoek alleen ingediend om een verwijdering uit te stellen of te verhinderen;
- e) veilig land van herkomst (Belgische lijst of lijst van de Unie);
- f) gevaar voor de nationale veiligheid of de openbare orde;
- g) volgend verzoek dat niet niet-ontvankelijk is;
- h) en i) verzoek dat niet « zo spoedig mogelijk » is gedaan, zonder geldige reden;
- j) nationaliteit van een land waarvoor de erkenningsgraad op het niveau van de Unie 20 % of minder bedraagt (zie de volgende rubriek).

Voor niet-begeleide minderjarigen is de lijst korter (artikel 42, § 3): veilig land van herkomst, gevaar voor de veiligheid, volgend verzoek, misleiding over de identiteit, drempel van 20 %.

**Waarom.** De wetgever wil verzoeken die hij minder kansrijk acht, sneller behandelen (overweging 56). Maar het Hof van Justitie herinnert eraan dat de versnelling plaatsvindt « onverminderd een passend en volledig onderzoek en de daadwerkelijke toegang van de verzoeker tot de fundamentele waarborgen en beginselen » (Alace en Canpelli, 1 augustus 2025, punt 102).

**Wat niet verandert.** Het onderzoek gebeurt « met inachtneming van de basisbeginselen en fundamentele waarborgen » (artikel 42, § 1). Het blijft objectief, onpartijdig en individueel, op basis van nauwkeurige en actuele informatie over het land (artikel 34, § 2). De persoon krijgt de mogelijkheid van een persoonlijk onderhoud ten gronde (artikel 12). Hij behoudt het recht op een tolk, op juridische bijstand en op de beoordeling van zijn bijzondere behoeften.

**Wat verandert.**

- Behandelingstermijn: ten hoogste drie maanden na de indiening van het verzoek (artikel 35, § 3), tegenover zes maanden in de gewone procedure (artikel 35, § 4).
- Beroepstermijn: tussen vijf en tien dagen (artikel 67, § 7, a)), tegenover twee weken tot een maand in de gewone procedure (artikel 67, § 7, b)).
- « Kennelijk ongegrond »: een afwijzing kan die kwalificatie krijgen als het nationale recht dat bepaalt (artikel 39, § 4). In België kan dat in de gevallen van artikel 57/6/1, § 1, a) tot j), maar nooit voor een niet-begeleide minderjarige (artikel 57/6/1, § 2).
- Geen automatisch schorsende werking van het beroep (artikel 68, § 3, a), i)). De rechter moet gevraagd worden om tijdens het beroep te mogen blijven, binnen een termijn van ten minste vijf dagen na de kennisgeving. Geen verwijdering is mogelijk zolang die termijn loopt of de rechter niet heeft beslist, en kosteloze rechtsbijstand is op verzoek verschuldigd (artikel 68, §§ 4 en 5).
- In België volgt het beroep bij de Raad voor Vreemdelingenbetwistingen voortaan de wet van 17 juni 2026: 30 dagen in de gewone procedure, 10 dagen in de versnelde procedure, 5 of 10 dagen in de dringende procedure (zie de rubriek « Raad voor Vreemdelingenbetwistingen: de nieuwe beroepstermijnen »). De toepasselijke termijn staat in de ter kennis gebrachte beslissing: controleer hem altijd.

**Hoe u haar vermijdt of eruit komt.**

- Kwetsbaarheid: als de nodige steun in de versnelde procedure niet kan worden geboden, « past » de autoriteit die procedure « niet toe of niet langer toe », in het bijzonder voor slachtoffers van foltering, verkrachting of andere ernstige vormen van geweld (artikel 21, § 2). De beoordeling van de behoefte aan bijzondere procedurele waarborgen begint zodra het verzoek wordt gedaan en eindigt binnen 30 dagen (artikel 20). Meld dus vroeg en leg medische of psychologische attesten voor.
- Complexiteit: te complexe feitelijke of juridische vragen rechtvaardigen de overgang naar de gewone procedure (artikel 42, § 2). De persoon wordt daarvan op de hoogte gebracht.
- Niet-begeleide minderjarigen: alleen in de gevallen van artikel 42, § 3. Het Grondwettelijk Hof had de ruimere toepassing van de versnelde procedure op deze minderjarigen al vernietigd (arrest nr. 23/2021 van 25 februari 2021).
- Drempel van 20 %: zie de volgende rubriek.
- Laattijdigheid: geldige redenen aanvoeren (zie het onderdeel « délai » (termijn) in Probasile).
- Veilig land van herkomst: het vermoeden weerleggen met ernstige persoonlijke redenen (zie de rubriek « u kunt altijd bescherming vragen »).
- Grensprocedure: ze wordt niet of niet langer toegepast, met name om medische redenen, ook van geestelijke gezondheid, of wanneer de nodige steun niet kan worden geboden aan personen met bijzondere behoeften (artikel 53, § 2).

### 2026-09-29 | Drempel van 20 %: waar u het percentage vindt en hoe u het betwist
Teksten: Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 34, 39, 42, § 1, j), 42, § 3, e), 45 en overweging 56 ; Wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, B.S. 31 december 1980 (LOI1980), art. 57/6/1, § 2 ; Eurostat, « Countries of citizenship with an asylum recognition rate for international protection of 20% or lower », referentiejaar 2025, gegevens geëxtraheerd op 21 mei 2026 (Unie zonder Denemarken, beslissingen in eerste aanleg, databank migr_asydec1pc) (EUROSTAT-20) ; Eurostat, databank migr_asydcfina, « Final decisions in appeal or review on applications by type of decision, citizenship, age and sex – annual data » (EUROSTAT-FINALES) ; Asielagentschap van de Europese Unie, Latest Asylum Trends – Annual Analysis, « Recognition rates » (EUAA-TAUX) ; Asielagentschap van de Europese Unie, landenbeleidsnota's (Country Guidance), artikel 11 van Verordening (EU) 2021/2303 (EUAA-ORIENTATION) ; Commissariaat-generaal voor de Vluchtelingen en de Staatlozen, maandelijkse asielstatistieken en jaarverslagen (CGRA-CHIFFRES)  
Blokken: Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité  
Belang: hoog  
Link: https://ec.europa.eu/eurostat/documents/d/migration-asylum/countries-of-citizenship-with-an-asylum-recognition-rate-of-20-or-lower-1  
Link: https://ec.europa.eu/eurostat/databrowser/view/migr_asydcfina/default/table?lang=en  
Link: https://www.euaa.europa.eu/asylum-knowledge/country-guidance  
Link: https://www.cgra.be/fr/chiffres

**De regel.** Het onderzoek wordt versneld wanneer de persoon de nationaliteit heeft van een land waarvoor « het aandeel beslissingen van de beslissingsautoriteit tot toekenning van internationale bescherming volgens de meest recente beschikbare jaarlijkse gemiddelde gegevens van Eurostat voor de hele Unie 20 % of minder bedraagt » (Verordening (EU) 2024/1348, artikel 42, § 1, j); voor niet-begeleide minderjarigen artikel 42, § 3, e)). Dit criterium betreft alleen de procedure: het laat nooit toe, op zich alleen, de bescherming te weigeren, en het onderzoek blijft individueel (artikel 34, § 2). Aan de grens maakt het ook de grensprocedure verplicht (artikel 45, § 1).

**Waar u het percentage vindt.** Eurostat publiceert een lijst die « solely for the purpose » van de verordening is opgesteld: « Countries of citizenship with an asylum recognition rate for international protection of 20% or lower ». De huidige versie betreft het jaar 2025, met gegevens geëxtraheerd op 21 mei 2026. De berekening:

- in de teller: de beslissingen die de vluchtelingenstatus of de subsidiaire beschermingsstatus toekennen (nationale humanitaire statussen tellen niet mee);
- in de noemer: alle beslissingen in eerste aanleg;
- voor de Unie zonder Denemarken, en alleen de beslissingen in eerste aanleg, dus zonder de beroepen.

De bijbehorende databank heet migr_asydec1pc. Een percentage met de vermelding « (u) » is weinig betrouwbaar: het berust op minder dan 30 beslissingen. De links worden geopend vanuit Probasile: « Vérifier la législation… » → « Ouvrir les pages dans le navigateur ».

**Hoe u het betwist.**

0. Eerst en vooral: de beoordeling geval per geval geldt altijd. Wat ook de grond voor versnelling is, de autoriteit onderzoekt elk verzoek « op objectieve, onpartijdige en individuele wijze », met de verklaringen en documenten van de persoon en nauwkeurige en actuele informatie over zijn land (Verordening (EU) 2024/1348, artikel 34, § 2). Het versnelde onderzoek eerbiedigt « de basisbeginselen en fundamentele waarborgen » (artikel 42, § 1). De drempel van 20 % bepaalt alleen het tempo van de procedure, nooit de uitkomst: hij staat niet bij de gronden van niet-ontvankelijkheid (artikel 38), en geen enkele bepaling laat toe een verzoek af te wijzen op grond van dat percentage alleen. Het Hof van Justitie herinnert eraan dat er « voor geen enkel individu een absolute veiligheidsgarantie » bestaat, zelfs niet in een land dat over het algemeen veilig is (Alace en Canpelli, 1 augustus 2025, C-758/24 en C-759/24, punt 97). Een statistisch percentage, dat alleen vroegere beslissingen beschrijft, kan nog minder vooruitlopen op de situatie van een persoon. Ten slotte is het verbod om iemand terug te sturen naar een risico van foltering of onmenselijke behandeling absoluut (artikel 3 van het Europees Verdrag voor de Rechten van de Mens; artikel 19, § 2, van het Handvest).
1. Het cijfer controleren. Alleen het meest recente jaarcijfer van Eurostat voor de hele Unie telt. Het Belgische percentage, een percentage dat humanitaire statussen omvat of een ouder jaar beantwoorden niet aan het criterium. Een percentage met « (u) » kan de versnelling niet ernstig onderbouwen.
2. Belangrijke verandering in het land sinds de publicatie van de gegevens (artikel 42, § 1, j)). Voorbeelden: staatsgreep, conflict, golf van repressie, nieuwe strafwet. Heeft het Asielagentschap van de Europese Unie (EUAA) zo'n verandering vastgesteld in een landenbeleidsnota, dan moeten de staten daarnaar verwijzen (artikel 42, § 1, tweede alinea).
3. Categorie personen voor wie het percentage niet representatief is. De tekst beoogt « een categorie personen voor wie het percentage van 20 % of minder niet als representatief voor hun beschermingsbehoeften kan worden beschouwd, onder meer rekening houdend met aanzienlijke verschillen tussen beslissingen in eerste aanleg en definitieve beslissingen ». Overweging 56 verduidelijkt dat het met name gaat om een « specifieke vervolgingsgrond ». Voorbeelden: politieke opposanten, LGBTIQ-personen, vrouwen die blootstaan aan gendergerelateerd geweld, minderheden. De landenbeleidsnota's van het EUAA wijzen die risicoprofielen vaak aan.
4. Eerste aanleg tegenover definitieve beslissingen. Het percentage negeert gewonnen beroepen. Eurostat publiceert de definitieve beslissingen afzonderlijk (databank migr_asydcfina). Het EUAA benadrukt dat zijn percentages « do not account for cases decided by the judiciary », en dat de erkenningsgraad in beroep in 2024 voor alle nationaliteiten samen 19 % bedroeg (factsheet EUAA/2025/37). Voor een bepaalde nationaliteit toont een groot verschil tussen eerste aanleg en definitieve beslissingen aan dat het percentage niet representatief is. Het beschermingspercentage van het CGVS voor die nationaliteit (maandelijkse statistieken) kan ook helpen.
5. Overweging 56 is duidelijk: in die twee uitzonderingsgevallen « zou het onderzoek van het verzoek niet mogen worden versneld ». Vraag het CGVS de versnelde procedure niet of niet langer toe te passen, en zijn beslissing ten minste op die uitzonderingen te motiveren.
6. Geen « kennelijk ongegrond » op deze grond alleen. De verordening laat die kwalificatie alleen toe als het nationale recht ze toestaat (artikel 39, § 4). Artikel 57/6/1, § 2, staat ze echter alleen toe in de situaties a) tot j) van § 1, waarbij de drempel van 20 % niet voorkomt.
   ⚠ Aandachtspunt: dit is een interpretatie, waarover de Raad voor Vreemdelingenbetwistingen nog niet heeft beslist. Ze berust op artikel 57/6/1, § 2, zoals het luidde op 29 september 2026: ga na of een wet de drempel van 20 % sindsdien niet aan de Belgische lijst heeft toegevoegd (de wetgevingsopvolging van Probasile zal dat melden). Het CGVS zou kunnen tegenwerpen dat de verordening rechtstreeks van toepassing is en dat haar artikel 39, § 4, alle gevallen van artikel 42 beoogt. Antwoord: die bepaling vereist een toestemming « krachtens het nationale recht », en de Belgische wetgever heeft die alleen gegeven voor de gevallen die hij opsomt. Ook als het argument wordt verworpen, blijft punt 0 volledig overeind.
7. De andere wegen blijven open: kwetsbaarheid (artikel 21, § 2), complexiteit (artikel 42, § 2), medische redenen aan de grens (artikel 53, § 2).

### 2026-09-29 | Veilig derde land: wat verandert met Verordening (EU) 2026/463
Teksten: Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 38, 57, 59 en 68 ; Verordening (EU) 2026/463 van het Europees Parlement en de Raad van 24 februari 2026 tot wijziging van Verordening (EU) 2024/1348 wat betreft de toepassing van het begrip veilig derde land, PB L 463, 26 februari 2026 (REG2026-463) ; HvJ EU, arrest LH t. Bevándorlási és Menekültügyi Hivatal, 19 maart 2020, zaak C-564/18 (CJUE-LH-2020) ; EHRM (Grote Kamer), arrest Ilias en Ahmed t. Hongarije, 21 november 2019, verz. nr. 47287/15 (ILIAS-AHMED)  
Blokken: Pays tiers sûr : conditions strictes et évaluation individuelle  
Belang: hoog  
Link: https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:02024R1348-20260227

Waarover gaat het? Het begrip veilig derde land laat toe een verzoek niet-ontvankelijk te verklaren, zonder het ten gronde te onderzoeken, omdat de persoon bescherming zou kunnen krijgen in een ander land dan het zijne, buiten de Unie (artikel 38, § 1, b)).

De basisvoorwaarden zijn niet veranderd: in dat land mogen niet-onderdanen niet vrezen voor hun leven of hun vrijheid, geen reëel risico op ernstige schade lopen, moeten zij beschermd zijn tegen refoulement, en moeten zij « daadwerkelijke bescherming » kunnen vragen en krijgen (artikel 59, § 1). Als het land het Vluchtelingenverdrag van Genève niet heeft geratificeerd en niet naleeft, veronderstelt die bescherming minstens het recht om er te blijven, voldoende middelen van bestaan, toegang tot gezondheidszorg en onderwijs, en bescherming tot er een duurzame oplossing is (artikel 57).

Wat verandert: de vereiste band tussen de persoon en het derde land. Sinds Verordening (EU) 2026/463 volstaat één van deze drie situaties (artikel 59, § 5, b)):

- een « band » die het redelijk maakt dat de persoon naar dat land gaat (bijvoorbeeld familie of een eerder verblijf);
- een louter doorreizen door dat land « op weg naar de Unie »;
- een overeenkomst of regeling met dat land, die het verplicht de gegrondheid van de verzoeken om bescherming van de betrokken personen te onderzoeken.

Dat is een belangrijke uitbreiding. Onder Richtlijn 2013/32/EU had het Hof van Justitie een regeling in strijd met het Unierecht geoordeeld die een verzoek niet-ontvankelijk verklaarde op de enkele grond dat de persoon was aangekomen via een staat waar hij niet werd blootgesteld aan vervolging of waar een passende mate van bescherming was gewaarborgd (arrest LH, 19 maart 2020, C-564/18, dictum, punt 1).

Wat niet verandert, en wat u moet aanvoeren:

- de individuele beoordeling: het begrip is niet van toepassing als de persoon elementen aanbrengt waaruit blijkt dat het niet op hem van toepassing is (artikel 59, § 5, a)) — korte of gedwongen doorreis, geweld ondergaan in dat land, geen reële toegang tot asiel, risico op kettingrefoulement;
- niet-begeleide minderjarigen: alleen als dat in hun belang is, na de verzekering van opvang en onmiddellijke daadwerkelijke bescherming, en nooit op basis van een overeenkomst (artikel 59, § 6);
- de overname: geen niet-ontvankelijkheid als duidelijk is dat het land de persoon niet zal overnemen (artikel 38, § 1, b)), en toegang tot de procedure als het hem niet toelaat (artikel 59, § 9);
- de informatie: een document moet het derde land, in zijn taal, meedelen dat het verzoek niet ten gronde is onderzocht (artikel 59, § 8, b));
- het Europees Verdrag voor de Rechten van de Mens: de staat die terugstuurt, moet grondig nagaan of de persoon in het derde land toegang zal hebben tot een adequate asielprocedure (EHRM, Ilias en Ahmed t. Hongarije, 21 november 2019, §§ 137-141 en 152-154);
- het beroep: geen automatisch schorsende werking tegen een beslissing van niet-ontvankelijkheid (artikel 68, § 3, b)); de rechter vragen om te mogen blijven (artikel 68, §§ 4 en 5).

Verordening (EU) 2024/1348 is van toepassing sinds 12 juni 2026; sommige bepalingen over veilige landen waren al van toepassing vanaf 27 februari 2026 (artikel 79).

### 2026-09-29 | Verordening (EU) 2024/1348 gewijzigd op 24 februari 2026
Teksten: Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 59, 60, 61, 62, 64, 68, 79 en bijlage II ; Verordening (EU) 2026/463 van het Europees Parlement en de Raad van 24 februari 2026 tot wijziging van Verordening (EU) 2024/1348 wat betreft de toepassing van het begrip veilig derde land, PB L 463, 26 februari 2026 (REG2026-463) ; Verordening (EU) 2026/464 van het Europees Parlement en de Raad van 24 februari 2026 tot wijziging van Verordening (EU) 2024/1348 wat betreft de vaststelling van een lijst van veilige landen van herkomst op Unieniveau, PB L 464, 26 februari 2026 (REG2026-464)  
Blokken: geen van de artikelen 26, 34 en 42 die in de oorspronkelijke blokken worden aangehaald, is gewijzigd  
Belang: informatie  
Link: https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:02024R1348-20260227

Twee verordeningen van 24 februari 2026 wijzigen Verordening (EU) 2024/1348 (geconsolideerde versie van 27 februari 2026): Verordening (EU) 2026/464 (veilige landen van herkomst op Unieniveau) en Verordening (EU) 2026/463 (veilig derde land). Zie de twee uitgebreide rubrieken hierboven. Een rectificatie van 25 november 2025 verbetert daarnaast de formulering van de artikelen 7, 28, 39, 48 en 50.

### 2026-09-29 | Probasile 1.0: de wetgevingsopvolging
Belang: informatie

Nieuwe knop « Vérifier la législation… » (wetgeving controleren, tabblad « Rédaction »). Hij vergelijkt de bijgewerkte versie van de wet van 15 december 1980, het koninklijk besluit van 8 oktober 1981, de Verordeningen (EU) 2024/1347 en 2024/1348 en het koninklijk besluit « veilige landen van herkomst » met de stand van het recht waarop de blokken zijn geschreven, en meldt de gewijzigde artikelen en de blokken die moeten worden herlezen. Hij aanvaardt ook pagina's die vanuit de browser zijn opgeslagen (HTML) en geconsolideerde versies van EUR-Lex in pdf.

### 2026-06-19 | Asielhervorming: wat verandert voor de termijn van acht dagen
Teksten: Wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, B.S. 31 december 1980 (LOI1980), art. 48/6, 50 en 50/1 ; Verordening (EU) 2024/1348 van het Europees Parlement en de Raad van 14 mei 2024 tot vaststelling van een gemeenschappelijke procedure voor internationale bescherming in de Unie en tot intrekking van Richtlijn 2013/32/EU, PB L, 2024/1348, 22 mei 2024 (REG2024-1348), art. 26, 28 en 42  
Blokken: Délai dépassé : ni irrecevabilité ni rejet automatique ; Procédure accélérée pour tardiveté ; Demande présentée dans le délai de huit jours  
Belang: hoog  
Link: https://www.ejustice.just.fgov.be/eli/loi/1980/12/15/1980121550/justel#Art.50

De wet van 16 juni 2026 (Belgisch Staatsblad van 19 juni 2026), in werking op 12 juni 2026, past de wet van 15 december 1980 aan de Europese asielverordeningen van 2024 aan.

De termijn van acht dagen bestaat nog steeds: artikel 50, § 1, bepaalt nog altijd dat wie binnenkomt zonder aan de voorwaarden te voldoen, zijn verzoek binnen acht werkdagen doet. De paragrafen 2 tot 5 van artikel 50 zijn daarentegen opgeheven, en Verordening (EU) 2024/1348 voorziet niet in de afwijzing of de niet-ontvankelijkheid van een verzoek op de enkele grond dat het laattijdig is. De vertraging kan alleen, onder bepaalde voorwaarden en zonder geldige reden, tot een versnelde procedure leiden (artikel 42 van de verordening).

De artikelen 48/3, 48/4, 48/5 en 48/7 van de wet zijn opgeheven (de materie valt voortaan onder Verordening (EU) 2024/1347). Artikel 48/6 regelt alleen nog de overlegging van de elementen en stukken ter staving van het verzoek, die « zo spoedig mogelijk » moeten worden voorgelegd; de paragrafen 4 en 5 ervan zijn opgeheven. Een nieuw artikel 50/1 regelt de indiening van het verzoek.

De blokken van Probasile houden sinds versie 0.9 rekening met deze hervorming.

### 2025-12-15 | Belgische lijst van veilige landen van herkomst: koninklijk besluit van 3 december 2025
Teksten: Wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, B.S. 31 december 1980 (LOI1980), art. 57/6/1 ; Koninklijk besluit van 3 december 2025 tot uitvoering van artikel 57/6/1, § 3, vierde lid, van de wet van 15 december 1980 betreffende de toegang tot het grondgebied, het verblijf, de vestiging en de verwijdering van vreemdelingen, tot vaststelling van de lijst van veilige landen van herkomst, B.S. 15 december 2025 (AR-PAYS-SURS-2025)  
Belang: hoog  
Link: https://www.ejustice.just.fgov.be/eli/arrete/2025/12/03/2025009368/justel

Het koninklijk besluit van 3 december 2025 (Belgisch Staatsblad van 15 december 2025), in werking op de dag van de bekendmaking, wijst als veilige landen van herkomst aan: Albanië, Bosnië en Herzegovina, Kosovo, Marokko, Montenegro, Noord-Macedonië en Servië.

Volgens het verslag aan de Koning is Marokko toegevoegd in afwijking van het advies van de Commissaris-generaal voor de Vluchtelingen en de Staatlozen, wiens laatste grondige analyse dateerde van 2021; de regering beroept zich op de daling van het beschermingspercentage en op het voorstel van de Europese Commissie (COM/2025/186).

Het verslag aan de Koning herinnert er ook aan dat afkomstig zijn uit een veilig land van herkomst niet leidt tot een automatische weigering: het verzoek wordt individueel onderzocht, en de verzoeker kan aantonen dat zijn land in zijn bijzondere situatie niet als veilig kan worden beschouwd.

## Deutsche Fassung

Diese deutsche Fassung ist eine Übersetzung zur Information; maßgeblich sind die französische Fassung oben und die amtlichen Texte. Das Programm Probasile ist französischsprachig: Die Namen der Schaltflächen und Bausteine stehen daher auf Französisch, teilweise mit einer Übersetzung in Klammern. Zitate aus französischsprachigen Quellen (Königlicher Erlass, Bericht an den König, Urteile) und aus EU-Verordnungen sind frei übersetzt: Prüfen Sie vor dem Zitieren den amtlichen deutschen Wortlaut (Belgisches Staatsblatt, Amtsblatt der Europäischen Union). Die Texte werden mit ihrer amtlichen Bezeichnung angegeben, gefolgt von ihrem Kürzel in Probasile in Klammern.

### 2026-10-01 | Probasile 1.1: Word, Unterlagen der Akte und Installation unter Windows
Bedeutung: Information

**Word.** Die Mustergliederung kann als Word- (.docx) oder LibreOffice-Datei (.odt) erstellt werden (Reiter « Rédaction », « Format »). Ein in Word geschriebener Text erhält beim Erzeugen echte Word-Fußnoten, das Anlagenverzeichnis und das PDF der Anlagen, wie mit LibreOffice.

**Unterlagen der Akte.** Neue Schaltfläche « Ajouter une pièce… » (Unterlage hinzufügen): Datei wählen (Bescheinigung, Zeugenaussage, Attest, Foto…) und beschreiben (Autor, Titel, Datum). Der Verweis [[PIECE …]] wird kopiert, um ihn in den Text einzufügen. Hinweis: Eine Unterlage wird nur dann als Anlage beigefügt, wenn sie im Text zitiert wird; die Anlagen werden in der Reihenfolge der ersten Zitierung nummeriert.

**Anlagen.** Fotos (JPEG, PNG) werden direkt in PDF umgewandelt; unter Windows kann Microsoft Word die Word-Dateien umwandeln, wenn LibreOffice fehlt.

**Installation unter Windows.** installer_windows.bat installiert Python selbst, falls es fehlt (für dein Konto, ohne Administratorrechte), danach die Module und die Verknüpfungen.

**Probasile vorstellen.** Die Datei GUIDE_DEMO.md (auf Französisch) enthält eine Demo von 5 oder 25 Minuten, häufige Fragen und eine Gedächtnisstütze zu den Anlagen.

### 2026-09-29 | Rat für Ausländerstreitsachen: die neuen Beschwerdefristen
Texte: Gesetz vom 17. Juni 2026 über den Rat für Ausländerstreitsachen, B.S. vom 19. Juni 2026 (LOI-CCE-2026) ; Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 67 Abs. 7 und Art. 68  
Bausteine: Procédure accélérée : quand, pourquoi, et comment en sortir  
Bedeutung: hoch  
Link: https://www.ejustice.just.fgov.be/eli/loi/2026/06/17/2026004052/justel  
Link: https://dofi.ibz.be/fr/themes/faq/appeal/le-conseil-du-contentieux-des-etrangers  
Link: https://www.fedasil.be/fr/actualites/accueil-des-demandeurs-dasile/entree-en-vigueur-du-pacte-migratoire-europeen

Das Gesetz vom 17. Juni 2026 über den Rat für Ausländerstreitsachen (Belgisches Staatsblatt vom 19. Juni 2026) ersetzt die Artikel 39/1 ff. des Gesetzes vom 15. Dezember 1980. Es gilt für Entscheidungen, die ab dem 12. Juni 2026 zugestellt wurden, dem Tag, ab dem das Europäische Migrations- und Asylpaket anwendbar ist. Es sieht drei Verfahren vor:

- ordentliches Verfahren: Beschwerde innerhalb von 30 Tagen nach der Zustellung (die allgemeine Frist);
- beschleunigtes Verfahren: 10 Tage;
- Dringlichkeitsverfahren: 5 oder 10 Tage (insbesondere Grenzverfahren und bestimmte Entscheidungen, die mit einer Inhaftnahme einhergehen).

Diese Fristen fügen sich in den Rahmen der Verordnung (EU) 2024/1348 ein: 5 bis 10 Tage gegen eine Ablehnung im beschleunigten Verfahren, eine Unzulässigkeit oder eine stillschweigende Rücknahme, und zwei Wochen bis ein Monat in den übrigen Fällen (Artikel 67 Absatz 7). Hat die Beschwerde keine aufschiebende Wirkung, muss beim Gericht innerhalb einer Frist von mindestens fünf Tagen beantragt werden, bleiben zu dürfen; bis dahin ist keine Abschiebung möglich (Artikel 68 Absätze 4 und 5).

Weitere Änderungen: Die mündliche Verhandlung wird zur Ausnahme (sie muss beantragt werden), die Beschwerdeschrift wird in ihrer Länge begrenzt, und das Gericht kann vertrauliche Unterlagen einsehen.

Zu prüfen: Die obigen Angaben stammen aus Sekundärquellen (Ausländeramt, Presse, Anwaltskanzleien). Der Gesetzestext konnte hier nicht nachgelesen werden, insbesondere nicht die genaue Zuordnung der Entscheidungen zu den drei Verfahren. Maßgeblich ist die Frist, die in der zugestellten Entscheidung angegeben ist; diese muss die Rechtsbehelfe nennen (Verordnung (EU) 2024/1348, Artikel 36 Absatz 3). Die Rechtsbeobachtung von Probasile verfolgt dieses Gesetz ab jetzt.

### 2026-09-29 | Probasile 1.0.4: der Reiter Jurisprudence wird erweitert
Bedeutung: Information

Der Reiter « Jurisprudence » (Rechtsprechung) bietet für die Suche beim Gerichtshof der Europäischen Union jetzt auch die Verordnungen (EU) 2026/463 (sicherer Drittstaat) und 2026/464 (Liste der Union) an, ebenso die Rechtsakte des Pakets: Richtlinie (EU) 2024/1346 (Aufnahme), Verordnungen (EU) 2024/1349 (Rückkehr an der Grenze), 2024/1351 (Asyl- und Migrationsmanagement), 2024/1356 (Screening) und 2024/1359 (Krisen). Diese Texte stehen auch in den Listen « de : » (von:), um nach Artikeln zu filtern, zusammen mit dem Gesetz vom 17. Juni 2026 über den Rat für Ausländerstreitsachen.

Neuer Rahmen 6, « Vos sources » (Ihre Quellen): « Ajouter des sources… » (Quellen hinzufügen) öffnet die Datei sources_jurisprudence.csv im Basisordner. Dort fügen Sie einen EU-Rechtsakt (CELEX-Nummer), eine Suchseite (Adresse) oder einen Text (Kürzel und Zitierweisen) hinzu und klicken anschließend auf « Recharger » (neu laden).

### 2026-09-29 | Sichere Herkunftsstaaten: die zwei Listen und wo Sie sie finden
Texte: Königlicher Erlass vom 3. Dezember 2025 zur Ausführung von Artikel 57/6/1 § 3 Absatz 4 des Gesetzes vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, zur Festlegung der Liste der sicheren Herkunftsstaaten, B.S. vom 15. Dezember 2025 (AR-PAYS-SURS-2025) ; Liste der sicheren Herkunftsstaaten auf Unionsebene: Verordnung (EU) 2024/1348, Anhang II, eingefügt durch die Verordnung (EU) 2026/464 (konsolidierte Fassung vom 27. Februar 2026) (UE-LISTE-PAYS-SURS) ; Gesetz vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, B.S. vom 31. Dezember 1980 (LOI1980), Art. 57/6/1 ; Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 61, 62 und Anhang II  
Bausteine: Pays d’origine sûr : une présomption qui se renverse au cas par cas ; Pays d’origine sûr : les personnes exposées malgré la désignation ; Pays d’origine sûr : une désignation fragile (Maroc)  
Bedeutung: hoch  
Link: https://www.ejustice.just.fgov.be/eli/arrete/2025/12/03/2025009368/justel  
Link: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:02024R1348-20260227

Seit 2026 bestehen zwei Listen nebeneinander.

Die belgische Liste wird jedes Jahr durch Königlichen Erlass festgelegt (Artikel 57/6/1 § 3 des Gesetzes vom 15. Dezember 1980). Der Königliche Erlass vom 3. Dezember 2025 (Belgisches Staatsblatt vom 15. Dezember 2025) bestimmt: Albanien, Bosnien und Herzegowina, Kosovo, Marokko, Montenegro, Nordmazedonien und Serbien. Zu zitieren: Königlicher Erlass vom 3. Dezember 2025, Artikel 1 (Kürzel in Probasile: `[[AR-PAYS-SURS-2025, art. 1er]]`).

Die Liste der Union steht in Anhang II der Verordnung (EU) 2024/1348, eingefügt durch die Verordnung (EU) 2026/464: Bangladesch, Kolumbien, Ägypten, Indien, Kosovo, Marokko und Tunesien. Ein Bewerberland für den Beitritt zur Union gilt grundsätzlich ebenfalls als bestimmt, außer bei einem bewaffneten Konflikt, restriktiven Maßnahmen der Union im Zusammenhang mit den Grundrechten oder einer Anerkennungsquote von über 20 % auf Unionsebene (Artikel 62 Absatz 1b). Zu zitieren: Verordnung (EU) 2024/1348, Anhang II (Kürzel in Probasile: `[[UE-LISTE-PAYS-SURS]]`).

Wo Sie sie finden: In Probasile öffnet « Vérifier la législation… » (Gesetzgebung prüfen) → « Ouvrir les pages dans le navigateur » (Seiten im Browser öffnen) den letzten belgischen Erlass (die Liste steht in Artikel 1), die Liste der Ausführungserlasse des Gesetzes (ein neuer Erlass erscheint ganz oben) und die konsolidierte Fassung der Verordnung (Anhang II). Die Rechtsbeobachtung meldet jedes Land, das in eine der beiden Listen aufgenommen oder daraus gestrichen wird.

### 2026-09-29 | Sicherer Herkunftsstaat: Schutz kann immer beantragt werden
Texte: Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 26, 28, 34, 38, 42 und 61 ; Gesetz vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, B.S. vom 31. Dezember 1980 (LOI1980), Art. 57/6/1 § 3 ; Abkommen über die Rechtsstellung der Flüchtlinge, unterzeichnet in Genf am 28. Juli 1951 (GENEVE), Art. 3  
Bausteine: Pays d’origine sûr : une présomption qui se renverse au cas par cas ; Pays d’origine sûr : les personnes exposées malgré la désignation  
Bedeutung: hoch

Ja: Eine Person aus einem sicheren Herkunftsstaat kann immer Schutz beantragen und erhalten. Die Begründung erfolgt in fünf Schritten.

1. Das Recht, einen Antrag zu stellen, steht allen offen. Jede Person kann einen Antrag auf internationalen Schutz stellen, der anschließend bei der zuständigen Behörde förmlich gestellt wird (Verordnung (EU) 2024/1348, Artikel 26 und 28). Keine Bestimmung schließt Staatsangehörige eines sicheren Herkunftsstaats aus.

2. Der sichere Herkunftsstaat ist kein Unzulässigkeitsgrund. Artikel 38 der Verordnung zählt die Fälle auf, in denen ein Antrag als unzulässig abgelehnt werden kann (erster Asylstaat, sicherer Drittstaat, bereits in einem anderen Mitgliedstaat gewährter Schutz, Überstellung an ein internationales Strafgericht, verspäteter Antrag nach einer Rückkehrentscheidung, Folgeantrag ohne neue Elemente). Der sichere Herkunftsstaat ist dort nicht aufgeführt: Der Antrag muss in der Sache geprüft werden.

3. Er führt lediglich zu einer beschleunigten Prüfung (Artikel 42 Absatz 1 Buchstabe e), die « die Grundsätze und grundlegenden Garantien » wahrt und eine individuelle Prüfung bleibt (Artikel 34 Absatz 2).

4. Die Bestimmung als sicher ist nur eine Vermutung, die im Einzelfall widerlegt werden kann. Das Konzept « kann nur angewandt werden », wenn der Antragsteller « keine Anhaltspunkte dafür vorbringen kann, warum das Konzept des sicheren Herkunftsstaats im Rahmen einer individuellen Prüfung auf ihn nicht anwendbar ist » (Artikel 61 Absatz 5 Buchstabe c), und es gilt nicht für eine Personengruppe, die von der Bestimmung ausgenommen ist (Artikel 61 Absatz 5 Buchstabe b). Nach belgischem Recht kann der Generalkommissar den Schutz nur verweigern, « wenn der Ausländer keine ernsthaften Gründe dafür vorgebracht hat, dass es sich aufgrund seiner persönlichen Situation nicht um einen sicheren Herkunftsstaat handelt » (Gesetz vom 15. Dezember 1980, Artikel 57/6/1 § 3). Der Bericht an den König zum Erlass vom 3. Dezember 2025 sagt es ausdrücklich: « Die bloße Tatsache, dass ein Antragsteller auf internationalen Schutz aus einem sicheren Herkunftsstaat stammt, hat keinesfalls automatisch zur Folge, dass sein Antrag auf internationalen Schutz abgelehnt wird ».

5. Das Genfer Flüchtlingsabkommen gilt « ohne Unterschied der Rasse, der Religion oder des Herkunftslandes » (Artikel 3), und das Verbot der Rückführung in die Gefahr von Folter oder unmenschlicher Behandlung ist absolut (Artikel 3 der Europäischen Menschenrechtskonvention; Artikel 19 Absatz 2 der Charta). Der Gerichtshof der Europäischen Union bezeichnet die Bestimmung als « widerlegbare Vermutung », die die betroffene Person mit ernsthaften Gründen aus ihrer persönlichen Situation widerlegen kann (Urteil CV, 4. Oktober 2024, C-406/22, Rn. 47), denn « selbst in einem für seine gesamte Bevölkerung allgemein sicheren Land gibt es keine absolute Sicherheitsgarantie für jeden Einzelnen » (Urteil Alace und Canpelli, 1. August 2025, C-758/24 und C-759/24, Rn. 97). Das Gericht muss einen Verstoß gegen die Voraussetzungen der Bestimmung von Amts wegen aufgreifen (CV, Rn. 98). Die betroffene Person und das Gericht müssen « einen ausreichenden und angemessenen Zugang » zu den Quellen haben, auf denen die Bestimmung beruht (Alace und Canpelli, Rn. 73 und 87). Diese Urteile ergingen zur Richtlinie 2013/32/EU, beruhen aber auf dem Recht auf einen wirksamen Rechtsbehelf (Artikel 47 der Charta).

In der Praxis: Von Anfang an die ernsthaften Gründe darlegen, die der Person eigen sind (bereits erlittene Verfolgung, gefährdetes Profil, fehlender Schutz), mit Nachweisen und Quellen zum Land.

### 2026-09-29 | Beschleunigtes Verfahren: was es ist, wann es gilt, wie man herauskommt
Texte: Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 12, 20, 21, 34, 35, 39, 42, 53, 67, 68 und Erwägungsgrund 56 ; Gesetz vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, B.S. vom 31. Dezember 1980 (LOI1980), Art. 57/6/1 §§ 1 und 2 ; EuGH (Große Kammer), Urteil Alace und Canpelli, 1. August 2025, verbundene Rechtssachen C-758/24 und C-759/24, EU:C:2025:591 (CJUE-ALACE-2025) ; Verfassungsgerichtshof, 25. Februar 2021, Nr. 23/2021 (CC-23-2021)  
Bausteine: Procédure accélérée : quand, pourquoi, et comment en sortir ; Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité ; Procédure accélérée pour tardiveté  
Bedeutung: hoch  
Link: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:02024R1348-20260227

**Was es ist.** Das beschleunigte Verfahren ist weder ein Ablehnungsverfahren noch eine Prüfung « zweiter Klasse ». Es ist eine vollständige Prüfung des Antrags in der Sache (braucht die Person Schutz?), die jedoch schneller durchgeführt wird und bei der die Beschwerde schwieriger ist. Seit dem 12. Juni 2026 ist es in der Verordnung (EU) 2024/1348 geregelt, die in Belgien unmittelbar gilt; Artikel 57/6/1 des Gesetzes vom 15. Dezember 1980 ergänzt sie.

**Wann es gilt.** Nur in den Fällen, die Artikel 42 Absatz 1 der Verordnung aufzählt. Die Verordnung sagt, dass die Behörde die Prüfung « beschleunigt »: In diesen Fällen handelt es sich nicht mehr um eine bloße Möglichkeit.

- a) die Person hat nur Umstände vorgebracht, die für den Schutz nicht von Belang sind;
- b) offensichtlich inkohärente, widersprüchliche, falsche oder unwahrscheinliche Angaben oder Angaben, die im Widerspruch zu den verfügbaren Informationen über das Herkunftsland stehen;
- c) vorsätzliche Täuschung über Identität oder Staatsangehörigkeit (gefälschte Dokumente, böswillig vernichtete Papiere);
- d) Antrag nur gestellt, um eine Abschiebung zu verzögern oder zu verhindern;
- e) sicherer Herkunftsstaat (belgische Liste oder Liste der Union);
- f) Gefahr für die nationale Sicherheit oder die öffentliche Ordnung;
- g) Folgeantrag, der nicht unzulässig ist;
- h) und i) Antrag, der nicht « so bald wie möglich » gestellt wurde, ohne triftigen Grund;
- j) Staatsangehörigkeit eines Landes, dessen Anerkennungsquote auf Unionsebene 20 % oder weniger beträgt (siehe den folgenden Eintrag).

Für unbegleitete Minderjährige ist die Liste kürzer (Artikel 42 Absatz 3): sicherer Herkunftsstaat, Gefahr für die Sicherheit, Folgeantrag, Täuschung über die Identität, Schwelle von 20 %.

**Warum.** Der Gesetzgeber will Anträge, die er für weniger aussichtsreich hält, schneller bearbeiten (Erwägungsgrund 56). Der Gerichtshof erinnert jedoch daran, dass die Beschleunigung « unbeschadet einer angemessenen und vollständigen Prüfung und des effektiven Zugangs des Antragstellers zu den grundlegenden Garantien und Grundsätzen » erfolgt (Alace und Canpelli, 1. August 2025, Rn. 102).

**Was sich nicht ändert.** Die Prüfung erfolgt « unter Wahrung der Grundsätze und grundlegenden Garantien » (Artikel 42 Absatz 1). Sie bleibt objektiv, unparteiisch und individuell, auf der Grundlage genauer und aktueller Informationen über das Land (Artikel 34 Absatz 2). Die Person erhält Gelegenheit zu einer persönlichen Anhörung zur Sache (Artikel 12). Sie behält das Recht auf einen Dolmetscher, auf rechtlichen Beistand und auf die Beurteilung ihrer besonderen Bedürfnisse.

**Was sich ändert.**

- Prüfungsfrist: höchstens drei Monate ab der förmlichen Antragstellung (Artikel 35 Absatz 3), gegenüber sechs Monaten im ordentlichen Verfahren (Artikel 35 Absatz 4).
- Beschwerdefrist: zwischen fünf und zehn Tagen (Artikel 67 Absatz 7 Buchstabe a), gegenüber zwei Wochen bis einem Monat im ordentlichen Verfahren (Artikel 67 Absatz 7 Buchstabe b).
- « Offensichtlich unbegründet »: Eine Ablehnung kann so eingestuft werden, wenn das nationale Recht dies vorsieht (Artikel 39 Absatz 4). In Belgien ist das in den Fällen von Artikel 57/6/1 § 1 Buchstaben a bis j möglich, aber nie bei einem unbegleiteten Minderjährigen (Artikel 57/6/1 § 2).
- Keine automatische aufschiebende Wirkung der Beschwerde (Artikel 68 Absatz 3 Buchstabe a Ziffer i). Es muss beim Gericht innerhalb einer Frist von mindestens fünf Tagen nach der Zustellung beantragt werden, während der Beschwerde bleiben zu dürfen. Keine Abschiebung ist möglich, solange diese Frist läuft oder das Gericht nicht entschieden hat, und unentgeltliche Rechtsberatung ist auf Antrag zu gewähren (Artikel 68 Absätze 4 und 5).
- In Belgien richtet sich die Beschwerde beim Rat für Ausländerstreitsachen nun nach dem Gesetz vom 17. Juni 2026: 30 Tage im ordentlichen Verfahren, 10 Tage im beschleunigten Verfahren, 5 oder 10 Tage im Dringlichkeitsverfahren (siehe den Eintrag « Rat für Ausländerstreitsachen: die neuen Beschwerdefristen »). Die anwendbare Frist steht in der zugestellten Entscheidung: Prüfen Sie sie immer.

**Wie man es vermeidet oder herauskommt.**

- Schutzbedürftigkeit: Kann die notwendige Unterstützung im beschleunigten Verfahren nicht geleistet werden, « wendet » die Behörde dieses Verfahren « nicht an oder nicht mehr an », insbesondere bei Opfern von Folter, Vergewaltigung oder anderen schweren Formen von Gewalt (Artikel 21 Absatz 2). Die Beurteilung des Bedarfs an besonderen Verfahrensgarantien beginnt, sobald der Antrag gestellt wird, und endet innerhalb von 30 Tagen (Artikel 20). Deshalb früh darauf hinweisen und ärztliche oder psychologische Bescheinigungen vorlegen.
- Komplexität: Zu komplexe Sach- oder Rechtsfragen rechtfertigen den Übergang in das ordentliche Verfahren (Artikel 42 Absatz 2). Die Person wird darüber informiert.
- Unbegleitete Minderjährige: nur in den Fällen von Artikel 42 Absatz 3. Der Verfassungsgerichtshof hatte die weitergehende Anwendung des beschleunigten Verfahrens auf diese Minderjährigen bereits für nichtig erklärt (Entscheid Nr. 23/2021 vom 25. Februar 2021).
- Schwelle von 20 %: siehe den folgenden Eintrag.
- Verspätung: triftige Gründe geltend machen (siehe den Abschnitt « délai » (Frist) in Probasile).
- Sicherer Herkunftsstaat: die Vermutung durch ernsthafte persönliche Gründe widerlegen (siehe den Eintrag « Schutz kann immer beantragt werden »).
- Grenzverfahren: Es wird nicht oder nicht mehr angewandt, insbesondere aus medizinischen Gründen, einschließlich Gründen der psychischen Gesundheit, oder wenn Personen mit besonderen Bedürfnissen die notwendige Unterstützung nicht geleistet werden kann (Artikel 53 Absatz 2).

### 2026-09-29 | Schwelle von 20 %: wo Sie die Quote finden und wie Sie sie anfechten
Texte: Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 34, 39, 42 Abs. 1 Buchst. j, 42 Abs. 3 Buchst. e, 45 und Erwägungsgrund 56 ; Gesetz vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, B.S. vom 31. Dezember 1980 (LOI1980), Art. 57/6/1 § 2 ; Eurostat, « Countries of citizenship with an asylum recognition rate for international protection of 20% or lower », Bezugsjahr 2025, Daten abgerufen am 21. Mai 2026 (Union ohne Dänemark, erstinstanzliche Entscheidungen, Datenbank migr_asydec1pc) (EUROSTAT-20) ; Eurostat, Datenbank migr_asydcfina, « Final decisions in appeal or review on applications by type of decision, citizenship, age and sex – annual data » (EUROSTAT-FINALES) ; Asylagentur der Europäischen Union, Latest Asylum Trends – Annual Analysis, « Recognition rates » (EUAA-TAUX) ; Asylagentur der Europäischen Union, Leitlinien zu Herkunftsländern (Country Guidance), Artikel 11 der Verordnung (EU) 2021/2303 (EUAA-ORIENTATION) ; Generalkommissariat für Flüchtlinge und Staatenlose, monatliche Asylstatistiken und Jahresberichte (CGRA-CHIFFRES)  
Bausteine: Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité  
Bedeutung: hoch  
Link: https://ec.europa.eu/eurostat/documents/d/migration-asylum/countries-of-citizenship-with-an-asylum-recognition-rate-of-20-or-lower-1  
Link: https://ec.europa.eu/eurostat/databrowser/view/migr_asydcfina/default/table?lang=de  
Link: https://www.euaa.europa.eu/asylum-knowledge/country-guidance  
Link: https://www.cgra.be/fr/chiffres

**Die Regel.** Die Prüfung wird beschleunigt, wenn die Person die Staatsangehörigkeit eines Landes besitzt, für das « der Anteil der Entscheidungen der Asylbehörde, mit denen internationaler Schutz gewährt wird, nach den neuesten verfügbaren unionsweiten jährlichen Durchschnittsdaten von Eurostat 20 % oder weniger beträgt » (Verordnung (EU) 2024/1348, Artikel 42 Absatz 1 Buchstabe j; für unbegleitete Minderjährige Artikel 42 Absatz 3 Buchstabe e). Dieses Kriterium betrifft nur das Verfahren: Es erlaubt niemals für sich allein, den Schutz zu verweigern, und die Prüfung bleibt individuell (Artikel 34 Absatz 2). An der Grenze macht es außerdem das Grenzverfahren verpflichtend (Artikel 45 Absatz 1).

**Wo Sie die Quote finden.** Eurostat veröffentlicht eine Liste, die « solely for the purpose » der Verordnung erstellt wurde: « Countries of citizenship with an asylum recognition rate for international protection of 20% or lower ». Die aktuelle Fassung betrifft das Jahr 2025, mit Daten, die am 21. Mai 2026 abgerufen wurden. Die Berechnung:

- im Zähler: die Entscheidungen, mit denen die Flüchtlingseigenschaft oder subsidiärer Schutz zuerkannt wird (nationale humanitäre Status zählen nicht);
- im Nenner: alle erstinstanzlichen Entscheidungen;
- für die Union ohne Dänemark und nur die erstinstanzlichen Entscheidungen, also ohne Beschwerden.

Die zugehörige Datenbank heißt migr_asydec1pc. Eine mit « (u) » gekennzeichnete Quote ist wenig zuverlässig: Sie beruht auf weniger als 30 Entscheidungen. Die Links öffnen sich aus Probasile: « Vérifier la législation… » → « Ouvrir les pages dans le navigateur ».

**Wie Sie sie anfechten.**

0. Vor allem: Die Einzelfallprüfung gilt immer. Unabhängig vom Beschleunigungsgrund prüft die Behörde jeden Antrag « objektiv, unparteiisch und individuell », mit den Angaben und Unterlagen der Person und genauen und aktuellen Informationen über ihr Land (Verordnung (EU) 2024/1348, Artikel 34 Absatz 2). Die beschleunigte Prüfung wahrt « die Grundsätze und grundlegenden Garantien » (Artikel 42 Absatz 1). Die Schwelle von 20 % bestimmt nur das Tempo des Verfahrens, niemals sein Ergebnis: Sie gehört nicht zu den Unzulässigkeitsgründen (Artikel 38), und keine Bestimmung erlaubt es, einen Antrag allein wegen dieser Quote abzulehnen. Der Gerichtshof erinnert daran, dass es « keine absolute Sicherheitsgarantie für jeden Einzelnen » gibt, selbst in einem allgemein sicheren Land (Alace und Canpelli, 1. August 2025, C-758/24 und C-759/24, Rn. 97). Eine statistische Quote, die nur frühere Entscheidungen beschreibt, kann der Situation einer Person noch weniger vorgreifen. Schließlich ist das Verbot, jemanden in die Gefahr von Folter oder unmenschlicher Behandlung zurückzuschicken, absolut (Artikel 3 der Europäischen Menschenrechtskonvention; Artikel 19 Absatz 2 der Charta).
1. Die Zahl prüfen. Es zählt nur die neueste Jahresquote von Eurostat für die gesamte Union. Weder die belgische Quote noch eine Quote, die humanitäre Status einschließt, noch ein älteres Jahr entsprechen dem Kriterium. Eine mit « (u) » gekennzeichnete Quote kann die Beschleunigung nicht ernsthaft begründen.
2. Wesentliche Veränderung im Land seit der Veröffentlichung der Daten (Artikel 42 Absatz 1 Buchstabe j). Beispiele: Staatsstreich, Konflikt, Repressionswelle, neues Strafgesetz. Hat die Asylagentur der Europäischen Union (EUAA) eine solche Veränderung in einer Leitlinie festgestellt, müssen die Staaten sich darauf beziehen (Artikel 42 Absatz 1 Unterabsatz 2).
3. Personengruppe, für die die Quote nicht repräsentativ ist. Der Text betrifft « eine Personengruppe, für die der Anteil von 20 % oder weniger nicht als repräsentativ für ihren Schutzbedarf angesehen werden kann, unter anderem unter Berücksichtigung erheblicher Unterschiede zwischen erstinstanzlichen und endgültigen Entscheidungen ». Erwägungsgrund 56 stellt klar, dass es insbesondere um einen « spezifischen Verfolgungsgrund » geht. Beispiele: politische Oppositionelle, LGBTIQ-Personen, Frauen, die geschlechtsspezifischer Gewalt ausgesetzt sind, Minderheiten. Die Leitlinien der EUAA benennen diese Risikoprofile häufig.
4. Erste Instanz gegenüber endgültigen Entscheidungen. Die Quote berücksichtigt gewonnene Beschwerden nicht. Eurostat veröffentlicht die endgültigen Entscheidungen gesondert (Datenbank migr_asydcfina). Die EUAA betont, dass ihre Quoten « do not account for cases decided by the judiciary », und dass die Anerkennungsquote in der Beschwerdeinstanz 2024 für alle Staatsangehörigkeiten zusammen 19 % betrug (Factsheet EUAA/2025/37). Für eine bestimmte Staatsangehörigkeit zeigt ein großer Abstand zwischen erster Instanz und endgültigen Entscheidungen, dass die Quote nicht repräsentativ ist. Die Schutzquote des Generalkommissariats für diese Staatsangehörigkeit (monatliche Statistiken) kann ebenfalls helfen.
5. Erwägungsgrund 56 ist eindeutig: In diesen beiden Ausnahmefällen « sollte die Prüfung des Antrags nicht beschleunigt werden ». Beantragen Sie beim Generalkommissariat, das beschleunigte Verfahren nicht oder nicht mehr anzuwenden, und seine Entscheidung zumindest in Bezug auf diese Ausnahmen zu begründen.
6. Kein « offensichtlich unbegründet » allein aus diesem Grund. Die Verordnung erlaubt diese Einstufung nur, wenn das nationale Recht sie zulässt (Artikel 39 Absatz 4). Artikel 57/6/1 § 2 lässt sie jedoch nur in den Fällen a bis j seines § 1 zu, unter denen die Schwelle von 20 % nicht vorkommt.
   ⚠ Hinweis: Dies ist eine Auslegung, über die der Rat für Ausländerstreitsachen noch nicht entschieden hat. Sie beruht auf Artikel 57/6/1 § 2 in der Fassung vom 29. September 2026: Prüfen Sie, ob ein Gesetz die Schwelle von 20 % seitdem nicht in die belgische Liste aufgenommen hat (die Rechtsbeobachtung von Probasile wird es melden). Das Generalkommissariat könnte einwenden, dass die Verordnung unmittelbar gilt und ihr Artikel 39 Absatz 4 alle Fälle von Artikel 42 erfasst. Antwort: Diese Bestimmung verlangt eine Ermächtigung « nach nationalem Recht », und der belgische Gesetzgeber hat sie nur für die von ihm aufgezählten Fälle erteilt. Selbst wenn das Argument zurückgewiesen wird, bleibt Punkt 0 unberührt.
7. Die anderen Wege bleiben offen: Schutzbedürftigkeit (Artikel 21 Absatz 2), Komplexität (Artikel 42 Absatz 2), medizinische Gründe an der Grenze (Artikel 53 Absatz 2).

### 2026-09-29 | Sicherer Drittstaat: was sich mit der Verordnung (EU) 2026/463 ändert
Texte: Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 38, 57, 59 und 68 ; Verordnung (EU) 2026/463 des Europäischen Parlaments und des Rates vom 24. Februar 2026 zur Änderung der Verordnung (EU) 2024/1348 hinsichtlich der Anwendung des Konzepts des sicheren Drittstaats, ABl. L 463, 26.2.2026 (REG2026-463) ; EuGH, Urteil LH gegen Bevándorlási és Menekültügyi Hivatal, 19. März 2020, Rechtssache C-564/18 (CJUE-LH-2020) ; EGMR (Große Kammer), Urteil Ilias und Ahmed gegen Ungarn, 21. November 2019, Beschwerde Nr. 47287/15 (ILIAS-AHMED)  
Bausteine: Pays tiers sûr : conditions strictes et évaluation individuelle  
Bedeutung: hoch  
Link: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:02024R1348-20260227

Worum geht es? Das Konzept des sicheren Drittstaats erlaubt es, einen Antrag ohne Prüfung in der Sache als unzulässig abzulehnen, weil die Person Schutz in einem anderen Land als ihrem eigenen, außerhalb der Union, erhalten könnte (Artikel 38 Absatz 1 Buchstabe b).

Die Grundvoraussetzungen haben sich nicht geändert: In diesem Land dürfen Nichtstaatsangehörige weder um ihr Leben noch um ihre Freiheit fürchten müssen, keinem tatsächlichen Risiko eines ernsthaften Schadens ausgesetzt sein, müssen vor Zurückweisung geschützt sein und « wirksamen Schutz » beantragen und erhalten können (Artikel 59 Absatz 1). Hat das Land das Genfer Flüchtlingsabkommen nicht ratifiziert und hält es nicht ein, setzt dieser Schutz mindestens das Recht voraus, dort zu bleiben, ausreichende Mittel zum Lebensunterhalt, Zugang zu Gesundheitsversorgung und Bildung sowie Schutz bis zu einer dauerhaften Lösung (Artikel 57).

Was sich ändert: die geforderte Verbindung zwischen der Person und dem Drittstaat. Seit der Verordnung (EU) 2026/463 genügt eine dieser drei Situationen (Artikel 59 Absatz 5 Buchstabe b):

- eine « Verbindung », aufgrund derer es vernünftig erscheint, dass die Person sich in dieses Land begibt (zum Beispiel Familie oder ein früherer Aufenthalt);
- eine bloße Durchreise durch dieses Land « auf dem Weg in die Union »;
- eine Vereinbarung oder Absprache mit diesem Land, die es verpflichtet, die Begründetheit der Schutzanträge der betroffenen Personen zu prüfen.

Das ist eine erhebliche Ausweitung. Zur Richtlinie 2013/32/EU hatte der Gerichtshof eine Regelung für unionsrechtswidrig erklärt, die einen Antrag allein deshalb für unzulässig erklärte, weil die Person über einen Staat eingereist war, in dem sie keiner Verfolgung ausgesetzt war oder in dem ein angemessenes Schutzniveau gewährleistet war (Urteil LH, 19. März 2020, C-564/18, Tenor, Nr. 1).

Was sich nicht ändert und geltend gemacht werden sollte:

- die individuelle Prüfung: Das Konzept gilt nicht, wenn die Person Anhaltspunkte vorbringt, dass es auf sie nicht anwendbar ist (Artikel 59 Absatz 5 Buchstabe a) — kurze oder erzwungene Durchreise, in diesem Land erlittene Gewalt, fehlender tatsächlicher Zugang zu Asyl, Gefahr der Kettenabschiebung;
- unbegleitete Minderjährige: nur wenn es ihrem Wohl entspricht, nach Zusicherung von Betreuung und sofortigem wirksamem Schutz, und nie auf der Grundlage einer Vereinbarung (Artikel 59 Absatz 6);
- die Rückübernahme: keine Unzulässigkeit, wenn klar ist, dass das Land die Person nicht zurücknimmt (Artikel 38 Absatz 1 Buchstabe b), und Zugang zum Verfahren, wenn es sie nicht aufnimmt (Artikel 59 Absatz 9);
- die Information: Ein Dokument muss den Drittstaat in seiner Sprache darüber informieren, dass der Antrag nicht in der Sache geprüft wurde (Artikel 59 Absatz 8 Buchstabe b);
- die Europäische Menschenrechtskonvention: Der zurückschiebende Staat muss gründlich prüfen, ob die Person im Drittstaat Zugang zu einem angemessenen Asylverfahren haben wird (EGMR, Ilias und Ahmed gegen Ungarn, 21. November 2019, §§ 137-141 und 152-154);
- die Beschwerde: keine automatische aufschiebende Wirkung gegen eine Unzulässigkeitsentscheidung (Artikel 68 Absatz 3 Buchstabe b); beim Gericht beantragen, bleiben zu dürfen (Artikel 68 Absätze 4 und 5).

Die Verordnung (EU) 2024/1348 gilt seit dem 12. Juni 2026; einige Bestimmungen über sichere Staaten galten bereits ab dem 27. Februar 2026 (Artikel 79).

### 2026-09-29 | Verordnung (EU) 2024/1348, geändert am 24. Februar 2026
Texte: Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 59, 60, 61, 62, 64, 68, 79 und Anhang II ; Verordnung (EU) 2026/463 des Europäischen Parlaments und des Rates vom 24. Februar 2026 zur Änderung der Verordnung (EU) 2024/1348 hinsichtlich der Anwendung des Konzepts des sicheren Drittstaats, ABl. L 463, 26.2.2026 (REG2026-463) ; Verordnung (EU) 2026/464 des Europäischen Parlaments und des Rates vom 24. Februar 2026 zur Änderung der Verordnung (EU) 2024/1348 hinsichtlich der Erstellung einer Liste sicherer Herkunftsstaaten auf Unionsebene, ABl. L 464, 26.2.2026 (REG2026-464)  
Bausteine: keiner der in den ursprünglichen Bausteinen zitierten Artikel 26, 34 und 42 ist geändert  
Bedeutung: Information  
Link: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:02024R1348-20260227

Zwei Verordnungen vom 24. Februar 2026 ändern die Verordnung (EU) 2024/1348 (konsolidierte Fassung vom 27. Februar 2026): die Verordnung (EU) 2026/464 (sichere Herkunftsstaaten auf Unionsebene) und die Verordnung (EU) 2026/463 (sicherer Drittstaat). Siehe die beiden ausführlichen Einträge oben. Eine Berichtigung vom 25. November 2025 korrigiert außerdem den Wortlaut der Artikel 7, 28, 39, 48 und 50.

### 2026-09-29 | Probasile 1.0: die Rechtsbeobachtung
Bedeutung: Information

Neue Schaltfläche « Vérifier la législation… » (Gesetzgebung prüfen, Reiter « Rédaction »). Sie vergleicht die aktuelle Fassung des Gesetzes vom 15. Dezember 1980, des Königlichen Erlasses vom 8. Oktober 1981, der Verordnungen (EU) 2024/1347 und 2024/1348 und des Königlichen Erlasses « sichere Herkunftsstaaten » mit dem Rechtsstand, auf dem die Bausteine beruhen, und meldet die geänderten Artikel und die zu überprüfenden Bausteine. Sie akzeptiert auch im Browser gespeicherte Seiten (HTML) und konsolidierte Fassungen von EUR-Lex im PDF-Format.

### 2026-06-19 | Asylreform: was sich bei der Frist von acht Tagen ändert
Texte: Gesetz vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, B.S. vom 31. Dezember 1980 (LOI1980), Art. 48/6, 50 und 50/1 ; Verordnung (EU) 2024/1348 des Europäischen Parlaments und des Rates vom 14. Mai 2024 zur Einführung eines gemeinsamen Verfahrens zur Gewährung internationalen Schutzes in der Union und zur Aufhebung der Richtlinie 2013/32/EU, ABl. L, 2024/1348, 22.5.2024 (REG2024-1348), Art. 26, 28 und 42  
Bausteine: Délai dépassé : ni irrecevabilité ni rejet automatique ; Procédure accélérée pour tardiveté ; Demande présentée dans le délai de huit jours  
Bedeutung: hoch  
Link: https://www.ejustice.just.fgov.be/eli/loi/1980/12/15/1980121550/justel#Art.50

Das Gesetz vom 16. Juni 2026 (Belgisches Staatsblatt vom 19. Juni 2026), in Kraft seit dem 12. Juni 2026, passt das Gesetz vom 15. Dezember 1980 an die europäischen Asylverordnungen von 2024 an.

Die Frist von acht Tagen besteht weiterhin: Artikel 50 § 1 sieht nach wie vor vor, dass eine Person, die ohne Erfüllung der Voraussetzungen eingereist ist, ihren Antrag innerhalb von acht Werktagen stellt. Die Paragraphen 2 bis 5 von Artikel 50 sind dagegen aufgehoben, und die Verordnung (EU) 2024/1348 sieht weder die Ablehnung noch die Unzulässigkeit eines Antrags allein wegen seiner Verspätung vor. Die Verspätung kann nur unter bestimmten Voraussetzungen und ohne triftigen Grund zu einem beschleunigten Verfahren führen (Artikel 42 der Verordnung).

Die Artikel 48/3, 48/4, 48/5 und 48/7 des Gesetzes sind aufgehoben (der Bereich unterliegt nun der Verordnung (EU) 2024/1347). Artikel 48/6 regelt nur noch die Vorlage der Anhaltspunkte und Unterlagen zur Begründung des Antrags, die « so bald wie möglich » vorzulegen sind; seine Paragraphen 4 und 5 sind aufgehoben. Ein neuer Artikel 50/1 regelt die förmliche Antragstellung.

Die Bausteine von Probasile berücksichtigen diese Reform seit Version 0.9.

### 2025-12-15 | Belgische Liste der sicheren Herkunftsstaaten: Königlicher Erlass vom 3. Dezember 2025
Texte: Gesetz vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, B.S. vom 31. Dezember 1980 (LOI1980), Art. 57/6/1 ; Königlicher Erlass vom 3. Dezember 2025 zur Ausführung von Artikel 57/6/1 § 3 Absatz 4 des Gesetzes vom 15. Dezember 1980 über die Einreise ins Staatsgebiet, den Aufenthalt, die Niederlassung und das Entfernen von Ausländern, zur Festlegung der Liste der sicheren Herkunftsstaaten, B.S. vom 15. Dezember 2025 (AR-PAYS-SURS-2025)  
Bedeutung: hoch  
Link: https://www.ejustice.just.fgov.be/eli/arrete/2025/12/03/2025009368/justel

Der Königliche Erlass vom 3. Dezember 2025 (Belgisches Staatsblatt vom 15. Dezember 2025), in Kraft am Tag seiner Veröffentlichung, bestimmt als sichere Herkunftsstaaten: Albanien, Bosnien und Herzegowina, Kosovo, Marokko, Montenegro, Nordmazedonien und Serbien.

Nach dem Bericht an den König wurde Marokko abweichend von der Stellungnahme des Generalkommissars für Flüchtlinge und Staatenlose aufgenommen, dessen letzte eingehende Analyse aus dem Jahr 2021 stammte; die Regierung beruft sich auf den Rückgang der Schutzquote und auf den Vorschlag der Europäischen Kommission (COM/2025/186).

Der Bericht an den König erinnert auch daran, dass die Herkunft aus einem sicheren Herkunftsstaat nicht zu einer automatischen Ablehnung führt: Der Antrag wird individuell geprüft, und der Antragsteller kann nachweisen, dass sein Land in seiner besonderen Situation nicht als sicher gelten kann.
