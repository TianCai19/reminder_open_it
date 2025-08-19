# NotionReminder - Timed URL Opener

NotionReminder is a Python GUI application that opens URLs at progressive intervals (immediate → 5 minutes → 10 minutes → 15 minutes repeating) until a total time duration is reached. The application is built with tkinter and packaged using PyInstaller for cross-platform distribution.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- Install Python dependencies: `pip install -r requirements.txt`
- Install tkinter for Linux: `sudo apt-get update && sudo apt-get install -y python3-tk`
- Test basic functionality: `python3 notion_reminder_gui.py` (requires display)

### Build Process
- **Linux build**: `pyinstaller --onefile --windowed --name NotionReminder notion_reminder_gui.py`
  - Build time: ~10-15 seconds. NEVER CANCEL. Set timeout to 60+ seconds minimum.
  - Output: `dist/NotionReminder` (executable)
- **macOS build**: `pyinstaller NotionReminder.spec`
  - Build time: ~10-15 seconds. NEVER CANCEL. Set timeout to 60+ seconds minimum.
  - Output: `dist/NotionReminder.app` (app bundle)
- **Windows build**: `pyinstaller --onefile --windowed --name NotionReminder --icon=assets/icon.icns notion_reminder_gui.py`
  - Build time: ~15-30 seconds. NEVER CANCEL. Set timeout to 90+ seconds minimum.
  - Output: `dist/NotionReminder.exe`

### Testing and Validation
- **CRITICAL**: Always run manual validation scenarios after making changes.
- **Quick validation**: `python3 validate.py` (runs basic functionality tests)
- Run the application with a virtual display for automated testing: `export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 &`
- Basic functionality test: Create test URLs, set short intervals (1-2 minutes), verify immediate opening and timing sequence.
- **NEVER skip manual testing** - the application's core functionality is timing-based and requires real scenario validation.

### CI/CD Pipeline
- Automated builds: GitHub Actions triggers on git tag pushes (`git tag v1.0.0 && git push origin v1.0.0`)
- Build time: 10-15 minutes for all platforms in parallel. NEVER CANCEL CI builds.
- Manual trigger: GitHub Actions → "Build and Release" workflow → "Run workflow"

## Key Application Behavior

### Timing Sequence
1. **Immediate**: Opens URL immediately when "Start" is clicked
2. **First interval**: Waits 5 minutes (configurable), then opens URL
3. **Second interval**: Waits 10 minutes (configurable), then opens URL  
4. **Subsequent intervals**: Waits 15 minutes (configurable) repeatedly until total time reached

### Input Validation
- URL must start with `http://` or `https://`
- All time values must be positive integers
- Chrome path is optional (uses system default browser if empty)

### Configuration Options
- Target URL (default: Notion page)
- Total duration in minutes (default: 60)
- First interval in minutes (default: 5)
- Second interval in minutes (default: 10)
- Subsequent interval in minutes (default: 15)
- Optional Chrome browser path

## Validation Scenarios

### Essential Manual Test Scenario
After making any changes, **ALWAYS** run this complete validation:

1. **Start the application**: `python3 notion_reminder_gui.py`
2. **Configure test values**:
   - URL: Use a harmless test URL (e.g., `https://example.com`)
   - Total time: 6 minutes
   - Intervals: 1, 2, 1 minutes
3. **Test the full sequence**:
   - Click "Start" → URL should open immediately
   - Wait 1 minute → URL should open again (2nd time)
   - Wait 2 minutes → URL should open again (3rd time)
   - Wait 1 minute → URL should open again (4th time)
   - Application should stop automatically when total time (6 minutes) is reached
4. **Test stop functionality**: Start again and click "Stop" mid-sequence
5. **Test validation**: Try invalid URLs and negative time values

### Build Validation
- Build the application: `pyinstaller --onefile --windowed --name NotionReminder notion_reminder_gui.py`
- Test the executable: `export DISPLAY=:99 && timeout 10s ./dist/NotionReminder` (should start without errors)
- **Do not run builds in production environments** - they may fail due to missing GUI libraries

### Error Cases to Test
- Invalid URL format (missing http/https)
- Negative or zero time values
- Invalid Chrome browser path
- Network connectivity issues (should gracefully handle browser failures)

## Important File Locations

### Core Application
- `notion_reminder_gui.py` - Main application file (246 lines)
- `requirements.txt` - Python dependencies (primarily PyInstaller)
- `NotionReminder.spec` - PyInstaller configuration for macOS builds
- `validate.py` - Quick validation script for testing core functionality

### Build and CI
- `.github/workflows/build-and-release.yml` - Multi-platform build pipeline
- `BUILD_INSTRUCTIONS.md` - Manual build and release instructions
- `assets/icon.icns` - Application icon for macOS

### Configuration
- `.gitignore` - Excludes build artifacts (`dist/`, `build/`, `__pycache__/`)

## Common Development Tasks

### Making Code Changes
1. Edit `notion_reminder_gui.py` 
2. **Quick test**: `python3 validate.py` (basic functionality validation)
3. Test manually: `python3 notion_reminder_gui.py`
4. Run complete validation scenario (see above)
5. Build and test executable
6. **Always verify timing behavior** if touching timing-related code

### Adding New Features
- The application uses tkinter's `after()` method for timing - be careful with timer management
- URL opening uses Python's `webbrowser` module - test with and without custom Chrome paths
- State management is critical - test start/stop transitions thoroughly

### Debugging Build Issues
- Linux: Ensure `python3-tk` is installed
- macOS: Icon file must be `.icns` format in `assets/` directory
- Windows: May need additional DLL handling for tkinter
- **All builds require GUI libraries** - will fail in headless environments

### Release Process
1. Test thoroughly on target platform
2. Update version in release notes (BUILD_INSTRUCTIONS.md)
3. Create and push git tag: `git tag v1.2.3 && git push origin v1.2.3`
4. Monitor GitHub Actions build (10-15 minutes total)
5. Verify release artifacts are created correctly

## Timing and Performance

### Build Times (Set Appropriate Timeouts)
- **Local builds**: 10-30 seconds depending on platform - NEVER CANCEL, set 90+ second timeouts
- **CI builds**: 10-15 minutes for all platforms in parallel - NEVER CANCEL, set 30+ minute timeouts
- **First-time builds**: May take longer due to dependency downloads

### Application Performance
- Memory usage: ~10-50MB (varies by platform due to tkinter bundling)
- Timing accuracy: ±1 second (uses 1-second tick interval)
- GUI responsiveness: Should remain responsive during countdown

## Troubleshooting

### Common Issues
- **"tkinter not available"**: Run `sudo apt-get install python3-tk` on Linux
- **"Cannot connect to display"**: Set up virtual display `export DISPLAY=:99 && Xvfb :99 &`
- **Build fails with library errors**: Ensure all GUI dependencies are installed
- **Executable crashes on startup**: Library path issues - rebuild or check PyInstaller logs

### Testing Without GUI
- Use virtual display (Xvfb) for automated testing
- Mock `webbrowser.open()` calls in unit tests
- Test timing logic separately from GUI components

Remember: This application's core value is reliable timing behavior. **Always validate the complete timing sequence manually** when making changes, even if they seem unrelated to timing functionality.