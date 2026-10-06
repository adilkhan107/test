import { NavLink, Route, Routes } from "react-router-dom";
import AnalysisDetail from "./pages/AnalysisDetail";
import Analyze from "./pages/Analyze";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden />
          <span>NirmaanAI</span>
        </div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/analyze">New analysis</NavLink>
          <NavLink to="/analyses">History</NavLink>
        </nav>
        <p className="side-note">Checks hardhats, vests and masks in site video.</p>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/analyses" element={<History />} />
          <Route path="/analyses/:id" element={<AnalysisDetail />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </div>
  );
}
