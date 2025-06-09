package me.omico.dotfiles.profile.customization

import kotlinx.serialization.Serializable

@Serializable
data class ShellExecutionStep(
    override val name: String? = null,
    val shell: String,
) : ProfileCustomizationStep
