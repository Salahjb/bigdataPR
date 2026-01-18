import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx
import plotly.graph_objects as go
from collections import Counter

# --- CONFIGURATION DU SID ---
st.set_page_config(page_title="SID Scientifique", layout="wide", page_icon="🔬")

# --- CHARGEMENT DU DATAWAREHOUSE ---
@st.cache_data
def load_data():
    df = pd.read_csv("results/F_Publications.csv")
    
    try:
        topics_dist = pd.read_csv("results/topics_dist.csv")
    except FileNotFoundError:
        topics_dist = pd.DataFrame(columns=["Topic", "Count"])
        
    return df, topics_dist

df, topics_dist = load_data()

def get_topic(title):
    t = str(title).lower()
    if 'ai' in t or 'learning' in t: return 'AI & Blockchain'
    if 'security' in t or 'privacy' in t: return 'Security & Privacy'
    if 'iot' in t or 'edge' in t: return 'IoT & Edge'
    if 'health' in t: return 'Healthcare'
    if 'supply' in t: return 'Supply Chain'
    if 'finance' in t or 'defi' in t: return 'DeFi & Finance'
    return 'General Blockchain'

if 'Topic' not in df.columns:
    df['Topic'] = df['title'].apply(get_topic)


# --- SIDEBAR (FONCTIONNALITÉS OLAP) ---
st.sidebar.title("🎛️ Cube OLAP")
st.sidebar.markdown("Use filters to **Slice & Dice** data.")

# Filtres (Dimensions)
selected_years = st.sidebar.slider("Dimension Temps (Année)", 
                                   int(df['Annee'].min()), int(df['Annee'].max()), (2020, 2025))
selected_quartiles = st.sidebar.multiselect("Dimension Qualité (Quartile)", 
                                            options=['Q1', 'Q2', 'Q3', 'Q4'], default=['Q1', 'Q2', 'Q3', 'Q4'])
selected_countries = st.sidebar.multiselect("Dimension Géographique (Pays)", 
                                            options=df['Pays'].unique(), default=df['Pays'].unique())

# Application des filtres (Slice operation)
filtered_df = df[
    (df['Annee'] >= selected_years[0]) & 
    (df['Annee'] <= selected_years[1]) &
    (df['Quartile'].isin(selected_quartiles)) &
    (df['Pays'].isin(selected_countries))
]

# --- KPI GLOBAUX ---
st.title("📊 SID : Analyse de la Production Scientifique")
st.markdown("Tableau de bord décisionnel pour l'analyse bibliométrique.")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Publications (Fait)", len(filtered_df))
kpi2.metric("Total Citations", filtered_df['Citations'].sum())
kpi3.metric("Impact Moyen", round(filtered_df['Impact_Score'].mean(), 2))
kpi4.metric("Pays Actifs", filtered_df['Pays'].nunique())

st.markdown("---")

# --- ONGLETS (VUES BI DEMANDÉES) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 1. Tendances (Temps)", 
    "🏆 2. Qualité (Quartiles)", 
    "🌍 3. Performance (Géo/Labs)", 
    "🕸️ 4. Thématique & Réseau"
])

# === ONGLET 1 : TENDANCES TEMPORELLES ===
with tab1:
    st.subheader("Analyse Temporelle (Dimension Temps)")
    
    # Histogramme Évolution
    pubs_per_year = filtered_df.groupby('Annee').size().reset_index(name='Publications')
    fig_hist = px.bar(pubs_per_year, x='Annee', y='Publications', 
                      title="Évolution annuelle du volume de publications",
                      text='Publications', color='Publications', color_continuous_scale='Blues')
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Pivot Table (OLAP Pivot: Année vs Quartile)
    st.markdown("##### Pivot Table: Année vs Quartile")
    pivot_table = pd.crosstab(filtered_df['Annee'], filtered_df['Quartile'])
    st.dataframe(pivot_table, use_container_width=True)

