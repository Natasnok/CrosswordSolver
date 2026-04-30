from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os
from werkzeug.utils import secure_filename

from backend.Scanner.Scandef import scan_definitions
from backend.Scanner.GridReader import scan_grid
from backend.Solver.CrosswordSolver import solve_crossword
from backend.Generateur.ThematicGenerator import thematic_generator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

app = Flask(__name__)
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

@app.route('/api', methods=['GET'], strict_slashes=False)
def home():
    return jsonify({
        'message': 'API Flask du solver de mots croisés active',
        'endpoint': 'POST /api/solve or /api/digitalise or /api/genthem',
        'required_fields': '[grid_image, definitions_image]' if request.args.get('type') != 'genthem' else '[word]'
    })

@app.route('/api/solve', methods=['POST'], strict_slashes=False)
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
        definition_word_list = scan_definitions(defs_path)

        test_cases = build_test_cases(definition_word_list, info_word_list)
        result = solve_crossword(test_cases, pos_case_noire, nbC, nbR, False)

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

@app.route('/api/digitalise', methods=['POST'], strict_slashes=False)
def digitalise_route():
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
        definition_word_list = scan_definitions(defs_path)
        info_word_list = scan_result["info_word"]
        test_cases = build_test_cases(definition_word_list, info_word_list)

        return jsonify({
            'success': True,
            'grid': {
                'nb_rows': scan_result["nb_rows"],
                'nb_cols': scan_result["nb_cols"],
                'black_cells': scan_result["pos_noir"],
            },
            'definitions': test_cases
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

@app.route('/api/genthem', methods=['POST'], strict_slashes=False)
def genthem_route():
    print("FORM =", request.form)

    themword = request.form.get('word', '').strip()
    width_raw = request.form.get('width', '').strip()
    height_raw = request.form.get('height', '').strip()

    print("WORD =", repr(themword))
    print("WIDTH =", repr(width_raw))
    print("HEIGHT =", repr(height_raw))

    if not themword:
        return jsonify({
            'success': False,
            'error': 'Le paramètre "word" est obligatoire'
        }), 400

    try:
        width = int(width_raw)
        height = int(height_raw)
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Les paramètres "width" et "height" doivent être des entiers'
        }), 400

    if width < 5 or width > 20 or height < 5 or height > 20:
        return jsonify({
            'success': False,
            'error': 'La largeur et la hauteur doivent être comprises entre 5 et 20'
        }), 400

    try:
        grid, compute_time = thematic_generator(themword, width, height)

        print("GRID =", grid)
        print("COMPUTE_TIME =", compute_time)

        return jsonify({
            'success': True,
            'word': themword,
            'width': width,
            'height': height,
            'result': grid,
            'compute_time': compute_time
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    file_path = os.path.join(FRONTEND_DIST, path)
    if path and os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)