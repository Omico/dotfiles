package me.omico.dotfiles.homebrew

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@SerialName("cask")
@Serializable
data class Cask(
    val id: String,
) : BrewEntry {
    override fun toString(): String = "cask \"$id\""
}
