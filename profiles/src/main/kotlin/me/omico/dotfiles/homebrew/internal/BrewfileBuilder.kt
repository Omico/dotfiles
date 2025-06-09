package me.omico.dotfiles.homebrew.internal

import me.omico.dotfiles.homebrew.Brew
import me.omico.dotfiles.homebrew.BrewEntry
import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.homebrew.BrewfileScope
import me.omico.dotfiles.homebrew.Cask
import me.omico.dotfiles.homebrew.Mas
import me.omico.dotfiles.homebrew.Tap

internal class BrewfileBuilder : BrewfileScope {
    private val entries: MutableSet<BrewEntry> = mutableSetOf()

    override fun combineWith(other: Brewfile): BrewfileScope = apply { entries.addAll(other) }

    override fun tap(name: String): BrewfileScope = apply { Tap(name = name).let(entries::add) }

    override fun brew(id: String): BrewfileScope = apply { Brew(id = id).let(entries::add) }

    override fun cask(id: String): BrewfileScope = apply { Cask(id = id).let(entries::add) }

    override fun mas(
        name: String,
        id: Long,
    ): BrewfileScope = apply { Mas(name = name, id = id).let(entries::add) }

    fun build(): Brewfile = entries
}
