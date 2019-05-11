from os import popen

import click


@click.group()
def cli():
    pass


@cli.command()
def scan():
    command = "netstat -op 2> /dev/null | grep Dofus.exe | grep personal-agent | awk '{print $4}' | awk -F':' '{print $2}'"
    out = popen(command)
    for line in out:
        line = line.replace('\n', '')
        print("Dofus is running on port : " + line)


if __name__ == "__main__":
    cli()
