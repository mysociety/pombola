# Budgets App

Stores and presents budgetary data for objects

## Commands

### `budgets_import_place_budgets`

Import a CSV of budgetary data and assign it to a place and budgetary session.

#### Usage

You will want to manually create a Budget Session first. This can be done
through the normal admin interface.

`./manage.py budgets_import_place_budgets filename budget_session organisation currency`

* `filename`: The path to the CSV file to import.
* `budget_session`: The ID of the budget session to allocate budgets to.
* `organisation`: The name of the organisation allocating the budget. This is a
  standalone value, and doesn't relate to other organisations in the data.
* `currency`: The [ISO 4217](http://en.wikipedia.org/wiki/ISO_4217) code for the
  currency of the budget. Used for formatting the monetary values correctly.

#### Source File Format

A CSV of budget data with `Place Name`, `Budget Name` and `Budget Value`
headings.

* `Place Name`: String of the place name, ideally in slug form for accurate matching.
* `Budget Name`: String name for this budgetary item.
* `Budget Value`: Numeric (ie no monetary symbol or separators) value for the budget.
