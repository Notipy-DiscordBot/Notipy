# 📁 DiscordBot Directory Overview

This folder contains the Discord bot implementation for the Notipy project. The structure is modular and separated by concerns for better maintainability and scalability.

---

## 📂 Structure

### `main.py`
- The entry point for starting the Discord bot.
- Initializes commands, extensions, and localization.

---

### `commons/`
Shared utilities and configurations used across the bot.

#### `localization/`
- `en-US.json` / `ko.json`: Localization files containing translated strings for supported languages.
- `Options.py`: Defines localized string options used in menus or selects.
- `locale.py`: Functions to retrieve and manage user/server locale preferences.
- `cache.py`: Caching logic for performance optimization.
- `__init__.py`: Initializes the localization package.

#### `var.py`
- Stores global variables and shared configuration constants.

---

### `extensions/`
Each file defines a specific category of bot commands or logic.

- `Dev.py`: Developer/admin tools and debug commands.
- `Misc.py`: Miscellaneous general-purpose commands.
- `Notion.py`: Commands related to Notion integration (e.g., token setup, DB linking).
- `Projects.py`: Commands for managing Notipy projects.
- `User.py`: Commands for managing user preferences or tokens.
- `Webhook.py`: Webhook event handling and external trigger management.

---

## 🛠️ Notes

- The bot uses a **localization-first** design, so all user-facing strings are sourced from the `localization/` files.
- Extensions are loaded dynamically from the `extensions/` folder at startup.
- Follows a clean separation of concerns: logic, localization, and I/O are separated for better testability and contribution.

---

For more information, refer to the [main project README](../README.md) or open an issue if you're contributing.
