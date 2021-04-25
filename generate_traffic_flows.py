import random


number_of_files = 3

def generate_data(file):
    with open(file, 'r') as f:
        for line in f:
            if line[:17] == '<NUMBER OF ZONES>':
                zones = int(line.split('>')[1])
            if line[0] == '~':
                break

    k = 0
    while k < number_of_files:
        f = open(f'demand{k}', 'w')
        f.write('origin\tdest\tdemand')
        for i in range(1, zones+1):
            for j in range(1, zones+1):
                if i == j:
                    continue
                f.write(f'i\tj\t{random.randint(10*i*j, 10000)}\n')
        f.close()
        k += 1


if __name__ == '__main__':
    generate_data('city/sioux_fals_trips.dat')