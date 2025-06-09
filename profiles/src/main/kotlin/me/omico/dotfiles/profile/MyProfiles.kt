package me.omico.dotfiles.profile

import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.homebrew.BrewfileScope
import me.omico.dotfiles.homebrew.buildBrewfile
import me.omico.dotfiles.profile.customization.ProfileCustomizationStepsScope

val PersonalBrewfile: Brewfile =
    buildBrewfile {
        commonHomebrewDependencies()
        personalHomebrewDependencies()
    }

val LumineProfile: Profile = buildProfile(
    name = "Lumine",
    customizationSteps = {
        commonPersonalCustomizationSteps()
    },
)

val NyrixaProfile: Profile = buildProfile(
    name = "Nyrixa",
    customizationSteps = {
        commonPersonalCustomizationSteps()
    },
)

fun ProfileCustomizationStepsScope.commonPersonalCustomizationSteps(): Unit =
    restoreBrewfile(
        name = "Restore Homebrew dependencies",
        brewfile = PersonalBrewfile,
    )

fun ProfileCustomizationStepsScope.restoreCommonHomebrewDependencies(): Unit =
    restoreBrewfile(
        name = "Restore common Homebrew dependencies",
        builder = BrewfileScope::commonHomebrewDependencies,
    )

fun ProfileCustomizationStepsScope.restorePersonalHomebrewDependencies(): Unit =
    restoreBrewfile(
        name = "Restore personal Homebrew dependencies",
        builder = BrewfileScope::personalHomebrewDependencies,
    )

fun BrewfileScope.commonHomebrewDependencies() {
    tap("homebrew/autoupdate")
    tap("homebrew/cask")
    brew("actionlint")
    brew("chezmoi")
    brew("cloc")
    brew("cmake")
    brew("coreutils")
    brew("fastfetch")
    brew("git")
    brew("gradle")
    brew("helm")
    brew("icu4c@77")
    brew("jadx")
    brew("jenv")
    brew("kdoctor")
    brew("kotlin")
    brew("llvm")
    brew("lsusb")
    brew("nvm")
    brew("openjdk")
    brew("opentofu")
    brew("p7zip")
    brew("pinentry-mac")
    brew("python@3.13")
    brew("rbenv")
    brew("repo")
    brew("ruby")
    brew("shellcheck")
    brew("shfmt")
    brew("telnet")
    brew("thefuck")
    brew("tlrc")
    brew("wget")
    brew("yq")
    cask("android-commandlinetools")
    cask("beyond-compare")
    cask("cursor")
    cask("docker-desktop")
    cask("dotnet-sdk")
    cask("easydict")
    cask("firefox")
    cask("font-fira-mono-nerd-font")
    cask("google-chrome")
    cask("gpg-suite")
    cask("iina")
    cask("jetbrains-toolbox")
    cask("ollama-app")
    cask("powershell")
    cask("snipaste")
    cask("squirrel-app")
    cask("visual-studio-code")
}

fun BrewfileScope.personalHomebrewDependencies() {
    brew("gh")
    brew("mas")
    brew("wgcf")
    brew("ykman")
    brew("ykpers")
    cask("anydesk")
    cask("anythingllm")
    cask("autodesk-fusion")
    cask("bartender")
    cask("bricklink-studio")
    cask("clash-verge-rev")
    cask("cloudflare-warp")
    cask("discord")
    cask("git-credential-manager")
    cask("github")
    cask("gitkraken")
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
    cask("temurin@11")
    cask("temurin@17")
    cask("temurin@21")
    cask("temurin@8")
    cask("tencent-meeting")
    cask("windows-app")
    mas("Bitwarden", id = 1352778147)
    mas("Compressor", id = 424390742)
    mas("Developer", id = 640199958)
    mas("Final Cut Pro", id = 424389933)
    mas("Keynote", id = 409183694)
    mas("Logic Pro", id = 634148309)
    mas("MainStage", id = 634159523)
    mas("Motion", id = 434290957)
    mas("Numbers", id = 409203825)
    mas("Pages", id = 409201541)
    mas("Xcode", id = 497799835)
    mas("iMovie", id = 408981434)
}
