import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../index.css";

function ImagePreview({ label, file, preview, onFileChange, onRemove }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleInputChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected && selected.type.startsWith("image/")) {
      onFileChange(selected);
    }
    e.target.value = null; 
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type && dropped.type.startsWith("image/")) {
      onFileChange(dropped);
    }
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
            title="Supprimer l'image"
          >
            ×
          </button>
        )}
      </div>

      <label
        className={`dropzone ${isDragging ? "drag-active" : ""} ${
          file ? "has-file" : ""
        }`}
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
      >
        <input
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          className="file-input"
        />

        {preview ? (
          <img
            key={preview} 
            src={preview}
            alt={label}
            className="preview-image"
          />
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

  const navigate = useNavigate();

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

  return (
    <div className="app-shell">
      <div className="app">
        <div className="hero">
          <p className="eyebrow">Crossword Solver</p>
          <div className="title-bar">
             <h1>Analyse ta grille et remplis les réponses automatiquement</h1>
            <button className="home-btn" onClick={() => navigate("/")}
            >⌂ Home</button>
          </div>
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
            onFileChange={(f) => {
              setGridFile(f);
              setResultGrid(null);
              setShowResult(false);
            }}
            onRemove={() => {
              setGridFile(null);
              setGridPreview(null);
              setResultGrid(null);
              setShowResult(false);
            }}
          />

          <ImagePreview
            label="Image des définitions"
            file={defsFile}
            preview={defsPreview}
            onFileChange={(f) => {
              setDefsFile(f);
              setResultGrid(null);
              setShowResult(false);
            }}
            onRemove={() => {
              setDefsFile(null);
              setDefsPreview(null);
              setResultGrid(null);
              setShowResult(false);
            }}
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
              ? "Réinitialiser"
              : "Lancer le solver"}
          </button>
        </div>

        {resultGrid && showResult && (
          <div className="result-section">
            <h2>Résultat</h2>

            <div
              className="grid-with-coords result-crossword"
              style={{
                display: "grid",
                gridTemplateColumns: `40px repeat(${resultGrid[0].length}, 44px)`,
              }}
            >
              <div />
              {resultGrid[0].map((_, col) => (
                <div key={`col-${col}`} className="coord-label">
                  {col + 1}
                </div>
              ))}

              {resultGrid.flatMap((row, r) => [
                <div key={`row-label-${r}`} className="coord-label">
                  {String.fromCharCode(65 + r)}
                </div>,
                ...row.map((cell, c) => (
                  <div
                    key={`${r}-${c}`}
                    className={`cell ${cell === "#" ? "block" : ""}`}
                  >
                    {cell !== "#" && cell !== "." && (
                      <div className="result-letter">{cell}</div>
                    )}
                  </div>
                )),
              ])}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}