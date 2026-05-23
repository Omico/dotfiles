#!/usr/bin/env bash

markdownlint() {
    local script_dir repo_root
    script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || return 1
    repo_root=$(cd -- "$script_dir/.." && pwd -P) || return 1

    local extra_args=()
    local arg

    if ! command -v npx >/dev/null 2>&1; then
        printf "npx is required.\n" >&2
        return 1
    fi

    for arg in "$@"; do
        case "$arg" in
            -h|--help)
                printf "Usage: %s [--fix] [markdownlint-cli2 args...]\n" "$0"
                return 0
                ;;
            --fix)
                extra_args+=(--fix)
                ;;
            *)
                extra_args+=("$arg")
                ;;
        esac
    done

    pushd "$repo_root" >/dev/null || return 1

    shopt -s extglob
    local markdown_files=()
    local file

    while IFS= read -r file; do
        markdown_files+=("$file")
    done < <(
        {
            find . -maxdepth 1 -type f -name "*.md" -print
            if [[ -d .agents ]]; then
                find .agents -type f -name "*.md" -print
            fi
            if [[ -d docs/src ]]; then
                find docs/src -type f -name "*.md" -print
            fi
        } | sed "s#^\./##" | sort
    )

    local markdownlint_output lint_status
    markdownlint_output=$(npx --yes markdownlint-cli2 "${markdown_files[@]}" --config .markdownlint-cli2.yaml "${extra_args[@]}" 2>&1)
    lint_status=$?

    if (( lint_status != 0 )); then
        printf "%s\n" "$markdownlint_output" >&2
    fi

    __markdownlint_check_hard_wraps "${markdown_files[@]}"
    local hard_wrap_status=$?

    popd >/dev/null || return 1

    if (( lint_status != 0 || hard_wrap_status != 0 )); then
        printf "markdownlint: failed\n" >&2
        return 1
    fi

    printf "markdownlint: ok\n"
    return 0
}

__markdownlint_trim() {
    local value=$1
    value=${value##+([[:space:]])}
    value=${value%%+([[:space:]])}
    printf "%s" "$value"
}

__markdownlint_check_hard_wraps() {
    local failed=0
    local fence_re='^[[:space:]]{0,3}(```|~~~)'
    local skipped_line_re='^[[:space:]]{4,}[^[:space:]]|^[[:space:]]{0,3}(\| |[|:]?-{3,}|:{3,}|<!--|</?[A-Za-z]|\[[^]]+\]:)'
    local block_start_re='^[[:space:]]{0,3}(#{1,6}[[:space:]]|>|([-+*]|[0-9]+[.)])[[:space:]]+|([-*_][[:space:]]*){3,}$)'
    local list_item_re='^[[:space:]]{0,3}([-+*]|[0-9]+[.)])[[:space:]]+'

    for file in "$@"; do
        [[ -f "$file" ]] || continue

        local in_fence=false
        local in_frontmatter=false
        local line_number=0
        local previous_line=0
        local line trimmed starts_block

        while IFS= read -r line || [[ -n "$line" ]]; do
            ((line_number += 1))
            trimmed=$(__markdownlint_trim "$line")

            if (( line_number == 1 )) && [[ "$trimmed" == "---" ]]; then
                in_frontmatter=true
                previous_line=0
                continue
            fi

            if [[ "$in_frontmatter" == true ]]; then
                if (( line_number > 1 )) && [[ "$trimmed" == "---" ]]; then
                    in_frontmatter=false
                fi

                previous_line=0
                continue
            fi

            if [[ "$line" =~ $fence_re ]]; then
                if [[ "$in_fence" == true ]]; then
                    in_fence=false
                else
                    in_fence=true
                fi

                previous_line=0
                continue
            fi

            if [[ "$in_fence" == true ]]; then
                previous_line=0
                continue
            fi

            if [[ -z "$trimmed" || "$line" =~ $skipped_line_re ]]; then
                previous_line=0
                continue
            fi

            starts_block=false
            if [[ "$line" =~ $block_start_re ]]; then
                starts_block=true
            fi

            if (( previous_line > 0 )) && [[ "$starts_block" == false ]]; then
                printf "%s:%d: hard-wrap\n" "$file" "$previous_line" >&2
                failed=1
            fi

            if [[ "$starts_block" == true ]] && [[ ! "$line" =~ $list_item_re ]]; then
                previous_line=0
            elif [[ "$line" == *\\ || "$line" == *"  " ]]; then
                previous_line=0
            else
                previous_line=$line_number
            fi
        done <"$file"
    done

    if (( failed != 0 )); then
        printf "hard-wrap: keep each paragraph or list item on one physical line.\n" >&2
    fi

    return "$failed"
}

markdownlint "$@"
