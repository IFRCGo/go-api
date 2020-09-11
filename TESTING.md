# Testing

## Snapshot Testing

### Commands

Run tests using `docker-compose run --rm test`

The above command executes tests defined in the `tests.py` files and compares
the API responses with the snapshots saved in the `snapshots/snap_tests.py`
files.

To update the snapshots of the API responses, execute
`docker-compose run --rm test_snapshot_update`

The above command updates the `snapshots/snap_tests.py` files with the API
responses of the tests defined in the `tests.py` files. Do **NOT** manually edit
the contents of the `snapshots/` folders.

### How to write tests?

Write tests in `tests.py` for each django app.

An example of a snapshot test is `TestProjectAPI` in
[`deployments/tests.py`](./README.md).

`TestProjectAPI` tests the `Project` model by comparing snapshots of the API
responses.

`self.assertMatchSnapshot(json.loads(response.content))`

## Test Coverage

Run `docker-compose run --rm coverage_report` to view a report of the lines of
code executed to run the tests. Report includes coverage of both the
snapshottests and drf tests.

For a line-by-line coverage report run `docker-compose run --rm coverage_html`
and view `htmlcov/index.html` in a browser.

#### References

1. https://github.com/syrusakbary/snapshottest
2. https://medium.com/analytics-vidhya/factoryboy-usage-cd0398fd11d2
