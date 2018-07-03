import random
import statistics
import numpy as np


class ModelBayesFast:
    def __init__(self, n_people, n_buckets, s_max, options):
        self.n_people = n_people
        self.n_buckets = n_buckets
        self.buckets = np.arange(-n_buckets, n_buckets + 1)
        self.buckets_total = 2 * n_buckets + 1
        self.s_max = s_max
        self.s_max_total = 2 * s_max + 1
        self.scores = np.arange(-s_max, s_max + 1)
        self.options = options
        self.proba_table = self.compute_proba_table(n_buckets, s_max, options)
        self.initializor = {i: 1/(2*n_buckets + 1) for i in range(-n_buckets, n_buckets + 1)}
        self.probabilities = [ 1/self.buckets_total * np.ones((self.buckets_total,)) for _ in range(n_people)]
        self.esperance = []
        self.mean = 0
        self.update_stats()

    def compute_proba_table(self, n_buckets, s_max, options):
        def fn(l1, l2, s, rho, bpgd):
            ecart = int(abs((l1 - l2)/bpgd - s))
            if ecart > 5:
                return 0.000001
            return [24, 22, 10, 4.5, 1.5, 0.5][ecart]
        rho = options['rho']
        bpgd = options['bucket_per_gd']
        triplet = {(l1, l2, s): max(fn(l1, l2, s, rho, bpgd), 0.0000001) if abs(l1 - l2 - s) < 6 else 0.0000001
                   for l1 in range(-n_buckets, n_buckets + 1)
                   for l2 in range(-n_buckets, n_buckets + 1)
                   for s in range(-s_max, s_max + 1)}
        sums = {(l1, l2): 0
                for l1 in range(-n_buckets, n_buckets + 1)
                for l2 in range(-n_buckets, n_buckets + 1)}
        for (l1, l2, _), p in triplet.items():
            sums[(l1, l2)] += p
        triplet = {(l1, l2, s): v / sums[(l1, l2)] for (l1, l2, s), v in triplet.items()}
        np_triplet = np.zeros((self.s_max_total, self.buckets_total, self.buckets_total))
        for (l1, l2, s), v in triplet.items():
            np_triplet[s + self.s_max][l1 + self.n_buckets][l2 + self.n_buckets] = v
        return np_triplet

    def update_stats(self):
        self.esperance = [np.sum(self.buckets * self.probabilities[people]) for people in range(self.n_people)]
        self.mean = statistics.mean(self.esperance)

    def adjust_mean(self):
        shift = round(self.mean)
        if shift == 0:
            return
        for people, probability in enumerate(self.probabilities):
            new_values = np.zeros(probability.shape)
            l = len(new_values)
            self.probabilities[people][:l - shift] = new_values[shift:]
            self.probabilities[people][l - shift:] = new_values[:shift]
        self.update_stats()

    def proba_score(self, user_1, user_2):
        p_user1 = self.probabilities[user_1]
        p_user1.shape = (len(p_user1), 1)
        p_user2 = self.probabilities[user_2]
        return {
            s: np.sum(self.proba_table[s + self.s_max] * p_user1 * p_user2) for s in range(-self.s_max, self.s_max + 1)
        }

    def print(self, teams, keep=set()):
        print("Team                     |", end="")
        print("  #  |", end="")
        for bucket in range(-self.n_buckets, self.n_buckets + 1):
            print("{0:^4} | ".format(bucket), end='')
        print()
        for people in range(self.n_people):
            if len(keep) > 0 and people not in keep:
                continue
            total = 0
            average = 0
            print("{0:^25}|".format(teams[people]), end="")
            print("{0:^5}|".format(people), end="")
            for bucket in range(-self.n_buckets, self.n_buckets + 1):
                print("{0:^4.1f} | ".format(100 * self.probabilities[people][bucket + self.n_buckets]), end='')
                total += 100 * self.probabilities[people][bucket + self.n_buckets]
                average += self.probabilities[people][bucket + self.n_buckets] * bucket
            print("{0:^4.1f} | ".format(total), end='')
            print("{0:^4.1f} | ".format(average), end='')
            print()
        print("Mean {:.2f}".format(self.mean))

    def account_for(self, d):
        user_1, user_2, score = d
        p_user1 = self.probabilities[user_1]
        p_user1.shape = (len(p_user1), 1)
        p_user2 = self.probabilities[user_2]
        probabilities = self.proba_table[score + self.s_max] * p_user1 * p_user2
        # normalize
        s = np.sum(probabilities)
        probabilities = probabilities / s
        # accumulate probabilities per user
        self.probabilities[user_1] = np.sum(probabilities, axis = 1)
        self.probabilities[user_2] = np.sum(probabilities, axis = 0)
        self.update_stats()
        self.adjust_mean()


def draw_ps(ps):
    return random.choices(list(ps.keys()), weights=list(ps.values()))[0]

'''
    r = random.random()
    s, t = 0, 0
    for s, p in ps.items():
        t += p
        if t > r:
            return s
    return s
'''

def print_p(proba, threshold=0.02):
    print("Probabilities by score")
    [print("{:^5d}|".format(i), end='') for i, p in proba.items() if p > threshold]
    print()
    [print("{:^5.0f}|".format(p * 100), end='') for i, p in proba.items() if p > threshold]
    print()
