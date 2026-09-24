#!/usr/bin/env python3
import sys
import os
import json
import datetime
import time
from pathlib import Path

# Add src to path to import siblings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_inspector import delete_model, discover_models, _format_bytes, R, B, D, RED, GRN, YLW, CYN, clear, header, info, warn, success, error, divider

# Store history locally inside the project directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_ROOT, ".model_usage_history.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def record_usage(model_id):
    data = load_data()
    if model_id not in data:
        data[model_id] = {"count": 0, "last_used": None}
    data[model_id]["count"] += 1
    data[model_id]["last_used"] = datetime.datetime.now().isoformat()
    save_data(data)

def press_enter_to_continue():
    print()
    input(f"  {D}Press Enter to continue...{R}")

def show_insights():
    while True:
        clear()
        header("Insights & History")
        data = load_data()
        
        installed_models = discover_models()
        installed_model_ids = {m["model_id"]: m for m in installed_models}
        
        # Filter usage data for installed models to not show uninstalled models?
        # The prompt says "show info of used models". We should probably show all used models,
        # but only allow deletion if they are installed.
        
        # Determine most used model from history
        sorted_usage = sorted(data.items(), key=lambda x: x[1]["count"], reverse=True)
        
        print()
        if not sorted_usage:
            info("No usage history found yet.")
            print()
        else:
            most_used_id, most_used_data = sorted_usage[0]
            print(f"  {B}🏆 Most Used Model:{R} {GRN}{most_used_id}{R} ({most_used_data['count']} times)")
            print()
            
        # Combine installed with usage data
        usage_list = []
        total_disk_bytes = 0
        for m_id, m_dict in installed_model_ids.items():
            count = data.get(m_id, {}).get("count", 0)
            last_used = data.get(m_id, {}).get("last_used", "Never")
            disk_bytes = m_dict.get("disk_bytes", 0)
            total_disk_bytes += disk_bytes
            if last_used != "Never":
                try:
                    dt = datetime.datetime.fromisoformat(last_used)
                    last_used = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            usage_list.append((count, m_id, last_used, disk_bytes, m_dict))
            
        # Show a list of models that are not used that much anymore
        # "Least used" = bottom half, or models with 0 count, or models not used in last X days
        header(f"Installed Models - Least Used (Total size: {_format_bytes(total_disk_bytes)})")
            
        usage_list.sort(key=lambda x: x[0]) # Ascending by count
        
        for idx, (count, m_id, last_used, disk_bytes, _) in enumerate(usage_list):
            formatted_size = _format_bytes(disk_bytes)
            print(f"  {B}{CYN}[{idx+1}]{R} {m_id} {YLW}({formatted_size}){R}")
            print(f"      {D}Times used: {count}  |  Last used: {last_used}{R}")
            divider()
        
        if not usage_list:
            info("No models installed.")
                
        print()
        if installed_model_ids:
            print(f"  {B}{GRN}[Number]{R} Select a model to remove completely")
        print(f"  {B}{GRN}[B]{R} Back to Main Menu")
        print()
        choice = input(f"  {B}Choice:{R} ").strip()
        
        if choice.lower() == 'b' or choice == '':
            return
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(usage_list):
                selected_model = usage_list[idx][4]
                model_name = selected_model.get("registry", {}).get("name", selected_model["model_id"].split("/")[-1])
                print()
                confirm = input(f"  {RED}Are you sure you want to completely remove {model_name}? [y/N]: {R}").strip().lower()
                if confirm == 'y':
                    if delete_model(selected_model):
                        press_enter_to_continue()
            else:
                warn("Invalid choice.")
                time.sleep(1)
        except ValueError:
            warn("Invalid input.")
            time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "record" and len(sys.argv) > 2:
            record_usage(sys.argv[2])
        elif sys.argv[1] == "show":
            show_insights()
    else:
        show_insights()
