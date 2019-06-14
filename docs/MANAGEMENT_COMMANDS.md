# Management commands

This document gives an overview of all the management commands in pombola. Further documentation can be found by running the command with the `--help` flag.

To run these commands make sure you're in the root of this repository and then prefix them with `./manage.py`:

    ./manage.py core_merge_people`

# budgets

See [the README for the budgets app](../pombola/budgets/README.md) for further details.

# core

    core_add_ward_places_2013
    core_check_mp_aspirants
    core_cleanup_disqus_urls
    core_create_elected_positions
    core_create_places_from_mapit_entries
    core_database_dump
    core_end_positions
    core_export_summary_csvs
    core_export_to_popolo_json
    core_extend_areas_to_generation_2
    core_extend_party_memberships
    core_find_stale_elasticsearch_documents
    core_fix_ward_names
    core_import_basic_positions_csv
    core_import_kenyan_boundaries_2013
    core_list_malformed_slugs
    core_list_person_primary_images
    core_match_places_to_mapit_areas
    core_match_places_to_mapit_areas_2013
    core_merge_organisations
    core_merge_people
    core_move_profile_url_to_parliament_url
    core_output_constituency_party_affiliation
    core_output_mp_contact_csv
    core_output_mp_scorecard_csv
    core_position_deduplicate
    core_render_template
    core_set_area_parents


# feedback
    feedback_report_pending

# interests_register
    interests_register_delete_existing
    interests_register_import_from_json

# pombola_sayit
    pombola_sayit_sync_pombola_to_popolo

# scorecards
    scorecard_update_person_contact_scores
    scorecard_update_person_hansard_appearances

# south_africa
    south_africa_adwords_csv
    south_africa_create_new_parties_for_election_2019
    south_africa_export_committee_members
    south_africa_export_constituency_offices
    south_africa_export_na_members
    south_africa_import_boundaries
    south_africa_import_constituency_offices
    south_africa_import_election_candidates_2014
    south_africa_import_election_candidates_2019
    south_africa_import_election_results_2014
    south_africa_import_election_results_2019
    south_africa_import_new_constituency_office_locations
    south_africa_import_parties
    south_africa_import_popolo_json
    south_africa_import_scraped_photos
    south_africa_restart_constituency_contacts
    south_africa_set_da_office_locations
    south_africa_sync_everypolitician_uuid
    south_africa_sync_wikidata_ids_from_everypolitician
    south_africa_update_constituency_office_address
    south_africa_update_constituency_offices

# za_hansard
    za_hansard_check_for_new_sources
    za_hansard_load_into_sayit
    za_hansard_load_json
    za_hansard_load_za_akomantoso
    za_hansard_one_off_create_hansard_hierarchies
    za_hansard_one_off_rename_hansard_month_sections
    za_hansard_one_off_tag_speeches
    za_hansard_pmg_api_scraper
    za_hansard_q_and_a_scraper
    za_hansard_run_parsing
