import yaml
import os
import re
import subprocess
import time
import glob
import shutil
from datetime import datetime

# --- Configuration ---
BASE_DIR = os.path.expanduser("~/OneDrive - Mavenir Systems, Inc/personal/journals")
ARCHIVE_DIR = os.path.join(BASE_DIR, ".archive")
TERMINAL_EDITOR = 'vim' 
STOP_WORDS = {'the', 'and', 'was', 'for', 'with', 'today', 'went', 'have', 'from', 'this', 'that', 'about', 'after'}

os.makedirs(ARCHIVE_DIR, exist_ok=True)

def get_daily_dir(date_obj):
    year = date_obj.strftime("%Y")
    month = date_obj.strftime("%m")
    day_folder = date_obj.strftime("%Y-%m-%d")
    target_dir = os.path.join(BASE_DIR, year, month, day_folder)
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

def manage_day():
    date_query = input("\nEnter date (YYYY-MM-DD) [Enter for today]: ") or datetime.now().strftime("%Y-%m-%d")
    year, month = date_query[:4], date_query[5:7]
    daily_dir = os.path.join(BASE_DIR, year, month, date_query)
    show_tree = False

    while True:
        os.system('clear')
        if not os.path.exists(daily_dir):
            print(f"❌ No records for {date_query}."); input("[Enter]"); break
        files = sorted([f for f in os.listdir(daily_dir) if f.endswith(".yaml")])
        if not files: print(f"❌ No logs found."); input("[Enter]"); break

        entry_map = []
        
        if not show_tree:
            print(f"--- 📖 CONSOLIDATED JOURNALS: {date_query} ---")
            for i, fname in enumerate(files, 1):
                path = os.path.join(daily_dir, fname)
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    backups = sorted(glob.glob(f"{path}.bak_*"))
                    history_chain = []
                    for b in backups:
                        with open(b, 'r') as bf: history_chain.append(yaml.safe_load(bf))
                    
                    marker = "⭐ [FINAL]" if data['metadata'].get('is_final') else "✅ [CURRENT]"
                    reason = data['metadata'].get('change_reason', 'Initial Version')
                    print(f"\n{i}. 🕒 {data['metadata']['time']} {marker} | 🏷️  {reason}")
                    print(f"   {data['summary'].replace(chr(10), chr(10)+'   ')}")
                    print("-" * 30)
                    entry_map.append({'path': path, 'lineage': history_chain + [data]})
        else:
            print(f"--- 🌳 CHRONOLOGICAL TREE: {date_query} ---")
            for i, fname in enumerate(files, 1):
                path = os.path.join(daily_dir, fname)
                backups = sorted(glob.glob(f"{path}.bak_*"))
                with open(path, 'r') as f: current_data = yaml.safe_load(f)
                
                history_chain = []
                for b in backups:
                    with open(b, 'r') as bf: history_chain.append(yaml.safe_load(bf))
                
                # 1. ROOT
                root_data = history_chain[0] if history_chain else current_data
                print(f"\n{i}. 📂 Root Created: {root_data['metadata']['time']}")
                print(f"   └── {root_data['summary'].replace(chr(10), chr(10)+'       ')}")
                
                # 2. EXPLODED BRANCHES
                display_idx = 1
                if history_chain:
                    # Show intermediate backups with full content
                    for b_data in history_chain[1:]:
                        msg = b_data['metadata'].get('change_reason', 'Edit')
                        print(f"       ├── [{i}.{display_idx}] 🏷️  Mod: {msg}")
                        print(f"       │   └── Content: {b_data['summary'].replace(chr(10), chr(10)+'       │                ')}")
                        display_idx += 1
                    
                    # Show Current at the tip with full content
                    final_m = "⭐ [FINAL]" if current_data['metadata'].get('is_final') else "✅ [CURRENT]"
                    curr_reason = current_data['metadata'].get('change_reason', 'Updated')
                    print(f"       └── [{i}.{display_idx}] {final_m}: {curr_reason}")
                    print(f"           └── Content: {current_data['summary'].replace(chr(10), chr(10)+'                        ')}")

                entry_map.append({'path': path, 'lineage': history_chain + [current_data]})

        print("\n" + "="*65)
        print("(N) Edit | (N.M) View | (dN) Archive | (fN) Toggle Final")
        print("'t' Tree View Toggle | 'p' Purge Backups | 'q' Menu")
        choice = input("\nAction: ").lower()

        if choice == 'q': break
        elif choice == 't': show_tree = not show_tree
        elif choice.startswith('f') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                with open(target_path, 'r') as f: data = yaml.safe_load(f)
                data['metadata']['is_final'] = not data['metadata'].get('is_final', False)
                with open(target_path, 'w') as f: yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        elif choice == 'p':
            all_baks = glob.glob(os.path.join(daily_dir, "*.bak_*"))
            if all_baks:
                confirm = input(f"⚠️  Purge {len(all_baks)} backups? (y/n): ").lower()
                if confirm == 'y':
                    for b in all_baks: os.remove(b)
                    print("✅ History purged."); time.sleep(1)
        elif choice.startswith('d') and choice[1:].isdigit():
            idx = int(choice[1:])
            if 0 < idx <= len(entry_map):
                target_path = entry_map[idx-1]['path']
                prefix = datetime.now().strftime('%Y%m%d_%H%M%S')
                shutil.move(target_path, os.path.join(ARCHIVE_DIR, f"{prefix}_{os.path.basename(target_path)}"))
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
                    old_data['summary'] = new_txt
                    old_data['metadata']['time'] = datetime.now().strftime("%H:%M")
                    old_data['metadata']['change_reason'] = reason
                    with open(target_path, 'w') as f: yaml.dump(old_data, f, sort_keys=False, allow_unicode=True)
                time.sleep(1)

# search_logs, write_new_entry, recover_entries, main remain consistent
def write_new_entry():
    now = datetime.now()
    daily_dir = get_daily_dir(now)
    file_path = os.path.join(daily_dir, f"{now.strftime('%H-%M')}.yaml")
    print(f"\n--- 🖋  Write a new Journal: {now.strftime('%H:%M')} ---")
    summary = open_vim_and_get_text()
    if summary:
        is_f = input("Mark as FINAL? (y/n): ").lower() == 'y'
        data = {
            'metadata': {'date': now.strftime("%Y-%m-%d"), 'time': now.strftime("%H:%M"), 'is_final': is_f, 'change_reason': 'Initial Version'},
            'summary': summary, 'auto_tags': extract_keywords(summary)
        }
        with open(file_path, 'w') as f: yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        print("✅ Saved."); time.sleep(1)

def search_logs():
    query = input("\nSearch Keyword: ").lower()
    for root, _, files in os.walk(BASE_DIR):
        for file in sorted(files):
            if file.endswith(".yaml") or ".yaml.bak_" in file:
                with open(os.path.join(root, file), 'r') as f:
                    try:
                        data = yaml.safe_load(f)
                        if query in data['summary'].lower() or query in data['metadata']['date']:
                            lbl = "[ARCH]" if ".archive" in root else ("[BAK]" if ".bak_" in file else "[LIVE]")
                            print(f"📅 {data['metadata']['date']} | 🕒 {data['metadata']['time']} {lbl}\n{data['summary']}\n" + "-"*30)
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
        print("📂 DEEPAK'S CHRONOLOGICAL JOURNAL")
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
