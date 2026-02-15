from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
import team_utils as lib

CSV_PATH = lib.CSV_PATH


class TeamSelectionWindow(QDialog):
    """PyQt window for selecting players and forming balanced teams."""

    SELECT_COL = 0
    NAME_COL = 1
    TIER_COL = 2
    POSITION_COL = 3
    STRENGTH_COL = 4

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

        input_row.addWidget(QLabel("Điểm ngưỡng gánh:"))
        self.carrier_spin = QDoubleSpinBox()
        self.carrier_spin.setRange(0.0, 10.0)
        self.carrier_spin.setSingleStep(0.1)
        self.carrier_spin.setValue(lib.get_carrier_threshold())
        input_row.addWidget(self.carrier_spin)

        layout.addLayout(input_row)

        # Player table (read-only values + selectable checkbox)
        self.player_table = QTableWidget()
        self.player_table.setColumnCount(5)
        self.player_table.setHorizontalHeaderLabels(["Chọn", "Tên", "Tier", "Vị trí", "Strength"])
        self.player_table.verticalHeader().setVisible(False)
        self.player_table.setSelectionMode(QTableWidget.NoSelection)
        self.player_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.player_table.setFocusPolicy(Qt.NoFocus)
        self.player_table.horizontalHeader().setSectionResizeMode(self.NAME_COL, QHeaderView.Stretch)
        self.player_table.horizontalHeader().setSectionResizeMode(self.SELECT_COL, QHeaderView.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(self.TIER_COL, QHeaderView.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(self.POSITION_COL, QHeaderView.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(self.STRENGTH_COL, QHeaderView.ResizeToContents)

        self._load_players()
        layout.addWidget(self.player_table)

        self.shuffle_button = QPushButton("Chia đội!!!")
        self.shuffle_button.clicked.connect(self.handle_shuffle)
        layout.addWidget(self.shuffle_button)

    def _make_readonly_item(self, value: str) -> QTableWidgetItem:
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled)
        return item

    def _load_players(self) -> None:
        players = lib.read_players_from_csv(str(CSV_PATH))
        self.player_table.setRowCount(len(players))

        for row, player in enumerate(players):
            strength = player.get(lib.STRENGTH_KEY)
            if not strength:
                strength = "balanced"
            player[lib.STRENGTH_KEY] = strength

            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            checkbox_item.setCheckState(Qt.Unchecked)
            checkbox_item.setData(Qt.UserRole, player)
            self.player_table.setItem(row, self.SELECT_COL, checkbox_item)

            self.player_table.setItem(row, self.NAME_COL, self._make_readonly_item(str(player.get(lib.NAME_KEY, ""))))
            self.player_table.setItem(row, self.TIER_COL, self._make_readonly_item(str(player.get(lib.TIER_KEY, ""))))
            self.player_table.setItem(
                row,
                self.POSITION_COL,
                self._make_readonly_item(str(player.get(lib.POSITION_KEY, ""))),
            )
            self.player_table.setItem(row, self.STRENGTH_COL, self._make_readonly_item(str(strength)))

    def handle_shuffle(self):
        team_count = self.team_spin.value()
        players_per_team = self.players_spin.value()
        tier_threshold = self.tier_spin.value()
        carrier_threshold = self.carrier_spin.value()

        if tier_threshold >= carrier_threshold:
            QMessageBox.warning(self, "Lỗi", "Ngưỡng gánh phải lớn hơn ngưỡng tạ.")
            return

        try:
            lib.set_carrier_threshold(carrier_threshold)
            lib.set_tier_threshold(tier_threshold)
        except ValueError as exc:
            QMessageBox.warning(self, "Lỗi", str(exc))
            return

        selected_players = []
        for row in range(self.player_table.rowCount()):
            check_item = self.player_table.item(row, self.SELECT_COL)
            player = check_item.data(Qt.UserRole)
            tier = player.get(lib.TIER_KEY, 0)
            if tier <= tier_threshold:
                strength = "weak"
            elif tier >= carrier_threshold:
                strength = "strong"
            else:
                strength = "balanced"
            player[lib.STRENGTH_KEY] = strength
            self.player_table.item(row, self.STRENGTH_COL).setText(strength)

            if check_item.checkState() == Qt.Checked:
                selected_players.append(player)

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
