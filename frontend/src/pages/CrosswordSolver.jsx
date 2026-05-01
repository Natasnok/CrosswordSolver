import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../index.css";

// ─── Image upload card ───────────────────────────────────────────────────────
function ImagePreview({ label, file, preview, onFileChange, onRemove }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleInputChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected && selected.type.startsWith("image/")) onFileChange(selected);
    e.target.value = null;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type?.startsWith("image/")) onFileChange(dropped);
  };

  return (
    <div className="upload-card">
      <div className="upload-card-top">
        <label className="upload-label">{label}</label>
        {file && (
          <button type="button" className="remove-btn" onClick={onRemove} title="Supprimer l'image">×</button>
        )}
      </div>
      <label
        className={`dropzone ${isDragging ? "drag-active" : ""} ${file ? "has-file" : ""}`}
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
      >
        <input type="file" accept="image/*" onChange={handleInputChange} className="file-input" />
        {preview ? (
          <img key={preview} src={preview} alt={label} className="preview-image" />
        ) : (
          <div className="dropzone-content">
            <div className="drop-icon">⬆</div>
            <p className="drop-title">Glisse ton image ici</p>
            <p className="drop-subtitle">ou clique pour parcourir</p>
          </div>
        )}
      </label>
      <div className="file-meta">
        {file ? (
          <>
            <p className="file-name">{file.name}</p>
            <p className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </>
        ) : (
          <p className="file-placeholder">Formats image acceptés</p>
        )}
      </div>
    </div>
  );
}

// ─── Grid editor ─────────────────────────────────────────────────────────────
function GridEditor({ nbRows, nbCols, blackCells, onBlackCellsChange, onSizeChange }) {
  const isBlack = (r, c) => blackCells.some(([br, bc]) => br === r && bc === c);

  const toggleCell = (r, c) => {
    if (isBlack(r, c)) {
      onBlackCellsChange(blackCells.filter(([br, bc]) => !(br === r && bc === c)));
    } else {
      onBlackCellsChange([...blackCells, [r, c]]);
    }
  };

  return (
    <div className="editor-section">
      <div className="editor-section-header">
        <h3 className="editor-title">Grille</h3>
        <div className="editor-size-controls">
          <label>Lignes
            <input type="number" min={1} max={30} value={nbRows}
              onChange={e => onSizeChange(parseInt(e.target.value) || 1, nbCols)}
              className="size-input" />
          </label>
          <label>Colonnes
            <input type="number" min={1} max={30} value={nbCols}
              onChange={e => onSizeChange(nbRows, parseInt(e.target.value) || 1)}
              className="size-input" />
          </label>
        </div>
      </div>
      <p className="editor-hint">Cliquez sur une case pour l'ajouter/retirer comme case noire</p>
      <div
        className="editable-grid"
        style={{ gridTemplateColumns: `28px repeat(${nbCols}, 36px)` }}
      >
        {/* header row */}
        <div />
        {Array.from({ length: nbCols }, (_, c) => (
          <div key={`ch-${c}`} className="coord-label" style={{ height: 28 }}>{c + 1}</div>
        ))}
        {/* grid rows */}
        {Array.from({ length: nbRows }, (_, r) => [
          <div key={`rh-${r}`} className="coord-label" style={{ width: 28, height: 36 }}>
            {String.fromCharCode(65 + r)}
          </div>,
          ...Array.from({ length: nbCols }, (_, c) => (
            <div
              key={`${r}-${c}`}
              className={`edit-cell ${isBlack(r, c) ? "block" : "white"}`}
              onClick={() => toggleCell(r, c)}
              title={isBlack(r, c) ? "Case noire — cliquer pour retirer" : "Case blanche — cliquer pour noircir"}
            />
          ))
        ])}
      </div>
    </div>
  );
}

