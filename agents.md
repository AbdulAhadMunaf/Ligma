AGENTS.md file

## Dev environment tips
In order to run tests run pytest -vv to run all tests and in order to run a particular test then run 
pytest -vv apps/PATH_TO_TEST_FILE

## Coding Instructions
Write clean code while keeping few things in mind
- the variables must be in snake_case
- If the code is complex then use the service class instead of writing the whole logic in api class
- For example: see the file abc_api.py in the same directory you will have a folders called services there you can use the function abc_service.py
- Try to keep the code clean and easy to read
- For TESTS keep the test file small and ensure that there are not more than 5 tests per file, if there are more than 5 tests then maybe create a new file.
- For the API written you must write the tests as well 
- If one of the service is calling any external api and you want to write tests for that then write tests using mock
- For the logic where you have to run async code for this repository you can use celery jobs.