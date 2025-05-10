# 1. First, add these imports at the top of your file
import base64
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 2. Add this function somewhere after your imports and before your main code
class BarCutDiagram(Flowable):
    """Flowable qui dessine un diagramme de découpe de barre"""
    def __init__(self, pattern, lengths, labels, total_length, width=500, height=60):
        Flowable.__init__(self)
        self.pattern = pattern
        self.lengths = lengths
        self.labels = labels
        self.total_length = total_length
        self.width = width
        self.height = height
        self.colors = {
            'cuts': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
            'waste': '#707070',
            'separator': '#000000'
        }
    
    def draw(self):
        """Dessine le diagramme"""
        # Calcul de l'échelle
        scale = self.width / self.total_length
        
        # Dessiner la barre
        x_pos = 0
        separator_width = 5
        
        # Pour chaque pièce dans le motif
        for i, length in enumerate(self.pattern):
            color_idx = i % len(self.colors['cuts'])
            piece_width = scale * length
            
            # Dessiner le rectangle de la pièce
            self.canv.setFillColor(colors.HexColor(self.colors['cuts'][color_idx]))
            self.canv.rect(x_pos, 0, piece_width, self.height, fill=1)
            
            # Ajouter le texte si assez d'espace
            if piece_width > 40:
                self.canv.setFillColor(colors.white)
                self.canv.setFont("Helvetica", 8)
                label = self.labels.get(length, f"{length}mm")
                text_width = self.canv.stringWidth(label, "Helvetica", 8)
                if text_width < piece_width - 4:
                    self.canv.drawCentredString(x_pos + piece_width/2, self.height/2 - 4, label)
            
            x_pos += piece_width
            
            # Ajouter un séparateur si ce n'est pas la dernière pièce
            if i < len(self.pattern) - 1:
                self.canv.setFillColor(colors.black)
                self.canv.rect(x_pos, 0, scale * separator_width, self.height, fill=1)
                x_pos += scale * separator_width
        
        # Dessiner la chute à la fin si elle existe
        waste = self.total_length - sum(self.pattern) - (len(self.pattern) - 1) * separator_width
        if waste > 0:
            waste_width = scale * waste
            self.canv.setFillColor(colors.HexColor(self.colors['waste']))
            self.canv.rect(x_pos, 0, waste_width, self.height, fill=1)
            
            # Ajouter le texte de chute si assez d'espace
            if waste_width > 40:
                waste_text = f"Chute: {waste}mm"
                text_width = self.canv.stringWidth(waste_text, "Helvetica", 8)
                if text_width < waste_width - 4:
                    self.canv.setFillColor(colors.white)
                    self.canv.drawCentredString(x_pos + waste_width/2, self.height/2 - 4, waste_text)

class PlateCutDiagram(Flowable):
    """Flowable qui dessine un diagramme de découpe de tôle/platine"""
    def __init__(self, dimensions, pattern, width=500, height=350):
        Flowable.__init__(self)
        self.plate_L = dimensions['plaque']['L']
        self.plate_l = dimensions['plaque']['l']
        self.piece_L = dimensions['piece']['L']
        self.piece_l = dimensions['piece']['l']
        self.h = pattern['h']
        self.v = pattern['v']
        self.width = width
        self.height = height
        self.scale = min(width / self.plate_L, height / self.plate_l)
    
    def draw(self):
        """Dessine le diagramme de découpe de tôle"""
        # Dessiner la plaque de base
        self.canv.setFillColor(colors.HexColor('#f0f0f0'))
        self.canv.setStrokeColor(colors.black)
        self.canv.rect(0, 0, self.scale * self.plate_L, self.scale * self.plate_l, fill=1, stroke=1)
        
        # Dessiner les pièces découpées
        self.canv.setFillColor(colors.HexColor('#1f77b4'))
        
        for row in range(self.v):
            for col in range(self.h):
                x0 = col * self.piece_L * self.scale
                y0 = row * self.piece_l * self.scale
                self.canv.rect(x0, y0, self.piece_L * self.scale, self.piece_l * self.scale, fill=1, stroke=1)

