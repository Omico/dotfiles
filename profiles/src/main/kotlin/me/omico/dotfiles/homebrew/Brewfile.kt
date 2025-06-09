package me.omico.dotfiles.homebrew

import me.omico.dotfiles.homebrew.internal.BrewfileBuilder

typealias Brewfile = Set<BrewEntry>

fun buildBrewfile(builder: BrewfileScope.() -> Unit): Brewfile = BrewfileBuilder().apply(builder).build()
