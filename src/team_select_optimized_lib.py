# === Config ===
CSV_FILE = "players.csv"
TIER_THRESHOLD_LOW = 2.8            # Players below this tier are considered low tier
TIER_THRESHOLD_HIGH = 3.8           # Players above this tier are considered strong tier
TEAM_COUNT = 3                     # Number of teams to split into
REQUIRE_GK_PER_TEAM = True          # Whether each team must have a GK
TIER_KEY = "tier"                   # Column used to evaluate players
POSITION_KEY = "position"
NAME_KEY = "name"
STRENGTH_KEY = "strength"
GK_LABEL = "GK"
DEFAULT_ENCODING = "utf-8"

# === Core Logic ===
import itertools
import random
import heapq
import pandas as pd
import tkinter as tk
from tkinter import messagebox


def classify_strength_from_tier(tier_value):
    """Return the strength classification for a tier value."""
    try:
        tier = float(tier_value)
    except (TypeError, ValueError):
        return "unknown"

    if tier <= TIER_THRESHOLD_LOW:
        return "weak"
    if tier >= TIER_THRESHOLD_HIGH:
        return "strong"
    return "balanced"

player_vars = []

def show_popup(title, text):
    root = tk.Tk()
    root.title(title)

    text_widget = tk.Text(root, wrap='word', height=30, width=60)
    text_widget.insert('1.0', text)
    text_widget.config(state='disabled')
    text_widget.pack(padx=10, pady=10)

    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        messagebox.showinfo("Copied", "Team result copied to clipboard!")

    button_frame = tk.Frame(root)
    button_frame.pack(pady=(0, 10))

    copy_button = tk.Button(button_frame, text="Copy", command=copy_to_clipboard)
    copy_button.pack(side='left', padx=5)

    ok_button = tk.Button(button_frame, text="OK", command=root.destroy)
    ok_button.pack(side='left', padx=5)

    root.mainloop()

def write_players_to_csv(filename, players):
    df = pd.DataFrame(players)
    if TIER_KEY in df.columns:
        df[STRENGTH_KEY] = df[TIER_KEY].apply(classify_strength_from_tier)
    df.to_csv(filename, index=False, encoding=DEFAULT_ENCODING)

def read_players_from_csv(filename):
    df = pd.read_csv(filename, encoding=DEFAULT_ENCODING)
    if TIER_KEY in df.columns:
        df[STRENGTH_KEY] = df[TIER_KEY].apply(classify_strength_from_tier)
    df[POSITION_KEY] = df[POSITION_KEY].apply(
        lambda x: x.strip("[]").replace("'", "").split(', ') if isinstance(x, str) else []
    )
    return df.to_dict(orient='records')

def evaluate_team(team):
    return sum(player[TIER_KEY] for player in team)

# Fix for 2 teams
#def balance_teams(players):
#    random.shuffle(players)
#
#    if REQUIRE_GK_PER_TEAM:
#        gks = [p for p in players if GK_LABEL in p[POSITION_KEY]]
#        if len(gks) < TEAM_COUNT:
#            raise ValueError(f"Not enough {GK_LABEL}s to form {TEAM_COUNT} teams.")
#        gks.sort(key=lambda p: p[TIER_KEY], reverse=True)
#        selected_gks = gks[:TEAM_COUNT]
#        random.shuffle(selected_gks)
#    else:
#        selected_gks = [None] * TEAM_COUNT
#
#    remaining_players = [p for p in players if p not in selected_gks]
#    low_tier_players = [p for p in remaining_players if p[TIER_KEY] <= TIER_THRESHOLD_LOW]
#    other_players = [p for p in remaining_players if p[TIER_KEY] > TIER_THRESHOLD_LOW]
#
#    half_low = len(low_tier_players) // TEAM_COUNT
#    team1_low = low_tier_players[:half_low]
#    team2_low = low_tier_players[half_low:]
#
#    total_players = len(players)
#    half_size = total_players // TEAM_COUNT - 1 - len(team1_low)
#
#    best_balance = float('inf')
#    best_teams = None
#    min_heap = []
#    teams_list = []
#
#    for team1_indices in itertools.combinations(range(len(other_players)), half_size):
#        team1 = [other_players[i] for i in team1_indices] + team1_low
#        team2 = [other_players[i] for i in range(len(other_players)) if i not in team1_indices] + team2_low
#
#        if REQUIRE_GK_PER_TEAM:
#            team1.append(selected_gks[0])
#            team2.append(selected_gks[1])
#
#        score_team1 = evaluate_team(team1)
#        score_team2 = evaluate_team(team2)
#
#        balance = abs(score_team1 - score_team2)
#
#        teams_list.append((team1, team2))
#        heapq.heappush(min_heap, (balance, len(teams_list) - 1))
#
#    _, best_index = heapq.heappop(min_heap)
#    return teams_list[best_index]