def create_download_report(patterns, type_profile, type_detail, Long, 
                           largeur_totale=None, taux_perte=None, taux_efficacite=None, 
                           unique_patterns=None, epaisseur=None, is_surface_optim=False,
                           longueurs=None, largeurs=None, quantites=None, noms=None):
    """
    Crée un rapport PDF téléchargeable avec les résultats d'optimisation
    avec une meilleure esthétique et plus d'informations
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, 
                           topMargin=20, bottomMargin=20)
    story = []
    
    # Définition des styles avec couleur bleue pour les titres
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#264CA8'),
        spaceAfter=10,
        alignment=1  # Centre
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#0066CC'),
        spaceBefore=15,
        spaceAfter=10,
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=6,
        spaceAfter=6
    )
    
    # En-tête du document
    title_text = f"Rapport d'optimisation de découpe - {type_profile} {type_detail}"
    if type_profile == "Tôle/Platine" and epaisseur is not None:
        title_text += f" - Épaisseur {epaisseur} mm"
    title = Paragraph(title_text, title_style)
    story.append(title)
    
    # Informations sur le type d'optimisation
    optim_type = "par surface" if is_surface_optim else "par longueur"
    subtitle = Paragraph(f"Type d'optimisation : {optim_type.capitalize()}", subtitle_style)
    story.append(subtitle)
    story.append(Spacer(1, 12))
    
    # 1. Tableau des longueurs demandées
    story.append(Paragraph("Longueurs demandées", subtitle_style))
    
    if type_profile == "Tôle/Platine":
        # Cas des tôles - inclut largeur
        headers = ['ID', 'Longueur (mm)', 'Largeur (mm)', 'Quantité']
        data = [headers]
        for i, (long, larg, quant) in enumerate(zip(longueurs, largeurs, quantites)):
            name = noms[i] if noms and i < len(noms) else f"Pièce {i+1}"
            data.append([name, f"{long}", f"{larg}", f"{quant}"])
    else:
        # Cas des UPN et cornières - sans largeur
        headers = ['ID', 'Longueur (mm)', 'Quantité']
        data = [headers]
        for i, (long, quant) in enumerate(zip(longueurs, quantites)):
            name = noms[i] if noms and i < len(noms) else f"{type_profile} {type_detail} - {i+1}"
            data.append([name, f"{long}", f"{quant}"])
    
    lengths_table = Table(data, colWidths=[doc.width/len(headers) for _ in headers])
    lengths_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#264CA8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))
    story.append(lengths_table)
    
    # 2. Statistiques de l'optimisation
    story.append(Paragraph("Statistiques de l'optimisation", subtitle_style))
    
    # Tableaux des statistiques
    if is_surface_optim and type_profile == "Tôle/Platine":
        # Cas des tôles/platines - statistiques de surface uniquement
        stats_data = [
            ['Statistique', 'Valeur'],
            ['Nombre de plaques utilisées', f"{len(patterns)}"],
            ['Dimensions des plaques', f"{Long} × {largeur_totale} mm"],
            ['Surface totale achetée', f"{len(patterns) * Long * largeur_totale / 1000000:.2f} m²"],
            ['Taux de perte', f"{taux_perte:.2f}%"],
            ['Taux d\'efficacité', f"{taux_efficacite:.2f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[doc.width/2 for _ in range(2)])
        
    elif is_surface_optim:
        # Cas UPN/Cornière avec optimisation surface - double tableau
        stats_length = [
            ['Statistique (Longueur)', 'Valeur'],
            ['Nombre de barres utilisées', f"{len(patterns)}"],
            ['Longueur standard', f"{Long} mm"],
            ['Longueur totale achetée', f"{len(patterns) * Long} mm"],
            ['Taux de perte (longueur)', f"{taux_perte:.2f}%"],
            ['Taux d\'efficacité (longueur)', f"{taux_efficacite:.2f}%"]
        ]
        
        stats_surface = [
            ['Statistique (Surface)', 'Valeur'],
            ['Surface totale achetée', f"{len(patterns) * Long * calculer_section(type_profile, type_detail) / 1000000:.4f} m²"],
            ['Surface utile', f"{sum((Long - p['waste_length']) * calculer_section(type_profile, type_detail) for p in patterns) / 1000000:.4f} m²"],
            ['Surface de chute', f"{sum(p['waste_surface'] for p in patterns):.4f} m²"],
            ['Taux de perte (surface)', f"{sum(p['waste_percentage'] for p in patterns) / len(patterns):.2f}%"],
            ['Taux d\'efficacité (surface)', f"{100 - sum(p['waste_percentage'] for p in patterns) / len(patterns):.2f}%"]
        ]
        
        # Créer une table à deux colonnes
        stats_length_table = Table(stats_length, colWidths=[doc.width/4-5, doc.width/4-5])
        stats_surface_table = Table(stats_surface, colWidths=[doc.width/4-5, doc.width/4-5])
        
        combined_data = []
        for i in range(max(len(stats_length), len(stats_surface))):
            row = []
            if i < len(stats_length):
                row.extend(stats_length[i])
            else:
                row.extend(['', ''])
            row.append('')  # séparateur
            if i < len(stats_surface):
                row.extend(stats_surface[i])
            else:
                row.extend(['', ''])
            combined_data.append(row)
        
        stats_table = Table(combined_data, colWidths=[doc.width/4-5, doc.width/4-5, 10, doc.width/4-5, doc.width/4-5])
        
    else:
        # Cas standard - optimisation par longueur
        stats_data = [
            ['Statistique', 'Valeur'],
            ['Nombre de barres utilisées', f"{len(patterns)}"],
            ['Longueur standard', f"{Long} mm"],
            ['Longueur totale achetée', f"{len(patterns) * Long} mm"],
            ['Longueur totale utilisée', f"{sum(sum(p['cuts']) for p in patterns)} mm"],
            ['Longueur totale de chute', f"{sum(p['waste'] for p in patterns)} mm"],
            ['Taux de perte', f"{taux_perte:.2f}%"],
            ['Taux d\'efficacité', f"{taux_efficacite:.2f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[doc.width/2 for _ in range(2)])
    
    # Style commun pour tous les tableaux de statistiques
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#264CA8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT')
    ]))
    
    if is_surface_optim and type_profile != "Tôle/Platine":
        # Style spécifique pour le tableau combiné
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#264CA8')),
            ('BACKGROUND', (3, 0), (4, 0), colors.HexColor('#264CA8')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('TEXTCOLOR', (3, 0), (4, 0), colors.white),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('ALIGN', (3, 0), (4, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (4, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (1, -1), 0.5, colors.grey),
            ('GRID', (3, 0), (4, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (4, -1), 'MIDDLE'),
            ('SPAN', (2, 0), (2, -1)),  # fusionner la colonne du séparateur
        ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 15))
    
    # 3. Graphiques de répartition (camembert)
    story.append(Paragraph("Répartition de l'utilisation des matériaux", subtitle_style))
    
    # Création du/des graphique(s) avec matplotlib
    if is_surface_optim and type_profile != "Tôle/Platine":
        # Double camembert pour longueur et surface
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
        
        # Camembert de longueur
        total_longueur = len(patterns) * Long
        total_waste_length = sum(p['waste_length'] for p in patterns)
        lengths = [total_longueur - total_waste_length, total_waste_length]
        ax1.pie(lengths, labels=['Utilisé', 'Perte'], autopct='%1.1f%%',
                colors=['#2ca02c', '#707070'], startangle=90)
        ax1.set_title("Répartition de la longueur", color='#264CA8')
        ax1.axis('equal')
        
        # Camembert de surface
        total_surface = len(patterns) * Long * calculer_section(type_profile, type_detail) / 1000
        total_waste_surface = sum(p['waste_surface'] for p in patterns)
        surfaces = [total_surface - total_waste_surface, total_waste_surface]
        ax2.pie(surfaces, labels=['Utilisé', 'Perte'], autopct='%1.1f%%',
                colors=['#2ca02c', '#707070'], startangle=90)
        ax2.set_title("Répartition de la surface", color='#264CA8')
        ax2.axis('equal')
        
    else:
        # Simple camembert
        fig, ax = plt.subplots(figsize=(6, 4))
        
        if is_surface_optim and type_profile == "Tôle/Platine":
            # Camembert pour la surface des tôles
            total_surface = len(patterns) * Long * largeur_totale
            total_waste_surface = sum(p['waste_surface'] for p in patterns)
            data = [total_surface - total_waste_surface, total_waste_surface]
            ax.pie(data, labels=['Utilisé', 'Perte'], autopct='%1.1f%%',
                   colors=['#2ca02c', '#707070'], startangle=90)
            ax.set_title("Répartition de la surface", color='#264CA8')
        else:
            # Camembert pour la longueur standard
            total_longueur_utilisee = sum(sum(p['cuts']) for p in patterns)
            total_waste = sum(p['waste'] for p in patterns)
            data = [total_longueur_utilisee, total_waste]
            ax.pie(data, labels=['Utilisé', 'Perte'], autopct='%1.1f%%',
                   colors=['#2ca02c', '#707070'], startangle=90)
            ax.set_title("Répartition de la longueur", color='#264CA8')
        
        ax.axis('equal')
    
    # Sauvegarder le graphique et l'ajouter au PDF
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    img_buffer.seek(0)
    img = Image(img_buffer, width=400, height=200)
    story.append(img)
    story.append(Spacer(1, 10))
    
    # 4. Synthèse des motifs de découpe
    story.append(Paragraph("Synthèse des motifs de découpe", subtitle_style))
    
    # Création d'une table pour présenter les motifs
    if unique_patterns:
        # Trier les motifs par fréquence décroissante
        unique_patterns.sort(key=lambda x: x['count'], reverse=True)
        
        # Créer un dictionnaire pour mapper les longueurs à leurs labels
        label_map = {}
        if longueurs and noms:
            for i, (long, nom) in enumerate(zip(longueurs, noms)):
                nom_long = f"{nom}" if nom else f"Pièce {i+1}"
                if type_profile == "Tôle/Platine" and largeurs:
                    label_map[long] = f"[{nom_long}] {long}×{largeurs[i]}mm"
                else:
                    label_map[long] = f"[{nom_long}] {long}mm"
        
        for i, pattern in enumerate(unique_patterns):
            motif_title = Paragraph(f"Motif #{i+1} - Utilisé {pattern['count']} fois", subtitle_style)
            story.append(motif_title)
            
            if type_profile == "Tôle/Platine" and 'dimensions' in pattern:
                # Motif de découpe de tôle/platine
                dimensions = pattern['dimensions']
                pattern_config = pattern['pattern']
                
                plate_diagram = PlateCutDiagram(dimensions, pattern_config, width=400, height=250)
                story.append(plate_diagram)
                
                # Informations sur le motif
                info_data = [
                    ['Dimensions pièce', f"{dimensions['piece']['L']}×{dimensions['piece']['l']} mm"],
                    ['Disposition', f"{pattern_config['h']}×{pattern_config['v']} pièces"],
                    ['Total', f"{pattern_config['h'] * pattern_config['v']} pièces par plaque"],
                    ['Taux de perte', f"{pattern['waste_percentage']:.2f}%"]
                ]
                
                info_table = Table(info_data, colWidths=[120, 150])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6)
                ]))
                story.append(info_table)
            else:
                # Motif de découpe standard (UPN, Cornière)
                if 'pattern' in pattern:
                    cuts = pattern['pattern']
                    waste = pattern.get('waste', 0)
                    
                    # Création du diagramme de découpe
                    bar_diagram = BarCutDiagram(cuts, longueurs, label_map, Long, width=400, height=50)
                    story.append(bar_diagram)
                    
                    # Tableau de détails des pièces
                    pieces_count = Counter(cuts)
                    detail_data = [['Pièce', 'Quantité']]
                    
                    for piece, count in pieces_count.items():
                        detail_data.append([label_map.get(piece, f"{piece}mm"), f"{count}"]) 
                    
                    if waste > 0:
                        detail_data.append(['Chute', f"{waste} mm"])
                    
                    detail_table = Table(detail_data, colWidths=[300, 100])
                    detail_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#264CA8')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER')
                    ]))
                    story.append(detail_table)
            
            story.append(Spacer(1, 15))
    
    # Construction du document final
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Encodage en base64 pour le téléchargement
    b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    return b64_pdf

def calculer_section(profile_type, type_detail):
    """Fonction helper pour calculer la section d'un profilé"""
    if profile_type == "UPN":
        sections = {"UPN80": 11, "UPN100": 13.5, "UPN120": 17, "UPN140": 20.4}
        return sections.get(type_detail, 11)
    elif profile_type == "Cornière":
        sections = {"70": 10.6, "60": 9.2, "45": 6.8, "40": 6.0}
        return sections.get(type_detail, 9.2)
    return 1  # Valeur par défaut



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
noms = []  # Nouvelle liste pour les noms/identifiants

