"""
Test script to verify logo resizing functionality in PhaseDRX.

This test verifies that:
1. The logo appears when no items are in the lists
2. The logo repositions correctly when the window is resized
3. The logo remains centered in both X and Y axes
"""

import sys
import os
from PySide6.QtWidgets import QApplication

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matfinder.tools.xrd.xrd import PhaseDRXWindow

def test_logo_resize():
    """Test the logo resize functionality."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create PhaseDRX window
    window = PhaseDRXWindow()
    window.show()
    
    print("✓ PhaseDRX window opened")
    print("✓ Logo should be visible (no items in lists)")
    print("\nTest Instructions:")
    print("1. Verify the logo is centered on the empty plot")
    print("2. Resize the window (drag corners/edges)")
    print("3. Verify the logo stays centered as you resize")
    print("4. The logo should reposition smoothly during resize")
    print("\nClose the window when done testing.")
    
    app.exec()

if __name__ == "__main__":
    test_logo_resize()