# new team balance
def balance_teams(players, team_count=2):
    if len(players) < team_count * 7:
        raise ValueError(f"Need at least {team_count * 7} players to form {team_count} teams of 7.")

    random.shuffle(players)

    # Chia GK
    if REQUIRE_GK_PER_TEAM:
        gks = [p for p in players if GK_LABEL in p[POSITION_KEY]]
        if len(gks) < team_count:
            raise ValueError(f"Not enough {GK_LABEL}s to form {team_count} teams.")
        gks.sort(key=lambda p: p[TIER_KEY], reverse=True)
        selected_gks = gks[:team_count]
    else:
        selected_gks = [None] * team_count

    # Loại GK khỏi player pool
    remaining_players = [p for p in players if p not in selected_gks]

    low_tier_players = []
    high_tier_players = []
    balanced_players = []

    for player in remaining_players:
        tier_value = player[TIER_KEY]
        if tier_value <= TIER_THRESHOLD_LOW:
            player[STRENGTH_KEY] = "weak"
            low_tier_players.append(player)
        elif tier_value >= TIER_THRESHOLD_HIGH:
            player[STRENGTH_KEY] = "strong"
            high_tier_players.append(player)
        else:
            player[STRENGTH_KEY] = "balanced"
            balanced_players.append(player)

    # Chia đều low tier trước
    teams = [[] for _ in range(team_count)]
    for idx, player in enumerate(low_tier_players):
        teams[idx % team_count].append(player)

    # Chia đều high tier để mỗi đội có người gánh
    for idx, player in enumerate(high_tier_players):
        teams[idx % team_count].append(player)

    # Số lượng còn lại cần chia
    players_per_team = len(players) // team_count
    gk_per_team = 1 if REQUIRE_GK_PER_TEAM else 0
    others_per_team = players_per_team - len(teams[0]) - gk_per_team

    if others_per_team < 0:
        raise ValueError("Tổng số người yếu/khỏe vượt quá giới hạn mỗi đội. Điều chỉnh lại ngưỡng.")

    best_balance = float('inf')
    best_team_combo = None

    combinations_needed = others_per_team * (team_count - 1)

    if combinations_needed <= 0:
        candidate_pools = [list(team) for team in teams]
        for i in range(team_count):
            if selected_gks[i]:
                candidate_pools[i].append(selected_gks[i])
        return candidate_pools

    if len(balanced_players) < combinations_needed:
        # Không đủ người cân bằng để brute-force, chia đều phần còn lại
        remaining_pool = list(balanced_players)
        temp_teams = [list(team) for team in teams]

        for i in range(team_count):
            needed = players_per_team - gk_per_team - len(temp_teams[i])
            temp_teams[i].extend(remaining_pool[:needed])
            remaining_pool = remaining_pool[needed:]

        for i in range(team_count):
            if selected_gks[i]:
                temp_teams[i].append(selected_gks[i])

        scores = [evaluate_team(team) for team in temp_teams]
        best_team_combo = temp_teams
        best_balance = max(scores) - min(scores)
    else:
        for combo in itertools.combinations(range(len(balanced_players)), combinations_needed):
            temp_teams = [list(team) for team in teams]
            used = set(combo)
            indices = list(combo) + [i for i in range(len(balanced_players)) if i not in used]

            for i in range(team_count - 1):
                start = i * others_per_team
                end = (i + 1) * others_per_team
                temp_teams[i].extend([balanced_players[indices[j]] for j in range(start, end)])

            temp_teams[-1].extend([balanced_players[indices[j]] for j in range((team_count - 1) * others_per_team, len(indices))])

            # Add GK
            for i in range(team_count):
                if selected_gks[i]:
                    temp_teams[i].append(selected_gks[i])

            scores = [evaluate_team(team) for team in temp_teams]
            balance = max(scores) - min(scores)

            if balance < best_balance:
                best_balance = balance
                best_team_combo = temp_teams

    if not best_team_combo:
        raise RuntimeError("Unable to balance teams.")

    return best_team_combo

