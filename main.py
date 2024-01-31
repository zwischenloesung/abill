#!/usr/bin/env python3

import click
from glob import glob

@click.command()
@click.option('--include', '-I', type=str, multiple=True, help='Arbitrary number of files to include and edit as the document, supports wildcards too.')
@click.option('--add', '-A', type=str, multiple=True, help='Arbitrary additional files to copy to the target dir, supports wildcards too.')
@click.option('--link', '-L', type=str, multiple=True, help='Arbitrary additional soft-links to create to the target dir, supports wildcards too.')
@click.option('--vcf', '-V', type=str, help='The vcards file(s) to get the personalized infos from (wildcards supported).')
def main(vcf, include, add, link):
    """
    Sometimes it is just necessary to create a series of documents with
    common content but still personalized or slightly customized.

    Not everyone wants to use LibreOffice or the like for such a task.
    What if you already have a nice LaTeX letter and a list of contacts
    in your contact book, exportable as vcf?

    This little piece of software let's you do it your way.
    """
    in_file_list = []
    vc_file_list = []
    for i in include:
        for f in glob(i):
            in_file_list.append(f)
    for a in add:
        print(a)
    for l in link:
        print(l)
    if vcf:
        for f in glob(vcf):
            vc_file_list.append(f)
    else:
        click.echo("Please provide a vcard file.")
        raise SystemExit

def parse_vcf(filename, addresslist=[]) -> list:
    return addresslist

if __name__ == '__main__':
    main()

