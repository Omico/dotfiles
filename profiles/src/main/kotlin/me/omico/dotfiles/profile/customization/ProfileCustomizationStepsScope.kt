package me.omico.dotfiles.profile.customization

import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.homebrew.BrewfileScope
import me.omico.dotfiles.homebrew.buildBrewfile

interface ProfileCustomizationStepsScope {
    fun executeShell(
        name: String? = null,
        shell: String,
    )

    fun restoreBrewfile(
        name: String? = null,
        brewfile: Brewfile,
    )

    fun restoreBrewfile(
        name: String? = null,
        builder: BrewfileScope.() -> Unit,
    ): Unit =
        restoreBrewfile(
            name = name,
            brewfile = buildBrewfile(builder = builder),
        )
}