def run_team_assignment(filename=CSV_FILE, selected_players=None, team_count=2):
    all_players = read_players_from_csv(filename)
    if selected_players is not None:
        selected_names = [p[NAME_KEY] for p in selected_players]
        players = [p for p in all_players if p[NAME_KEY] in selected_names]
    else:
        players = all_players

    teams = balance_teams(players, team_count=team_count)

    result = []
    team_scores = []

    for idx, team in enumerate(teams, start=1):
        result.append(f"\nTeam {idx}:")
        for i, player in enumerate(team, start=1):
            gk_flag = " (GK)" if GK_LABEL in player[POSITION_KEY] else ""
            strength = player.get(STRENGTH_KEY, classify_strength_from_tier(player[TIER_KEY]))
            result.append(
                f"{i}. {player[NAME_KEY]} (Tier: {player[TIER_KEY]}, Strength: {strength}){gk_flag}"
            )
        score = evaluate_team(team)
        team_scores.append(score)
        result.append(f"Team {idx} Score: {score} (Players: {len(team)})")

    balance_diff = max(team_scores) - min(team_scores)
    result.append(f"\nBalance Difference: {balance_diff}")

    return "\n".join(result)


#def run_team_assignment(filename=CSV_FILE, selected_players=None):
#    all_players = read_players_from_csv(filename)
#    if selected_players is not None:
#        # selected_players is assumed to be a list of names
#        selected_names = [p[NAME_KEY] for p in selected_players]
#        players = [p for p in all_players if p[NAME_KEY] in selected_names]
#    else:
#        players = all_players
#
#    #print(f"players: {players}")
#    #print(f"selected_players : {selected_players}")
#    #print(f"all_players: {all_players}")
#
#    team1, team2 = balance_teams(players)
#
#    result = []
#    result.append("Team 1:")
#    for i, player in enumerate(team1, start=1):
#        gk_flag = " (GK)" if GK_LABEL in player[POSITION_KEY] else ""
#        result.append(f"{i}. {player[NAME_KEY]} (Tier: {player[TIER_KEY]}){gk_flag}")
#
#    result.append("\nTeam 2:")
#    for i, player in enumerate(team2, start=1):
#        gk_flag = " (GK)" if GK_LABEL in player[POSITION_KEY] else ""
#        result.append(f"{i}. {player[NAME_KEY]} (Tier: {player[TIER_KEY]}){gk_flag}")
#
#    score_team1 = evaluate_team(team1)
#    score_team2 = evaluate_team(team2)
#    result.append(f"\nTeam 1 Score: {score_team1} (Players: {len(team1)})")
#    result.append(f"Team 2 Score: {score_team2} (Players: {len(team2)})")
#    result.append(f"Balance Difference: {abs(score_team1 - score_team2)}")
#
#    return "\n".join(result)

#insert new players
def add_new_player_to_csv(name, tier, positions, filename=CSV_FILE):
    if isinstance(positions, str):
        positions = [positions]
    elif not isinstance(positions, list):
        raise ValueError("Positions must be a list or a string.")

    new_player = {
        NAME_KEY: name,
        TIER_KEY: float(tier),
        POSITION_KEY: positions,
        STRENGTH_KEY: classify_strength_from_tier(tier)
    }

    try:
        df = pd.read_csv(filename, encoding=DEFAULT_ENCODING)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[NAME_KEY, TIER_KEY, POSITION_KEY, STRENGTH_KEY])

    df = df._append(new_player, ignore_index=True)
    df.to_csv(filename, index=False, encoding=DEFAULT_ENCODING)

# Old one
#def show_attendance_gui(parent=None):
#    all_players = read_players_from_csv(CSV_FILE)
#    player_vars = []
#
#    top = tk.Toplevel(parent) if parent else tk.Tk()
#    top.title("Player Attendance")
#
#    canvas = tk.Canvas(top)
#    scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
#    scrollable_frame = tk.Frame(canvas)
#
#    scrollable_frame.bind(
#        "<Configure>",
#        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
#    )
#
#    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
#    canvas.configure(yscrollcommand=scrollbar.set)
#
#    for player in all_players:
#        var = tk.IntVar(value=0)
#        cb_text = f"{player[NAME_KEY]} (Tier: {player[TIER_KEY]})"
#        cb = tk.Checkbutton(scrollable_frame, text=cb_text, variable=var)
#        cb.pack(anchor='w')
#        player_vars.append((var, player[NAME_KEY]))
#
#    def handle_shuffle():
#        selected_players = []
#        for var, name in player_vars:
#            if var.get():
#                for player in all_players:
#                    if player[NAME_KEY] == name:
#                        selected_players.append(player)
#                        break
#
#        if len(selected_players) < TEAM_COUNT:
#            messagebox.showerror("Error", "Not enough players to form teams!")
#            return
#
#        try:
#            result = run_team_assignment(selected_players=selected_players, team_count=TEAM_COUNT)
#            show_popup("Team Assignment Result", result)
#        except ValueError as e:
#            messagebox.showerror("Error", str(e))
#
#    shuffle_button = tk.Button(top, text="Chia đội!!!", command=handle_shuffle)
#    shuffle_button.pack(pady=10)
#
#    canvas.pack(side="left", fill="both", expand=True)
#    scrollbar.pack(side="right", fill="y")

