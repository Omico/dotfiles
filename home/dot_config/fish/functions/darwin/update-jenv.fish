#!/usr/bin/env fish

function update-jenv --description "Detect JDKs and add to jenv"
  if test -d "$HOME/.jenv"
    set -l found 0
    for jdk in /Library/Java/JavaVirtualMachines/*.jdk
      if test -d "$jdk/Contents/Home"
        echo "➕ Adding: $jdk"
        jenv add "$jdk/Contents/Home" >/dev/null 2>&1
        set found 1
      end
    end
    if test $found -eq 0
      echo "⚠️  No JDKs found in /Library/Java/JavaVirtualMachines."
    else
      jenv rehash >/dev/null 2>&1
      echo "✅ Update complete. 🔄 Environment refreshed!"
    end
  else
    echo "❌ jEnv not installed."
  end
end
