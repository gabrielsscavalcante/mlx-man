import subprocess
import os
import time

DESCRIPTIONS = {
    "Safari (and open tabs)": "Web browser. Closing will kill your open tabs.",
    "Google Chrome (and open tabs)": "Web browser. Closing will kill your open tabs.",
    "Antigravity IDE": "Your coding environment. Closing will interrupt your work.",
    "VS Code": "Code editor.",
    "opencode-cli": "The OpenCode AI agent running in your terminal.",
    "Spotify": "Music player.",
    "Slack": "Team communication app.",
    "Discord": "Chat application.",
    "Docker Desktop": "Container virtualization. Very heavy, safe to close if not coding.",
    "Notes": "Apple Notes.",
    "Messages": "Apple Messages (iMessage).",
    "Mail": "Apple Mail client.",
    "Siri AI": "macOS Siri / Apple Intelligence background process.",
    "corespotlightd": "macOS Search indexing (restarts automatically).",
    "language_server": "Code analysis tool used by your IDE.",
    "Activity Monitor": "Task manager app."
}

def get_free_memory_mb():
    try:
        pagesize = int(subprocess.check_output(['sysctl', '-n', 'hw.pagesize']).strip())
        vm_stat = subprocess.check_output(['vm_stat']).decode('utf-8')
        free = inactive = speculative = 0
        for line in vm_stat.split('\n'):
            if 'Pages free' in line: free = int(line.split(':')[1].strip().strip('.'))
            elif 'Pages inactive' in line: inactive = int(line.split(':')[1].strip().strip('.'))
            elif 'Pages speculative' in line: speculative = int(line.split(':')[1].strip().strip('.'))
        
        return (free + inactive + speculative) * pagesize / (1024 * 1024)
    except:
        return 0

def get_processes():
    result = subprocess.run(['ps', '-c', '-x', '-m', '-o', 'pid,rss,comm'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    
    apps = {}
    for line in lines:
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid, rss, comm = parts
        rss = int(rss) // 1024
        
        if rss < 50:
            continue
            
        if 'WebKit' in comm or 'Safari' in comm:
            name = "Safari (and open tabs)"
        elif 'Chrome' in comm:
            name = "Google Chrome (and open tabs)"
        elif 'Antigravity' in comm:
            name = "Antigravity IDE"
        elif 'Code Helper' in comm or 'VS Code' in comm or 'Electron' in comm:
            name = "VS Code"
        elif 'Docker' in comm or 'com.docker' in comm:
            name = "Docker Desktop"
        else:
            name = comm
            
        ignore_list = ['WindowServer', 'Finder', 'Dock', 'loginwindow', 'sysmond', 'kernel_task', 'Terminal', 'zsh', 'bash', 'python3', 'opencode', 'opencode-cli', 'coreaudiod', 'hidd']
        if name in ignore_list:
            continue

        if name not in apps:
            apps[name] = {'total_mb': 0, 'pids': []}
        
        apps[name]['total_mb'] += rss
        apps[name]['pids'].append(pid)
        
    return apps

def main():
    while True:
        os.system('clear')
        print("=================================================")
        print("           Mac Memory Cleaner Helper             ")
        print("=================================================")
        
        free_mb = get_free_memory_mb()
        print(f"Current Estimated Free Memory: ~{int(free_mb / 1024)} GB ({int(free_mb)} MB)")
        print("*(Aim for roughly ~24 GB free if using the massive 35B model)*")
        print("=================================================\n")
        
        apps = get_processes()
        sorted_apps = sorted(apps.items(), key=lambda x: x[1]['total_mb'], reverse=True)
        
        if not sorted_apps:
            print("Your system is already very clean! No large apps found.")
            break
        
        for i, (name, data) in enumerate(sorted_apps):
            desc = DESCRIPTIONS.get(name, "Background process or application.")
            print(f"{i+1}) {name} - {data['total_mb']} MB")
            print(f"   ↳ {desc}")
            print("-" * 50)
            
        print("Type the number of the app you want to forcefully close.")
        print("Type 'q' or 'quit' to finish and continue to the LLM.")
        
        choice = input("\nSelect an option: ")
        
        if choice.lower() in ['q', 'quit', 'exit']:
            print("Continuing...")
            break
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(sorted_apps):
                target_app = sorted_apps[index][0]
                target_pids = sorted_apps[index][1]['pids']
                
                print(f"\nClosing {target_app} (closing {len(target_pids)} background processes)...")
                for pid in target_pids:
                    try:
                        os.kill(int(pid), 9)
                    except ProcessLookupError:
                        pass
                print(f"Successfully freed up ~{sorted_apps[index][1]['total_mb']} MB of memory!")
                time.sleep(1.5) # Give the system a second to reclaim memory
            else:
                print("Invalid number.")
                time.sleep(1)
        except ValueError:
            print("Invalid input.")
            time.sleep(1)

if __name__ == "__main__":
    main()
