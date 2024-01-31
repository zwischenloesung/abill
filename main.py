#!/usr/bin/env python3

import click
from glob import glob
import os

@click.command()
@click.option('--end_marker', '-e', type=str, default='%', help='The closing marker to denote a variable in the template (e.g. "%FN%")')
@click.option('--flavor', '-F', type=str, default='TeX?', help='If the template is `TeX`, and you say so here,an attempt to transform it directly to PDF will be made.')
@click.option('--include', '-I', type=str, multiple=True, help='Arbitrary additional files to copy to the target dir, supports wildcards too.')
@click.option('--link', '-l', type=str, multiple=True, help='Arbitrary additional soft-links to create to the target dir, supports wildcards too.')
@click.option('--dry_run', '-n', type=bool, help='Do not really change anything...')
@click.option('--output_directory', '-o', type=str, help='Directory to put the output documents into.')
@click.option('--template', '-t', type=str, multiple=True, help='Arbitrary number of files to edit as the document, supports wildcards too.')
@click.option('--start_marker', '-s', type=str, default='%', help='The opening marker to denote a variable in the template (e.g. "%FN%")')
@click.option('--vcf', '-V', type=str, help='The vcards file(s) to get the personalized infos from (wildcards supported).')
def main(end_marker, flavor, include, link, dry_run, output_directory, template, start_marker, vcf):
    """
    Sometimes it is just necessary to create a series of documents with
    common content but still personalized or slightly customized.

    Not everyone wants to use LibreOffice or the like for such a task.
    What if you already have a nice LaTeX letter and a list of contacts
    in your contact book, exportable as vcf?

    This little piece of software let's you do it your way.
    """
    include_file_list = []
    template_file_list = []
    template_file_list = []
    vcf_file_list = []
    for i in include:
        for f in glob(i):
            include_file_list.append(f)
    for t in template:
        for f in glob(t):
            template_file_list.append(f)
    for l in link:
        for f in glob(l):
            link_file_list.append(f)
    if vcf:
        for f in glob(vcf):
            vc_file_list.append(f)
    else:
        click.echo("Please provide a vcard file.")
        raise SystemExit

    if not dry_run:
        organize_output(output_directory)

        if flavor == "TeX":
            pass

def organize_output(output_directory):
    try:
        os.makedirs(output_directory)
    except FileExistsError:
        pass


def parse_vcf(filename, addresslist=[]) -> list:
    return addresslist

if __name__ == '__main__':
    main()

