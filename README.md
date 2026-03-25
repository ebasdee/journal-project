# 🌳 Deepak's Chronological Journal Manager

A high-performance, terminal-based journaling system designed for technical professionals. This tool manages daily journals in a hierarchical YAML structure with built-in version control and chronological tree views.

## 🚀 Key Features

* **Vim Integration:** Seamlessly write and edit journals using the power of Vim.
* **Chronological Tree View:** Track the evolution of your entries from the "Original Root" to the "Current" state with full version sub-indexing.
* **Consolidated Reading:** View the full text of all latest entries for any given date at a glance.
* **Transactional Backups:** Automatically creates historical backups only when content actually changes.
* **Changelog Logic:** Attach custom "Reasons for Change" to every edit, creating a human-readable version history.
* **Global Search:** Deep-search through live entries, historical backups, and the archive vault.
* **Safe Archive:** Move old or sensitive entries to a hidden vault with full recovery support.

## 🛠️ Installation & Setup

1.  **Clone the Repository:**
    \`\`\`bash
    git clone git@github.com:ebasdee/journal-project.git
    cd journal-project
    \`\`\`

2.  **Configuration:**
    The script is configured to save journals in your Mavenir OneDrive folder:
    \`~/OneDrive - Mavenir Systems, Inc/personal/journals\`

3.  **Run the Script:**
    \`\`\`bash
    python3 journal.py
    \`\`\`

## 📖 How to Use

* **Option 1 (Write):** Create a new timestamped entry for today.
* **Option 2 (Manage):** * Type a date (YYYY-MM-DD) or hit Enter for today.
    * Press **'t'** to toggle between the **Consolidated Full-Text View** and the **Chronological Version Tree**.
    * Use **'f1'** to toggle the "Final" status of an entry.
    * Use **'1.1'** to view a specific historical version in read-only mode.

## 📁 Storage Structure
Journals are stored logically by date:
\`/journals/YYYY/MM/YYYY-MM-DD/HH-MM.yaml\`

