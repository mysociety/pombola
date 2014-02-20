This package abtracts away country-specific helper code, such as
that which defines which positions are considered worth
highlighting, so that one can just do:

    from pombola.country import significant_positions_filter
