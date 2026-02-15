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
import random
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from fairness_config import DEFAULT_MEDIAN_DELTA, DEFAULT_IQR_DELTA, MAX_RETRIES


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
    df[POSITION_KEY] = df[POSITION_KEY].apply(normalize_position)
    return df.to_dict(orient='records')


def normalize_position(position_value):
    """Normalize position values to a single label: GK/DF/MF/ST."""
    if not isinstance(position_value, str):
        return ""

    cleaned = position_value.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        parts = cleaned.strip("[]").replace("'", "").split(',')
        cleaned = parts[0].strip() if parts else ""

    return cleaned.upper()

def evaluate_team(team):
    return sum(player[TIER_KEY] for player in team)


def median(values):
    """Compute median for odd and even value counts."""
    if not values:
        return 0.0

    ordered = sorted(float(value) for value in values)
    mid = len(ordered) // 2

    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def iqr(values):
    """Compute Tukey IQR (median of halves)."""
    if not values:
        return 0.0

    ordered = sorted(float(value) for value in values)
    n = len(ordered)
    mid = n // 2

    if n % 2 == 1:
        lower = ordered[:mid]
        upper = ordered[mid + 1:]
    else:
        lower = ordered[:mid]
        upper = ordered[mid:]

    if not lower or not upper:
        return 0.0

    q1 = median(lower)
    q3 = median(upper)
    return q3 - q1


def _line_tiers(team):
    lines = {"DF": [], "MF": [], "ST": []}
    for player in team:
        line = normalize_position(player.get(POSITION_KEY, ""))
        if line in lines:
            lines[line].append(float(player[TIER_KEY]))
    return lines


def _evaluate_fairness(teams):
    if len(teams) != 2:
        return {
            "accepted": True,
            "medians": {},
            "iqr": {},
            "median_delta": {},
            "iqr_delta": {},
            "violation_score": 0.0,
        }

    team_line_tiers = [_line_tiers(teams[0]), _line_tiers(teams[1])]
    medians = {"team1": {}, "team2": {}}
    iqrs = {"team1": {}, "team2": {}}
    median_delta = {}
    iqr_delta = {}
    violation_score = 0.0
    accepted = True

    for line in ["DF", "MF", "ST"]:
        t1_values = team_line_tiers[0][line]
        t2_values = team_line_tiers[1][line]

        medians["team1"][line] = median(t1_values)
        medians["team2"][line] = median(t2_values)
        iqrs["team1"][line] = iqr(t1_values)
        iqrs["team2"][line] = iqr(t2_values)

        median_delta[line] = abs(medians["team1"][line] - medians["team2"][line])
        iqr_delta[line] = abs(iqrs["team1"][line] - iqrs["team2"][line])

        epsilon = 1e-9
        median_over = max(0.0, median_delta[line] - DEFAULT_MEDIAN_DELTA[line] - epsilon)
        iqr_over = max(0.0, iqr_delta[line] - DEFAULT_IQR_DELTA[line] - epsilon)
        violation_score += median_over + iqr_over

        if median_delta[line] - DEFAULT_MEDIAN_DELTA[line] > epsilon or iqr_delta[line] - DEFAULT_IQR_DELTA[line] > epsilon:
            accepted = False

    return {
        "accepted": accepted,
        "medians": medians,
        "iqr": iqrs,
        "median_delta": median_delta,
        "iqr_delta": iqr_delta,
        "violation_score": violation_score,
    }


def generate_balanced_teams(players, team_count=2, max_retries=MAX_RETRIES):
    attempts = []

    for attempt_idx in range(1, max_retries + 1):
        candidate_teams = balance_teams(players, team_count=team_count)
        fairness = _evaluate_fairness(candidate_teams)
        attempt_payload = {
            "teams": candidate_teams,
            "fairness": fairness,
            "attempt_index": attempt_idx,
        }
        attempts.append(attempt_payload)
        if fairness["accepted"]:
            attempt_payload["selection"] = "accepted"
            attempt_payload["retries_used"] = attempt_idx - 1
            attempt_payload["attempts_evaluated"] = attempts
            return attempt_payload

    chosen = min(attempts, key=lambda attempt: attempt["fairness"]["violation_score"])
    chosen["selection"] = "fallback"
    chosen["retries_used"] = max_retries
    chosen["attempts_evaluated"] = attempts
    return chosen

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
def _lowest_score_team_index(team_scores):
    """Return a random index among teams with the current lowest score."""
    min_score = min(team_scores)
    candidates = [idx for idx, score in enumerate(team_scores) if score == min_score]
    return random.choice(candidates)


