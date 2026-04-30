import { useNavigate } from "react-router-dom";
import "../index.css";

const TOOLS = [
  {
    path: "/solver",
    emoji: "🧩",
    title: "Solver de mots croisés",
    badge: "Cruciverbiste",
    description:
      "Charge deux images — la grille et les définitions. L'OCR extrait le texte, la structure matricielle est reconstruite, puis un algorithme de backtracking optimisé résout la grille en propageant les contraintes croisées.",
    tags: ["OpenCV", "Tesseract", "Scraping"],
  },
  {
    path: "/digitaliser",
    emoji: "🖼️",
    title: "Digitaliseur de grille",
    badge: "Cruciverbiste",
    description:
      "Dépose une photo ou un scan de grille. La zone est détectée automatiquement, les cases segmentées et classifiées, puis la grille est restituée dans une interface interactive pour la remplir, la modifier ou l'effacer.",
    tags: ["OpenCV", "React"],
  },
  {
    path: "/thematic-generator",
    emoji: "✨",
    title: "Générateur thématique",
    badge: "Verbicruciste",
    description:
      "Saisis un mot ou un thème de départ. Les termes sémantiquement proches sont récupérés via l'API JeuxDeMots, filtrés et regroupés dans un dictionnaire thématique, puis Wizium génère une grille cohérente.",
    tags: ["JeuxDeMots", "Wizium"],
  },
];

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="app-shell">
      <div className="app">
        <div className="home-layout">
          {/* ── Hero ── */}
          <div className="hero">
            <p className="eyebrow">HAI606I - L3 CMI Informatique</p>
            <h1>Recherche et développement d'outils pour les mots croisés</h1>
            <p className="hero-text">
              Une suite d'outils conçus pour accompagner la création et la résolution de grilles de mots croisés
              
            </p>
            <p className="hero-authors">
              COQUELLE Addison · FAURON Quentin · LAMKADDEM Yassine · THOMAS Lucas
            </p>
          </div>

          {/* ── Cards outils ── */}
          <div className="tools-grid">
            {TOOLS.map((tool) => (
              <button
                key={tool.path}
                className="tool-card"
                onClick={() => navigate(tool.path)}
              >
                {/* Header : icône + badge */}
                <div className="tool-card-header">
                  <div className="tool-icon">{tool.emoji}</div>
                  <span className="tool-badge">{tool.badge}</span>
                </div>

                {/* Texte */}
                <div className="tool-body">
                  <p className="tool-title">{tool.title}</p>
                  <p className="tool-desc">{tool.description}</p>
                </div>

                {/* Tags technos */}
                <div className="tool-tags">
                  {tool.tags.map((tag) => (
                    <span key={tag} className="tool-tag">{tag}</span>
                  ))}
                </div>

                {/* CTA */}
                <span className="tool-cta">
                  Ouvrir l'outil
                  <svg
                    width="13" height="13" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor"
                    strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                  >
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              </button>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}