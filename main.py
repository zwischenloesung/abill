#!/usr/bin/env python3

import click
from glob import glob
from datetime import datetime
import os
import re
import shutil
from unidecode import unidecode

def date(field):
    """
    Wrap datetime for shorter access.
    """
    n = datetime.now()
    if field == 'y':
        p = '{:%Y}'
    elif field == 'm':
        p = '{:%m}'
    elif field == 'd':
        p = '{:%d}'
    return p.format(n)

@click.command()
@click.option('--end_marker', '-e', type=str, default='%', help='The closing marker to denote a variable in the template (e.g. "%FirstName%"; default: "%"; only valid if jinja2 is NOT used).')
@click.option('--include', '-i', type=str, multiple=True, help='Arbitrary additional files to copy to the target dir, supports wildcards too.')
@click.option('--jinja', '-j', is_flag=True, help='Use the mighty jinja2 engine to do the work (otherwise just the keywords are replaced).')
@click.option('--link', '-l', type=str, multiple=True, help='Arbitrary additional soft-links to create to the target dir, supports wildcards too.')
@click.option('--dry_run', '-n', is_flag=True, help='Show what would be done, but do not change anything...')
@click.option('--output_directory', '-o', type=str, required=True, help='Directory to put the output documents into.')
@click.option('--template', '-t', type=str, multiple=True, help='Arbitrary number of files to edit as the document, supports wildcards too.')
@click.option('--template_mapping', '-T', type=str, default=[ "firstName:N:1", "lastName:N:0", "streetAddress:ADR;TYPE=HOME:2", "postalCodeAddress:ADR;TYPE=HOME:5", "cityAddress:ADR;TYPE=HOME:3", "countryAddress:ADR;TYPE=HOME:6" ], multiple=True, help='Arbitrary number of mappings from string in template to vcard-field (default: "firstName:N[:1]"; the third part optional and only for fields that have more then one value).')
@click.option('--template_mapping_separator', '-S', type=str, default=':', help='A character separating the key from the value in template_mapping (only valid if NOT jinja2; default: ":").')
@click.option('--template_mapping_unique', '-U', type=str, default=[ "N:0", "N:1" ], multiple=True, help='Select fields from the vcard in order to generate a unique identifier per contact (default: -U "N:0" -U "N:1"). Make sure it really is unique...')
@click.option('--template_filename_unique', '-u', is_flag=True, default=False, help='This flag only affects the name of files generated from templates and makes the filename itself unique by adding the contact-id (see `-U`) just before the suffix (or at the end if there is no ".").')
@click.option('--tex2pdf', '-p', is_flag=True, help='Assume the resulting document is written in TeX and try to convert it to PDF')
@click.option('--start_marker', '-s', type=str, default='%', help='The opening marker to denote a variable in the template (e.g. "%FirstName%"; default: "%"; only valid if jinja2 is NOT used).')
@click.option('--extra_field', '-x', type=str, multiple=True, default=[ 'dateYear:' + date('y'), 'dateMonth:' + date('m'), 'dateDay:' + date('d') ], help='Arbitrary number of additional extra fields that can be replaced in the template (default: "dateYear:' + date('y') + '", "dateMonth:' + date('m') + '", "dateDay:' + date('d') + '"')
@click.option('--vcf', '-V', type=str, required=True, help='The vcards file(s) to get the personalized infos from (wildcards supported).')
def main(end_marker, include, jinja, link, dry_run, output_directory, template, template_mapping, template_mapping_separator, template_mapping_unique, template_filename_unique, tex2pdf, start_marker, extra_field, vcf):
    """
    Sometimes it is just necessary to create a series of documents with
    common content but still personalized or slightly customized.

    Not everyone wants to use LibreOffice or the like for such a task.
    What if you already have a nice LaTeX letter and a list of contacts
    in your contact book, exportable as vcf?

    This little piece of software let's you do it your way.

    Example:
      python -m main -n -V tests/com_example_crm.vcf -T "firstName:N:1" -T "lastName:N:0" -o outputdir
    """
    include_file_list = []
    link_file_list = []
    template_file_list = []
    vcf_file_list = []
    for i in include:
        for f in glob(i):
            include_file_list.append(f)
    for t in template:
        for f in glob(t):
            template_file_list.append(f)
        if len(template_file_list) < 1:
            click.secho('Error: could not find a template file to edit', fg='red')
            raise SystemExit
    for l in link:
        for f in glob(l):
            link_file_list.append(f)
    if vcf:
        for f in glob(vcf):
            vcf_file_list.append(f)
        if len(vcf_file_list) < 1:
            click.secho('Error: could not find a vcards file to parse', fg='red')
            raise SystemExit
    else:
        click.error("Please provide a vcard file.")
        raise SystemExit

    template_mapping_map = map_keywords(template_mapping, template_mapping_separator)
    extra_mapping_map = add_extra_mapping(extra_field, {})

    contact_list = parse_contacts([], vcf_file_list, template_mapping_map, template_mapping_unique)

    if dry_run:
        print_contacts(contact_list)
    elif output_directory != None:
        create_output(output_directory, include_file_list, link_file_list, \
                template_file_list, contact_list, extra_mapping_map, \
                template_filename_unique, start_marker, end_marker)

