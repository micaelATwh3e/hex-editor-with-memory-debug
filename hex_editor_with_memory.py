#!/usr/bin/env python3
"""
Hex Editor with Real-time Memory Monitoring
A hex editor that can monitor live process memory with breakpoints
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
from datetime import datetime
import psutil
import ctypes
from ctypes import wintypes, Structure, c_size_t, c_void_p
import subprocess
import sys

# Windows API structures for memory enumeration
class MEMORY_BASIC_INFORMATION(Structure):
    _fields_ = [
        ("BaseAddress", c_void_p),
        ("AllocationBase", c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD)
    ]

# Memory protection constants
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
MEM_IMAGE = 0x1000000


class HexEditorWithMemoryMonitoring:
    def __init__(self, root):
        self.root = root
        self.root.title("Hex Editor with Memory Monitoring")
        self.root.geometry("1400x800")
        
        # File editing
        self.current_file = None
        self.file_data = bytearray()
        self.modified = False
        
        # Memory monitoring
        self.target_process = None
        self.process_handle = None
        self.process_base_address = 0
        self.process_memory_snapshot = bytearray()
        self.monitoring_active = False
        self.monitor_thread = None
        self.running = True
        
        # Breakpoints and debugging
        self.breakpoints = {0x14}  # Default breakpoint at 0x14
        self.last_breakpoint_time = 0
        self.breakpoint_cooldown = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        
        # Memory menu
        memory_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Memory Debug", menu=memory_menu)
        memory_menu.add_command(label="Attach to Process", command=self.show_process_selector)
        # memory_menu.add_command(label="Launch Test Process", command=self.launch_test_process)
        memory_menu.add_separator()
        memory_menu.add_command(label="Start Monitoring", command=self.start_memory_monitoring)
        memory_menu.add_command(label="Stop Monitoring", command=self.stop_memory_monitoring)
        
        # Create main paned window for file view and memory monitoring
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left pane: Hex file viewer
        file_frame = ttk.LabelFrame(main_paned, text="Hex File Viewer", padding="5")
        main_paned.add(file_frame, weight=1)
        
        # File toolbar
        file_toolbar = ttk.Frame(file_frame)
        file_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(file_toolbar, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=5)
        
        # File hex display
        self.file_hex_text = scrolledtext.ScrolledText(file_frame, font=("Courier", 10), 
                                                      wrap=tk.NONE, height=25)
        self.file_hex_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for file display
        self.file_hex_text.tag_config("offset", foreground="#0000FF")
        self.file_hex_text.tag_config("hex", foreground="#000000")
        self.file_hex_text.tag_config("ascii", foreground="#008000")
        self.file_hex_text.tag_config("modified", background="#FFFF99")
        
        # Right pane: Memory monitoring
        memory_frame = ttk.LabelFrame(main_paned, text="Real-time Memory Monitor", padding="5")
        main_paned.add(memory_frame, weight=1)
        
        # Memory controls
        control_frame = ttk.Frame(memory_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(control_frame, text="Attach Process", 
                  command=self.show_process_selector).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Start Monitor", 
                  command=self.start_memory_monitoring).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Stop Monitor", 
                  command=self.stop_memory_monitoring).pack(side=tk.LEFT, padx=2)
        
        # Breakpoint controls
        bp_frame = ttk.Frame(memory_frame)
        bp_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(bp_frame, text="Breakpoint (hex):").pack(side=tk.LEFT)
        self.bp_entry = ttk.Entry(bp_frame, width=8)
        self.bp_entry.pack(side=tk.LEFT, padx=5)
        self.bp_entry.insert(0, "14")
        
        ttk.Button(bp_frame, text="Add BP", 
                  command=self.add_breakpoint).pack(side=tk.LEFT, padx=2)
        ttk.Button(bp_frame, text="Clear All", 
                  command=self.clear_breakpoints).pack(side=tk.LEFT, padx=2)
        
        # Memory hex display
        self.memory_hex_text = scrolledtext.ScrolledText(memory_frame, font=("Courier", 10), 
                                                        wrap=tk.NONE, height=15)
        self.memory_hex_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configure tags for memory display  
        self.memory_hex_text.tag_config("breakpoint", background="#FF6B6B", foreground="#FFFFFF")
        self.memory_hex_text.tag_config("changed", background="#FFE66D")
        
        # Status and log
        log_frame = ttk.LabelFrame(memory_frame, text="Memory Debug Log", padding="5")
        log_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.memory_log_text = scrolledtext.ScrolledText(log_frame, height=6, font=("Courier", 9))
        self.memory_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial messages
        self.log_memory_message("🚀 Memory Debugger Ready!")
        self.log_memory_message("🎯 Default breakpoint set at offset 0x14")
    
    def open_file(self):
        """Open a binary file"""
        filename = filedialog.askopenfilename(
            title="Open Binary File",
            filetypes=[("All Files", "*.*"), ("Binary Files", "*.bin")]
        )
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    self.file_data = bytearray(f.read())
                
                self.current_file = filename
                self.modified = False
                self.display_file_hex()
                self.update_status(f"Opened: {os.path.basename(filename)} ({len(self.file_data)} bytes)")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def save_file(self):
        """Save the current file"""
        if not self.current_file:
            self.save_as_file()
            return
        
        try:
            with open(self.current_file, 'wb') as f:
                f.write(self.file_data)
            
            self.modified = False
            self.update_status(f"Saved: {os.path.basename(self.current_file)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def save_as_file(self):
        """Save file with new name"""
        filename = filedialog.asksaveasfilename(
            title="Save Binary File",
            filetypes=[("All Files", "*.*"), ("Binary Files", "*.bin")]
        )
        
        if filename:
            self.current_file = filename
            self.save_file()
    
    def display_file_hex(self):
        """Display file data in hex format"""
        self.file_hex_text.delete(1.0, tk.END)
        
        if not self.file_data:
            self.file_hex_text.insert(tk.END, "No file loaded")
            return
        
        for i in range(0, len(self.file_data), 16):
            # Address
            addr_str = f"{i:08X}  "
            self.file_hex_text.insert(tk.END, addr_str, "offset")
            
            # Hex bytes
            row_data = self.file_data[i:i+16]
            hex_str = " ".join([f"{byte:02X}" for byte in row_data])
            hex_str += "   " * (16 - len(row_data))  # Pad incomplete rows
            self.file_hex_text.insert(tk.END, hex_str, "hex")
            
            # ASCII
            ascii_str = " |"
            for byte in row_data:
                ascii_str += chr(byte) if 32 <= byte <= 126 else "."
            ascii_str += "|\n"
            self.file_hex_text.insert(tk.END, ascii_str, "ascii")
    
    def display_memory_hex(self):
        """Display process memory in hex format"""
        self.memory_hex_text.delete(1.0, tk.END)
        
        if not self.process_memory_snapshot:
            self.memory_hex_text.insert(tk.END, "No process memory loaded")
            return
        
        for i in range(0, len(self.process_memory_snapshot), 16):
            # Address (base + offset)
            addr_str = f"{self.process_base_address + i:08X}  "
            self.memory_hex_text.insert(tk.END, addr_str, "offset")
            
            # Hex bytes with breakpoint highlighting
            row_data = self.process_memory_snapshot[i:i+16]
            for j, byte in enumerate(row_data):
                offset = i + j
                hex_str = f"{byte:02X} "
                
                # Check if this offset has a breakpoint
                if offset in self.breakpoints:
                    self.memory_hex_text.insert(tk.END, hex_str, "breakpoint")
                else:
                    self.memory_hex_text.insert(tk.END, hex_str, "hex")
            
            # Pad incomplete rows
            if len(row_data) < 16:
                self.memory_hex_text.insert(tk.END, "   " * (16 - len(row_data)))
            
            # ASCII
            ascii_str = " |"
            for byte in row_data:
                ascii_str += chr(byte) if 32 <= byte <= 126 else "."
            ascii_str += "|\n"
            self.memory_hex_text.insert(tk.END, ascii_str, "ascii")
    
    def show_process_selector(self):
        """Show process selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Process")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select a process to monitor:").pack(pady=10)
        
        # Search filter frame
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        def clear_search():
            search_var.set("")
            search_entry.focus()
        
        ttk.Button(search_frame, text="Clear", command=clear_search, width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        # Add helpful hint
        hint_label = ttk.Label(dialog, text="💡 Type to filter processes (e.g., 'note' for notepad, 'calc' for calculator)", 
                              font=('TkDefaultFont', 8), foreground='gray')
        hint_label.pack(pady=(0, 5))
        
        # Process list
        columns = ('PID', 'Name', 'Arch')
        tree = ttk.Treeview(dialog, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Store all processes for filtering
        all_processes = []
        
        def populate_all_processes():
            """Load all processes into memory for filtering"""
            all_processes.clear()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    # Simple architecture detection
                    arch = "64-bit" if "64" in name.lower() else "32-bit"
                    all_processes.append((pid, name, arch))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        def filter_processes(*args):
            """Filter processes based on search text"""
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            search_text = search_var.get().lower()
            
            # Add matching processes
            for pid, name, arch in all_processes:
                if search_text == "" or search_text in name.lower():
                    tree.insert('', tk.END, values=(pid, name, arch))
        
        # Initial population
        populate_all_processes()
        filter_processes()
        
        # Bind search to real-time filtering
        search_var.trace('w', filter_processes)
        
        # Focus search entry for immediate typing
        search_entry.focus()
        
        # Bind Enter key to attach selected process
        def on_enter_key(event):
            if tree.selection():  # Only attach if something is selected
                attach_selected()
        
        search_entry.bind('<Return>', on_enter_key)
        dialog.bind('<Return>', on_enter_key)
        
        def attach_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a process")
                return
            
            item = tree.item(selection[0])
            pid = int(item['values'][0])
            name = item['values'][1]
            
            self.log_memory_message(f"🔗 Attaching to {name} (PID: {pid})")
            
            if self.attach_to_process(pid):
                self.log_memory_message(f"✅ Successfully attached to {name}")
                dialog.destroy()
            else:
                self.log_memory_message(f"❌ Failed to attach to {name}")
        
        def refresh_processes():
            """Refresh the process list and apply current filter"""
            populate_all_processes()
            filter_processes()
            self.log_memory_message(f"🔄 Process list refreshed ({len(all_processes)} processes found)")
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Attach", command=attach_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=refresh_processes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Enable double-click to attach
        def on_double_click(event):
            attach_selected()
        
        tree.bind("<Double-1>", on_double_click)
    
    def launch_test_process(self):
        """Launch a test process for memory debugging"""
        try:
            test_script = '''import time
import os

# Create predictable memory pattern
test_data = bytearray(256)
for i in range(256):
    test_data[i] = i % 256

# Add recognizable text
test_message = b"HEXEDITOR_TEST_PATTERN"
for i, byte_val in enumerate(test_message):
    if i < 200:
        test_data[50 + i] = byte_val

counter = 0
print(f"Test process started (PID: {os.getpid()})")
print("Memory pattern created. Modifying offset 20 (0x14) every 3 seconds...")

while True:
    time.sleep(3)
    counter += 1
    
    # Modify byte at offset 20 (0x14)
    test_data[20] = (test_data[20] + 1) % 256
    print(f"Modified offset 20: {test_data[20]:02X}")
    
    if counter > 30:
        break
'''
            
            with open('test_memory_process.py', 'w') as f:
                f.write(test_script)
            
            test_process = subprocess.Popen([
                sys.executable, 'test_memory_process.py'
            ], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            self.log_memory_message(f"🚀 Test process launched (PID: {test_process.pid})")
            self.log_memory_message("💡 Now use 'Attach Process' to connect to this test process")
            
        except Exception as e:
            self.log_memory_message(f"❌ Failed to launch test process: {e}")
    
    def attach_to_process(self, pid):
        """Attach to a process for memory debugging"""
        try:
            # Get process object
            self.target_process = psutil.Process(pid)
            
            # Get process handle with required permissions
            PROCESS_VM_READ = 0x0010
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_OPERATION = 0x0008
            PROCESS_ALL_ACCESS = 0x1F0FFF
            
            permission_levels = [
                PROCESS_ALL_ACCESS,
                PROCESS_VM_READ | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION,
                PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                PROCESS_QUERY_INFORMATION
            ]
            
            self.process_handle = None
            for perms in permission_levels:
                handle = ctypes.windll.kernel32.OpenProcess(perms, False, pid)
                if handle:
                    self.process_handle = handle
                    self.log_memory_message(f"✅ Process handle acquired with permissions: 0x{perms:X}")
                    break
            
            if not self.process_handle:
                raise Exception("Could not open process handle")
            
            # Get initial memory snapshot
            self.get_initial_memory()
            return True
            
        except Exception as e:
            self.log_memory_message(f"❌ Failed to attach to process: {e}")
            return False
    
    def get_initial_memory(self):
        """Get initial memory snapshot"""
        try:
            self.log_memory_message("🔍 Enumerating process memory regions...")
            
            readable_regions = self.enumerate_readable_memory()
            
            if readable_regions:
                best_region = readable_regions[0]  # Use first readable region
                self.process_base_address = best_region[0]
                self.log_memory_message(f"✅ Selected memory region: 0x{self.process_base_address:016X}")
            else:
                # Fallback
                self.process_base_address = 0x140000000
                self.log_memory_message(f"⚠️ Using fallback address: 0x{self.process_base_address:016X}")
            
            # Read initial snapshot
            self.process_memory_snapshot = self.read_process_memory(1024)
            if self.process_memory_snapshot:
                self.display_memory_hex()
                self.log_memory_message(f"✅ Memory snapshot loaded ({len(self.process_memory_snapshot)} bytes)")
            else:
                self.log_memory_message("⚠️ Could not read process memory")
                
        except Exception as e:
            self.log_memory_message(f"❌ Failed to get initial memory: {e}")
    
    def enumerate_readable_memory(self):
        """Enumerate readable memory regions"""
        if not self.process_handle:
            return []
        
        readable_regions = []
        
        try:
            # Try psutil memory maps first
            memory_maps = self.target_process.memory_maps(grouped=False)
            
            for mmap in memory_maps[:10]:  # Limit to first 10
                if hasattr(mmap, 'addr') and '-' in mmap.addr:
                    try:
                        start_addr = int(mmap.addr.split('-')[0], 16)
                        end_addr = int(mmap.addr.split('-')[1], 16)
                        size = end_addr - start_addr
                        perms = getattr(mmap, 'perms', '')
                        
                        if 'r' in perms and 1024 <= size <= 1024*1024:
                            readable_regions.append((start_addr, size, 0x04, MEM_COMMIT, MEM_PRIVATE))
                            self.log_memory_message(f"📍 Found region: 0x{start_addr:X} ({size} bytes) {perms}")
                    except:
                        continue
        except Exception as e:
            self.log_memory_message(f"⚠️ Memory enumeration failed: {e}")
        
        return readable_regions
    
    def read_process_memory(self, size):
        """Read memory from process"""
        if not self.process_handle:
            return bytearray()
        
        actual_size = min(size, 1024)
        
        try:
            buffer = (ctypes.c_byte * actual_size)()
            bytes_read = wintypes.DWORD()
            
            result = ctypes.windll.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(self.process_base_address),
                buffer,
                actual_size,
                ctypes.byref(bytes_read)
            )
            
            if result and bytes_read.value > 0:
                # Convert buffer safely
                raw_bytes = []
                for i in range(bytes_read.value):
                    byte_val = buffer[i] & 0xFF
                    raw_bytes.append(byte_val)
                
                result_data = bytearray(raw_bytes)
                if len(result_data) < size:
                    result_data.extend(bytearray(size - len(result_data)))
                return result_data
            
        except Exception as e:
            self.log_memory_message(f"❌ Memory read error: {e}")
        
        return bytearray()
    
    def start_memory_monitoring(self):
        """Start real-time memory monitoring"""
        if self.monitoring_active:
            return
        
        if not self.target_process:
            messagebox.showwarning("Warning", "No process attached")
            return
        
        self.log_memory_message(f"▶️ Starting monitoring with breakpoints: {[hex(bp) for bp in self.breakpoints]}")
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active and self.running:
            try:
                if not self.target_process.is_running():
                    self.root.after(0, self.process_ended)
                    break
                
                # Read current memory
                current_memory = self.read_process_memory(len(self.process_memory_snapshot))
                
                if current_memory and len(current_memory) == len(self.process_memory_snapshot):
                    changes = []
                    
                    # Compare with previous snapshot
                    for i in range(len(current_memory)):
                        if current_memory[i] != self.process_memory_snapshot[i]:
                            changes.append({
                                'offset': i,
                                'address': self.process_base_address + i,
                                'old_value': self.process_memory_snapshot[i],
                                'new_value': current_memory[i]
                            })
                    
                    if changes:
                        # Update snapshot
                        self.process_memory_snapshot = current_memory
                        
                        # Handle changes on UI thread
                        self.root.after(0, lambda: self.handle_memory_changes(changes))
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.root.after(0, lambda: self.log_memory_message(f"❌ Monitor error: {e}"))
                break
    
    def handle_memory_changes(self, changes):
        """Handle detected memory changes"""
        for change in changes:
            # Log the change
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.log_memory_message(f"{timestamp} | +{change['offset']:04X} | {change['old_value']:02X}→{change['new_value']:02X}")
            
            # Check for breakpoints
            if change['offset'] in self.breakpoints:
                current_time = time.time()
                if current_time - self.last_breakpoint_time >= self.breakpoint_cooldown:
                    self.trigger_breakpoint(change)
                    self.last_breakpoint_time = current_time
        
        # Update display
        self.display_memory_hex()
    
    def trigger_breakpoint(self, change):
        """Trigger breakpoint notification"""
        self.log_memory_message("=" * 50)
        self.log_memory_message(f"🛑 BREAKPOINT HIT!")
        self.log_memory_message(f"   Offset: +0x{change['offset']:04X}")
        self.log_memory_message(f"   Address: 0x{change['address']:08X}")
        self.log_memory_message(f"   Value: 0x{change['old_value']:02X} → 0x{change['new_value']:02X}")
        self.log_memory_message("=" * 50)
        
        # Show dialog for important breakpoints
        messagebox.showinfo("🛑 Breakpoint Hit!", 
            f"Memory changed at offset 0x{change['offset']:04X}\n"
            f"Address: 0x{change['address']:08X}\n"
            f"Old: 0x{change['old_value']:02X} → New: 0x{change['new_value']:02X}")
    
    def stop_memory_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        self.log_memory_message("⏹️ Memory monitoring stopped")
    
    def add_breakpoint(self):
        """Add breakpoint at specified offset"""
        try:
            offset_str = self.bp_entry.get().strip()
            if not offset_str:
                return
            
            offset = int(offset_str, 16)
            self.breakpoints.add(offset)
            self.bp_entry.delete(0, tk.END)
            self.log_memory_message(f"🔴 Breakpoint added at offset 0x{offset:04X}")
            
            # Update display
            if self.process_memory_snapshot:
                self.display_memory_hex()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid hex value")
    
    def clear_breakpoints(self):
        """Clear all breakpoints"""
        self.breakpoints.clear()
        self.log_memory_message("🗑️ All breakpoints cleared")
        if self.process_memory_snapshot:
            self.display_memory_hex()
    
    def process_ended(self):
        """Handle when target process ends"""
        self.monitoring_active = False
        self.log_memory_message("⚠️ Target process ended")
    
    def log_memory_message(self, message):
        """Log message to memory console"""
        self.memory_log_text.insert(tk.END, message + "\n")
        self.memory_log_text.see(tk.END)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
    
    def exit_app(self):
        """Exit application"""
        self.running = False
        if self.monitoring_active:
            self.monitoring_active = False
        self.root.quit()


def main():
    root = tk.Tk()
    app = HexEditorWithMemoryMonitoring(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()


if __name__ == "__main__":
    main()