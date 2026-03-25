# 🌳 Deepak's Chronological Journal Manager (v1.9.0)

A high-performance, OS-agnostic terminal journaling system. Designed for technical professionals to track with full version history and zero-configuration overhead.

## 🚀 Key Features

* **Zero-Config Wizard:** Automatically detects your OS (macOS/Windows/Linux) and guides you through setup on the first run.
* **Chronological Tree View:** Recursive "Root-to-Branch" visualization of how your notes evolved over multiple edits.
* **Deep-Clean Deletion (xN):** Targeted purging that removes an entry and its entire hidden version history (`.bak` files) in one click.
* **Smart Storage:** Portable path handling via `pathlib`; perfect for syncing across Google Drive or OneDrive.
* **Vim/Editor Integration:** Seamlessly uses Vim (with readonly `-R` support) or falls back to system defaults like Notepad on Windows.
* **Archive Vault:** Safely tuck away completed project logs while maintaining global searchability.

## 🛠️ Quick Start

1.  **Clone the Repository:**
    ```bash
    git clone git@github.com:ebasdee/journal-project.git
    cd journal-project
    ```

2.  **Run the Manager:**
    ```bash
    python3 journal.py
    ```
    *The wizard will launch if it's your first time.*

## 📖 Commands & Workflow

| Command | Action | Description |
| :--- | :--- | :--- |
| **(N)** | **Edit** | Opens the entry in your preferred editor. |
| **(N.M)** | **View** | Opens a specific historical version in Read-Only mode. |
| **(xN)** | **Delete** | Permanently purges an entry and all its backups. |
| **(dN)** | **Archive** | Moves an entry to the hidden `.archive` vault. |
| **(fN)** | **Final** | Toggles the ⭐ [FINAL] milestone marker. |
| **t** | **Tree** | Toggles between Full-Text view and Chronological Tree. |

## 📁 Cross-Platform Sync
To keep your data synced across machines:
1. Install **Google Drive** or **OneDrive**.
2. Run the script and point the **Storage Path** to your cloud folder.
3. The script handles the rest, ensuring your `config.yaml` stays local and private.

---
*Maintained by ebasdee*
