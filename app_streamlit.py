import streamlit as st
from backend_decoupe import optimiser_decoupe
from backend_dcg import optimiser_decoupe_dcg
from backend_surface import optimiser_decoupe_surface
import plotly.graph_objects as go
import numpy as np

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

# Paramètres de longueur (et largeur pour les tôles)
st.markdown("""
    <h2 style="color:#264CA8; background-color:#F0F0F0; padding:10px; border-radius:10px;">
        Paramètres de longueur
    </h2>
""", unsafe_allow_html=True)

if type_profile in ["UPN", "Cornière"]:
    Long = st.number_input("Longueur unitaire du profilé (mm) :", min_value=1000, step=500, value=6000)
    largeur_totale = None
else:  # Tôle/Platine
    Long = st.number_input("Longueur de la tôle/platine (mm) :", min_value=500, step=100, value=2000)
    largeur_totale = st.number_input("Largeur de la tôle/platine (mm) :", min_value=500, step=100, value=1000)

# Définition des pièces à découper
st.markdown("""
    <h2 style="color:#264CA8; background-color:#F0F0F0; padding:10px; border-radius:10px;">
        Pièces à découper
    </h2>
""", unsafe_allow_html=True)

n = st.number_input("Nombre de types de longueurs :", min_value=1, step=1, value=2)

longueurs = []
largeurs = []
quantites = []

