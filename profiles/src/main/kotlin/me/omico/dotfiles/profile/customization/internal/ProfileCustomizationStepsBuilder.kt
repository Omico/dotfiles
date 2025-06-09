package me.omico.dotfiles.profile.customization.internal

import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.profile.customization.BrewfileRestoreStep
import me.omico.dotfiles.profile.customization.ProfileCustomizationStep
import me.omico.dotfiles.profile.customization.ProfileCustomizationSteps
import me.omico.dotfiles.profile.customization.ProfileCustomizationStepsScope
import me.omico.dotfiles.profile.customization.ShellExecutionStep

internal class ProfileCustomizationStepsBuilder : ProfileCustomizationStepsScope {
    private val steps: MutableList<ProfileCustomizationStep> = mutableListOf()

    override fun executeShell(
        name: String?,
        shell: String,
    ) {
        ShellExecutionStep(
            name = name,
            shell = shell,
        ).let(steps::add)
    }

    override fun restoreBrewfile(
        name: String?,
        brewfile: Brewfile,
    ) {
        BrewfileRestoreStep(
            name = name,
            brewfile = brewfile,
        ).let(steps::add)
    }

    fun build(): ProfileCustomizationSteps = steps
}
