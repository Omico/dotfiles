#!/usr/bin/env fish

function gradle-or-gradlew
    # find project root
    set dir (pwd)
    set project_root $dir

    while test "$dir" != /
        if test -x "$dir/gradlew"
            set project_root $dir
            break
        end
        set dir (dirname "$dir")
    end

    # if gradlew found, run it instead of gradle
    if test -f "$project_root/gradlew"
        echo "Executing gradlew instead of gradle..."
        "$project_root/gradlew" $argv
    else
        command gradle $argv
    end
end
