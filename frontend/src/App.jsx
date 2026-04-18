import React, { useState, useEffect } from "react";
import "./index.css";

function ImagePreview({ label, file, preview, onChange }) {
  return (
    <div className="upload-card">
      <label className="upload-label">{label}</label>

      <input
        type="file"
        accept="image/*"
        onChange={onChange}
      />

      <div className="preview-box">
        {preview ? (
          <img src={preview} alt={label} className="preview-image" />
        ) : (
          <span>Aucune image sélectionnée</span>
        )}
      </div>

      {file && <p className="file-name">{file.name}</p>}
    </div>
  );
}

export default function App() {
  const [gridFile, setGridFile] = useState(null);
  const [defsFile, setDefsFile] = useState(null);

  const [gridPreview, setGridPreview] = useState(null);
  const [defsPreview, setDefsPreview] = useState(null);

  const [resultGrid, setResultGrid] = useState(null);
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

  const handleGridChange = (e) => {
    const file = e.target.files?.[0];
    if (file) setGridFile(file);
  };

  const handleDefsChange = (e) => {
    const file = e.target.files?.[0];
    if (file) setDefsFile(file);
  };

  const runSolver = async () => {
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
      console.log(data);
      if (!res.ok || !data.success) {
        console.error("Erreur backend :", data.error);
        alert(data.error || "Erreur serveur");
        return;
      }

      setResultGrid(data.result);
    } catch (err) {
      console.error(err);
      alert("Erreur lors du lancement du solver");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>Solver de mots croisés</h1>

      <div className="upload-grid">
        <ImagePreview
          label="Image de la grille"
          file={gridFile}
          preview={gridPreview}
          onChange={handleGridChange}
        />

        <ImagePreview
          label="Image des définitions"
          file={defsFile}
          preview={defsPreview}
          onChange={handleDefsChange}
        />
      </div>

      <button
        className="solve-btn"
        onClick={runSolver}
        disabled={!gridFile || !defsFile || loading}
      >
        {loading ? "Analyse en cours..." : "Lancer le solver"}
      </button>

      {resultGrid && (
        <div
          className="result-grid"
          style={{
            gridTemplateColumns: `repeat(${resultGrid[0].length}, 42px)`,
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
      )}
    </div>
  );
}