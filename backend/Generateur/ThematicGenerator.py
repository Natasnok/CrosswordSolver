import os
import platform
import requests
import random
from functools import lru_cache
from unidecode import unidecode
import importlib.util
import time
from ..config import *

wrapper_path = os.path.join(os.path.dirname(__file__), "Wizium", "Wrappers", "Python", "libWizium.py")

spec = importlib.util.spec_from_file_location("libWizium", wrapper_path)
libWizium = importlib.util.module_from_spec(spec)
spec.loader.exec_module(libWizium)

# Récupérer la classe Wizium
Wizium = libWizium.Wizium


# --------------------------------------------------------------------
# Charger la DLL et créer l'objet
# --------------------------------------------------------------------

base_dir = os.path.dirname(__file__)

if platform.system() == "Windows":
    lib_path = os.path.join(base_dir, "Wizium", "Binaries", "Windows", "libWizium_x64.dll")
else:
    lib_path = os.path.join(base_dir, "Wizium", "Binaries", "Linux", "libWizium_x64.so")

wiz = Wizium(lib_path)

#Variable globale
LIM_MIN = 12000
LIM_MAX = 20000

#Sauvegardera les type de relation avec l'attribut playable a 1
type_relation = []

#Les types de noueds présents dans JDM qui peuvent etres interessant
type_noeud = [1, 2, 5, 0]

#Pour les nodes qui seront deja visisites, evite les doublons
visited_nodes = set()

#pour les nodes que l'on a deja utilise dans les requetes
request_nodes = set()

#Contient les ids des nodes a eviter comme : _COM ou _SW (/!\ Il y en a surement d'autre que je n'ai pas trouve, ils ont le type 36)
node_a_eviter = [239128, 2983124]

#On extrait toutes les relations qui ont playable à 1 afin de récupérer les mots qui ont des relations intéressante
def RelationJouableId():
    type_relation = []
    url = "https://jdm-api.demo.lirmm.fr/v0/relations_types"
    response = requests.get(url, timeout=5)#timeout peur-etre pas necessaire
    relations = response.json()
    nb_relation = len(relations)
    for i in range(nb_relation -1):
        if relations[i]['playable'] == 1:
            type_relation.append(relations[i]['id'])
    return type_relation


#On récupère tous les ids des relations intéressantes (liste d'entiers)
type_relation = RelationJouableId()

def getMotsLong234():
    """Pour récupérer tous les mots de longueur 2 d'un dico déjà existant"""
    with open(DICO_PATH, "r", encoding="utf-8") as f:
        mots = f.read().split()
# Filtrer les mots de longueur 2, 3 ,4
    mots_2 = [mot for mot in mots if len(mot) == 2 or len(mot) == 3 or len(mot) == 4]
    return mots_2

def getNameNode(node_id):
    """Recupere le name d'un node a partir de son id"""
    node = getNode(node_id)
    return node['name'] if node and 'name' in node else ""

def getIdNode(node_name):
    """Recupere l'id d'un node a partir de son name"""
    node = getNodeByName(node_name)
    return node['id'] if node and 'id' in node else ""

@lru_cache(maxsize=None)
def getNodeByName(node_name):
    """Recupere le noeud a partir de son <nom> et on le met dans le cache"""
    url = f"https://jdm-api.demo.lirmm.fr/v0/node_by_name/{node_name}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

@lru_cache(maxsize=None)
def getNode(node_id):
    """Recupere un noeud a partir de son id, pour recuperer a partir du name il faut utiliser : getNodeByName(node_name)"""
    url = f"https://jdm-api.demo.lirmm.fr/v0/node_by_id/{node_id}"
    response = requests.get(url)
    if response.status_code != 200:
        print("erreur lors de la reception de la requete pour le noeud :", node_id)
        return None
    return response.json()

def getTypeRelation(relations, node2):
    """A partir d'une liste de relations et d'un id de noeud\n -> retourne le type de la relation avec le plus de poids"""    
    poidmax = 0
    rel_type = None
    for rel in relations :
        if rel['node2'] == node2 :
            if poidmax < rel['w'] :
                rel_type = rel['type']
                poidmax = rel['w']
    return rel_type

