# Hex Editor with Memory Debugging

A powerful hex editor with real-time process memory monitoring and debugging capabilities for Windows.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Features

### 📄 Hex File Editor
- **Open & Edit Binary Files**: View and modify any binary file in hexadecimal format
- **Dual View**: Simultaneous hex and ASCII representation
- **Address Display**: Memory addresses with proper formatting
- **Save Functionality**: Save modifications back to file

### 🔍 Real-time Memory Monitoring
- **Process Attachment**: Attach to any running Windows process
- **Live Memory Reading**: Real-time monitoring of process memory changes
- **Smart Process Selection**: Advanced filtering to quickly find processes
- **Memory Enumeration**: Automatic detection of readable memory regions

### 🎯 Advanced Debugging
- **Breakpoints**: Set breakpoints on specific memory offsets
- **Change Detection**: Automatic detection of memory modifications
- **Visual Highlighting**: Breakpoints highlighted in red in memory view
- **Detailed Logging**: Timestamped log of all memory changes
- **Rate Limiting**: Intelligent cooldown to prevent notification spam

## 🖥️ Screenshots

### Main Interface
The application features a dual-pane interface:
- **Left Panel**: Traditional hex file editor
- **Right Panel**: Real-time memory monitor with process controls

### Process Selection with Smart Filtering
- Type to instantly filter processes (e.g., "note" shows notepad)
- Multiple attachment methods: click + attach, double-click, or press Enter
- Real-time process list with PID, name, and architecture

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8 or higher
- Administrator privileges (recommended for memory access)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/micaelATwh3e/hex-editor-with-memory-debug.git
   cd hex-editor-with-memory-debug
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install psutil
   ```

4. **Run the application**
   ```bash
   python hex_editor_with_memory.py
   ```

### First Time Usage

1. **File Editing**: Click "Open File" in the left panel to load a binary file
2. **Memory Monitoring**: 
   - Click "Attach Process" in the right panel
   - Filter processes by typing (e.g., "calc" for calculator)
   - Select a process and click "Attach" or double-click
   - Click "Start Monitor" to begin real-time monitoring

## 📋 Dependencies

- **psutil** - Process and system information
- **tkinter** - GUI framework (included with Python)
- **ctypes** - Windows API access (included with Python)

## 🎯 Usage Examples

### Memory Debugging Workflow

1. **Launch Target Application**
   ```
   Start the application you want to debug (e.g., notepad.exe)
   ```

2. **Attach to Process**
   - Click "Attach Process"
   - Type "note" to filter for notepad
   - Double-click notepad.exe or select and click "Attach"

3. **Set Breakpoints**
   - Enter hex offset in breakpoint field (e.g., "14")
   - Click "Add BP" to set breakpoint
   - Breakpoints appear highlighted in red in memory view

4. **Monitor Memory**
   - Click "Start Monitor" to begin real-time monitoring
   - Memory changes are logged with timestamps
   - Breakpoints trigger notifications when hit

### Common Use Cases

- **Reverse Engineering**: Monitor how applications handle data
- **Game Modding**: Track memory addresses for game values
- **Malware Analysis**: Observe suspicious process behavior
- **Educational**: Learn about process memory layout
- **Debugging**: Track memory corruption or unexpected changes

## 🛠️ Advanced Features

### Memory Region Detection
The application automatically:
- Enumerates process memory regions using Windows VirtualQueryEx API
- Finds readable/writable memory sections
- Handles both 32-bit and 64-bit processes
- Provides fallback methods for restricted processes

### Smart Breakpoint System
- **Rate Limited**: Prevents notification spam with configurable cooldown
- **Visual Feedback**: Breakpoints highlighted in memory view
- **Detailed Info**: Shows address, old/new values, and ASCII representation
- **Flexible Offsets**: Set breakpoints at any hex offset

### Process Filtering
- **Real-time Search**: Instant filtering as you type
- **Smart Matching**: Partial name matching (case-insensitive)
- **Keyboard Shortcuts**: Enter key to attach, arrow keys to navigate
- **Process Information**: PID, name, and architecture detection

## ⚠️ Important Notes

### Windows Permissions
- **Administrator Rights**: Recommended for best memory access
- **Process Protection**: Some system processes may be inaccessible
- **Antivirus Software**: May flag memory access as suspicious behavior

### Memory Access Limitations
- **Protected Processes**: System-critical processes may deny access
- **DEP/ASLR**: Modern protection mechanisms may limit functionality
- **Architecture**: 32-bit vs 64-bit process differences handled automatically

### Performance Considerations
- **Memory Size**: Large memory regions may slow down monitoring
- **Update Frequency**: 100ms monitoring interval balances performance/responsiveness
- **Breakpoint Limit**: No hard limit but many breakpoints may impact performance

## 🐛 Troubleshooting

### Common Issues

**"Could not open process handle"**
- Run as Administrator
- Target process may be protected
- Try a different process (user processes work better than system processes)

**"Memory enumeration failed"**
- Process may have terminated
- Insufficient permissions
- Try refreshing the process list

**"No memory changes detected"**
- Process may be idle
- Memory region may be read-only
- Try setting breakpoints at different offsets

### Debug Tips
- Check the debug log for detailed error messages
- Use "Refresh" button to update process list
- Try attaching to simpler processes first (notepad, calculator)
- Ensure the process is actively using memory

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python's tkinter for cross-platform GUI
- Uses psutil for robust process management
- Windows API integration via ctypes for memory access
- Inspired by classic hex editors and debugging tools

## 📧 Contact

If you have questions or suggestions, please open an issue on GitHub.

---

**⚠️ Legal Notice**: This tool is intended for educational and legitimate debugging purposes only. Users are responsible for ensuring compliance with applicable laws and software licenses when analyzing processes.