package me.omico.dotfiles.homebrew

interface BrewfileScope {
    fun combineWith(other: Brewfile)
    fun tap(name: String)
    fun brew(id: String)
    fun cask(id: String)
    fun mas(name: String, id: Long)
}
