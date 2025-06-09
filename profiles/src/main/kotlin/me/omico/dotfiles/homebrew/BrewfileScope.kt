package me.omico.dotfiles.homebrew

interface BrewfileScope {
    fun tap(name: String)
    fun brew(id: String)
    fun cask(id: String)
    fun mas(name: String, id: Long)
}
