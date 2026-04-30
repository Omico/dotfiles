# Orchard Docs

This directory contains the design and implementation notes for the Rust
rewrite of Orchard.

## Documents

- [Manifest schema](manifest-schema.md): KDL app manifests, `platform` blocks,
  `fetch`, `download`, `install`, `bin`, and `action` nodes.
- [Architecture](architecture.md): Rust crate boundaries, validation, install
  flow, concurrency, errors, and testing.
- [Fish to KDL migration](fish-to-kdl-migration.md): Coverage of current Fish
  packages and the migration path to KDL.
- [Implementation plan](implementation-plan.md): Task-by-task execution plan
  for building the Rust implementation.

## Current Policy

Schema v1 supports multiple `platform` blocks in a manifest, but only
`platform "macos"` is executable. Non-macOS platform blocks are reserved for
future backends and should not influence the macOS implementation.
