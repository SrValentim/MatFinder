#!/usr/bin/env python3
"""
Simple test to verify the language menu appears in the UI.
This will launch the app briefly to verify the menu structure.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from matfinder.core.settings_manager import settings_manager
from matfinder.core import i18n


def test_menu_structure():
    """Test that the menu structure is correct"""
    print("Testing menu structure...")
    
    # Initialize language
    current_language = settings_manager.get_language()
    i18n.set_language(current_language)
    print(f"  Current language: {current_language}")
    
    # Create app
    app = QApplication(sys.argv)
    
    # Import MaterialsApp
    from matfinder.app_main import MaterialsApp
    
    # Create main window
    main_window = MaterialsApp()
    
    # Get the menubar
    menubar = main_window.menuBar()
    
    # Check menus exist
    menus = {}
    for action in menubar.actions():
        menu = action.menu()
        if menu:
            menus[menu.title()] = menu
    
    print(f"\n  Found {len(menus)} menus:")
    for menu_title in menus.keys():
        print(f"    - {menu_title}")
    
    # Check if Configuration menu exists
    config_menu = None
    for title, menu in menus.items():
        if "Configuração" in title or "Settings" in title or "Einstellungen" in title:
            config_menu = menu
            break
    
    assert config_menu is not None, "Configuration menu not found!"
    print(f"\n  ✓ Configuration menu found: {config_menu.title()}")
    
    # Check if Language submenu exists
    language_menu_found = False
    for action in config_menu.actions():
        if action.menu():
            submenu = action.menu()
            if "Idioma" in submenu.title() or "Language" in submenu.title() or "Sprache" in submenu.title():
                language_menu_found = True
                print(f"  ✓ Language submenu found: {submenu.title()}")
                
                # Check language options
                lang_actions = [a for a in submenu.actions() if not a.isSeparator()]
                print(f"  ✓ Found {len(lang_actions)} language options:")
                for lang_action in lang_actions:
                    checked = "✓" if lang_action.isChecked() else " "
                    print(f"    [{checked}] {lang_action.text()}")
                
                assert len(lang_actions) == 3, f"Expected 3 language options, found {len(lang_actions)}"
                break
    
    assert language_menu_found, "Language submenu not found!"
    
    # Close the app without showing
    app.quit()
    
    print("\n  ✓ Menu structure test PASSED!")
    return True


def main():
    """Run the test"""
    print("=" * 60)
    print("MatFinder Language Menu - UI Structure Test")
    print("=" * 60)
    print()
    
    try:
        test_menu_structure()
        
        print("\n" + "=" * 60)
        print("✓ UI STRUCTURE TEST PASSED!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
