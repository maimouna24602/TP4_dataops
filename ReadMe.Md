# TP4 DataOps - Web & PDF Scraping Pipeline

Pipeline automatisé de collecte et nettoyage de données publiques mauritaniennes (Budget, Football, INPC).

##  Description

Ce projet implémente un pipeline DataOps reproductible qui :
-  Collecte des données HTML depuis des sites web publics
-  Extrait des tableaux depuis des fichiers PDF
-  Nettoie et structure les données avec pandas
- S'exécute dans un container Docker
-  Génère des métriques et rapports d'exécution

##  Sources de données

| Source | Type | URL |
|--------|------|-----|
| **Budget** | HTML | https://services.tresor.mr/budget |
| **Football** | HTML | https://www.tntsports.co.uk/football/mauritanian-league/calendar-results.shtml |
| **INPC** | PDF | https://ansade.mr/fr/note-mensuelle-de-lindice-national-des-prix-a-la-consommation-inpc-decembre-2025/ |

##  Architecture

```
TP4_DataOps/
├── app/
│   ├── main.py                 # Pipeline principal (orchestration)
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── budget.py          # Scraping Budget (HTML)
│   │   ├── football.py        # Scraping Football (HTML)
│   │   └── inpc.py            # Scraping INPC (PDF)
├── shared_out/                 # Dossier de sortie (monté depuis l'hôte)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

##  Fichiers de sortie

Le pipeline génère **5 fichiers** dans `./shared_out/` :

1. **`budget_execution.csv`** - Données du budget mauritanien
2. **`football_results.csv`** - Résultats du championnat
3. **`inpc_table2.csv`** - Tableau 2 de l'indice des prix (INPC)
4. **`kpi.json`** - Métriques de collecte (statuts, lignes, erreurs)
5. **`run_report.md`** - Rapport d'exécution lisible

##  Installation et exécution

### Prérequis
- Docker
- Docker Compose
- Git

###  Cloner le repository

```bash
git clone https://github.com/VOTRE_USERNAME/TP4_DataOps.git
cd TP4_DataOps
```

### Configuration (optionnel)

Copiez le fichier d'exemple et modifiez les paramètres si nécessaire :

```bash
cp .env.example .env
```

Variables disponibles dans `.env` :
```env
BUDGET_URL=https://services.tresor.mr/budget
FOOTBALL_URL=https://www.tntsports.co.uk/football/mauritanian-league/calendar-results.shtml
INPC_PAGE_URL=https://ansade.mr/fr/note-mensuelle-de-lindice-national-des-prix-a-la-consommation-inpc-decembre-2025/
HTTP_TIMEOUT_SECONDS=20
OUTPUT_DIR=/out
USER_AGENT=Mozilla/5.0 (TP4 DataOps Pipeline)
```

###  Lancer le pipeline

```bash
docker-compose up --build
```

Ou en mode détaché :
```bash
docker-compose up --build -d
```

### Vérifier les résultats

```bash
ls -lh shared_out/
cat shared_out/kpi.json
cat shared_out/run_report.md
```

## Schémas des données

### budget_execution.csv
| Colonne | Type | Description |
|---------|------|-------------|
| `date` | date | Date de l'indicateur |
| `indicateur` | string | Nom de l'indicateur budgétaire |
| `valeur` | float | Valeur numérique |
| `unite` | string | Unité de mesure |
| `scraped_at` | datetime | Horodatage du scraping |

### football_results.csv
| Colonne | Type | Description |
|---------|------|-------------|
| `match_date` | date | Date du match |
| `home_team` | string | Équipe à domicile |
| `away_team` | string | Équipe extérieure |
| `home_score` | int | Score domicile |
| `away_score` | int | Score extérieur |
| `status` | string | Statut (Terminé/À venir) |
| `scraped_at` | datetime | Horodatage du scraping |

### inpc_table2.csv
| Colonne | Type | Description |
|---------|------|-------------|
| `categorie` | string | Catégorie de produits |
| `poids` | float | Poids dans l'indice |
| `variation_mensuelle` | float | Variation mensuelle (%) |
| `variation_annuelle` | float | Variation annuelle (%) |
| `scraped_at` | datetime | Horodatage du scraping |

##  Idempotence

**Stratégie** : Écrasement propre des fichiers à chaque exécution.

- Les fichiers CSV sont recréés complètement
- Pas de duplication de données
- Le timestamp `scraped_at` permet de tracer l'exécution
- Alternative possible : versionnement par timestamp (ex: `budget_2026-01-19_14-30.csv`)

## 🛠️ Technologies utilisées

- **Python 3.10** - Langage principal
- **requests** - Requêtes HTTP
- **beautifulsoup4** - Parsing HTML
- **pandas** - Manipulation de données
- **camelot-py** - Extraction de tableaux PDF
- **Docker & Docker Compose** - Conteneurisation

## Règles de nettoyage

### Budget
- Conversion des montants en numériques
- Suppression des espaces et caractères spéciaux
- Normalisation des unités (Millions MRU, etc.)
- Gestion des valeurs manquantes

### Football
- Normalisation des dates (format ISO)
- Extraction propre des scores
- Gestion des matchs non joués (scores = NULL)
- Suppression des doublons

### INPC
- Extraction du Tableau 2 uniquement
- Suppression des entêtes répétés
- Conversion des pourcentages en float
- Normalisation des noms de colonnes

##  Limitations connues

1. **Stabilité des sources** : Les sites web peuvent changer de structure
2. **Format PDF** : L'extraction dépend de la mise en page du PDF
3. **Réseau** : Nécessite une connexion internet stable
4. **Timeout** : Certaines sources peuvent être lentes (configurable via `HTTP_TIMEOUT_SECONDS`)
5. **Langue** : Extraction optimisée pour le français
6. **Java** : `camelot-py` nécessite Java (inclus dans l'image Docker)

##  Logs et debugging

Les logs sont affichés sur la sortie standard :

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Logs d'un run précédent
docker-compose logs
```

Format des logs :
```
2026-01-19 14:30:00 - INFO - TP4 DataOps Pipeline - Starting
2026-01-19 14:30:01 - INFO - Budget: Extracted 45 raw rows
2026-01-19 14:30:02 - ERROR - Football scraping failed: Connection timeout
```

##  Tests manuels

### Test 1 : Build de l'image
```bash
docker build -t tp4-dataops .
```

### Test 2 : Exécution sans Compose
```bash
docker run -v $(pwd)/shared_out:/out tp4-dataops
```

### Test 3 : Vérification des fichiers
```bash
wc -l shared_out/*.csv
python -m json.tool shared_out/kpi.json
```

### Test 4 : Validation des CSV
```python
import pandas as pd

df_budget = pd.read_csv('shared_out/budget_execution.csv')
print(df_budget.info())
print(df_budget.head())
```


##  Liens utiles

- [Documentation camelot-py](https://camelot-py.readthedocs.io/)
- [Documentation pandas](https://pandas.pydata.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
