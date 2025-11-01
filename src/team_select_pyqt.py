from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QTextEdit,
)
import team_utils as lib

CSV_PATH = lib.CSV_PATH

class TeamSelectionWindow(QDialog):
    """PyQt window for selecting players and forming balanced teams."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chia đội")
        layout = QVBoxLayout(self)

        # Input controls
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Số đội:"))
        self.team_spin = QSpinBox()
        self.team_spin.setRange(2, 10)
        self.team_spin.setValue(lib.TEAM_COUNT)
        input_row.addWidget(self.team_spin)

        input_row.addWidget(QLabel("Người/đội:"))
        self.players_spin = QSpinBox()
        self.players_spin.setRange(1, 30)
        self.players_spin.setValue(7)
        input_row.addWidget(self.players_spin)

        input_row.addWidget(QLabel("Điểm ngưỡng tạ:"))
        self.tier_spin = QDoubleSpinBox()
        self.tier_spin.setRange(0.0, 10.0)
        self.tier_spin.setSingleStep(0.1)
        self.tier_spin.setValue(lib.get_tier_threshold())
        input_row.addWidget(self.tier_spin)

        layout.addLayout(input_row)

        # Player checklist
        self.player_list = QListWidget()
        players = lib.read_players_from_csv(str(CSV_PATH))
        for p in players:
            item = QListWidgetItem(f"{p[lib.NAME_KEY]} (Tier: {p[lib.TIER_KEY]})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, p)
            self.player_list.addItem(item)
        layout.addWidget(self.player_list)

        self.shuffle_button = QPushButton("Chia đội!!!")
        self.shuffle_button.clicked.connect(self.handle_shuffle)
        layout.addWidget(self.shuffle_button)

    def handle_shuffle(self):
        team_count = self.team_spin.value()
        players_per_team = self.players_spin.value()
        lib.set_tier_threshold(self.tier_spin.value())

        selected_players = [
            self.player_list.item(i).data(Qt.UserRole)
            for i in range(self.player_list.count())
            if self.player_list.item(i).checkState() == Qt.Checked
        ]

        if len(selected_players) < team_count * players_per_team:
            QMessageBox.warning(
                self,
                "Lỗi",
                f"Cần ít nhất {team_count * players_per_team} người để chia {team_count} đội.",
            )
            return

        try:
            result = lib.run_team_assignment(
                filename=str(CSV_PATH),
                selected_players=selected_players,
                team_count=team_count,
            )
        except ValueError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
            return

        self.show_result_dialog(result)

    def show_result_dialog(self, text: str) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Kết quả chia đội")
        layout = QVBoxLayout(dlg)

        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(text)
        layout.addWidget(text_box)

        button_row = QHBoxLayout()

        copy_btn = QPushButton("Copy")

        def copy_to_clipboard():
            QGuiApplication.clipboard().setText(text)

        copy_btn.clicked.connect(copy_to_clipboard)
        button_row.addWidget(copy_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dlg.accept)
        button_row.addWidget(ok_btn)

        layout.addLayout(button_row)

        dlg.exec_()
