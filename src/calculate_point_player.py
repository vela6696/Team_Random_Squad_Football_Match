import tkinter as tk
from tkinter import ttk
import pandas as pd
import team_select_optimized_lib


def ensure_strength_column(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Ensure the strength column exists and is up to date."""
    strength_key = team_select_optimized_lib.STRENGTH_KEY
    if 'tier' in dataframe.columns:
        dataframe[strength_key] = dataframe['tier'].apply(
            team_select_optimized_lib.classify_strength_from_tier
        )
    return dataframe

# === Config ===
CSV_FILE = "players.csv"  # CSV file path
SKILL_LEVELS = ["1 sao", "2 sao", "3 sao", "4 sao", "5 sao","6 sao", "7 sao", "8 sao", "9 sao", "10 sao", "siêu sao" ]
STAMINA_LEVELS = ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]
DEFAULT_SKILL_INDEX = 1  # "2 sao"
DEFAULT_STAMINA_INDEX = 1  # "15p"
DEFAULT_SKILL_WEIGHT = 50  # In percentage

MIN_POINT = 1.0
MAX_POINT = 4.0  # final score = MIN_POINT + normalized * MAX_POINT

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
    "siêu sao": 1.0
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
    "100": 1.0
}
# =================

# Load CSV file into a DataFrame
df = ensure_strength_column(pd.read_csv(CSV_FILE))

def get_score_level(level: str) -> float:
    if level in SKILL_MAPPING:
        return SKILL_MAPPING.get(level, 0.0)
    elif level in STAMINA_MAPPING:
        return STAMINA_MAPPING.get(level, 0.0)

def calculate_score(skill: str, stamina: str, skill_weight: float, stamina_weight: float) -> float:
    skill_score = get_score_level(skill)
    stamina_score = get_score_level(stamina)
    normalized = skill_weight * skill_score + stamina_weight * stamina_score
    final_score = MIN_POINT + normalized * MAX_POINT
    return round(final_score, 1)

def update_player_fields(event=None):
    selected_name = name_combo.get()
    player_row = df[df['name'] == selected_name]

    if not player_row.empty:
        skill = player_row.iloc[0].get('skill', SKILL_LEVELS[DEFAULT_SKILL_INDEX])
        stamina = player_row.iloc[0].get('stamina', STAMINA_LEVELS[DEFAULT_STAMINA_INDEX])

        # Set comboboxes
        if skill in SKILL_LEVELS:
            skill_combo.set(skill)
        else:
            skill_combo.set(SKILL_LEVELS[DEFAULT_SKILL_INDEX])

        # Normalize stamina by converting to float, then back to int string for matching
        try:
            stamina_val = float(stamina)
            stamina_str = str(int(stamina_val)) if stamina_val.is_integer() else str(stamina_val)
        except (ValueError, TypeError):
            stamina_str = STAMINA_LEVELS[DEFAULT_STAMINA_INDEX]
        

        if stamina_str in STAMINA_LEVELS:
            stamina_combo.set(stamina_str)
        else:
            stamina_combo.set(STAMINA_LEVELS[DEFAULT_STAMINA_INDEX])

def on_calculate():
    name = name_combo.get()
    skill = skill_combo.get()
    stamina = stamina_combo.get()
    skill_weight = skill_weight_slider.get() / 100
    stamina_weight = 1.0 - skill_weight

    score = calculate_score(skill, stamina, skill_weight, stamina_weight)

    global df
    df['skill'] = df['skill'].astype('object')
    df['stamina'] = df['stamina'].astype('object')

    if name in df['name'].values:
        df.loc[df['name'] == name, 'tier'] = score
        df.loc[df['name'] == name, 'skill'] = skill
        df.loc[df['name'] == name, 'stamina'] = stamina
        df.loc[df['name'] == name, team_select_optimized_lib.STRENGTH_KEY] = (
            df.loc[df['name'] == name, 'tier'].apply(
                team_select_optimized_lib.classify_strength_from_tier
            )
        )
        df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

    result_label.config(text=f"{name} (Tier: {score})")

# GUI setup
root = tk.Tk()
root.title("FIFA Tool")
root.geometry("300x620")

tk.Label(root, text="Tên cầu thủ:").pack()
name_combo = ttk.Combobox(root, values=df['name'].tolist())
name_combo.current(0)
name_combo.pack()
name_combo.bind("<<ComboboxSelected>>", update_player_fields)


def reload_player_names():
    global df
    df = ensure_strength_column(pd.read_csv(CSV_FILE))
    name_combo['values'] = df['name'].tolist()
    if df['name'].tolist():
        name_combo.current(0)
    result_label.config(text="Danh sách đã được tải lại.")

tk.Button(root, text="Tải lại", command=reload_player_names).pack(pady=(0, 10))

tk.Label(root, text="Kỹ năng:").pack()
skill_combo = ttk.Combobox(root, values=SKILL_LEVELS)
skill_combo.current(DEFAULT_SKILL_INDEX)
skill_combo.pack()

tk.Label(root, text="Thể lực:").pack()
stamina_combo = ttk.Combobox(root, values=STAMINA_LEVELS)
stamina_combo.current(DEFAULT_STAMINA_INDEX)
stamina_combo.pack()
#update player info
update_player_fields()

tk.Label(root, text="Tỉ lệ kỹ năng (%):").pack()
skill_weight_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL)
skill_weight_slider.set(DEFAULT_SKILL_WEIGHT)
skill_weight_slider.pack()

tk.Button(root, text="Tính điểm", command=on_calculate).pack(pady=10)
chia_doi_btn = tk.Button(root, text="Điểm danh", command=lambda: team_select_optimized_lib.show_attendance_gui(root))
chia_doi_btn.pack(pady=10)

result_label = tk.Label(root, text="")
result_label.pack()

# --- Add New Player Section ---
tk.Label(root, text="Thêm cầu thủ mới").pack(pady=(10, 0))

tk.Label(root, text="Tên:").pack()
new_name_entry = tk.Entry(root)
new_name_entry.pack()

tk.Label(root, text="Tier điểm (ví dụ: 2.7):").pack()
new_tier_entry = tk.Entry(root)
new_tier_entry.pack()

tk.Label(root, text="Vị trí:").pack()
position_combo = ttk.Combobox(root, values=["GK", "DF", "MF", "ST"], state="readonly")
position_combo.current(2)
position_combo.pack()

def on_add_new_player():
    name = new_name_entry.get().strip()
    try:
        tier = float(new_tier_entry.get().strip())
    except ValueError:
        result_label.config(text="Lỗi: Tier phải là số!")
        return

    position = position_combo.get().strip()

    if not name or not position:
        result_label.config(text="Tên và vị trí không được để trống.")
        return

    # Check duplicate
    if name in df['name'].values:
        result_label.config(text=f"{name} đã tồn tại!")
        return

    # Add to CSV
    team_select_optimized_lib.add_new_player_to_csv(name, tier, position, filename=CSV_FILE)
    result_label.config(text=f"Đã thêm {name} ({tier})")

    # Update combobox
    reload_player_names()

tk.Button(root, text="Thêm cầu thủ", command=on_add_new_player).pack(pady=5)

root.mainloop()