for i in range(n):
    st.markdown(f"""
        <div style="border: 2px solid #4CAF50; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
            <div style="background: linear-gradient(90deg, blue, #00B6F7); color: white; padding: 8px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 18px; text-align: center;">
                Paramètres de la coupe {i+1}
            </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    l = col1.number_input(f"Longueur {i+1} (mm) :", min_value=100, step=100, key=f"long_{i}", value=1000+i*500)
    if type_profile == "Tôle/Platine":
        w = col2.number_input(f"Largeur {i+1} (mm) :", min_value=100, step=100, key=f"larg_{i}", value=300+i*100)
        largeurs.append(w)
    else:
        largeurs.append(None)
    q = col3.number_input(f"Quantité {i+1} :", min_value=1, step=1, key=f"quant_{i}", value=2)
    
    longueurs.append(l)
    quantites.append(q)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Options de visualisation et d'algorithme
st.markdown("""
    <h2 style="color:#264CA8; background-color:#F0F0F0; padding:10px; border-radius:10px;">
        Options d'optimisation et de visualisation
    </h2>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    algo_choice = st.selectbox(
        "Choisissez l'algorithme d'optimisation :",
        ("Exact (Docplex)", "Delayed Column Generation")
    )

with col2:
    optim_type = st.selectbox(
        "Type d'optimisation :",
        ("Optimisation par longueur", "Optimisation par surface")
    )

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

# Bouton pour lancer
bouton_calcul = st.button("Calculer l'optimisation")

if bouton_calcul:
    if optim_type == "Optimisation par longueur":
        if algo_choice == "Exact (Docplex)":
            patterns = optimiser_decoupe(longueurs, quantites, Long)
        else:
            patterns = optimiser_decoupe_dcg(longueurs, quantites, Long)
            
        # Calcul des statistiques
        total_barres = len(patterns)
        total_coupe = sum(sum(pattern['cuts']) for pattern in patterns)
        total_waste = sum(pattern['waste'] for pattern in patterns)
        total_longueur_utilisee = total_coupe
        total_longueur_achetee = total_barres * Long
        taux_perte = (total_waste / total_longueur_achetee) * 100
        taux_efficacite = (total_longueur_utilisee / total_longueur_achetee) * 100

        # Affichage des statistiques
        st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Statistiques - Optimisation par longueur
            </h3>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Nombre total de barres", total_barres)
        col2.metric("Total des chutes (mm)", total_waste)
        col3.metric("Taux de perte (%)", f"{taux_perte:.2f}")
        col4.metric("Taux d'efficacité (%)", f"{taux_efficacite:.2f}")

        # Visualisation en camembert
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Utilisé', 'Perte'],
            values=[total_longueur_utilisee, total_waste],
            marker_colors=['#2ca02c', '#707070']
        )])
        st.plotly_chart(fig_pie, use_container_width=True)

        # Visualisation des découpes
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

    else:  # Optimisation par surface
        with st.spinner("Calcul de l'optimisation par surface en cours..."):
            surface_patterns = optimiser_decoupe_surface(
                longueurs, largeurs, quantites, 
                type_profile, type_detail, Long, 
                largeur_totale, epaisseur
            )
            
            if type_profile == "Tôle/Platine":
                # Statistiques pour les tôles/platines (optimisation 2D)
                total_plaques = len(surface_patterns)
                total_surface_achetee = total_plaques * Long * largeur_totale
                total_waste_surface = sum(pattern['waste_surface'] for pattern in surface_patterns)
                taux_perte_surface = sum(pattern['waste_percentage'] for pattern in surface_patterns) / total_plaques
                taux_efficacite_surface = 100 - taux_perte_surface
                
                st.markdown("""
                    <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                        Statistiques - Optimisation par surface (Tôle/Platine)
                    </h3>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Nombre total de plaques", total_plaques)
                col2.metric("Surface totale de chute (mm²)", f"{total_waste_surface:,.0f}")
                col3.metric("Taux de perte (%)", f"{taux_perte_surface:.2f}")
                col4.metric("Taux d'efficacité (%)", f"{taux_efficacite_surface:.2f}")
                
                # Visualisation en camembert
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Utilisé', 'Perte'],
                    values=[total_surface_achetee - total_waste_surface, total_waste_surface],
                    marker_colors=['#2ca02c', '#707070']
                )])
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Visualisation des découpes 2D
                st.subheader("Visualisation des découpes 2D")
                
                for i, pattern in enumerate(surface_patterns):
                    st.markdown(f"""
                        <div style="border: 2px solid #4CAF50; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
                            <div style="background: linear-gradient(90deg, blue, #00B6F7); color: white; padding: 8px; border-radius: 8px; font-weight: bold; font-size: 18px; text-align: center;">
                                Plaque {i+1} - Chute: {pattern['waste_percentage']:.2f}%
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    fig = go.Figure()
                    
                    plaque_L = pattern['dimensions']['plaque']['L']
                    plaque_l = pattern['dimensions']['plaque']['l']
                    piece_L = pattern['dimensions']['piece']['L']
                    piece_l = pattern['dimensions']['piece']['l']
                    h = pattern['pattern']['h']
                    v = pattern['pattern']['v']
                    
                    # Dessiner la plaque de base
                    fig.add_shape(
                        type="rect",
                        x0=0, y0=0,
                        x1=plaque_L, y1=plaque_l,
                        line=dict(color="black"),
                        fillcolor="rgba(200, 200, 200, 0.3)"
                    )
                    
                    # Dessiner les pièces découpées
                    for row in range(v):
                        for col in range(h):
                            x0 = col * piece_L
                            y0 = row * piece_l
                            x1 = x0 + piece_L
                            y1 = y0 + piece_l
                            
                            fig.add_shape(
                                type="rect",
                                x0=x0, y0=y0,
                                x1=x1, y1=y1,
                                line=dict(color="blue"),
                                fillcolor="rgba(0, 100, 255, 0.5)"
                            )
                            
                            # Ajouter le texte avec les dimensions
                            fig.add_annotation(
                                x=(x0 + x1) / 2,
                                y=(y0 + y1) / 2,
                                text=f"{piece_L}x{piece_l}",
                                showarrow=False,
                                font=dict(color="white", size=12)
                            )
                    
                    fig.update_layout(
                        title=f"Plaque {i+1} - {plaque_L}x{plaque_l} mm",
                        xaxis_title="Longueur (mm)",
                        yaxis_title="Largeur (mm)",
                        width=800,
                        height=500,
                        showlegend=False,
                        xaxis=dict(range=[0, plaque_L]),
                        yaxis=dict(range=[0, plaque_l], scaleanchor="x", scaleratio=1)
                    )
                    
                    st.plotly_chart(fig)
                    
                    # Information sur la chute
                    st.info(f"Surface de chute: {pattern['waste_surface']:,.0f} mm² ({pattern['waste_percentage']:.2f}%)")
                
            else:  # UPN ou Cornière (optimisation 1D avec calcul de surface)
                # Statistiques pour les UPN/Cornières
                total_barres = len(surface_patterns)
                total_coupe = sum(len(pattern['cuts']) for pattern in surface_patterns)
                total_waste_length = sum(pattern['waste_length'] for pattern in surface_patterns)
                total_waste_surface = sum(pattern['waste_surface'] for pattern in surface_patterns)
                total_longueur_achetee = total_barres * Long
                taux_perte_longueur = (total_waste_length / total_longueur_achetee) * 100
                taux_perte_surface = sum(pattern['waste_percentage'] for pattern in surface_patterns) / total_barres
                
                st.markdown("""
                    <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                        Statistiques - Optimisation par surface et longueur
                    </h3>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Statistiques de longueur")
                    col1a, col1b = st.columns(2)
                    col1a.metric("Nombre total de barres", total_barres)
                    col1b.metric("Chute totale (mm)", total_waste_length)
                    col1c, col1d = st.columns(2)
                    col1c.metric("Taux de perte en longueur (%)", f"{taux_perte_longueur:.2f}")
                    col1d.metric("Taux d'efficacité en longueur (%)", f"{100-taux_perte_longueur:.2f}")
                
                with col2:
                    st.subheader("Statistiques de surface")
                    col2a, col2b = st.columns(2)
                    col2a.metric("Surface totale achetée (m²)", f"{total_barres * Long / 1000000:.2f}")
                    col2b.metric("Surface de chute (m²)", f"{total_waste_surface:.4f}")
                    col2c, col2d = st.columns(2)
                    col2c.metric("Taux de perte en surface (%)", f"{taux_perte_surface:.2f}")
                    col2d.metric("Taux d'efficacité en surface (%)", f"{100-taux_perte_surface:.2f}")
                
                # Visualisation en double camembert
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_pie1 = go.Figure(data=[go.Pie(
                        labels=['Utilisé', 'Perte'],
                        values=[total_longueur_achetee - total_waste_length, total_waste_length],
                        marker_colors=['#2ca02c', '#707070'],
                        title="Répartition de la longueur"
                    )])
                    st.plotly_chart(fig_pie1, use_container_width=True)
                
                with col2:
                    surface_totale = total_barres * Long / 1000  # Une valeur approximative pour la surface
                    fig_pie2 = go.Figure(data=[go.Pie(
                        labels=['Utilisé', 'Perte'],
                        values=[surface_totale - total_waste_surface, total_waste_surface],
                        marker_colors=['#2ca02c', '#707070'],
                        title="Répartition de la surface"
                    )])
                    st.plotly_chart(fig_pie2, use_container_width=True)
                
                # Visualisation des découpes
                st.subheader("Visualisation des découpes")
                
                couleurs_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                couleur_map = {l: couleurs_palette[i % len(couleurs_palette)] for i, l in enumerate(sorted(set(longueurs)))}

                fig = go.Figure()

                for i, pattern in enumerate(surface_patterns):
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

                    if pattern['waste_length'] > 0:
                        fig.add_trace(go.Bar(
                            x=[pattern['waste_length']],
                            y=[i],
                            width=0.7,
                            name='Chute',
                            orientation='h',
                            text=f"Chute: {pattern['waste_length']} mm",
                            textposition='inside',
                            marker=dict(color='black', opacity=0.5)
                        ))

                fig.update_layout(
                    barmode='stack',
                    title_text='Découpe optimisée de toutes les barres',
                    xaxis_title='Longueur (mm)',
                    yaxis=dict(
                        tickvals=list(range(len(surface_patterns))),
                        ticktext=[f"Barre {i+1} - Chute surface: {pattern['waste_percentage']:.2f}%" for i, pattern in enumerate(surface_patterns)]
                    ),
                    height=200 + 50 * len(surface_patterns),
                    legend_title_text='Longueurs'
                )

                st.plotly_chart(fig, use_container_width=True)
                
                # Affichage des informations de chutes de surface
                st.subheader("Détails des chutes de surface")
                for i, pattern in enumerate(surface_patterns):
                    st.info(f"Barre {i+1}: Chute en longueur = {pattern['waste_length']} mm, " +
                            f"Chute en surface = {pattern['waste_surface']:.4f} m² ({pattern['waste_percentage']:.2f}%)")