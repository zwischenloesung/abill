#!/usr/bin/env python3

import click
from glob import glob
import os

@click.command()
@click.option('--end_marker', '-e', type=str, default='%', help='The closing marker to denote a variable in the template (e.g. "%FirstName%"; default: "%"; only valid if jinja2 is NOT used).')
@click.option('--include', '-I', type=str, multiple=True, help='Arbitrary additional files to copy to the target dir, supports wildcards too.')
@click.option('--jinja', '-J', is_flag=True, help='Use the mighty jinja2 engine to do the work (otherwise just the keywords are replaced).')
@click.option('--link', '-l', type=str, multiple=True, help='Arbitrary additional soft-links to create to the target dir, supports wildcards too.')
@click.option('--dry_run', '-n', is_flag=True, help='Show what would be done, but do not change anything...')
@click.option('--output_directory', '-o', type=str, help='Directory to put the output documents into.')
@click.option('--template', '-t', type=str, multiple=True, help='Arbitrary number of files to edit as the document, supports wildcards too.')
@click.option('--template_mapping', '-T', type=str, default=[ "firstName:N:1", "lastName:N:0", "streetAddress:ADR;TYPE=HOME:2", "postalCodeAddress:ADR;TYPE=HOME:5", "cityAddress:ADR;TYPE=HOME:3", "countryAddress:ADR;TYPE=HOME:6" ], multiple=True, help='Arbitrary number of mappings from string in template to vcard-field (default: "firstName:N[:1]"; the third part optional and only for fields that have more then one value).')
@click.option('--template_mapping_separator', '-S', type=str, default=':', help='A character separating the key from the value in template_mapping (only valid if NOT jinja2; default: ":").')
@click.option('--tex2pdf', '-p', is_flag=True, help='Assume the resulting document is written in TeX and try to convert it to PDF')
@click.option('--start_marker', '-s', type=str, default='%', help='The opening marker to denote a variable in the template (e.g. "%FirstName%"; default: "%"; only valid if jinja2 is NOT used).')
@click.option('--vcf', '-V', type=str, help='The vcards file(s) to get the personalized infos from (wildcards supported).')
def main(end_marker, include, jinja, link, dry_run, output_directory, template, template_mapping, template_mapping_separator, tex2pdf, start_marker, vcf):
    """
    Sometimes it is just necessary to create a series of documents with
    common content but still personalized or slightly customized.

    Not everyone wants to use LibreOffice or the like for such a task.
    What if you already have a nice LaTeX letter and a list of contacts
    in your contact book, exportable as vcf?

    This little piece of software let's you do it your way.

    Example:
      python -m main -n -V tests/com_example_crm.vcf -T "firstName:N:1" -T "lastName:N:0"
    """
    contacts = []
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
            vcf_file_list.append(f)
    else:
        click.error("Please provide a vcard file.")
        raise SystemExit

    template_mapping_map = create_mapping(template_mapping, template_mapping_separator, start_marker, end_marker)

    contacts = parse_contacts(template_mapping_map, vcf_file_list)

    if dry_run:
        print_contacts(contacts)
    else:
        pass
        #organize_output(output_directory)

        if flavor == "TeX":
            pass

def print_contacts(contacts):
    """
    Just pretty print an overview.
    """
    click.secho("The following (" + str(len(contacts)) + ") contacts were imported:", fg='green')
    for c in contacts:
        click.echo("---")
        for f in c:
            click.echo("  " + f + ": " + c[f])

def parse_contacts(template_mapping_map, vcf_file_list) -> list:
    """
    Parse the .vcf files, only looking for the values of interest, that were collected in the
    mapping.
    """
    contacts = []
    for cf in vcf_file_list:
        with open(cf, 'r') as f:
            state = None
            i = 0
            for line in f:
                i += 1
                line = line[0:-1]
                if not state and line == "BEGIN:VCARD":
                    state = "vcard"
                    contact = {}
                elif state and line == "END:VCARD":
                    state = None
                    contacts.append(contact)
                elif state:
                    for mapping in template_mapping_map:
                        if line.startswith(template_mapping_map[mapping]["name"] + ":"):
                            nl = line.split(":", 1)
                            if template_mapping_map[mapping]["part"]:
                                nl = nl[1].split(";")
                                contact[mapping] = nl[int(template_mapping_map[mapping]["part"])]
                            else:
                                contact[mapping] = nl[1]
                else:
                    click.secho("WARNING: Unexpected content on line `" + i + "`:")
                    click.echo(line)
    return contacts


def create_mapping(template_mapping, template_mapping_separator, start_marker, end_marker) -> map:
    """
    Use the custom mapping provided on the CLI (or the default) to map the contents of the vcards
    in the .vcf to the keywords in the template.
    """
    template_mapping_map = {}
    for m in template_mapping:
        tm = m.split(template_mapping_separator)
        if len(tm) == 2:
            template_mapping_map[start_marker + tm[0] + end_marker] = { "name": tm[1] }
        elif len(tm) >= 2:
            template_mapping_map[start_marker + tm[0] + end_marker] = { "name": tm[1], "part": tm[2] }
        else:
            click.secho("ERROR: Could not parse the template_mapping", fg='red')
            raise SystemExit
    return template_mapping_map

def organize_output(output_directory):
    try:
        os.makedirs(output_directory)
    except FileExistsError:
        pass


def parse_vcf(filename, addresslist=[]) -> list:
    return addresslist

if __name__ == '__main__':
    main()

