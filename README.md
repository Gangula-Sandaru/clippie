<div align="center">
  <img src="assets/icon.ico" width="128" height="128" />
  <h1>Clippie - Your Smart Clipboard Manager</h1>
  <p><b>A modern, lightning-fast, and intelligent clipboard manager built with Python and Qt.</b></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
</div>

<br>

**Clippie** isn't just another clipboard history tool—it's designed from the ground up to be smart, seamlessly integrated with Windows, and beautiful to look at. With dynamic theming, stealthy background operations, intelligent data sorting, and robust file/image payload support, Clippie revolutionizes how you interact with your desktop history.

---

## ✨ Features

- 🖼️ **Native Image & File Support**: Don't just copy text! Raw images, screenshots, and file paths are intercepted, cached locally, and fully structured as rich `.MimeData`. Seamlessly paste images straight from Clippie directly into Discord, Word, or natively drop them as files into Windows Explorer directories!
- 🎨 **Dynamic Theme Engine**: Three high-quality modern stylesheets built-in—**Dark OLED**, **Tokyo Night**, and **Light Minimal**. The entire application (from menus to system tray instances) hot-swaps visually without needing a restart.
- ⌨️ **Double-Ctrl Quick Access**: Out-of-the-box global hotkey detection. Just rapidly tap `Ctrl` twice to smoothly summon or banish your clipboard directly under your mouse.
- 🚀 **The Floating Dot (Hover Mode)**: Hold `Alt` and hover over a tiny, configurable on-screen dot to peek at your Recent Clips instantly. Move your mouse away, and the window dynamically closes itself.
- 🧠 **Intelligent Auto-Tagging**: Every distinct type of text (URLs, Code Blocks, Emails, standard text) is accurately separated and dynamically filtered in your expanded Dashboard view with customized styling.
- 📌 **Pin & Favorite Mechanics**: Permanently tag imperative clips or images directly from the floating quick-view card with a single star click. Favorited clips resist history truncation and cleanups.
- 👻 **Stealth System Tray Engine**: Say goodbye to a cluttered taskbar. Clippie initializes instantly to your clock tray when launched. Right-click the icon to natively pause background listening, open the Dashboard, or forcefully terminate the process.
- ⚡ **Lightning Fast SQLite**: Thousands of clips are instantly archived via our fast, asynchronous SQLite backbone with zero application lag.

## 🛠️ Installation

Clippie requires Python 3.8+ to run. 

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YourUsername/Clippie.git
   cd Clippie
   ```
2. **Setup your Virtual Environment (Optional but recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Clippie primarily relies on `PyQt5`, `keyboard`, `pyperclip`, and `Pillow`)*
4. **Launch Clippie!**
   ```bash
   python main.py
   ```

## 🎮 Usage 

1. On your very first launch, Clippie will greet you with a beautiful 5-step onboarding overlay detailing the core features.
2. The UI natively divides into two facets:
   - **The Dashboard (`HistoryWindow`)**: The massive search-capable command center allowing you to edit records, delete items, filter specifically by "IMAGES" or "URLS", and control your settings (Syncing, Wiping, Hotkeys).
   - **The Quick Menu (`MainWindow`)**: The compact, floating fast-access list. Click **any item** on this list, and Clippie automatically simulates the Ctrl+V shortcut instantly into whatever app you were using in the background!
3. If you want to temporarily stop Clippie from watching your `Ctrl+C` behavior (such as when working with sensitive keys or passwords), simply right-click the system tray icon and select **Pause Tracking**. 

## ❤️ Open Source & Donations

Clippie is an entirely open-source project created out of a desire for a genuinely powerful, fast, and beautiful utility without bloated executable sizes or subscription fees.

Feel free to open issues, submit Pull Requests, or fork the repository! Contributions regarding Linux/macOS specific clipboard payload testing are heavily welcome!

If you find Clippie actively improving your workflow every single day, consider fueling the project by buying me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/YOUR_KOFI_LINK)
*(Or support through [Patreon](https://patreon.com/YOUR_PATREON_LINK) / [GitHub Sponsors](https://github.com/sponsors/YOUR_USERNAME))*

Contributions directly fund hosting costs for the built-in Cloud Sync backup mechanisms and enable continued full-time optimizations! Thanks for checking it out! 