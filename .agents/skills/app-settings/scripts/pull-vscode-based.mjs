#!/usr/bin/env -S bun run --install=force
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

class InputError extends Error {}

// Keep the source token: parseTree's numeric value can round large integers.
class JsonNumber {
  constructor(raw) {
    this.raw = raw;
    this.integer = !/[.eE]/u.test(raw);
    this.value = this.integer ? BigInt(raw) : Number(raw);
  }
}

function location(source, offset) {
  const prefix = source.slice(0, offset);
  return `${prefix.split("\n").length}:${Array.from(prefix.slice(prefix.lastIndexOf("\n") + 1)).length + 1}`;
}

export async function loadJsoncObject(filename) {
  const { parseTree, printParseErrorCode } = await import("jsonc-parser@3.3.1");
  let source;
  try {
    if (!fs.lstatSync(filename).isFile())
      throw new Error("input is not a regular file");
    source = new TextDecoder("utf-8", { fatal: true }).decode(
      fs.readFileSync(filename),
    );
  } catch (error) {
    throw new InputError(`Error: failed to read ${filename}: ${error.message}`);
  }
  const errors = [];
  const root = parseTree(source, errors, {
    allowTrailingComma: true,
    allowEmptyContent: false,
  });
  if (errors.length) {
    const error = errors[0];
    throw new InputError(
      `Error: invalid JSONC in ${filename}:${location(source, error.offset)}: ${printParseErrorCode(error.error)}`,
    );
  }
  if (root?.type !== "object") {
    throw new InputError(
      `Error: invalid JSONC in ${filename}:1:1: expected a JSON object`,
    );
  }
  function decode(node) {
    if (node.type === "object") {
      const result = Object.create(null);
      for (const property of node.children ?? [])
        result[property.children[0].value] = decode(property.children[1]);
      return result;
    }
    if (node.type === "array") return (node.children ?? []).map(decode);
    if (node.type === "number") {
      const raw = source.slice(node.offset, node.offset + node.length);
      if (!Number.isFinite(Number(raw))) {
        throw new InputError(
          `Error: invalid JSONC in ${filename}:${location(source, node.offset)}: Number too big to be stored in double`,
        );
      }
      return new JsonNumber(raw);
    }
    return node.value;
  }
  return decode(root);
}

function loadIgnoredKeys(filename) {
  let stat;
  try {
    stat = fs.lstatSync(filename);
  } catch (error) {
    if (error.code === "ENOENT") return new Set();
    throw new InputError(
      `Error: invalid JSON in ${filename}: ${error.message}`,
    );
  }
  if (!stat.isFile())
    throw new InputError(
      `Error: ignored input is not a regular file: ${filename}`,
    );
  let data;
  try {
    // Unlike live JSONC, ignored inputs use strict JSON and do not strip a BOM.
    const source = new TextDecoder("utf-8", {
      fatal: true,
      ignoreBOM: true,
    }).decode(fs.readFileSync(filename));
    data = JSON.parse(source);
  } catch (error) {
    throw new InputError(
      `Error: invalid JSON in ${filename}: ${error.message}`,
    );
  }
  if (!Array.isArray(data) || !data.every((item) => typeof item === "string")) {
    throw new InputError(
      `Error: ignored file must be a JSON array of strings: ${filename}`,
    );
  }
  return new Set(data);
}

export function serializeJson(data) {
  return (
    JSON.stringify(
      data,
      (_, value) =>
        value instanceof JsonNumber ? JSON.rawJSON(value.raw) : value,
      2,
    ) + "\n"
  );
}

function equal(left, right) {
  if (left instanceof JsonNumber || right instanceof JsonNumber) {
    return (
      left instanceof JsonNumber &&
      right instanceof JsonNumber &&
      left.integer === right.integer &&
      left.value === right.value
    );
  }
  if (
    left === null ||
    right === null ||
    typeof left !== "object" ||
    typeof right !== "object"
  )
    return left === right;
  if (Array.isArray(left) !== Array.isArray(right)) return false;
  const keys = Object.keys(left);
  return (
    keys.length === Object.keys(right).length &&
    keys.every(
      (key) => Object.hasOwn(right, key) && equal(left[key], right[key]),
    )
  );
}

