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

## How to write a test case?

Write tests in the `tests.py` file under each django app.

First, create a factory for each model in the app. A model's factory can be used
to create multiple instances of the model.

For example, we define a simple model,

```
class ExampleModel(models.Model):
    name = models.TextField(verbose_name=_('name'))
    age = models.IntegerField(verbose_name=_('age'))
```

### How to create a factory?

To test API endpoints which depend on `ExampleModel`, we first create a factory
using a handy library called
[factory_boy](https://factoryboy.readthedocs.io/en/latest/). `ExampleFactory` is
defined as,

```
class ExampleFactory(factory.django.DjangoModelFactory):
    name = 'Example Instance'
    age = 42
```

A good factory covers all possible values accepted by the model. To achieve
sufficient randomness, we use
[fuzzy](https://factoryboy.readthedocs.io/en/latest/fuzzy.html) attributes that
generate random values for each instance of `ExampleModel` created by
`ExampleFactory`.

```
class ExampleFactory(factory.django.DjangoModelFactory):
    name = fuzzy.FuzzyText(length=10)
    age = fuzzy.FuzzyInteger(0)
```

Now we are ready to write test cases for API endpoints involving `ExampleModel`.

A real-world factory is
[`ProjectFactory`](./deployments/factories/project.py#L12) which is used to
create instances of the [`Project`](./deployments/models.py#L310) model.

### Test case for `list` API

For `list` test cases we make a `GET` request,

```
class TestExampleAPI(TestCase):
    def test_example_list(self):
        # submit list request
        response = self.client.get("/api/v2/example/")

        # check response
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))
```

The `test_example_list` test case calls the `GET /api/v2/example/` endpoint. It
checks for the response status code using `assetEqual` and response body using
`assertMatchSnapshot` and `json.loads` (only if the expected response is in JSON
format).

By default, the test run starts with an empty database. So `test_example_list`
will always return an empty list.

To check for a response with a non-empty list response, first populate the
database with an instance of `ExampleModel`. Call the
[`create`](https://factoryboy.readthedocs.io/en/latest/reference.html#factory.create)
function on `ExampleFactory` to create an instance of `ExampleModel`,

```
def test_example_list_one(self):
    # create instance
    ExampleFactory.create()

    # submit list request
    response = self.client.get("/api/v2/example/")

    # check response
    self.assertEqual(response.status_code, 200)
    self.assertMatchSnapshot(json.loads(response.content))
```

To create multiple instances, call the
[`create_batch`](https://factoryboy.readthedocs.io/en/latest/reference.html#factory.create_batch)
function.

### Test case for `create` API with authentication

We create an instance of `ExampleModel` to submit to the `POST` endpoint,

`create` endpoints require user authentication. Authentication is possible via
the
[`force_login`](https://docs.djangoproject.com/en/3.1/topics/testing/tools/#django.test.Client.force_login)
function.

```
def test_example_create(self):
    # create instance
    new_name = "Mock Example for Create API Test"
    new_example = ExampleFactory.stub(name=new_name)

    # authenticate
    new_user = UserFactory.create()
    self.client.force_login(new_user)

    # submit create request
    response = self.client.post(
        "/api/v2/example/", new_example, content_type="application/json"
    )

    # check response
    self.assertEqual(response.status_code, 201)
    self.assertMatchSnapshot(json.loads(response.content))
    self.assertTrue(ExampleModel.objects.get(name=new_name))
```

The `test_example_create` test case calls the `POST /api/v2/example/` endpoint
with a request body. It also uses `assertTrue` to check if the `ExampleModel`
object is created as a result of the POST request.

Using methods used in the above examples, test cases can be written for
`update`, `read` and `delete` endpoints.

### Reproducible Randomness

Although our factories generate random attributes, we require the API response
to be exactly the same at each run to have comparable snapshots.

Reproducibility is achieved by
[setting a random seed](./deployments/tests.py#L21),
[using mocks](./deployments/tests.py#L23-L26) and
[resetting the database](./deployments/tests.py#L20)
[before executing each test](./deployments/tests.py#L19).

An example of a real-world snapshot test is defined for
[`TestProjectAPI`](./deployments/tests.py#L17).

## Test Coverage

Run `docker-compose run --rm coverage_report` to view a report of the lines of
code executed to run the tests. Report includes coverage of both the
snapshottests and drf tests.

For a line-by-line coverage report run `docker-compose run --rm coverage_html`
and view `htmlcov/index.html` in a browser.

#### References

1. https://github.com/syrusakbary/snapshottest
2. https://medium.com/analytics-vidhya/factoryboy-usage-cd0398fd11d2
3. https://factoryboy.readthedocs.io/en/latest/recipes.html#using-reproducible-randomness
