from math import floor
import data_2018
from modelbayes import ModelBayes
from modelbayesfast import ModelBayesFast

def account_for_history(model, matches, teams):
    numbered_teams ={team: number for number,team in enumerate(teams)}
    for i, match in enumerate(matches):
        if ord(match['match'][0]) < 65:
            continue
        print(i, end='')
        l1 = numbered_teams[match['w_team1']]
        l2 = numbered_teams[match['w_team2']]
        if 'gd' in match:
            score = match['gd']
        else:
            score = -2
        model.account_for((l1, l2, score))
        #model.print(teams)
    print()

# Programme Principal
n_buckets = 6
rho = 0.5
bucket_per_gd = 1

teams = data_2018.teams()
matches = data_2018.matches()
match_codes = data_2018.match_codes()
n_people = len(teams)

model = ModelBayes(n_people, n_buckets, s_max=floor((2 * n_buckets + 1) / bucket_per_gd) + 1, options={'rho': rho, 'bucket_per_gd': bucket_per_gd})
account_for_history(model, matches, teams)

model_fast = ModelBayesFast(n_people, n_buckets, s_max=floor((2 * n_buckets + 1) / bucket_per_gd) + 1, options={'rho': rho, 'bucket_per_gd': bucket_per_gd})
account_for_history(model_fast, matches, teams)

model.print(teams)
model_fast.print(teams)
