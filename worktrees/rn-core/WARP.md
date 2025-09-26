# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a React Native password generator app with a pure React Native CLI setup (no Expo dependencies). The app focuses on security and uses native modules for biometrics and keychain integration.

## Architecture

- React Native (0.72.7) with TypeScript
- React Native Paper for Material Design components
- Native modules:
  - react-native-biometrics for biometric authentication
  - react-native-keychain for secure storage
- Jest for testing
- ESLint + Prettier for code quality

## Development Commands

### Environment Setup
```bash
yarn install
```

### Running the App
- iOS: `yarn ios`
- Android: `yarn android`
- Metro bundler: `yarn start`

### Testing
- Run all tests: `yarn test`
- Run tests with coverage: `yarn test:coverage`
- Type checking: `yarn check-types`
- Full validation: `yarn validate` (runs lint, tests, and type checks)

### Code Quality
- Lint: `yarn lint`
- Format code: `yarn format`

### Common Development Patterns

1. All secure storage operations should use react-native-keychain
2. Biometric authentication should be implemented via react-native-biometrics
3. UI components should use react-native-paper for consistency

## Project Structure

```
src/
├── components/     # Reusable UI components
├── screens/        # App screens
├── services/      # Core services (biometrics, keychain)
├── utils/         # Utility functions
├── hooks/         # Custom React hooks
└── types/         # TypeScript type definitions
```

## Important Files

- `app.json` - React Native configuration
- `tsconfig.json` - TypeScript configuration
- `.eslintrc.js` - ESLint rules
- `jest.config.js` - Test configuration

## Development Rules

1. Avoid using Expo or EAS dependencies unless absolutely necessary
2. Use Yarn as the package manager
3. Keep the app as a pure React Native CLI project
4. Run the full validation suite (`yarn validate`) before committing changes