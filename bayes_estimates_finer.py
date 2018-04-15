import matplotlib.pyplot as plt
import itertools as it
import csv
from math import sqrt, floor
import random

class Model_base:
    def __init__(self, n_people, n_buckets, s_max, options):
        self.n_people = n_people
        self.n_buckets = n_buckets
        self.proba_win_function = self.compute_probability_function(n_buckets, s_max, options)
        self.s_max = s_max
        self.options = options
        self.initializor = {i: 1/(2*n_buckets + 1) for i in range(-n_buckets, n_buckets + 1)}
        self.probabilities = [self.initializor.copy() for _ in range(n_people)]
        self.update_stats()

    def compute_probability_function(self, n_buckets, s_max, options):
        rho = options['rho']
        bpgd= options['bucket_per_gd']
        triplet = {(l1, l2,s): max(rho ** abs((l1 - l2)/bpgd - s), 0.01)
                   for l1 in range(-n_buckets, n_buckets + 1)
                   for l2 in range(-n_buckets, n_buckets + 1)
                   for s in range(-s_max, s_max + 1)}
        #centror = options['centror']
        sums = {(l1,l2):0
                for l1 in range(-n_buckets, n_buckets + 1)
                for l2 in range(-n_buckets, n_buckets + 1)}
        for (l1, l2, _), p in triplet.items():
            sums[(l1, l2)] += p
        triplet = {(l1, l2, s): v / sums[(l1,l2)] for (l1, l2, s), v in triplet.items()}
        return triplet

    def proba_win(self, level_user1, level_user2, score):
        if abs(score) > self.s_max:
            return 0.005
        return self.proba_win_function[level_user1, level_user2, score]

    def update_stats(self):
        self.esperance = [sum(bucket * self.probabilities[people][bucket] for bucket in range(-n_buckets, n_buckets + 1))
                          for people in range(n_people)]
        self.mean = sum(self.esperance) / len(self.esperance)

    def adjust_mean(self):
        self.mean = sum(self.esperance) / len(self.esperance)
        for people, probability in enumerate(self.probabilities):
            for bucket, p in probability.items():
                if bucket != 0:
                    self.probabilities[people][bucket] -= self.mean / bucket

    def proba_score(self,user_1, user_2):
        return {
            s: sum(self.proba_win(i, j, s)* self.probabilities[user_1][i] * self.probabilities[user_2][j]
            for i in range(-self.n_buckets, self.n_buckets + 1) for j in range(-self.n_buckets, self.n_buckets + 1))
            for s in range(-self.s_max, self.s_max + 1)
        }

    def print(self, teams, keep=set()):
        print("Team          ", end="")
        print("  #  ", end="")
        for bucket in range(-self.n_buckets, self.n_buckets + 1):
            print("{0:^4} | ".format(bucket), end='')
        print()
        for people in range(self.n_people):
            if len(keep)>0 and people not in keep:
                continue
            total = 0
            average = 0
            print("{0:^14}".format(teams[people]), end="")
            print("{0:^5}".format(people), end="")
            for bucket in range(-self.n_buckets, self.n_buckets + 1):
                print("{0:^4.1f} | ".format(100 * self.probabilities[people][bucket]), end='')
                total += 100 * self.probabilities[people][bucket]
                average += self.probabilities[people][bucket] *  bucket
            print("{0:^4.1f} | ".format(total), end='')
            print("{0:^4.1f} | ".format(average), end='')
            print()

    def write_csv(self, filename, min_number):
        with open(filename, 'w', newline='') as csvfile:
            result_writer = csv.writer(csvfile, delimiter=';')
            result_writer.writerow(['People', 'Bucket', 'Reliability', 'Bucket0', 'Bucket1'])
            for people in range(self.n_people):
                result_writer.writerow([people+min_number,
                                        str(self.buckets[people]).replace('.',','),
                                        str(self.reliabilities[people][1]).replace('.',','),
                                        str(self.buckets_reliability[people][0]).replace('.',','),
                                        str(self.buckets_reliability[people][1]).replace('.',',')])

    def account_for(self, d):
        user_1,user_2, score = d

        probabilities = {
            (i, j): self.proba_win(i, j, score)* self.probabilities[user_1][i] * self.probabilities[user_2][j]
            for i in range(-self.n_buckets, self.n_buckets + 1) for j in range(-self.n_buckets, self.n_buckets + 1)}
        # normalize
        s = sum(v for v in probabilities.values())
        probabilities = { k: v/s for k,v in probabilities.items()}

        # accumulate probabilities per user
        probabilities_cumulated = [{i:0 for i in range(-self.n_buckets, n_buckets + 1)} for _ in range(2)]
        for (i,j),p in probabilities.items():
            probabilities_cumulated[0][i] += p
            probabilities_cumulated[1][j] += p
        self.probabilities[user_1] = probabilities_cumulated[0]
        self.probabilities[user_2] = probabilities_cumulated[1]
        self.update_stats()

def draw_ps(ps):
    return random.choices(list(ps.keys()), weights=list(ps.values()))[0]

def print_p(proba, threshold=0.02):
    print("Probabilities by score")
    [print("{:^5d}|".format(i), end='') for i,p in proba.items() if p>threshold]
    print()
    [print("{:^5.0f}|".format(p * 100), end='') for i,p in proba.items() if p>threshold]
    print()


def ordered_match(n_people):
    return [ (user_1, user_2, 1 if user_1>user_2 else -1) for user_1 in range(n_people) for user_2 in range(n_people) if user_1 != user_2]

def partial_ordered_match(n_people):
    return [ (user_1, user_2, 1 if user_1>user_2 else -1) for user_1 in range(n_people) for user_2 in range(n_people) if user_1 < user_2]

n_people = 20
n_buckets = 6
rho = 0.5
bucket_per_gd = 1

model = Model_base(n_people, n_buckets, s_max=floor((2*n_buckets+1)/bucket_per_gd)+1, options={'rho': rho, 'bucket_per_gd': bucket_per_gd} )
'''
matches = [(0,1, 1), (0,2, 1), (1,2, 1), (1,2, 1), (1,2, 1) ]
matches = ordered_match(n_people)
matches = [(0,1, 1), (0,2, 1), (1,2, 1), (1,2, 1), (1,2, 1) ]
'''
import matches_ligue1
matches = matches_ligue1.matches()
teams = matches_ligue1.team()
#model.print(teams)
filtered = set()
for i, match in enumerate(matches):
    l1, l2, score = match
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
        model.print(teams)
        print(model.mean)


ps = model.proba_score(14,19)
print_p(ps)