# === ONGLET 2 : QUALITÉ SCIENTIFIQUE ===
with tab2:
    st.subheader("Analyse Qualitative (Dimension Journal/Impact)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Diagramme Circulaire (Pie Chart) - Répartition Quartiles
        quartile_counts = filtered_df['Quartile'].value_counts().reset_index()
        quartile_counts.columns = ['Quartile', 'Count']
        fig_pie = px.pie(quartile_counts, values='Count', names='Quartile', 
                         title="Répartition par Quartile (Q1-Q4)",
                         color='Quartile',
                         color_discrete_map={'Q1':'#2ecc71', 'Q2':'#3498db', 'Q3':'#f1c40f', 'Q4':'#e74c3c'})
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Box Plot Impact Score
        fig_box = px.box(filtered_df, x='Quartile', y='Impact_Score', 
                         title="Distribution du Facteur d'Impact par Quartile",
                         points="all")
        st.plotly_chart(fig_box, use_container_width=True)

# === ONGLET 3 : PERFORMANCE (PAYS & AUTEURS) ===
with tab3:
    st.subheader("Performance Géographique et Auteurs")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Carte Géographique
        pubs_by_country = filtered_df.groupby('Pays').size().reset_index(name='Count')
        fig_map = px.choropleth(pubs_by_country, locations="Pays", locationmode='country names',
                                color="Count", hover_name="Pays",
                                color_continuous_scale='Plasma',
                                title="Production Scientifique Mondiale")
        st.plotly_chart(fig_map, use_container_width=True)
        
    with col2:
        # Top 10 Auteurs (Extraction depuis la string)
        all_authors = []
        for authors_str in filtered_df['authors'].dropna():
            # Nettoyage basique
            authors = [a.strip() for a in str(authors_str).split(',')]
            all_authors.extend(authors)
            
        top_authors = pd.DataFrame(Counter(all_authors).most_common(10), columns=['Auteur', 'Publications'])
        
        fig_bar = px.bar(top_authors, x='Publications', y='Auteur', orientation='h',
                         title="Top 10 Auteurs les plus productifs")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# === ONGLET 4 : ANALYSE THÉMATIQUE & RÉSEAU ===
with tab4:
    st.subheader("Analyse de Réseau et Sémantique")

    # --- PARTIE 1 : VISUALISATION DES TOPICS ---
    st.markdown("### 🧩 Distribution des Thématiques (Topics)")
    
    col_topic1, col_topic2 = st.columns([1, 2])

    with col_topic1:
        # Bar Chart des Topics
        if not topics_dist.empty:
            fig_topics = px.bar(topics_dist, x='Count', y='Topic', orientation='h',
                                title="Dominance des Topics",
                                color='Count', color_continuous_scale='Viridis')
            fig_topics.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_topics, use_container_width=True)
        else:
            st.warning("Fichier topics_dist.csv introuvable.")

    with col_topic2:
        # EXPLORATEUR D'ARTICLES PAR TOPIC
        st.info("👇 Sélectionnez un Topic pour voir les articles associés")
        
        # Liste déroulante des topics
        available_topics = sorted(list(set(filtered_df['Topic'].unique())))
        selected_topic = st.selectbox("Filtrer par Thématique :", available_topics)
        
        # Filtrer le dataframe principal pour ce topic
        articles_in_topic = filtered_df[filtered_df['Topic'] == selected_topic][['title', 'Annee', 'Journal', 'Citations']]
        
        st.write(f"**{len(articles_in_topic)} Articles trouvés pour '{selected_topic}'**")
        st.dataframe(articles_in_topic, use_container_width=True, hide_index=True)


    st.markdown("---")
    
    # --- PARTIE 2 : GRAPHE DE RÉSEAU ---
    st.markdown("### 🕸️ Graphe de Collaboration (Co-auteurs)")
    st.info("Ce graphe montre les liens entre les chercheurs qui publient ensemble (Top 50 relations).")
    
    # Construction du graphe
    G = nx.Graph()
    
    # On prend un échantillon pour ne pas surcharger le graphe
    sample_df = filtered_df.head(50) 
    
    for authors_str in sample_df['authors'].dropna():
        authors = [a.strip() for a in str(authors_str).split(',') if len(a) > 2]
        # Créer des liens entre tous les auteurs d'un même papier
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                G.add_edge(authors[i], authors[j])

    # Visualisation simple avec Plotly via les positions des nœuds
    if len(G.nodes) > 0:
        pos = nx.spring_layout(G, k=0.5)
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

        node_x = []
        node_y = []
        node_text = []
        node_adjacencies = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_adjacencies.append(len(G.adj[node]))

        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers', hoverinfo='text',
            marker=dict(showscale=True, colorscale='YlGnBu', size=10, color=node_adjacencies,
                        colorbar=dict(thickness=15, title='Nb Collaborations')),
            text=node_text)

        fig_net = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(showlegend=False, hovermode='closest',
                                             margin=dict(b=0,l=0,r=0,t=0),
                                             xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                             yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        st.plotly_chart(fig_net, use_container_width=True)
    else:
        st.warning("Pas assez de données pour générer le graphe.")
