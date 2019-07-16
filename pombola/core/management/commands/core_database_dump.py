import os
from os.path import dirname, join, realpath
import subprocess
import sys
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


def shellquote(s):
    return "'" + s.replace("'", "'\\''") + "'"


class Command(BaseCommand):

    help = 'Output a database dump only containing public data'
    args = '<OUTPUT-FILENAME>'

    def get_tables_to_dump(self):
        tables = connection.introspection.table_names()
        tables_to_ignore = set([
            'auth_group',
            'auth_group_permissions',
            'auth_message',
            'auth_permission',
            'auth_user',
            'auth_user_groups',
            'auth_user_user_permissions',
            'django_admin_log',
            'django_select2_keymap',
            'django_session',
            'experiments_event',
            'feedback_feedback',
            'popit_resolver_entityname',
            'thumbnail_kvstore',
            # Older tables that might still be present:
            'comments2_comment',
            'comments2_commentflag',
            'django_comment_flags',
            'django_comments',
            'mz_comments_commentwithtitle',
            'votematch_submission',
            # Exclude PostGIS tables
            'layer',
            'topology',
            # This table is very large, and entirely generated from
            # other data in the database; it can be recreated with
            # the popolo_name_resolver_init management command.
            'popolo_name_resolver_entityname',
            'writeinpublic_configuration',
        ])
        tables_to_dump = [
            t for t in tables if t not in tables_to_ignore
        ]
        expected_tables = [
            'budgets_budget',
            'budgets_budgetsession',
            'core_alternativepersonname',
            'core_contact',
            'core_contactkind',
            'core_identifier',
            'core_informationsource',
            'core_organisation',
            'core_organisationkind',
            'core_organisationrelationship',
            'core_organisationrelationshipkind',
            'core_parliamentarysession',
            'core_person',
            'core_place',
            'core_placekind',
            'core_position',
            'core_positiontitle',
            'core_slugredirect',
            'django_content_type',
            'django_migrations',
            'django_site',
            'easy_thumbnails_source',
            'easy_thumbnails_thumbnail',
            'easy_thumbnails_thumbnaildimensions',
            'experiments_experiment',
            'file_archive_file',
            'images_image',
            'info_category',
            'info_infopage',
            'info_infopage_categories',
            'info_infopage_tags',
            'info_tag',
            'info_viewcount',
            'instances_instance',
            'instances_instance_users',
            'mapit_area',
            'mapit_code',
            'mapit_codetype',
            'mapit_country',
            'mapit_generation',
            'mapit_geometry',
            'mapit_name',
            'mapit_nametype',
            'mapit_postcode',
            'mapit_postcode_areas',
            'mapit_type',
            'popit_apiinstance',
            'popit_person',
            'popolo_area',
            'popolo_areai18name',
            'popolo_contactdetail',
            'popolo_identifier',
            'popolo_language',
            'popolo_link',
            'popolo_membership',
            'popolo_organization',
            'popolo_othername',
            'popolo_person',
            'popolo_post',
            'popolo_source',
            'scorecards_category',
            'scorecards_entry',
            'slug_helpers_slugredirect',
            'south_migrationhistory',
            'tasks_task',
            'tasks_taskcategory',
        ]
        if settings.COUNTRY_APP in ('south_africa',):
            expected_tables += [
                'interests_register_category',
                'interests_register_entry',
                'interests_register_entrylineitem',
                'interests_register_release',
                'pombola_sayit_pombolasayitjoin',
                'speeches_recording',
                'speeches_recordingtimestamp',
                'speeches_section',
                'speeches_slug',
                'speeches_speaker',
                'speeches_speech',
                'speeches_speech_tags',
                'speeches_tag',
                'surveys_survey',
                'za_hansard_answer',
                'za_hansard_pmgcommitteeappearance',
                'za_hansard_pmgcommitteereport',
                'za_hansard_question',
                'za_hansard_questionpaper',
                'za_hansard_source',
            ]
        if settings.COUNTRY_APP in ('south_africa'):
            # spinner
            expected_tables += [
                'spinner_imagecontent',
                'spinner_quotecontent',
                'spinner_slide',
            ]
        unexpected = set(tables_to_dump) - set(expected_tables)
        if unexpected:
            print '''The following tables were found which weren't expected
and which hadn't been explicitly excluded.  If these are safe to make
available in a public database dump (in particular check that they
contain no personal information of site users) then add them to
'expected_table'. Otherwise (i.e. they should *not* be made available
publicly) add them to 'tables_to_ignore'.'''
            for t in sorted(unexpected):
                print " ", t
            sys.exit(2)

        return tables_to_dump

    def handle(self, *args, **options):
        if len(args) != 1:
            self.print_help(sys.argv[0], sys.argv[1])
            sys.exit(1)
        output_prefix = args[0]

        for dump_type in ('schema', 'data'):
            output_filename = '{}_{}.sql'.format(output_prefix, dump_type)

            db_settings = connection.settings_dict
            host = db_settings['HOST']
            current_host = subprocess.check_output(['hostname', '--fqdn']).strip()
            dump_over_ssh = host and (host not in ('localhost', current_host))

            command = [
                'pg_dump',
                '--no-owner',
                '--no-acl',
                '--schema=public',
            ]

            command.append({
                'schema': '--schema-only',
                'data': '--data-only',
            }[dump_type])

            if dump_type == 'data':
                for t in self.get_tables_to_dump():
                    command += ['-t', t]

            if (not dump_over_ssh) and host:
                command += [
                    '-h', host,
                ]
            if db_settings['USER']:
                command += [
                    '-U', db_settings['USER'],
                ]
            command.append(db_settings['NAME'])
            if int(options['verbosity']) > 1:
                print >> sys.stderr, "Going to run the command:", ' '.join(command)
            output_directory = dirname(realpath(output_filename))

            ntf = NamedTemporaryFile(
                delete=False, prefix=join(output_directory, 'tmp')
            )
            with open(ntf.name, 'wb') as f:
                shell_command = ''
                if dump_over_ssh:
                    if db_settings['PASSWORD']:
                        shell_command = 'PGPASSWORD={0} '.format(
                            shellquote(db_settings['PASSWORD']))
                    shell_command += ' '.join(shellquote(p) for p in command)
                    try:
                        subprocess.check_call(['ssh', host, shell_command], stdout=f)
                    except subprocess.CalledProcessError:
                        raise CommandError('Problem trying to ssh to {}'.format(host))
                else:
                    subprocess.check_call(command, stdout=f)
            os.chmod(ntf.name, 0o644)
            os.rename(ntf.name, output_filename)
