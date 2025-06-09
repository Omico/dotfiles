package me.omico.dotfiles.homebrew.internal

import me.omico.dotfiles.homebrew.Brewfile
import java.nio.file.Path
import kotlin.io.path.writeText

internal fun Brewfile.dumpTo(file: Path): Unit =
    toSortedSet(BrewEntryComparator)
        .joinToString("\n")
        .let(file::writeText)
