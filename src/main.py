from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import sys
from ui.mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))  # use .ico on Windows, .png works too

    win = MainWindow()
    win.show()
    sys.exit(app.exec())