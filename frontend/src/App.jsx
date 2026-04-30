import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Digitaliser from "./pages/CrosswordDigitaliser";
import Solver from "./pages/CrosswordSolver";
import ThematicGenerator from "./pages/CrosswordThematicGenerator";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/digitaliser" element={<Digitaliser />} />
        <Route path="/solver" element={<Solver />} />
        <Route path="/thematic-generator" element={<ThematicGenerator />} />
      </Routes>
    </BrowserRouter>
  );
}