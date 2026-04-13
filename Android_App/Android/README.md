# Android Client (Gradle Project)

Android project name: `Snipping`
Package: `com.example.snipping`

## Requirements

- Android Studio (latest stable)
- JDK 11
- Android SDK matching:
  - `compileSdk 36`
  - `targetSdk 36`
  - `minSdk 24`

## Open and Run

1. Open this folder (`Android_App/Android`) in Android Studio.
2. Allow Gradle sync.
3. Select a device/emulator.
4. Run the `app` configuration.

## Command Line Build

From `Android_App/Android`:

```bash
gradlew.bat assembleDebug
```

Output APK is generated under `app/build/outputs/apk/debug/`.
