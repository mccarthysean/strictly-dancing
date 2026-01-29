# App Store Assets Checklist

This document lists all required assets for iOS App Store and Google Play Store submission.

## Required Icon Files

Create these files in `apps/mobile/assets/`:

### iOS Icons (Required)
- `icon.png` - 1024x1024px (App Store icon)

### Android Icons (Required)
- `adaptive-icon.png` - 1024x1024px (foreground layer)
- `icon.png` - 512x512px (legacy icon)

### Web/Expo
- `favicon.png` - 48x48px

### Notifications
- `notification-icon.png` - 96x96px (white with transparency)

## Splash Screens

Create these files in `apps/mobile/assets/`:

- `splash.png` - 1284x2778px (centered logo on solid background)

Expo will automatically resize for all device sizes.

## App Store Screenshots

Create a folder `apps/mobile/assets/screenshots/` with:

### iOS Screenshots (Required)
- **iPhone 6.7"** (1290x2796px): login, discover, host_profile, booking, messages
- **iPhone 6.5"** (1284x2778px): Same screens
- **iPhone 5.5"** (1242x2208px): Same screens
- **iPad Pro 12.9"** (2048x2732px): Same screens (if supporting tablets)

### Android Screenshots (Required)
- **Phone** (1080x1920px minimum): 4-8 screenshots
- **Tablet 7"** (1200x1920px): If supporting tablets
- **Tablet 10"** (1920x1200px): If supporting tablets

## Privacy Policy

Add your privacy policy URL to `app.json`:

```json
{
  "expo": {
    "extra": {
      "privacyPolicyUrl": "https://strictlydancing.com/privacy"
    }
  }
}
```

## App Store Metadata

### App Name
- **iOS**: Strictly Dancing (max 30 chars)
- **Android**: Strictly Dancing - Dance Host Marketplace (max 50 chars)

### Subtitle/Short Description
"Connect with dance hosts worldwide" (max 30 chars iOS, 80 chars Android)

### Full Description
```
Strictly Dancing connects travelers and dance enthusiasts with qualified dance hosts for paid social dancing sessions worldwide.

Features:
• Find verified dance hosts near you
• Book sessions for salsa, tango, bachata, and more
• Real-time messaging with hosts
• Secure payments via Stripe
• Leave reviews after sessions
• Host dashboard for managing bookings

Whether you're traveling or looking for a dance partner in your city, Strictly Dancing makes it easy to find the perfect host for your dancing style.
```

### Keywords (iOS - 100 chars max)
dance,dancing,salsa,tango,bachata,lessons,hosts,social,partner,travel

### Category
- **iOS**: Lifestyle or Sports
- **Android**: Social / Lifestyle

### Age Rating
- **iOS**: 4+ (if no user-generated content visible without account)
- **Android**: Teen (13+)

## Build Commands

```bash
# Development build (for testing)
eas build --profile development --platform all

# Preview build (internal testing)
eas build --profile preview --platform all

# Production build (App Store/Play Store)
eas build --profile production --platform all

# Submit to stores
eas submit --platform ios
eas submit --platform android
```

## Pre-submission Checklist

- [ ] All icon sizes created and placed in assets/
- [ ] Splash screen created
- [ ] Screenshots captured for all required sizes
- [ ] Privacy policy page created and URL configured
- [ ] Terms of service page created
- [ ] App metadata written (descriptions, keywords)
- [ ] eas.json configured with correct IDs
- [ ] Apple Developer account set up
- [ ] Google Play Console account set up
- [ ] Stripe account configured for production
- [ ] Sentry project created for production
- [ ] API backend deployed to production
