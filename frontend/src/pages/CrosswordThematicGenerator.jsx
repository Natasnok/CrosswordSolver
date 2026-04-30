import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../index.css";

export default function App() {
  const [word, setWord] = useState("");
  const [resultGrid, setResultGrid] = useState(null);
  const [computeTime, setComputeTime] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gridWidth, setGridWidth] = useState(10);
  const [gridHeight, setGridHeight] = useState(10);

  const navigate = useNavigate();

  const formatComputeTime = (value) => {
    const n = Number(value);

    if (!Number.isFinite(n)) return "N/A";
    if (n < 1) return `${(n * 1000).toFixed(1)} ms`;
    return `${n.toFixed(3)} s`;
  };

  const runGenerator = async () => {
    if (resultGrid && showResult) {
      setShowResult(false);
      return;
    }

    if (!word.trim()) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("word", word.trim());
    formData.append("width", String(gridWidth));
    formData.append("height", String(gridHeight));

    try {
      const res = await fetch("/api/genthem", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.error || "Erreur serveur");
        return;
      }

      setResultGrid(
        data.result.map((row) => row.replace(/\n/g, "").split(""))
      );
      setComputeTime(data.compute_time ?? null);
      setShowResult(true);
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la génération");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app">
        <div className="hero">
          <p className="eyebrow">Thematic Crossword Generator</p>

          <div className="title-bar">
            <h1>Entre un seul mot et génère une grille thématique</h1>
            <button className="home-btn" onClick={() => navigate("/")}>
              ⌂ Home
            </button>
          </div>

          <p className="hero-text">
            Saisis un mot thème, puis lance la génération automatique.
          </p>
        </div>

        <div className="theme-generator-wrap">
          <div className="theme-card">
            <div className="theme-card-top">
              <label className="theme-label" htmlFor="theme-word">
                Mot thème
              </label>
            </div>

            <p className="theme-hint">
              Un seul mot suffit. Exemples : "espace", "manga", "Paris"...
            </p>

            <div className="theme-input-wrap">
              <input
                id="theme-word"
                type="text"
                className="theme-input"
                placeholder="Entrer un mot ou un thème de départ..."
                value={word}
                onChange={(e) => {
                  setWord(e.target.value);
                  setResultGrid(null);
                  setComputeTime(null);
                  setShowResult(false);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    runGenerator();
                  }
                }}
              />
            </div>

            <div className="theme-size-row">
                <div className="theme-size-field">
                    <label className="theme-label" htmlFor="grid-width">
                    Largeur
                    </label>
                    <input
                    id="grid-width"
                    type="number"
                    min="5"
                    max="20"
                    className="theme-input theme-number-input"
                    value={gridWidth}
                    onChange={(e) => {
                        const value = Number(e.target.value);
                        setGridWidth(value);
                        setResultGrid(null);
                        setComputeTime(null);
                        setShowResult(false);
                    }}
                    />
                </div>

                <div className="theme-size-field">
                    <label className="theme-label" htmlFor="grid-height">
                    Hauteur
                    </label>
                    <input
                    id="grid-height"
                    type="number"
                    min="5"
                    max="20"
                    className="theme-input theme-number-input"
                    value={gridHeight}
                    onChange={(e) => {
                        const value = Number(e.target.value);
                        setGridHeight(value);
                        setResultGrid(null);
                        setComputeTime(null);
                        setShowResult(false);
                    }}
                    />
                </div>
                </div>

            <div className="theme-meta">
              <p className="theme-meta-text">
                Attention : la génération peut prendre du temps selon
                le mot choisi et la complexité de la grille.
              </p>
              <p className="theme-count">{word.length} caractère(s)</p>
            </div>
          </div>
        </div>

        <div className="actions">
          <button
            className={`solve-btn ${loading ? "loading" : ""}`}
            onClick={runGenerator}
            disabled={loading || !word.trim()}
          >
            {loading
              ? "Génération en cours..."
              : resultGrid && showResult
              ? "Réinitialiser"
              : "Générer la grille"}
          </button>
        </div>

        {resultGrid && showResult && (
          <div className="result-section">
            <h2>Résultat</h2>

            <div className="result-stats">
              <div className="result-stat-card">
                <span className="result-stat-icon">⏱</span>
                <div className="result-stat-content">
                  <p className="result-stat-label">Temps de calcul</p>
                  <p className="result-stat-value">
                    {formatComputeTime(computeTime)}
                  </p>
                </div>
              </div>
            </div>

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