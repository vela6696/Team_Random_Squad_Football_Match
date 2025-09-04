import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSlider,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
)
from PyQt5.QtCore import Qt


class RandomSquadWindow(QMainWindow):
    """PyQt replacement GUI for the Random Squad tool.

    This interface mirrors the original tkinter-based application but
    does not perform any real data processing. Widgets are wired to
    dummy handlers which can later be replaced by API calls.
    """

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
        self.name_combo.addItems(["Player 1", "Player 2", "Player 3"])  # placeholder data
        layout.addWidget(self.name_combo)

        layout.addWidget(QLabel("Kỹ năng:"))
        self.skill_combo = QComboBox()
        self.skill_combo.addItems(
            [
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
        )
        layout.addWidget(self.skill_combo)

        layout.addWidget(QLabel("Thể lực:"))
        self.stamina_combo = QComboBox()
        self.stamina_combo.addItems(["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])
        layout.addWidget(self.stamina_combo)

        layout.addWidget(QLabel("Tỉ lệ kỹ năng (%):"))
        self.skill_slider = QSlider(Qt.Horizontal)
        self.skill_slider.setRange(0, 100)
        self.skill_slider.setValue(50)
        layout.addWidget(self.skill_slider)

        # ---- Action buttons ----
        self.calc_button = QPushButton("Tính điểm")
        self.calc_button.clicked.connect(self.dummy_calculate)
        layout.addWidget(self.calc_button)

        self.attendance_button = QPushButton("Điểm danh")
        self.attendance_button.clicked.connect(self.dummy_attendance)
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
        self.add_button.clicked.connect(self.dummy_add)
        layout.addWidget(self.add_button)

    # ---- Dummy handlers ----
    def dummy_calculate(self) -> None:
        """Placeholder for score calculation."""
        self.result_label.setText("Dummy calculate called")

    def dummy_attendance(self) -> None:
        """Placeholder for attendance GUI."""
        self.result_label.setText("Dummy attendance GUI")

    def dummy_add(self) -> None:
        """Placeholder for adding a new player."""
        self.result_label.setText("Dummy add player")


def main() -> None:
    app = QApplication(sys.argv)
    win = RandomSquadWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
