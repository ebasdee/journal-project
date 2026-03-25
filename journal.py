import yaml
import os
import re
import subprocess
import time
import glob
import shutil
from datetime import datetime

# --- ⚙️  Configuration Loader ---
def load_config():
    """Loads configuration from config.yaml or provides smart defaults."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.yaml")
    
    defaults = {
        'storage': {
            'base_dir': "~/journals",
            'archive_dir': ".archive"
        },
        'editor': {'command': 'vim'},
        'processing': {
            'stop_words': ['the', 'and', 'was', 'for', 'with', 'today', 'went', 'have', 'from', 'this', 'that', 'about', 'after']
        }
    }

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            if user_config:
                if 'storage' in user_config: defaults['storage'].update(user_config['storage'])
                if 'editor' in user_config: defaults['editor'].update(user_config['editor'])
                if 'processing' in user_config: defaults['processing'].update(user_config['processing'])
    
    defaults['storage']['base_dir'] = os.path.expanduser(defaults['storage']['base_dir'])
    return defaults

# Initialize Global Configuration
CONFIG = load_config()
BASE_DIR = CONFIG['storage']['base_dir']
ARCHIVE_DIR = os.path.join(BASE_DIR, CONFIG['storage']['archive_dir'])
TERMINAL_EDITOR = CONFIG['editor']['command']
STOP_WORDS = set(CONFIG['processing']['stop_words'])

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# --- 🛠️  Helper Functions ---

def get_daily_dir(date_obj):
    year, month, day = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%Y-%m-%d")
    target_dir = os.path.join(BASE_DIR, year, month, day)
    os.makedirs(target_dir, exist_ok=True)
    return target_dir

def extract_keywords(text):
    words = re.findall(r'\b\w{3,}\b', text.lower())
    return sorted(list(set(words) - STOP_WORDS))

def open_vim_readonly(content):
    temp_txt = os.path.expanduser("~/journal_view.txt")
    with open(temp_txt, 'w') as f: f.write(content)
    subprocess.run([TERMINAL_EDITOR, "-R", temp_txt])
    if os.path.exists(temp_txt): os.remove(temp_txt)

def open_vim_and_get_text(initial_content=""):
    temp_txt = os.path.expanduser("~/journal_temp.txt")
    with open(temp_txt, 'w') as f: f.write(initial_content)
    subprocess.run([TERMINAL_EDITOR, temp_txt])
    if os.path.exists(temp_txt):
        with open(temp_txt, 'r') as f:
            content = f.read().strip()
        os.remove(temp_txt)
        return content
    return None

# --- 📖 Core Logic Modules ---

def manage_day():
    date_query = input("\nEnter date (YYYY-MM-DD) [Enter for today]: ") or datetime.now().strftime("%Y-%m-%d")
    year, month = date_query[:4], date_query[5:7]
    daily_dir = os.path.join(BASE_DIR, year, month, date_query)
    show_tree = False

    while True:
        os.system('clear')
        if not os.path.exists(daily_dir):
            print(f"❌ No records found for {date_query}."); input("[Enter]"); break
        files = sorted([f for f in os.listdir(daily_dir) if f.endswith(".yaml")])
        if not files: print(f"❌ Folder is empty."); input("[Enter]"); break

        entry_map = []
        
        if not show_tree:
            print(f"--- 📖 CONSOLIDATED JOURNALS: {date_query} ---")
            for i, fname in enumerate(files, 1):
                path = os.path.join(daily_dir, fname)
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    backups = sorted(glob.glob(f"{path}.bak_*"))
                    history_chain = [yaml.safe_load(open(b)) for b in backups]
                    marker = "⭐ [FINAL]" if data['metadata'].get('is_final') else "✅ [CURRENT]"
                    print(f"\n{i}. 🕒 {data['metadata']['time']} {marker} | 🏷️  {data['metadata'].get('change_reason', 'Initial')}")
                    print(f"   {data['summary'].replace(chr(10), chr(10)+'   ')}")
                    print("-" * 30)
                    entry_map.append({'path': path, 'lineage': history_chain + [data]})
        else:
            print(f"--- 🌳 CHRONOLOGICAL TREE: {date_query} ---")
            for i, fname in enumerate(files, 1):
                path = os.path.join(daily_dir, fname)
                backups = sorted(glob.glob(f"{path}.bak_*"))
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
        
        # --- (xN) DELETE LOGIC ---
        elif choice.startswith('x') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                backups = glob.glob(f"{target_path}.bak_*")
                print(f"\n⚠️  WARNING: Deleting Entry {idx} and {len(backups)} history files.")
                confirm = input(f"Type 'yes' to confirm: ").lower()
                if confirm == 'yes':
                    if os.path.exists(target_path): os.remove(target_path)
                    for b in backups: os.remove(b)
                    print(f"✅ Deleted."); time.sleep(1)

        elif choice.startswith('f') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                with open(target_path, 'r') as f: data = yaml.safe_load(f)
                data['metadata']['is_final'] = not data['metadata'].get('is_final', False)
                with open(target_path, 'w') as f: yaml.dump(data, f, sort_keys=False, allow_unicode=True)

        elif choice == 'p':
            all_baks = glob.glob(os.path.join(daily_dir, "*.bak_*"))
            if all_baks and input(f"⚠️  Purge {len(all_baks)} backups? (y/n): ").lower() == 'y':
                for b in all_baks: os.remove(b)
                print("✅ History purged."); time.sleep(1)

        elif choice.startswith('d') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                shutil.move(target_path, os.path.join(ARCHIVE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(target_path)}"))
                print("✅ Archived."); time.sleep(1)

        elif '.' in choice:
            try:
                e_idx, v_idx = map(int, choice.split('.'))
                open_vim_readonly(entry_map[e_idx-1]['lineage'][v_idx]['summary'])
            except: pass

        elif choice.isdigit():
            idx = int(choice)
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                with open(target_path, 'r') as f: old_data = yaml.safe_load(f)
                new_txt = open_vim_and_get_text(old_data['summary'])
                if new_txt and new_txt != old_data['summary']:
                    reason = input("\nReason for change: ") or "Update"
                    bak_path = f"{target_path}.bak_{old_data['metadata']['time'].replace(':','-')}_v{datetime.now().strftime('%H%M%S')}"
                    with open(bak_path, 'w') as f: yaml.dump(old_data, f)
                    old_data.update({'summary': new_txt, 'metadata': {**old_data['metadata'], 'time': datetime.now().strftime("%H:%M"), 'change_reason': reason}})
                    with open(target_path, 'w') as f: yaml.dump(old_data, f, sort_keys=False, allow_unicode=True)
                time.sleep(1)

def write_new_entry():
    now = datetime.now()
    daily_dir = get_daily_dir(now)
    file_path = os.path.join(daily_dir, f"{now.strftime('%H-%M')}.yaml")
    print(f"\n--- 🖋️  New Journal: {now.strftime('%H:%M')} ---")
    summary = open_vim_and_get_text()
    if summary:
        data = {
            'metadata': {'date': now.strftime("%Y-%m-%d"), 'time': now.strftime("%H:%M"), 'is_final': input("FINAL? (y/n): ").lower() == 'y', 'change_reason': 'Initial Version'},
            'summary': summary, 'auto_tags': extract_keywords(summary)
        }
        with open(file_path, 'w') as f: yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        print("✅ Saved."); time.sleep(1)

def search_logs():
    query = input("\nGlobal Search Keyword: ").lower()
    for root, _, files in os.walk(BASE_DIR):
        for file in sorted(files):
            if file.endswith(".yaml") or ".yaml.bak_" in file:
                with open(os.path.join(root, file), 'r') as f:
                    try:
                        data = yaml.safe_load(f)
                        if query in data['summary'].lower() or query in data['metadata']['date']:
                            print(f"📅 {data['metadata']['date']} | 🕒 {data['metadata']['time']}\n{data['summary']}\n" + "-"*30)
                    except: continue
    input("[Enter]")

def recover_entries():
    while True:
        os.system('clear')
        archived = sorted([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".yaml")])
        print("--- ♻️  ARCHIVE VAULT ---")
        if not archived: print("(Empty)"); break
        for i, f in enumerate(archived, 1):
            with open(os.path.join(ARCHIVE_DIR, f), 'r') as file:
                d = yaml.safe_load(file)
                print(f"{i}. [{d['metadata']['date']}] {d['summary'][:60]}...")
        c = input("\n(N) Recover | 'e' Empty | 'q' Back: ").lower()
        if c == 'q': break
        elif c == 'e':
            for f in os.listdir(ARCHIVE_DIR): os.remove(os.path.join(ARCHIVE_DIR, f))
            print("✅ Emptied."); time.sleep(1)
        elif c.isdigit() and 0 < int(c) <= len(archived):
            t_name = archived[int(c)-1]
            with open(os.path.join(ARCHIVE_DIR, t_name), 'r') as f:
                d = yaml.safe_load(f)
                r_dir = get_daily_dir(datetime.strptime(d['metadata']['date'], "%Y-%m-%d"))
                shutil.move(os.path.join(ARCHIVE_DIR, t_name), os.path.join(r_dir, t_name.split("_", 1)[-1]))
                print("✅ Recovered."); time.sleep(1)

def main():
    while True:
        os.system('clear')
        print("==========================================")
        print("📂 DEEPAK'S CHRONOLOGICAL JOURNAL v1.7.0")
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
