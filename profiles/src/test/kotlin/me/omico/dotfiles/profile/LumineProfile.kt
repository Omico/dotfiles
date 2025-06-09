package me.omico.dotfiles.profile

import me.omico.dotfiles.profile.customization.ProfileCustomizationStepsScope

internal val LumineProfile: Profile =
    buildProfile(
        name = "Lumine",
        customizationSteps = {
            restorePersonalBrewfile()
            restoreLumineBrewfile()
        },
    )

private fun ProfileCustomizationStepsScope.restoreLumineBrewfile(): Unit =
    restoreBrewfile(name = "Restore Lumine Homebrew dependencies") {
        cask("bartender")
    }
