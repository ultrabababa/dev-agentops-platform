import { access, cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDir, "../..");
const sourceDir = resolve(repositoryRoot, "docs/architecture");
const destinationDir = resolve(repositoryRoot, "frontend/public/architecture-assets");

const artifacts = [
  "system.html",
  "system.svg",
  "evaluation-workflow.html",
  "evaluation-workflow.svg",
  "l4-runtime.html",
  "l4-runtime.svg",
];

const readerMinWidth = new Map([
  ["evaluation-workflow.html", 1460],
  ["l4-runtime.html", 1760],
]);

async function localArtifactsAvailable() {
  try {
    await Promise.all(artifacts.map((artifact) => access(resolve(sourceDir, artifact))));
    return true;
  } catch {
    return false;
  }
}

async function fetchPinnedArtifact(artifact) {
  const repository = process.env.RENDER_GIT_REPO_SLUG ?? "ultrabababa/dev-agentops-platform";
  const revision = process.env.RENDER_GIT_COMMIT;
  if (!revision) {
    throw new Error(
      `docs/architecture is unavailable and RENDER_GIT_COMMIT is not set; cannot sync ${artifact}`,
    );
  }

  const url = `https://raw.githubusercontent.com/${repository}/${revision}/docs/architecture/${artifact}`;
  const response = await fetch(url, {
    headers: { "user-agent": "devagentops-architecture-sync" },
  });
  if (!response.ok) {
    throw new Error(`failed to fetch ${artifact} from ${repository}@${revision}: ${response.status}`);
  }
  return response.text();
}

function addReadableDiagramMode(html, artifact) {
  const minimumWidth = readerMinWidth.get(artifact);
  if (!minimumWidth || html.includes('data-reader="true"')) return html;

  const presentBlock = `          if (new URLSearchParams(window.location.search).get('present') === '1') {
            document.documentElement.setAttribute('data-present', 'true');
          }`;
  const readerBlock = `${presentBlock}
          if (new URLSearchParams(window.location.search).get('reader') === '1') {
            document.documentElement.setAttribute('data-reader', 'true');
          }`;

  if (!html.includes(presentBlock)) {
    throw new Error(`cannot add reader query handling to ${artifact}: presentation marker not found`);
  }
  html = html.replace(presentBlock, readerBlock);

  const presentationMarker = `    /* Presentation Stage is a viewer-only layer: it gives the live diagram`;
  const readerCss = `    /* DevAgentOps public reader mode: preserve Archify interaction while
       giving dense Workflow / Sequence diagrams a readable physical scale.
       Smaller viewports scroll the diagram instead of shrinking its text. */
    html[data-reader="true"] body {
      min-height: 100vh;
      padding: 1rem;
      overflow: auto;
      background-attachment: fixed;
    }
    html[data-reader="true"] .container {
      width: 100%;
      max-width: none;
      margin: 0;
    }
    html[data-reader="true"] .header,
    html[data-reader="true"] .cards,
    html[data-reader="true"] .guided-views {
      display: none !important;
    }
    html[data-reader="true"] .diagram-container {
      width: 100%;
      padding: 1rem;
      overflow: auto;
    }
    html[data-reader="true"] .diagram-container > svg {
      width: max(calc(100vw - 4rem), ${minimumWidth}px);
      min-width: ${minimumWidth}px;
      max-width: none;
      height: auto;
      margin: 0 auto;
    }
    @media (max-width: 720px) {
      html[data-reader="true"] body { padding: 0.5rem; }
      html[data-reader="true"] .diagram-container { padding: 0.5rem; }
      html[data-reader="true"] .diagram-container > svg {
        width: ${minimumWidth}px;
        min-width: ${minimumWidth}px;
      }
    }

`;

  if (!html.includes(presentationMarker)) {
    throw new Error(`cannot add reader styles to ${artifact}: presentation CSS marker not found`);
  }
  return html.replace(presentationMarker, `${readerCss}${presentationMarker}`);
}

await rm(destinationDir, { recursive: true, force: true });
await mkdir(destinationDir, { recursive: true });

const useLocalSource = await localArtifactsAvailable();

for (const artifact of artifacts) {
  const source = resolve(sourceDir, artifact);
  const destination = resolve(destinationDir, artifact);

  if (artifact.endsWith(".html")) {
    const original = useLocalSource
      ? await readFile(source, "utf8")
      : await fetchPinnedArtifact(artifact);
    await writeFile(destination, addReadableDiagramMode(original, artifact), "utf8");
    continue;
  }

  if (useLocalSource) {
    await cp(source, destination);
  } else {
    await writeFile(destination, await fetchPinnedArtifact(artifact), "utf8");
  }
}

console.log(
  `Synced ${artifacts.length} architecture artifacts from ${useLocalSource ? "local docs/architecture" : `GitHub revision ${process.env.RENDER_GIT_COMMIT}`} to frontend/public/architecture-assets`,
);
