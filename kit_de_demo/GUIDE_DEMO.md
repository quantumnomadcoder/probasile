# Présenter Probasile : guide de démonstration

Ce guide aide à montrer Probasile en 25 minutes (ou en 5 minutes, version courte à la fin) à des avocat·es, juristes, permanences ou collectifs. Il dit quoi préparer, quoi cliquer, quoi dire, et comment répondre aux questions. Il s'appuie sur les fichiers de ce kit : **tout est fictif**.

À projeter pendant la démo, ou à envoyer ensuite : `Presentation_Probasile.pptx` (mêmes étapes, avec captures et notes de l'orateur·rice). Pour l'installation : `Installation_Probasile.pptx`.

---

## Le message à faire passer (à dire en ouverture)

1. **Le problème** : les sources qui gagnent un dossier existent (observations des comités de l'ONU, ratifications, rapports d'ONG, jurisprudence), mais elles sont éparpillées dans des bases de données difficiles à utiliser, et beaucoup d'intervenant·es ne savent même pas qu'elles existent.
2. **Ce que fait Probasile** : il les rassemble pour un pays, les range avec leur référence complète, puis aide à rédiger : plan type, passages juridiques sourcés, notes de bas de page et annexes automatiques.
3. **Pour qui** : avocat·es, juristes, permanences, collectifs, proches qui montent un dossier. Gratuit, libre, et tout reste sur votre ordinateur.

---

## Avant la démo

**Installer Probasile** (voir `Installation_Probasile.pptx`) :
- Windows : double-clic sur `installer_windows.bat` (Python est installé s'il manque) ;
- macOS : Python 3 de python.org, puis double-clic sur `Installer Probasile (Mac).command` ;
- **Linux : la méthode sûre est le terminal.** Le double-clic sur `Installer Probasile (Linux).sh` échoue souvent (le zip téléchargé perd le droit d'exécuter les scripts, ou le fichier s'ouvre dans l'éditeur de texte). Ouvrez le dossier du programme, clic droit → *Ouvrir dans un terminal*, puis :
  ```
  sh installer_mac_linux.sh
  ```
  S'il manque des éléments de Python (`python3-venv`, `python3-tk`), répondez **O** : le script les installe (mot de passe demandé). Pour lancer sans raccourci : `sh lancer_mac_linux.command`.

**Matériel**
- Word ou LibreOffice installé (il en faut un pour convertir le témoignage Word en PDF).
- Une connexion Internet seulement pour la petite collecte en direct (étape 2). Tout le reste fonctionne hors ligne avec le kit.

**Le dossier de démonstration** (prêt, rien à collecter la veille) :
- copiez `kit_de_demo` dans un dossier de travail : la génération écrit ses fichiers dans `Redaction`, l'original reste propre ;
- lancez Probasile, **« Choisir… »** → `dossier_demo` comme « Dossier de base » ;
- **Pays** : Indonésie (IDN) ; **Dans une phrase** : « de l'Indonésie » ;
- faites une génération d'essai (étape 6) et comparez avec `resultats_attendus/` : **17 notes, 4 annexes, aucun problème relevé**.

**Si vous voulez montrer une vraie collecte complète**, préparez-la la veille dans un **autre** dossier de base (une collecte prend de quelques minutes à une heure).

**Vérifier, juste avant**
- Aucun dossier client ouvert ni visible à l'écran (explorateur de fichiers, courriels, notifications).
- `Texte_demo.docx` ouvert en arrière-plan dans Word ou LibreOffice.
- Agrandir la fenêtre de Probasile ; zoom du projecteur lisible.

---

## Déroulé en 25 minutes

### 0. Le problème (2 min)
Montrez, sans Probasile, où se trouvent les sources : le site des organes de traités du HCDH, la Collection des traités de l'ONU, ReliefWeb, HUDOC. Dites : « Chacun a sa logique, ses codes, ses pages illisibles. Trouver, télécharger, citer correctement, numéroter les annexes : des heures par dossier. »
*Diapositives 2 et 3.*

### 1. Choisir le pays et le dossier (1 min)
En haut de la fenêtre : **Pays** (tapez les premières lettres), **Dans une phrase** (« de l'Indonésie »), **Dossier de base** (`dossier_demo`).
À dire : « Tout ce que le programme trouve sera rangé ici, dans des dossiers numérotés, avec un tableau qui décrit chaque document. »

### 2. Collecte ONU, en direct (3 min)
Onglet **ONU** (capture `captures/01_onglet_ONU.png`) :
- montrez les comités (CCPR, CAT…) et les cadres numérotés ; chaque onglet a son bouton « Mode d'emploi de l'onglet » ;
- cochez seulement le cadre **4. Ratifications** et cliquez sur **Lancer la collecte** : quelques dizaines de secondes ;
- ouvrez `02_Ratifications/ratifications.html` : traités ratifiés ou non, dates, **réserves et déclarations en français**.

À dire : « Le pays n'a jamais accepté les plaintes individuelles devant tel comité ? C'est un argument, et il est sourcé. »
Sans Internet : ouvrez `02_Ratifications/ratifications.csv` du kit.

### 3. Les autres sources (3 min)
Parcourez rapidement, sans lancer :
- **Rapports ONU, ONG, États (ReliefWeb)** : préréglages « Droits humains (PI, OQT) » et « Santé (9ter) » ;
- **Presse et sources nationales (veille)** : collez les recherches de `exemples/veille_presse_exemple.txt` ; seules des fiches sont créées (titre, source, date, lien) ;
- **Jurisprudence** : C.J.U.E. par acte et par article (règlements du pacte, pays sûrs…), Cour constitutionnelle ; cadre 4, collez `exemples/references_a_importer_exemple.txt` ; cadre 6 « Vos sources » : le fichier `dossier_demo/sources_jurisprudence.csv` du kit ajoute déjà Eurodac, Refworld, EDAL et la directive traite (« Ajouter des sources… » montre sa forme) ;
- **Importer** : choisissez `exemples/Rapport_ONG_FICTIF_2025.pdf` ; les lettres des rapporteurs spéciaux et les arrêts sont reconnus automatiquement, les autres documents se complètent dans « Gérer… ».

### 4. Le résultat rangé (2 min)
Cliquez sur **Ouvrir le dossier** : dossiers numérotés (`00_Pieces_du_dossier`, `01_ONU_organes_de_traites`, `02_Ratifications`…) et `sources.csv`.
À dire : « Chaque document a sa référence complète et sa date de consultation. Rien n'est jamais téléchargé deux fois. »

### 5. Rédaction : le plan type (5 min)
Onglet **Rédaction**, cadre 1 (`captures/06_onglet_redaction.png`) :
- procédure **Non-délivrance d'OQT** (ou Protection internationale), nom « Madame A. Exemple », **Qui demande ?** « une femme » ;
- **Choisir les blocs…** (`captures/07_choisir_les_blocs.png`) : passages juridiques types (pays d'origine sûr, procédure accélérée, seuil de 20 %…) ;
- case **« Paragraphes calculés »** : ratifications, plaintes, rapports en retard, écrits à partir du dossier du kit ;
- format **Word (.docx)**, puis **Créer le plan et l'ouvrir**.

Dans Word, montrez :
- les titres de la procédure et la table des matières (clic droit puis « Mettre à jour les champs ») ;
- en gris, les indications de rédaction ; en bleu, les repères des sources collectées sous chaque titre ;
- un bloc déjà rédigé, **accordé au féminin** (« la demanderesse… elle »), avec ses repères [[…]].

Résultats de référence : `resultats_attendus/Plan_oqt_exemple.docx` et `Plan_pi_exemple.docx`.
À dire : « Les passages sont écrits pour être favorables aux personnes, et chaque affirmation est sourcée. Vous les adaptez, vous ne partez pas de zéro. »

### 6. Les notes et les annexes (5 min)
Montrez `Redaction/Texte_demo.docx` (`captures/13_texte_avant_reperes.png`). Il contient :
- quatre pièces : `[[PIECE 01_Attestation_scolarite_FICTIVE]]`, `[[PIECE 02_Temoignage_FICTIF]]`, `[[PIECE 04_Certificat_medical_FICTIF]]`, `[[PIECE 03_Carte_identite_SPECIMEN]]` ;
- des ratifications `[[IV-4]]`, `[[IV-5]]`, des documents ONU `[[CCPR/C/IDN/CO/2]]` (cité deux fois), `[[CAT/C/IDN/CO/2]]`, deux courriers de suivi dans une même note `[[INT/CCPR/FUL/IDN/21848 ; INT/CCPR/FUL/IDN/27205]]` ;
- des textes de référence `[[LOI1980, art. 74/13]]` (cité deux fois), `[[CEDH, art. 3]]`, `[[CJUE-ALACE-2025, point 97]]` ;
- un bloc `[[BLOC Intérêt supérieur de l'enfant (article 74/13)]]`, une note écrite à la main `[[= …]]` et `[[INDEX DES ANNEXES]]`.

Puis, cadre 3 : **Choisir le texte (.docx ou .odt)…** → `Texte_demo.docx`, **Générer** (`captures/12_resultat_de_la_generation.png`). Ouvrez :
- `Texte_demo_notes.docx` (`captures/14_texte_apres_notes.png`) : de vraies notes de bas de page Word ; référence complète à la première citation, *Ibid.* à la note 8, *op.cit.* aux notes 14 et 16, « voir l'annexe n° 1 au présent courrier », le bloc inséré et accordé, l'index des annexes ;
- `Texte_demo_annexes.pdf` (`captures/15_pdf_des_annexes.png`) : les 4 annexes dans l'ordre, une page « Annexe n° X » devant chacune, chaque page tamponnée ;
- `Texte_demo_rapport.txt` : les annexes et les problèmes éventuels.

À dire : « Votre texte d'origine n'est jamais modifié. Vous corrigez, vous régénérez : les numéros d'annexes suivent. »
Pour montrer le rapport en situation d'erreur : tapez `[[CCPR/C/IDN/CO/9]]` dans le texte et régénérez : « SOURCE INTROUVABLE ».

### 7. Les pièces du dossier (2 min)
Montrez la règle avec le kit : la carte d'identité (fichier `03_…`) est citée **en dernier**, elle devient donc l'**annexe 4**, après le certificat médical (fichier `04_…`). « Une pièce n'est annexée que si elle est citée. Déposer le fichier ne suffit pas : c'est la citation qui fait l'annexe, et l'ordre des citations fait la numérotation. »

Puis montrez comment décrire une pièce : la carte n'a pas de description (son titre est « Carte identite SPECIMEN »). Cadre 2, **Gérer…** (`captures/08_gerer_les_reperes.png`), sélectionnez-la, **Modifier…**, remplissez auteur, titre, date ; régénérez : la note et l'index changent.
Pour une nouvelle pièce : **Ajouter une pièce…** (`captures/09_ajouter_une_piece.png`), le repère `[[PIECE …]]` est copié, collez-le dans le texte.

### 8. La veille législative et le bulletin (2 min)
Cadre 1 : **Vérifier la législation…** (`captures/11_verifier_la_legislation.png`), puis **Lire le bulletin** (ou **Vérifier en ligne**).
À dire : « La loi change souvent. Probasile signale les articles modifiés et les blocs à relire. Le bulletin, en français, néerlandais et allemand, explique les réformes en langage courant et vit sur GitHub : tout le monde peut proposer une information. »

### 9. Vie privée et logiciel libre (1 min)
- Tout tourne sur votre ordinateur : pas de compte, pas de cloud, pas de télémétrie. Les dossiers ne quittent jamais la machine.
- Le programme ne contacte que les sites publics qu'on lui demande de lire, plus GitHub pour le bulletin.
- Licence GPL-3.0 : gratuit, code ouvert, modifiable.

### 10. Conclusion et appel (1 min)
« Le projet est porté par une seule personne. On cherche des testeurs Windows et Mac, des juristes pour relire les blocs et le bulletin, des traductions, du code. » Montrez la page GitHub.

---

## Version courte (5 minutes)

1. Le problème en une phrase (sources éparpillées et méconnues).
2. Ouvrir le dossier du kit : dossiers rangés, `sources.csv`, `02_Ratifications`.
3. Créer un plan Word avec un bloc accordé au féminin.
4. Générer `Texte_demo.docx` : notes, *Ibid.*, annexes et PDF.
5. Vie privée, gratuit, libre, appel à l'aide.

---

## Questions fréquentes (et réponses)

**« Ça marche avec Word ? »** Oui : plans en .docx, texte Word avec de vraies notes Word. LibreOffice aussi (`Texte_demo.odt` est la version LibreOffice du texte de démo).

**« Il faut savoir programmer ? »** Non : boutons et cases à cocher. Sous Windows, l'installateur installe même Python s'il manque. Sous Linux, une seule commande : `sh installer_mac_linux.sh`.

**« Les données de mes clients partent où ? »** Nulle part : tout reste sur votre ordinateur.

**« Les blocs juridiques sont-ils fiables ? »** Ils sont sourcés et datés, mais restent des propositions : vous relisez et adaptez. La veille législative signale les articles modifiés ; les points incertains sont signalés « à vérifier » dans les textes de référence.

**« Et pour d'autres pays que la Belgique ? »** La collecte (ONU, ONG, jurisprudence européenne) sert partout ; les plans et les blocs sont faits pour le droit belge, mais modifiables (`exemples/bloc_exemple.md` montre comment ajouter un bloc).

**« Et en néerlandais ou en allemand ? »** La documentation et le bulletin existent dans les trois langues ; le programme et les blocs sont en français pour l'instant.

**« Combien de temps prend une collecte ? »** De quelques minutes à une heure selon les cases cochées. On peut l'arrêter à tout moment : ce qui est téléchargé est gardé. Ensuite, « Nouveautés seulement » ne cherche que ce qui est paru depuis.

---

## Pièges à éviter

- **Ne jamais montrer un vrai dossier** : noms, numéros nationaux, adresses. Restez dans `dossier_demo` ; ne remplacez pas les pièces fictives par de vraies pièces, même anonymisées.
- **Ne pas lancer une collecte complète en direct** : seulement le cadre 4 de l'onglet ONU.
- **Vérifier la connexion Internet** de la salle avant (certains réseaux bloquent des sites).
- **Si un site refuse le programme** (ReliefWeb, HUDOC) : c'est prévu. Montrez le bouton qui ouvre la recherche dans le navigateur, puis l'onglet Importer.
- **Sous Linux, ne pas perdre de temps avec le double-clic** : terminal, `sh installer_mac_linux.sh`.
- **Tester la génération la veille** et comparer avec `resultats_attendus/`.

---

## Aide-mémoire : annexer correctement

| Je veux… | Je fais… |
|---|---|
| Annexer un document collecté (observations finales, rapport) | Je le cite avec son repère ; il est annexé automatiquement (case « Annexer toutes les sources citées »). |
| Annexer une pièce personnelle (attestation, témoignage, certificat) | « Ajouter une pièce… » (ou je dépose le fichier dans 00_Pieces_du_dossier), puis je cite `[[PIECE nom]]` dans le texte. |
| Donner une belle référence à une pièce | Je remplis auteur, titre et date en l'ajoutant, ou plus tard avec « Gérer… » puis « Modifier… ». |
| Ne pas annexer une source citée | `[[repère +sansannexe]]`, ou « Ne pas annexer » dans « Gérer… ». |
| Annexer une source qui ne le serait pas | `[[repère +annexe]]`, ou « Annexer » dans « Gérer… ». |
| Placer l'index des annexes | `[[INDEX DES ANNEXES]]` seul sur une ligne ; sinon il est ajouté à la fin. |

Les annexes sont numérotées dans l'ordre de leur **première citation**. Une source citée plusieurs fois garde son numéro. Une pièce présente dans le dossier mais jamais citée **n'est pas annexée**. Les photos (JPEG, PNG) et les fichiers Word sont convertis en PDF automatiquement ; si une conversion échoue, le rapport le dit : enregistrez la pièce en PDF.

---

## Fichiers du kit cités dans ce guide

| Étape | Fichiers |
|---|---|
| Installation | `Installation_Probasile.pptx`, `captures/17_…`, `19_…`, `20_…` |
| 1–4 Collecte | `dossier_demo/`, `exemples/veille_presse_exemple.txt`, `exemples/references_a_importer_exemple.txt`, `dossier_demo/sources_jurisprudence.csv`, `exemples/Rapport_ONG_FICTIF_2025.pdf` |
| 5 Plan type | `resultats_attendus/Plan_oqt_exemple.docx`, `Plan_pi_exemple.docx`, `exemples/bloc_exemple.md` |
| 6 Notes et annexes | `Redaction/Texte_demo.docx` (`.odt`), `resultats_attendus/Texte_demo_notes.docx` (`.odt`), `Texte_demo_annexes.pdf`, `Texte_demo_rapport.txt` |
| 7 Pièces | `00_Pieces_du_dossier/` (4 pièces fictives et `pieces.csv`) |
| Tout | `Presentation_Probasile.pptx`, `captures/` |
