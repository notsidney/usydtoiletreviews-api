import requests
import datetime
import pytz
import json

def scraper(environ, start_response):

    start_time = datetime.datetime.utcnow()

    with open('access_token.txt', 'r') as token_file:
        access_token = token_file.readline().strip()
    req = requests.get('https://graph.facebook.com/v3.0/221844801737554?fields=posts.limit(100){created_time,message,permalink_url,type,id}&access_token=' + access_token)

    # Get JSON
    data = req.json()

    # Get page ID
    page_id = data['posts']['data'][0]['id'].split('_')[0]

    # Store posts in this list
    posts = []

    for post in data['posts']['data']:
        # Ignore non-photo posts since they're not reviews
        if post['type'] != 'photo':
            continue
        # Check if post is a review by looking for '/10' in 'message'
        if 'message' not in post:
            continue
        if '/10' not in post['message']:
            continue

        # Initialise all dict items as empty strings
        post_data = {
            'id': post['id'].replace(page_id, '').replace('_', ''),
            'timestamp': '',
            'building': '',
            'level': '',
            'type': '',
            'notes': '',
            'rating': ''
        }

        # Get UTC timestamp
        utc_time = datetime.datetime.strptime(\
            post['created_time'], '%Y-%m-%dT%H:%M:%S%z')
        # And convert to Sydney time
        syd_time = utc_time.astimezone(pytz.timezone('Australia/Sydney'))
        # Write to output dict
        post_data['timestamp'] = syd_time.strftime('%Y-%m-%d %H:%M')

        # Read data from 'message'
        split_msg = post['message'].split('\n')
        meta_line = split_msg[0]
        post_data['rating'] = split_msg[-1].split('/10')[0]

        # Check if meta_line has any notes, denoted by [] or ()
        if '[' in meta_line:
            start = meta_line.find('[')
            end = meta_line.find(']')
            post_data['notes'] = meta_line[start : end + 1]
            meta_line = meta_line.replace(post_data['notes'], '').strip()
        if '(' in meta_line:
            start = meta_line.find('(')
            end = meta_line.find(')')
            post_data['notes'] = meta_line[start : end + 1]
            meta_line = meta_line.replace(post_data['notes'], '').strip()

        meta_line = meta_line.split(',')

        post_data['building'] = meta_line[0]

        # Loops through rest of meta_items
        for meta_item in meta_line[1:]:
            if 'Toilet' in meta_item.title():
                post_data['type'] = meta_item.title()\
                    .replace('Toilets', '').replace('Toilet', '')\
                    .strip()
            else:
                post_data['level'] = meta_item.replace('Level', '').strip()

        posts.append(post_data)

    data_list = []
    data_list.append('{\n    "posts": [\n')
    for post in posts:
        data_list.append(' ' * 8 + json.dumps(post) + ',\n')
    current_time = datetime.datetime.utcnow()
    runtime = current_time - start_time
    current_time_iso = current_time.isoformat()
    data_list.append('    ],\n    "page_id": "' + page_id + \
        '",\n    "updated": "' + current_time_iso + \
        '",\n    "runtime": "' + str(runtime) + '"\n}')

    data = ''.join(data_list).encode('utf_8')
    
    response_headers = [
        ('Content-Type', 'application/json; charset=UTF-8'),
        ('Content-Length', str(len(data)))
    ]
    start_response('200 OK', response_headers)
    return [data]