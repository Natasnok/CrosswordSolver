import requests
from bs4 import BeautifulSoup
import cloudscraper
import unicodedata
from urllib.parse import quote
import string
import sys
sys.stdout.reconfigure(encoding="utf-8")
from collections import defaultdict
from ..config import *
from copy import deepcopy

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


def defToUrl1(definition):
    s = unicodedata.normalize("NFD", definition)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace(" ", "+")
    s = quote(s, safe="+" + string.ascii_letters + string.digits)
    return s


def defToUrl2(definition):
    s = definition.upper()
    s = s.replace("'", "*")
    s = s.replace(" ", "*")
    return s


def findListWord(definition, taille):
    url1 = f"https://q.mots-croises-solutions.com/croises/{taille}/{defToUrl1(definition)}/"
    url2 = f"https://www.fsolver.fr/mots-fleches/{defToUrl2(definition)}/"
    resultats = []

    r = session.get(url1, timeout=10)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")

    for tr in soup.select(f"tr.pagere.section_{taille}"):
        a = tr.find("a")
        if a is None:
            continue
        mot = a.get_text(strip=True).upper()
        if mot not in resultats:
            resultats.append(mot)

    scraper = cloudscraper.create_scraper()
    r = scraper.get(url2, timeout=10)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")

    for div in soup.select("div.elemTable"):
        span_text = div.select_one("span[itemprop='acceptedAnswer'] a")
        span_size = div.select_one(f"span.color{taille}")
        if span_text and span_size:
            mot = span_text.get_text(strip=True).upper()
            if mot not in resultats:
                resultats.append(mot)

    return resultats

def fillWordList(test_cases, word_by_size, use_dico=True):
    for case in test_cases:
        solution = findListWord(case["definition"], case["taille"])
        solution = [w.upper() for w in solution if len(w) == case["taille"]]
        
        if solution:
            case["solution"] = solution
            print(f"{case['definition'][:40]} : {solution}")
        else:
            if use_dico:
                case["solution"] = word_by_size[case["taille"]][:]
                print(f"Aucun mot web pour : {case['definition']} -> fallback dico")
            else:
                case["solution"] = []
                print(f"Aucun mot pour : {case['definition']}")

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


def solve(cases, grid, used_words=None, index=0, best=None, filled=0, use_dico=True):
    if used_words is None:
        used_words = set()

    if best is None:
        best = {"score": filled, "grid": deepcopy(grid)}

    if filled > best["score"]:
        best["score"] = filled
        best["grid"] = deepcopy(grid)

    if index == len(cases):
        return True, best

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

    original_order = cases[index:]
    cases[index:] = [item[2] for item in ranked]

    if nb_candidates == 0:
        if use_dico:
            cases[index:] = original_order
            return False, best
        else:
            new_cases = cases[:index] + [c for c in cases[index:] if c is not case]
            return solve(new_cases, grid, used_words, index, best, filled, use_dico)

    for word in candidates:
        snapshot = place_word(word, case, grid)
        filled += 1
        used_words.add(word)
        try:
            solved, best = solve(cases, grid, used_words, index + 1, best, filled, use_dico)
            if solved:
                return True, best
        finally:
            remove_word(snapshot, grid)
            filled -= 1
            used_words.discard(word)

    cases[index:] = original_order
    return False, best

# Main ----------------------------------------------------
def solve_crossword(test_cases, black_cells, width, height, use_dico):
    grid = create_grid(black_cells, width, height)
    word_dict = load_dict()
    word_by_size = defaultdict(list)

    for w in word_dict:
        word_by_size[len(w)].append(w.upper())

    fillWordList(test_cases, word_by_size, use_dico)

    solved, best = solve(test_cases, grid, use_dico=use_dico)

    print(f"Grille avec {best['score']} lettres remplies")
    return best["grid"]