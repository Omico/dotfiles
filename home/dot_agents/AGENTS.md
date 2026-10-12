# Global Agent Instructions

- Before each task, follow `~/Git/Omico/memory/AGENTS.md` if readable.
- Apply memory repository rules only within that repository.
- Resolve relative instruction paths from the containing file's directory.
- If memory retrieval or synchronization is unavailable, continue and briefly report the limitation.
- Remote writes require explicit authorization for the action and target, regardless of tool.
- Remote writes include pushes, remote branch or tag changes, PR or issue creation, PR merges, and releases.
- General task requests do not authorize remote writes.
- An explicit request for the remote action and target counts as authorization.
- Reuse existing authorization within its scope.
- Complete local preparation and validation before asking for missing authorization.
- Draft progress updates in ASD-STE100.
- Deliver all responses in the user's language unless requested otherwise.
