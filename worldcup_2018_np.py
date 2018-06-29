from math import floor
import data_2018
from modelbayesfast import ModelBayesFast, print_p, draw_ps
import random
import numpy as np

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
            return result['team1'] if result['gd'] > 0 else result['team2']

        def match_loser(result):
            return result['team2'] if result['gd'] > 0 else result['team1']

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
    '''
        # garde tous les matchs de pool
        for c in list(given.keys()):
            pool = ord(c[0]) > 64
            if not pool:
                del given[c]
        #given = {}
    '''
    numbered_teams ={ team:number for number,team in enumerate(teams)}
    team_group_score = { team: {'points': 0, 'gd': 0} for team in teams}
    results = {}
    ffirst = True
    for match in matches:
        code = match['match']
        pool = ord(code[0]) > 64
        m = {'date': match['date'], 'match': code, 'pool': pool, 'ending':'std'}
        if code in given:
            m['given'] = True
            m['gd'] = match['gd']
            m['team1'] = match['team1']
            m['team2'] = match['team2']
            team1 = numbered_teams[m['team1']]
            team2 = numbered_teams[m['team2']]
            score = m['gd']
            model.account_for((team1, team2, score))
        else:
            if ffirst:
                #print("Not given")
                #model.print(teams)
                ffirst = False
            m['given'] = False
            # Determination des équipes
            if pool:
                m['team1'] = match['team1']
                m['team2'] = match['team2']
            else:
                m['team1'], m['team2'] = find_next_match(code, results, team_group_score)

            team1 = numbered_teams[m['team1']]
            team2 = numbered_teams[m['team2']]
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
            m['winner'] = m['team1']
        elif score < 0:
            m['winner'] = m['team2']
        else:
            m['winner'] = None
        # Gestion des points la phase Pool
        if pool:
            if score > 0:
                team_group_score[m['team1']]['points'] += 3
                team_group_score[m['team1']]['gd'] += score
            elif score == 0:
                team_group_score[m['team1']]['points'] += 1
                team_group_score[m['team2']]['points'] += 1
            else:
                team_group_score[m['team2']]['points'] += 3
                team_group_score[m['team2']]['gd'] += (-score)
            m['team1_score'] = team_group_score[m['team1']]['points']
            m['team2_score'] = team_group_score[m['team2']]['points']
        if printing:
            print(m)
            model.print(teams)

        results[code] = m
    return results, team_group_score

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

def print_results(results, matches, groups, teams, team_group_score):
    print("Date       |    Code    | Pool | Team1             | Team2             | Score | Winner             |")
    for m in matches:
        code = m['match']
        match = results[code]
        gd = match['gd']
        team1 = match['team1']
        team2 = match['team2']
        winner = ''
        if not match['pool']:
            winner = team1 if gd>0 else team2
        print("{:^11}|{:^12}|{:^6}|{:^19}|{:^19}|{:^7}|{:^19}".format(
            m['date'], code, match['pool'], team1, team2, gd, winner)
        )
    print()

def print_team_score(team_score, n_tir):
    keys = False
    for t, v in team_score.items():
        if not keys:
            keys = list(v.keys())
            print("{:^20}|".format("Teams"), end='')
            [print("{:^5}|".format(k), end='') for k in keys]
            [print("{:^7}|".format("p"+ k), end='') for k in keys]
            [print("{:^7}|".format("c"+ k), end='') for k in keys]
            print()
        print("{:^20}|".format(t), end='')
        [print("{:^5d}|".format(v[k]), end='') for k in keys]
        [print("{:^7.1f}|".format(v[k]/n_tir * 100), end='') for k in keys]
        [print("{:^7.1f}|".format(n_tir / v[k] if v[k] > 0 else 0), end='') for k in keys]
        print()

def print_pool_result_stats(stats, n_tir):
    print("Date       |    Code    | Team1             | Team2             |  1  |  N  |  2  |  p1   |  pN   |  p2   |  c1   |  cN   |  C2   |  1G   |  2G   |")
    for code, match in stats.items():
        team1 = match['team1']
        team2 = match['team2']
        m1, mn, m2 = match['1'], match['N'], match['2']
        g1, g2 = match['1GD'], match['2GD']
        print("{:^11}|{:^12}|{:^19}|{:^19}|{:^5}|{:^5d}|{:^5d}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|".format(
            match['date'], code, team1, team2, m1, mn, m2,
            100 * m1/n_tir, 100 * mn / n_tir, 100 * m2/n_tir,
            n_tir / m1 if m1 > 0 else 0, n_tir / mn  if mn > 0 else 0, n_tir / m2 if m2 > 0 else 0,
            g1 / m1 if m1 > 0 else 0, g2 / m2 if m2 > 0 else 0)
        )
    print()


def print_pool_result_stats(stats, n_tir):
    print("Date       |    Code    | Team1             | Team2             |  1  |  N  |  2  |  p1   |  pN   |  p2   |  c1   |  cN   |  C2   |  1G   |  2G   |")
    for code, match in stats.items():
        team1 = match['team1']
        team2 = match['team2']
        m1, mn, m2 = match['1'], match['N'], match['2']
        g1, g2 = match['1GD'], match['2GD']
        print("{:^11}|{:^12}|{:^19}|{:^19}|{:^5}|{:^5d}|{:^5d}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|{:^7.1f}|".format(
            match['date'], code, team1, team2, m1, mn, m2,
            100 * m1/n_tir, 100 * mn / n_tir, 100 * m2/n_tir,
            n_tir / m1 if m1 > 0 else 0, n_tir / mn  if mn > 0 else 0, n_tir / m2 if m2 > 0 else 0,
            g1 / m1 if m1 > 0 else 0, g2 / m2 if m2 > 0 else 0)
        )
    print()



