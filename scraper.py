import os
import requests
import datetime
import pytz
import json
import hashlib

def get_json(url, output_list):
    req = requests.get(url)
    data = req.json()
    # Add all posts to out list
    output_list.extend(data['data'])
    # Check if there's a next page - if True, call recursively
    if 'next' in data['paging']:
        return get_json(data['paging']['next'], output_list)
    return True

def scraper(environ, start_response):
    # Store start time
    start_time = datetime.datetime.utcnow()

    # Get access token
    access_token = os.environ['FB_ACCESS_TOKEN']
    # Store raw post data here
    data = []
    # Request
    get_json(
        'https://graph.facebook.com/v3.0/221844801737554/posts?limit=100&fields=created_time,message,type,id&access_token=' + access_token,
        data
    )

    # Get page ID
    page_id = data[0]['id'].split('_')[0]

    # Store posts in this list
    posts = []

    # Loop through raw posts
    for post in data:
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

    # Create MD5 hash
    etag_hash = hashlib.md5(str(posts).encode('utf_8')).hexdigest()

    if 'HTTP_IF_NONE_MATCH' in environ:
        if environ['HTTP_IF_NONE_MATCH'] == etag_hash:
            start_response('304 Not Modified', [])
            return

    # Store end time and runtime
    end_time = datetime.datetime.utcnow()
    runtime = end_time - start_time
    # Create output JSON
    json_dict = {
        'posts': posts,
        'length': len(posts),
        'page_id': page_id,
        'updated': end_time.isoformat(),
        'runtime': str(runtime)
    }
    json_bstr = json.dumps(json_dict, indent=4).encode('utf_8')
    
    response_headers = [
        ('Content-Type', 'application/json; charset=UTF-8'),
        ('Content-Length', str(len(json_bstr))),
        ('Cache-Control', 'public, max-age:86400'),
        ('ETag', etag_hash),
        ('Access-Control-Allow-Origin', '*')
    ]
    start_response('200 OK', response_headers)

    yield json_bstr
