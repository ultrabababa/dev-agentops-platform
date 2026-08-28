import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./styles.css";
import "./typography.css";
import "./condition-polish.css";
import "./condition-layout-final.css";
import "./font-system.css";
import "./explorer.css";
import "./explorer-interview-polish.css";
import "./explorer-table-fixes.css";
import "./compare.css";
import "./compare-final.css";
import "./loading-state.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
