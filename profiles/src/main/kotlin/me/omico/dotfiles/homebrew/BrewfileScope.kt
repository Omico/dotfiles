package me.omico.dotfiles.homebrew

interface BrewfileScope {
    fun combineWith(other: Brewfile): BrewfileScope

    fun tap(name: String): BrewfileScope

    fun brew(id: String): BrewfileScope

    fun cask(id: String): BrewfileScope

    fun mas(
        name: String,
        id: Long,
    ): BrewfileScope
}