@lru_cache(maxsize=None) 
def getRelationsFrom(node_name):
    """Renvoie le json de la requete : 'https://jdm-api.demo.lirmm.fr/v0/relations/from/{node_name}'""" 
    url = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{node_name}" 
    print(url) 
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur HTTP {response.status_code} pour {node_name}")
        return {"nodes": [], "relations": []}  # retourne un dict vide
    try:
        return response.json()
    except ValueError:
        print(f"Réponse non JSON pour {node_name}: {response.text[:100]}")
        return {"nodes": [], "relations": []}

@lru_cache(maxsize=None) 
def getRelationsTo(node_name): 
    """Renvoie le json de la requete : 'https://jdm-api.demo.lirmm.fr/v0/relations/to/{node_name}'""" 
    url = f"https://jdm-api.demo.lirmm.fr/v0/relations/to/{node_name}" 
    print(url) 
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur HTTP {response.status_code} pour {node_name}")
        return {"nodes": [], "relations": []}  # retourne un dict vide
    try:
        return response.json()
    except ValueError:
        print(f"Réponse non JSON pour {node_name}: {response.text[:100]}")
        return {"nodes": [], "relations": []}

def supprRaffinement(node_name):
    """On enleve le raffinement sémantique car sinon la requete ne marche pas"""
    if ">" in node_name:
        node_name = node_name.split()[0]
    return node_name

def fill_from_node(node_name, dictionnaire, compteur):
    """On souhaite recuperer tous les noeuds relies à un autre, retourne une liste de nom (pour l'instant)
    si le dictionnaire qui est cree depasse LIM_MAX mots, la fonction s'arrete toute seule
    si le dictionnaire contient moins de LIM_MIN mots, la fonction se rappelle avec un mot proche\n
    /!\\ La fonction renvoie les mots sans tenir compte des majuscules et des '-'\n
    Usage : dictionnaire = fill_from_node(node_name, list, 0)
    """
    response = getRelationsFrom(supprRaffinement(node_name))
    response_to = getRelationsTo(supprRaffinement(node_name))
    
    print("Les requêtes sont bonnes, Nombre de mots :", compteur)
    nodes = response['nodes']
    relations = response['relations']

    nodes_to = response_to['nodes']
    relations_to = response_to['relations']

    close_node_id = None
    close_node_name = None

    if compteur >= LIM_MAX :
        return dictionnaire
    
    visited_nodes.add(node_name)
    
    #Pour les noeuds <node_name> -> node
    for node in nodes:
        mot = filtreMot(node['name'])
        if (node['w'] > 50) and (node['type'] in type_noeud) and (node['name'] not in visited_nodes) and mot != 0:
                dictionnaire.append(mot)#Si on souhaite ajouter le type de la relation on peut le faire ici
                visited_nodes.add(node['name'])
                compteur = compteur + 1
                #print(compteur)

    
    #Pour les noeuds node -> <node_name>
    for node_to in nodes_to:
        mot_to = filtreMot(node_to['name'])
        if (node_to['w'] > 50) and (node_to['type'] in type_noeud) and (node_to['name'] not in visited_nodes) and mot_to != 0:
                dictionnaire.append(mot_to)#Si on souhaite ajouter le type de la relation on peut le faire ici
                visited_nodes.add(node_to['name'])
                compteur = compteur + 1
                #print(compteur)

    # Rassembler tous les candidats
    candidats = []

    for rel in relations:
        if rel['type'] in type_relation and rel['w'] > 40 and rel['node2'] not in node_a_eviter:
            candidats.append((rel['w'], rel['node2']))

    for rel_to in relations_to:
        if rel_to['type'] in type_relation and rel_to['w'] > 40 and rel_to['node1'] not in node_a_eviter:
            candidats.append((rel_to['w'], rel_to['node1']))

    # Trier par poids d�croissant
    candidats.sort(key=lambda x: x[0], reverse=True)

    # Prendre les 10 ou 20 premiers
    top_candidats = candidats[:20]  # Ajuste 10 ou 20 selon ton choix

    # Filtrer ceux d�j� dans request_nodes
    candidats_disponibles = [node_id for _, node_id in top_candidats if node_id not in request_nodes]

    if candidats_disponibles:
        # Choisir un node au hasard parmi les candidats disponibles
        close_node_id = random.choice(candidats_disponibles)
        node_a_eviter.append(close_node_id)


    # R�cup�rer le nom filtr�
    close_node_name = filtreMot(getNameNode(close_node_id)) if close_node_id else None

    # Ajouter le node � ceux � �viter
    if close_node_id:
        node_a_eviter.append(close_node_id)

    
    if compteur < LIM_MIN and (close_node_name is not None) and close_node_name not in request_nodes and close_node_name != 0:
        print(close_node_name, "Le compteur est de :", compteur, "\n")
        return fill_from_node(close_node_name, dictionnaire, compteur)
    
    elif compteur < LIM_MIN:
        close_node_name = random.choice(list(visited_nodes))#Pas propre, on pourrais faire une classe specifique : https://stackoverflow.com/questions/15993447/python-data-structure-for-efficient-add-remove-and-random-choice
        print(close_node_name, "Le compteur est de :", compteur, "\n")
        return fill_from_node(close_node_name, dictionnaire, compteur)
    
    else :
        return dictionnaire

