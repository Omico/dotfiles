# Global Agent Instructions

## Instruction sources

- Resolve relative instruction paths from the containing file's directory.

## Instruction changes

- Base instruction changes on observed evidence or explicit user preferences.
- Before adding rules for a failure, check loading, conflicts, and tool availability.
- Keep global rules cross-project; put project rules and procedures with their owners.
- Preserve rule meaning and authorization outside the approved change.
- Validate changed behavior with realistic cases.

## Authorization

- Preserve and reuse existing permissions and authorizations within their scope.
- Splitting work authorizes no commits, history rewrites, or remote writes.
- Remote writes need explicit authorization naming the action and target, for any tool.
  - A request naming both suffices.
  - Includes pushes and remote branch or tag changes.
  - Also includes PR or issue creation, PR merges, and releases.
- Complete local preparation and validation before requesting missing authorization.

## Chat scope

- Start a new chat for independent work in another workspace.
- Reuse a chat only for the same task or at the user's explicit direction.

## Problem solving

- Default to `ast-grep` for code searches; use text search if unsuitable or unavailable.
- Define user-observable success before choosing a solution.
- For reported failures, collect evidence along the actual failure path.
- When a failure cannot be reproduced, state the resulting verification gap.
- Test the smallest direct change first.
- Reassess necessity when adding abstractions or accumulating exceptions.

## Workspace changes

- Prefer linear Git history; avoid merge commits unless necessary.
- Assess tracked, untracked, and expected change size before starting or expanding work.
- Divide scope into independently deliverable goals.
- Keep each workspace's changes reviewable.
- Split early if current or expected changes hinder review.
  - Give each goal a separate chat and worktree or working directory.
- For independent split goals, weigh tools, resources, and coordination costs.
- Run them in parallel when feasible and beneficial. Otherwise, run them sequentially.
- Preserve existing changes and the full task scope when splitting work.
- Chats sharing one working tree still share its diff.
- Before parallel work, assign shared-file write ownership and set the integration order.

## Verification and handoff

- Track material discrepancies, failures, deviations, and verification limits.
- Before reporting completion, account for each material finding:
  - Resolved: give the outcome and verification.
  - Remaining: give the impact and next action.
- Match claims to evidence. Distinguish facts, inferences, and unverified assumptions.
- Report implementation completion, checks, and outcome verification separately.
- Claim resolution only with evidence for the original outcome.
- Identify pending activation, validation, cleanup, or user action.
- Explain consequential departures from referenced procedures before acting.
- Use short Markdown list items for the final handoff.
  - Cover one subject and its result, limit, or next action per item.
  - Keep evidence and caveats beside the claim.
  - Include material unresolved findings, even if reported earlier.
  - Scale detail to the task. Omit inapplicable items.
  - Use status labels when useful.

## Writing and communication

- For documents and responses, apply ISO 24495-1 principles:
  - Make text relevant, findable, understandable, and usable.
- Adapt ASD-STE100 practices to the language and content.
  - Use short sentences, clear actions, and consistent technical terms.
- Keep progress updates concise: meaningful progress, findings, blockers, or next steps.
- Deliver all responses in the user's language unless requested otherwise.
