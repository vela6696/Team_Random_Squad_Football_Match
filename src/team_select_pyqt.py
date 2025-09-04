from pathlib import Path
from PyQt5.QtCore import Qt
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
)
import team_select_optimized_lib as lib

CSV_PATH = Path(lib.__file__).with_name(lib.CSV_FILE)

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
        self.team_spin.setValue(lib.TEAM_COUNT if hasattr(lib, "TEAM_COUNT") else 2)
        input_row.addWidget(self.team_spin)

        input_row.addWidget(QLabel("Người/đội:"))
        self.players_spin = QSpinBox()
        self.players_spin.setRange(1, 30)
        self.players_spin.setValue(7)
        input_row.addWidget(self.players_spin)

        input_row.addWidget(QLabel("Tier threshold:"))
        self.tier_spin = QDoubleSpinBox()
        self.tier_spin.setRange(0.0, 10.0)
        self.tier_spin.setSingleStep(0.1)
        self.tier_spin.setValue(lib.TIER_THRESHOLD_LOW)
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
        lib.TIER_THRESHOLD_LOW = self.tier_spin.value()

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

        QMessageBox.information(self, "Kết quả chia đội", result)
