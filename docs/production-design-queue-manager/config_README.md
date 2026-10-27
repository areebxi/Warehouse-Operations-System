# Configuration Directory

This directory contains configuration files, data files, and application assets.

## Contents

### Data Files
- **`Pocket Design IDs Database.xlsx`** - Database of pocket design IDs (auto-loaded by application)
- **`Size Reference.xlsx`** - Size reference file with dimensions (user-configured)

### Application Assets
- **`Color Bar.png`** - Color bar image (auto-loaded by application if present)

### Settings
- **`queue_app_settings.json`** - Application settings (auto-created, user preferences)

## Usage

These files are used by the Queue App application:

- **Pocket Design IDs Database**: Automatically loaded from this location on application startup
- **Size Reference**: User selects this file through the application UI
- **Color Bar**: Automatically loaded from this location if present
- **Settings**: Automatically created and managed by the application

## Notes

- The application expects these files in the application directory or user-selected locations
- For production deployment, users will need to configure their own `Size Reference.xlsx` file
- `Pocket Design IDs Database.xlsx` and `Color Bar.png` are optional

---

**Last Updated:** December 29, 2025

