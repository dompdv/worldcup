from math import sqrt, floor
import operator
import data_2014
from modelbayes import ModelBayes, print_p, draw_ps
import random
import collections

def fire_once(model,teams, groups, matches, match_codes, given, printing=False):
    # Calcule le match suivant après les pools
    def find_next_match(code, results, team_group_score):
        def group_winner(group, position):
            def order_teams(t):
                return (t[1]['points'], t[1]['gd'])
            g_scores = {team: team_group_score[team] for team in groups[group]}
            sorted_g = sorted(g_scores.items(), key=order_teams)
            team, _ = sorted_g[-position]
            return team

        def match_winner(result):
            return result['w_team1'] if result['gd'] > 0 else result['w_team2']

        def match_loser(result):
            return result['w_team2'] if result['gd'] > 0 else result['w_team1']

        if code[0] == "8":
            team1, team2 = group_winner(code[1],1), group_winner(code[2], 2)

        if code[0] == "4":
            team1, team2 = match_winner(results["8" + code[1:3]]), match_winner(results["8" + code[3:]])

        if code[0] == "2":
            team1, team2 = match_winner(results["4" + code[1:5]]), match_winner(results["4" + code[5:]])

        if code == "1":
            team1, team2 = match_winner(results["2ABCDDCBA"]), match_winner(results["2EFGHFEHG"])

        if code == "1M":
            team1, team2 = match_loser(results["2ABCDDCBA"]), match_loser(results["2EFGHFEHG"])
        return team1, team2
    # garde tous les matchs de pool
    for c in list(given.keys()):
        pool = ord(c[0]) > 64
        if not pool:
            del given[c]
    #given = {}
    numbered_teams ={ team:number for number,team in enumerate(teams)}
    team_group_score = { team: {'points': 0, 'gd': 0} for team in teams}
    results = {}
    for match in matches:
        code = match['match']
        pool = ord(code[0]) > 64
        m = {'date': match['date'], 'match': code, 'pool': pool, 'ending':'std'}
        if code in given:
            m['given'] = True
            m['gd'] = match['gd']
            m['w_team1'] = match['w_team1']
            m['w_team2'] = match['w_team2']
            team1 = numbered_teams[m['w_team1']]
            team2 = numbered_teams[m['w_team2']]
            score = m['gd']
            model.account_for((team1, team2, score))
        else:
            m['given'] = False
            # Determination des équipes
            if pool:
                m['w_team1'] = match['w_team1']
                m['w_team2'] = match['w_team2']
            else:
                m['w_team1'], m['w_team2'] = find_next_match(code, results, team_group_score)

            team1 = numbered_teams[m['w_team1']]
            team2 = numbered_teams[m['w_team2']]
            # Determination du score
            proba = model.proba_score(team1, team2)
            m['proba'] = proba
            # Randomly choose an outcome
            #tirages = [draw_ps(proba) for _ in range(10000)]
            #print(collections.Counter(tirages))
            score = draw_ps(proba)
            if score == 0 and not pool:
                # Pas de nul possible après les Pools, on relance
                m['ending'] = 'prolong'
                score = draw_ps(proba)
                # Penalty : 1 chance sur 2
                if score == 0:
                    m['ending'] = 'penalties'
                    score = random.choice([-1,1])
            m['gd'] = score
            model.account_for((team1, team2, score))
        if score > 0:
            m['winner'] = m['w_team1']
        elif score < 0:
            m['winner'] = m['w_team2']
        else:
            m['winner'] = None
        # Gestion des points la phase Pool
        if pool:
            if score > 0:
                team_group_score[m['w_team1']]['points'] += 3
                team_group_score[m['w_team1']]['gd'] += score
            elif score == 0:
                team_group_score[m['w_team1']]['points'] += 1
                team_group_score[m['w_team2']]['points'] += 1
            else:
                team_group_score[m['w_team2']]['points'] += 3
                team_group_score[m['w_team2']]['gd'] += (-score)
            m['team1_score'] = team_group_score[m['w_team1']]['points']
            m['team2_score'] = team_group_score[m['w_team2']]['points']
        if printing:
            print(m)
            model.print(teams)

        results[code] = m
    return results, team_group_score

def account_for_history(model, matches, teams):
    numbered_teams ={ team:number for number,team in enumerate(teams)}
    filtered = set()
    for i, match in enumerate(matches):
        l1 = numbered_teams[match['w_team1']]
        l2 = numbered_teams[match['w_team2']]
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

def print_results(results, matches, groups, teams, team_group_score):
    print("Date       |    Code    | Pool | Team1             | Team2             | Score | Winner             |")
    for m in matches:
        code = m['match']
        match = results[code]
        gd = match['gd']
        team1 = match['w_team1']
        team2 = match['w_team2']
        winner = ''
        if not match['pool']:
            winner = team1 if gd>0 else team2
        print("{:^11}|{:^12}|{:^6}|{:^19}|{:^19}|{:^7}|{:^19}".format(
            m['date'], code, match['pool'], team1, team2, gd, winner)
        )
    print()

def print_team_score(team_score):
    keys = False
    for t, v in team_score.items():
        if not keys:
            keys = list(v.keys())
            print("{:^20}|".format("Teams"), end='')
            [print("{:^5}|".format(k), end='') for k in keys]
            print()
        print("{:^20}|".format(t), end='')
        [print("{:^5d}|".format(v[k]), end='') for k in keys]
        print()


# Programme Principal
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
delta_elo = max_elo_score - min_elo_score
mean_elo = (max_elo_score + min_elo_score) / 2.0
# On repositionne linéirement les Ecarts en fonction du ELO
elo_scores = {k: (v - mean_elo) * 2.5 / 500 for k,v in elo_scores.items()}

def elo_function(avg, x):
    return 0.1 ** (abs(x-avg))
#Calage des probabilités en fonction des ELOs
probabilities = {}
for team in elo_scores.keys():
    avg = elo_scores[team]
    proba = {k: (elo_function(avg, k-0.5) + elo_function(avg, k+0.5))/2.0 for k in range(-n_buckets, n_buckets+1)}
    s = sum(proba.values())
    proba = {k:v/s for k,v in proba.items()}
    probabilities[team] = proba



model = ModelBayes(n_people, n_buckets, s_max=floor((2 * n_buckets + 1) / bucket_per_gd) + 1, options={'rho': rho, 'bucket_per_gd': bucket_per_gd})
# récupère les etats historiques
model.probabilities = [probabilities[teams[i]] for i in range(len(model.probabilities))]
model.update_stats()
model.adjust_mean()
model.print(teams)

probabilities = model.probabilities.copy()

team_score = {team: {"1": 0, "1M": 0, "2": 0, "4": 0, "8": 0, "q8": 0} for team in teams}

for _ in range(1000):
    model.probabilities = probabilities.copy()
    model.update_stats()
    results, team_group_score = fire_once(model,teams, groups, matches, match_codes, given)
    print("Results")
    print_results(results, matches, groups, teams, team_group_score)
#    model.print(teams)
    team1, team2 = results["1"]['w_team1'], results["1"]['w_team2']
    gd = results["1"]['gd']
    winner = team1 if gd>0 else team2
    print("Finale {} / {} : {} Winner {}".format(team1, team2, gd, winner))
    for code,m in results.items():
        c = code[0]
        if ord(c)<65:
            if c == "8":
                # Les équipes ont passé les pool
                team_score[m['w_team1']]['q8'] += 1
                team_score[m['w_team2']]['q8'] += 1
            if code == '1M':
                c = '1M'
            team_score[m['winner']][c] += 1


print_team_score(team_score)
