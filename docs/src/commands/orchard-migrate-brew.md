# Orchard: migrate from Homebrew


> Auto-generated from [`.cursor/commands/orchard-migrate-brew.md`](https://github.com/Omico/dotfiles/blob/HEAD/.cursor/commands/orchard-migrate-brew.md).

## Purpose

Use this command when you want to migrate macOS GUI apps that are currently installed via Homebrew casks into Orchard app packages managed by `orchard`.

## Behavior

When this command is invoked, the agent should:

1. **Check user input**
   - If the user provided **no additional instructions** beyond running this command (empty or very short generic input), treat this as a request to review all outdated Homebrew casks that could be migrated.
   - If the user **names one or more specific Homebrew casks** (e.g. `jetbrains-toolbox`, `firefox`), or explicitly says they want to **write Orchard packages**, treat this as a request to help author or update Orchard app packages for those casks.

2. **Global migration flow (no extra input)**
   1. Run a dry-run migration plan by executing:
      - `orchard migrate brew --plan`
   2. Show the user a clear summary:
      - Which outdated Homebrew casks can be migrated (i.e. have Orchard packages).
      - Which outdated Homebrew casks do **not** yet have Orchard packages.
      - If **no** outdated casks can be migrated, explain that there is nothing to do and stop without asking for confirmation.
   3. If there are any casks that can be migrated, ask the user for confirmation before making any changes:
      - Example question (yes/no):
        “Do you want me to run `orchard migrate brew` now to uninstall those Homebrew casks and reinstall them via Orchard?”
   4. If the user **confirms**:
      - Execute `orchard migrate brew`.
      - Show a short summary of what was migrated and any failures.
   5. If the user **declines**:
      - Do not run the real migration.
      - Optionally offer to help author Orchard packages for specific casks that are missing packages.

3. **Targeted cask / package-authoring flow (extra input)**
   1. Parse the user’s input to extract any mentioned Homebrew cask names.
   2. For each cask:
      - Check whether an Orchard app package already exists at `home/dot_config/orchard/apps/<cask>.fish`.
   3. If a package already exists:
      - Offer to run `orchard migrate brew --plan` scoped to that cask (by explaining what would happen) or suggest using `orchard install <app_id>` directly if migration is not needed.
   4. If a package does **not** exist:
      - Switch into Orchard package authoring mode:
        - Ask the user for missing details if needed (e.g. homepage, download URL, special install behavior).
        - Use the GitHub API to fetch the Homebrew cask definition from the `Homebrew/homebrew-cask` repository (instead of calling `brew info --cask` locally), and extract homepage, download URL, and install details from that cask file. This describes the agent’s behavior in a sandbox or remote environment, so it uses the GitHub API rather than local `brew` commands.
        - Follow the Orchard skill’s guidelines and `app-package-format.md` to draft a new `apps/<cask>.fish` file.
      - Write the Orchard app package directly to `home/dot_config/orchard/apps/<cask>.fish` without asking for additional confirmation.
   5. After authoring or modifying any Orchard packages:
      - Remind the user to run `chezmoi apply` and then `orchard list` / `orchard install <app_id>` as appropriate.

4. **Safety and conventions**
   - Never run `brew` commands that remove or modify casks **without explicit user confirmation**.
   - Keep all comments and user-visible strings in Orchard-related scripts in English (follow the workspace rules).
   - For `orchard migrate brew --plan` and `orchard migrate brew`, run them in the user’s real environment (not in an isolated or simulated sandbox), so that Homebrew state reflects the actual system.
   - Prefer concise summaries and avoid dumping large command outputs unless the user asks for details.
