from argparse import ArgumentParser

def parse_server():
    parser = ArgumentParser(description = 'DHT server')
    parser.add_argument('--verbose', '-v', action = 'count')
    parser.add_argument('--address', '-a', required = True, help = 'ethernet interface addres', metavar='x.x.x.x')
    parser.add_argument('--port', '-p', required = True, help = 'TCP port number', type = int)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_server()
    print args
