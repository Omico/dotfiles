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

    override fun tap(name: String) {
        Tap(name = name).let(entries::add)
    }

    override fun brew(id: String) {
        Brew(id = id).let(entries::add)
    }

    override fun cask(id: String) {
        Cask(id = id).let(entries::add)
    }

    override fun mas(name: String, id: Long) {
        Mas(name = name, id = id).let(entries::add)
    }

    fun build(): Brewfile = entries
}