function classify(code, cursor, ignored, codeIgnored, cursorIgnored) {
  code = Object.fromEntries(
    Object.entries(code).filter(
      ([key]) => !ignored.has(key) && !codeIgnored.has(key),
    ),
  );
  cursor = Object.fromEntries(
    Object.entries(cursor).filter(
      ([key]) => !ignored.has(key) && !cursorIgnored.has(key),
    ),
  );
  const shared = Object.create(null),
    codeOnly = Object.create(null),
    cursorOnly = Object.create(null);
  for (const key of [
    ...new Set([...Object.keys(code), ...Object.keys(cursor)]),
  ].sort()) {
    if (Object.hasOwn(code, key) && Object.hasOwn(cursor, key)) {
      if (equal(code[key], cursor[key])) shared[key] = code[key];
      else if (
        key === "yaml.disableSchemaDetection" &&
        Array.isArray(code[key]) &&
        Array.isArray(cursor[key]) &&
        code[key].length !== cursor[key].length
      ) {
        shared[key] =
          code[key].length > cursor[key].length ? code[key] : cursor[key];
      } else {
        codeOnly[key] = code[key];
        cursorOnly[key] = cursor[key];
      }
    } else if (Object.hasOwn(code, key)) codeOnly[key] = code[key];
    else cursorOnly[key] = cursor[key];
  }
  return [shared, codeOnly, cursorOnly];
}

export function writeJsonLayers(layers, io = fs) {
  const prepared = [],
    replaced = [],
    preserved = new Set();
  const remove = (filename) => {
    if (filename) {
      try {
        io.unlinkSync(filename);
      } catch {}
    }
  };
  try {
    for (const [filename, data] of layers) {
      io.mkdirSync(path.dirname(filename), { recursive: true });
      const exists = io.existsSync(filename);
      if (exists && !io.statSync(filename).isFile())
        throw new Error(`output path is not a regular file: ${filename}`);
      const temporary = path.join(
        path.dirname(filename),
        `.${path.basename(filename)}.${randomUUID()}.tmp`,
      );
      let backup;
      try {
        const fd = io.openSync(temporary, "wx", 0o600);
        try {
          io.writeFileSync(fd, serializeJson(data), "utf8");
          if (exists) io.fchmodSync(fd, io.statSync(filename).mode);
          io.fsyncSync(fd);
        } finally {
          io.closeSync(fd);
        }
        if (exists) {
          backup = path.join(
            path.dirname(filename),
            `.${path.basename(filename)}.${randomUUID()}.bak`,
          );
          const backupFd = io.openSync(backup, "wx", 0o600);
          io.closeSync(backupFd);
          io.copyFileSync(filename, backup);
          io.chmodSync(backup, io.statSync(filename).mode);
        }
        prepared.push({ filename, temporary, backup });
      } catch (error) {
        remove(temporary);
        remove(backup);
        throw error;
      }
    }
    for (const item of prepared) {
      io.renameSync(item.temporary, item.filename);
      replaced.push(item);
    }
  } catch (original) {
    const rollbackErrors = [];
    for (const { filename, backup } of replaced.reverse()) {
      try {
        if (!backup) io.unlinkSync(filename);
        else {
          try {
            io.renameSync(backup, filename);
          } catch {
            io.copyFileSync(backup, filename);
            io.chmodSync(filename, io.statSync(backup).mode);
          }
        }
      } catch (error) {
        if (backup) preserved.add(backup);
        rollbackErrors.push(`${filename}: ${error.message}`);
      }
    }
    if (rollbackErrors.length) {
      throw new Error(
        `failed to roll back managed layers: ${rollbackErrors.join("; ")}${preserved.size ? "; recovery backups preserved: " + [...preserved].sort().join(", ") : ""}`,
        { cause: original },
      );
    }
    throw original;
  } finally {
    for (const { temporary, backup } of prepared) {
      remove(temporary);
      if (!preserved.has(backup)) remove(backup);
    }
  }
}

