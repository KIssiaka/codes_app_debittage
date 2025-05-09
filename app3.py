# 1. First, add these imports at the top of your file
import base64
from io import BytesIO
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
import matplotlib.pyplot as plt
import datetime

# 2. Add this function somewhere after your imports and before your main code
def create_download_report(patterns, type_profile, type_detail, Long, largeur_totale=None, 
                           taux_perte=None, taux_efficacite=None, unique_patterns=None,
                           epaisseur=None, is_surface_optim=False, piece_names=None):
    """Creates a PDF report for download with optimization results"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    from reportlab.lib import colors
    # Setup styles with blue theme
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        textColor=colors.HexColor('#0000CC'),
        spaceAfter=12,
        fontSize=16
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#0055AA'),
        spaceAfter=10,
        fontSize=14
    )
    normal_style = styles["Normal"]
    
    # Add title and date
    current_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if is_surface_optim and type_profile == "Tôle/Platine":
        title_text = "Rapport d'optimisation de découpe de tôle"
    else:
        title_text = "Rapport d'optimisation de découpe de barres"
    
    title = Paragraph(f"{title_text} - {current_date}", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Material Information
    if type_profile == "UPN":
        material_info = f"Profilé: {type_profile} {type_detail} - Longueur: {Long} mm"
    elif type_profile == "Cornière":
        material_info = f"Profilé: {type_profile} {type_detail} - Longueur: {Long} mm"
    elif type_profile == "Tôle/Platine":
        material_info = f"Tôle: {epaisseur} mm - Dimensions: {Long} × {largeur_totale} mm"
    else:
        material_info = f"Produit: {type_profile} {type_detail} - Longueur: {Long} mm"
    
    product_info = Paragraph(material_info, subtitle_style)
    story.append(product_info)
    story.append(Spacer(1, 12))
    
    # -------------------------------
    # Tableau des longueurs demandées avec noms
    # -------------------------------
    if not is_surface_optim and patterns:
        lengths_data = [['Identifiant', 'Longueur (mm)', 'Quantité']]
        for i, (length, quantity) in enumerate(zip(longueurs, quantites)):
            name = piece_names[i] if piece_names and i < len(piece_names) else ""
            identifier = f"{name} {type_detail}" if name else f"{type_detail}"
            lengths_data.append([identifier, f"{length}", f"{quantity}"])
        
        lengths_table_title = Paragraph("Détail des longueurs demandées", subtitle_style)
        story.append(lengths_table_title)
        
        lengths_table = Table(lengths_data, colWidths=[doc.width/3-10, doc.width/3-10, doc.width/3-10])
        lengths_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#0055AA')),
            ('TEXTCOLOR', (0, 0), (2, 0), colors.white),
            ('ALIGN', (0, 0), (2, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (2, 0), 6),
            ('TOPPADDING', (0, 0), (2, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT')
        ]))
        story.append(lengths_table)
        story.append(Spacer(1, 15))
    
    # -------------------------------
    # Tableaux de statistiques côte à côte
    # -------------------------------
    col1, col2 = st.columns(2)
    
    # Statistiques de longueur
    length_stats = [['Statistiques de longueur', 'Valeurs']]
    length_stats.append(['Métrage net (mm)', f"{int(total_length_net)}"])
    length_stats.append(['Métrage utilisé (mm)', f"{int(Long * len(patterns))}"])
    length_stats.append(['Nombre de barres', f"{len(patterns)}"])
    length_stats.append(['Total des chutes (mm)', f"{int(total_waste)}"])
    length_stats.append(['Taux de chute', f"{taux_perte:.1f}%"])
    length_stats.append(['Taux d\'efficacité', f"{taux_efficacite:.1f}%"])
    
    # Statistiques de surface
    surface_stats = [['Statistiques de surface', 'Valeurs']]
    total_surface = Long * largeur_totale if largeur_totale else Long * 100  # Approximation si pas de largeur
    surface_utilisee = total_surface * (taux_efficacite/100)
    surface_perdue = total_surface * (taux_perte/100)
    
    surface_stats.append(['Surface totale (mm²)', f"{int(total_surface)}"])
    surface_stats.append(['Surface utilisée (mm²)', f"{int(surface_utilisee)}"])
    surface_stats.append(['Surface perdue (mm²)', f"{int(surface_perdue)}"])
    surface_stats.append(['Taux de perte surface', f"{taux_perte:.1f}%"])
    surface_stats.append(['Taux d\'efficacité surface', f"{taux_efficacite:.1f}%"])

    # Création des tableaux
    stats_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#0055AA')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT')
    ])

    length_table = Table(length_stats, colWidths=[doc.width/2-10, doc.width/2-10])
    length_table.setStyle(stats_table_style)
    
    surface_table = Table(surface_stats, colWidths=[doc.width/2-10, doc.width/2-10])
    surface_table.setStyle(stats_table_style)

    # Ajout des tableaux côte à côte
    story.append(Paragraph("Statistiques d'optimisation", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Création d'un tableau pour contenir les deux tableaux de stats
    stats_container = Table([[length_table, surface_table]], colWidths=[doc.width/2-10, doc.width/2-10])
    story.append(stats_container)
    story.append(Spacer(1, 15))

    # -------------------------------
    # Graphiques en camembert côte à côte
    # -------------------------------
    # Création des deux graphiques
    plt.figure(figsize=(10, 5))
    
    # Graphique de longueur
    plt.subplot(1, 2, 1)
    labels = ['Utilisé', 'Perte']
    sizes = [taux_efficacite, taux_perte]
    colors = ['#4CAF50', '#AAAAAA']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Répartition des longueurs')
    plt.axis('equal')
    
    # Graphique de surface
    plt.subplot(1, 2, 2)
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Répartition des surfaces')
    plt.axis('equal')
    
    # Sauvegarde des graphiques
    chart_buffer = BytesIO()
    plt.savefig(chart_buffer, format='png', bbox_inches='tight')
    chart_buffer.seek(0)
    plt.close()
    
    # Ajout des graphiques au PDF
    chart_img = Image(chart_buffer, width=6*inch, height=3*inch)
    story.append(chart_img)
    story.append(Spacer(1, 15))
    
    # -------------------------------
    # Graphique des motifs de découpe
    # -------------------------------
    patterns_title = Paragraph("Synthèse des motifs de découpe", title_style)
    story.append(patterns_title)
    story.append(Spacer(1, 10))
    
    # Draw patterns graphically
    if not is_surface_optim:
        # Find unique patterns if not provided
        if not unique_patterns:
            unique_patterns = []
            for i, pattern in enumerate(patterns):
                unique_patterns.append({
                    'pattern': pattern,
                    'count': 1  # Just show each pattern once if unique_patterns not provided
                })
        
        # For each unique pattern
        for i, unique_pattern in enumerate(unique_patterns):
            pattern = unique_pattern.get('pattern', patterns[i] if i < len(patterns) else patterns[0])
            count = unique_pattern.get('count', 1)
            
            pattern_title = Paragraph(f"Motif de découpe #{i+1} (×{count})", subtitle_style)
            story.append(pattern_title)
            
            # Create a visualization of the pattern
            fig, ax = plt.subplots(figsize=(8, 1.5))
            
            # Extract segments from pattern based on format
            segments = []
            if 'segments' in pattern:
                segments = sorted(pattern['segments'], key=lambda x: x.get('position', 0))
            elif 'cuts' in pattern:
                # Convert older 'cuts' format to segments
                pos = 0
                for j, cut in enumerate(pattern['cuts']):
                    segment = {
                        'length': cut,
                        'position': pos,
                        'type': type_detail
                    }
                    # Try to get name if it exists
                    if 'names' in pattern and j < len(pattern['names']):
                        segment['name'] = pattern['names'][j]
                    segments.append(segment)
                    pos += cut
            
            # Track position for drawing
            current_pos = 0
            segment_colors = ['#4CAF50', '#F44336', '#2196F3', '#FFC107', '#9C27B0']  # Green, Red, Blue, Yellow, Purple
            
            # Draw each segment
            for j, segment in enumerate(segments):
                width = segment['length']
                color_index = j % len(segment_colors)
                
                # Get name for display
                if 'name' in segment and segment['name']:
                    display_name = f"[{segment['name']} {segment.get('type', type_detail)}] {width}mm"
                else:
                    display_name = f"[{segment.get('type', type_detail)}] {width}mm"
                    
                # Draw rectangle
                rect = plt.Rectangle((current_pos, 0), width, 0.5, 
                                    facecolor=segment_colors[color_index])
                ax.add_patch(rect)
                
                # Add text in the middle of the segment
                ax.text(current_pos + width/2, 0.25, display_name, 
                        ha='center', va='center', color='white', fontweight='bold')
                
                current_pos += width
            
            # If there's waste at the end, draw it in grey
            if isinstance(pattern, list):
                # Assuming you want to access the first element of the list
                waste = pattern[0].get('waste', pattern[0].get('waste_length', 0)) if pattern else 0
            else:
                waste = pattern.get('waste', pattern.get('waste_length', 0))
            if waste > 0:
                waste_rect = plt.Rectangle((current_pos, 0), waste, 0.5, facecolor='grey')
                ax.add_patch(waste_rect)
                ax.text(current_pos + waste/2, 0.25, f"Chute: {waste} mm", 
                        ha='center', va='center', color='white')
            
            # Set axis limits and remove ticks
            ax.set_xlim(0, Long)
            ax.set_ylim(0, 0.5)
            ax.set_xticks(np.arange(0, Long+1, 1000))
            ax.set_yticks([])
            ax.set_xlabel("Longueur (mm)")
            
            # Save the pattern visualization
            pattern_buffer = BytesIO()
            plt.savefig(pattern_buffer, format='png', bbox_inches='tight', dpi=100)
            pattern_buffer.seek(0)
            plt.close()
            
            # Add the pattern visualization to the PDF
            pattern_img = Image(pattern_buffer, width=6*inch, height=1.2*inch)
            story.append(pattern_img)
            
            # Add details panel on the right side (like in your image)
            details_data = [['Sections']]
            for segment in segments:
                if 'name' in segment and segment['name']:
                    section_name = f"{segment['name']} {segment.get('type', type_detail)}: {segment['length']} mm"
                else:
                    section_name = f"{segment.get('type', type_detail)}: {segment['length']} mm"
                details_data.append([section_name])
            
            if waste > 0:
                details_data.append([f"Chute: {waste} mm"])
            
            # Create the details table
            details_table = Table(details_data, colWidths=[doc.width/2-10])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#0055AA')),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (0, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
            ]))
            
            story.append(Spacer(1, 5))
            story.append(Paragraph("Détails", subtitle_style))
            story.append(details_table)
            story.append(Spacer(1, 15))
    
    # Build PDF
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Encode to base64 for download
    b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    return b64_pdf

import streamlit as st
from backend_decoupe import optimiser_decoupe
from backend_dcg import optimiser_decoupe_dcg
from backend_surface import optimiser_decoupe_surface
import plotly.graph_objects as go
import numpy as np
from collections import Counter

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
    type_detail = f"Tôle {epaisseur} mm"

# Paramètres de longueur (et largeur pour les tôles)
# Injection CSS globale
st.markdown("""
    <style>
    .stNumberInput input {
        border: 2px solid #264CA8;
        border-radius: 6px;
        padding: 8px;
        font-size: 16px;
    }
    .stSelectbox div[data-baseweb="select"] {
        border: 2px solid #264CA8;
        border-radius: 8px;
    }
    .stSelectbox span {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Titre stylisé
st.markdown("""
    <h2 style="
        color:#264CA8;
        background-color:#f9f9f9;
        padding:15px;
        border-radius:12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        font-family: 'Arial', sans-serif;
        ">
        Paramètres de longueur
    </h2>
""", unsafe_allow_html=True)

# Les inputs comme avant
if type_profile in ["UPN", "Cornière"]:
    Long = st.number_input("Longueur unitaire du profilé (mm) :", min_value=1000, step=500, value=6000)
    largeur_totale = None
else:
    Long = st.number_input("Longueur de la tôle (mm) :", min_value=500, step=100, value=2000)
    largeur_totale = st.number_input("Largeur de la tôle (mm) :", min_value=500, step=100, value=1000)


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
piece_names = []

for i in range(n):
    st.markdown(f"""
        <div style="border: 2px solid #4CAF50; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
            <div style="background: linear-gradient(90deg, blue, #00B6F7); color: white; padding: 8px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 18px; text-align: center;">
                Paramètres de la coupe {i+1}
            </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        piece_name = st.text_input(f"Nom de la pièce {i+1}", key=f"name_{i}")
    with col2:
        longueur = st.number_input(f"Longueur {i+1} (mm)", min_value=1, value=1000, key=f"longueur_{i}")
    with col3:
        quantite = st.number_input(f"Quantité {i+1}", min_value=1, value=1, key=f"quantite_{i}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    longueurs.append(longueur)
    quantites.append(quantite)
    piece_names.append(piece_name)  # Stockage des noms des pièces

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
    # Fonction pour formater les labels de pièces
    def format_piece_label(length, type_profile, type_detail, largeur=None):
        if type_profile == "UPN":
            return f"[{type_detail}] {length}mm"
        elif type_profile == "Cornière":
            return f"[L{type_detail}] {length}mm"
        elif type_profile == "Tôle/Platine":
            if largeur:
                return f"[{type_detail}] {length}×{largeur}mm"
            else:
                return f"[{type_detail}] {length}mm"
        else:
            return f"{length}mm"
    
    # Fonction pour convertir les découpes en motifs uniques
    # 1. Correction de la fonction get_unique_patterns() - ligne 171 environ
    def get_unique_patterns(patterns):
        unique_patterns = {}
        
        for pattern in patterns:
            if 'cuts' in pattern:
                # Pour optimisation par longueur
                pattern_str = '-'.join(map(str, sorted(pattern['cuts'])))
                if pattern_str not in unique_patterns:
                    unique_patterns[pattern_str] = {
                        'pattern': pattern['cuts'],
                        'count': 1,
                        'waste': pattern.get('waste', pattern.get('waste_length', 0))  # Utilisez get() avec valeur par défaut
                    }
                else:
                    unique_patterns[pattern_str]['count'] += 1
            elif 'pattern' in pattern:
                # Pour optimisation par surface de tôles
                h = pattern['pattern']['h']
                v = pattern['pattern']['v']
                pattern_str = f"{h}×{v}"
                if pattern_str not in unique_patterns:
                    unique_patterns[pattern_str] = {
                        'pattern': {'h': h, 'v': v},
                        'count': 1,
                        'waste_percentage': pattern['waste_percentage'],
                        'dimensions': pattern['dimensions']
                    }
                else:
                    unique_patterns[pattern_str]['count'] += 1
        
        return list(unique_patterns.values())
    
    if optim_type == "Optimisation par longueur":
        if algo_choice == "Exact (Docplex)":
            patterns = optimiser_decoupe(longueurs, quantites, Long)
        else:
            patterns = optimiser_decoupe_dcg(longueurs, quantites, Long)
            
        # Calcul des statistiques
        # Calcul des statistiques avec protection contre la division par zéro
        total_barres = len(patterns)
        total_coupe = sum(sum(pattern['cuts']) for pattern in patterns)
        total_waste = sum(pattern['waste'] for pattern in patterns)
        total_longueur_utilisee = total_coupe
        total_longueur_achetee = total_barres * Long if total_barres > 0 else 1  # Éviter division par zéro
        taux_perte = (total_waste / total_longueur_achetee) * 100 if total_longueur_achetee > 0 else 0
        taux_efficacite = (total_longueur_utilisee / total_longueur_achetee) * 100 if total_longueur_achetee > 0 else 0


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
        fig_pie.update_layout(title="Répartition de l'utilisation des matériaux")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Préparation pour le rendu avec des labels détaillés
        formatted_labels = [format_piece_label(l, type_profile, type_detail) for l in longueurs]
        label_map = {l: formatted_labels[i] for i, l in enumerate(longueurs)}

        # Visualisation des découpes avec séparateurs
        st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Visualisation des découpes
            </h3>
        """, unsafe_allow_html=True)

        couleurs_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        couleur_map = {l: couleurs_palette[i % len(couleurs_palette)] for i, l in enumerate(sorted(set(longueurs)))}

        fig = go.Figure()

        for i, pattern in enumerate(patterns):
            x_pos = 0
            for j, piece_length in enumerate(pattern['cuts']):
                # Ajouter une pièce
                fig.add_trace(go.Bar(
                    x=[piece_length],
                    y=[i],
                    width=0.7,
                    name=label_map[piece_length],
                    orientation='h',
                    text=label_map[piece_length],
                    textposition='inside',
                    marker=dict(color=couleur_map[piece_length]),
                    base=x_pos
                ))
                x_pos += piece_length
                
                # Ajouter un séparateur après chaque pièce sauf la dernière
                if j < len(pattern['cuts']) - 1:
                    fig.add_trace(go.Bar(
                        x=[5],  # largeur de 5mm pour le séparateur
                        y=[i],
                        width=0.7,
                        orientation='h',
                        marker=dict(color='black'),
                        showlegend=False if j > 0 else True,
                        name="Séparateur" if j == 0 else None,
                        base=x_pos
                    ))
                    x_pos += 5  # Ajustement après le séparateur

            # Ajouter la chute à la fin
            if pattern['waste'] > 0:
                fig.add_trace(go.Bar(
                    x=[pattern['waste']],
                    y=[i],
                    width=0.7,
                    name='Chute',
                    orientation='h',
                    text=f"Chute: {pattern['waste']} mm",
                    textposition='inside',
                    marker=dict(color='#505050', opacity=0.7),
                    base=x_pos
                ))

        fig.update_layout(
            barmode='stack',
            title_text=f'Découpe optimisée de toutes les barres ({type_profile} {type_detail})',
            xaxis_title='Longueur (mm)',
            yaxis=dict(
                title='Barres',
                tickvals=list(range(len(patterns))),
                ticktext=[f"Barre {i+1}" for i in range(len(patterns))]
            ),
            height=200 + 50 * len(patterns),
            legend_title_text='Sections'
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Analyse et visualisation des motifs uniques
        # Analyse et visualisation des motifs uniques
        unique_patterns = get_unique_patterns(patterns)

        st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Synthèse des motifs de découpe
            </h3>
        """, unsafe_allow_html=True)

        # Tri des motifs uniques par fréquence décroissante
        unique_patterns.sort(key=lambda x: x['count'], reverse=True)

        for i, unique_pattern in enumerate(unique_patterns):

            # Création d'un graphique pour chaque motif unique
            fig_pattern = go.Figure()
            
            x_pos = 0
            pattern_pieces = []  # Pour stocker les informations des pièces pour l'affichage latéral
            
            for j, piece_length in enumerate(unique_pattern['pattern']):
                # Ajouter une pièce
                piece_label = label_map[piece_length]
                fig_pattern.add_trace(go.Bar(
                    x=[piece_length],
                    y=[0],
                    width=0.7,
                    name=piece_label,
                    orientation='h',
                    text=piece_label,
                    textposition='inside',
                    marker=dict(color=couleur_map[piece_length]),
                    base=x_pos
                ))
                pattern_pieces.append(piece_label)
                x_pos += piece_length
                
                # Ajouter un séparateur après chaque pièce sauf la dernière
                if j < len(unique_pattern['pattern']) - 1:
                    fig_pattern.add_trace(go.Bar(
                        x=[5],
                        y=[0],
                        width=0.7,
                        orientation='h',
                        marker=dict(color='black'),
                        showlegend=j == 0,
                        name="Séparateur" if j == 0 else None,
                        base=x_pos
                    ))
                    x_pos += 5
            
            # Ajouter la chute à la fin
            if unique_pattern['waste'] > 0:
                fig_pattern.add_trace(go.Bar(
                    x=[unique_pattern['waste']],
                    y=[0],
                    width=0.7,
                    name='Chute',
                    orientation='h',
                    text=f"Chute: {unique_pattern['waste']} mm",
                    textposition='inside',
                    marker=dict(color='#505050', opacity=0.7),
                    base=x_pos
                ))
            
            # Création d'un layout avec barmode='stack' pour assurer l'alignement correct
            fig_pattern.update_layout(
                barmode='stack',  # Important pour l'alignement correct
                title_text=f"Motif de découpe #{i+1} (×{unique_pattern['count']})",
                xaxis_title='Longueur (mm)',
                yaxis=dict(
                    showticklabels=False,
                ),
                height=150,
                legend_title_text='Sections',
                xaxis=dict(range=[0, Long]),  # S'assurer que l'échelle est constante
                margin=dict(l=50, r=50, t=70, b=50),  # Ajuster les marges
            )
            
            # Créer une disposition à colonnes pour le graphique et les informations
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.plotly_chart(fig_pattern, use_container_width=True)
                
            with col2:
                st.markdown("<h4 style='text-align: center; color: #0D47A1;'>Détails</h4>", unsafe_allow_html=True)
                
                # Détails du motif avec comptage
                pieces_count = Counter(unique_pattern['pattern'])
                pieces_details = []
                
                for piece, count in pieces_count.items():
                    st.markdown(f"<div style='padding: 5px; margin: 5px 0; background-color: {couleur_map[piece]}; color: white; border-radius: 5px; text-align: center;'>{count}× {label_map[piece]}</div>", unsafe_allow_html=True)
                
                if unique_pattern['waste'] > 0:
                    st.markdown(f"<div style='padding: 5px; margin: 5px 0; background-color: #505050; color: white; border-radius: 5px; text-align: center;'>Chute: {unique_pattern['waste']} mm</div>", unsafe_allow_html=True)


            
            #st.plotly_chart(fig_pattern, use_container_width=True)
            
            # Détails du motif
            #pieces_count = Counter(unique_pattern['pattern'])
            #pieces_details = [f"{count}× {label_map[piece]}" for piece, count in pieces_count.items()]
            #st.info(f"Composition: {', '.join(pieces_details)}, Chute: {unique_pattern['waste']} mm")

            # 3. In the "if bouton_calcul:" section, after all visualization code but before the end of the block,
        # add this code to create the download button

        # Add this at the end of the "if bouton_calcul:" block, just before it ends:

        # Create download button for report
        st.markdown("---")
        st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Télécharger la synthèse
            </h3>
        """, unsafe_allow_html=True)

        if optim_type == "Optimisation par longueur":
            pdf_base64 = create_download_report(
                patterns=patterns,
                type_profile=type_profile,
                type_detail=type_detail,
                Long=Long,
                taux_perte=taux_perte,
                taux_efficacite=taux_efficacite,
                unique_patterns=unique_patterns,
                piece_names=piece_names
            )
            
            download_filename = f"decoupe_{type_profile}_{type_detail}.pdf"
        else:  # Optimisation par surface
            if type_profile == "Tôle/Platine":
                pdf_base64 = create_download_report(
                    patterns=surface_patterns,
                    type_profile=type_profile,
                    type_detail=type_detail,
                    Long=Long,
                    largeur_totale=largeur_totale,
                    taux_perte=taux_perte_surface,
                    taux_efficacite=taux_efficacite_surface,
                    unique_patterns=unique_patterns,
                    epaisseur=epaisseur,
                    is_surface_optim=True,
                    piece_names=[format_piece_label(l, type_profile, type_detail, w) for l, w in zip(longueurs, largeurs)]
                )
                
                download_filename = f"decoupe_tole_{epaisseur}mm.pdf"
            else:
                pdf_base64 = create_download_report(
                    patterns=surface_patterns,
                    type_profile=type_profile,
                    type_detail=type_detail,
                    Long=Long,
                    taux_perte=taux_perte_longueur,
                    taux_efficacite=100-taux_perte_longueur,
                    unique_patterns=unique_patterns,
                    piece_names=[format_piece_label(l, type_profile, type_detail) for l in longueurs]
                )
                
                download_filename = f"decoupe_{type_profile}_{type_detail}.pdf"

        # Create the download link
        href = f'<a href="data:application/pdf;base64,{pdf_base64}" download="{download_filename}" style="text-decoration:none;">'+\
            '<div style="background-color: #0066cc; color: white; padding: 12px 24px; border-radius: 8px; cursor: pointer; display: inline-block; text-align: center; width: 100%; font-weight: bold;">'+\
            '<i class="fas fa-download" style="margin-right: 8px;"></i>Télécharger le rapport PDF</div></a>'

        st.markdown(href, unsafe_allow_html=True)

        st.info("Ce rapport contient un résumé des statistiques principales, le graphique de répartition des matériaux et les détails des motifs de découpe.")       

# Dans la section de calcul des statistiques pour l'optimisation par surface:
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
                total_surface_achetee = total_plaques * Long * largeur_totale if total_plaques > 0 else 1
                total_waste_surface = sum(pattern['waste_surface'] for pattern in surface_patterns)
                # Protection contre la division par zéro
                taux_perte_surface = sum(pattern['waste_percentage'] for pattern in surface_patterns) / total_plaques if total_plaques > 0 else 0
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
                fig_pie.update_layout(title="Répartition de l'utilisation des matériaux")
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Visualisation des découpes 2D
                st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Visualisation des découpes 2D
            </h3>
        """, unsafe_allow_html=True)
                
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
                        line=dict(color="black", width=2),
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
                                line=dict(color="blue", width=1),
                                fillcolor="rgba(0, 100, 255, 0.5)"
                            )
                            
                            # Ajouter le texte avec les dimensions et type
                            piece_label = format_piece_label(piece_L, type_profile, type_detail, piece_l)
                            fig.add_annotation(
                                x=(x0 + x1) / 2,
                                y=(y0 + y1) / 2,
                                text=piece_label,
                                showarrow=False,
                                font=dict(color="white", size=12)
                            )
                    
                    fig.update_layout(
                        title=f"Plaque {i+1} - {plaque_L}×{plaque_l} mm ({type_detail})",
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
                
                # Synthèse des motifs uniques pour les tôles

                # MODIFICATION 2 : Pour le code similaire dans la section d'optimisation par surface (vers la ligne ~990)
                # Remplacez le code équivalent pour les motifs uniques de tôles par:

                # Synthèse des motifs uniques pour les tôles
                unique_patterns = get_unique_patterns(surface_patterns)

                st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Synthèse des motifs de découpe
            </h3>
        """, unsafe_allow_html=True)


                # Tri des motifs uniques par fréquence décroissante
                unique_patterns.sort(key=lambda x: x['count'], reverse=True)

                for i, unique_pattern in enumerate(unique_patterns):
                    st.markdown(f"""
                        <div style="border: 2px solid #2196F3; border-radius: 12px; padding: 10px; margin-bottom: 15px; background-color: #E3F2FD;">
                            <div style="font-weight: bold; font-size: 18px; color: #0D47A1; margin-bottom: 10px;">
                                Motif #{i+1} - Utilisé {unique_pattern['count']} fois
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Création d'un graphique pour chaque motif unique
                    fig_pattern = go.Figure()
                    
                    dimensions = unique_pattern['dimensions']
                    pattern_config = unique_pattern['pattern']
                    
                    plaque_L = dimensions['plaque']['L']
                    plaque_l = dimensions['plaque']['l']
                    piece_L = dimensions['piece']['L']
                    piece_l = dimensions['piece']['l']
                    h = pattern_config['h']
                    v = pattern_config['v']
                    
                    # Dessiner la plaque de base
                    fig_pattern.add_shape(
                        type="rect",
                        x0=0, y0=0,
                        x1=plaque_L, y1=plaque_l,
                        line=dict(color="black", width=2),
                        fillcolor="rgba(200, 200, 200, 0.3)"
                    )
                    
                    # Dessiner les pièces découpées
                    for row in range(v):
                        for col in range(h):
                            x0 = col * piece_L
                            y0 = row * piece_l
                            x1 = x0 + piece_L
                            y1 = y0 + piece_l
                            
                            fig_pattern.add_shape(
                                type="rect",
                                x0=x0, y0=y0,
                                x1=x1, y1=y1,
                                line=dict(color="blue", width=1),
                                fillcolor="rgba(0, 100, 255, 0.5)"
                            )
                            
                            # Ajouter le texte avec les dimensions
                            piece_label = format_piece_label(piece_L, type_profile, type_detail, piece_l)
                            fig_pattern.add_annotation(
                                x=(x0 + x1) / 2,
                                y=(y0 + y1) / 2,
                                text=piece_label,
                                showarrow=False,
                                font=dict(color="white", size=12)
                            )
                    
                    # Création d'un layout à colonnes pour le graphique et les informations
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        fig_pattern.update_layout(
                            title=f"Motif de découpe #{i+1} (×{unique_pattern['count']}) - {h}×{v} pièces",
                            xaxis_title="Longueur (mm)",
                            yaxis_title="Largeur (mm)",
                            width=800,
                            height=500,
                            showlegend=False,
                            xaxis=dict(
                                range=[0, plaque_L],
                                constrain="domain"
                            ),
                            yaxis=dict(
                                range=[0, plaque_l], 
                                scaleanchor="x", 
                                scaleratio=1
                            ),
                            margin=dict(l=50, r=50, t=70, b=50),
                            plot_bgcolor='rgba(240, 240, 240, 0.5)'
                        )
                        
                        st.plotly_chart(fig_pattern)
                    
                    with col2:
                        st.markdown("<h4 style='text-align: center; color: #0D47A1;'>Détails</h4>", unsafe_allow_html=True)
                        st.markdown(f"""
                            <div style='padding: 10px; background-color: #E3F2FD; border-radius: 5px; margin-bottom: 10px;'>
                                <p><b>Dimensions:</b> {piece_L}×{piece_l} mm</p>
                                <p><b>Disposition:</b> {h} × {v} pièces</p>
                                <p><b>Total:</b> {h*v} pièces par plaque</p>
                                <p><b>Chute:</b> {unique_pattern['waste_percentage']:.2f}%</p>
                            </div>
                        """, unsafe_allow_html=True)

                    
                    # Détails du motif
                    perte = unique_pattern['waste_percentage']
                    st.info(f"Composition: {h}×{v} pièces de {piece_L}×{piece_l} mm, Chute: {perte:.2f}%")
                
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
                
                # Préparation pour le rendu avec des labels détaillés
                formatted_labels = [format_piece_label(l, type_profile, type_detail) for l in longueurs]
                label_map = {l: formatted_labels[i] for i, l in enumerate(longueurs)}
                
                # Visualisation des découpes
                st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Visualisation des découpes
            </h3>
        """, unsafe_allow_html=True)
                
                couleurs_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                couleur_map = {l: couleurs_palette[i % len(couleurs_palette)] for i, l in enumerate(sorted(set(longueurs)))}

                fig = go.Figure()

                for i, pattern in enumerate(surface_patterns):
                    x_pos = 0
                    for j, piece_length in enumerate(pattern['cuts']):
                        # Ajouter une pièce
                        fig.add_trace(go.Bar(
                            x=[piece_length],
                            y=[i],
                            width=0.7,
                            name=label_map[piece_length],
                            orientation='h',
                            text=label_map[piece_length],
                            textposition='inside',
                            marker=dict(color=couleur_map[piece_length]),
                            base=x_pos
                        ))
                        x_pos += piece_length
                        
                        # Ajouter un séparateur après chaque pièce sauf la dernière
                        if j < len(pattern['cuts']) - 1:
                            fig.add_trace(go.Bar(
                                x=[5],  # largeur de 5mm pour le séparateur
                                y=[i],
                                width=0.7,
                                orientation='h',
                                marker=dict(color='black'),
                                showlegend=False if j > 0 or i > 0 else True,
                                name="Séparateur" if j == 0 and i == 0 else None,
                                base=x_pos
                            ))
                            x_pos += 5  # Ajustement après le séparateur

                    # Ajouter la chute à la fin
                    if pattern['waste_length'] > 0:
                        fig.add_trace(go.Bar(
                            x=[pattern['waste_length']],
                            y=[i],
                            width=0.7,
                            name='Chute',
                            orientation='h',
                            text=f"Chute: {pattern['waste_length']} mm",
                            textposition='inside',
                            marker=dict(color='#505050', opacity=0.7),
                            base=x_pos
                        ))

                fig.update_layout(
                    barmode='stack',
                    title_text=f'Découpe optimisée de toutes les barres ({type_profile} {type_detail})',
                    xaxis_title='Longueur (mm)',
                    yaxis=dict(
                        tickvals=list(range(len(surface_patterns))),
                        ticktext=[f"Barre {i+1} - Chute surface: {pattern['waste_percentage']:.2f}%" for i, pattern in enumerate(surface_patterns)]
                    ),
                    height=200 + 50 * len(surface_patterns),
                    legend_title_text='Sections'
                )

                st.plotly_chart(fig, use_container_width=True)
                
                # Analyse et visualisation des motifs uniques

                # MODIFICATION 3 : Pour le code de la synthèse des motifs dans la partie UPN/Cornière (vers la ligne ~1180)
                # Remplacez le code par:

                # Analyse et visualisation des motifs uniques
                unique_patterns = get_unique_patterns(surface_patterns)

                st.markdown("""
            <h3 style="color:blue; background-color:#E3F2FD; padding:8px; border-radius:8px;">
                Synthèse des motifs de découpe
            </h3>
        """, unsafe_allow_html=True)


                # Tri des motifs uniques par fréquence décroissante
                unique_patterns.sort(key=lambda x: x['count'], reverse=True)

                for i, unique_pattern in enumerate(unique_patterns):
 
                    
                    # Création d'un graphique pour chaque motif unique avec barmode='stack'
                    fig_pattern = go.Figure()
                    
                    x_pos = 0
                    for j, piece_length in enumerate(unique_pattern['pattern']):
                        # Ajouter une pièce
                        fig_pattern.add_trace(go.Bar(
                            x=[piece_length],
                            y=[0],
                            width=0.7,
                            name=label_map[piece_length],
                            orientation='h',
                            text=label_map[piece_length],
                            textposition='inside',
                            marker=dict(color=couleur_map[piece_length]),
                            base=x_pos
                        ))
                        x_pos += piece_length
                        
                        # Ajouter un séparateur après chaque pièce sauf la dernière
                        if j < len(unique_pattern['pattern']) - 1:
                            fig_pattern.add_trace(go.Bar(
                                x=[5],
                                y=[0],
                                width=0.7,
                                orientation='h',
                                marker=dict(color='black'),
                                showlegend=j == 0,
                                name="Séparateur" if j == 0 else None,
                                base=x_pos
                            ))
                            x_pos += 5
                    
                    # Ajouter la chute à la fin si présente
                    if 'waste' in unique_pattern:
                        waste = unique_pattern['waste']
                        if waste > 0:
                            fig_pattern.add_trace(go.Bar(
                                x=[waste],
                                y=[0],
                                width=0.7,
                                name='Chute',
                                orientation='h',
                                text=f"Chute: {waste} mm",
                                textposition='inside',
                                marker=dict(color='#505050', opacity=0.7),
                                base=x_pos
                            ))
                    
                    # Création d'un layout à colonnes pour le graphique et les détails
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        fig_pattern.update_layout(
                            barmode='stack',  # Important pour l'alignement correct
                            title_text=f"Motif de découpe #{i+1} (×{unique_pattern['count']})",
                            xaxis_title='Longueur (mm)',
                            yaxis=dict(
                                showticklabels=False,
                            ),
                            height=200,
                            legend_title_text='Sections',
                            xaxis=dict(range=[0, Long]),
                            margin=dict(l=50, r=50, t=70, b=50),
                            plot_bgcolor='rgba(240, 240, 240, 0.5)'
                        )
                        
                        st.plotly_chart(fig_pattern, use_container_width=True)
                    
                    with col2:
                        st.markdown("<h4 style='text-align: center; color: #0D47A1;'>Détails</h4>", unsafe_allow_html=True)
                        
                        # Détails du motif
                        pieces_count = Counter(unique_pattern['pattern'])
                        
                        for piece, count in pieces_count.items():
                            st.markdown(f"""
                                <div style='padding: 5px; margin: 5px 0; background-color: {couleur_map[piece]}; 
                                    color: white; border-radius: 5px; text-align: center;'>
                                    {count}× {label_map[piece]}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        if 'waste' in unique_pattern and unique_pattern['waste'] > 0:
                            st.markdown(f"""
                                <div style='padding: 5px; margin: 5px 0; background-color: #505050; 
                                    color: white; border-radius: 5px; text-align: center;'>
                                    Chute: {unique_pattern['waste']} mm
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Détails du motif
                    #pieces_count = Counter(unique_pattern['pattern'])
                    #pieces_details = [f"{count}× {label_map[piece]}" for piece, count in pieces_count.items()]
                    #if 'waste' in unique_pattern:
                    #    st.info(f"Composition: {', '.join(pieces_details)}, Chute: {unique_pattern['waste']} mm")
                    #else:
                    #    st.info(f"Composition: {', '.join(pieces_details)}")
                
                # Affichage des informations de chutes de surface
                st.subheader("Détails des chutes de surface")
                for i, pattern in enumerate(surface_patterns):
                    st.info(f"Barre {i+1}: Chute en longueur = {pattern['waste_length']} mm, " +
                            f"Chute en surface = {pattern['waste_surface']:.4f} m² ({pattern['waste_percentage']:.2f}%)")