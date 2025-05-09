# backend_dcg.py

from docplex.mp.model import Model
import random

def generer_pattern_initial(longueurs, quantites, L):
    """
    Génère un pattern initial utilisant une heuristique gloutonne
    """
    patterns = []
    reste_quantites = quantites.copy()
    
    # Tant qu'il reste des pièces à découper
    while sum(reste_quantites) > 0:
        pattern = []
        reste_L = L
        
        # Essayer de remplir la barre actuelle
        for i, l in enumerate(longueurs):
            while reste_quantites[i] > 0 and reste_L >= l:
                pattern.append(l)
                reste_L -= l
                reste_quantites[i] -= 1
        
        if pattern:  # Si le pattern n'est pas vide
            patterns.append({
                'cuts': pattern,
                'waste': reste_L
            })
    
    return patterns

def calculer_couts_reduits(dual_values, longueurs, L):
    """
    Calcule le coût réduit pour chaque longueur et détermine si de nouveaux patterns doivent être générés
    """
    best_pattern = []
    best_value = 0
    reste_L = L
    
    # Trier les longueurs par valeur duale décroissante
    indices_tries = sorted(range(len(longueurs)), key=lambda i: dual_values[i] / longueurs[i], reverse=True)
    
    # Construire le pattern avec la meilleure valeur duale
    for i in indices_tries:
        while reste_L >= longueurs[i]:
            best_pattern.append(longueurs[i])
            reste_L -= longueurs[i]
            best_value += dual_values[i]
    
    # Si le coût réduit est positif, ajouter ce pattern
    if best_value > 1:  # 1 est le coût d'une nouvelle barre
        return True, best_pattern, reste_L
    
    return False, None, None

def optimiser_decoupe_dcg(longueurs, quantites, L=6000, max_iterations=100):
    """
    Optimise la découpe de barres en utilisant la méthode de génération de colonnes (DCG)
    """
    # Générer un ensemble initial de patterns
    patterns = generer_pattern_initial(longueurs, quantites, L)
    
    for iteration in range(max_iterations):
        # Résoudre le problème maître restreint
        mdl = Model("master_problem")
        x = [mdl.continuous_var(name=f"x_{i}") for i in range(len(patterns))]
        
        # Contraintes: satisfaire les quantités demandées
        for j, l in enumerate(longueurs):
            mdl.add_constraint(
                mdl.sum(x[i] * patterns[i]['cuts'].count(l) for i in range(len(patterns))) >= quantites[j],
                name=f"demand_{j}"
            )
        
        # Objectif: minimiser le nombre de barres utilisées
        mdl.minimize(mdl.sum(x[i] for i in range(len(patterns))))
        
        solution = mdl.solve()
        
        if not solution:
            break
        
        # Récupérer les valeurs duales
        dual_values = [mdl.dual_values(c) for c in mdl.iter_constraints()]
        
        # Générer un nouveau pattern avec un coût réduit positif
        has_new_pattern, new_pattern, waste = calculer_couts_reduits(dual_values, longueurs, L)
        
        if not has_new_pattern:
            break  # Aucun nouveau pattern à ajouter
        
        # Ajouter le nouveau pattern
        patterns.append({
            'cuts': new_pattern,
            'waste': waste
        })
    
    # Résoudre le problème final avec variables entières
    mdl = Model("final_problem")
    x = [mdl.integer_var(name=f"x_{i}") for i in range(len(patterns))]
    
    # Contraintes: satisfaire les quantités demandées
    for j, l in enumerate(longueurs):
        mdl.add_constraint(
            mdl.sum(x[i] * patterns[i]['cuts'].count(l) for i in range(len(patterns))) >= quantites[j]
        )
    
    # Objectif: minimiser le nombre de barres utilisées
    mdl.minimize(mdl.sum(x[i] for i in range(len(patterns))))
    
    solution = mdl.solve()
    
    resultats = []
    if solution:
        for i in range(len(patterns)):
            quantite = int(solution[x[i]])
            if quantite > 0:
                for _ in range(quantite):
                    resultats.append(patterns[i])
    
    return resultats