function repoRoot() {
  let candidate = path.dirname(fileURLToPath(import.meta.url));
  while (true) {
    if (
      fs.existsSync(path.join(candidate, ".chezmoiroot")) ||
      fs.existsSync(path.join(candidate, ".git"))
    )
      return candidate;
    const parent = path.dirname(candidate);
    if (parent === candidate) return process.cwd();
    candidate = parent;
  }
}

const help = `Usage: bun run --install=force pull-vscode-based.mjs [--code PATH] [--cursor PATH] [--out PATH] [--dry-run]
Pull live Code/Cursor User settings into managed layers.
  --code PATH    Code settings.json (default: platform live path)
  --cursor PATH  Cursor settings.json (default: platform live path)
  --out PATH     Output directory (default: <repo>/app-settings/vscode-based)
  --dry-run      Print counts without writing files
  -h, --help     Show this help
Output: shared.json, code.json, cursor.json; ignored files are inputs only.
Exit codes: 0 success; 1 write failure; 2 usage or invalid input.
Example: bun run --install=force pull-vscode-based.mjs --code code.json --cursor cursor.json --out layers --dry-run`;

export async function main(args = process.argv.slice(2)) {
  let values;
  try {
    ({ values } = parseArgs({
      args,
      options: {
        code: { type: "string" },
        cursor: { type: "string" },
        out: { type: "string" },
        "dry-run": { type: "boolean" },
        help: { type: "boolean", short: "h" },
      },
    }));
  } catch (error) {
    console.error(`Error: ${error.message}\n${help}`);
    return 2;
  }
  if (values.help) {
    console.log(help);
    return 0;
  }
  const base = path.join(
    os.homedir(),
    process.platform === "darwin" ? "Library/Application Support" : ".config",
  );
  const codePath = values.code ?? path.join(base, "Code/User/settings.json");
  const cursorPath =
    values.cursor ?? path.join(base, "Cursor/User/settings.json");
  const out = values.out ?? path.join(repoRoot(), "app-settings/vscode-based");
  try {
    for (const [name, filename] of [
      ["Code", codePath],
      ["Cursor", cursorPath],
    ]) {
      let regular = false;
      try {
        regular = fs.lstatSync(filename).isFile();
      } catch {}
      if (!regular)
        throw new InputError(
          `Error: ${name} settings is not a regular file: ${filename}`,
        );
    }
    const code = await loadJsoncObject(codePath),
      cursor = await loadJsoncObject(cursorPath);
    const ignored = loadIgnoredKeys(path.join(out, "ignored.json"));
    const codeIgnored = loadIgnoredKeys(path.join(out, "code.ignored.json"));
    const cursorIgnored = loadIgnoredKeys(
      path.join(out, "cursor.ignored.json"),
    );
    const layers = classify(code, cursor, ignored, codeIgnored, cursorIgnored);
    const counts = `shared=${Object.keys(layers[0]).length} code=${Object.keys(layers[1]).length} cursor=${Object.keys(layers[2]).length} ignored=${ignored.size} code.ignored=${codeIgnored.size} cursor.ignored=${cursorIgnored.size}`;
    if (values["dry-run"]) {
      console.log(`${counts}\ndry-run: would write under ${out}`);
      return 0;
    }
    writeJsonLayers(
      ["shared.json", "code.json", "cursor.json"].map((name, i) => [
        path.join(out, name),
        layers[i],
      ]),
    );
    console.log(`${counts}\nwrote managed layers under ${out}`);
    return 0;
  } catch (error) {
    console.error(
      error instanceof InputError
        ? error.message
        : `Error: failed to write managed layers under ${out}: ${error.message}`,
    );
    return error instanceof InputError ? 2 : 1;
  }
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
)
  process.exitCode = await main();
