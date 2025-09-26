# React Native Expo Template

A minimal, production-ready template for React Native apps using Expo SDK 53.

## Quick Start

1) Click "Use this template" on GitHub
2) Clone your new repository
3) Install dependencies

```
npm install
```

4) Start development

```
npm start
```

- ✨ Clean Material Design interface with gradient background
- 🔐 Password generation with customizable length (8-50 characters)
- ⚙️ Toggle options for uppercase, lowercase, numbers, special characters
- 💪 Real-time password strength meter with color coding
- 📋 One-tap copy to clipboard with success animation
- 📜 Password history (last 10 generated passwords) with timestamps
- 🌓 Dark mode toggle with system preference detection
- 📳 Haptic feedback for interactions

### Premium Features ($2.99 one-time purchase)

- 📜 Unlimited password history
- ☁️ Cloud sync across devices
- 🎯 Custom character sets and exclusion rules
- 📦 Bulk password generation (up to 100 at once)
- 📊 Export passwords to CSV
- 🔒 Advanced security settings
- 🚫 No advertisements

## Tech Stack

- React Native with Expo
- TypeScript
- React Navigation
- React Native Paper (Material Design)
- AsyncStorage for local data
- Firebase (ready for integration)
- Google AdMob (ready for integration)

## What's Included
- Expo SDK 53 with React 19 and React Native 0.79.5
- TypeScript configuration
- ESLint + Prettier with Husky pre-commit hooks
- GitHub Actions CI pipeline
- Node 20 configuration

## Scripts
- npm start — Start Expo development server
- npm run ios — Run on iOS simulator
- npm run android — Run on Android emulator
- npm run web — Run in web browser
- npm run lint — Run ESLint
- npm run fmt — Check Prettier formatting
- npm run type-check — Run TypeScript compiler checks

## Cursor IDE
See docs/Cursor.md for AI-assisted development guidance.

### Prerequisites

- Node.js 16+ and npm/yarn
- Expo CLI
- iOS Simulator (Mac only) or Android Emulator

### Installation

1. Copy env and install dependencies:

```bash
cp .env.example .env
npm install
```

2. Start the development server:

```bash
npx expo start
```

3. Run on iOS Simulator:

```bash
npx expo run:ios
```

4. Run on Android Emulator:

```bash
npx expo run:android
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── screens/        # App screens
├── navigation/     # Navigation setup
├── services/       # Services (storage, Firebase, etc.)
├── utils/          # Utility functions
├── hooks/          # Custom React hooks
├── types/          # TypeScript type definitions
├── constants/      # App constants and theme
└── store/          # State management
```

## Building for Production

### Using EAS Build

#### Manual Builds

1. Install EAS CLI:

```bash
npm install -g eas-cli
```

2. Configure EAS:

```bash
eas build:configure
```

3. Build for iOS:

```bash
eas build --platform ios
```

4. Build for Android:

```bash
eas build --platform android
```

#### Automated CI/CD Builds

This project supports automated builds via GitHub Actions in three ways:

1. **Pull Request Labels**: Add one of these labels to your PR to trigger a build:
   - `eas-build-ios:development` - iOS development build
   - `eas-build-ios:preview` - iOS preview build
   - `eas-build-ios:production` - iOS production build
   - `eas-build-android:development` - Android development build
   - `eas-build-android:preview` - Android preview build
   - `eas-build-android:production` - Android production build

2. **Manual Trigger**: Use GitHub Actions UI to trigger builds with custom parameters

3. **Release Tags**: Pushing a tag starting with 'v' (e.g., v1.0.0) automatically triggers production builds

##### Required Secrets

Set these secrets in your GitHub repository settings:

- `EXPO_TOKEN` - Your Expo access token (required)
- `APPLE_TEAM_ID` - Your Apple Developer Team ID (required for iOS builds)
- `EXPO_APPLE_APP_SPECIFIC_PASSWORD` - App-specific password for your Apple ID (required for iOS builds)

##### Build Profiles

- **development**: Debug builds with development client
- **preview**: Internal testing builds with development features
- **production**: Release builds for app store submission

## App Store Configuration

### Google Play Store

- Package name: `com.securepass.generator`
- Target SDK: 34
- Min SDK: 24 (Android 7.0+)

### Apple App Store

- Bundle ID: `com.securepass.generator`
- Deployment target: iOS 13.0+

## Firebase Setup (Required for production)

1. Create a Firebase project at https://console.firebase.google.com
2. Add iOS and Android apps with the package/bundle IDs
3. Download `google-services.json` (Android) and `GoogleService-Info.plist` (iOS)
4. Place configuration files in the project root
5. Configure Firebase services:
   - Authentication
   - Firestore
   - Remote Config
   - Analytics
   - Crashlytics

## AdMob Setup (Required for monetization)

1. Create AdMob account at https://admob.google.com
2. Create ad units:
   - Banner ad for main screen
   - Interstitial ad for password generations
   - Rewarded video for premium trial
3. Add AdMob App IDs to app configuration
4. Test with test ad unit IDs during development

## Environment Variables

Copy `.env.example` to `.env` and set values. Key settings:

- APP_NAME, APP_SLUG, APP_SCHEME, EXPO_OWNER
- IOS_BUNDLE_ID, ANDROID_PACKAGE
- EAS_PROJECT_ID
- ADMOB_APP_ID_IOS, ADMOB_APP_ID_ANDROID
- SENTRY_DSN

## Testing

Run tests:

```bash
npm test
```

Run TypeScript type checking:

```bash
npx tsc --noEmit
```

## License

MIT

## Support

For support, email support@securepass.app
