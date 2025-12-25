# Data Directory

This directory contains all user data for MacroPad Configurator.

## Structure

```
data/
├── config.json          # Application configuration
├── profiles/            # User profiles
│   ├── profile.json     # Profile list and current selection
│   ├── macros_wark.json # Profile macro definitions
│   └── macros_sums.json
└── library/             # Macro templates library
    ├── window_1_farm.json
    ├── window_2_farm.json
    └── ankou_attack.json
```

## Backup

To backup your data, simply copy the entire `data/` folder.

## Reset

To reset to defaults, delete the `data/` folder. It will be recreated on next launch with default templates.
