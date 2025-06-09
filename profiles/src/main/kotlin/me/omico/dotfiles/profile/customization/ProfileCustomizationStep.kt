package me.omico.dotfiles.profile.customization

import kotlinx.serialization.Serializable
import me.omico.dotfiles.internal.generateRandomUuidString
import me.omico.dotfiles.profile.customization.internal.ProfileCustomizationStepsBuilder

@Serializable
sealed interface ProfileCustomizationStep {
    val id: String get() = generateRandomUuidString()
    val name: String?
}

fun buildProfileCustomizationSteps(builder: ProfileCustomizationStepsScope.() -> Unit): ProfileCustomizationSteps =
    ProfileCustomizationStepsBuilder().apply(builder).build()
