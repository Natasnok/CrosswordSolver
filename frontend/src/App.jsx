import React, { useState, useEffect } from "react";
import "./index.css";

function ImagePreview({ label, file, preview, onFileChange, onRemove }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleInputChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) onFileChange(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type.startsWith("image/")) {
      onFileChange(dropped);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="upload-card">
      <div className="upload-card-top">
        <label className="upload-label">{label}</label>

        {file && (
          <button
            type="button"
            className="remove-btn"
            onClick={onRemove}
            aria-label={`Supprimer ${label}`}
            title="Supprimer l'image"
          >
            ×
          </button>
        )}
      </div>

      <label
        className={`dropzone ${isDragging ? "drag-active" : ""} ${file ? "has-file" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          className="file-input"
        />

        {preview ? (
          <img src={preview} alt={label} className="preview-image" />
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
            <p className="file-size">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </>
        ) : (
          <p className="file-placeholder">Formats image acceptés</p>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [gridFile, setGridFile] = useState(null);
  const [defsFile, setDefsFile] = useState(null);

  const [gridPreview, setGridPreview] = useState(null);
  const [defsPreview, setDefsPreview] = useState(null);

  const [resultGrid, setResultGrid] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!gridFile) {
      setGridPreview(null);
      return;
    }
    const url = URL.createObjectURL(gridFile);
    setGridPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [gridFile]);

  useEffect(() => {
    if (!defsFile) {
      setDefsPreview(null);
      return;
    }
    const url = URL.createObjectURL(defsFile);
    setDefsPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [defsFile]);

  const runSolver = async () => {
    if (resultGrid && showResult) {
      setShowResult(false);
      return;
    }

    if (!gridFile || !defsFile) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("grid_image", gridFile);
    formData.append("definitions_image", defsFile);

    try {
      const res = await fetch("/api/solve", {
        method: "POST",
        body: formData,
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
      setLoading(false);
    }
  };

  const handleGridFileChange = (file) => {
    setGridFile(file);
    setResultGrid(null);
    setShowResult(false);
  };

  const handleDefsFileChange = (file) => {
    setDefsFile(file);
    setResultGrid(null);
    setShowResult(false);
  };

  const removeGrid = () => {
    setGridFile(null);
    setGridPreview(null);
    setResultGrid(null);
    setShowResult(false);
  };

  const removeDefs = () => {
    setDefsFile(null);
    setDefsPreview(null);
    setResultGrid(null);
    setShowResult(false);
  };

  return (
    <div className="app-shell">
      <div className="app">
        <div className="hero">
          <p className="eyebrow">Crossword Solver</p>
          <h1>Analyse ta grille et remplis les réponses automatiquement</h1>
          <p className="hero-text">
            Dépose l’image de la grille et celle des définitions, puis lance
            l’analyse.
          </p>
        </div>

        <div className="upload-grid">
          <ImagePreview
            label="Image de la grille"
            file={gridFile}
            preview={gridPreview}
            onFileChange={handleGridFileChange}
            onRemove={removeGrid}
          />

          <ImagePreview
            label="Image des définitions"
            file={defsFile}
            preview={defsPreview}
            onFileChange={handleDefsFileChange}
            onRemove={removeDefs}
          />
        </div>

        <div className="actions">
          <button
            className={`solve-btn ${loading ? "loading" : ""}`}
            onClick={runSolver}
            disabled={loading || !gridFile || !defsFile}
          >
            {loading
              ? "Analyse en cours..."
              : resultGrid && showResult
              ? "Masquer le résultat"
              : "Lancer le solver"}
          </button>
        </div>

        {resultGrid && showResult && (
          <div className="result-section">
            <div className="result-head">
              <h2>Résultat</h2>
              <p>Grille reconstruite par le solveur</p>
            </div>

            <div
              className="result-grid"
              style={{
                gridTemplateColumns: `repeat(${resultGrid[0].length}, minmax(34px, 42px))`,
              }}
            >
              {resultGrid.flatMap((row, r) =>
                row.map((cell, c) => (
                  <div
                    key={`${r}-${c}`}
                    className={`result-cell ${cell === "#" ? "block" : ""}`}
                  >
                    {cell !== "#" && cell !== "." ? cell : ""}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}