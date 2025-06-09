package me.omico.dotfiles.profile

import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.homebrew.BrewfileScope
import me.omico.dotfiles.homebrew.buildBrewfile
import me.omico.dotfiles.profile.customization.ProfileCustomizationStepsScope

internal fun ProfileCustomizationStepsScope.restorePersonalBrewfile(): Unit =
    restoreBrewfile(
        name = "Restore personal Homebrew dependencies",
        brewfile = PersonalBrewfile,
    )

internal val PersonalBrewfile: Brewfile =
    buildBrewfile {
        commonHomebrewDependencies()
        commonDeveloperHomebrewDependencies()
        personalHomebrewDependencies()
        personalDeveloperHomebrewDependencies()
    }

private fun BrewfileScope.personalHomebrewDependencies() {
    brew("mas")
    brew("wgcf")
    cask("anydesk")
    cask("anythingllm")
    cask("clash-verge-rev")
    cask("cloudflare-warp")
    cask("discord")
    cask("google-drive")
    cask("microsoft-auto-update")
    cask("microsoft-office")
    cask("nomachine")
    cask("obs")
    cask("parallels")
    cask("qbittorrent")
    cask("slack")
    cask("steam")
    cask("tailscale-app")
    cask("telegram-desktop")
    cask("tencent-meeting")
    cask("windows-app")
    mas("Bitwarden", id = 1352778147)
    mas("Keynote", id = 409183694)
    mas("Numbers", id = 409203825)
    mas("Pages", id = 409201541)
    mas("iMovie", id = 408981434)
}

private fun BrewfileScope.personalDeveloperHomebrewDependencies() {
    brew("gh")
    brew("ykman")
    brew("ykpers")
    mas("Developer", id = 640199958)
    mas("Xcode", id = 497799835)
}
