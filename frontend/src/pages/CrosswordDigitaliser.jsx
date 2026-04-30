import React, { useMemo, useState, useRef, useEffect, useCallback } from "react";
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
    if (dropped && dropped.type?.startsWith("image/")) {
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

function Cell({
  cell,
  onChange,
  direction,
  toggleDirection,
  moveCaret,
  inputRef,
  activeCell,
  changeActiveCell,
  cells,
}) {
  if (cell.isBlock) return <div className="cell block" />;

  const getWordCells = useCallback(() => {
    if (!activeCell) return [];
    const word = [];

    if (direction === "h") {
      let c = activeCell.col;
      while (
        c >= 0 &&
        !cells.find((cl) => cl.row === activeCell.row && cl.col === c)?.isBlock
      ) {
        c--;
      }
      c++;
      while (
        c < cells.filter((cl) => cl.row === activeCell.row).length &&
        !cells.find((cl) => cl.row === activeCell.row && cl.col === c)?.isBlock
      ) {
        word.push(`${activeCell.row}-${c}`);
        c++;
      }
    } else {
      let r = activeCell.row;
      while (
        r >= 0 &&
        !cells.find((cl) => cl.row === r && cl.col === activeCell.col)?.isBlock
      ) {
        r--;
      }
      r++;
      while (
        r < Math.max(...cells.map((cl) => cl.row)) + 1 &&
        !cells.find((cl) => cl.row === r && cl.col === activeCell.col)?.isBlock
      ) {
        word.push(`${r}-${activeCell.col}`);
        r++;
      }
    }

    return word;
  }, [activeCell, direction, cells]);

  const isSelectedWord = getWordCells().includes(`${cell.row}-${cell.col}`);

  return (
    <div className="cell">
      <input
        ref={inputRef}
        className={`cell-input ${isSelectedWord ? "selected" : ""} ${
          cell.isWrong ? "line-through" : ""
        }`}
        maxLength={1}
        value={cell.value}
        onClick={() => {
          changeActiveCell(cell.row, cell.col);
          if (cell.row === activeCell?.row && cell.col === activeCell?.col) {
            toggleDirection();
          }
        }}
        onKeyDown={(e) => {
          if (e.key === "ArrowRight") {
            e.preventDefault();
            moveCaret(cell.row, cell.col + 1);
          } else if (e.key === "ArrowLeft") {
            e.preventDefault();
            moveCaret(cell.row, cell.col - 1);
          } else if (e.key === "ArrowDown") {
            e.preventDefault();
            moveCaret(cell.row + 1, cell.col);
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            moveCaret(cell.row - 1, cell.col);
          } else if (e.key === " ") {
            e.preventDefault();
            onChange(cell.row, cell.col, "");
            if (direction === "h") {
              moveCaret(cell.row, cell.col + 1);
            } else {
              moveCaret(cell.row + 1, cell.col);
            }
          } else if (e.key === "Backspace" || e.key === "Delete") {
            e.preventDefault();
            onChange(cell.row, cell.col, "");
            if (direction === "h") {
              moveCaret(cell.row, cell.col - 1);
            } else {
              moveCaret(cell.row - 1, cell.col);
            }
          }
          else if (/^[a-zA-Z]$/.test(e.key)) {
            e.preventDefault();
            const v = e.key.toUpperCase();
            onChange(cell.row, cell.col, v);

            if (direction === "h") {
              moveCaret(cell.row, cell.col + 1);
            } else {
              moveCaret(cell.row + 1, cell.col);
            }
         }
        }}
        onChange={(e) => {
          const v = e.target.value.toUpperCase().replace(/[^A-Z]/g, "");
          onChange(cell.row, cell.col, v);

          if (v !== "") {
            if (direction === "h") {
              moveCaret(cell.row, cell.col + 1);
            } else {
              moveCaret(cell.row + 1, cell.col);
            }
          }
        }}
      />
    </div>
  );
}

function CluesColumn({ title, list, direction, onClueClick }) {
  return (
    <div className="clues-column">
      <h3>{title}</h3>
      <ul>
        {list.map((item) => (
          <li key={item.number} onClick={() => onClueClick(item)}>
            <strong>{item.number}</strong> {item.clue} <em>({item.length})</em>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function App() {
  const [gridFile, setGridFile] = useState(null);
  const [defsFile, setDefsFile] = useState(null);
  const [gridPreview, setGridPreview] = useState(null);
  const [defsPreview, setDefsPreview] = useState(null);

  const [rows, setRows] = useState(0);
  const [cols, setCols] = useState(0);
  const [cells, setCells] = useState([]);
  const [horizontalClues, setHorizontalClues] = useState([]);
  const [verticalClues, setVerticalClues] = useState([]);
  const [direction, setDirection] = useState("h");
  const [activeCell, setActiveCell] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const inputRefs = useRef([]);

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

  useEffect(() => {
    inputRefs.current = [];
    for (let r = 0; r < rows; r++) {
      inputRefs.current[r] = [];
      for (let c = 0; c < cols; c++) {
        inputRefs.current[r][c] = null;
      }
    }
  }, [rows, cols]);

  useEffect(() => {
    if (activeCell && inputRefs.current[activeCell.row]?.[activeCell.col]) {
        inputRefs.current[activeCell.row][activeCell.col].focus();
    }
    }, [activeCell]);

  const resetAll = () => {
    setRows(0);
    setCols(0);
    setCells([]);
    setHorizontalClues([]);
    setVerticalClues([]);
    setError("");
    setActiveCell(null);
  };

  const runDigitalise = async () => {
  if (!gridFile || !defsFile) return;

  setLoading(true);
  setError("");
  resetAll();

  const formData = new FormData();
  formData.append("grid_image", gridFile);
  formData.append("definitions_image", defsFile);

  try {
    const res = await fetch("/api/digitalise", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      setError(data.error || "Erreur serveur");
      return;
    }

    // Grille depuis black_cells
    const blackSet = new Set(
      (data.grid.black_cells || []).map(([r, c]) => `${r}-${c}`)
    );

    // Numéros de cellules + clues
    const cellNumbers = new Map();
    const horizontal = [];
    const vertical = [];

    (data.definitions || []).forEach((def) => {
      if (!def.pos || !def.definition || !def.taille || !def.direction) return;

      const [x, y] = def.pos; 
      const row = y;
      const col = x;
      const rowletter = String.fromCharCode(65 + row);
      const colnumber = col + 1;
      const number = def.direction === "H" ? `${rowletter}.${colnumber}` : `${colnumber}.${rowletter}`;

      // Numéro de cellule
      cellNumbers.set(`${row}-${col}`, number);

      // Clue selon direction
      const clueItem = {
        number,
        clue: def.definition,
        length: def.taille,
        pos: [col, row], 
      };

      const dir = def.direction;
      if (dir === "H") {
        horizontal.push(clueItem);
      } else if (dir === "V") {
        vertical.push(clueItem);
      }
    });

    // Construire cellules avec numéros
    const newCells = [];
    for (let r = 0; r < data.grid.nb_rows; r++) {
      for (let c = 0; c < data.grid.nb_cols; c++) {
        const isBlock = blackSet.has(`${r}-${c}`);
        const number = cellNumbers.get(`${r}-${c}`) || null;
        newCells.push({
          row: r,
          col: c,
          isBlock,
          isWrong: false,
          solution: "",
          value: "",
          number,
        });
      }
    }

    setHorizontalClues(horizontal);
    setVerticalClues(vertical);
    setRows(data.grid.nb_rows);
    setCols(data.grid.nb_cols);
    setCells(newCells);

  } catch (err) {
    console.error(err);
    setError("Erreur lors de la digitalisation");
  } finally {
    setLoading(false);
  }
};

  const moveCaret = (r, c) => {
    if (r >= 0 && r < rows && c >= 0 && c < cols) {
      const cell = cells.find(cell => cell.row === r && cell.col === c);
      if (cell && !cell.isBlock) {
        setActiveCell({ row: r, col: c });
      }
    }
  };

  const handleChange = (r, c, v) => {
    setCells((prev) =>
      prev.map((cell) =>
        cell.row === r && cell.col === c ? { ...cell, value: v, isWrong: false } : cell
      )
    );
  };

  const toggleDirection = () => {
    setDirection((prev) => (prev === "h" ? "v" : "h"));
    };

    useEffect(() => {
    if (activeCell) {
        inputRefs.current[activeCell.row]?.[activeCell.col]?.focus();
    }
  }, [direction, activeCell]);

  const changeActiveCell = (r, c) => {
    setActiveCell({ row: r, col: c });
  };
  
  const reset = () => {
    if (isProcessing) return;
    setIsProcessing(true);
    setCells((prev) =>
      prev.map((cell) => (cell.isBlock ? cell : { ...cell, value: "", isWrong: false }))
    );
    setTimeout(() => setIsProcessing(false), 100);
  };

  const retour = () => {
    window.location.href = "/digitaliser";
 };

  const onClueClick = (clue) => {
    if (clue.pos) {
        const [col, row] = clue.pos;

        setDirection(
            horizontalClues.some((item) => item.number === clue.number) ? "h" : "v"
        );

        changeActiveCell(row, col);

        const input = inputRefs.current[row]?.[col];
        if (input) {
        input.focus();
        }
    }
    };

  if (rows === 0) {
    return (
    <div className="app-shell">
        <div className="app">
            <div className="hero">
            <p className="eyebrow">Crossword Digitizer</p>
            <div className="title-bar">
                <h1>Digitalise ta grille et remplis-la</h1>
                <button className="home-btn" onClick={() => navigate("/")}
                >⌂ Home</button>
            </div>
            <p className="hero-text">
                Dépose l'image de la grille et celle des définitions, puis édite !
            </p>
            </div>

            <div className="upload-grid">
            <ImagePreview
                label="Image de la grille"
                file={gridFile}
                preview={gridPreview}
                onFileChange={(f) => {
                setGridFile(f);
                resetAll();
                }}
                onRemove={() => {
                setGridFile(null);
                setGridPreview(null);
                resetAll();
                }}
            />

            <ImagePreview
                label="Image des définitions"
                file={defsFile}
                preview={defsPreview}
                onFileChange={(f) => {
                setDefsFile(f);
                resetAll();
                }}
                onRemove={() => {
                setDefsFile(null);
                setDefsPreview(null);
                resetAll();
                }}
            />
            </div>

            <div className="actions">
            <button
                className={`solve-btn ${loading ? "loading" : ""}`}
                onClick={runDigitalise}
                disabled={loading || !gridFile || !defsFile}
            >
                {loading ? "Digitalisation..." : "Digitaliser"}
            </button>
            </div>

            {error && <div className="error-box">{error}</div>}
        </div>
    </div>
    );
  }

  const rowLabels = Array.from({ length: rows }, (_, i) => String.fromCharCode(65 + i));
  const colLabels = Array.from({ length: cols }, (_, i) => i + 1);

  return (
    <div className="app">
        <div className="hero">
          <p className="eyebrow">Crossword Digitizer</p>
          <div className="title-bar">
             <h1>Digitalise ta grille et remplis-la</h1>
            <button className="home-btn" onClick={() => navigate("/")}
            >⌂ Home</button>
          </div>
          <p className="hero-text">
            Dépose l'image de la grille et celle des définitions, puis édite !
          </p>
        </div>
      <div className="main">
        <div className="grid-area">
          <div
            className="grid-with-coords"
            style={{
              display: "grid",
              gridTemplateColumns: `44px repeat(${cols}, 44px)`,
            }}
          >
            <div />
            {colLabels.map((col) => (
              <div key={col} className="coord-label">{col}</div>
            ))}
            {cells.map((cell) => {
              const row = cell.row;
              const col = cell.col;
              return (
                <React.Fragment key={`${row}-${col}`}>
                  {col === 0 && <div className="coord-label">{rowLabels[row]}</div>}
                  <Cell
                    cell={cell}
                    onChange={handleChange}
                    direction={direction}
                    toggleDirection={toggleDirection}
                    moveCaret={moveCaret}
                    inputRef={(el) => {
                    if (!inputRefs.current[row]) {
                        inputRefs.current[row] = [];
                    }
                        inputRefs.current[row][col] = el;
                    }}
                    cells={cells}
                    activeCell={activeCell}
                    changeActiveCell={changeActiveCell}
                  />
                </React.Fragment>
              );
            })}
          </div>
          <div className="controls">
            <button onClick={reset} disabled={isProcessing}>
              Réinitialiser la grille actuelle
            </button>
            <button onClick={retour} disabled={isProcessing}>
              Digitaliser une autre grille
            </button>
          </div>
        </div>
        <div className="clues">
          <button className="direction-btn" onClick={toggleDirection}>
            Direction : {direction === "h" ? "→ Horizontal" : "↓ Vertical"}
          </button>
          {direction === "h" ? (
            <CluesColumn
              title="Horizontal"
              list={horizontalClues}
              direction={direction}
              onClueClick={onClueClick}
            />
          ) : (
            <CluesColumn
              title="Vertical"
              list={verticalClues}
              direction={direction}
              onClueClick={onClueClick}
            />
          )}
        </div>
      </div>
    </div>
  );
}