for i in range(n):
    st.markdown(f"### Paramètres de la coupe {i+1}")
    
    # Disposition en colonnes pour tous les champs
    if type_profile == "Tôle/Platine":
        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
        
        l = col1.number_input(f"Longueur {i+1} (mm) :", min_value=100, step=100, key=f"long_{i}", value=1000+i*500)
        w = col2.number_input(f"Largeur {i+1} (mm) :", min_value=100, step=100, key=f"larg_{i}", value=300+i*100)
        q = col3.number_input(f"Quantité {i+1} :", min_value=1, step=1, key=f"quant_{i}", value=2)
        nom = col4.text_input(f"Identifiant {i+1} :", key=f"nom_{i}", value=f"Pièce {i+1}")
        
        largeurs.append(w)
    else:
        col1, col2, col3 = st.columns([2, 1, 2])
        
        l = col1.number_input(f"Longueur {i+1} (mm) :", min_value=100, step=100, key=f"long_{i}", value=1000+i*500)
        q = col2.number_input(f"Quantité {i+1} :", min_value=1, step=1, key=f"quant_{i}", value=2)
        nom = col3.text_input(f"Identifiant {i+1} :", key=f"nom_{i}", value=f"Pièce {i+1}")
        
        largeurs.append(None)
    
    longueurs.append(l)
    quantites.append(q)
    noms.append(nom)

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
                longueurs=longueurs,  # Ajout des paramètres manquants
                largeurs=largeurs,
                quantites=quantites,
                noms=noms
            )
            download_filename = f"decoupe_{type_profile}_{type_detail}.pdf"

        elif optim_type == "Optimisation par surface":
            if type_profile == "Tôle/Platine":
                pdf_base64 = create_download_report(
                    patterns=patterns,
                    type_profile=type_profile,
                    type_detail=type_detail,
                    Long=Long,
                    largeur_totale=largeur_totale,
                    taux_perte=taux_perte,
                    taux_efficacite=taux_efficacite,
                    unique_patterns=unique_patterns,
                    epaisseur=epaisseur,
                    is_surface_optim=True,
                    longueurs=longueurs,  # Ajout des paramètres manquants
                    largeurs=largeurs,
                    quantites=quantites,
                    noms=noms
                )
                download_filename = f"decoupe_tole_{epaisseur}mm.pdf"
            else:
                pdf_base64 = create_download_report(
                    patterns=patterns,
                    type_profile=type_profile,
                    type_detail=type_detail,
                    Long=Long,
                    taux_perte=taux_perte,
                    taux_efficacite=100 - taux_perte,
                    unique_patterns=unique_patterns,
                    longueurs=longueurs,  # Ajout des paramètres manquants
                    largeurs=largeurs,
                    quantites=quantites,
                    noms=noms,
                    is_surface_optim=True  # Important pour les UPN/Cornière en optimisation surface
                )
                download_filename = f"decoupe_{type_profile}_{type_detail}.pdf"
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