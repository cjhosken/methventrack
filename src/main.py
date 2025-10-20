from PySide6.QtWidgets import QApplication
import sys
from ui.mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())