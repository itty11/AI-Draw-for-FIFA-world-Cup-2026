import random
import json


# -----------------------------------------------------------
#  VALIDATION HELPERS
# -----------------------------------------------------------

def validate_team_pair(t1, t2, rules):
    """Return True if t1 can be placed with t2 based on given rules."""

    # Avoid same nation in same group
    if rules.get("avoid_same_nation"):
        if t1["nation"] == t2["nation"]:
            return False

    # Hard conflict pairs (rare cases)
    conflict_pairs = rules.get("conflicts", [])
    if (t1["name"], t2["name"]) in conflict_pairs or (t2["name"], t1["name"]) in conflict_pairs:
        return False

    return True


def group_allows_team(group, team, rules):
    """Check if a team can be added to a group under rules."""
    for placed in group:
        if not validate_team_pair(team, placed, rules):
            return False
    return True


# -----------------------------------------------------------
#  MAIN AI DRAW ENGINE (Backtracking System)
# -----------------------------------------------------------

class DrawEngine:

    def __init__(self, pots, rules):
        self.pots = pots                      # List of four pots (Pot1 → Pot4)
        self.rules = rules                    # Validation rules dict
        self.groups = {f"Group {chr(65+i)}": [] for i in range(8)}
        self.max_group_size = 4               # WC groups of 4 teams

    # -----------------------------------------

    def try_place_team(self, team, group_name):
        """Try placing a team inside a group with rule checks."""
        group = self.groups[group_name]

        if len(group) >= self.max_group_size:
            return False

        if not group_allows_team(group, team, self.rules):
            return False

        group.append(team)
        return True

    # -----------------------------------------

    def remove_team(self, team, group_name):
        """Undo placement (for backtracking)."""
        if team in self.groups[group_name]:
            self.groups[group_name].remove(team)

    # -----------------------------------------

    def assign_pot(self, pot_index):
        """Recursive backtracking assignment for pots."""

        # If all pots assigned → success
        if pot_index >= len(self.pots):
            return True

        pot = self.pots[pot_index]
        random.shuffle(pot)  # Shuffle to allow randomness

        for team in pot:

            random_groups = list(self.groups.keys())
            random.shuffle(random_groups)

            placed = False

            for g in random_groups:
                if self.try_place_team(team, g):
                    placed = True

                    # Continue with next team or pot
                    if self.assign_pot(pot_index + (1 if pot.index(team) == len(pot) - 1 else 0)):
                        return True

                    # If failed later → backtrack
                    self.remove_team(team, g)

            if not placed:
                return False

        return True

    # -----------------------------------------

    def run_draw(self, max_attempts=2000):
        """Main entry. Try draw repeatedly until valid solution appears."""

        for _ in range(max_attempts):
            # Reset groups
            self.groups = {f"Group {chr(65+i)}": [] for i in range(8)}

            if self.assign_pot(0):
                return self.groups

        raise Exception("No valid draw possible after many attempts.")


# -----------------------------------------------------------
#  HELPER UTILITIES
# -----------------------------------------------------------

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------------------------------------
#  FACTORY FUNCTION (Used in app.py)
# -----------------------------------------------------------

def run_draw_engine(pots, rules, attempts=2000):
    engine = DrawEngine(pots, rules)
    return engine.run_draw(max_attempts=attempts)
