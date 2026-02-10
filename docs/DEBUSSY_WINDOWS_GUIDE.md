# DEBUSSY v2.2 Windows Installation and Setup Guide

## 📋 About DEBUSSY

DEBUSSY (DEBye USer SYstem) is advanced software for analyzing crystal structures using the Pair Distribution Function (PDF) analysis method. It's a complementary tool to MatFinder for more in-depth crystallographic analyses.

---

## 🖥️ System Requirements

### Minimum Requirements
- **Operating System**: Windows 7/8/10/11 (64-bit recommended)
- **RAM**: 2GB minimum (4GB recommended)
- **Disk Space**: 200MB
- **Processor**: Dual-core 2.0 GHz or higher

### Required Software
- Windows with command-line application support
- File decompression software (WinRAR, 7-Zip, or similar)
- Text editor (Notepad++, Sublime Text, or similar - optional but recommended)

---

## 📥 Step 1: Download DEBUSSY

### Option A: Via GitHub CLI (Recommended)

1. **Install GitHub CLI** (if you don't have it yet):
   - Download from: https://cli.github.com/
   - Run the installer and follow on-screen instructions

2. **Open Command Prompt**:
   - Press `Win + R`
   - Type `cmd` and press Enter

3. **Navigate to your desired folder**:
   ```cmd
   cd C:\Users\YourUsername\Documents
   ```

4. **Clone the repository**:
   ```cmd
   gh repo clone DeByeUSerSYstem/DEBUSSY_v2.2-WINDOWS
   ```

### Option B: Manual Download

1. **Access the repository**:
   - Open your browser and go to: https://github.com/DeByeUSerSYstem/DEBUSSY_v2.2-WINDOWS

2. **Download the code**:
   - Click the green "Code" button
   - Select "Download ZIP"
   - Save the file to an easily accessible folder (e.g., `C:\DEBUSSY`)

3. **Extract the files**:
   - Right-click the downloaded ZIP file
   - Select "Extract all..." or "Extract Here"
   - Wait for extraction to complete

---

## 📂 Step 2: Organize the Files

1. **Locate the extracted folder**:
   - The folder should be named `DEBUSSY_v2.2-WINDOWS` or similar
   - It's recommended to move it to a simple location, such as:
     - `C:\DEBUSSY`
     - `C:\Programs\DEBUSSY`

2. **Verify the contents**:
   - Navigate to the folder
   - You should see executable files (`.exe`), libraries (`.dll`), and possibly an `examples` or `docs` folder

---

## 🚀 Step 3: Run DEBUSSY

### First Execution

1. **Open the DEBUSSY folder**:
   - Navigate to `C:\DEBUSSY` (or wherever you extracted it)

2. **Locate the main executable**:
   - Look for files such as:
     - `DEBUSSY.exe`
     - `debussy.exe`
     - `run_debussy.bat`
     - `start.exe`

3. **Run the program**:
   - Double-click the executable file
   - **If a Windows security warning appears**:
     - Click "More info"
     - Click "Run anyway"
     - (This is common for unsigned software)

### Running via Command Line (Alternative Method)

1. **Open Command Prompt as Administrator**:
   - Press `Win + X`
   - Select "Command Prompt (Admin)" or "Windows PowerShell (Admin)"

2. **Navigate to the DEBUSSY folder**:
   ```cmd
   cd C:\DEBUSSY
   ```

3. **Run the program**:
   ```cmd
   DEBUSSY.exe
   ```
   or
   ```cmd
   .\DEBUSSY.exe
   ```

---

## ⚙️ Step 4: Initial Configuration

### Configure Environment Variables (Optional)

To make DEBUSSY accessible from anywhere:

1. **Open System Settings**:
   - Press `Win + Pause/Break` or
   - Right-click "This PC" → "Properties"

2. **Access Environment Variables**:
   - Click "Advanced system settings"
   - Click "Environment Variables"

3. **Add to PATH**:
   - Under "System variables", find and select "Path"
   - Click "Edit"
   - Click "New"
   - Add the full path: `C:\DEBUSSY`
   - Click "OK" on all windows

4. **Test**:
   - Open a new Command Prompt
   - Type `DEBUSSY` and press Enter
   - The program should start from any folder

### Create Desktop Shortcut

1. **Locate the executable**:
   - Navigate to `C:\DEBUSSY`
   - Find `DEBUSSY.exe`

2. **Create shortcut**:
   - Right-click the executable
   - Select "Send to" → "Desktop (create shortcut)"

3. **Customize the shortcut** (optional):
   - Right-click the shortcut
   - Select "Properties"
   - You can change the icon, name, and startup folder

---

## 📚 Step 5: Using DEBUSSY

### Input Files

DEBUSSY typically works with:
- **CIF files** (Crystallographic Information File)
- **Diffraction data** (.dat, .xy, .txt formats)
- **Configuration files** (DEBUSSY-specific)

### Basic Workflow

1. **Prepare your data**:
   - Have your CIF files or diffraction data ready
   - Organize them in an easily accessible folder

2. **Load data into DEBUSSY**:
   - Use the program interface (if there's a GUI)
   - Or follow command-line instructions as per documentation

3. **Configure analysis**:
   - Set parameters as needed
   - Consult official DEBUSSY documentation

4. **Run analysis**:
   - Start processing
   - Wait for results

5. **View results**:
   - Examine output files
   - Use complementary visualization tools if needed

---

## 🔧 Troubleshooting

### Program won't open

**Problem**: Double-clicking the executable does nothing
- **Solution 1**: Try running as Administrator (right-click → "Run as administrator")
- **Solution 2**: Check if all files were extracted correctly
- **Solution 3**: Check for missing DLL files in the folder

### Missing DLL error

**Problem**: Error message about DLL not found
- **Solution 1**: Install Microsoft Visual C++ Redistributable:
  - Download from: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist
  - Install both x86 and x64 versions
- **Solution 2**: Check if all DLLs are in the DEBUSSY folder

### Antivirus blocks the program

**Problem**: Antivirus detects DEBUSSY as a threat
- **Solution**: Add an exception to your antivirus:
  1. Open antivirus settings
  2. Look for "Exceptions" or "Whitelist"
  3. Add the entire `C:\DEBUSSY` folder

### Command not recognized

**Problem**: When trying to run via CMD, "not recognized as a command" appears
- **Solution**: 
  - Make sure you're in the correct folder: `cd C:\DEBUSSY`
  - Use `.\DEBUSSY.exe` instead of just `DEBUSSY.exe`

---

## 🔗 Integration with MatFinder

DEBUSSY can be used together with MatFinder for more complete analyses:

1. **Use MatFinder** for:
   - Searching crystal structures
   - Downloading CIF files
   - Simulating initial diffraction patterns

2. **Use DEBUSSY** for:
   - Advanced PDF analysis
   - Structure refinement
   - Local disorder modeling

### Integrated Workflow

```
MatFinder → Search material → Download CIF → DEBUSSY → PDF Analysis
    ↑                                                      ↓
    └──────────────── Refine structure ←──────────────────┘
```

---

## 📖 Additional Resources

### Documentation

- **GitHub Repository**: https://github.com/DeByeUSerSYstem/DEBUSSY_v2.2-WINDOWS
- **Issues/Problems**: Open an issue on GitHub if you encounter problems
- **MatFinder**: For complementary analyses, use MatFinder

### Support

- **GitHub Issues**: Report problems in the DEBUSSY repository
- **MatFinder Community**: For integration questions

### Recommended Tutorials

1. Start with examples included in the `examples` folder (if available)
2. Read the official DEBUSSY documentation (README or docs file)
3. Practice with simple structures before complex analyses

---

## ✅ Installation Checklist

- [ ] Windows 7 or higher installed
- [ ] Sufficient disk space (200MB+)
- [ ] DEBUSSY downloaded from GitHub
- [ ] Files extracted to a permanent folder
- [ ] Main executable located
- [ ] Program successfully run for the first time
- [ ] Shortcut created (optional)
- [ ] Environment variables configured (optional)
- [ ] Dependencies installed (Visual C++ Redistributable if needed)
- [ ] Sample files tested (if available)

---

## 💡 Important Tips

1. **Keep the folder organized**: Don't move individual files, keep the entire structure intact
2. **Backup**: Before updates, backup your configurations
3. **Use simple paths**: Avoid spaces and special characters in paths (use `C:\DEBUSSY` instead of `C:\My Programs\DEBUSSY 2.2`)
4. **Consult documentation**: Always refer to the project's README for specific instructions
5. **Update regularly**: Check GitHub for new versions and fixes

---

## 📝 Final Notes

This guide provides a general step-by-step process for running DEBUSSY on Windows. Due to the specific nature of the software, some details may vary depending on the exact version of the program. Always consult the official documentation included in the repository for more specific instructions.

For questions or specific problems:
1. Consult the DEBUSSY GitHub repository
2. Check the Issues section for similar problems
3. Open a new issue with details of your problem

---

**Developed for the MatFinder community**  
*For crystallographic analysis excellence*

---

<div align="center">
  <sub>Guide created: February 2026</sub>
</div>
