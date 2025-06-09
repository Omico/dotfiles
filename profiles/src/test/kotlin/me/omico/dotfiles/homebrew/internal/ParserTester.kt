package me.omico.dotfiles.homebrew.internal

import kotlinx.serialization.encodeToString
import me.omico.dotfiles.internal.prettyJson
import me.omico.dotfiles.profile.PersonalBrewfile
import kotlin.io.path.Path
import kotlin.io.path.readText
import kotlin.io.path.writeText

fun main() {
    val text = Path(System.getProperty("user.home")).resolve(".local/share/chezmoi/Brewfile").readText()
    println(text)
    val brewfile = parseBrewfile(text)
    println(brewfile)
    Path("Brewfile.json").writeText(prettyJson.encodeToString(brewfile))
    val generatedBrewfilePath = Path("Brewfile.Generated")
    val personalBrewfilePath = Path("Brewfile.Personal")
    brewfile.dumpTo(generatedBrewfilePath)
    PersonalBrewfile.dumpTo(personalBrewfilePath)
    assert(generatedBrewfilePath.readText() == personalBrewfilePath.readText()) {
        "Generated Brewfile does not match the Personal Brewfile."
    }
}
