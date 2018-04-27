import random
import statistics


class ModelBayes:
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
        def fn(l1, l2, s, rho, bpgd):
            ecart = abs((l1 - l2)/bpgd - s)
            if ecart <= 0.5:
                return 24
            if ecart <= 1.5:
                return 22
            if ecart <= 2.5:
                return 10
            if ecart <= 3.5:
                return 4.5
            if ecart <= 4.5:
                return 1.4
            if ecart <= 5.5:
                return 0.5
            return 0.000001
        rho = options['rho']
        bpgd= options['bucket_per_gd']
        triplet = {(l1, l2,s): max(fn(l1, l2, s, rho, bpgd), 0.0000001) if abs(l1 - l2 - s) < 6 else 0.0000001
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
            return 0.00001
        return self.proba_win_function[level_user1, level_user2, score]

    def update_stats(self):
        self.esperance = [sum(bucket * self.probabilities[people][bucket] for bucket in range(-self.n_buckets, self.n_buckets + 1))
                          for people in range(self.n_people)]
        self.mean = statistics.mean(self.esperance)


    def adjust_mean(self):
        shift = round(self.mean)
        if shift == 0:
            return
        for people, probability in enumerate(self.probabilities):
            new_values = list(probability.values())
            new_values = new_values[shift:] + new_values[:shift]
            self.probabilities[people] = {k:new_values[i] for i,k in enumerate(probability.keys())}
        self.update_stats()


    def proba_score(self,user_1, user_2):
        return {
            s: sum(self.proba_win(i, j, s)* self.probabilities[user_1][i] * self.probabilities[user_2][j]
            for i in range(-self.n_buckets, self.n_buckets + 1) for j in range(-self.n_buckets, self.n_buckets + 1))
            for s in range(-self.s_max, self.s_max + 1)
        }

    def print(self, teams, keep=set()):
        print("Team                     ", end="")
        print("  #  ", end="")
        for bucket in range(-self.n_buckets, self.n_buckets + 1):
            print("{0:^4} | ".format(bucket), end='')
        print()
        for people in range(self.n_people):
            if len(keep)>0 and people not in keep:
                continue
            total = 0
            average = 0
            print("{0:^25}".format(teams[people]), end="")
            print("{0:^5}".format(people), end="")
            for bucket in range(-self.n_buckets, self.n_buckets + 1):
                print("{0:^4.1f} | ".format(100 * self.probabilities[people][bucket]), end='')
                total += 100 * self.probabilities[people][bucket]
                average += self.probabilities[people][bucket] *  bucket
            print("{0:^4.1f} | ".format(total), end='')
            print("{0:^4.1f} | ".format(average), end='')
            print()
        print("Mean {:.2f}".format(self.mean))

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
        probabilities_cumulated = [{i:0 for i in range(-self.n_buckets, self.n_buckets + 1)} for _ in range(2)]
        for (i,j),p in probabilities.items():
            probabilities_cumulated[0][i] += p
            probabilities_cumulated[1][j] += p
        self.probabilities[user_1] = probabilities_cumulated[0]
        self.probabilities[user_2] = probabilities_cumulated[1]
        self.update_stats()
        self.adjust_mean()

def draw_ps(ps):
    return random.choices(list(ps.keys()), weights=list(ps.values()))[0]

def print_p(proba, threshold=0.02):
    print("Probabilities by score")
    [print("{:^5d}|".format(i), end='') for i,p in proba.items() if p>threshold]
    print()
    [print("{:^5.0f}|".format(p * 100), end='') for i,p in proba.items() if p>threshold]
    print()

