plugins {
    `kotlin-dsl`
    @Suppress("UnstableApiUsage")
    embeddedKotlin("plugin.serialization")
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
}

dependencies {
    testImplementation(kotlin("test"))
}
