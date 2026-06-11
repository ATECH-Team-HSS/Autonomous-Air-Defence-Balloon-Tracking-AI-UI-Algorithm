from PyQt5 import QtWidgets, QtCore
from ui.frames.upper_frame import UpperFrame


class LowerFrame(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Frame styling
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        self.setSizePolicy(sizePolicy)
        self.setMaximumSize(QtCore.QSize(2000, 500))

        # Main vertical layout of the lower frame
        self.layout = QtWidgets.QVBoxLayout(self)

        # GroupBox for system log
        self.groupbox = QtWidgets.QGroupBox(self)
        self.groupbox.setSizePolicy(sizePolicy)
        self.groupbox.setTitle("System Log")

        # Vertical horizontal of the GroupBox widget
        self.groupboxLayout = QtWidgets.QHBoxLayout(self.groupbox)

        # TextEdit for system log and AI system log to be written to
        self.system_log = QtWidgets.QTextEdit(self.groupbox)
        self.system_log.setMaximumSize(QtCore.QSize(1000, 300))

        self.AI_system_log = QtWidgets.QTextEdit(self.groupbox)
        self.AI_system_log.setMaximumSize(QtCore.QSize(1000, 300))

        # Adding the TextEdit and groupbox to their specified layout
        self.groupboxLayout.addWidget(self.system_log)
        self.groupboxLayout.addWidget(self.AI_system_log)
        self.layout.addWidget(self.groupbox)

    # ───── Logging Methods ─────
    def log_error(self, message: str):
        self._append_colored_text(message, "red")

    def log_update(self, message: str):
        self._append_colored_text(message, "blue")

    def log_completed(self, message: str):
        self._append_colored_text(message, "green")

    def _append_colored_text(self, message: str, color: str):
        # Format message as colored HTML
        self.system_log.append(f'<span style="color:{color}; font-size:9pt;">{message}</span>')

    def log_ai_system(self, message: str):
        # Append message to AI system log
        self.AI_system_log.append(f'<span style="color:black; font-size:9pt;">{message}</span>')
