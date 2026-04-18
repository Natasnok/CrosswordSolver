import requests
from bs4 import BeautifulSoup
import unicodedata
from urllib.parse import quote
import string
import sys
sys.stdout.reconfigure(encoding="utf-8")
from collections import defaultdict
from ..config import *

'''
CELL = 35
MARGIN = 40


def draw_grid(canvas, grid, title=""):
    root.update_idletasks()
    root.update()
    canvas.delete("all")


    width = len(grid[0])
    height = len(grid)


    # Titre
    canvas.create_text(MARGIN, 25, anchor="w", text=title, font=("Arial", 14, "bold"))


    # Lettres colonnes
    for c in range(width):
        x = MARGIN + c * CELL + CELL / 2
        canvas.create_text(x, MARGIN + 20, text=chr(ord('A') + c), font=("Arial", 10, "bold"))


    # Lignes + cellules
    for r in range(height):
        y = MARGIN + 30 + r * CELL
        canvas.create_text(25, y + CELL / 2, text=str(r + 1), font=("Arial", 10, "bold"))
        for c in range(width):
            x = MARGIN + c * CELL
            val = grid[r][c]


            if val == "#":
                fill = "black"
                txt = ""
            elif val == ".":
                fill = "white"
                txt = ""
            else:
                fill = "white"
                txt = val.upper()


            canvas.create_rectangle(x, y, x + CELL, y + CELL, outline="gray", fill=fill)
            if txt:
                canvas.create_text(x + CELL / 2, y + CELL / 2, text=txt, font=("Arial", 14, "bold"))


def make_viewer():
    root = tk.Tk()
    root.title("Résolution de la grille")
    canvas = tk.Canvas(root, width=900, height=500, bg="white")
    canvas.pack(fill="both", expand=True)
    root.update()
    return root, canvas
'''

# grid ----------------------------------------------------

def create_grid(black_cells, width, height):
    grid = [["." for _ in range(width)] for _ in range(height)]
    for r, c in black_cells:
        grid[r][c] = "#"
    return grid

# Dico ----------------------------------------------------

def load_dict(path=DICO_PATH):
    with open(path, encoding="utf-8") as f:
        words = [line.strip().upper() for line in f if line.strip()]
    return words

# Scrapper ----------------------------------------------------

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def defToUrl(definition):
    s = unicodedata.normalize("NFD", definition)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace(" ", "+")
    s = quote(s, safe="+" + string.ascii_letters + string.digits)
    return s


def findListWord(definition, taille):
    def_url = defToUrl(definition)
    url = f"https://q.mots-croises-solutions.com/croises/{taille}/{def_url}/"

    r = session.get(url, timeout=10)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")
    resultats = []

    for tr in soup.select(f"tr.pagere.section_{taille}"):
        a = tr.find("a")
        if a is None:          
            continue
        texte = a.get_text(strip=True)
        if texte not in resultats:
            resultats.append(texte.upper())

    return resultats

def fillWordList(test_cases, word_by_size):
    for case in test_cases:
        solution = findListWord(case["definition"], case["taille"])
        if solution:
            case["solution"] = solution
            print(f" {case['definition'][:40]} : {solution}")
        else:
            print(f" Aucun mot pour : {case['definition']}")
            case["solution"] = []
            #case["solution"] = word_by_size[case["taille"]]

# Backtrack ----------------------------------------------------

def get_cells(case):
    x,y = case["pos"]
    if case["direction"] == "H":
        return [(y, x + i) for i in range(case["taille"])]
    else:
        return [(y + i, x) for i in range(case["taille"])]

def place_word(word, case, grid):
    cells = get_cells(case)
    snapshot = [(row, col, grid[row][col]) for row, col in cells]
    for i, (row, col) in enumerate(cells):
        grid[row][col] = word[i]
    return snapshot

def remove_word(snapshot, grid):
    for row, col, original in snapshot:
        grid[row][col] = original

def get_pattern(case, grid):
    pattern = []
    for row, col in get_cells(case):
        cell = grid[row][col]
        if cell == "#":
            return None
        pattern.append(cell.upper() if cell != "." else ".")
    return "".join(pattern)

def get_candidates(case, grid, used_words):
    pattern = get_pattern(case, grid)
    if pattern is None:
        return []

    results = []
    for w in case["solution"]:
        if w in used_words:
            continue

        valid = True
        for i, ch in enumerate(pattern):
            if ch != "." and w[i] != ch:
                valid = False
                break

        if valid:
            results.append(w)

    return results


def solve(cases, grid, used_words=None, index=0):
    if used_words is None:
        used_words = set()

    if index == len(cases):
        return True

    remaining = cases[index:]

    ranked = []
    for case in remaining:
        candidates = get_candidates(case, grid, used_words)
        nb_fixed = sum(
            1 for row, col in get_cells(case)
            if grid[row][col] != "."
        )
        ranked.append((len(candidates), -nb_fixed, case, candidates))

    ranked.sort(key=lambda x: (x[0], x[1]))
    nb_candidates, _, case, candidates = ranked[0]

    cases[index:] = [item[2] for item in ranked]

    if nb_candidates == 0:
        return False
    
    for word in candidates:
        snapshot = place_word(word, case, grid)
        used_words.add(word)  

        if solve(cases, grid, used_words, index + 1):
            return True

        remove_word(snapshot, grid)
        used_words.remove(word)

    return False

# Main ----------------------------------------------------
def solve_crossword(test_cases, black_cells, width, height):
    grid = create_grid(black_cells, width, height)
    word_dict = load_dict()
    word_by_size = defaultdict(list)
    for w in word_dict:
        word_by_size[len(w)].append(w.upper())
    fillWordList(test_cases, word_by_size)
    test_cases.sort(key=lambda c: len(c.get("solution", [])))
    if solve(test_cases, grid):
        return grid