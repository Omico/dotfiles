# Global Agent Instructions

## Instruction sources

- Before each task, check `~/Git/Omico/memory/AGENTS.md`.
  - Read and follow it if present.
  - Otherwise, silently continue.
- Apply memory repository rules only within that repository.
- Resolve relative instruction paths from the containing file's directory.

## Authorization

- Preserve existing permissions and authorizations.
  - Reuse authorizations within their scope.
- Splitting work authorizes no commits, history rewrites, or remote writes.
- Remote writes include:
  - Pushes.
  - Remote branch or tag changes.
  - PR or issue creation.
  - PR merges.
  - Releases.
- Remote writes need explicit authorization, regardless of tool.
  - Authorization must specify the action and target.
  - An explicit request for both counts as authorization.
  - General task requests do not count.
- Complete local preparation and validation before requesting missing authorization.

## Chat scope

- Start a new chat for independent work in another workspace.
- Reuse a chat only for the same task or at the user's explicit direction.

## Workspace changes

- Avoid Git merges unless necessary.
- Before starting or expanding a task, assess change size:
  - Existing changes, including untracked files.
  - Expected additions.
- Divide scope into independently deliverable goals.
- Keep each workspace's changes reviewable.
- Split work early if current or expected changes hinder review.
  - Give each split goal a separate chat.
  - Use a separate worktree or working directory for each goal.
  - Run independent goals in parallel.
  - Preserve existing changes and the full task scope.
- Chats sharing one working tree still share its diff.
- Before parallel work:
  - Assign write ownership for shared files.
  - Set the integration order.

## Writing and communication

- For documents and text responses:
  - Apply ISO 24495-1 principles for relevant, findable, understandable, usable text.
  - Borrow ASD-STE100 practices suited to the language and content type.
    - Use short sentences, clear actions, and consistent technical terms.
- Keep progress updates concise.
  - Report meaningful progress, findings, blockers, or next steps.
- Deliver all responses in the user's language unless requested otherwise.
