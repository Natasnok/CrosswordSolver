from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os
from werkzeug.utils import secure_filename

from backend.Scanner.Scandef import scan_definitions
from backend.Scanner.GridReader import scan_grid
from backend.Solver.CrosswordSolver import solve_crossword

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path="/")
CORS(app)

def build_test_cases(definition_word_list, info_word_list):
    infos = []
    for num, data in info_word_list:
        infos.append({
            "num": num + 1,
            "pos": data["pos"],        
            "taille": data["len"],
            "direction": data["dir"]
        })

    defs_h = [d for d in definition_word_list if d["direction"] == "H"]
    defs_v = [d for d in definition_word_list if d["direction"] == "V"]

    infos_h = [i for i in infos if i["direction"] == "H"]
    infos_v = [i for i in infos if i["direction"] == "V"]

    test_cases = []

    # Horizontal
    for definition, info in zip(defs_h, infos_h):
        x, y = info["pos"]
        test_cases.append({
            "definition": definition["mot"],       
            "taille": info["taille"],
            "direction": info["direction"],       
            "pos": (x, y)                         
        })

    # Vertical
    for definition, info in zip(defs_v, infos_v):
        x, y = info["pos"]
        test_cases.append({
            "definition": definition["mot"],
            "taille": info["taille"],
            "direction": info["direction"],       
            "pos": (x, y)
        })

    return test_cases

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api"):
        return jsonify({"success": False, "error": "API route not found"}), 404

    file_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)

    return send_from_directory(app.static_folder, "index.html")

@app.route('/api', methods=['GET'])
def home():
    return jsonify({
        'message': 'API Flask du solver de mots croisés active',
        'endpoint': 'POST /api/solve',
        'required_fields': ['grid_image', 'definitions_image']
    })

@app.route('/api/solve', methods=['POST'])
def solve_route():
    grid_file = request.files.get('grid_image')
    defs_file = request.files.get('definitions_image')

    if grid_file is None or defs_file is None:
        return jsonify({
            'success': False,
            'error': 'Les deux fichiers sont obligatoires : grid_image et definitions_image'
        }), 400

    if grid_file.filename == '' or defs_file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Un ou plusieurs fichiers sont vides'
        }), 400

    temp_dir = tempfile.mkdtemp()
    grid_filename = secure_filename(grid_file.filename)
    defs_filename = secure_filename(defs_file.filename)
    grid_path = os.path.join(temp_dir, grid_filename)
    defs_path = os.path.join(temp_dir, defs_filename)

    try:
        grid_file.save(grid_path)
        defs_file.save(defs_path)

        scan_result = scan_grid(grid_path)
        nbR = scan_result["nb_rows"]
        nbC = scan_result["nb_cols"]
        pos_case_noire = scan_result["pos_noir"]
        info_word_list = scan_result["info_word"]
        definition_word_list = scan_definitions(defs_path, 'M')

        test_cases = build_test_cases(definition_word_list, info_word_list)
        print(test_cases)
        result = solve_crossword(test_cases, pos_case_noire, nbC, nbR)

        return jsonify({
            'success': True,
            'result': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

    finally:
        try:
            if os.path.exists(grid_path):
                os.remove(grid_path)
            if os.path.exists(defs_path):
                os.remove(defs_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except OSError:
            pass