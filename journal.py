import yaml
import os
import re
import subprocess
import time
import glob
import shutil
from datetime import datetime
from pathlib import Path

# --- 🧙 First Run Wizard ---
def run_wizard(config_path):
    """Walks the user through initial setup if config.yaml is missing."""
    clear_screen()
    print("✨ WELCOME TO DEEPAK'S CHRONOLOGICAL JOURNAL MANAGER ✨")
    print("-------------------------------------------------------")
    print("No configuration found. Let's set up your environment.\n")

    # 1. Choose Storage Path
    default_base = Path.home() / "Documents" / "journals"
    print(f"📂 Where should we store your journals?")
    user_base = input(f"   [Enter for default: {default_base}]: ").strip()
    base_dir = user_base if user_base else str(default_base)

    # 2. Choose Editor
    default_editor = "vim"
    if os.name == 'nt':
        # Check if vim exists on Windows, else fallback to notepad
        try:
            subprocess.run(["vim", "--version"], capture_output=True)
        except FileNotFoundError:
            default_editor = "notepad"
    
    print(f"\n📝 Which text editor do you prefer?")
    user_editor = input(f"   [Enter for default: {default_editor}]: ").strip()
    editor_cmd = user_editor if user_editor else default_editor

    # 3. Save the Config
    config_data = {
        'storage': {
            'base_dir': base_dir,
            'archive_dir': ".archive"
        },
        'editor': {'command': editor_cmd},
        'processing': {
            'stop_words': ['the', 'and', 'was', 'for', 'with', 'today', 'went', 'have', 'from', 'this', 'that', 'about', 'after']
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, sort_keys=False)
    
    print(f"\n✅ Configuration saved to {config_path}!")
    print(f"🚀 Journals will be saved in: {base_dir}")
    time.sleep(2)

# --- ⚙️  Configuration Loader ---
def load_config():
    script_dir = Path(__file__).parent.absolute()
    config_path = script_dir / "config.yaml"
    
    if not config_path.exists():
        run_wizard(config_path)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config['storage']['base_dir'] = Path(config['storage']['base_dir']).expanduser()
    return config

# Initialize Global Configuration
CONFIG = load_config()
BASE_DIR = CONFIG['storage']['base_dir']
ARCHIVE_DIR = BASE_DIR / CONFIG['storage']['archive_dir']
TERMINAL_EDITOR = CONFIG['editor']['command']
STOP_WORDS = set(CONFIG['processing']['stop_words'])

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# --- 🛠️  Helper Functions ---

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_daily_dir(date_obj):
    year, month, day = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%Y-%m-%d")
    target_dir = BASE_DIR / year / month / day
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def extract_keywords(text):
    words = re.findall(r'\b\w{3,}\b', text.lower())
    return sorted(list(set(words) - STOP_WORDS))

def open_editor_readonly(content):
    temp_txt = Path.home() / "journal_view.txt"
    with open(temp_txt, 'w') as f: f.write(content)
    cmd = [TERMINAL_EDITOR, "-R", str(temp_txt)] if 'vim' in TERMINAL_EDITOR else [TERMINAL_EDITOR, str(temp_txt)]
    subprocess.run(cmd, shell=(os.name == 'nt'))
    if temp_txt.exists(): temp_txt.unlink()

def open_editor_and_get_text(initial_content=""):
    temp_txt = Path.home() / "journal_temp.txt"
    with open(temp_txt, 'w') as f: f.write(initial_content)
    subprocess.run([TERMINAL_EDITOR, str(temp_txt)], shell=(os.name == 'nt'))
    if temp_txt.exists():
        with open(temp_txt, 'r') as f:
            content = f.read().strip()
        temp_txt.unlink()
        return content
    return None

# --- 📖 Core Logic Modules ---

def manage_day():
    date_query = input("\nEnter date (YYYY-MM-DD) [Enter for today]: ") or datetime.now().strftime("%Y-%m-%d")
    year, month = date_query[:4], date_query[5:7]
    daily_dir = BASE_DIR / year / month / date_query
    show_tree = False

    while True:
        clear_screen()
        if not daily_dir.exists():
            print(f"❌ No records found for {date_query}."); input("[Enter]"); break
        
        files = sorted([f for f in daily_dir.glob("*.yaml") if ".bak_" not in f.name])
        if not files: print(f"❌ Folder is empty."); input("[Enter]"); break

        entry_map = []
        
        if not show_tree:
            print(f"--- 📖 CONSOLIDATED JOURNALS: {date_query} ---")
            for i, path in enumerate(files, 1):
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    backups = sorted(daily_dir.glob(f"{path.name}.bak_*"))
                    history_chain = [yaml.safe_load(open(b)) for b in backups]
                    marker = "⭐ [FINAL]" if data['metadata'].get('is_final') else "✅ [CURRENT]"
                    print(f"\n{i}. 🕒 {data['metadata']['time']} {marker} | 🏷️  {data['metadata'].get('change_reason', 'Initial')}")
                    print(f"   {data['summary'].replace(chr(10), chr(10)+'   ')}")
                    print("-" * 30)
                    entry_map.append({'path': path, 'lineage': history_chain + [data]})
        else:
            print(f"--- 🌳 CHRONOLOGICAL TREE: {date_query} ---")
            for i, path in enumerate(files, 1):
                backups = sorted(daily_dir.glob(f"{path.name}.bak_*"))
                with open(path, 'r') as f: current_data = yaml.safe_load(f)
                history_chain = [yaml.safe_load(open(b)) for b in backups]
                root_data = history_chain[0] if history_chain else current_data
                print(f"\n{i}. 📂 Root Created: {root_data['metadata']['time']}")
                print(f"   └── {root_data['summary'].replace(chr(10), chr(10)+'       ')}")
                display_idx = 1
                if history_chain:
                    for b_data in history_chain[1:]:
                        print(f"       ├── [{i}.{display_idx}] 🏷️  {b_data['metadata'].get('change_reason', 'Edit')}")
                        print(f"       │   └── {b_data['summary'].replace(chr(10), chr(10)+'       │       ')}")
                        display_idx += 1
                    final_m = "⭐ [FINAL]" if current_data['metadata'].get('is_final') else "✅ [CURRENT]"
                    print(f"       └── [{i}.{display_idx}] {final_m}: {current_data['metadata'].get('change_reason', 'Updated')}")
                    print(f"           └── {current_data['summary'].replace(chr(10), chr(10)+'                       ')}")
                entry_map.append({'path': path, 'lineage': history_chain + [current_data]})

        print("\n" + "="*65)
        print("(N) Edit | (N.M) View | (dN) Archive | (xN) DELETE | (fN) Toggle Final")
        print("'t' Tree View Toggle | 'p' Purge Backups | 'q' Menu")
        choice = input("\nAction: ").lower()

        if choice == 'q': break
        elif choice == 't': show_tree = not show_tree
        elif choice.startswith('x') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                backups = list(daily_dir.glob(f"{target_path.name}.bak_*"))
                confirm = input(f"⚠️  Delete Entry {idx} and {len(backups)} history files? (yes/no): ").lower()
                if confirm == 'yes':
                    target_path.unlink(missing_ok=True)
                    for b in backups: b.unlink(missing_ok=True)
                    print(f"✅ Deleted."); time.sleep(1)

        elif choice.startswith('f') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                with open(target_path, 'r') as f: data = yaml.safe_load(f)
                data['metadata']['is_final'] = not data['metadata'].get('is_final', False)
                with open(target_path, 'w') as f: yaml.dump(data, f, sort_keys=False, allow_unicode=True)

        elif choice == 'p':
            all_baks = list(daily_dir.glob("*.bak_*"))
            if all_baks and input(f"⚠️  Purge {len(all_baks)} backups? (y/n): ").lower() == 'y':
                for b in all_baks: b.unlink()
                print("✅ History purged."); time.sleep(1)

        elif choice.startswith('d') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                dest = ARCHIVE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{target_path.name}"
                shutil.move(str(target_path), str(dest))
                print("✅ Archived."); time.sleep(1)

        elif '.' in choice:
            try:
                e_idx, v_idx = map(int, choice.split('.'))
                open_editor_readonly(entry_map[e_idx-1]['lineage'][v_idx]['summary'])
            except: pass

        elif choice.isdigit():
            idx = int(choice)
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                with open(target_path, 'r') as f: old_data = yaml.safe_load(f)
                new_txt = open_editor_and_get_text(old_data['summary'])
                if new_txt and new_txt != old_data['summary']:
                    reason = input("\nReason for change: ") or "Update"
                    bak_path = daily_dir / f"{target_path.name}.bak_{old_data['metadata']['time'].replace(':','-')}_v{datetime.now().strftime('%H%M%S')}"
                    with open(bak_path, 'w') as f: yaml.dump(old_data, f)
                    old_data.update({'summary': new_txt, 'metadata': {**old_data['metadata'], 'time': datetime.now().strftime("%H:%M"), 'change_reason': reason}})
                    with open(target_path, 'w') as f: yaml.dump(old_data, f, sort_keys=False, allow_unicode=True)
                time.sleep(1)

def write_new_entry():
    now = datetime.now()
    daily_dir = get_daily_dir(now)
    file_path = daily_dir / f"{now.strftime('%H-%M')}.yaml"
    print(f"\n--- 🖋️  New Journal: {now.strftime('%H:%M')} ---")
    summary = open_editor_and_get_text()
    if summary:
        data = {
            'metadata': {'date': now.strftime("%Y-%m-%d"), 'time': now.strftime("%H:%M"), 'is_final': input("FINAL? (y/n): ").lower() == 'y', 'change_reason': 'Initial Version'},
            'summary': summary, 'auto_tags': extract_keywords(summary)
        }
        with open(file_path, 'w') as f: yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        print("✅ Saved."); time.sleep(1)

def search_logs():
    query = input("\nGlobal Search Keyword: ").lower()
    for root, _, files in os.walk(str(BASE_DIR)):
        for file in sorted(files):
            if file.endswith(".yaml") or ".yaml.bak_" in file:
                path = Path(root) / file
                with open(path, 'r') as f:
                    try:
                        data = yaml.safe_load(f)
                        if query in data['summary'].lower() or query in data['metadata']['date']:
                            print(f"📅 {data['metadata']['date']} | 🕒 {data['metadata']['time']}\n{data['summary']}\n" + "-"*30)
                    except: continue
    input("[Enter]")

def recover_entries():
    while True:
        clear_screen()
        archived = sorted([f for f in ARCHIVE_DIR.glob("*.yaml")])
        print("--- ♻️  ARCHIVE VAULT ---")
        if not archived: print("(Empty)"); break
        for i, path in enumerate(archived, 1):
            with open(path, 'r') as file:
                d = yaml.safe_load(file)
                print(f"{i}. [{d['metadata']['date']}] {d['summary'][:60]}...")
        c = input("\n(N) Recover | 'e' Empty | 'q' Back: ").lower()
        if c == 'q': break
        elif c == 'e':
            for f in ARCHIVE_DIR.glob("*"): f.unlink()
            print("✅ Emptied."); time.sleep(1)
        elif c.isdigit() and 0 < int(c) <= len(archived):
            t_path = archived[int(c)-1]
            with open(t_path, 'r') as f:
                d = yaml.safe_load(f)
                r_dir = get_daily_dir(datetime.strptime(d['metadata']['date'], "%Y-%m-%d"))
                shutil.move(str(t_path), str(r_dir / t_path.name.split("_", 1)[-1]))
                print("✅ Recovered."); time.sleep(1)

def main():
    while True:
        clear_screen()
        print("==========================================")
        print(f"📂 DEEPAK'S CHRONOLOGICAL JOURNAL v1.9.0")
        print(f"🖥️  OS: {'Windows' if os.name == 'nt' else 'macOS/Linux'}")
        print("==========================================")
        print("1. 🖋️  Write a new Journal\n2. 🛠️  Manage Journals\n3. 🔍 Global Search\n4. ♻️  Archive & Recovery\n5. 🚪 Exit")
        choice = input("\nSelect (1-5): ")
        if choice == '1': write_new_entry()
        elif choice == '2': manage_day()
        elif choice == '3': search_logs()
        elif choice == '4': recover_entries()
        elif choice == '5': break

if __name__ == "__main__":
    main()
