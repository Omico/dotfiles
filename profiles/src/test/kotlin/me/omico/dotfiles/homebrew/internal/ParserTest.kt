package me.omico.dotfiles.homebrew.internal

import me.omico.dotfiles.internal.prettyJson
import me.omico.dotfiles.profile.NyrixaBrewfile
import kotlin.io.path.Path
import kotlin.io.path.readText
import kotlin.io.path.writeText
import kotlin.test.Test
import kotlin.test.assertEquals

class ParserTest {
    @Test
    fun test() {
        val text = Path(System.getProperty("user.home")).resolve(".local/share/chezmoi/Brewfile").readText()
        val brewfile = parseBrewfile(text)
        Path("Brewfile.json").writeText(prettyJson.encodeToString(brewfile))
        val generatedBrewfilePath = Path("Brewfile.Generated")
        val personalBrewfilePath = Path("Brewfile.Personal")
        brewfile.dumpTo(generatedBrewfilePath)
        NyrixaBrewfile.dumpTo(personalBrewfilePath)
        assertEquals(
            expected = generatedBrewfilePath.readText(),
            actual = personalBrewfilePath.readText(),
            message = "Generated Brewfile does not match the Personal Brewfile.",
        )
    }
}
