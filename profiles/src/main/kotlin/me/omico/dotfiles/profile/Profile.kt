package me.omico.dotfiles.profile

import kotlinx.serialization.Serializable
import me.omico.dotfiles.internal.generateRandomUuidString
import me.omico.dotfiles.profile.customization.ProfileCustomizationStep
import me.omico.dotfiles.profile.customization.ProfileCustomizationStepsScope
import me.omico.dotfiles.profile.customization.buildProfileCustomizationSteps

@Serializable
data class Profile(
    val id: String = generateRandomUuidString(),
    val name: String = "",
    val customizationSteps: List<ProfileCustomizationStep> = emptyList(),
)

fun buildProfile(
    name: String = "",
    customizationSteps: ProfileCustomizationStepsScope.() -> Unit,
): Profile =
    Profile(
        name = name,
        customizationSteps = buildProfileCustomizationSteps(customizationSteps),
    )
