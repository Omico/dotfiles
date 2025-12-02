#!/usr/bin/env fish

function gradle-or-gradlew
    set dir (pwd)
    set project_root $dir

    while test "$dir" != /
        if test -x "$dir/gradlew"
            set project_root $dir
            break
        end
        if test -d "$dir/.git"
            break
        end
        set dir (dirname "$dir")
    end

    if test -f "$project_root/gradlew"
        echo "Executing gradlew instead of gradle..."
        "$project_root/gradlew" $argv
        return $status
    end

    if type -q gradle
        command gradle $argv
    else
        echo "Error: 'gradle' command not found, and no 'gradlew' script was detected in the project." >&2
        echo "Please install Gradle or add a 'gradlew' wrapper script in the project root." >&2
        return 127
    end
end
