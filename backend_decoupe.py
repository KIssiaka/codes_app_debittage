# backend_decoupe_pulp.py

from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpInteger, PULP_CBC_CMD, value
import itertools

def generer_patterns(longueurs, L):
    patterns = []
    max_coupes = [L // l for l in longueurs]
    
    for n_coupes in itertools.product(*[range(max_coupes[i]+1) for i in range(len(longueurs))]):
        longueur_totale = sum(n_coupes[i] * longueurs[i] for i in range(len(longueurs)))
        if 0 < longueur_totale <= L:
            patterns.append((n_coupes, L - longueur_totale))
    return patterns

def optimiser_decoupe(longueurs, quantites, L=6000):
    patterns = generer_patterns(longueurs, L)
    
    # Création du modèle
    mdl = LpProblem("decoupe", LpMinimize)
    
    # Variables de décision (nombre d'utilisation de chaque pattern)
    x = [LpVariable(f"x_{i}", lowBound=0, cat=LpInteger) for i in range(len(patterns))]
    
    # Contraintes : satisfaire exactement les quantités demandées
    for j, l in enumerate(longueurs):
        mdl += lpSum(x[i] * patterns[i][0][j] for i in range(len(patterns))) == quantites[j]
    
    # Objectif : minimiser la somme des chutes
    mdl += lpSum(x[i] * patterns[i][1] for i in range(len(patterns)))
    
    # Résoudre
    solver = PULP_CBC_CMD(msg=0)  # msg=0 pour ne pas afficher les logs
    mdl.solve(solver)
    
    resultats = []
    if mdl.status == 1:  # status 1 = optimal
        for i in range(len(patterns)):
            quantite = int(value(x[i]))
            if quantite > 0:
                coupure = []
                for j, n in enumerate(patterns[i][0]):
                    coupure.extend([longueurs[j]] * n)  # répéter la longueur n fois
                for _ in range(quantite):  # répéter le pattern complet quantite fois
                    resultats.append({
                        'cuts': coupure,
                        'waste': patterns[i][1]
                    })
    return resultats

# Exemple de résultats
patterns = [
    {'cuts': [1500, 1200, 1300], 'waste': 200},
    {'cuts': [1600, 1400], 'waste': 800},
    # ...
]
