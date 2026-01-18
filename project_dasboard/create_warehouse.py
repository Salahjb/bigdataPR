import json
import pandas as pd
import random
import re

# 1. Chargement du JSON brut (Source)
try:
    with open('../scraping_processing/final_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
except FileNotFoundError:
    print("Erreur: Place final_data.json dans le dossier parent ou modifie le chemin.")
    exit()

df = pd.DataFrame(raw_data)

# 2. Nettoyage & Dimensions (Transformation)

# D_TEMPS (Extraction de l'année)
def clean_year(d):
    match = re.search(r'20\d{2}', str(d))
    return int(match.group(0)) if match else 2024
df['Annee'] = df['date_pub'].apply(clean_year)

# D_ARTICLE (Simulation Score Impact & Quartile pour le BI)
quartiles = ['Q1', 'Q2', 'Q3', 'Q4']
# On donne plus de poids à Q1 et Q2
df['Quartile'] = [random.choices(quartiles, weights=[0.4, 0.3, 0.2, 0.1])[0] for _ in range(len(df))]
df['Impact_Score'] = [round(random.uniform(0.5, 10.0), 2) for _ in range(len(df))]
df['Citations'] = df['Impact_Score'].apply(lambda x: int(x * random.randint(1, 20)))

# D_LABORATOIRE / PAYS (Simulation depuis les affiliations manquantes)
countries = ['USA', 'China', 'France', 'Germany', 'India', 'UK', 'Canada', 'Brazil']
df['Pays'] = [random.choice(countries) for _ in range(len(df))]

# D_JOURNAL
df['Journal'] = df['source']

# 3. Création de la Table de Faits (F_Publications)
# On garde les colonnes nécessaires pour le Cube OLAP
f_publications = df[['title', 'authors', 'Annee', 'Pays', 'Journal', 'Quartile', 'Citations', 'Impact_Score', 'abstract_']]

# Sauvegarde dans results
f_publications.to_csv('results/F_Publications.csv', index=False)
print("✅ Datawarehouse généré : results/F_Publications.csv")
