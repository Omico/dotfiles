package me.omico.dotfiles.profile.customization

import kotlinx.serialization.Serializable
import me.omico.dotfiles.homebrew.Brewfile

@Serializable
data class BrewfileRestoreStep(
    override val name: String? = null,
    val brewfile: Brewfile,
) : ProfileCustomizationStep
