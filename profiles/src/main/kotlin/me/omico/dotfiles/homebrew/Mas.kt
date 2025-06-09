package me.omico.dotfiles.homebrew

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@SerialName("mas")
@Serializable
data class Mas(
    val name: String,
    val id: Long,
) : BrewEntry {
    override fun toString(): String = "mas \"$name\", id: $id"
}
