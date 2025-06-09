package me.omico.dotfiles.internal

import kotlinx.serialization.json.Json

internal val prettyJson: Json =
    Json {
        prettyPrint = true
    }
