package me.omico.dotfiles.internal

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
internal fun generateRandomUuidString(): String = Uuid.random().toString()
