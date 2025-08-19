#!/usr/bin/env python3
"""
Quick validation script for NotionReminder functionality.
Run this after making changes to verify core functionality.
"""

import os
import sys
import tkinter as tk
from unittest.mock import patch, MagicMock

# Ensure we can import the main application
try:
    import notion_reminder_gui
except ImportError:
    print("✗ Cannot import notion_reminder_gui.py - ensure you're in the correct directory")
    sys.exit(1)

def validate_basic_functionality():
    """Run basic functionality validation."""
    print("🔍 Running basic functionality validation...")
    
    # Ensure we have a display
    if not os.environ.get('DISPLAY'):
        print("⚠️  No DISPLAY environment variable set. If running on Linux, run:")
        print("   export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 &")
        print("   (Or use any available display)")
    
    # Mock webbrowser to avoid opening real URLs
    with patch('notion_reminder_gui.webbrowser') as mock_browser:
        mock_browser.open = MagicMock()
        
        try:
            root = tk.Tk()
            app = notion_reminder_gui.ReminderApp(root)
            
            # Test 1: Default values
            assert app.url_var.get() == notion_reminder_gui.DEFAULTS["url"]
            print("✓ Default values loaded correctly")
            
            # Test 2: Start functionality
            app.start()
            assert app.running == True
            assert app.count == 1  # Should open immediately
            print("✓ Start functionality works")
            
            # Test 3: URL opening
            mock_browser.open.assert_called_with(notion_reminder_gui.DEFAULTS["url"])
            print("✓ URL opening functionality works")
            
            # Test 4: Stop functionality
            app.stop()
            assert app.running == False
            print("✓ Stop functionality works")
            
            # Test 5: Input validation
            app.url_var.set("invalid-url")
            with patch('notion_reminder_gui.messagebox.showerror') as mock_error:
                app.start()
                mock_error.assert_called()
                assert app.running == False
            print("✓ Input validation works")
            
            root.destroy()
            print("✅ All basic functionality tests passed!")
            return True
            
        except Exception as e:
            print(f"✗ Validation failed: {e}")
            return False

def main():
    print("NotionReminder Validation Script")
    print("=" * 40)
    
    success = validate_basic_functionality()
    
    if success:
        print("\n🎉 Validation completed successfully!")
        print("\nNext steps:")
        print("1. Test the build process: pyinstaller --onefile --windowed --name NotionReminder notion_reminder_gui.py")
        print("2. Run manual validation with short intervals to test timing")
        print("3. Test with real URLs to ensure browser integration works")
    else:
        print("\n💥 Validation failed! Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())