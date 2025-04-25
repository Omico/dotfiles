function update-jenv() {
  if [ -d "$HOME/.jenv" ]; then
    found=0
    for jdk in /Library/Java/JavaVirtualMachines/temurin-*.jdk; do
      if [ -d "$jdk/Contents/Home" ]; then
        echo "➕ Adding: $jdk"
        jenv add "$jdk/Contents/Home" >/dev/null 2>&1
        found=1
      fi
    done
    if [ "$found" -eq 0 ]; then
      echo "⚠️  No Temurin JDKs found in /Library/Java/JavaVirtualMachines."
    else
      jenv rehash >/dev/null 2>&1
      echo "✅ Update complete. 🔄 Environment refreshed!"
    fi
  else
    echo "❌ jEnv not installed."
  fi
}