// ─── Definitions editor ───────────────────────────────────────────────────────
function DefsEditor({ definitions, onDefsChange }) {
  const update = (idx, field, value) => {
    const next = definitions.map((d, i) => i === idx ? { ...d, [field]: value } : d);
    onDefsChange(next);
  };

  const addDef = () => {
    onDefsChange([...definitions, { definition: "", taille: 5, direction: "H", pos: [0, 0] }]);
  };

  const removeDef = (idx) => {
    onDefsChange(definitions.filter((_, i) => i !== idx));
  };

  return (
    <div className="editor-section">
      <div className="editor-section-header">
        <h3 className="editor-title">Définitions</h3>
        <button className="add-def-btn" onClick={addDef}>+ Ajouter</button>
      </div>
      <div className="defs-list">
        {definitions.map((def, idx) => (
          <div key={idx} className="def-row">
            <span className="def-index">{idx + 1}</span>
            <input
              className="def-input def-text"
              value={def.definition}
              placeholder="Définition..."
              onChange={e => update(idx, "definition", e.target.value)}
            />
            <select
              className="def-select"
              value={def.direction}
              onChange={e => update(idx, "direction", e.target.value)}
            >
              <option value="H">H</option>
              <option value="V">V</option>
            </select>
            <label className="def-label-small">Taille
              <input
                type="number"
                className="def-input def-size"
                min={1} max={30}
                value={def.taille}
                onChange={e => update(idx, "taille", parseInt(e.target.value) || 1)}
              />
            </label>
            <label className="def-label-small">Ligne
              <input
                type="number"
                className="def-input def-pos"
                min={0}
                value={def.pos[0]}
                onChange={e => update(idx, "pos", [parseInt(e.target.value) || 0, def.pos[1]])}
              />
            </label>
            <label className="def-label-small">Col
              <input
                type="number"
                className="def-input def-pos"
                min={0}
                value={def.pos[1]}
                onChange={e => update(idx, "pos", [def.pos[0], parseInt(e.target.value) || 0])}
              />
            </label>
            <button className="remove-def-btn" onClick={() => removeDef(idx)} title="Supprimer">×</button>
          </div>
        ))}
        {definitions.length === 0 && (
          <p className="defs-empty">Aucune définition. Cliquez sur "+ Ajouter" pour en créer une.</p>
        )}
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function CrosswordSolverPage() {
  // Step 1: upload
  const [gridFile, setGridFile]   = useState(null);
  const [defsFile, setDefsFile]   = useState(null);
  const [gridPreview, setGridPreview] = useState(null);
  const [defsPreview, setDefsPreview] = useState(null);
  const [loading, setLoading]     = useState(false);

  // Step 2: edit
  const [editMode, setEditMode]   = useState(false);
  const [nbRows,   setNbRows]     = useState(0);
  const [nbCols,   setNbCols]     = useState(0);
  const [blackCells, setBlackCells] = useState([]);
  const [definitions, setDefinitions] = useState([]);

  // Step 3: result
  const [resultGrid, setResultGrid] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [solving, setSolving]     = useState(false);

  const navigate = useNavigate();

  // Object-URL lifecycle for preview images
  useEffect(() => {
    if (!gridFile) { setGridPreview(null); return; }
    const url = URL.createObjectURL(gridFile);
    setGridPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [gridFile]);

  useEffect(() => {
    if (!defsFile) { setDefsPreview(null); return; }
    const url = URL.createObjectURL(defsFile);
    setDefsPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [defsFile]);

  // ── Step 1 → 2: digitize ──────────────────────────────────────────────────
  const digitize = async () => {
    if (!gridFile || !defsFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("grid_image", gridFile);
    formData.append("definitions_image", defsFile);

    try {
      const res  = await fetch("/api/digitalise", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.error || "Erreur lors de la numérisation");
        return;
      }

      setNbRows(data.grid.nb_rows);
      setNbCols(data.grid.nb_cols);
      setBlackCells(data.grid.black_cells || []);
      setDefinitions(data.definitions || []);
      setResultGrid(null);
      setShowResult(false);
      setEditMode(true);
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la numérisation");
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2 → 3: solve ─────────────────────────────────────────────────────
  const solveDirect = async () => {
    setSolving(true);
    try {
      const body = {
        grid: { nb_rows: nbRows, nb_cols: nbCols, black_cells: blackCells },
        definitions,
      };
      const res  = await fetch("/api/solve_from_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.error || "Erreur serveur");
        return;
      }
      setResultGrid(data.result);
      setShowResult(true);
    } catch (err) {
      console.error(err);
      alert("Erreur lors du lancement du solver");
    } finally {
      setSolving(false);
    }
  };

  const reset = () => {
    setGridFile(null); setDefsFile(null);
    setEditMode(false); setResultGrid(null); setShowResult(false);
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="app-shell">
      <div className="app">

        <div className="hero">
          <p className="eyebrow">Crossword Solver</p>
          <div className="title-bar">
            <h1>Analyse ta grille et remplis les réponses automatiquement</h1>
            <button className="home-btn" onClick={() => navigate("/")}>⌂ Home</button>
          </div>
          <p className="hero-text">
            Dépose les images, vérifie et corrige la numérisation, puis lance le solver.
          </p>
        </div>

        {/* ── Stepper ────────────────────────────────────────────────────── */}
        <div className="stepper">
          <div className={`step ${!editMode ? "step-active" : "step-done"}`}>
            <span className="step-num">1</span>
            <span className="step-label">Upload images</span>
          </div>
          <div className="step-connector" />
          <div className={`step ${editMode && !showResult ? "step-active" : editMode || showResult ? "step-done" : ""}`}>
            <span className="step-num">2</span>
            <span className="step-label">Vérifier &amp; éditer</span>
          </div>
          <div className="step-connector" />
          <div className={`step ${showResult ? "step-active" : ""}`}>
            <span className="step-num">3</span>
            <span className="step-label">Résultat</span>
          </div>
        </div>

        {/* ── STEP 1: Upload ─────────────────────────────────────────────── */}
        {!editMode && (
          <>
            <div className="upload-grid">
              <ImagePreview
                label="Image de la grille"
                file={gridFile} preview={gridPreview}
                onFileChange={(f) => { setGridFile(f); }}
                onRemove={() => { setGridFile(null); }}
              />
              <ImagePreview
                label="Image des définitions"
                file={defsFile} preview={defsPreview}
                onFileChange={(f) => { setDefsFile(f); }}
                onRemove={() => { setDefsFile(null); }}
              />
            </div>
            <div className="actions">
              <button
                className={`solve-btn ${loading ? "loading" : ""}`}
                onClick={digitize}
                disabled={loading || !gridFile || !defsFile}
              >
                {loading ? "Numérisation en cours..." : "Numériser et vérifier →"}
              </button>
            </div>
          </>
        )}

        {/* ── STEP 2: Edit ───────────────────────────────────────────────── */}
        {editMode && !showResult && (
          <>
            <div className="edit-layout">
              <GridEditor
                nbRows={nbRows} nbCols={nbCols}
                blackCells={blackCells}
                onBlackCellsChange={setBlackCells}
                onSizeChange={(r, c) => { setNbRows(r); setNbCols(c); }}
              />
              <DefsEditor
                definitions={definitions}
                onDefsChange={setDefinitions}
              />
            </div>
            <div className="actions actions-row">
              <button className="secondary-btn" onClick={reset}>← Retour</button>
              <button
                className={`solve-btn ${solving ? "loading" : ""}`}
                onClick={solveDirect}
                disabled={solving || definitions.length === 0}
              >
                {solving ? "Résolution en cours..." : "Lancer le solver ✓"}
              </button>
            </div>
          </>
        )}

        {/* ── STEP 3: Result ─────────────────────────────────────────────── */}
        {showResult && resultGrid && (
          <>
            <div className="result-section">
              <h2>Résultat</h2>
              <div
                className="grid-with-coords result-crossword"
                style={{ display: "grid", gridTemplateColumns: `40px repeat(${resultGrid[0].length}, 44px)` }}
              >
                <div />
                {resultGrid[0].map((_, col) => (
                  <div key={`col-${col}`} className="coord-label">{col + 1}</div>
                ))}
                {resultGrid.flatMap((row, r) => [
                  <div key={`row-label-${r}`} className="coord-label">
                    {String.fromCharCode(65 + r)}
                  </div>,
                  ...row.map((cell, c) => (
                    <div key={`${r}-${c}`} className={`cell ${cell === "#" ? "block" : ""}`}>
                      {cell !== "#" && cell !== "." && (
                        <div className="result-letter">{cell}</div>
                      )}
                    </div>
                  )),
                ])}
              </div>
            </div>
            <div className="actions actions-row">
              <button className="secondary-btn" onClick={() => setShowResult(false)}>
                ← Modifier encore
              </button>
              <button className="secondary-btn" onClick={reset}>
                Recommencer
              </button>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
