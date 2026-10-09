import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { writeJsonLayers } from "../../.agents/skills/app-settings/scripts/pull-vscode-based.mjs";

for (const failure of ["replace", "rollback rename", "rollback copy"]) {
  test(`transaction recovers from ${failure} failure`, () => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), "settings-pull-"));
    try {
      const paths = ["shared", "code", "cursor"].map((name) =>
        path.join(directory, `${name}.json`),
      );
      for (const filename of paths) {
        fs.writeFileSync(
          filename,
          `{"original":"${path.basename(filename)}"}\n`,
        );
        fs.chmodSync(filename, 0o640);
      }
      const before = paths.map((filename) => fs.readFileSync(filename));
      const io = {
        ...fs,
        renameSync(source, destination) {
          if (destination === paths[1] && source.endsWith(".tmp"))
            throw new Error("forced replacement failure");
          if (
            failure !== "replace" &&
            destination === paths[0] &&
            source.endsWith(".bak")
          )
            throw new Error("forced rollback rename failure");
          fs.renameSync(source, destination);
        },
        copyFileSync(source, destination) {
          if (
            failure === "rollback copy" &&
            destination === paths[0] &&
            source.endsWith(".bak")
          )
            throw new Error("forced rollback copy failure");
          fs.copyFileSync(source, destination);
        },
      };
      assert.throws(
        () =>
          writeJsonLayers(
            paths.map((filename) => [filename, { new: true }]),
            io,
          ),
        failure === "rollback copy"
          ? /recovery backups preserved/
          : /forced replacement failure/,
      );
      for (let i = 0; i < paths.length; i++) {
        if (i === 0 && failure === "rollback copy")
          assert.notDeepEqual(fs.readFileSync(paths[i]), before[i]);
        else assert.deepEqual(fs.readFileSync(paths[i]), before[i]);
        assert.equal(fs.statSync(paths[i]).mode & 0o777, 0o640);
      }
      const backups = fs
        .readdirSync(directory)
        .filter((name) => name.endsWith(".bak"));
      assert.equal(backups.length, failure === "rollback copy" ? 1 : 0);
      if (backups.length)
        assert.deepEqual(
          fs.readFileSync(path.join(directory, backups[0])),
          before[0],
        );
      assert.equal(
        fs.readdirSync(directory).filter((name) => name.endsWith(".tmp"))
          .length,
        0,
      );
    } finally {
      fs.rmSync(directory, { recursive: true, force: true });
    }
  });
}

test("failed transaction removes newly created layers", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "settings-pull-"));
  try {
    const paths = ["shared", "code", "cursor"].map((name) =>
      path.join(directory, `${name}.json`),
    );
    const io = {
      ...fs,
      renameSync(source, destination) {
        if (destination === paths[1])
          throw new Error("forced replacement failure");
        fs.renameSync(source, destination);
      },
    };
    assert.throws(
      () =>
        writeJsonLayers(
          paths.map((filename) => [filename, {}]),
          io,
        ),
      /forced replacement failure/,
    );
    assert.deepEqual(fs.readdirSync(directory), []);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

test("CLI keeps integer precision and distinguishes numeric types and prototype keys", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "settings-pull-"));
  try {
    const code = path.join(directory, "code-input.json"),
      cursor = path.join(directory, "cursor-input.json");
    fs.writeFileSync(
      code,
      '{"large":9007199254740993,"different":9007199254740992,"typed":1,"__proto__":{"v":true},"float":1.0}',
    );
    fs.writeFileSync(
      cursor,
      '{"large":9007199254740993,"different":9007199254740993,"typed":1.0,"__proto__":{"v":true},"float":1e0}',
    );
    const command = fileURLToPath(
      new URL(
        "../../.agents/skills/app-settings/scripts/pull-vscode-based.mjs",
        import.meta.url,
      ),
    );
    const result = spawnSync(
      "bun",
      [
        "run",
        "--install=force",
        command,
        "--code",
        code,
        "--cursor",
        cursor,
        "--out",
        directory,
      ],
      { encoding: "utf8", cwd: os.tmpdir() },
    );
    assert.equal(result.status, 0, result.stderr);
    const shared = fs.readFileSync(path.join(directory, "shared.json"), "utf8");
    assert.match(shared, /"large": 9007199254740993/u);
    assert.match(shared, /"float": 1\.0/u);
    assert.ok(Object.hasOwn(JSON.parse(shared), "__proto__"));
    assert.match(
      fs.readFileSync(path.join(directory, "code.json"), "utf8"),
      /"different": 9007199254740992/u,
    );
    assert.match(
      fs.readFileSync(path.join(directory, "cursor.json"), "utf8"),
      /"typed": 1\.0/u,
    );
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
