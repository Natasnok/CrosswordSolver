import cv2
import numpy as np
import random
import math
import os
from backend.config import IMG_GRID_PATH, DIR_RES_PATH
import backend.Scanner.GridUtility

#IMG_PATH = IMG_GRID_PATH
DIR_RES_PATH = DIR_RES_PATH

# ================= Prétraitement Image ====================

def recadrer_image(image, IMG_PATH):
    h, w = image.shape[:2]

    if h*w >= 2000*2000: 
        image = cv2.resize(image, (w // 2, h // 2))
        #print(f"[RECADRER_IMAGE](RESIZE) ({h} {w}) -> ({h//2} {w//2})")

    gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binaire = cv2.threshold(gris, 100, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(binaire, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    plus_grand_contour = max(contours, key=cv2.contourArea)
    imgContours = image.copy()

    cv2.drawContours(imgContours, [plus_grand_contour], -1, (0, 255, 0), 2) #debug
    
    x, y, w, h = cv2.boundingRect(plus_grand_contour)
    Cut = image[y:y+h, x:x+w]

    # cv2.imshow("gray", gray)
    # cv2.imshow("blur", blur)
    # cv2.imshow("edges", edges)
    Fname= IMG_PATH.split('.')[0]
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_gray.jpg",binaire)
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_imgContours.jpg",imgContours)
    path = os.path.join(DIR_RES_PATH, f"{Fname}_cut.jpg")
    cv2.imwrite(path,Cut)
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_blur.jpg",blur)
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_canny.jpg",canny)
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_edges.jpg",edges)
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_edges_proc.jpg",edges_proc)
    # cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_sicamarchecfou.jpg",img)
    
    return Cut

def seuillage_auto(image, IMG_PATH):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    avg_intensity = np.mean(gray)
    #print("[AUTO_SEUIL] Luminosité moyenne (blanc/noir):", avg_intensity)
    
    #  ////////// suppression de  bruit ///////////////////
    # SEUL VALEUR DANGEREUSE DU CODE (normelement)
    seuil = max(0,int(avg_intensity*0.6))
    seuil2 = min(255,int(avg_intensity*1.3))

    #print("[AUTO_SEUIL] seuil1:",seuil)
    #print("[AUTO_SEUIL] seuil2 :",seuil2)
    
    thresh = cv2.Canny(gray, seuil, seuil2, 3)# fonction tres puissante qu'on a fait en cours (part sur les gradients)
    
    #  ///// Amplifie la densité de pixel  /////
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)  # dilatation vu en cours

    Fname= IMG_PATH.split('.')[0]
    cv2.imwrite(f"{DIR_RES_PATH}/{Fname}_canny.jpg",thresh)
    return thresh

# ================= Posttraitement (juste des fonctions que j'appelle en fin) ==========================
# def avg_case(image,intersec):
#     n_rows = len(intersec) - 1
#     n_cols = len(intersec[0]) - 1
#     moyennes =[]
#     for i in range(n_rows):
#         for j in range(n_cols):
#             p1 = intersec[i][j]
#             p2 = intersec[i+1][j+1]
#             nb_pix = nb_pixel_entre(p1, p2)
#             if nb_pix == 0:
#                 moyennes[i, j] = 0
#    
#             acc = projection_entre_p1_P2(thresh, p1, p2)
#             moyennes[i, j] = acc / nb_pix
#     return moyennes


# ================= Outil ====================
def projection_ligne(thresh_img):
    '''prend une image noir et blanc et renvoie 2 listes :
    la somme des pixels de chaque ligne et
    la somme des pixels de chaque colonne'''
    vertical_projection = np.sum(thresh_img, axis=0) // 255
    
    # Somme des pixels lignes par lignes (axis=1)
    horizontal_projection = np.sum(thresh_img, axis=1) // 255
    
    return vertical_projection, horizontal_projection

def moyenne_ensemble_ligne(proj,x,r):
    """
    Renvoie la moyenne dela somme des pixes de la ligne x-r à x+r 
    proj : projection,
    x: indice,
    r: rayon,
    maxlenght: taille max de l'image
    """
    start = max(0, x - r)
    end   = min(len(proj), x + r + 1)
    
    return np.mean(proj[start:end])

def projection_entre_p1_P2(img,p1,p2):
    x1, y1 = p1
    x2, y2 = p2

    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)

    zone = img[y_min:y_max+1, x_min:x_max+1]

    acc = np.sum(zone)
    return acc

def nb_pixel_entre(p1, p2):
    return (abs(p2[0]-p1[0])+1) * (abs(p2[1]-p1[1])+1)


# ========= traitement Image =============


def FoundRawAndCol(tresh):
    hori_proj,vert_proj = projection_ligne(tresh)
    h, w = tresh.shape[:2]
    rawIndex=[]
    colIndex=[]

    seuil_h = np.percentile(hori_proj, 85) # en gros ça prend les 15% + grande val 
    seuil_v = np.percentile(vert_proj, 85)
    #print("[FoundRaw&Column] seuil_h",seuil_h)
    #print("[FoundRaw&Column] seuil_v",seuil_v)

    diametre_hori = int(w*0.005)
    diametre_verti = int(h*0.005)

    for x in range(w): 
        if moyenne_ensemble_ligne(hori_proj,x,diametre_hori) > seuil_h:
            rawIndex.append(x)
    #print(f"[Foundraw] : {rawIndex}")

    for y in range(h):
        if moyenne_ensemble_ligne(vert_proj,y,diametre_verti) > seuil_v:
            colIndex.append(y)
    #print(f"[Colindex] : {colIndex}")
    return rawIndex,colIndex

def mergeIndex(L, maxLen):
    if not L:
        return []
    
    seuil = max(1, int(maxLen * 0.02))  
    newT = []
    accL = [L[0]]

    for i in range(1, len(L)):

        if L[i] - accL[-1] <= seuil:
            accL.append(L[i])
        else:
            newT.append(int(np.mean(accL)))
            accL = [L[i]] 
    newT.append(int(np.mean(accL)))

    return newT

def Drawintersec(image,pointss):
    img = image.copy()
    for points in pointss:
        for p in points:
                cv2.circle(img, p, 10, (0,0,255), -1)
    return img



#////////////// MAIN ///////////////////////
def scan_grid(IMG_PATH):
    # setup les res visuel
    os.makedirs(DIR_RES_PATH, exist_ok=True)

    image = cv2.imread(IMG_PATH)

    # pretraitement Image
    image_recadrer = recadrer_image(image, IMG_PATH)
    img= image_recadrer.copy()
    image_thresh = seuillage_auto(image_recadrer, IMG_PATH)

    # /////////// ANALYSE Image /////////// 
    h, w = image_thresh.shape[:2]
    #print("MAIN taille : ",h,w)

    R,C = FoundRawAndCol(image_thresh)
    R = mergeIndex(R,h)
    C = mergeIndex(C,w)
    #print(f"[MAIN]apres merge R : {R}")
    #print(f"[MAIN]apres merge C : {C}")

    nbC = len(R)-1
    nbR= len(C)-1
    #print(f"[MAIN] grille détecté: {nbC}x{nbR}")

    intersec = [[(x, y) for x in R] for y in C]
    newimg= Drawintersec(img,intersec)
    # ////////////// Fin Analyse ///////////////

    # //////////////Traitement Donnée Analysé /////////////////////////
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    cases = []
    for i in range(len(intersec)-1):
        L=[]
        for j in range(len(intersec[0])-1):
            p1 = intersec[i][j]
            p2 = intersec[i+1][j+1]
            L.append((p1,p2))
        cases.append(L)

    cases_avg=[]
    for line in cases:
        for p1,p2 in line:
            val= projection_entre_p1_P2(gray,p1,p2) / (nb_pixel_entre(p1,p2)*255)
            cases_avg.append(1-val)
    
    T = [(i, val) for i, val in enumerate(cases_avg)]
    T.sort(key=lambda x: x[1],reverse=True)
    mediane = 0.5
    case_noir = [(i, val) for i, val in T if val >= mediane]  


    seuil_noir = case_noir[0][1] * 0.8

    case_noir = [(i, val) for i, val in case_noir if val >= seuil_noir]

    pos_case_noire = [(i // nbC, i % nbC) for i, _ in case_noir]

    #print(pos_case_noire)
    res=[[0 for _ in range(nbC)]for _ in range(nbR)]
    for x,y in pos_case_noire:
        res[x][y]=1

    
    Fname= IMG_PATH.split('.')[0]
    path = os.path.join(DIR_RES_PATH, f"{Fname}_intersec.jpg")
    #print(path)
    cv2.imwrite(path,newimg)
    #for l in res:
        #print(l)
    
    grid = backend.Scanner.GridUtility.Grid(nbR, nbC, pos_case_noire)
    info_word_list = list(grid.get_info_word())

    return {
        "nb_cols": nbC,
        "nb_rows": nbR,
        "pos_noir": pos_case_noire,
        "info_word": info_word_list
    }