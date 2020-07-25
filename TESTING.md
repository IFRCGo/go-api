# Testing

## Snapshot Testing

Write tests in `tests.py` for each django app.

An example of a snapshot test is `TestDeploymentsModelsProject` in [`deployments/tests.py`](./README.md).

`TestDeploymentsModelsProject` tests the `Project` model by making a shallow comparison.

For a deeper comparison, write additional assert statements such as,

`self.assertEqual(project_model.reached_total, 10)`

### Commands

Run tests using `docker-compose run --rm test`

Executes `tests.py` and compares result with `snapshots/snap_tests.py`

Update tests using `docker-compose run --rm test_snapshot_update`

Writes `snapshots/snap_tests.py` with the execution result of `tests.py`
Do **NOT** manually edit the contents of the snapshots folder.


## Test Coverage

Run `docker-compose run --rm coverage_report` to view a report of the lines of code executed to run the tests.
Report includes coverage of both the snapshottests and drf tests.

For a line-by-line coverage report run `docker-compose run --rm coverage_html` and view `htmlcov/index.html` in a browser.

#### References
1. https://github.com/syrusakbary/snapshottest
2. https://medium.com/analytics-vidhya/factoryboy-usage-cd0398fd11d2
