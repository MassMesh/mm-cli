from argh import ArghParser, dispatch

from . import (
  client,
  gateway
)

parser = ArghParser(description='MassMesh CLI tool')
parser.add_commands(client.cmd, namespace='cl', title='client configuration')
parser.add_commands(gateway.cmd, namespace='gw', title='gateway configuration')

def main():
    try:
        dispatch(parser)
    except KeyboardInterrupt as e:
        pass


if __name__ == '__main__':
    main()
