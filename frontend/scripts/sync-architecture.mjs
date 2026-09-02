import { cp, mkdir, rm } from "node:fs/promises";
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

await rm(destinationDir, { recursive: true, force: true });
await mkdir(destinationDir, { recursive: true });

for (const artifact of artifacts) {
  await cp(resolve(sourceDir, artifact), resolve(destinationDir, artifact));
}

console.log(`Synced ${artifacts.length} architecture artifacts to frontend/public/architecture-assets`);
