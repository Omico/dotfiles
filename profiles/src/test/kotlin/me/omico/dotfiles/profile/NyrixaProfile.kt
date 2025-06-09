package me.omico.dotfiles.profile

import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.homebrew.buildBrewfile
import me.omico.dotfiles.profile.customization.ProfileCustomizationStepsScope

internal val NyrixaProfile: Profile by lazy {
    buildProfile(
        name = "Nyrixa",
        customizationSteps = {
            restoreNyrixaBrewfile()
        },
    )
}

internal val NyrixaBrewfile: Brewfile by lazy {
    buildBrewfile {
        combineWith(PersonalBrewfile)
        cask("autodesk-fusion")
        cask("bricklink-studio")
        mas("Compressor", id = 424390742)
        mas("Final Cut Pro", id = 424389933)
        mas("Logic Pro", id = 634148309)
        mas("MainStage", id = 634159523)
        mas("Motion", id = 434290957)
    }
}

private fun ProfileCustomizationStepsScope.restoreNyrixaBrewfile(): Unit =
    restoreBrewfile(name = "Restore Nyrixa Homebrew dependencies", NyrixaBrewfile)
