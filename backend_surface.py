# backend_surface.py
import itertools
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpInteger, value

def calculer_surface_profile(profile_type, type_detail, longueur):
    longueur_m = longueur / 1000  # Conversion en mètres
    if profile_type == "UPN":
        surface_par_metre = {"UPN80": 0.312, "UPN100": 0.392, "UPN120": 0.448, "UPN140": 0.512}
        return surface_par_metre.get(type_detail, 0.312) * longueur_m
    elif profile_type == "Cornière":
        surface_par_metre = {"70": 0.272, "60": 0.226, "45": 0.168, "40": 0.150}
        return surface_par_metre.get(type_detail, 0.226) * longueur_m
    elif profile_type == "Tôle/Platine":
        return None
    return 0

def generer_patterns_surface(longueurs, largeurs, quantites, profile_type, type_detail, L, largeur_totale=None):
    if profile_type == "Tôle/Platine" and largeur_totale:
        patterns = []
        for orientation in [(0, 1), (1, 0)]:
            for i, l in enumerate(longueurs):
                for j, w in enumerate(largeurs):
                    piece_l, piece_w = (l, w) if orientation == (0,1) else (w, l)
                    if piece_l > L or piece_w > largeur_totale:
                        continue
                    max_horizontal = L // piece_l
                    max_vertical = largeur_totale // piece_w
                    for h in range(1, max_horizontal + 1):
                        for v in range(1, max_vertical + 1):
                            pattern = [[0 for _ in range(len(largeurs))] for _ in range(len(longueurs))]
                            pattern[i][j] = h * v
                            surface_utilisee = piece_l * piece_w * h * v
                            surface_totale = L * largeur_totale
                            waste = surface_totale - surface_utilisee
                            patterns.append((pattern, waste, h, v, piece_l, piece_w, orientation == (1,0)))
        return patterns
    else:
        return generer_patterns_longueur(longueurs, L)

def generer_patterns_longueur(longueurs, L):
    patterns = []
    max_coupes = [L // l for l in longueurs]
    for n_coupes in itertools.product(*[range(max_coupes[i]+1) for i in range(len(longueurs))]):
        longueur_totale = sum(n_coupes[i] * longueurs[i] for i in range(len(longueurs)))
        if 0 < longueur_totale <= L:
            patterns.append((n_coupes, L - longueur_totale))
    return patterns

def optimiser_decoupe_surface(longueurs, largeurs, quantites, profile_type, type_detail, L, largeur_totale=None, epaisseur=None):
    if profile_type == "Tôle/Platine" and largeur_totale:
        patterns = generer_patterns_surface(longueurs, largeurs, quantites, profile_type, type_detail, L, largeur_totale)
        prob = LpProblem("decoupe_surface", LpMinimize)
        x = [LpVariable(f"x_{i}", lowBound=0, cat=LpInteger) for i in range(len(patterns))]
        
        for i in range(len(longueurs)):
            for j in range(len(largeurs)):
                prob += lpSum(x[k] * patterns[k][0][i][j] for k in range(len(patterns))) >= quantites[i]
        
        prob += lpSum(x[i] * patterns[i][1] for i in range(len(patterns)))
        prob.solve()

        resultats = []
        for i in range(len(patterns)):
            quantite = int(value(x[i]))
            if quantite > 0:
                for _ in range(quantite):
                    _, waste, h, v, piece_l, piece_w, rotated = patterns[i]
                    surface_waste = waste / (L * largeur_totale) * 100
                    layout = []
                    for _ in range(v):
                        row = []
                        for _ in range(h):
                            dim = f"{piece_w}x{piece_l}" if rotated else f"{piece_l}x{piece_w}"
                            row.append(dim)
                        layout.append(row)
                    resultats.append({
                        'type': '2D',
                        'layout': layout,
                        'waste_surface': waste,
                        'waste_percentage': surface_waste,
                        'dimensions': {'plaque': {'L': L, 'l': largeur_totale}, 'piece': {'L': piece_l, 'l': piece_w, 'rotated': rotated}},
                        'pattern': {'h': h, 'v': v}
                    })
        return resultats
    else:
        patterns = generer_patterns_longueur(longueurs, L)
        prob = LpProblem("decoupe", LpMinimize)
        x = [LpVariable(f"x_{i}", lowBound=0, cat=LpInteger) for i in range(len(patterns))]

        for j, l in enumerate(longueurs):
            prob += lpSum(x[i] * patterns[i][0][j] for i in range(len(patterns))) >= quantites[j]

        prob += lpSum(x[i] for i in range(len(patterns)))
        prob.solve()

        resultats = []
        for i in range(len(patterns)):
            quantite = int(value(x[i]))
            if quantite > 0:
                coupure = []
                for j, n in enumerate(patterns[i][0]):
                    coupure.extend([longueurs[j]] * n)
                for _ in range(quantite):
                    surface_totale = calculer_surface_profile(profile_type, type_detail, L)
                    surface_utilisee = sum(calculer_surface_profile(profile_type, type_detail, l) for l in coupure)
                    waste_surface = surface_totale - surface_utilisee if surface_totale else 0
                    resultats.append({
                        'type': '1D',
                        'cuts': coupure,
                        'waste_length': patterns[i][1],
                        'waste_surface': waste_surface,
                        'waste_percentage': (waste_surface / surface_totale * 100) if surface_totale else 0
                    })
        return resultats