def print_group_winner_stats(winners, n_tir, groups):
    for group in "ABCDEFGH":
        countries = sorted(groups[group])
        print("Group {:^2}{:^8}|{:^18}|{:^18}|{:^18}|{:^18}|".format(group, "", *countries))
        for i in range(2):
            print("{:^8}{:^8}|".format("", "First" if i == 0 else "Second"), end='')
            for country in countries:
                s = winners[i][group][country]
                print("{:^6d}{:^6.0f}{:^6.1f}|".format(s, 100 * s / n_tir, n_tir / s if s > 0 else 0), end='')
            print()

    print()


# Programme Principal
n_buckets = 6
rho = 0.5
bucket_per_gd = 1

teams = data_2018.teams()
matches = data_2018.matches()
match_codes = data_2018.match_codes()
given = data_2018.results()
groups = data_2018.groups()
n_people = len(teams)

elo_scores = data_2018.elo_scores()
#elo_scores = data_2018.fifa_scores()
max_elo_score = max(elo_scores.values())
min_elo_score = min(elo_scores.values())
delta_elo = max_elo_score - min_elo_score
mean_elo = (max_elo_score + min_elo_score) / 2.0
# On repositionne linéirement les Ecarts en fonction du ELO

# ELO Ai calculé que 500 points correspondent à 3 points d'ecart au total
elo_scores = {k: (v - mean_elo) * 3 / 500 for k,v in elo_scores.items()}

# FIFA Scores Ai calculé que 500 points correspondent à 3 points d'ecart au total
#elo_scores = {k: (v - mean_elo) * 3 / 1100 for k,v in elo_scores.items()}

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

model = ModelBayesFast(n_people, n_buckets, s_max=floor((2 * n_buckets + 1) / bucket_per_gd) + 1, options={'rho': rho, 'bucket_per_gd': bucket_per_gd})
# récupère les etats historiques
model.probabilities = [np.array(list(probabilities[teams[i]].values())) for i in range(len(model.probabilities))]
model.update_stats()
model.adjust_mean()
#model.print(teams)

probabilities = model.probabilities.copy()

team_score = {team: {"1": 0, "1M": 0, "2": 0, "4": 0, "8": 0, "q8": 0} for team in teams}
pool_match_stats = {m['match'] : {'date': m['date'], 'team1':m['team1'], 'team2':m['team2'], '1':0, 'N':0, '2':0, '1GD':0, '2GD':0}
                  for m in matches if ord(m['match'][0]) > 64}
post_pool_match_stats = None

pool_winner_stats = [{group: {country:0 for country in countries} for group, countries in groups.items()} for _ in range(2)]
n_tir = 0
for _ in range(10000):
    n_tir += 1
    print("Shot n:{}".format(n_tir))
    model.probabilities = probabilities.copy()
    model.update_stats()
    results, team_group_score = fire_once(model,teams, groups, matches, match_codes, given)
    if post_pool_match_stats is None:
        post_pool_match_stats = {
            m['match']: {'date': m['date'], 'team1': results[m['match']]['team1'], 'team2': results[m['match']]['team2'],
                         '1': 0, 'N': 0, '2': 0, '1GD': 0, '2GD': 0}
            for m in matches if m['match'][0] == '8'}


    #print_results(results, matches, groups, teams, team_group_score)
    #model.print(teams)
    team1, team2 = results["1"]['team1'], results["1"]['team2']
    gd = results["1"]['gd']
    winner = team1 if gd > 0 else team2
    print("Finale {} / {} : {} Winner {}".format(team1, team2, gd, winner))
    # Mise à jour des résultats post-poules
    for code, m in results.items():
        c = code[0]
        if ord(c)<65:
            if c == "8":
                # Les équipes ont passé les pool
                team_score[m['team1']]['q8'] += 1
                team_score[m['team2']]['q8'] += 1
                group1, group2 = code[1], code[2]
                pool_winner_stats[0][group1][m['team1']] += 1
                pool_winner_stats[1][group2][m['team2']] += 1
            if code == '1M':
                c = '1M'
            team_score[m['winner']][c] += 1
    # Mise à jour des statistiques de matches de Poules
    for code, m in results.items():
        if ord(code[0]) < 65:
            continue
        if m['gd'] > 0:
            pool_match_stats[code]['1'] += 1
            pool_match_stats[code]['1GD'] += m['gd']
        elif m['gd'] < 0:
            pool_match_stats[code]['2'] += 1
            pool_match_stats[code]['2GD'] -= m['gd']
        else:
            pool_match_stats[code]['N'] += 1

    # Mise à jour des statistiques de matches post Pools
    for code, m in results.items():
        if code[0] != '8':
            continue
        if m['gd'] > 0:
            post_pool_match_stats[code]['1'] += 1
            post_pool_match_stats[code]['1GD'] += m['gd']
        elif m['gd'] < 0:
            post_pool_match_stats[code]['2'] += 1
            post_pool_match_stats[code]['2GD'] -= m['gd']
        else:
            post_pool_match_stats[code]['N'] += 1

#model.print(teams)
print_team_score(team_score, n_tir)
#print_pool_result_stats(pool_match_stats, n_tir)
print_pool_result_stats(post_pool_match_stats, n_tir)
#print_group_winner_stats(pool_winner_stats, n_tir, groups)
