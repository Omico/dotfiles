package me.omico.dotfiles.homebrew.internal

import me.omico.dotfiles.homebrew.Brew
import me.omico.dotfiles.homebrew.BrewEntry
import me.omico.dotfiles.homebrew.Brewfile
import me.omico.dotfiles.homebrew.Cask
import me.omico.dotfiles.homebrew.Mas
import me.omico.dotfiles.homebrew.Tap
import kotlin.reflect.KClass

internal fun parseBrewfile(text: String): Brewfile =
    text
        .lines()
        .mapNotNull { line -> line.trim().takeIf { it.isNotBlank() && !it.startsWith("#") } }
        .map { line ->
            when {
                line.startsWith("tap ") -> {
                    Tap(name = line.extractQuoted())
                }

                line.startsWith("brew ") -> {
                    Brew(id = line.extractQuoted())
                }

                line.startsWith("cask ") -> {
                    Cask(id = line.extractQuoted())
                }

                line.startsWith("mas ") -> {
                    val parts = line.split(",").map { it.trim() }
                    val name = parts[0].extractQuoted()
                    val id =
                        parts
                            .getOrNull(1)
                            ?.substringAfter("id:")
                            ?.trim()
                            ?.toLong() ?: 0
                    Mas(name = name, id = id)
                }

                else -> {
                    error("Unable to parse line: $line, expected format is 'tap', 'brew', 'cask', or 'mas'.")
                }
            }
        }.toSortedSet(BrewEntryComparator)

internal object BrewEntryComparator : Comparator<BrewEntry> {
    override fun compare(
        o1: BrewEntry,
        o2: BrewEntry,
    ): Int =
        compareValuesBy(
            a = o1,
            b = o2,
            { brewEntryKindOrder[it::class] ?: Int.MAX_VALUE },
            BrewEntry::toString,
        )
}

private fun String.extractQuoted(): String = substringAfter("\"").substringBeforeLast("\"")

private val brewEntryKindOrder: Map<KClass<out BrewEntry>, Int> =
    mapOf(
        Tap::class to 0,
        Brew::class to 1,
        Cask::class to 2,
        Mas::class to 3,
    )
