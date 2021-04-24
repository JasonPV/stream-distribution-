def rewrite_network(file):
    outfile = open('network.dat', 'w')
    header = 'origin\tdest\tcapacity\tlength\tfft\talpha\tbeta\tspeedLimit'
    outfile.write(header+'\n')
    with open(file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            if line.split()[0] == '~':
                break
        for line in f:
            line = line.split()[:8]
            line = '\t'.join(line)
            outfile.write(line+'\n')
    outfile.close()


def rewrite_demand(file):
    outfile = open('demand.dat', 'w')
    header = 'origin\tdest\tdemand'
    outfile.write(header+'\n')
    with open(file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            if line.split()[0] == 'Origin':
                k = line.split()[1]
                break

        for line in f:
            if not line.strip():
                continue
            if line.split()[0] == 'Origin':
                k = line.split()[1]
            else:
                line = line.split(';')[:-1]
                for el in line:
                    buf = el.split(':')
                    if k == buf[0].strip():
                        continue
                    else:
                        outfile.write(k+'\t'+buf[0].strip()+'\t'+buf[1].strip()+'\n')



if __name__ == '__main__':
    rewrite_network('city/sioux_fals_net.dat')
    rewrite_demand('city/sioux_fals_trips.dat')
