#!/usr/bin/env python3
"""
Test script to verify the language menu functionality.
Tests settings manager and i18n module.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from matfinder.core.settings_manager import settings_manager
from matfinder.core import i18n


def test_settings_manager():
    """Test the settings manager"""
    print("Testing Settings Manager...")
    
    # Test loading
    current_lang = settings_manager.get_language()
    print(f"  Current language: {current_lang}")
    
    # Test saving different languages
    for lang in ["pt", "en", "de"]:
        result = settings_manager.set_language(lang)
        print(f"  Set language to {lang}: {'✓' if result else '✗'}")
        assert result, f"Failed to set language to {lang}"
        assert settings_manager.get_language() == lang, f"Language not set correctly to {lang}"
    
    # Reset to Portuguese
    settings_manager.set_language("pt")
    print("  Settings Manager: ✓ PASSED")


def test_i18n_module():
    """Test the i18n translation module"""
    print("\nTesting i18n Module...")
    
    # Test language names
    for code, expected_name in [("pt", "Português"), ("en", "English"), ("de", "Deutsch")]:
        name = i18n.get_language_name(code)
        print(f"  Language name for '{code}': {name}")
        assert name == expected_name, f"Expected {expected_name}, got {name}"
    
    # Test translations for each language
    test_keys = [
        "menu_file",
        "menu_config",
        "menu_language",
        "language_portuguese",
        "restart_title"
    ]
    
    for lang in ["pt", "en", "de"]:
        i18n.set_language(lang)
        print(f"\n  Testing translations in {lang.upper()}:")
        for key in test_keys:
            translation = i18n.tr(key)
            print(f"    {key}: '{translation}'")
            assert translation, f"Missing translation for {key} in {lang}"
    
    print("\n  i18n Module: ✓ PASSED")


def test_translation_examples():
    """Show examples of translations"""
    print("\n" + "="*60)
    print("Translation Examples:")
    print("="*60)
    
    for lang_code in ["pt", "en", "de"]:
        i18n.set_language(lang_code)
        print(f"\n{i18n.get_language_name(lang_code)} ({lang_code}):")
        print("-" * 40)
        print(f"  Menu File:     {i18n.tr('menu_file')}")
        print(f"  Menu Settings: {i18n.tr('menu_config')}")
        print(f"  Menu Language: {i18n.tr('menu_language')}")
        print(f"  Restart Title: {i18n.tr('restart_title')}")
        
        # Show restart message
        lang_name = i18n.get_language_name(lang_code)
        restart_msg = i18n.tr('restart_message').format(lang_name)
        print(f"  Restart Msg:   {restart_msg[:60]}...")


def main():
    """Run all tests"""
    print("=" * 60)
    print("MatFinder Language Menu - Unit Tests")
    print("=" * 60)
    print()
    
    try:
        test_settings_manager()
        test_i18n_module()
        test_translation_examples()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
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
