import os

frontend_url = os.environ.get('FRONTEND_URL')
if frontend_url == 'prddsgoproxyapp.azurewebsites.net':
    # We use a nicer frontend URL:
    frontend_url = 'go.ifrc.org'
