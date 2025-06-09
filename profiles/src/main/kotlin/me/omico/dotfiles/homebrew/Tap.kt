package me.omico.dotfiles.homebrew

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@SerialName("tap")
@Serializable
data class Tap(
    val name: String,
) : BrewEntry {
    override fun toString(): String = "tap \"$name\""
}
