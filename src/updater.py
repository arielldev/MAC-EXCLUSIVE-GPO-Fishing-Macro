import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import zipfile
import tempfile
import shutil
from datetime import datetime

class UpdateManager:
    def __init__(self, app):
        self.app = app
        self.repo_url = "https://api.github.com/repos/arielldev/gpo-fishing/commits/main"
        self.download_url = "https://github.com/arielldev/gpo-fishing/archive/refs/heads/main.zip"
        self.last_check = 0
        self.check_interval = 300  # 5 minutes
        
        print("✅ Simple UpdateManager initialized")

    def check_for_updates_manual(self):
        """Manual update check triggered by user"""
        try:
            self.app.update_status('Checking for updates...', 'info', '🔍')
            print("🔍 Manual update check started")
            
            # Check GitHub for latest commit
            response = requests.get(self.repo_url, timeout=10)
            if response.status_code != 200:
                self.app.update_status('Failed to check for updates', 'error', '❌')
                print(f"❌ GitHub API returned status {response.status_code}")
                return
            
            commit_data = response.json()
            commit_hash = commit_data['sha'][:7]
            commit_message = commit_data['commit']['message'].split('\n')[0]
            
            print(f"✅ Found commit: {commit_hash} - {commit_message}")
            
            # Always show update dialog for manual checks (let user decide)
            self.app.root.after(0, lambda: self._show_update_dialog(commit_hash, commit_message, commit_data))
            
        except requests.exceptions.ConnectionError:
            self.app.update_status('No internet connection', 'error', '❌')
            print("❌ No internet connection")
        except requests.exceptions.Timeout:
            self.app.update_status('Update check timed out', 'error', '❌')
            print("❌ Update check timed out")
        except Exception as e:
            self.app.update_status(f'Update check failed: {str(e)[:20]}...', 'error', '❌')
            print(f"❌ Update check error: {e}")

    def _show_update_dialog(self, commit_hash, commit_message, commit_data):
        """Show simple update dialog"""
        try:
            print(f"🔄 Showing update dialog for commit {commit_hash}")
            
            dialog = tk.Toplevel(self.app.root)
            dialog.title("Update Available")
            dialog.geometry("450x250")
            dialog.resizable(False, False)
            dialog.transient(self.app.root)
            dialog.grab_set()
            
            # Force dialog to be on top and visible
            dialog.attributes('-topmost', True)
            dialog.lift()
            dialog.focus_force()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            print("✅ Update dialog created and positioned")
            
            # Main frame
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill="both", expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="🔄 Update Available", 
                                   font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 15))
            
            # Info
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill="x", pady=(0, 20))
            
            ttk.Label(info_frame, text=f"Latest Commit: {commit_hash}", 
                     font=("Arial", 10)).pack(anchor="w")
            ttk.Label(info_frame, text=f"Changes: {commit_message}", 
                     font=("Arial", 10), wraplength=400).pack(anchor="w", pady=(5, 0))
            
            # Warning
            warning_label = ttk.Label(main_frame, 
                                     text="⚠️ This will download and install the latest version.\nYour settings will be preserved.",
                                     font=("Arial", 9), foreground="orange")
            warning_label.pack(pady=(0, 20))
            
            # Buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x")
            
            def on_update():
                dialog.destroy()
                self._download_and_install_update(commit_data)
            
            def on_cancel():
                dialog.destroy()
                self.app.update_status('Update cancelled', 'info', '❌')
            
            ttk.Button(btn_frame, text="Update Now", command=on_update).pack(side="right", padx=(10, 0))
            ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right")
            
            print("✅ Update dialog fully created with buttons")
        
        except Exception as e:
            print(f"❌ Error creating update dialog: {e}")
            # Fallback: show simple messagebox
            import tkinter.messagebox as msgbox
            result = msgbox.askyesno("Update Available", 
                                   f"New update available!\n\nCommit: {commit_hash}\nChanges: {commit_message}\n\nDownload and install?")
            if result:
                self._download_and_install_update(commit_data)
            else:
                self.app.update_status('Update cancelled', 'info', '❌')

    def _download_and_install_update(self, commit_data):
        """Download and install the update with progress feedback"""
        try:
            self.app.update_status('Downloading update...', 'info', '⬇️')
            print("🔄 Starting update download...")
            
            # Download the zip file
            response = requests.get(self.download_url, timeout=60, stream=True)
            if response.status_code != 200:
                self.app.update_status('Download failed', 'error', '❌')
                return
            
            # Use temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "update.zip")
                
                # Save the downloaded file
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.app.update_status('Extracting update...', 'info', '📦')
                print("📦 Extracting update files...")
                
                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the extracted folder
                extracted_folder = None
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path) and 'gpo-fishing' in item.lower():
                        extracted_folder = item_path
                        break
                
                if not extracted_folder:
                    self.app.update_status('Extraction failed - folder not found', 'error', '❌')
                    return
                
                self.app.update_status('Installing update...', 'info', '⚙️')
                print("⚙️ Installing update files...")
                
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Create backup folder
                backup_dir = os.path.join(project_root, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                os.makedirs(backup_dir, exist_ok=True)
                
                # Files and folders to preserve (user data)
                preserve_items = [
                    'default_settings.json',
                    'presets',
                    '.git',
                    '.gitignore',
                    'installed_version.json'
                ]
                
                # Backup current installation
                print("💾 Creating backup...")
                for item in os.listdir(project_root):
                    if item.startswith('backup_'):
                        continue
                    
                    src_path = os.path.join(project_root, item)
                    backup_path = os.path.join(backup_dir, item)
                    
                    try:
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, backup_path, ignore_errors=True)
                        else:
                            shutil.copy2(src_path, backup_path)
                    except Exception as e:
                        print(f"Warning: Could not backup {item}: {e}")
                
                # Install new files
                print("🔄 Installing new files...")
                for item in os.listdir(extracted_folder):
                    # Skip preserved items
                    if item in preserve_items:
                        print(f"⏭️ Preserving {item}")
                        continue
                    
                    src_path = os.path.join(extracted_folder, item)
                    dst_path = os.path.join(project_root, item)
                    
                    try:
                        # Remove existing file/folder
                        if os.path.exists(dst_path):
                            if os.path.isdir(dst_path):
                                shutil.rmtree(dst_path)
                            else:
                                os.remove(dst_path)
                        
                        # Copy new file/folder
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dst_path)
                        else:
                            shutil.copy2(src_path, dst_path)
                        
                        print(f"✅ Updated {item}")
                        
                    except Exception as e:
                        print(f"❌ Error updating {item}: {e}")
                
                self.app.update_status('Update complete! Restarting...', 'success', '✅')
                print("✅ Update installation complete!")
                
                # Schedule restart
                self.app.root.after(2000, self._restart_application)
                
        except requests.exceptions.ConnectionError:
            self.app.update_status('No internet connection', 'error', '❌')
        except requests.exceptions.Timeout:
            self.app.update_status('Download timed out', 'error', '❌')
        except Exception as e:
            error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            self.app.update_status(f'Update failed: {error_msg}', 'error', '❌')
            print(f"❌ Update error: {e}")

    def _restart_application(self):
        """Restart the application after update"""
        try:
            import subprocess
            
            print("🔄 Restarting application...")
            
            # Close current application
            self.app.root.quit()
            self.app.root.destroy()
            
            # Determine how to restart
            if getattr(sys, 'frozen', False):
                # Running as executable
                subprocess.Popen([sys.executable])
            else:
                # Running as Python script - find the main entry point
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Look for common main script names
                main_scripts = ['main.py', 'gui.py', 'app.py', 'run.py']
                main_script = None
                
                for script in main_scripts:
                    script_path = os.path.join(project_root, script)
                    if os.path.exists(script_path):
                        main_script = script_path
                        break
                
                # Also check src folder
                if not main_script:
                    src_dir = os.path.join(project_root, 'src')
                    for script in main_scripts:
                        script_path = os.path.join(src_dir, script)
                        if os.path.exists(script_path):
                            main_script = script_path
                            break
                
                if main_script:
                    subprocess.Popen([sys.executable, main_script])
                else:
                    print("❌ Could not find main script to restart")
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Restart failed: {e}")
            messagebox.showerror("Restart Failed", 
                               f"Could not restart automatically.\nPlease restart the application manually.\n\nError: {e}")
            sys.exit(1)