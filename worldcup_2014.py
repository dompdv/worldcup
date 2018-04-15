from math import sqrt, floor
import data_2014
from model_base import Model_base, print_p, draw_ps


def fire_once(model,teams, groups, matches, match_codes, given):
    numbered_teams ={ team:number for number,team in enumerate(teams)}
    results = []
    for match in matches:
        code = match['match']
        m = {'date': match['date'], 'match': code}
        print(m)
        if code in given:
            print("given")
            m['gd'] = match['gd']
            m['team1'] = match['team1']
            m['team2'] = match['team2']
            team1 = numbered_teams[m['team1']]
            team2 = numbered_teams[m['team2']]
            score = m['gd']
            model.account_for((team1, team2, score))
            model.print(teams)
        pool = ord(code[0]) < 65

def account_for_history(model, matches, teams):
    numbered_teams ={ team:number for number,team in enumerate(teams)}
    filtered = set()
    for i, match in enumerate(matches):
        l1 = numbered_teams[match['team1']]
        l2 = numbered_teams[match['team2']]
        score = match['gd']
        if len(filtered) > 0:
            display_list = filtered.copy()
            display_list.add(l1)
            display_list.add(l2)
            if l1 in filtered or l2 in filtered:
                print(i, match)
                print("Before")
                model.print(teams, keep=display_list)
                model.account_for((l1, l2, score))
                print("After")
                model.print(teams, keep=display_list)
        else:
            print(i, match)
            model.account_for((l1, l2, score))
    #model.print(teams)

n_buckets = 6
rho = 0.5
bucket_per_gd = 1

teams = data_2014.teams()
matches = data_2014.matches()
match_codes = data_2014.match_codes()
given = data_2014.results()
groups = data_2014.groups()
n_people = len(teams)

elo_scores = data_2014.elo_scores()
# Ai calculé que 500 points correspondent à 3 points d'ecart au total
max_elo_score = max(elo_scores.values())
min_elo_score = min(elo_scores.values())
delte_elo = max_elo_score - min_elo_score


model = Model_base(n_people, n_buckets, s_max=floor((2*n_buckets+1)/bucket_per_gd)+1, options={'rho': rho, 'bucket_per_gd': bucket_per_gd} )
# récupère les etats historiques
model.probabilities = [probabilities[teams[i]] for i in range(len(model.probabilities))]
model.update_stats()
model.adjust_mean()
model.print(teams)
print(model.mean)

ps = model.proba_score(14,19)
print_p(ps)

#fire_once(model,teams, groups, matches, match_codes, given)