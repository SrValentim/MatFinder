# Language Menu Feature

## Overview

This feature adds multi-language support to MatFinder, allowing users to switch between Portuguese, English, and German interfaces.

## Implementation

### Files Added

1. **matfinder/core/settings_manager.py**
   - Manages application settings in a JSON file (`settings.json`)
   - Handles loading and saving user preferences
   - Currently supports language preference storage

2. **matfinder/core/i18n.py**
   - Internationalization (i18n) module
   - Contains translation dictionaries for Portuguese (pt), English (en), and German (de)
   - Provides `tr()` function for translating UI strings
   - Currently translates menu items and dialog messages

### Files Modified

1. **matfinder/app_main.py**
   - Added imports for `settings_manager` and `i18n`
   - Added language initialization in `__init__`
   - Added language submenu in `create_menu()` method
   - Added `change_language()` method to handle language switching
   - Added QActionGroup import for radio button behavior

2. **.gitignore**
   - Added `settings.json` to ignore user-specific configuration

### Features

#### Language Menu
- Located in: **Configuração > Idioma** (or **Settings > Language** in English)
- Three language options:
  - Português (Portuguese)
  - English (English)
  - Deutsch (German)
- Uses radio buttons to show current selection
- Current language is checked in the menu

#### Language Switching
When a user selects a different language:
1. The application saves the preference to `settings.json`
2. A dialog appears asking: "Restart to apply?"
   - **Yes**: Closes the application (user must restart manually)
   - **No**: Shows an info message that restart is needed later

#### Settings Persistence
- User's language choice is saved in `settings.json` in the project root
- Settings are loaded on application startup
- Default language is Portuguese (`pt`) if no settings exist

## Usage

### For Users

1. Open MatFinder
2. Go to menu: **Configuração** → **Idioma**
3. Select your preferred language:
   - **Português** (Portuguese)
   - **English** (English)
   - **Deutsch** (German)
4. When prompted, restart the application to apply changes

### For Developers

#### Adding New Translations

To add translations for new UI elements:

1. Edit `matfinder/core/i18n.py`
2. Add new keys to all language dictionaries (pt, en, de)
3. Use the key in your code: `i18n.tr("your_key")`

Example:
```python
# In i18n.py
TRANSLATIONS = {
    "pt": {
        "my_button": "Meu Botão",
        ...
    },
    "en": {
        "my_button": "My Button",
        ...
    },
    "de": {
        "my_button": "Meine Schaltfläche",
        ...
    }
}

# In your code
from matfinder.core import i18n
button_text = i18n.tr("my_button")
```

#### Adding New Settings

To add new application settings:

1. Edit `matfinder/core/settings_manager.py`
2. Add default value in `load_settings()` method
3. Add getter/setter methods
4. Use in your code via the global `settings_manager` instance

## Testing

Run the test suite:
```bash
python3 tests/test_language_menu.py
```

This verifies:
- Settings manager load/save functionality
- Translation system for all languages
- Language name retrieval
- All menu translations exist

## Future Enhancements

Potential improvements for full internationalization:
1. Translate all UI strings (currently only menu items are translated)
2. Add more languages
3. Automatic restart without manual user action
4. Date/time formatting per locale
5. Number formatting per locale
6. Translation of error messages and tooltips

## Technical Notes

- The language setting is stored in `settings.json` at the project root
- The `settings.json` file is user-specific and not committed to git
- Language changes take effect on next application restart
- Default language is Portuguese to maintain backward compatibility
- The i18n system is extensible for future translation needs
