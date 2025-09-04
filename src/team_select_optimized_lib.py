# === Config ===
CSV_FILE = "players.csv"
TIER_THRESHOLD_LOW = 2.8            # Players below this tier are considered low tier
TEAM_COUNT = 3                     # Number of teams to split into
REQUIRE_GK_PER_TEAM = True          # Whether each team must have a GK
TIER_KEY = "tier"                   # Column used to evaluate players
POSITION_KEY = "position"
NAME_KEY = "name"
GK_LABEL = "GK"
DEFAULT_ENCODING = "utf-8"

# === Core Logic ===
import itertools
import random
import heapq
import pandas as pd

def write_players_to_csv(filename, players):
    df = pd.DataFrame(players)
    df.to_csv(filename, index=False)

def read_players_from_csv(filename):
    df = pd.read_csv(filename, encoding=DEFAULT_ENCODING)
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
    low_tier_players = [p for p in remaining_players if p[TIER_KEY] <= TIER_THRESHOLD_LOW]
    other_players = [p for p in remaining_players if p[TIER_KEY] > TIER_THRESHOLD_LOW]

    # Chia đều low tier trước
    teams = [[] for _ in range(team_count)]
    for idx, player in enumerate(low_tier_players):
        teams[idx % team_count].append(player)

    # Số lượng còn lại cần chia
    num_remaining = len(other_players)
    players_per_team = len(players) // team_count
    others_per_team = players_per_team - len(teams[0]) - 1  # trừ low-tier và GK

    best_balance = float('inf')
    best_team_combo = None

    # Generate combinations
    for combo in itertools.combinations(range(len(other_players)), others_per_team * (team_count - 1)):
        temp_teams = [list(team) for team in teams]
        used = set(combo)
        indices = list(combo) + [i for i in range(len(other_players)) if i not in used]

        for i in range(team_count - 1):
            temp_teams[i].extend([other_players[indices[j]] for j in range(i * others_per_team, (i + 1) * others_per_team)])

        # Add remaining to last team
        temp_teams[-1].extend([other_players[indices[j]] for j in range((team_count - 1) * others_per_team, len(indices))])

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
            result.append(f"{i}. {player[NAME_KEY]} (Tier: {player[TIER_KEY]}){gk_flag}")
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
        POSITION_KEY: positions
    }

    try:
        df = pd.read_csv(filename, encoding=DEFAULT_ENCODING)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[NAME_KEY, TIER_KEY, POSITION_KEY])

    df = df._append(new_player, ignore_index=True)
    df.to_csv(filename, index=False, encoding=DEFAULT_ENCODING)




# Run it like this:
# run_team_assignment()
# add_new_player_to_csv("Leo", 2.7, ["GK", "DEF"])