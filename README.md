Created for [USYD Toilet Reviews][fb]

# USYD Toilet Reviews API
Returns reviews from USYD Toilet Reviews in JSON format using the Facebook API.
Used in the [USYD Toilet Reviews web app][wa].

## Requirements
* Python 3
* Pip
* Pipenv


## Installation
1. Clone the repo
2. Inside the repo directory, run `pipenv install` to install Python dependencies
3. Get a Facebook API access token [(instructions)](access_token.txt) for the page and set the environment variable `FB_ACCESS_TOKEN` to that token
4. Run the command `pipenv shell`
5. Run the command `gunicorn --preload --max-requests 1200 usydtoiletreviews_api:serve_api`
6. Open http://127.0.0.1:8080 in your browser

[fb]: https://www.facebook.com/usydlooreviews
[wa]: https://usydtoiletreviews.netlify.com/
