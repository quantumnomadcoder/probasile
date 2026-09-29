# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bibliothèque de blocs de texte juridiques, par procédure, modifiable dans LibreOffice.

Structure du document « bibliotheque_blocs.odt » (dans le dossier de base) :
    Titre 1 : la procédure       (Non-délivrance d’OQT / Protection internationale / 9ter)
    Titre 2 : la rubrique du plan où le bloc est inséré (ex. « IV. La demande »)
    Titre 3 : le nom du bloc, suivi de « (par défaut) » s'il est coché d'office
    paragraphes : le texte du bloc, avec ses repères de notes [[…]] et des variables
                  {demandeur}, {pays}, {en_pays}, {Le_pays}, {de_pays}
Un bloc peut en inclure un autre par un paragraphe [[BLOC nom du bloc]].
Les textes de loi et arrêts cités sont dans references_juridiques.csv (repères LOI1980, SOERING…).
"""

import copy
import os
import re
import shutil

import redaction as R
from redaction import NS, T, etree

ICI = os.path.dirname(os.path.abspath(__file__))
NOM = "bibliotheque_blocs.odt"
REF_NOM = "references_juridiques.csv"
PROCEDURES = {"oqt": "Non-délivrance d’OQT", "pi": "Protection internationale", "9ter": "9ter"}

A_VERIFIER_REG = ("[À VÉRIFIER : bloc repris d’un dossier de 2019 et adapté au règlement (UE) 2024/1347 – relisez-le "
                  "puis supprimez cette mention.] ")
A_VERIFIER = "[À VÉRIFIER : texte de départ antérieur à la réforme de 2026 – relisez-le puis supprimez cette mention.] "

DEFAUT = [
    # --- Non-délivrance d'OQT (repris d’un dossier type) -----------------
    ("oqt", "IV. La demande", "Convention contre la torture et article 33 de la Convention de Genève", True, [
        "Rappelons que la Belgique a ratifié – et est donc liée par – la Convention contre la torture et autres peines ou "
        "traitements cruels, inhumains ou dégradants[[TRAITE-CAT]]. L’article 3 de cette Convention prévoit qu’« aucun État "
        "partie n’expulsera, ne refoulera, ni n’extradera une personne vers un autre État où il y a des motifs sérieux de "
        "croire qu’elle risque d’être soumise à la torture ». Dès lors, la Belgique a l’obligation de s’abstenir d’expulser "
        "un individu de nationalité étrangère, même s’il n’est pas bénéficiaire d’une protection internationale, lorsqu’il "
        "existe des motifs sérieux de croire qu’il risque d’être soumis à la torture. De même, l’article 33 de la Convention "
        "de Genève interdit d’expulser ou de refouler un demandeur d’asile vers les frontières des territoires où sa vie ou "
        "sa liberté serait menacée en raison notamment de sa religion ou de ses opinions politiques[[GENEVE, art. 33]]."]),
    ("oqt", "IV. La demande", "Caractère déclaratif du statut de réfugié", True, [
        "Rappelons que la protection offerte par l’article 33 de la Convention de 1951 relative au statut des réfugiés ne "
        "bénéficie pas uniquement aux personnes qui se sont déjà vu reconnaître formellement le statut de réfugié, mais "
        "également aux demandeurs d’asile dont la demande n’a pas encore été examinée, et plus largement à toute personne qui "
        "remplit les conditions pour être reconnue réfugiée. En effet, le statut de réfugié revêt un caractère déclaratif et "
        "non constitutif : une personne est un réfugié, au sens de la Convention de 1951, dès qu’elle satisfait aux critères "
        "énoncés dans la définition de l’article 1er, A, 2, et cette situation est nécessairement antérieure à la "
        "reconnaissance formelle de son statut. Autrement dit, « une personne ne devient pas un réfugié du fait de sa "
        "reconnaissance en tant que tel, mais est reconnue en tant que tel parce qu’elle est un réfugié »[[HCR-GUIDE, §28 ; "
        "GICQUEL]]. Ce caractère déclaratif est expressément consacré par le droit de l’Union européenne, qui précise que "
        "« la reconnaissance du statut de réfugié est un acte déclaratif »[[REG2024-1347, considérant 22 ; DIR2011-95, "
        "considérant 21]]. Cela a été rappelé par la Cour de justice de l’Union européenne en 2019[[CJUE-M, §§85-92]] : "
        "« il découle des considérations qui précèdent que la qualité de “réfugié”, au sens de l’article 2, sous d), de la "
        "directive 2011/95 et de l’article 1er, section A, de la convention de Genève, ne dépend pas de la reconnaissance "
        "formelle de cette qualité par l’octroi du “statut de réfugié”, au sens de l’article 2, sous e), de cette directive, "
        "lu en combinaison avec l’article 13 de cette dernière »[[CJUE-M, §92]]. Il en découle que le principe de "
        "non-refoulement « s’applique non seulement aux réfugiés reconnus, mais aussi à ceux dont le statut n’a pas été "
        "formellement déclaré »[[GICQUEL]]. Le Comité exécutif du Haut-Commissariat des Nations Unies pour les réfugiés l’a "
        "d’ailleurs réaffirmé à plusieurs reprises, en soulignant que ce principe protège toute personne susceptible d’être "
        "persécutée, qu’elle ait ou non été officiellement reconnue comme réfugiée[[HCR-EXCOM6 ; HCR-AVIS2007, §6 ; "
        "GICQUEL]]. De plus, en 2020, l’Agence des droits fondamentaux de l’Union européenne et le Conseil de l’Europe "
        "rappellent également que l’article 33 de la Convention de 1951 interdit le retour « des réfugiés et des demandeurs "
        "d’asile » vers des pays où ils risquent d’être persécutés, et que ces obligations « n’admettent aucune dérogation, "
        "ni exception ou limitation »[[FRA2020, p.5]]."]),
    ("oqt", "IV. La demande", "Cour européenne des droits de l’homme : article 3", True, [
        "Par ailleurs, rappelons que la Cour européenne des droits de l’homme a, à plusieurs reprises, souligné qu’un "
        "individu – même un criminel étranger – ne pouvait pas être expulsé s’il existe de sérieux motifs de croire qu’il "
        "sera soumis à des actes de torture ou à des traitements inhumains ou dégradants[[SOERING, §88 ; X-SUEDE-2018, "
        "§§52-56 ; X-PAYSBAS-2018, §71 +souligne]]. Autrement dit, la Cour européenne des droits de l’homme a dit pour droit "
        "qu’une personne étrangère ne peut être expulsée vers son pays d’origine s’il existe de sérieux motifs de croire "
        "qu’elle y sera soumise à des traitements contraires à l’article 3 de la Convention européenne des droits de "
        "l’homme – des actes de torture ou des traitements inhumains ou dégradants. La Cour a étendu l’interdiction "
        "d’expulsion aux cas de risque de traitements inhumains ou dégradants et ne limite pas le champ de cette obligation "
        "d’abstention aux cas de torture[[SOERING, §88]]. Cette interdiction s’applique également lorsque le risque émane "
        "d’acteurs non étatiques et que les autorités du pays de destination ne sont pas en mesure ou ne souhaitent pas y "
        "parer par une protection appropriée[[HLR, §40]]. La Cour a en outre condamné la Belgique pour avoir éloigné un "
        "demandeur sans avoir vérifié le risque qu’il encourait dans le pays de destination[[MSS]]."]),
    ("oqt", "IV. La demande", "Conseil du contentieux des étrangers", True, [
        "Enfin, le Conseil du contentieux des étrangers applique les principes dégagés par la jurisprudence de la Cour "
        "européenne des droits de l’homme[[CCE-212381]]. Par conséquent, l’État belge ne peut pas expulser une personne "
        "étrangère lorsqu’il existe de sérieux motifs de croire qu’elle sera soumise à des actes de torture ou à des "
        "traitements inhumains ou dégradants ou sans avoir vérifié le risque qu’elle encourait dans le pays de destination."]),
    ("oqt", "IV. La demande", "Intérêt supérieur de l’enfant (article 74/13)", True, [
        "Par ailleurs, l’article 74/13 de la loi du 15 décembre 1980 impose, lors de la prise d’une décision d’éloignement, "
        "de tenir compte de l’intérêt supérieur de l’enfant, de la vie familiale et de l’état de santé du ressortissant d’un "
        "pays tiers concerné[[LOI1980, art. 74/13]]. L’intérêt supérieur de l’enfant doit en outre être une considération "
        "primordiale dans toutes les décisions qui le concernent, conformément à l’article 3 de la Convention relative aux "
        "droits de l’enfant et à l’article 22bis de la Constitution[[CIDE, art. 3, §1er ; CONSTITUTION, art. 22bis]]. Or, en "
        "l’espèce, un ordre de quitter le territoire exposerait [les enfants], qui ont grandi en Belgique et y sont "
        "scolarisés, aux risques de persécution ou de traitements inhumains ou dégradants décrits ci-dessus (supra)."]),
    ("oqt", "IV. La demande", "Éligibilité à la protection internationale et absence d’examen au fond", False, [
        "Incidemment, en soutien à l’application du principe de non-refoulement, nous souhaitons attirer l’attention des "
        "autorités administratives chargées de statuer sur la délivrance d’un ordre de quitter le territoire à l’encontre de "
        "{demandeur}[ et des membres de {sa} famille] sur deux éléments. D’une part, les éléments qui précèdent démontrent, à "
        "tout le moins, que {le_demandeur} {pourrait|pourraient} être éligible{s} à la protection internationale, à savoir au statut de "
        "réfugié au sens de l’article 3, point 5), du règlement (UE) 2024/1347 et de la Convention de Genève, en raison de "
        "[{ses} opinions politiques et de {sa} religion], ou, à tout le moins, à la protection subsidiaire au sens de "
        "l’article 3, point 6), et de l’article 15, b), de ce règlement, en raison du risque réel de torture ou de "
        "traitements inhumains ou dégradants qu’{il} {encourt|encourent}[[REG2024-1347, art. 3, points 5) et 6), 9, 10 et 15, b) ; "
        "GENEVE, art. 1er, A, 2]]. À titre subsidiaire, {il} {pourrait|pourraient} prétendre à une autorisation de séjour. D’autre part, "
        "{le_demandeur} n’{a} jusqu’à présent jamais pu faire valoir {ses} droits sur le fond, [{sa} demande précédente "
        "ayant été déclarée irrecevable]. Dès lors, délivrer un ordre de quitter le territoire {au_demandeur} reviendrait à "
        "{le} renvoyer {en_pays} sans qu’aucune autorité belge n’ait jamais examiné, sur le fond, le risque qu’{il} y "
        "{encourt|encourent}. Une telle décision serait contraire à l’enseignement de l’arrêt M.S.S. c. Belgique et Grèce, par lequel "
        "la Cour européenne des droits de l’homme a condamné la Belgique pour avoir éloigné un demandeur d’asile sans s’être "
        "assurée qu’il ne serait pas exposé, dans le pays de destination, à des traitements contraires à l’article 3 de la "
        "Convention européenne des droits de l’homme[[MSS]]."]),
    ("oqt", "IV. La demande", "Dispositif", True, [
        "Au regard de tout ce qui précède, [nous nous joignons à {demandeur}, et aux membres de {sa} famille, pour demander] "
        "respectueusement à l’Office des étrangers :",
        "de ne pas délivrer d’ordre de quitter le territoire à {demandeur}[ et aux membres de {sa} famille] ;",
        "de reconnaître qu’{il} {bénéficie|bénéficient} de la protection du principe de non-refoulement, en application de l’article 3 de "
        "la Convention européenne des droits de l’homme, de l’article 3 de la Convention contre la torture et de l’article "
        "33 de la Convention de Genève, dès lors qu’il existe des motifs sérieux de croire qu’{il} {courrait|courraient}, en cas de "
        "retour {en_pays}, un risque réel d’être {soumis/soumise|soumis/soumises} à la torture ou à des traitements inhumains ou dégradants ;",
        "à tout le moins, de tenir compte, conformément à l’article 74/13 de la loi du 15 décembre 1980, de l’intérêt "
        "supérieur des enfants, de la vie familiale {du_demandeur} et des risques qu’{il} {encourt|encourent} {en_pays} avant toute "
        "décision d’éloignement."]),
    ("oqt", "IV. La demande", "Portée de la demande", False, [
        "{Le_demandeur} ne {sollicite|sollicitent} pas un droit automatique au séjour [ni ne {remet|remettent} en cause la "
        "précédente décision]. {Il} {demande|demandent} seulement que la Belgique ne {le} renvoie pas vers un pays où il existe "
        "des motifs sérieux de croire qu’{il} y {serait|seraient} exposé{e} à la persécution ou à des atteintes graves, avant "
        "qu’{il} n’{ait|aient} pu faire valoir, sur le fond, {son} droit à une protection."]),
    # --- Ratifications, réserves et déclarations (dossier type, 2026) --------------------------
    ("oqt", "a. Le Pacte international relatif aux droits civils et politiques",
     "Pacte : adhésion et réserves (à compléter à la main)", True, [
        "{Le_pays} a [adhéré au / ratifié le] Pacte international relatif aux droits civils et politiques le [date] [et "
        "n’a pas émis de réserves concernant ses dispositions – mises à part quelques précisions quant à l’article 1er "
        "du Pacte][[TRAITE-PIDCP]].",
        "[Or, {le_pays} avait jusqu’au [date] pour transmettre son premier rapport et ne l’a soumis que le [date] "
        "(note : repère de l’état des rapports), soit [durée] après l’échéance du délai.]"]),
    ("oqt", "a. Le Pacte international relatif aux droits civils et politiques",
     "Pacte : obligation de faire rapport (article 40)", True, [
        "Dès lors, conformément à l’article 40 du Pacte, {le_pays} a l’obligation de fournir au Comité des droits de "
        "l’homme un rapport sur les mesures prises pour donner effet aux droits consacrés par le Pacte. Ce "
        "rapport doit être fourni dans un délai d’un an à compter de l’entrée en vigueur du Pacte à l’égard de l’État "
        "(art. 40, §1, a), du Pacte) et, par la suite, chaque fois que le Comité en fait la demande (art. 40, §1, b), du "
        "Pacte)[[PIDCP, art. 40]]."]),
    ("oqt", "b. La Convention contre la torture",
     "Convention contre la torture : ratification et articles 21 et 22 (à compléter à la main)", True, [
        "{Le_pays} a ratifié la Convention contre la torture et autres peines ou traitements cruels, inhumains ou "
        "dégradants le [date][[TRAITE-CAT]]. [Toutefois, l’État n’a pas fait les déclarations prévues aux articles 21 et "
        "22 de la Convention[[TRAITE-CAT]], de sorte qu’il ne reconnaît pas la compétence du Comité contre la torture pour "
        "connaître de plaintes déposées par d’autres États parties à la Convention (art. 21 de la Convention contre la "
        "torture) ou par des individus relevant de sa juridiction (art. 22 de la Convention contre la torture)"
        "[[TRAITE-CAT]]. Autrement dit, une personne victime de torture {en_pays} ne peut pas saisir le Comité.]"]),
    ("oqt", "b. La Convention contre la torture", "Convention contre la torture : l’enquête de l’article 20", True, [
        "En outre, l’article 20 de la Convention prévoit un mécanisme d’enquête coopératif permettant au Comité contre la "
        "torture, en cas d’indications fondées de pratique systématique de la torture, d’enquêter, de faire rapport et "
        "d’émettre des recommandations à l’État partie, dont il assure le suivi[[CAT, art. 20]]. Ce mécanisme va au-delà "
        "de la seule procédure de rapports et de suivi prévue par le Pacte international relatif aux droits civils et "
        "politiques. De plus, le paragraphe 3 de l’article 20 de la Convention prévoit qu’une visite sur place est "
        "possible avec l’accord de l’État partie. [Toutefois, {le_pays} a fait une déclaration concernant l’article 20 de "
        "la Convention[[TRAITE-CAT]].]",
        "[En effet, {le_pays} a déclaré : « texte de la déclaration, à recopier depuis la Collection des Traités ; pour "
        "l’Indonésie : Le Gouvernement de la République d’Indonésie déclare que les dispositions contenues dans les "
        "paragraphes 1, 2 et 3 de l’article 20 de la Convention devront être appliquées dans le strict respect des "
        "principes de la souveraineté et de l’intégrité territoriale des États »[[TRAITE-CAT]].]"]),
    ("oqt", "b. La Convention contre la torture", "Notion de réserve : une déclaration peut être une réserve", True, [
        "Certes, il ne s’agit pas d’une « réserve » au sens le plus strict du terme. Toutefois, l’article 2, §1, d), de la "
        "Convention de Vienne sur le droit des traités de 1969 définit la notion de « réserve » comme une « déclaration "
        "unilatérale, __quel que soit son libellé ou sa désignation__, faite par un État quand il signe, ratifie, accepte ou "
        "approuve un traité ou y adhère, par laquelle il vise à exclure ou à modifier l’effet juridique de certaines "
        "dispositions du traité dans leur application à cet État »[[VIENNE1969, art. 2, §1, d) +souligne]].",
        "[Certes, {le_pays} n’a pas ratifié la Convention de Vienne sur le droit des traités[[TRAITE-VIENNE]]. Toutefois, "
        "la] Cour internationale de Justice reconnaît le caractère coutumier de règles contenues dans cette convention"
        "[[CIJ-CAMEROUN-NIGERIA, p. 429, §263]]. Ensuite, rappelons que la consécration d’une règle coutumière par un "
        "traité ne fait pas disparaître la règle coutumière : les deux règles sont applicables et continuent d’exister "
        "côte à côte[[CIJ-NICARAGUA, p. 94, §176]]. Enfin, cette conception de la réserve prévalait déjà avant la "
        "naissance de la Convention de Vienne sur le droit des traités[[SHATZKY-1933, pp. 216-217 ; MEEK-1955, p. 41 ; "
        "MCRAE-1978, p. 156]].",
        "Dès lors, il convient d’avoir égard au contenu de la déclaration faite par {le_pays} plutôt qu’à l’intitulé de "
        "ladite déclaration. [Analyse propre au pays. Exemple pour l’Indonésie : Par conséquent, en déclarant que "
        "l’article 20 de la Convention contre la torture doit être appliqué dans le strict respect de sa souveraineté et "
        "de son intégrité territoriale, l’Indonésie marque son intention de se dégager du contrôle du Comité contre la "
        "torture tout en pouvant affirmer qu’elle est tenue par l’article 20 de la Convention contre la torture. En "
        "effet, l’insistance de l’Indonésie quant à sa souveraineté indique une volonté de l’État indonésien de marquer "
        "son champ de compétence et traduit à tout le moins une attitude réfractaire envers tout mécanisme de contrôle et "
        "de surveillance de la situation des droits de l’homme sur son territoire puisque, outre cette déclaration, "
        "l’Indonésie n’a pas non plus fait la déclaration permettant au Comité de connaître de plaintes émanant "
        "d’individus relevant de sa juridiction. En outre, l’attitude de l’Indonésie semble confirmer notre "
        "interprétation de sa déclaration puisque l’Indonésie ne répond plus aux sollicitations du Comité contre la "
        "torture depuis [année] (note : repère de l’état des rapports).]"]),
    ("pi", "a. Le Pacte international relatif aux droits civils et politiques",
     "Pacte : adhésion et réserves (renvoi) (à compléter à la main)", True,
     ["[[BLOC Pacte : adhésion et réserves (à compléter à la main)]]"]),
    ("pi", "a. Le Pacte international relatif aux droits civils et politiques", "Pacte : article 40 (renvoi)", True,
     ["[[BLOC Pacte : obligation de faire rapport (article 40)]]"]),
    ("pi", "b. La Convention contre la torture", "Convention contre la torture : articles 21 et 22 (renvoi) (à "
     "compléter à la main)", True,
     ["[[BLOC Convention contre la torture : ratification et articles 21 et 22 (à compléter à la main)]]"]),
    ("pi", "b. La Convention contre la torture", "Convention contre la torture : article 20 et réserves (renvoi)", True, [
        "[[BLOC Convention contre la torture : l’enquête de l’article 20]]",
        "[[BLOC Notion de réserve : une déclaration peut être une réserve]]"]),
    # --- Protection internationale : le délai de huit jours (art. 50) --------------------------------------
    # Textes vérifiés : loi du 15 décembre 1980, art. 50 (version au 12 juin 2026) ; loi du 16 juin 2026, art. 25 et 34 ;
    # règlement (UE) 2024/1347, art. 4, §5, et considérant 27 ; règlement (UE) 2024/1348, art. 26, 34 et 42.
    ("pi", "L’introduction de la demande dans le délai", "Demande présentée dans le délai de huit jours", False, [
        "{demandeur} est arrivé{e} sur le territoire le [date] et a présenté {sa} demande de protection internationale "
        "le [date], soit dans le délai de huit jours ouvrables visé à l’article 50, §1er, alinéa 1er, de la loi du 15 "
        "décembre 1980[[LOI1980, art. 50, §1er, al. 1er]]. Aucune tardiveté ne peut dès lors {lui} être opposée."]),
    ("pi", "L’introduction de la demande dans le délai", "Délai dépassé : ni irrecevabilité ni rejet automatique", True, [
        "À supposer que la demande ait été présentée au-delà du délai de huit jours ouvrables prévu par l’article 50, "
        "§1er, alinéa 1er, de la loi du 15 décembre 1980[[LOI1980, art. 50, §1er, al. 1er]], ce dépassement n’est "
        "assorti d’aucune sanction. Les paragraphes 2 à 5 de l’article 50 ont été abrogés avec effet au 12 juin 2026"
        "[[LOI2026, art. 34]], et le règlement (UE) 2024/1348, qui régit désormais la procédure, ne fixe aucun délai "
        "pour présenter une demande : celle-ci est « considérée comme ayant été présentée » dès que l’intéressé exprime "
        "en personne à une autorité compétente le souhait de bénéficier d’une protection internationale"
        "[[REG2024-1348, art. 26, §1]]. La demande doit en outre être examinée « de manière objective, impartiale et "
        "individualisée »[[REG2024-1348, art. 34, §2]].",
        "Le moment de la demande n’intervient donc qu’au stade de l’appréciation de la crédibilité, et seulement pour "
        "les aspects des déclarations qui ne sont pas étayés par des preuves. Or, depuis le 12 juin 2026, il n’est plus "
        "une condition autonome du bénéfice du doute : l’article 4, §5, du règlement (UE) 2024/1347, directement "
        "applicable, n’en retient que quatre, à savoir l’effort réel pour étayer la demande, la production des éléments "
        "disponibles, la cohérence et la plausibilité des déclarations, et la crédibilité générale du demandeur, "
        "appréciée « compte tenu, entre autres, de la date à laquelle le demandeur a demandé une protection "
        "internationale »[[REG2024-1347, art. 4, §5]]. L’ancienne condition selon laquelle le demandeur devait avoir "
        "présenté sa demande « dès que possible, à moins qu’il puisse avancer de bonnes raisons pour ne pas l’avoir "
        "fait » n’a pas été reprise[[= Anciennement loi du 15 décembre 1980, art. 48/6, §4, d), abrogé par l’article "
        "25, 4°, de la loi du 16 juin 2026, et directive 2011/95/UE, art. 4, §5, d)]]. La date de la demande n’est "
        "donc plus qu’un élément parmi d’autres de l’appréciation de la crédibilité générale, qui doit en outre tenir "
        "compte, « le cas échéant, des raisons pour lesquelles il ne l’a pas demandée plus tôt »[[REG2024-1347, "
        "considérant 27]].",
        "Il s’ensuit que le seul dépassement du délai de huit jours ouvrables ne peut ni fonder le refus d’une "
        "protection internationale, ni priver {le_demandeur} du bénéfice du doute : faire de ce délai une condition "
        "supplémentaire reviendrait à ajouter aux règlements, directement applicables dans tout État membre, une "
        "exigence qu’ils ne contiennent pas[[TFUE, art. 288]]. Les éléments établis par des documents ou par les "
        "informations disponibles sur le pays d’origine restent, quant à eux, établis quel que soit le moment de la "
        "demande.",
        "Tout au plus la date de la demande peut-elle constituer un indice, à apprécier avec l’ensemble des éléments du "
        "dossier, notamment le profil du demandeur et les circonstances de son arrivée[[CCE-273434, §14 ; = arrêt rendu "
        "sous l’empire de l’ancien article 48/6, §4]]. Elle ne saurait, à elle seule, fonder le refus d’une protection "
        "internationale.",
        "Cette lecture est conforme aux exigences internationales. La Cour européenne des droits de l’homme a jugé que "
        "l’application automatique et mécanique d’un délai bref pour l’introduction d’une demande d’asile est "
        "incompatible avec la protection de la valeur fondamentale consacrée par l’article 3 de la Convention"
        "[[JABARI, §40]]. Le Comité exécutif du HCR a de même rappelé que le non-respect d’un délai, ou d’autres "
        "exigences formelles, ne devrait pas conduire à écarter une demande d’asile de tout examen[[HCR-EXCOM15, "
        "point i)]]."]),
    ("pi", "L’introduction de la demande dans le délai", "Les raisons du délai : cadre (à compléter)", True, [
        "Les raisons du délai doivent être examinées concrètement : le règlement (UE) 2024/1347 impose de tenir "
        "compte, « le cas échéant, des raisons pour lesquelles [le demandeur] ne l’a pas demandée plus tôt »"
        "[[REG2024-1347, considérant 27]], et le règlement (UE) 2024/1348 ne permet un traitement accéléré que si le "
        "retard est intervenu « sans motif valable »[[REG2024-1348, art. 42, §1er, h) et i)]]. Or les recherches "
        "consacrées aux parcours des demandeurs d’asile montrent que le moment de la demande s’explique le plus souvent "
        "par des circonstances étrangères à toute volonté de tromper les autorités ; là où le retard est légalement "
        "présumé nuire à la crédibilité, la doctrine relève qu’il s’agit d’éléments « souvent sans rapport avec la "
        "crainte de persécution » de l’intéressé[[KENDALL-2022 +trad]].",
        "En l’espèce, {le_demandeur} {a|ont} présenté {sa} demande [nombre] jours ouvrables après {son} arrivée, "
        "pour les raisons exposées ci-après."]),
    ("pi", "L’introduction de la demande dans le délai", "Motif valable : ignorance de l’existence de la protection", False, [
        "D’abord, {le_demandeur} {ignorait|ignoraient} l’existence même d’une procédure de protection "
        "internationale et la possibilité d’y recourir. Cette situation n’a rien d’exceptionnel. Une étude menée auprès "
        "de quatre-vingt-sept demandeurs d’asile venus d’Afghanistan, de Colombie, du Kosovo et de Somalie constate "
        "que la plupart « savaient peu de choses de la politique et de la pratique en matière d’asile », et en "
        "identifie cinq raisons : beaucoup n’avaient pas choisi eux-mêmes leur destination, peu avaient de la famille "
        "ou des amis dans le pays d’accueil, certains avaient reçu des informations fausses ou trompeuses, beaucoup "
        "avaient quitté leur pays dans la précipitation et la plupart étaient relativement peu scolarisés"
        "[[GILBERT-KOSER-2006, p. 1209 +trad]]. Une étude publiée en 2025 par le ministère britannique de l’Intérieur "
        "relève de même que « peu de demandeurs d’asile disposent de ressources financières, peuvent planifier à "
        "l’avance ou ont les moyens de rechercher le pays qui leur conviendrait le mieux », et que seules les personnes "
        "les plus aisées accèdent à une information complète[[HOMEOFFICE-2025, sections 2.1 et 2.4.3 +trad]]. "
        "[Préciser : niveau d’études, conditions du départ, absence de contacts en Belgique, informations reçues en "
        "chemin.]"]),
    ("pi", "L’introduction de la demande dans le délai", "Motif valable : ignorance que sa situation relève d’une protection", False, [
        "Ensuite, même une personne qui sait que l’asile existe peut ignorer que sa propre situation y correspond. La "
        "qualification de réfugié ou de bénéficiaire de la protection subsidiaire est une opération juridique : il "
        "n’appartient pas au demandeur d’analyser son cas au point d’identifier lui-même le motif de persécution, "
        "cette tâche incombant aux instances d’asile[[HCR-GUIDE, §66]]. [Exposer ici pourquoi {le_demandeur} ne "
        "{pensait|pensaient} pas pouvoir prétendre à une protection : persécution émanant d’un acteur non étatique "
        "ou perçue comme une affaire privée, violences liées au genre, orientation sexuelle, séjour d’abord envisagé "
        "comme temporaire, croyance qu’un autre titre de séjour (visa, regroupement familial, études, travail) était "
        "la seule voie possible…]",
        "Cette ignorance est sans incidence sur la qualité de réfugié, qui préexiste à sa reconnaissance (voir supra, "
        "sur le caractère déclaratif du statut). La Cour de justice de l’Union européenne a d’ailleurs jugé que "
        "l’obligation de présenter les éléments de la demande « aussi rapidement que possible » « est tempérée par "
        "l’exigence qui est imposée aux autorités compétentes […] de mener l’entretien en tenant compte de la "
        "situation personnelle ou générale dans laquelle s’inscrit la demande, notamment de la vulnérabilité du "
        "demandeur et de procéder à une évaluation individuelle de cette demande »[[CJUE-ABC, §70]], de sorte "
        "qu’un demandeur ne peut être jugé non crédible au seul motif qu’il n’a pas dévoilé un élément sensible de "
        "sa demande « à la première occasion qui lui a été donnée »[[CJUE-ABC, §71]]."]),
    ("pi", "L’introduction de la demande dans le délai", "Motif valable : dépendance à l’égard des passeurs", False, [
        "{Le_demandeur} {était|étaient} en outre sous l’emprise [du passeur / d’un réseau]. Les recherches montrent "
        "que les passeurs choisissent souvent la destination finale[[GILBERT-KOSER-2006, p. 1209 +trad]], que « les "
        "agents prenaient les décisions relatives à la destination des demandeurs d’asile », et que certains ne "
        "quittent pas leur pays avec l’objectif d’atteindre un pays déterminé mais y sont « poussés » en cours de "
        "route[[HOMEOFFICE-2025, section 2.4.2 +trad]]. Une personne qui dépend d’un passeur pour son hébergement, ses "
        "documents ou la suite de son voyage, ou qui lui doit de l’argent, n’est pas en mesure de se présenter "
        "librement aux autorités. [S’il existe des indices de traite des êtres humains, les exposer, pièces à l’appui.]"]),
    ("pi", "L’introduction de la demande dans le délai", "Motif valable : traumatisme, honte et violences sexuelles", False, [
        "Le délai s’explique aussi par l’état psychologique {du_demandeur} [, attesté par (pièce : ajoutez son "
        "repère)]. L’évitement de ce qui rappelle l’événement traumatique est l’un des symptômes caractéristiques du "
        "trouble de stress post-traumatique[[DSM5, trouble de stress post-traumatique, critère C]] : se présenter aux "
        "autorités pour relater les faits suppose précisément de les affronter. Une étude menée auprès de demandeurs "
        "d’asile entendus par l’administration britannique a montré que les personnes ayant subi des violences "
        "sexuelles éprouvent davantage de difficultés à révéler des informations personnelles, sont plus susceptibles "
        "de se dissocier pendant les entretiens et présentent des niveaux significativement plus élevés de symptômes "
        "post-traumatiques et de honte ; les auteurs concluent à « l’importance de la honte, de la dissociation et de "
        "la psychopathologie » dans la révélation des faits[[BOGNER-2007, p. 75 +trad]]. La Cour de justice de "
        "l’Union européenne a tenu compte de cette réticence à propos de l’orientation sexuelle[[CJUE-ABC, "
        "§§69-71]]."]),
    ("pi", "L’introduction de la demande dans le délai", "Motif valable : langue, méfiance et accès à l’information", False, [
        "Enfin, {le_demandeur} ne {parlait|parlaient} ni le français, ni le néerlandais, ni l’anglais, et ne "
        "{savait|savaient} pas où s’adresser. [Selon le dossier : méfiance à l’égard des autorités, fondée sur "
        "l’expérience des forces de l’ordre dans le pays d’origine ; informations fausses reçues en chemin, par exemple "
        "la crainte d’être renvoyé vers le premier pays traversé ; impossibilité matérielle de se faire enregistrer "
        "(préciser les dates et démarches, pièces à l’appui).] Ces circonstances, étrangères à toute volonté de "
        "retarder ou d’empêcher un éloignement, constituent autant de motifs valables.",
        "La méfiance à l’égard des institutions mérite d’être prise au sérieux. Une personne qui a été persécutée "
        "par l’État, ou qui craint sérieusement de l’être, a appris que les institutions peuvent être la source du "
        "danger plutôt que de la protection. Le Haut-Commissariat des Nations unies pour les réfugiés le reconnaît : "
        "« Une personne qui, par expérience, a appris à craindre les autorités de son propre pays peut continuer à "
        "éprouver de la défiance à l’égard de toute autre autorité »[[HCR-GUIDE, §198]]. Il souligne que la "
        "rationalité que l’État prête aux personnes qui craignent d’être persécutées, et qui voudrait qu’elles "
        "s’adressent immédiatement aux procédures prévues, « peut ne pas s’appliquer de manière aussi simple dans "
        "les situations individuelles » : la difficulté à faire confiance aux autorités, fondée sur l’expérience "
        "vécue dans le pays d’origine, « implique clairement une motivation à ne pas s’engager dans un système qui "
        "exige un certain degré de confiance »[[HCR-BEYOND-PROOF, p. 200 +trad]]. Un demandeur peut ainsi avoir "
        "tardé à introduire sa demande « par crainte ou méfiance à l’égard des autorités, ou par doute quant à la "
        "capacité de la procédure à aboutir à un résultat équitable », et l’instance d’asile doit tenir compte des "
        "effets de la désorientation, des barrières linguistiques, de l’anxiété et de la peur[[HCR-BEYOND-PROOF, "
        "p. 202 +trad]]. Les recherches en sciences sociales le confirment. Lorsque le lien de confiance entre "
        "l’individu et l’État est rompu, « le réfugié ne fait plus confiance à son propre gouvernement pour sa "
        "propre vie »[[HYNES-2003, p. 4 +trad]] ; une fois arrivé dans le pays d’asile, sa méfiance envers les "
        "agents de l’immigration et les fonctionnaires est « nourrie par l’expérience passée des agents publics "
        "dans son pays d’origine »[[HYNES-2003, p. 5 +trad]]. Une étude qualitative menée auprès de jeunes "
        "demandeurs d’asile en Irlande montre de même que ceux qui avaient perçu le gouvernement de leur pays "
        "comme indigne de confiance traitaient les personnes perçues comme travaillant pour l’État d’accueil "
        "(travailleurs sociaux, agents de l’immigration, médecins) « avec une suspicion particulière, surtout au "
        "début »[[NIRAGHALLAIGH-2014, p. 91 +trad]].",
        "Retrouver la confiance nécessaire pour s’adresser aux institutions prend du temps. Cette confiance se "
        "reconstruit le plus souvent par l’intermédiaire de proches qui connaissent la procédure d’asile, ou grâce "
        "à un réseau qui se constitue progressivement autour du demandeur : soutien psychologique, accompagnement "
        "dans les démarches, conseil juridique, aide matérielle et financière. La même étude conclut que "
        "restaurer une confiance détruite ou gravement atteinte « prendra vraisemblablement du temps et des efforts "
        "soutenus »[[NIRAGHALLAIGH-2014, p. 96 +trad]]. Les organisations communautaires de réfugiés « ont beaucoup "
        "à offrir » à ceux qui tentent de reconstruire leur vie et de « reconstituer la confiance »[[HYNES-2003, "
        "p. 7 +trad]] ; en revanche, si les individus peuvent recommencer à faire confiance, « il est peu probable "
        "que le monde de l’administration regagne la confiance des réfugiés »[[HYNES-2003, p. 8 +trad]]. C’est "
        "pourquoi l’accès aux institutions passe si souvent par des personnes de confiance. À l’inverse, l’absence de famille ou "
        "d’amis dans le pays d’accueil figure parmi les raisons pour lesquelles les demandeurs d’asile savent peu "
        "de choses de la procédure à leur arrivée[[GILBERT-KOSER-2006, p. 1209 +trad]]. Le Haut-Commissariat "
        "rappelle d’ailleurs que le fait qu’une demande n’ait été introduite « qu’après avoir reçu les conseils "
        "d’un avocat » n’exclut pas la crédibilité des faits invoqués[[HCR-BEYOND-PROOF, p. 202 +trad]]. "
        "[Selon le dossier : préciser comment ce réseau s’est constitué (proche, compatriote, association, service "
        "social, psychologue, avocat), à quelle date, quelle aide il a apportée (psychologique, administrative, "
        "juridique, financière), pièces à l’appui : attestations, rendez-vous, échanges.] Le moment où "
        "{le_demandeur} {a|ont} introduit {sa} demande correspond ainsi à celui où {il} {a|ont} retrouvé les moyens "
        "et la confiance nécessaires pour s’adresser aux autorités belges ; ce délai n’est pas le signe d’une "
        "absence de crainte, mais la conséquence de la persécution elle-même."]),
    ("pi", "L’introduction de la demande dans le délai", "Procédure accélérée pour tardiveté", False, [
        "Le traitement accéléré d’une demande en raison de son moment n’est possible que si trois conditions sont "
        "réunies : le demandeur est entré ou a prolongé son séjour illégalement, il ne s’est pas présenté aux "
        "autorités ou n’a pas présenté sa demande « le plus rapidement possible compte tenu des circonstances de son "
        "entrée », et il l’a fait « sans motif valable »[[REG2024-1348, art. 42, §1er, h)]]. Pour le demandeur entré "
        "légalement, le délai s’apprécie « compte tenu des motifs de sa demande », « sans préjudice du besoin d’une "
        "protection internationale apparaissant sur place »[[REG2024-1348, art. 42, §1er, i)]]. Le critère européen "
        "n’est donc pas le délai de huit jours de l’article 50, mais un délai apprécié au regard des circonstances, qui "
        "réserve expressément les motifs valables.",
        "S’agissant d’une demande de protection internationale, ces conditions doivent en outre être lues à la lumière "
        "du caractère déclaratif du statut de réfugié.",
        "[[BLOC Caractère déclaratif du statut de réfugié]]",
        "Il en résulte, d’abord, que la condition tenant à l’entrée ou au séjour illégal ne peut pas être appliquée "
        "comme si elle révélait, par elle-même, un usage abusif de la procédure. Une personne qui remplit les "
        "conditions de la définition du réfugié est un réfugié dès avant la reconnaissance de son statut ; or, pour un "
        "réfugié, l’entrée irrégulière est le plus souvent la conséquence même de la fuite. La Convention de Genève en "
        "tient compte : son article 31, §1er, interdit d’appliquer des sanctions pénales, du fait de leur entrée ou de "
        "leur séjour irréguliers, aux réfugiés qui, arrivant directement du territoire où leur vie ou leur liberté "
        "était menacée, entrent ou se trouvent sur le territoire sans autorisation, sous la réserve qu’ils se "
        "présentent sans délai aux autorités et leur exposent des raisons reconnues valables de leur entrée ou présence "
        "irrégulières[[GENEVE, art. 31, §1er]]. Si la procédure accélérée n’est pas une sanction pénale, cette "
        "disposition exprime un principe : l’irrégularité de l’entrée d’un réfugié ne peut, en elle-même, lui être "
        "reprochée. Même la réserve de l’article 31 s’apprécie au regard des raisons exposées par l’intéressé, et non "
        "d’un délai fixe.",
        "Il en résulte, ensuite, que la crainte de persécution qui a motivé la fuite, les conditions de celle-ci et "
        "leurs conséquences (traumatisme, dépendance à l’égard des passeurs, méconnaissance de la langue et de la "
        "procédure) constituent précisément des « motifs valables » au sens de l’article 42, §1er, h) et i), du "
        "règlement (UE) 2024/1348. Le règlement (UE) 2024/1347 impose d’ailleurs de tenir compte, « le cas échéant, "
        "des raisons pour lesquelles [le demandeur] ne l’a pas demandée plus tôt »[[REG2024-1347, considérant 27]].",
        "Enfin, la procédure accélérée ne dispense pas d’examiner le bien-fondé de la demande : l’autorité « accélère, "
        "dans le respect des principes de base et des garanties fondamentales », l’examen « du bien-fondé » de la "
        "demande[[REG2024-1348, art. 42, §1er, al. 1er]]. Et le seul fait d’avoir présenté la demande après le délai "
        "de huit jours ne suffit pas à établir qu’elle aurait été présentée « qu’afin de retarder, d’empêcher ou "
        "d’éviter l’exécution d’une décision relative à son éloignement »[[REG2024-1348, art. 42, §1er, d)]], d’autant "
        "que {le_demandeur} {justifie|justifient} ce délai par [raisons] (voir supra)."]),
    # --- Protection internationale (dossier de 2019, adapté au règlement (UE) 2024/1347) -----------------
    ("pi", "Pays sûr ?", "Pays d’origine sûr : une présomption qui se renverse au cas par cas", True, [
        "[{Le_pays} figure sur la liste belge des pays d’origine sûrs[[AR-PAYS-SURS-2025, art. 1er]] / sur la liste des "
        "pays d’origine sûrs au niveau de l’Union[[UE-LISTE-PAYS-SURS]].] Cette désignation ne ferme pas la porte à la "
        "protection : elle ne dispense ni d’enregistrer la demande, ni de l’examiner. Le pays d’origine sûr ne figure "
        "pas parmi les motifs d’irrecevabilité[[REG2024-1348, art. 38]] ; il est seulement un motif d’examen "
        "accéléré[[REG2024-1348, art. 42, §1er, e)]], examen qui se déroule « dans le respect des principes de base et "
        "des garanties fondamentales »[[REG2024-1348, art. 42, §1er, al. 1er]] et doit rester objectif, impartial et "
        "individualisé[[REG2024-1348, art. 34, §2]].",
        "La désignation n’instaure qu’une présomption, qui se renverse au cas par cas. Le concept de pays d’origine sûr "
        "ne peut s’appliquer que si « le demandeur ne peut fournir d’éléments justifiant pourquoi le concept de pays "
        "d’origine sûr ne lui est pas applicable, dans le cadre d’une évaluation individuelle »[[REG2024-1348, art. 61, "
        "§5, c)]]. Le droit belge est construit de la même manière : le Commissaire général ne peut refuser la "
        "protection à un ressortissant d’un pays d’origine sûr que « lorsque l’étranger n’a pas fait valoir de raisons "
        "sérieuses permettant de penser qu’il ne s’agit pas d’un pays d’origine sûr en raison de sa situation "
        "personnelle »[[LOI1980, art. 57/6/1, §3, al. 1er]]. Le rapport au Roi qui accompagne la liste belge le rappelle "
        "expressément : « Le simple fait pour un demandeur de protection internationale d’être originaire d’un pays "
        "d’origine sûr n’aura en aucun cas pour conséquence automatique que sa demande de protection internationale "
        "sera refusée »[[AR-PAYS-SURS-2025, rapport au Roi]].",
        "La Cour de justice le dit de manière générale : le régime des pays d’origine sûrs « repose sur une forme de "
        "présomption réfragable de protection suffisante dans le pays d’origine, laquelle peut […] être renversée par "
        "le demandeur s’il fait état de raisons sérieuses tenant à sa situation personnelle »[[CJUE-CV-2024, point 47]], "
        "car « même dans un pays généralement sûr pour toute sa population, il n’existe aucune garantie absolue de "
        "sécurité pour chaque individu »[[CJUE-ALACE-2025, point 97]].",
        "Cette lecture s’impose aussi au regard de la Convention de Genève, que les États appliquent « sans "
        "discrimination quant à la race, la religion ou le pays d’origine »[[GENEVE, art. 3]], et du caractère absolu de "
        "l’interdiction du renvoi vers un risque de torture ou de traitements inhumains ou dégradants[[CEDH, art. 3]]"
        "[[CHARTE, art. 19, §2]].",
        "[Exposer les raisons sérieuses propres {au_demandeur} : persécutions déjà subies, profil exposé (opinions "
        "politiques, orientation sexuelle, genre, appartenance à une minorité…), absence de protection des autorités ; "
        "pièces et sources de la partie 4.]"]),
    ("pi", "Pays sûr ?", "Pays d’origine sûr : les personnes exposées malgré la désignation", False, [
        "La désignation d’un pays comme sûr repose sur une appréciation générale : le droit belge exige qu’il soit "
        "démontré que, « d’une manière générale et de manière durable », il n’y est pas recouru à des actes de "
        "persécution et qu’il n’y existe aucun risque réel d’atteintes graves[[LOI1980, art. 57/6/1, §3, al. 2]]. Le "
        "règlement permet d’assortir la désignation d’« exceptions pour des parties spécifiques de son territoire ou des "
        "catégories de personnes clairement identifiables »[[REG2024-1348, art. 61, §2]], et le concept ne s’applique "
        "pas au demandeur qui appartient à une telle catégorie[[REG2024-1348, art. 61, §5, b)]]. Une désignation "
        "générale n’exclut donc pas qu’un groupe reste exposé.",
        "[Exemple pour le Maroc : dans l’évaluation reprise par le rapport au Roi de l’arrêté du 3 décembre 2025, la "
        "Commission européenne relève elle-même que « Si le comportement homosexuel entre adultes consentants est "
        "généralement toléré dans la sphère privée, il reste une infraction pénale en vertu du code pénal. La situation "
        "des personnes LGBTIQ reste compliquée », et précise que la désignation est faite « sans préjudice des "
        "difficultés spécifiques rencontrées par certains groupes dans le pays, qui peuvent mériter une attention "
        "particulière »[[AR-PAYS-SURS-2025, rapport au Roi]].] {Le_demandeur} {appartient|appartiennent} à "
        "[catégorie], exposée {en_pays} à [risques], comme l’établissent les sources citées dans la partie 4.",
        "La Cour de justice a jugé, sous l’empire de la directive 2013/32/UE, que le juge saisi d’un recours doit "
        "soulever, sur la base du dossier et des éléments portés à sa connaissance, une méconnaissance des conditions "
        "matérielles de la désignation[[CJUE-CV-2024, point 98]]. Elle a ajouté que « la possibilité pour le demandeur "
        "de renverser cette présomption requiert, pour être effective, que ce demandeur soit mis en mesure de connaître "
        "les raisons pour lesquelles son pays d’origine est présumé sûr »[[CJUE-ALACE-2025, point 73]] : l’État doit "
        "garantir « un accès suffisant et adéquat » aux sources d’information sur lesquelles repose la "
        "désignation[[CJUE-ALACE-2025, point 87]], et le juge peut tenir compte d’informations qu’il a lui-même recueillies, dans "
        "le respect du contradictoire[[CJUE-ALACE-2025, point 86]]. Le règlement (UE) 2024/1348 autorise désormais des exceptions "
        "par catégories de personnes, ce que la Cour présente comme un nouveau choix du législateur[[CJUE-ALACE-2025, point "
        "106]] ; mais les exigences de contrôle et d’accès aux sources procèdent du droit à un recours "
        "effectif[[CHARTE, art. 47]] et gardent toute leur pertinence."]),
    ("pi", "Pays sûr ?", "Pays d’origine sûr : une désignation fragile (Maroc)", False, [
        "L’inscription du Maroc sur la liste belge repose sur des bases que le Gouvernement lui-même présente comme "
        "discutables. Selon le rapport au Roi, « En ce qui concerne Maroc, il est donc décidé de s’écarter des avis du "
        "Commissaire général » ; le Gouvernement s’appuie principalement sur la baisse du taux de protection, tout en "
        "admettant que « le taux de protection ne constitue pas un critère déterminant »[[AR-PAYS-SURS-2025, rapport au "
        "Roi]]. Or l’évaluation d’un pays d’origine sûr « doit reposer sur une série de sources d’information », dont "
        "celles du Haut Commissariat des Nations Unies pour les réfugiés et du Conseil de l’Europe[[LOI1980, art. "
        "57/6/1, §3, al. 3]], et le règlement impose la même exigence[[REG2024-1348, art. 61, §3]]. Un taux de "
        "reconnaissance peu élevé mesure les décisions prises, non l’absence de persécution : il ne saurait, à lui seul, "
        "fonder la présomption.",
        "Le Maroc figure aussi sur la liste des pays d’origine sûrs au niveau de l’Union[[UE-LISTE-PAYS-SURS]] : la "
        "même présomption réfragable s’applique, et {le_demandeur} peut la renverser par des éléments propres à "
        "{sa} situation[[REG2024-1348, art. 61, §5, c)]]. [Confronter la désignation aux sources de la partie 4 "
        "(organes de traités, ONG) sur la situation {en_pays}.]"]),
    ("pi", "Pays sûr ?", "Procédure accélérée : quand, pourquoi, et comment en sortir", False, [
        "La procédure accélérée n’est pas une procédure de rejet : c’est un examen au fond de la demande, mené dans des "
        "délais plus courts. Elle ne peut être appliquée que dans les cas limitativement énumérés par le règlement (UE) "
        "2024/1348[[REG2024-1348, art. 42, §1er]] : des questions sans pertinence pour la protection ; des déclarations "
        "manifestement incohérentes, contradictoires, fausses ou peu plausibles, ou qui contredisent les informations "
        "disponibles sur le pays d’origine ; la tromperie intentionnelle sur l’identité ou la nationalité ; une demande "
        "présentée uniquement pour retarder ou empêcher un éloignement ; l’origine d’un pays d’origine sûr ; un danger "
        "pour la sécurité nationale ou l’ordre public ; une demande ultérieure recevable ; l’absence, sans motif valable, "
        "de demande « le plus rapidement possible » ; une nationalité pour laquelle le taux de reconnaissance à "
        "l’échelle de l’Union est de 20 % ou moins. Le droit belge contient une liste comparable[[LOI1980, art. 57/6/1, "
        "§1er]].",
        "Le législateur justifie ces cas par le souci de traiter plus vite des demandes présumées moins susceptibles "
        "d’aboutir, « en tenant compte, entre autres, des différences importantes entre la première instance et les "
        "décisions finales »[[REG2024-1348, considérant 56]]. La Cour de justice rappelle toutefois que l’accélération "
        "se fait « sans préjudice de la réalisation d’un examen approprié et exhaustif et de l’accès effectif du "
        "demandeur aux garanties et aux principes fondamentaux »[[CJUE-ALACE-2025, point 102]]. L’examen se déroule "
        "« dans le respect des principes de base et des garanties fondamentales »[[REG2024-1348, art. 42, §1er, al. "
        "1er]] ; il reste objectif, impartial et individualisé et tient compte d’informations précises et actualisées "
        "sur le pays d’origine[[REG2024-1348, art. 34, §2]] ; la possibilité d’un entretien sur le fond demeure la "
        "règle[[REG2024-1348, art. 12, §1er]].",
        "Ce qui change réellement tient aux délais et au recours : l’examen doit être conclu au plus tard trois mois "
        "après l’introduction de la demande[[REG2024-1348, art. 35, §3]] ; le délai de recours est compris entre cinq "
        "et dix jours[[REG2024-1348, art. 67, §7, a)]] ; le rejet peut être qualifié de manifestement infondé si le "
        "droit national le prévoit[[REG2024-1348, art. 39, §4]] (en droit belge, jamais pour un mineur non "
        "accompagné[[LOI1980, art. 57/6/1, §2]]) ; surtout, le recours n’a pas d’effet suspensif "
        "automatique[[REG2024-1348, art. 68, §3, a), i)]]. Il faut alors demander au juge l’autorisation de rester sur "
        "le territoire pendant le recours, dans un délai d’au moins cinq jours à compter de la notification ; aucun "
        "éloignement ne peut avoir lieu tant que ce délai court ou que le juge n’a pas statué, et une assistance "
        "juridique gratuite est due sur demande[[REG2024-1348, art. 68, §§4 et 5]]. En droit belge, la procédure "
        "devant le Conseil du contentieux des étrangers est désormais réglée par la loi du 17 juin 2026, qui a remplacé "
        "les articles 39/1 et suivants de la loi du 15 décembre 1980 et prévoit un délai de recours de trente jours "
        "en procédure ordinaire, de dix jours en procédure accélérée et de cinq ou dix jours en procédure "
        "urgente[[LOI-CCE-2026]]. [Vérifier le délai et l’article applicables à la décision attaquée, tels qu’ils sont "
        "indiqués dans la décision notifiée.]",
        "Plusieurs voies permettent d’éviter la procédure accélérée ou d’en sortir :",
        "– la vulnérabilité : lorsque le soutien nécessaire ne peut être fourni dans le cadre de la procédure accélérée, "
        "« en accordant une attention particulière aux victimes de torture, de viol ou d’autres formes graves de violence "
        "psychologique, physique, sexuelle ou sexiste », l’autorité « n’applique pas, ou cesse d’appliquer, ces "
        "procédures »[[REG2024-1348, art. 21, §2]]. L’évaluation du besoin de garanties procédurales spéciales commence "
        "dès la présentation de la demande et doit être achevée dans les 30 jours[[REG2024-1348, art. 20]] : il faut "
        "signaler tôt les éléments de vulnérabilité et produire les attestations médicales ou psychologiques ;",
        "– la complexité : lorsque l’examen fait intervenir « des questions factuelles ou juridiques trop complexes pour "
        "être examinées dans le cadre d’une procédure accélérée », l’autorité peut poursuivre l’examen selon la "
        "procédure ordinaire[[REG2024-1348, art. 42, §2]] ;",
        "– les mineurs non accompagnés : l’examen accéléré ne leur est applicable que dans des cas limités[[REG2024-1348, "
        "art. 42, §3]], et leur demande ne peut pas être déclarée manifestement infondée[[LOI1980, art. 57/6/1, §2]] ; la "
        "Cour constitutionnelle avait déjà annulé l’application de la procédure accélérée aux mineurs non accompagnés "
        "au-delà des hypothèses prévues par le droit de l’Union[[CC-23-2021]] ;",
        "– le seuil de 20 % : il ne joue pas lorsqu’un changement important est intervenu dans le pays, ni pour une "
        "catégorie de personnes pour lesquelles ce taux n’est pas représentatif[[REG2024-1348, art. 42, §1er, j)]] "
        "(voir le bloc consacré à ce seuil) ;",
        "– le retard : les motifs valables exposés dans la section consacrée au délai d’introduction de la demande ;",
        "– le pays d’origine sûr : les raisons sérieuses propres {au_demandeur}, qui renversent la présomption ;",
        "– la procédure à la frontière, lorsqu’elle est envisagée : elle n’est pas appliquée, ou cesse de l’être, "
        "notamment pour des raisons médicales, y compris de santé mentale, ou lorsque le soutien nécessaire ne peut être "
        "fourni aux demandeurs ayant des besoins particuliers[[REG2024-1348, art. 53, §2]]."]),
    ("pi", "Pays sûr ?", "Seuil de 20 % : contester l’examen accéléré fondé sur la nationalité", False, [
        "L’examen est accéléré lorsque {le_demandeur} {possède|possèdent} la nationalité d’un pays pour lequel « la "
        "proportion de décisions prises par l’autorité responsable de la détermination qui octroient une protection "
        "internationale est, selon les dernières données disponibles d’Eurostat concernant la moyenne annuelle à "
        "l’échelle de l’Union, de 20 % ou moins »[[REG2024-1348, art. 42, §1er, j)]]. Ce critère est un chiffre "
        "collectif : il ne dit rien de la situation de la personne, et il ne peut justifier qu’un traitement plus "
        "rapide, jamais un refus. L’examen reste individuel[[REG2024-1348, art. 34, §2]].",
        "Le taux pertinent est celui publié par Eurostat « solely for the purpose » du règlement (UE) 2024/1348 : la "
        "part des décisions octroyant le statut de réfugié ou la protection subsidiaire dans l’ensemble des décisions "
        "de première instance, pour l’Union sans le Danemark[[EUROSTAT-20]]. [Taux publié pour {le_pays} : [x] % "
        "(année [aaaa]) ; nombre de décisions : [n].] Un taux signalé comme peu fiable, faute de 30 décisions au moins, "
        "ne peut fonder une présomption sérieuse. Un autre chiffre (taux belge, taux incluant les statuts humanitaires "
        "nationaux, année plus ancienne) ne correspond pas au critère légal.",
        "La disposition prévoit elle-même deux exceptions, que le considérant 56 formule comme une obligation : dans "
        "ces cas, « l’examen de la demande ne devrait pas être accéléré »[[REG2024-1348, considérant 56]].",
        "– un changement important dans le pays depuis la publication des données d’Eurostat[[REG2024-1348, art. 42, "
        "§1er, j)]]. Lorsque l’Agence de l’Union européenne pour l’asile a constaté un tel changement dans une note "
        "d’orientation, les États membres doivent s’y référer[[REG2024-1348, art. 42, §1er, al. 2]][[EUAA-ORIENTATION]]. "
        "[Événements postérieurs à l’année de référence : [coup d’État, conflit, vague de répression, nouvelle loi "
        "pénale…], sources de la partie 4.] ;",
        "– l’appartenance à « une catégorie de personnes pour lesquelles la proportion de 20 % ou moins ne peut être "
        "considérée comme représentative de leurs besoins en matière de protection, compte tenu, entre autres, des "
        "différences importantes entre les décisions prises en première instance et les décisions finales »"
        "[[REG2024-1348, art. 42, §1er, j)]], notamment « en raison d’un motif spécifique de persécution »"
        "[[REG2024-1348, considérant 56]]. [{Le_demandeur} {appartient|appartiennent} à [catégorie : opposants "
        "politiques, personnes LGBTIQ, femmes exposées à des violences de genre, minorité…], pour laquelle les "
        "sources de la partie 4 établissent un risque spécifique.]",
        "Le taux de première instance ne reflète pas non plus l’issue réelle des demandes : les décisions rendues sur "
        "recours sont publiées séparément par Eurostat[[EUROSTAT-FINALES]], et l’Agence de l’Union européenne pour "
        "l’asile relève que ses propres taux « do not account for cases decided by the judiciary »[[EUAA-TAUX]]. "
        "[Comparer, pour {le_pays}, le taux de première instance et la part des décisions positives sur "
        "recours[[EUAA-2DE-INSTANCE]] ; au besoin, le taux de protection du Commissariat général pour cette "
        "nationalité[[CGRA-CHIFFRES]].]",
        "Enfin, le règlement ne permet de qualifier un rejet de manifestement infondé que si le droit national "
        "l’autorise[[REG2024-1348, art. 39, §4]]. Or le droit belge ne le prévoit que dans les situations énumérées à "
        "l’article 57/6/1, §1er, a) à j), de la loi du 15 décembre 1980, parmi lesquelles le seuil de 20 % ne figure "
        "pas[[LOI1980, art. 57/6/1, §2]] : un rejet fondé sur ce seul critère ne peut pas être qualifié de manifestement "
        "infondé.",
        "[Point d’attention : cet argument est une interprétation, qui n’a pas encore été tranchée par le Conseil du "
        "contentieux des étrangers. Il repose sur l’article 57/6/1, §2, tel qu’il était rédigé le 29 septembre 2026 : "
        "vérifier qu’une loi n’a pas, depuis, ajouté le seuil de 20 % à la liste belge. Le Commissaire général pourrait "
        "objecter que le règlement est directement applicable et que son article 39, §4, vise tous les cas de "
        "l’article 42 ; la réponse est que cette disposition exige une autorisation donnée « en vertu du droit "
        "national », et que le législateur belge ne l’a donnée que pour les cas qu’il énumère.]",
        "Quoi qu’il en soit, l’examen reste toujours individuel. Quel que soit le motif d’accélération, l’autorité "
        "« examine les demandes de manière objective, impartiale et individualisée », en tenant compte des déclarations "
        "et documents {du_demandeur} et d’informations précises et actualisées sur le pays d’origine[[REG2024-1348, "
        "art. 34, §2]], et l’examen accéléré se déroule « dans le respect des principes de base et des garanties "
        "fondamentales »[[REG2024-1348, art. 42, §1er, al. 1er]]. Le seuil de 20 % ne détermine que le rythme de la "
        "procédure, jamais son issue : il ne figure pas parmi les motifs d’irrecevabilité[[REG2024-1348, art. 38]] et "
        "aucune disposition ne permet de rejeter une demande en raison de ce seul taux. La Cour de justice souligne "
        "qu’il n’existe « aucune garantie absolue de sécurité pour chaque individu », même dans un pays généralement "
        "sûr[[CJUE-ALACE-2025, point 97]] ; un taux statistique, qui ne décrit que des décisions passées, peut encore "
        "moins préjuger de la situation d’une personne. L’interdiction de renvoyer une personne vers un risque de "
        "torture ou de traitements inhumains ou dégradants est absolue[[CEDH, art. 3]][[CHARTE, art. 19, §2]].",
        "Il est dès lors demandé au Commissaire général de ne pas appliquer, ou de cesser d’appliquer, la procédure "
        "accélérée et, à tout le moins, de motiver spécialement sa décision au regard de ces exceptions."]),
    ("pi", "Pays sûr ?", "Pays tiers sûr : conditions strictes et évaluation individuelle", False, [
        "Le concept de pays tiers sûr permet de déclarer une demande irrecevable, sans l’examiner au fond, au motif que "
        "{le_demandeur} pourrait obtenir une protection dans un pays tiers[[REG2024-1348, art. 38, §1er, b)]]. Il "
        "s’agit d’une exception à l’examen de la demande dans l’Union : elle est d’interprétation stricte et subordonnée à "
        "des conditions cumulatives.",
        "Un pays ne peut être considéré comme pays tiers sûr que si les non-ressortissants n’y ont à craindre ni pour "
        "leur vie ni pour leur liberté, n’y courent aucun risque réel d’atteintes graves, y sont protégés contre le "
        "refoulement, et s’il existe « la possibilité de demander et, si les conditions sont remplies, de recevoir une "
        "protection effective »[[REG2024-1348, art. 59, §1er]]. À défaut de ratification et de respect de la Convention "
        "de Genève, la protection effective suppose au minimum le droit de rester dans le pays, des moyens de subsistance "
        "suffisants, l’accès aux soins de santé et à l’éducation, et une protection « toujours disponible dans l’attente "
        "d’une solution durable »[[REG2024-1348, art. 57]].",
        "Depuis le règlement (UE) 2026/463[[REG2026-463]], le lien exigé entre le demandeur et le pays tiers est élargi : "
        "il suffit désormais d’un « lien de connexion » rendant raisonnable que le demandeur se rende dans ce pays, d’un "
        "transit par ce pays « sur le trajet vers l’Union », ou d’un accord ou arrangement imposant à ce pays d’examiner "
        "le bien-fondé des demandes de protection effective[[REG2024-1348, art. 59, §5, al. 1er, b)]]. Sous la "
        "directive 2013/32/UE, la Cour de justice avait jugé contraire au droit de l’Union une réglementation "
        "permettant de déclarer une demande irrecevable au seul motif que le demandeur était arrivé par un État dans "
        "lequel il n’était pas exposé à des persécutions ou dans lequel était assuré un degré de protection "
        "adéquat[[CJUE-LH-2020, dispositif, point 1]].",
        "Cet élargissement ne supprime aucune garantie :",
        "– le concept ne s’applique que si le demandeur « ne peut fournir d’éléments justifiant que le concept de pays "
        "tiers sûr ne lui est pas applicable, dans le cadre d’une évaluation individuelle »[[REG2024-1348, art. 59, §5, "
        "al. 1er, a)]] : un passage bref, forcé ou marqué par des violences, l’absence de tout accès réel à une procédure "
        "d’asile dans le pays de transit ou un risque de renvoi en chaîne sont autant d’éléments à faire valoir ;",
        "– lorsque le pays n’est pas désigné, les conditions de sécurité doivent être remplies à l’égard du demandeur "
        "lui-même[[REG2024-1348, art. 59, §4, b)]], et une désignation peut comporter des exceptions pour des catégories "
        "de personnes[[REG2024-1348, art. 59, §2]] ;",
        "– pour un mineur non accompagné, le concept n’est admis que si ce n’est pas contraire à son intérêt supérieur, "
        "après assurance d’une prise en charge et d’une protection effective immédiate, et l’hypothèse de l’accord ou "
        "de l’arrangement ne s’applique pas[[REG2024-1348, art. 59, §6]] ;",
        "– l’irrecevabilité est exclue s’il est clair que le demandeur ne sera pas admis ou réadmis dans le pays "
        "tiers[[REG2024-1348, art. 38, §1er, b)]], et si ce pays ne l’admet pas, le demandeur a accès à la "
        "procédure[[REG2024-1348, art. 59, §9]] ;",
        "– le demandeur reçoit un document informant les autorités du pays tiers, dans leur langue, que sa demande n’a "
        "pas été examinée au fond[[REG2024-1348, art. 59, §8, b)]].",
        "Enfin, l’article 3 de la Convention européenne des droits de l’homme impose à l’État qui renvoie un demandeur "
        "vers un pays tiers sans examiner sa demande au fond d’apprécier de manière approfondie si l’intéressé y aura "
        "accès à une procédure d’asile adéquate le protégeant contre le refoulement ; une présomption de sécurité doit "
        "reposer sur une analyse de la situation et du système d’asile de ce pays[[ILIAS-AHMED, §§137-141 et 152-154]]. "
        "Le recours contre une décision d’irrecevabilité n’ayant pas d’effet suspensif automatique, il convient de "
        "demander au juge l’autorisation de rester[[REG2024-1348, art. 68, §3, b), et §§4-5]]. [Exposer : trajet, durée "
        "et conditions du passage dans le pays tiers, absence d’accès à la protection, risques de refoulement ; pièces "
        "et sources.]"]),
    ("pi", "4. À titre principal : l’octroi du statut de réfugié", "Caractère déclaratif du statut (renvoi)", True, [
        "[[BLOC Caractère déclaratif du statut de réfugié]]"]),
    ("pi", "1) La définition du réfugié et la crainte avec raison", "Définition du réfugié", True, [
        A_VERIFIER_REG + "Depuis le 12 juin 2026, les conditions d’octroi du statut de réfugié sont régies directement par "
        "le règlement (UE) 2024/1347 ; les articles 48/3 à 48/5 et 48/7 de la loi du 15 décembre 1980 sont abrogés et "
        "l’article 48/6 ne règle plus que la production et la traduction des pièces[[REG2024-1347 ; "
        "LOI2026]]. Est un réfugié « tout ressortissant de pays tiers qui, parce qu’il craint avec raison d’être persécuté "
        "du fait de sa race, de sa religion, de sa nationalité, de ses opinions politiques ou de son appartenance à un "
        "certain groupe social, se trouve hors du pays dont il a la nationalité […] »[[REG2024-1347, art. 3, point 5) ; "
        "GENEVE, art. 1er, A, 2]]. Les actes de persécution et les motifs de persécution sont précisés aux articles 9 et 10 "
        "du règlement[[REG2024-1347, art. 9 et 10]]."]),
    ("pi", "1) La définition du réfugié et la crainte avec raison", "Crainte avec raison : éléments objectif et subjectif",
     True, [
        A_VERIFIER_REG + "La crainte de persécution doit être fondée, « avec raison » : elle comporte un élément subjectif, "
        "la crainte éprouvée par {demandeur}, et un élément objectif, les circonstances qui la rendent vraisemblable au "
        "regard de la situation {en_pays}[[GENEVE, art. 1er, A, 2 ; HCR-GUIDE, §§37-38]]. Dans l’hypothèse d’un retour "
        "{en_pays}, {demandeur} {craint|craignent} [des persécutions de la part de …] (voir infra)."]),
    ("pi", "1) La définition du réfugié et la crainte avec raison", "Persécutions déjà subies : indice sérieux", False, [
        A_VERIFIER_REG + "Le fait qu’un demandeur a déjà été persécuté ou a déjà subi des atteintes graves, ou a déjà fait "
        "l’objet de menaces directes d’une telle persécution ou de telles atteintes, constitue un indice sérieux de la "
        "crainte fondée du demandeur d’être persécuté ou du risque réel de subir des atteintes graves, sauf s’il existe de "
        "bonnes raisons de penser que cette persécution ou ces atteintes graves ne se reproduiront pas[[REG2024-1347, art. "
        "4, §4 ; = anciennement loi du 15 décembre 1980, art. 48/7, abrogé par la loi du 16 juin 2026]]."]),
    ("pi", "2) Les acteurs des persécutions", "Acteurs des persécutions et de la protection", True, [
        A_VERIFIER_REG + "Les persécutions ou les atteintes graves peuvent émaner de l’État, de partis ou d’organisations qui "
        "contrôlent l’État ou une partie importante de son territoire, ou d’acteurs non étatiques, s’il peut être démontré "
        "que l’État ou ces partis ou organisations ne peuvent pas ou ne veulent pas accorder une protection contre les "
        "persécutions ou les atteintes graves[[REG2024-1347, art. 6]]. Cette protection doit être effective et non "
        "temporaire : elle suppose notamment « un système judiciaire effectif permettant de déceler, de poursuivre et de "
        "sanctionner » les actes constituant une persécution ou une atteinte grave[[REG2024-1347, art. 7]]. [Si l’autorité "
        "envisage une protection à l’intérieur du pays : REG2024-1347, art. 8.]"]),
    ("pi", "i. Les persécutions de groupe", "Persécution de groupe", False, [
        A_VERIFIER_REG + "Certes, l’octroi d’une protection internationale suppose que le demandeur ait des raisons "
        "personnelles de craindre des persécutions[[BODART-1995, p.49]]. Cette exigence ne peut toutefois exclure qu’un "
        "« individu subit des persécutions, ou en redoute, au seul motif qu’il appartient à un groupe persécuté »[[BODART-"
        "1995, p.49]]. Il y a persécution de groupe lorsqu’il existe dans l’État d’origine « une politique systématique de "
        "persécution d’un groupe déterminé, susceptible de frapper de manière indistincte tout membre dudit groupe »"
        "[[BODART-1995, p.50]]. Le Conseil du contentieux des étrangers admet l’existence de persécutions de groupe et en "
        "donne une définition similaire[[CCE-215858 ; CCE-217591]]. La seule appartenance à une minorité discriminée ne "
        "suffit pas, à elle seule, à fonder la reconnaissance du statut de réfugié[[BODART-1995, p.50]] : il faut établir "
        "la politique systématique qui vise ses membres."]),
    ("pi", "iii. Les craintes personnelles de persécutions émanant d’acteurs non étatiques",
     "Absence de protection contre les acteurs non étatiques", False, [
        A_VERIFIER_REG + "Lorsque les persécutions émanent d’acteurs non étatiques, il suffit de démontrer que l’État ne "
        "peut pas ou ne veut pas accorder une protection effective[[REG2024-1347, art. 6 et 7]]. Or {Le_pays} est tenu, en "
        "vertu de l’article 2 du Pacte international relatif aux droits civils et politiques, de respecter et de garantir "
        "à tous les individus relevant de sa juridiction les droits reconnus par le Pacte, dont celui de ne pas être soumis "
        "à la torture ni à des traitements cruels, inhumains ou dégradants[[PIDCP, art. 2 et 7]], et, en vertu de "
        "l’article 2 de la Convention contre la torture, de prendre des mesures efficaces pour empêcher de tels actes"
        "[[CAT, art. 2]]. [Montrer ici, sources à l’appui, que ces obligations ne sont pas respectées en pratique.]"]),
    ("pi", "5. À titre subsidiaire", "Examen sous l’angle de la protection subsidiaire", True, [
        A_VERIFIER_REG + "Si le statut de réfugié ne devait pas être reconnu à {demandeur}, {sa} demande doit être examinée "
        "sous l’angle de la protection subsidiaire, qui bénéficie à la personne qui ne remplit pas les conditions pour être "
        "reconnue réfugiée mais pour laquelle il existe des motifs sérieux et avérés de croire qu’elle courrait, en cas de "
        "retour dans son pays d’origine, un risque réel de subir des atteintes graves[[REG2024-1347, art. 3, point 6)]]."]),
    ("pi", "1) Les atteintes graves", "Protection subsidiaire : atteintes graves", True, [
        A_VERIFIER_REG + "Les atteintes graves sont la peine de mort ou l’exécution, la torture ou des traitements ou "
        "sanctions inhumains ou dégradants infligés au demandeur dans son pays d’origine, et des menaces graves et "
        "individuelles contre la vie ou la personne d’un civil en raison d’une violence aveugle en cas de conflit armé "
        "international ou interne[[REG2024-1347, art. 15]]. Nous examinerons les deux premières hypothèses[[REG2024-1347, "
        "art. 15, a) et b)]]."]),
    ("pi", "2) Les acteurs des atteintes graves", "Acteurs des atteintes graves (renvoi)", True, [
        "Comme pour le statut de réfugié, les atteintes graves peuvent émaner de l’État ou d’acteurs non étatiques lorsque "
        "l’État ne peut pas ou ne veut pas accorder une protection effective (voir supra)[[REG2024-1347, art. 6 et 7]]."]),
    ("pi", "B. Le principe de non-refoulement", "Non-refoulement (renvois)", True, [
        "Enfin, si le bénéfice de la protection subsidiaire devait être refusé à {demandeur}, nous demandons qu’{il} "
        "{bénéficie|bénéficient} de la protection offerte par le principe de non-refoulement.",
        "[[BLOC Convention contre la torture et article 33 de la Convention de Genève]]",
        "[[BLOC Cour européenne des droits de l’homme : article 3]]",
        "[[BLOC Conseil du contentieux des étrangers]]",
        "Dès lors, nous demandons, pour les mêmes raisons et au regard de l’argumentation développée supra concernant la "
        "protection subsidiaire, que {demandeur} ne {soit|soient} pas éloigné{e} {en_pays}."]),
    ("pi", "6. La demande", "Dispositif (protection internationale)", True, [
        "Au regard de tout ce qui précède, nous demandons respectueusement [au Commissariat général aux réfugiés et aux "
        "apatrides] :",
        "à titre principal, de reconnaître à {demandeur} le statut de réfugié, au sens de l’article 3, point 5), du "
        "règlement (UE) 2024/1347 et de l’article 1er, A, 2, de la Convention de Genève, en raison de [{ses} opinions "
        "politiques / {sa} religion / {son} appartenance à un certain groupe social] ;",
        "à titre subsidiaire, de {lui} accorder le statut de protection subsidiaire, au sens de l’article 3, point 6), et de "
        "l’article 15, [a) et] b), de ce règlement ;",
        "à titre infiniment subsidiaire, de constater qu’{il} {bénéficie|bénéficient} de la protection du principe de non-refoulement, en "
        "application de l’article 3 de la Convention européenne des droits de l’homme, de l’article 3 de la Convention "
        "contre la torture et de l’article 33 de la Convention de Genève."]),
    # --- 9ter (repris du dossier 9ter de 2021 ; à vérifier) -----------------------------------------------
    ("9ter", "A. Récapitulatif des éléments d’identification", "Identification des demandeurs", True, [
        "{demandeur} {demande|demandent}[ pour {eux} et pour les membres de {sa} famille] l’autorisation de séjourner sur le "
        "territoire belge en application de l’article 9ter de la loi du 15 décembre 1980 sur l’accès au territoire, le "
        "séjour, l’établissement et l’éloignement des étrangers, en raison de l’état de santé de [nom de la personne malade].",
        "[Nom, prénom], {né/née|né(e)} à [lieu] ({pays}), le [date]{| [répéter pour chaque personne]}. {Il} {est|sont} de "
        "nationalité [nationalité] et {réside|résident} effectivement [adresse].",
        "Les copies des passeports {du_demandeur} sont jointes à la présente demande[ajoutez ici, entre doubles crochets, le repère de chaque pièce, par exemple PIECE 04_Passeport]. [Le certificat "
        "de mariage et les certificats de naissance sont également joints.]"]),
    ("9ter", "B. Le fondement de la demande", "Article 9ter, §1er, alinéa 1er", True, [
        A_VERIFIER + "L’article 9ter, §1er, alinéa 1er, de la loi du 15 décembre 1980 sur l’accès au territoire, le "
        "séjour, l’établissement et l’éloignement des étrangers dispose que : « l’étranger qui séjourne en Belgique qui "
        "démontre son identité conformément au § 2 et qui souffre d’une maladie telle qu’elle entraîne un risque réel pour "
        "sa vie ou son intégrité physique ou un risque réel de traitement inhumain ou dégradant lorsqu’il n’existe aucun "
        "traitement adéquat dans son pays d’origine ou dans le pays où il séjourne, peut demander l’autorisation de "
        "séjourner dans le Royaume auprès du ministre ou son délégué »[[LOI1980, art. 9ter, §1er, al. 1er]]."]),
    ("9ter", "B. Le fondement de la demande", "Article 9ter et jurisprudence Paposhvili", True, [
        A_VERIFIER + "La Cour européenne des droits de l’homme a précisé que l’article 3 de la Convention s’oppose à "
        "l’éloignement d’une personne gravement malade lorsqu’il existe des motifs sérieux de croire qu’elle serait "
        "exposée, en raison de l’absence de traitements adéquats dans le pays de destination ou du défaut d’accès à "
        "ceux-ci, à un risque réel d’être exposée à un déclin grave, rapide et irréversible de son état de santé "
        "entraînant des souffrances intenses ou à une réduction significative de son espérance de vie[[PAPOSHVILI, "
        "§183]]."]),
    ("9ter", "B. Le fondement de la demande", "Portée autonome de l’article 9ter", True, [
        A_VERIFIER + "L’article 9ter offre une protection plus large que l’article 3 de la Convention européenne des "
        "droits de l’homme. Comme le souligne le Conseil du contentieux des étrangers, « le fait que l’article 3 de la "
        "CEDH constitue une norme supérieure à la loi du 15 décembre 1980, et prévoit éventuellement une protection moins "
        "étendue, ne fait pas obstacle à l’application de l’article 9ter, § 1er, alinéa 1er, de cette loi […]. La CEDH "
        "fixe en effet des normes minimales et n’empêche nullement les Etats parties de prévoir une protection plus large "
        "dans leur législation interne »[[CCE-241336, p.7]]. Il ajoute que « dès lors, le champ d’application de "
        "l’article 9ter de la loi du 15 décembre 1980 ne coïncide pas avec les situations dans lesquelles, selon la Cour "
        "E.D.H., un éloignement est contraire à l’article 3 de la CEDH »[[CCE-241336, p.7]]. Ce qui est licite au regard "
        "de l’article 53 de la Convention[[CEDH, art. 53]]. Le Conseil d’État a d’ailleurs jugé que « l’article 9ter de la "
        "loi du 15 décembre 1980 précitée ne constitue pas une transposition d’une norme du droit européen dérivé mais "
        "qu’il doit être appréhendé comme étant une simple norme de droit national […] », à interpréter « par seule "
        "référence au droit interne, de manière autonome »[[CE-228778, p.8]]. La Cour de cassation a, de même, admis que "
        "si une dégradation importante de l’état de santé de l’étranger ne suffit pas toujours à emporter la violation de "
        "l’article 3 de la Convention, l’article 9ter reste applicable à l’étranger qui se trouve dans une situation "
        "« susceptible d’exposer le demandeur à un risque sérieux de détérioration grave et irréversible de son état de "
        "santé »[[CASS-P150762F]]."]),
    ("9ter", "B. Le fondement de la demande", "Les deux hypothèses de l’article 9ter", True, [
        A_VERIFIER + "Le Conseil du contentieux des étrangers interprète cette disposition en ce sens « qu’il y a d’une "
        "part, des cas dans lesquels l’étranger souffre actuellement d’une maladie menaçant sa vie, ou d’une affection qui "
        "emporte actuellement un danger pour son intégrité physique, ce qui signifie que le risque invoqué pour sa vie ou "
        "l’atteinte à son intégrité physique doit être imminent et que l’étranger n’est de ce fait pas en état de voyager. "
        "D’autre part, il y a le cas de l’étranger qui n’encourt actuellement pas de danger pour sa vie ou son intégrité "
        "physique et peut donc en principe voyager, mais qui risque de subir un traitement inhumain et dégradant, s’il "
        "n’existe pas de traitement adéquat pour sa maladie ou son affection dans son pays d’origine ou dans le pays de "
        "résidence. Même si, dans ce dernier cas, il ne s’agit pas d’une maladie présentant un danger imminent pour la vie, "
        "un certain degré de gravité de la maladie ou de l’affection invoquée est toutefois requis »[[CCE-135035, p.12 ; "
        "CCE-135037, p.4 ; CCE-135038, p.9 ; CCE-135039, p.7 ; CCE-135041, p.4]]. Cette interprétation a été confirmée "
        "depuis[[CCE-248197, p.3 ; CCE-248703, p.3 ; CCE-253813, p.7]]. L’article 9ter, §1er, alinéa 1er, vise donc deux "
        "situations distinctes, dont chacune donne droit au séjour : celle d’une personne dont la maladie menace "
        "actuellement la vie ou l’intégrité physique au point qu’elle n’est pas en mesure de voyager, et celle d’une "
        "personne médicalement stable en Belgique qui subirait un traitement inhumain ou dégradant si elle était renvoyée "
        "dans son pays d’origine en raison de l’absence de traitement adéquat."]),
    ("9ter", "B. Le fondement de la demande", "Intérêt supérieur de l’enfant (renvoi)", False, [
        "[[BLOC Intérêt supérieur de l’enfant (article 74/13)]]"]),
    ("9ter", "2. L’absence de traitement adéquat", "Traitement adéquat : approprié et suffisamment accessible", True, [
        A_VERIFIER + "Selon la jurisprudence constante du Conseil du contentieux des étrangers, « il ressort des travaux "
        "préparatoires de la loi du 15 septembre 2006 ayant inséré l’article 9ter précité dans la loi, que le “traitement "
        "adéquat” mentionné dans cette disposition vise “un traitement approprié et suffisamment accessible dans le pays "
        "d’origine ou de séjour”, et que l’examen de cette question doit se faire “au cas par cas, en tenant compte de la "
        "situation individuelle du demandeur” […]. Il en résulte que pour être “adéquats” au sens de l’article 9ter "
        "précité, les traitements existant dans le pays d’origine ou de résidence du demandeur doivent être non seulement "
        "“appropriés” à la pathologie concernée, mais également “suffisamment accessibles” à l’intéressé dont la situation "
        "individuelle doit être prise en compte lors de l’examen de la demande »[[CCE-84888, p.5 ; CCE-117951, p.4 ; "
        "CCE-146669, p.4 ; CCE-246745, p.5 ; CCE-253811, pp.3-4]]. Les travaux préparatoires précisent aussi que "
        "« l’accessibilité effective d’une infrastructure et la possibilité matérielle de recevoir un traitement et des "
        "médicaments sont également prises en compte »[[DOCPARL-51-2478, p.35]].",
        "La notion de traitement adéquat implique donc qu’un traitement approprié à la maladie existe dans le pays "
        "d’origine du demandeur et, si c’est le cas, qu’il lui soit suffisamment accessible au regard de sa situation "
        "individuelle. Il convient en effet de ne pas confondre disponibilité et accessibilité : un traitement peut exister "
        "dans le pays d’origine sans être pour autant accessible au demandeur[[CCE-162147, p.3]]. Nous examinerons donc la "
        "disponibilité des soins appropriés {en_pays} (a.), puis leur accessibilité d’un point de vue structurel (b.) et au "
        "regard de la situation individuelle de {demandeur}[ et de {sa} famille] (c.)."]),
    ("9ter", "a. La disponibilité des soins appropriés", "Disponibilité effective des soins", True, [
        A_VERIFIER + "Le Conseil du contentieux des étrangers a jugé que « la simple présence d’infrastructures "
        "hospitalières ou de médecins spécialistes sur le sol [du pays d’origine] ne renseigne pas, en soi, sur la "
        "disponibilité de tous les examens ou analyses qui sont généralement pratiqués en Belgique »[[CCE-82194, p.5]]. "
        "Sa jurisprudence ultérieure a confirmé que les soins appropriés doivent être « effectivement disponibles » dans "
        "le pays d’origine du demandeur[[CCE-158676, p.4]]."]),
    ("9ter", "b. L’accessibilité des soins d’un point de vue structurel", "Accessibilité financière des soins", True, [
        A_VERIFIER + "La condition d’accessibilité des soins comprend notamment l’accessibilité financière des traitements "
        "appropriés disponibles[[CCE-82230, p.5]]. La seule énumération des médicaments et traitements disponibles, ou la "
        "seule démonstration de l’existence d’un système de sécurité sociale, ne permet pas de conclure à l’accessibilité "
        "des traitements[[CCE-49781, pp.4-5 ; CCE-121938, p.4]]. De même, « la mention générale de l’existence d’un "
        "système de sécurité sociale comportant, dans certains cas non précisés, des soins gratuits » ne suffit pas à "
        "démontrer l’accessibilité des soins appropriés dans le pays d’origine[[CCE-49781, pp.4-5]]."]),
    ("9ter", "c. L’accessibilité des soins au regard de la situation individuelle", "Situation individuelle du demandeur",
     True, [
        A_VERIFIER + "Conformément à la jurisprudence du Conseil du contentieux des étrangers, qui impose un examen « au "
        "cas par cas, en tenant compte de la situation individuelle du demandeur »[[CCE-84888, p.5]], il convient de "
        "montrer en quoi la situation particulière de {demandeur}[ et de {sa} famille] rend inaccessibles, financièrement, les "
        "soins appropriés éventuellement disponibles {en_pays}. [Revenus prévisibles de la famille (qualifications, "
        "salaires moyens par secteur), coût annuel du traitement et du suivi, comparaison ; préciser les sources et la "
        "fiabilité des chiffres.]"]),
]


# ---------------------------------------------------------------------------
# Fichiers de l'utilisateur (créés au premier usage dans le dossier de base)
# ---------------------------------------------------------------------------
def chemin_references(base):
    """Fichier de l'utilisateur ; les références ajoutées dans une nouvelle version du programme
    y sont complétées (sans jamais modifier ni supprimer les lignes existantes)."""
    c = os.path.join(base, REF_NOM)
    defaut = os.path.join(ICI, "references_juridiques_defaut.csv")
    if not os.path.exists(c):
        os.makedirs(base, exist_ok=True)
        shutil.copy(defaut, c)
        return c
    try:
        import csv
        with open(c, encoding="utf-8-sig", newline="") as f:
            connus = {(r.get("repere") or "").strip() for r in csv.DictReader(f, delimiter=";")}
        with open(defaut, encoding="utf-8-sig", newline="") as f:
            nouveaux = [r for r in csv.DictReader(f, delimiter=";") if r["repere"] not in connus]
        if nouveaux:
            with open(c, "rb") as f:
                fin = f.read()[-1:]
            with open(c, "a", encoding="utf-8", newline="") as f:
                if fin not in (b"\n", b""):
                    f.write("\n")
                w = csv.DictWriter(f, fieldnames=["repere", "reference_complete", "reference_courte", "url",
                                                  "consulte_le", "a_verifier"], delimiter=";", extrasaction="ignore")
                for r in nouveaux:
                    w.writerow(r)
    except Exception:
        pass
    try:
        _migrer_references(c, defaut)
    except Exception:
        pass
    return c


# Références d'origine corrigées dans une version ultérieure : (repère, ancienne référence complète,
# ancien « à vérifier »). La ligne de l'utilisateur n'est remplacée par la version corrigée que si elle
# est restée exactement identique à l'ancienne version d'origine (jamais si elle a été modifiée).
REFERENCES_CORRIGEES = [
    ("HCR-GUIDE", "HCR, Guide des procédures et critères à appliquer pour déterminer le statut des réfugiés au "
     "regard de la Convention de 1951 et du Protocole de 1967 relatifs au statut des réfugiés, 1979, réédité en "
     "2019", ""),
    ("CJUE-ABC", "C.J.U.E. (Gde Ch.), arrêt A, B et C c. Staatssecretaris van Veiligheid en Justitie, 2 décembre "
     "2014, aff. jointes C-148/13 à C-150/13", "points 69-71 à vérifier"),
    ("DSM5", "American Psychiatric Association, Diagnostic and Statistical Manual of Mental Disorders, 5e éd. "
     "(DSM-5), 2013", ""),
    ("HYNES-2003", None, "pages 5-6 à vérifier dans le PDF"),
    ("NIRAGHALLAIGH-2014", "M. Ní Raghallaigh, « The Causes of Mistrust amongst Asylum Seekers and Refugees: "
     "Insights from Research with Unaccompanied Asylum-Seeking Minors Living in the Republic of Ireland », "
     "Journal of Refugee Studies, vol. 27, n° 1, 2014, pp. 82-100", ""),
    # 1.0.3 : intitulés officiels et points vérifiés sur les textes
    ("REG2026-463", "Règlement (UE) 2026/463 du Parlement européen et du Conseil du 24 février 2026 modifiant le "
     "règlement (UE) 2024/1348 (concept de pays tiers sûr), J.O.U.E., L, 2026/463, 26 février 2026",
     "intitulé officiel à vérifier"),
    ("REG2026-464", "Règlement (UE) 2026/464 du Parlement européen et du Conseil du 24 février 2026 modifiant le "
     "règlement (UE) 2024/1348 (pays d’origine sûrs au niveau de l’Union), J.O.U.E., L, 2026/464, 26 février 2026",
     "intitulé officiel à vérifier"),
    ("CJUE-CV-2024", "C.J.U.E., arrêt CV c. Ministerstvo vnitra České republiky, 4 octobre 2024, aff. C-406/22",
     "formation de jugement et points à vérifier"),
    ("CJUE-ALACE-2025", "C.J.U.E. (Gde Ch.), arrêt Alace et Canpelli, 1er août 2025, aff. jointes C-758/24 et "
     "C-759/24", "points à vérifier"),
    ("CJUE-LH-2020", "C.J.U.E., arrêt LH c. Bevándorlási és Menekültügyi Hivatal, 19 mars 2020, aff. C-564/18",
     "points à vérifier"),
]


def _migrer_references(c, defaut):
    import csv
    with open(defaut, encoding="utf-8-sig", newline="") as f:
        neuves = {r["repere"]: r for r in csv.DictReader(f, delimiter=";")}
    with open(c, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    change = False
    for l in lignes:
        rep = (l.get("repere") or "").strip()
        for r, ancienne, verif in REFERENCES_CORRIGEES:
            if rep != r or rep not in neuves:
                continue
            if ancienne is not None and (l.get("reference_complete") or "").strip() != ancienne:
                continue
            if (l.get("a_verifier") or "").strip() != verif:
                continue
            n = neuves[rep]
            if all((l.get(k) or "") == (n.get(k) or "") for k in CHAMPS_REF):
                continue
            for k in CHAMPS_REF[1:]:
                l[k] = n.get(k) or ""
            change = True
    if change:
        tmp = c + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CHAMPS_REF, delimiter=";", extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            for l in lignes:
                w.writerow({k: (l.get(k) or "") for k in CHAMPS_REF})
        os.replace(tmp, c)


BIB_VERSION = 14  # à augmenter quand les blocs par défaut changent


def _empreinte(chemin):
    import hashlib
    import zipfile
    with zipfile.ZipFile(chemin) as z:
        root = etree.fromstring(z.read("content.xml"))
    body = root.find("office:body/office:text", NS)
    return hashlib.sha1(" ".join("".join(body.itertext()).split()).encode("utf-8")).hexdigest()


def chemin_bibliotheque(base):
    """Crée la bibliothèque au premier usage. Nouvelle version des blocs par défaut : si l'utilisatrice n'a pas
    modifié la sienne, elle est remplacée (l'ancienne est gardée en copie) ; sinon la nouvelle est posée à côté.
    Renvoie le chemin ; les messages éventuels sont dans AVIS (lus puis vidés par l'interface)."""
    c = os.path.join(base, NOM)
    marque = c + ".version"

    def marquer():
        with open(marque, "w", encoding="utf-8") as f:
            f.write("%d;%s" % (BIB_VERSION, _empreinte(c)))
    if not os.path.exists(c):
        os.makedirs(base, exist_ok=True)
        construire_defaut(c)
        marquer()
        return c
    try:
        ver, emp = open(marque, encoding="utf-8").read().strip().split(";")
        ver = int(ver)
    except Exception:
        ver, emp = 1, None
    if ver >= BIB_VERSION:
        return c
    try:
        modifiee = emp is not None and emp != _empreinte(c)
        if modifiee:
            nouv = os.path.join(base, NOM.replace(".odt", "_nouvelle_version.odt"))
            construire_defaut(nouv)
            AVIS.append("La bibliothèque de blocs a une nouvelle version (nouveaux blocs et corrections). Comme vous aviez modifié la vôtre, elle est conservée telle quelle ; la nouvelle "
                        "version est ici : %s. Recopiez-y vos modifications puis renommez-la « %s » si vous voulez "
                        "l'utiliser." % (nouv, NOM))
            with open(marque, "w", encoding="utf-8") as f:
                f.write("%d;%s" % (BIB_VERSION, _empreinte(c)))
        else:
            import datetime
            copie = os.path.join(base, NOM.replace(".odt", "_ancienne_%s.odt" % datetime.date.today().isoformat()))
            shutil.copy(c, copie)
            construire_defaut(c)
            marquer()
            AVIS.append("La bibliothèque de blocs a été mise à jour (nouveaux blocs et corrections). "
                        "L'ancienne version est gardée ici : %s." % copie)
    except Exception as e:
        AVIS.append("Mise à jour de la bibliothèque impossible : %s" % e)
    return c


AVIS = []


CHAMPS_REF = ["repere", "reference_complete", "reference_courte", "url", "consulte_le", "a_verifier"]


def lire_references(base):
    import csv
    with open(chemin_references(base), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def ajouter_reference(base, ligne):
    """Ajoute une ligne à references_juridiques.csv (guillemets gérés). Renvoie un message d'erreur ou ""."""
    import csv
    rep = (ligne.get("repere") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][\w./-]*", rep):
        return "Le repère doit être un nom court sans espace (lettres, chiffres, tirets), par ex. CCE-310000."
    if not (ligne.get("reference_complete") or "").strip():
        return "La référence complète est obligatoire."
    if any((r.get("repere") or "").strip().lower() == rep.lower() for r in lire_references(base)):
        return "Le repère %s existe déjà : choisissez-en un autre, ou corrigez la ligne existante." % rep
    c = chemin_references(base)
    with open(c, "rb") as f:
        fin = f.read()[-1:]
    with open(c, "a", encoding="utf-8", newline="") as f:
        if fin not in (b"\n", b""):
            f.write("\n")
        w = csv.DictWriter(f, fieldnames=CHAMPS_REF, delimiter=";", extrasaction="ignore", lineterminator="\n")
        w.writerow({k: (ligne.get(k) or "").strip() for k in CHAMPS_REF})
    return ""


def est_reference_d_origine(repere):
    import csv
    with open(os.path.join(ICI, "references_juridiques_defaut.csv"), encoding="utf-8-sig", newline="") as f:
        return any((r.get("repere") or "").strip().lower() == repere.strip().lower()
                   for r in csv.DictReader(f, delimiter=";"))


def _reecrire_references(base, lignes):
    import csv
    c = chemin_references(base)
    tmp = c + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS_REF, delimiter=";", extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for l in lignes:
            w.writerow({k: (l.get(k) or "") for k in CHAMPS_REF})
    os.replace(tmp, c)


def modifier_reference(base, repere, ligne):
    lignes = lire_references(base)
    n = 0
    for l in lignes:
        if (l.get("repere") or "").strip() == repere:
            for k in CHAMPS_REF[1:]:
                l[k] = (ligne.get(k) or "").strip()
            n += 1
    if not n:
        return "Repère %s introuvable." % repere
    if not (ligne.get("reference_complete") or "").strip():
        return "La référence complète est obligatoire."
    _reecrire_references(base, lignes)
    return ""


def supprimer_reference(base, repere):
    if est_reference_d_origine(repere):
        return ("%s fait partie des références fournies avec le programme : elle serait recréée au prochain "
                "démarrage. Corrigez-la plutôt (bouton « Enregistrer »)." % repere)
    lignes = lire_references(base)
    reste = [l for l in lignes if (l.get("repere") or "").strip() != repere]
    if len(reste) == len(lignes):
        return "Repère %s introuvable." % repere
    _reecrire_references(base, reste)
    return ""


def blocs_citant(chemin_biblio, repere):
    """Blocs dont un repère [[…]] commence par ce repère (ex. CCE-212381, LOI1980)."""
    cible = R.C.norm(repere)
    out = []
    for b in Bibliotheque(chemin_biblio).blocs:
        txt = " ".join("".join(el.itertext()) for el in b.elements)
        for m in re.finditer(r"\[\[(.+?)\]\]", txt):
            for part in m.group(1).split(";"):
                tete = re.split(r"[,\s]", part.strip(), 1)[0]
                if R.C.norm(tete) == cible:
                    out.append((PROCEDURES.get(b.procedure, b.procedure), b.rubrique, b.titre, m.group(0)))
    vus, uniq = set(), []
    for x in out:
        if x[:3] not in vus:
            vus.add(x[:3])
            uniq.append(x)
    return uniq


def construire_defaut(chemin):
    root = etree.fromstring(R._gabarit_contenu().encode("utf-8"))
    body = root.find("office:body/office:text", NS)

    def p(texte, style="Pcorps"):
        """Les passages entre __ __ sont soulignés."""
        e = etree.SubElement(body, T + "p")
        e.set(T + "style-name", style)
        morceaux = texte.split("__")
        e.text = morceaux[0]
        for i, m in enumerate(morceaux[1:], 1):
            if i % 2:
                sp = etree.SubElement(e, T + "span")
                sp.set(T + "style-name", "Tsoul")
                sp.text = m
            else:
                sp.tail = m

    def h(texte, niveau):
        e = etree.SubElement(body, T + "h")
        e.set(T + "style-name", "Heading_20_%d" % niveau)
        e.set(T + "outline-level", str(niveau))
        e.text = texte

    p("Bibliothèque de blocs de texte", "Ptitre")
    p("Mode d’emploi (ce paragraphe gris est ignoré par le programme) : Titre 1 = la procédure ; Titre 2 = la rubrique du "
      "plan où le bloc est inséré (le début du titre de la rubrique suffit) ; Titre 3 = le nom du bloc, suivi de « (par "
      "défaut) » s’il doit être coché d’office. Sous le Titre 3, le texte du bloc, avec ses repères de notes, par exemple "
      "[[LOI1980, art. 74/13]] (les textes de loi et arrêts sont dans references_juridiques.csv). Variables remplacées "
      "automatiquement : {demandeur}, {pays}, {en_pays} (« en Indonésie »), {Le_pays} (« L’Indonésie »), {de_pays} "
      "(« de l’Indonésie »), {le_pays} (« l’Indonésie », en cours de phrase). Accords selon la personne choisie dans l’onglet (homme, femme, plusieurs) : {le_demandeur} "
      "(le demandeur / la demanderesse / les demandeurs…), {Le_demandeur}, {du_demandeur}, {au_demandeur}, {il} {Il} "
      "(il / elle / ils / elles), {le} (le / la / les), {lui} (lui / leur), {eux} (lui / elle / eux / elles), {son} {sa} "
      "{ses} (son / sa / ses, ou leur / leurs), {est} (est / sont), {a} (a / ont), {e} (exposé{e} : exposé, exposée, "
      "exposés, exposées), {s} (éligible{s}). Pour un verbe : {craint|craignent} (singulier|pluriel) ; pour un mot "
      "masculin/féminin : {soumis/soumise|soumis/soumises}. Un paragraphe [[BLOC nom d’un autre bloc]] insère cet autre bloc. Pour ajouter un bloc : "
      "copiez un Titre 3 et son texte, modifiez-les, enregistrez (format ODT).", "Paide")
    courant = [None, None]
    for proc, rub, titre, defaut, paras in DEFAUT:
        if courant[0] != proc:
            h(PROCEDURES[proc], 1)
            courant = [proc, None]
        if courant[1] != rub:
            h(rub, 2)
            courant[1] = rub
        h(titre + (" (par défaut)" if defaut else ""), 3)
        for x in paras:
            p(x)
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
    R._ecrire_odt(chemin, fichiers)
    return chemin


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------
class Bloc:
    def __init__(self, procedure, rubrique, titre, defaut):
        self.procedure, self.rubrique, self.titre, self.defaut = procedure, rubrique, titre, defaut
        self.elements = []

    def __repr__(self):
        return "Bloc(%s / %s / %s)" % (self.procedure, self.rubrique, self.titre)


def _proc_de(titre):
    n = R.C.norm(titre)
    if "oqt" in n or "quitter" in n or "refoulement" in n and "protection" not in n:
        return "oqt"
    if "9ter" in n or "medical" in n:
        return "9ter"
    if "protection internationale" in n or "asile" in n:
        return "pi"
    return n


class Bibliotheque:
    def __init__(self, chemin):
        self.chemin = chemin
        import zipfile
        with zipfile.ZipFile(chemin) as z:
            self.root = etree.fromstring(z.read("content.xml"))
        auto = self.root.find("office:automatic-styles", NS)
        self.styles_auto = {s.get("{%s}name" % NS["style"]): s for s in (auto if auto is not None else [])}
        self.blocs = []
        body = self.root.find("office:body/office:text", NS)
        proc = rub = None
        bloc = None
        for el in body:
            if el.tag == T + "h":
                niv = int(el.get(T + "outline-level", "1") or 1)
                titre = " ".join("".join(el.itertext()).split())
                if niv == 1:
                    proc, rub, bloc = _proc_de(titre), None, None
                elif niv == 2:
                    rub, bloc = titre, None
                else:
                    defaut = bool(re.search(r"\(par d[ée]faut\)\s*$", titre, re.I))
                    titre = re.sub(r"\s*\(par d[ée]faut\)\s*$", "", titre, flags=re.I)
                    bloc = Bloc(proc, rub or "", titre, defaut)
                    self.blocs.append(bloc)
            elif bloc is not None and el.tag in (T + "p", T + "list", "{%s}table" % NS["table"]):
                if el.get(T + "style-name") == "Paide":
                    continue
                if el.tag == T + "p" and not "".join(el.itertext()).strip() and len(el) == 0:
                    continue
                bloc.elements.append(el)

    def de_procedure(self, procedure):
        return [b for b in self.blocs if b.procedure == procedure]

    def trouver(self, nom):
        n = R.C.norm(nom)
        for b in self.blocs:
            if R.C.norm(b.titre) == n:
                return b
        c = [b for b in self.blocs if R.C.norm(b.titre).startswith(n)]
        return c[0] if len(c) == 1 else None

    # --- copie des éléments d'un bloc dans un autre document --------------------------------------
    def copier(self, bloc, cible_root, variables, deja=None, profondeur=0):
        """Copies des paragraphes du bloc, prêtes à insérer dans cible_root (styles recopiés, variables
        remplacées, blocs inclus développés)."""
        deja = deja if deja is not None else {}
        out = []
        for el in bloc.elements:
            texte = "".join(el.itertext()).strip()
            m = re.fullmatch(r"\[\[\s*BLOC\s+(.+?)\s*\]\]", texte)
            if m and profondeur < 5:
                inc = self.trouver(m.group(1))
                if inc is not None and inc is not bloc:
                    deja_blocs = deja.setdefault("__blocs__", set())
                    if inc.titre in deja_blocs:  # déjà développé plus haut dans le même document : simple renvoi
                        c = copy.deepcopy(el)
                        for x in list(c):
                            c.remove(x)
                        c.text = "(Voir supra : « %s ».)" % inc.titre
                        self._styles(c, cible_root, deja)
                        out += [c, etree.Element(T + "p")]
                        continue
                    deja_blocs.add(inc.titre)
                    out += self.copier(inc, cible_root, variables, deja, profondeur + 1)
                    continue
            c = copy.deepcopy(el)
            self._styles(c, cible_root, deja)
            _variables(c, variables)
            out.append(c)
            if c.tag == T + "p":  # ligne vide entre les paragraphes, comme dans les dossiers
                vide = etree.Element(T + "p")
                if c.get(T + "style-name"):
                    vide.set(T + "style-name", c.get(T + "style-name"))
                out.append(vide)
        return out

    def _styles(self, el, cible_root, deja):
        auto = cible_root.find("office:automatic-styles", NS)
        if auto is None:
            auto = etree.SubElement(cible_root, "{%s}automatic-styles" % NS["office"])
            cible_root.insert(0, auto)
        for x in el.iter():
            for attr in (T + "style-name",):
                nom = x.get(attr)
                if nom and nom in self.styles_auto:
                    nouveau = deja.get(nom)
                    if nouveau is None:
                        nouveau = "Bib_" + nom
                        st = copy.deepcopy(self.styles_auto[nom])
                        st.set("{%s}name" % NS["style"], nouveau)
                        auto.append(st)
                        deja[nom] = nouveau
                    x.set(attr, nouveau)


def _variables(el, variables):
    def rempl(s):
        if not s or "{" not in s:
            return s
        return R.remplacer(s, variables)
    for x in el.iter():
        x.text = rempl(x.text)
        x.tail = rempl(x.tail) if x is not el else x.tail


def variables_pays(de_pays, nom_pays, demandeur, personne="m"):
    v = R.formes_pays(de_pays, nom_pays)
    v.update(R.formes_personne(personne))
    v.update({"pays": nom_pays, "demandeur": demandeur or "[nom du demandeur]"})
    return v


def developper_blocs(root, biblio, variables, log=print):
    """Remplace dans le document chaque paragraphe [[BLOC nom]] par la dernière version du bloc."""
    body = root.find("office:body/office:text", NS)
    n, manquants = 0, []
    deja = {}
    for p in list(body.iter(T + "p")):
        texte = "".join(p.itertext()).strip()
        m = re.fullmatch(r"\[\[\s*BLOC\s+(.+?)\s*\]\]", texte)
        if not m:
            continue
        b = biblio.trouver(m.group(1))
        if b is None:
            manquants.append(m.group(1))
            continue
        parent = p.getparent()
        pos = parent.index(p)
        parent.remove(p)
        for i, c in enumerate(biblio.copier(b, root, variables, deja)):
            parent.insert(pos + i, c)
        n += 1
    return n, manquants