def show_attendance_gui(parent=None):
    all_players = read_players_from_csv(CSV_FILE)
    player_vars = []

    top = tk.Toplevel(parent) if parent else tk.Tk()
    top.title("Player Attendance")

    canvas = tk.Canvas(top)
    scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # ==== Inputs for team settings ====
    input_frame = tk.Frame(top)
    input_frame.pack(pady=5)

    tk.Label(input_frame, text="Số đội:").grid(row=0, column=0, padx=5)
    team_count_entry = tk.Entry(input_frame, width=5)
    team_count_entry.insert(0, "2")
    team_count_entry.grid(row=0, column=1, padx=5)

    tk.Label(input_frame, text="Người/đội:").grid(row=0, column=2, padx=5)
    players_per_team_entry = tk.Entry(input_frame, width=5)
    players_per_team_entry.insert(0, "7")
    players_per_team_entry.grid(row=0, column=3, padx=5)

    tk.Label(input_frame, text="Tier threshold:").grid(row=0, column=4, padx=5)
    tier_threshold_entry = tk.Entry(input_frame, width=5, validate="key")
    tier_threshold_entry.insert(0, str(TIER_THRESHOLD_LOW))  # default = 2.8
    tier_threshold_entry.grid(row=0, column=5, padx=5)

    tk.Label(input_frame, text="Carrier threshold:").grid(row=0, column=6, padx=5)
    carrier_threshold_entry = tk.Entry(input_frame, width=5, validate="key")
    carrier_threshold_entry.insert(0, str(TIER_THRESHOLD_HIGH))
    carrier_threshold_entry.grid(row=0, column=7, padx=5)

    # enforce numeric only
    def validate_numeric(P):
        return P == "" or P.replace(".", "", 1).isdigit()

    vcmd = (top.register(validate_numeric), "%P")
    tier_threshold_entry.config(validatecommand=vcmd)
    carrier_threshold_entry.config(validatecommand=vcmd)

    # ==== Checkboxes for player attendance ====
    for player in all_players:
        var = tk.IntVar(value=0)
        strength = player.get(STRENGTH_KEY, classify_strength_from_tier(player[TIER_KEY]))
        cb_text = f"{player[NAME_KEY]} (Tier: {player[TIER_KEY]}, Strength: {strength})"
        cb = tk.Checkbutton(scrollable_frame, text=cb_text, variable=var)
        cb.pack(anchor='w')
        player_vars.append((var, player[NAME_KEY]))

    def handle_shuffle():
        global TIER_THRESHOLD_LOW, TIER_THRESHOLD_HIGH
        # Get inputs
        try:
            team_count = int(team_count_entry.get())
            players_per_team = int(players_per_team_entry.get())
            TIER_THRESHOLD_LOW = float(tier_threshold_entry.get())
            TIER_THRESHOLD_HIGH = float(carrier_threshold_entry.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ cho cấu hình chia đội.")
            return

        if TIER_THRESHOLD_LOW >= TIER_THRESHOLD_HIGH:
            messagebox.showerror("Lỗi", "Ngưỡng mạnh phải lớn hơn ngưỡng yếu.")
            return

        if team_count < 2 or players_per_team < 1:
            messagebox.showerror("Lỗi", "Phải có ít nhất 2 đội và mỗi đội ít nhất 1 người.")
            return

        selected_players = []
        for var, name in player_vars:
            if var.get():
                for player in all_players:
                    if player[NAME_KEY] == name:
                        selected_players.append(player)
                        break

        if len(selected_players) < team_count * players_per_team:
            messagebox.showerror("Lỗi", f"Cần ít nhất {team_count * players_per_team} người để chia {team_count} đội.")
            return

        try:
            result = run_team_assignment(selected_players=selected_players, team_count=team_count)
            show_popup("Kết quả chia đội", result)
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))

    shuffle_button = tk.Button(top, text="Chia đội!!!", command=handle_shuffle)
    shuffle_button.pack(pady=10)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")



# Run it like this:
# run_team_assignment()
# show_attendance_gui()
# add_new_player_to_csv("Leo", 2.7, ["GK", "DEF"])