def filtreMot(name):
    global MAX_LONG
    """Empeche de prendre les mots qui contiennent des caractere speciaux ou des mots avec 'en:' devant ou encore enleve le raffinement semantique"""
    charS = ["0","1","2","3","4","5","6","7","8","9", "en:", " ", "_", "&", "#", ".", "'", "/", ",", ";", ":", "?", "!", "^", "%", "(", ")", "*", "+", "[", "]", "@"]
    if len(name) >= MAX_LONG or len(name) < 4:
        return 0
    if ">" in name :#Pour cacher le raffinement semantique
        noms = name.split('>')
        return filtreMot(noms[0])
    if any(char in name for char in charS) :
        return 0
    return name

#####################################################################
#Wizium fonctions                                                   #
#####################################################################

# ============================================================================
def draw (wiz):
    """Draw the grid content, with a very simple formating

    wiz     Wizium instance"""
# ============================================================================
    lines = wiz.grid_read ()
    for l in lines:
        print (''.join ([s + '   ' for s in l]))
# ============================================================================
def solve (wiz, max_black=0, heuristic_level=3, seed=0, black_mode='DIAG'):
    """Solve the grid

    wiz             Wizium instance
    max_black       Max number of black cases to add (0 if not allowed)
    heuristic_level Heuristic level (0 if deactivated)
    seed            Random Number Generator seed (0: take at random)
    """
# ============================================================================

    if not seed: seed = random.randint(1, 1000000)

    # Configure the solver
    wiz.solver_start (seed=seed, black_mode=black_mode, max_black=max_black, heuristic_level=heuristic_level)
    tstart = time.time ()

    # Solve with steps of 500ms max, in order to draw the grid content evolution
    while True:
        status = wiz.solver_step (max_time_ms=500)

        draw (wiz)
        print (status)

        if status.fillRate == 100:
            print ("SUCCESS !")
            break
        if status.fillRate == 0:
            print ("FAILED !")
            break

    # Ensure to release grid content
    wiz.solver_stop ()

    compute_time = time.time() - tstart
    print(f"Compute time: {compute_time:.1f}s")
    return wiz.grid_read(), compute_time

MAX_LONG = 10

##################################################################################################
#               MAIN                                                                            #
###################################################################################################
def thematic_generator(word, largeur=10, longueur=12):
    global MAX_LONG
    MAX_LONG = max(largeur,longueur)
    wiz.dic_clear()

    dictionnaire = []
    dictionnaire.extend(getMotsLong234())
    dictionnaire = fill_from_node(word.lower(), dictionnaire, 0)
    print("Longueur du dictionnaire créé : ", len(dictionnaire))

    # dictionnaire pour le solveur (ASCII, majuscules, sans '-')
    dictionnaire_ascii = [unidecode(m.replace("-", "")).upper() for m in dictionnaire]


    if wiz.dic_add_entries(dictionnaire_ascii) != len(dictionnaire_ascii):
        print("gros probleme")
        rejected = [m for m in dictionnaire_ascii if not wiz.dic_add_entries([m])]
        print("Mots rejetés :", rejected)

    wiz.grid_set_size(largeur, longueur)

    return solve(wiz, max_black=(longueur * largeur) // 7, heuristic_level=3)