def _assign_players_in_rounds(teams, players, team_scores, team_count):
    """Assign players in top-tier rounds; leftover players go to lowest-score teams."""
    ordered_players = list(players)
    random.shuffle(ordered_players)
    ordered_players.sort(key=lambda p: p[TIER_KEY], reverse=True)

    for start in range(0, len(ordered_players), team_count):
        batch = ordered_players[start:start + team_count]
        if len(batch) == team_count:
            random.shuffle(batch)
            for team_idx, player in enumerate(batch):
                teams[team_idx].append(player)
                team_scores[team_idx] += player[TIER_KEY]
            continue

        for player in batch:
            team_idx = _lowest_score_team_index(team_scores)
            teams[team_idx].append(player)
            team_scores[team_idx] += player[TIER_KEY]


def balance_teams(players, team_count=2):
    position_order = [GK_LABEL, "DF", "MF", "ST"]
    teams = [[] for _ in range(team_count)]
    team_scores = [0.0] * team_count
    players_by_position = {position: [] for position in position_order}

    for player in players:
        position = normalize_position(player.get(POSITION_KEY, ""))
        player[POSITION_KEY] = position
        if position not in players_by_position:
            raise ValueError(f"Unsupported position '{position}' for {player[NAME_KEY]}.")
        players_by_position[position].append(player)
        player[STRENGTH_KEY] = classify_strength_from_tier(player[TIER_KEY])

    gk_players = players_by_position[GK_LABEL]
    if REQUIRE_GK_PER_TEAM and len(gk_players) < team_count:
        raise ValueError(f"Not enough {GK_LABEL}s to form {team_count} teams.")

    mandatory_gks = list(gk_players[:team_count])
    if mandatory_gks:
        _assign_players_in_rounds(teams, mandatory_gks, team_scores, team_count)

    extra_gks = gk_players[team_count:]

    for position in ["DF", "MF", "ST"]:
        position_players = players_by_position[position]
        if not position_players:
            continue

        _assign_players_in_rounds(teams, position_players, team_scores, team_count)

    if extra_gks:
        _assign_players_in_rounds(teams, extra_gks, team_scores, team_count)

    return teams

def run_team_assignment(filename=CSV_FILE, selected_players=None, team_count=2, return_details=False):
    all_players = read_players_from_csv(filename)
    if selected_players is not None:
        selected_names = [p[NAME_KEY] for p in selected_players]
        players = [p for p in all_players if p[NAME_KEY] in selected_names]
    else:
        players = all_players

    selection = generate_balanced_teams(players, team_count=team_count)
    teams = selection["teams"]
    fairness = selection["fairness"]

    result = []
    team_scores = []

    for idx, team in enumerate(teams, start=1):
        result.append(f"\nTeam {idx}:")
        for i, player in enumerate(team, start=1):
            position = player.get(POSITION_KEY, "")
            result.append(
                f"{i}. {player[NAME_KEY]} (Tier: {player[TIER_KEY]}, Position: {position})"
            )
        score = evaluate_team(team)
        team_scores.append(score)
        result.append(f"Team {idx} Score: {score} (Players: {len(team)})")

    balance_diff = max(team_scores) - min(team_scores)
    result.append(f"\nBalance Difference: {balance_diff}")

    result.append("\nFairness Checks:")
    result.append(
        f"Selected via: {selection['selection']} | Attempt: {selection['attempt_index']} | Retries used: {selection['retries_used']}"
    )
    for line in ["DF", "MF", "ST"]:
        result.append(
            (
                f"{line} median T1/T2: {fairness['medians']['team1'][line]} / {fairness['medians']['team2'][line]} "
                f"(Δ {fairness['median_delta'][line]}, threshold {DEFAULT_MEDIAN_DELTA[line]})"
            )
        )
        result.append(
            (
                f"{line} IQR T1/T2: {fairness['iqr']['team1'][line]} / {fairness['iqr']['team2'][line]} "
                f"(Δ {fairness['iqr_delta'][line]}, threshold {DEFAULT_IQR_DELTA[line]})"
            )
        )

    text_result = "\n".join(result)
    if return_details:
        return {
            "text": text_result,
            "teams": teams,
            "medians": fairness["medians"],
            "iqr": fairness["iqr"],
            "median_delta": fairness["median_delta"],
            "iqr_delta": fairness["iqr_delta"],
            "selection": selection["selection"],
            "attempt_index": selection["attempt_index"],
            "retries_used": selection["retries_used"],
        }

    return text_result


def self_test_statistics():
    """Simple self-check for median and IQR helpers."""
    sample = [1.0, 2.0, 3.0, 4.0, 10.0]
    return {
        "sample": sample,
        "median": median(sample),
        "iqr": iqr(sample),
    }


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
def add_new_player_to_csv(name, tier, position, filename=CSV_FILE):
    if not isinstance(position, str):
        raise ValueError("Position must be a single string value: GK, DF, MF, or ST.")

    position = normalize_position(position)
    if position not in {GK_LABEL, "DF", "MF", "ST"}:
        raise ValueError("Position must be one of: GK, DF, MF, ST.")

    new_player = {
        NAME_KEY: name,
        TIER_KEY: float(tier),
        POSITION_KEY: position,
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
# add_new_player_to_csv("Leo", 2.7, "GK")
