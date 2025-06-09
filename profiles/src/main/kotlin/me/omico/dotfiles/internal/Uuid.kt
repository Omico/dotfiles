package me.omico.dotfiles.internal

import java.util.UUID

internal fun generateRandomUuidString(): String = UUID.randomUUID().toString()
