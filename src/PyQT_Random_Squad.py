import sys
from pathlib import Path
from typing import List

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import team_utils
import team_select_pyqt

# Path to the CSV file containing player information
CSV_FILE = Path(__file__).with_name("players.csv")


class RandomSquadWindow(QMainWindow):
    """PyQt interface for the Random Squad tool."""

    SKILL_LEVELS = [
        "1 sao",
        "2 sao",
        "3 sao",
        "4 sao",
        "5 sao",
        "6 sao",
        "7 sao",
        "8 sao",
        "9 sao",
        "10 sao",
        "siêu sao",
    ]
    STAMINA_LEVELS = ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]
    DEFAULT_SKILL_INDEX = 1
    DEFAULT_STAMINA_INDEX = 1
    DEFAULT_SKILL_WEIGHT = 50
    MIN_POINT = 1.0
    MAX_POINT = 4.0
    SKILL_MAPPING = {
        "1 sao": 0.0,
        "2 sao": 0.1,
        "3 sao": 0.2,
        "4 sao": 0.3,
        "5 sao": 0.4,
        "6 sao": 0.5,
        "7 sao": 0.6,
        "8 sao": 0.7,
        "9 sao": 0.8,
        "10 sao": 0.9,
        "siêu sao": 1.0,
    }
    STAMINA_MAPPING = {
        "0": 0.0,
        "10": 0.1,
        "20": 0.2,
        "30": 0.3,
        "40": 0.4,
        "50": 0.5,
        "60": 0.6,
        "70": 0.7,
        "80": 0.8,
        "90": 0.9,
        "100": 1.0,
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Random Squad Tool")
        self.setGeometry(100, 100, 400, 620)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # ---- Player selection ----
        layout.addWidget(QLabel("Tên cầu thủ:"))
        self.name_combo = QComboBox()
        layout.addWidget(self.name_combo)

        reload_button = QPushButton("Tải lại")
        reload_button.clicked.connect(self.load_data)
        layout.addWidget(reload_button)

        layout.addWidget(QLabel("Kỹ năng:"))
        self.skill_combo = QComboBox()
        self.skill_combo.addItems(self.SKILL_LEVELS)
        layout.addWidget(self.skill_combo)

        layout.addWidget(QLabel("Thể lực:"))
        self.stamina_combo = QComboBox()
        self.stamina_combo.addItems(self.STAMINA_LEVELS)
        layout.addWidget(self.stamina_combo)

        layout.addWidget(QLabel("Tỉ lệ kỹ năng (%):"))
        self.skill_slider = QSlider(Qt.Horizontal)
        self.skill_slider.setRange(0, 100)
        self.skill_slider.setValue(self.DEFAULT_SKILL_WEIGHT)
        layout.addWidget(self.skill_slider)

        # ---- Action buttons ----
        self.calc_button = QPushButton("Tính điểm")
        self.calc_button.clicked.connect(self.handle_calculate)
        layout.addWidget(self.calc_button)

        self.attendance_button = QPushButton("Điểm danh")
        self.attendance_button.clicked.connect(self.handle_attendance)
        layout.addWidget(self.attendance_button)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        # ---- Add new player section ----
        layout.addWidget(QLabel("Thêm cầu thủ mới"))

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tên:"))
        self.new_name = QLineEdit()
        name_layout.addWidget(self.new_name)
        layout.addLayout(name_layout)

        tier_layout = QHBoxLayout()
        tier_layout.addWidget(QLabel("Tier:"))
        self.new_tier = QLineEdit()
        tier_layout.addWidget(self.new_tier)
        layout.addLayout(tier_layout)

        layout.addWidget(QLabel("Vị trí (chọn nhiều):"))
        self.pos_list = QListWidget()
        self.pos_list.setSelectionMode(QListWidget.MultiSelection)
        for pos in ["GK", "MF"]:
            QListWidgetItem(pos, self.pos_list)
        layout.addWidget(self.pos_list)

        self.add_button = QPushButton("Thêm cầu thủ")
        self.add_button.clicked.connect(self.handle_add)
        layout.addWidget(self.add_button)

        self.load_data()
        self.name_combo.currentIndexChanged.connect(self.update_player_fields)

    # ---- Data handling ----
    def load_data(self) -> None:
        """Load player data from the CSV file."""
        try:
            self.df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=["name", "tier", "position", "stamina", "skill"])

        self.name_combo.clear()
        if "name" in self.df:
            self.name_combo.addItems(self.df["name"].tolist())
            if not self.df.empty:
                self.name_combo.setCurrentIndex(0)
                self.update_player_fields()

    def update_player_fields(self) -> None:
        """Update skill and stamina fields based on selected player."""
        name = self.name_combo.currentText()
        if "name" not in self.df or name not in self.df["name"].values:
            return

        player_row = self.df[self.df["name"] == name]
        if player_row.empty:
            return
        skill = player_row.iloc[0].get("skill", self.SKILL_LEVELS[self.DEFAULT_SKILL_INDEX])
        stamina = player_row.iloc[0].get("stamina", self.STAMINA_LEVELS[self.DEFAULT_STAMINA_INDEX])

        self.skill_combo.setCurrentText(skill if skill in self.SKILL_LEVELS else self.SKILL_LEVELS[self.DEFAULT_SKILL_INDEX])

        try:
            stamina_val = float(stamina)
            stamina_str = str(int(stamina_val)) if stamina_val.is_integer() else str(stamina_val)
        except (ValueError, TypeError):
            stamina_str = self.STAMINA_LEVELS[self.DEFAULT_STAMINA_INDEX]
        self.stamina_combo.setCurrentText(
            stamina_str if stamina_str in self.STAMINA_LEVELS else self.STAMINA_LEVELS[self.DEFAULT_STAMINA_INDEX]
        )

    # ---- Core logic ----
    def calculate_score(self, skill: str, stamina: str, skill_weight: float, stamina_weight: float) -> float:
        skill_score = self.SKILL_MAPPING.get(skill, 0.0)
        stamina_score = self.STAMINA_MAPPING.get(stamina, 0.0)
        normalized = skill_weight * skill_score + stamina_weight * stamina_score
        final_score = self.MIN_POINT + normalized * self.MAX_POINT
        return round(final_score, 1)

    def handle_calculate(self) -> None:
        name = self.name_combo.currentText()
        skill = self.skill_combo.currentText()
        stamina = self.stamina_combo.currentText()
        skill_weight = self.skill_slider.value() / 100
        stamina_weight = 1.0 - skill_weight

        score = self.calculate_score(skill, stamina, skill_weight, stamina_weight)

        self.df["skill"] = self.df["skill"].astype("object")
        self.df["stamina"] = self.df["stamina"].astype("object")

        if "name" in self.df and name in self.df["name"].values:
            self.df.loc[self.df["name"] == name, "tier"] = score
            self.df.loc[self.df["name"] == name, "skill"] = skill
            self.df.loc[self.df["name"] == name, "stamina"] = stamina
            self.df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

        self.result_label.setText(f"{name} (Tier: {score})")

    def handle_attendance(self) -> None:
        dlg = team_select_pyqt.TeamSelectionWindow(self)
        dlg.exec_()

    def get_selected_positions(self) -> List[str]:
        return [item.text() for item in self.pos_list.selectedItems()]

    def handle_add(self) -> None:
        name = self.new_name.text().strip()
        try:
            tier = float(self.new_tier.text().strip())
        except ValueError:
            self.result_label.setText("Lỗi: Tier phải là số!")
            return

        positions = self.get_selected_positions()
        if not name or not positions:
            self.result_label.setText("Tên và vị trí không được để trống.")
            return

        if "name" in self.df and name in self.df["name"].values:
            self.result_label.setText(f"{name} đã tồn tại!")
            return

        team_utils.add_new_player_to_csv(name, tier, positions, filename=str(CSV_FILE))
        self.result_label.setText(f"Đã thêm {name} ({tier})")
        self.load_data()


def main() -> None:
    app = QApplication(sys.argv)
    win = RandomSquadWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