def add_extra_mapping(extra_field, extra_map) -> dict:
    """
    Add custom extra fields to the template editing map.
    """
    for x in extra_field:
        s = x.split(":")
        if len(s) != 2:
            click.secho("Please check the input of `--extra_field`, '" + x + "' as it is not correct.'")
            raise SystemExit
        extra_map[s[0]] = s[1]
    return extra_map

def print_contacts(contacts):
    """
    Just pretty print an overview.
    """
    click.secho("The following (" + str(len(contacts)) + ") contacts were imported:", fg='green')
    for c in contacts:
        click.echo("---")
        for f in c:
            click.echo("  " + f + ": " + c[f])

def parse_contacts(contact_list, vcf_file_list, template_mapping_map, template_mapping_unique) -> list:
    """
    Parse the .vcf files, only looking for the values of interest, that were collected in the
    mapping.
    """
    uids = {}
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
                    contact_list.append(contact)
                elif state:
                    # first start to select all fields of interest
                    for mapping in template_mapping_map:
                        if line.startswith(template_mapping_map[mapping]["name"] + ":"):
                            nl = line.split(":", 1)
                            try:
                                if template_mapping_map[mapping]["part"]:
                                    nl = nl[1].split(";")
                                    contact[mapping] = nl[int(template_mapping_map[mapping]["part"])]
                            except KeyError:
                                contact[mapping] = nl[1]
                    # next parse the uid part provided by 'template_mapping_unique'
                    uid = ''
                    for unique in template_mapping_unique:
                        u = unique.split(":", 1)
                        if line.startswith(u[0] + ":"):
                            nl = line.split(":", 1)
                            nl = nl[1].split(";")
                            uid += '.' + nl[int(u[1])]
                    if uid != '':
                        uid = sanitize(uid[1:])
                        if uids.get(uid) != None:
                            click.secho('Error: The identifier "' + uid + '" is not UNIQUE, either the vcards file contains duplicates or you have chosen a wrong group of fields as UID (-U).', fg='red')
                            raise SystemExit
                        uids[uid] = ''
                        contact['uid'] = uid
                else:
                    click.secho("WARNING: Unexpected content on line `" + i + "`:")
                    click.echo(line)
    return contact_list

def sanitize(text, do_german_style=False) -> str:
    """
    Make sure we do not have strange chars in our uid. Replace at least some characters...
    """
    text = text.lower()
    if do_german_style:
        german_umlauts = {ord('ä'):'ae', ord('ö'):'oe', ord('ü'):'ue'}
        text = text.translate(trans)
    text = re.sub('\W+', '_', text)
    return unidecode(text)

def map_keywords(template_mapping, template_mapping_separator) -> dict:
    """
    Use the custom mapping provided on the CLI (or the default) to map the contents of the vcards
    in the .vcf to the keywords in the template.
    """
    template_mapping_map = {}
    for m in template_mapping:
        tm = m.split(template_mapping_separator)
        if len(tm) == 2:
            template_mapping_map[tm[0]] = { "name": tm[1] }
        elif len(tm) >= 2:
            template_mapping_map[tm[0]] = { "name": tm[1], "part": tm[2] }
        else:
            click.secho("ERROR: Could not parse the template_mapping", fg='red')
            raise SystemExit
    return template_mapping_map

def create_output(output_directory, include_file_list, link_file_list, \
        template_file_list, contact_list, extra_mapping_map, \
        template_filename_unique, start_marker, end_marker):
    try:
        for contact in contact_list:
            od = output_directory + "/" + contact['uid'] + "/"
            try:
                os.makedirs(od)
            except FileExistsError:
                pass
            for include_file_name in include_file_list:
                shutil.copy(include_file_name, od)
            for link_name in link_file_list:
                os.symlink(link_name, os)
            for template_file_name in template_file_list:
                ofbn = template_file_name.rsplit('/', 1)[1]
                if template_filename_unique:
                    ofbname = ofbn.rsplit('.', 1)
                    output_file_name = od + ofbname[0] + '.' + \
                            contact['uid'] + '.' + ofbname[1]
                else:
                    output_file_name = od + ofbn
                with open(template_file_name, 'r') as template_file:
                    with open(output_file_name, 'w') as output_file:
                        print(output_file_name)
                        for line in template_file:
                            for extra_mapping in extra_mapping_map:
                                line = line.replace(start_marker + \
                                        extra_mapping + end_marker, \
                                        extra_mapping_map[extra_mapping])
                            for contact_mapping in contact:
                                line = line.replace(start_marker + \
                                        contact_mapping + end_marker, \
                                        contact[contact_mapping])
                            output_file.write(line)
    except Exception as e:
        print('TODO: Not good...', e)
        raise SystemExit

if __name__ == '__main__':
    main()

