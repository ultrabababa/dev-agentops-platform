import { access, cp, mkdir, rm, writeFile } from "node:fs/promises";
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

await rm(destinationDir, { recursive: true, force: true });
await mkdir(destinationDir, { recursive: true });

const useLocalSource = await localArtifactsAvailable();

for (const artifact of artifacts) {
  const destination = resolve(destinationDir, artifact);
  if (useLocalSource) {
    await cp(resolve(sourceDir, artifact), destination);
  } else {
    await writeFile(destination, await fetchPinnedArtifact(artifact), "utf8");
  }
}

console.log(
  `Synced ${artifacts.length} architecture artifacts from ${useLocalSource ? "local docs/architecture" : `GitHub revision ${process.env.RENDER_GIT_COMMIT}`} to frontend/public/architecture-assets`,
);
