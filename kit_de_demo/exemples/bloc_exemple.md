# Ajouter un bloc à la bibliothèque (exemple)

Onglet Rédaction → « Modifier la bibliothèque… » ouvre `bibliotheque_blocs.odt` (dans le dossier de base).

Organisation du document :
- **Titre 1** = la procédure (« Non-délivrance d’OQT (non-refoulement) », « Protection internationale », « 9ter ») ;
- **Titre 2** = la rubrique du plan où le bloc sera placé (ex. « IV. La demande ») ;
- **Titre 3** = le nom du bloc ; ajoutez « (par défaut) » à la fin pour qu’il soit coché d’office.

Exemple de bloc à copier sous une rubrique (un Titre 3, puis un paragraphe normal) :

> **Titre 3 :** Scolarité des enfants (exemple)
>
> Les enfants {du_demandeur} sont scolarisés en Belgique depuis [année][[PIECE 01_Attestation_scolarite_FICTIVE]]. Un éloignement interromprait leur scolarité en cours d’année, ce qui doit être pris en compte au titre de l’intérêt supérieur de l’enfant[[LOI1980, art. 74/13]][[CIDE, art. 3]].

Ce que le programme fait du bloc :
- `{du_demandeur}` devient « du demandeur », « de la demanderesse », « des demandeurs »… selon « Qui demande ? » ;
- `[[…]]` devient une note de bas de page à la génération ;
- `[année]` (crochets simples) est un passage à compléter à la main.

Enregistrez le document en gardant le format .odt (Word sait aussi l’enregistrer en .odt). Le nouveau bloc apparaît dans « Choisir les blocs… », ou s’insère n’importe où avec `[[BLOC Scolarité des enfants (exemple)]]` seul sur une ligne.
