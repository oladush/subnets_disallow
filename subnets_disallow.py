#    /\________/\
#   /,,◕　⋏　◕,,\   usage: python3 subnets_disallow.py -o 0.0.0.0/0 -e 192.168.0.0/24 8.8.8.8/32
#   |     ---     |

import ipaddress as ip
from argparse import ArgumentParser


def remove_excess(subnets_: list[ip.IPv4Network]) -> list[ip.IPv4Network]:
    # remove duplicates
    subnets = list(set(subnets_))

    # search and remove subnets who include to other subnet
    exclude_indexes = set()
    for i in range(len(subnets)):
        for j in range(len(subnets)):
            if i != j and subnets[i].supernet_of(subnets[j]):
                exclude_indexes.add(j)

    for index in sorted(exclude_indexes, reverse=True):
        del subnets[index]

    return subnets


def try_merge(sub1: ip.IPv4Network, sub2: ip.IPv4Network) -> ip.IPv4Network:
    if sub1 > sub2:
        sub1, sub2 = sub2, sub1

    first_ip = sub1.network_address
    last_ip = sub2.broadcast_address

    nets = list(ip.summarize_address_range(first_ip, last_ip))

    if len(nets) == 1:
        return nets[0]


def try_merge_all(subnets: list[ip.IPv4Network], ind=0) -> list[ip.IPv4Network]:
    if ind == len(subnets) - 1:
        return remove_excess(subnets)

    for i in range(len(subnets)):
        if i != ind and (m := try_merge(subnets[ind], subnets[i])):
            if m not in subnets:
                return try_merge_all(subnets + [m], ind + 1)

    return try_merge_all(subnets, ind + 1)


def exclude(orig: list[ip.IPv4Network], excl: list[ip.IPv4Network]):
    res = []

    flag = 0
    for orig_net in orig:
        for excl_net in excl:
            if orig_net.supernet_of(excl_net):
                res += list(orig_net.address_exclude(excl_net))
                flag = 1
            elif excl_net.supernet_of(orig_net):
                flag = 1

        if not flag:
            res.append(orig_net)
        flag = 0

    return remove_excess(res)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog='subnets_disallow.py',
        description="Exclude some ip or ip ranges from subnets",
    )
    parser.add_argument('-o', nargs='+', help='enter here original subnets', metavar='subnet', required=True, dest='orig')
    parser.add_argument('-e', nargs='+', help='enter here subnets for exclude', metavar='subnet', required=True, dest='excl')

    args = parser.parse_args()

    print('original subnets:\n', ', '.join(args.orig))
    print('subnets for exclude:\n', ', '.join(args.excl))

    orig_blocks = remove_excess([ip.ip_network(s) for s in args.orig])
    excl_blocks = remove_excess([ip.ip_network(s) for s in args.excl])

    orig_merged = try_merge_all(orig_blocks)
    excl_merged = try_merge_all(excl_blocks)

    res = exclude(orig_merged, excl_merged)

    print('result:\n', ', '.join([str(s) for s in sorted(res)]))
