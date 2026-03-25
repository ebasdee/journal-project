v1.0.0 — Initial Concept
Core Functionality: Basic script to write timestamped journal entries to a nested directory structure (YYYY/MM/YYYY-MM-DD/HH-MM.yaml).
Vim Integration: Automated opening of Vim for entry creation.
Metadata: Initial YAML schema including date, time, and is_final status.

v1.1.0 — Transactional Versioning
Change Detection: Logic added to compare "Before" and "After" text. Backups are now only created if the file content actually changed.
Snapshot Backups: Implemented .bak file generation to prevent data loss during edits.

v1.2.0 — Chronological Tree Architecture
Root-to-Tip Logic: Re-engineered the display to show the [ORIGINAL] version as the Root and subsequent edits as numbered branches (1.1, 1.2).
Lineage Mapping: Backups are now logically linked to their parent entry's original creation time rather than the backup time.
Exploded View: Added recursive printing to show the full text of every historical version within the tree.

v1.3.0 — Changelog & Commit Metadata
Reason for Change: Added a prompt for "Reason for Change" during every edit.
Metadata Sync: Fixed a bug where the change_reason was lagging behind; reasons are now correctly mapped to the versions they created.
Status Toggles: Added the fN command to toggle the ⭐ [FINAL] status of any entry without needing to open the editor.

v1.4.0 — User Experience & Navigation
Read-First Mode: Redesigned the "Manage Journals" entry point to show a Consolidated Full-Text View by default for rapid daily review.
Tree Toggle: Added the t command to switch between the Consolidated view and the Version Tree on demand.
Global Search: Enhanced search functionality to scan across Live entries, Backups, and the Archive Vault simultaneously.

v1.5.0 — Lifecycle & Security
Archive Vault: Implemented a hidden .archive folder system to move entries out of the active workspace.
Recovery Engine: Added logic to restore archived entries (and their full histories) back to their original date-based folders.
Purge Protection: Added the p command to permanently clear local backup files while keeping the latest "Current" version intact.

v1.6.0 — Configuration & Portability
Dynamic Path Resolution: Removed all hardcoded strings for BASE_DIR and ARCHIVE_DIR.
External Configuration: Implemented config.yaml loading logic. The script now looks for this file in its own directory.
Smart Defaults: Added a fallback mechanism that creates a local ~/journals folder if no configuration is found.
Environment Awareness: Integrated os.path.expanduser to ensure tilde (~) paths work correctly across different macOS user accounts.
Privacy Guard: Explicitly added config.yaml to the .gitignore recommendation to prevent leaking local file structures to GitHub.

v1.7.0 — Deep Clean Deletion:
Implemented xN command to permanently delete journals.
Logic automatically identifies and purges associated .bak_ version history files to prevent orphaned data.
Added a strict yes confirmation requirement to prevent accidental deletion of critical technical logs.
Refined the script's visual feedback during deletion to show exactly what files are being destroyed.
