package me.omico.dotfiles.homebrew

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@SerialName("brew")
@Serializable
data class Brew(
    val id: String,
) : BrewEntry {
    override fun toString(): String = "brew \"$id\""
}
