# Admin tasks

## Common tasks

This section documents tasks that you will likely use regularly in the day to
day maintenance of the site.

### Merging two people together

Sometimes you'll have two person records for the same person and you'll need to
merge them together. Use the `core_merge_people` management to merge people
together safely, ensuring their positions etc are preserved.

You will need to pick one person to keep and one that will be deleted. You
provide these as the `--keep-id` and `--delete-id` arguments respectively.

When you run the command you will be asked to confirm that you want to merge the
two people together. Make sure the correct names are displayed before proceeding
as there's no way to undo this operation.

If there is any differences between the people that can't be resolved
automatically then the command will print out a list of problems and exit
without making any changes.

#### Examples

This will keep the person with ID 78 and delete the person with ID 4567.
Information from the deleted person will be added to the person that is kept.

    ./manage.py core_merge_people --keep-id=78 --delete-id=4567

You can also use slugs rather than IDs.

    ./manage.py core_merge_people --keep-id=john-smith --delete-id=jonathan-smith

### Merging two organisations together

Similarly to merging people together, you can use this command when you need to
merge two organisations that are duplicates of each other. Use the
`core_merge_organisations` command to merge organisations.

You will need to pick one organisation to keep and one that will be deleted. You
provide these as the `--keep-id` and `--delete-id` arguments respectively.

When you run the command you will be asked to confirm that you want to merge the
two organisations together. Make sure the correct names are displayed before
proceeding as there's no way to undo this operation.

If there is any differences between the organisations that can't be resolved
automatically then the command will print out a list of problems and exit
without making any changes.

#### Examples

This will keep the organisation with ID 90 and delete the organisation with ID
123. Information from the deleted organisation will be added to the organisation
that is kept.

    ./manage.py core_merge_organisations --keep-id=90 --delete-id=123

You can also use slugs rather than IDs.

    ./manage.py core_merge_organisations --keep-id=abc-corp --delete-id=alphabet-corp
