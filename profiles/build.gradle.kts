plugins {
    `kotlin-dsl`
    embeddedKotlin("plugin.serialization")
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
}

dependencies {
    testImplementation(kotlin("test"))
}
