import { spawnSync } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// =============================================================================
// Repo / docs roots
// =============================================================================

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const docsRoot = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(docsRoot, "..");
const configPath = path.join(repoRoot, ".markdownlint-cli2.yaml");
const cliPath = path.join(
  docsRoot,
  "node_modules",
  ".bin",
  "markdownlint-cli2",
);

const USAGE =
  "Usage: node docs/scripts/markdownlint.mjs [--fix] [markdownlint-cli2 args...]";

const HARD_WRAP_HINT =
  "hard-wrap: keep each paragraph or list item on one physical line.";

const FENCE_RE = /^[ \t]{0,3}(```|~~~)/;
const SKIPPED_LINE_RE =
  /^[ \t]{4,}\S|^[ \t]{0,3}(\| |[|:]?-{3,}|:{3,}|<!--|<\/?[A-Za-z]|\[[^\]]+\]:)/;
const BLOCK_START_RE =
  /^[ \t]{0,3}(#{1,6}[ \t]|>|([-+*]|[0-9]+[.)])[ \t]+|([-*_][ \t]*){3,}$)/;
const LIST_ITEM_RE = /^[ \t]{0,3}([-+*]|[0-9]+[.)])[ \t]+/;

// =============================================================================
// FS helpers
// =============================================================================

async function walkMarkdownDir(dir, files) {
  let entries;

  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      await walkMarkdownDir(fullPath, files);
      continue;
    }

    if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(path.relative(repoRoot, fullPath));
    }
  }
}

async function collectMarkdownFiles() {
  const files = [];

  for (const entry of await fs.readdir(repoRoot, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(entry.name);
    }
  }

  await walkMarkdownDir(path.join(repoRoot, ".agents"), files);
  await walkMarkdownDir(path.join(docsRoot, "src"), files);

  return files.sort();
}

// =============================================================================
// markdownlint-cli2
// =============================================================================

function runMarkdownlintCli2(files, extraArgs) {
  if (!files.length) {
    return 0;
  }

  const result = spawnSync(
    cliPath,
    [...files, "--config", configPath, ...extraArgs],
    { cwd: repoRoot, encoding: "utf8" },
  );

  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`.trimEnd();
  if (output) {
    console.error(output);
  }

  return result.status ?? 1;
}

// =============================================================================
// Hard-wrap checker
// =============================================================================

function findHardWrapViolations(filePath, content) {
  const state = { inFence: false, inFrontmatter: false, previousLine: 0 };
  const violations = [];

  for (const [index, line] of content.split("\n").entries()) {
    const displayLine = index + 1;
    const trimmed = line.trim();

    if (displayLine === 1 && trimmed === "---") {
      state.inFrontmatter = true;
      state.previousLine = 0;
      continue;
    }

    if (state.inFrontmatter) {
      if (displayLine > 1 && trimmed === "---") {
        state.inFrontmatter = false;
      }

      state.previousLine = 0;
      continue;
    }

    if (FENCE_RE.test(line)) {
      state.inFence = !state.inFence;
      state.previousLine = 0;
      continue;
    }

    if (state.inFence || !line.trim() || SKIPPED_LINE_RE.test(line)) {
      state.previousLine = 0;
      continue;
    }

    const startsBlock = BLOCK_START_RE.test(line);

    if (state.previousLine > 0 && !startsBlock) {
      violations.push(`${filePath}:${state.previousLine}: hard-wrap`);
    }

    if (startsBlock && !LIST_ITEM_RE.test(line)) {
      state.previousLine = 0;
    } else if (line.endsWith("\\") || line.endsWith("  ")) {
      state.previousLine = 0;
    } else {
      state.previousLine = displayLine;
    }
  }

  return violations;
}

async function checkHardWraps(files) {
  const violations = [];
  let readFailed = false;

  for (const file of files) {
    const fullPath = path.join(repoRoot, file);

    try {
      const content = await fs.readFile(fullPath, "utf8");
      violations.push(...findHardWrapViolations(file, content));
    } catch (err) {
      console.error(`${file}: ${err.message}`);
      readFailed = true;
    }
  }

  if (violations.length > 0) {
    for (const violation of violations) {
      console.error(violation);
    }
    console.error(HARD_WRAP_HINT);
  }

  return readFailed || violations.length > 0 ? 1 : 0;
}

// =============================================================================
// Main
// =============================================================================

async function main() {
  const argv = process.argv.slice(2);

  if (argv.some((arg) => arg === "-h" || arg === "--help")) {
    console.log(USAGE);
    return;
  }

  try {
    await fs.access(cliPath);
  } catch {
    console.error("markdownlint-cli2 is not installed. Run `npm ci` in docs/.");
    process.exitCode = 1;
    return;
  }

  const files = await collectMarkdownFiles();
  const lintStatus = runMarkdownlintCli2(files, argv);
  const hardWrapStatus = await checkHardWraps(files);

  if (lintStatus !== 0 || hardWrapStatus !== 0) {
    console.error("markdownlint: failed");
    process.exitCode = 1;
    return;
  }

  console.log("markdownlint: ok");
}

main().catch((err) => {
  console.error("markdownlint:", err);
  process.exitCode = 1;
});
