from PySide6.QtWidgets import QApplication

def copy_text(text: str):  # call from GUI thread
    QApplication.clipboard().setText(text)
