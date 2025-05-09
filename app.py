import streamlit as st
from backend_decoupe import optimiser_decoupe
from backend_dcg import optimiser_decoupe_dcg
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.markdown("""
    <div style="
        background: linear-gradient(90deg, #B9D9E0, blue);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        text-align: center;
    ">
        <h1 style="
            color: white;
            font-size: 48px;
            font-weight: 800;
            text-shadow: 1px 1px 2px black;
            margin: 0;
        ">✂️ Optimisation de découpe de barres</h1>
        <p style="
            color: #E8F5E9;
            font-size: 20px;
            margin-top: 10px;
            letter-spacing: 1px;
        ">Minimisez vos pertes. Maximisez votre rendement.</p>
    </div>
""", unsafe_allow_html=True)


st.markdown("""
    <h2 style="color:#264CA8; background-color:#F0F0F0; padding:10px; border-radius:10px;">
        Choix du type de profilé
    </h2>
""", unsafe_allow_html=True)

type_profile = st.selectbox("Type de profilé :", ["UPN", "Cornière", "Tôle/Platine"])

if type_profile == "UPN":
    type_detail = st.selectbox("Choisissez le type de UPN :", ["UPN80", "UPN100", "UPN120", "UPN140"])
    epaisseur = None  # inutile ici
elif type_profile == "Cornière":
    type_detail = st.selectbox("Choisissez la dimension de la cornière :", ["70", "60", "45", "40"])
    epaisseur = None
elif type_profile == "Tôle/Platine":
    epaisseur = st.number_input("Épaisseur (mm) :", min_value=1.0, step=0.5)
    type_detail = f"Tôle/Platine {epaisseur} mm"


if type_profile in ["UPN", "Cornière"]:
    Long = st.number_input("Longueur unitaire du profilé (mm) :", min_value=1000, step=500)
    largeur = None
else:  # Tôle/Platine
    Long = st.number_input("Longueur de la tôle/platine (mm) :", min_value=500, step=100)
    largeur = st.number_input("Largeur de la tôle/platine (mm) :", min_value=500, step=100)








st.markdown("""
    <h2 style="color:#264CA8; background-color:#F0F0F0; padding:10px; border-radius:10px;">
        Paramètres d'entrée
    </h2>
""", unsafe_allow_html=True)

Long = st.number_input("Longueur unitaire du profilé:", min_value=1000, step=1000)
n = st.number_input("Nombre de types de longueurs :", min_value=1, step=1)

longueurs = []
largeurs = []  # ajouter cette liste pour les tôles/platines
quantites = []

for i in range(n):
    st.markdown(f"""
        <div style="border: 2px solid #4CAF50; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
            <div style="background: linear-gradient(90deg, blue, #00B6F7); color: white; padding: 8px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 18px; text-align: center;">
                Paramètres de la coupe {i+1}
            </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    l = col1.number_input(f"Longueur {i+1} (mm) :", min_value=100, step=100, key=f"long_{i}")
    if type_profile == "Tôle/Platine":
        w = col2.number_input(f"Largeur {i+1} (mm) :", min_value=100, step=100, key=f"larg_{i}")
        largeurs.append(w)
    else:
        largeurs.append(None)
    q = col3.number_input(f"Quantité {i+1} :", min_value=1, step=1, key=f"quant_{i}")
    
    longueurs.append(l)
    quantites.append(q)
    
    st.markdown("</div>", unsafe_allow_html=True)




# Choix de l'algorithme (à mettre *hors* de la boucle)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: blue;
        color: white;
        border-radius: 10px;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
    }
    div.stSelectbox > div {
        background-color: #E3F2FD;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

algo_choice = st.selectbox(
    "Choisissez l'algorithme d'optimisation :",
    ("Exact (Docplex)", "Delayed Column Generation")
)

# Bouton pour lancer
bouton_calcul = st.button("Calculer l'optimisation")

if bouton_calcul:
    if algo_choice == "Exact (Docplex)":
        patterns = optimiser_decoupe(longueurs, quantites, Long)
    else:
        patterns = optimiser_decoupe_dcg(longueurs, quantites, Long)

    # ====== Statistiques ======
    total_barres = len(patterns)
    total_coupe = sum(sum(pattern['cuts']) for pattern in patterns)
    total_waste = sum(pattern['waste'] for pattern in patterns)
    total_longueur_utilisee = total_coupe
    total_longueur_achetee = total_barres * Long
    taux_perte = (total_waste / total_longueur_achetee) * 100
    taux_efficacite = (total_longueur_utilisee / total_longueur_achetee) * 100

    st.markdown("""
    <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
        Statistiques
    </h3>
""", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nombre total de barres", total_barres)
    col2.metric("Total des chutes (mm)", total_waste)
    col3.metric("Taux de perte (%)", f"{taux_perte:.2f}")
    col4.metric("Taux d’efficacité (%)", f"{taux_efficacite:.2f}")

    fig_pie = go.Figure(data=[go.Pie(
        labels=['Utilisé', 'Perte'],
        values=[total_longueur_utilisee, total_waste],
        marker_colors=['#2ca02c', '#707070']
    )])
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Visualisation des découpes")

    couleurs_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    couleur_map = {l: couleurs_palette[i % len(couleurs_palette)] for i, l in enumerate(sorted(set(longueurs)))}

    fig = go.Figure()

    for i, pattern in enumerate(patterns):
        x_start = 0
        for piece_length in pattern['cuts']:
            fig.add_trace(go.Bar(
                x=[piece_length],
                y=[i],
                width=0.7,
                name=f"{piece_length} mm",
                orientation='h',
                text=f"{piece_length} mm",
                textposition='inside',
                marker=dict(color=couleur_map[piece_length])
            ))
            x_start += piece_length

            fig.add_trace(go.Bar(
                x=[1],
                y=[i],
                width=0.05,
                orientation='h',
                marker=dict(color='black', opacity=0.5),
                showlegend=False,
                hoverinfo='skip',
                text=None
            ))

        if pattern['waste'] > 0:
            fig.add_trace(go.Bar(
                x=[pattern['waste']],
                y=[i],
                width=0.7,
                name='Chute',
                orientation='h',
                text=f"Chute: {pattern['waste']} mm",
                textposition='inside',
                marker=dict(color='black', opacity=0.5)
            ))

    fig.update_layout(
        barmode='stack',
        title_text='Découpe optimisée de toutes les barres',
        xaxis_title='Longueur (mm)',
        yaxis=dict(
            tickvals=list(range(len(patterns))),
            ticktext=[f"Barre {i+1}" for i in range(len(patterns))]
        ),
        height=200 + 50 * len(patterns),
        legend_title_text='Longueurs'
    )

    st.plotly_chart(fig, use_container_width=True)
