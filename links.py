from bs4 import BeautifulSoup
import requests

url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/build0058/'
url_t = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/'


def check_tag(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content)
    links = soup.find_all('a')  # Finds all hrefs
    builds = []  # list builds to save all the builds from server
    tags = []  # list tags to save all the tags that are not download yet
    for link in links:
        if 'build' in link.get('href'):
            builds.append(link.get('href'))
            # print(link.get('href'))
    f = open('Build_download_test.txt', 'r')
    f.data = f.read()
    for build in builds:
        if build[:-1] not in f.data:  #use [:-1] to remove the '/' in tag
            tags.append(build)
    if len(tags) == 0:
        print('There is no new build on the Server')
    else:
        print(tags)
        return tags


def get_urls(url, tag):
    url += tag
    builds = []
    is_md5sum = False

    resp = requests.get(url)
    soup = BeautifulSoup(resp.content)
    links = soup.find_all('a')
    for link in links:
        if '.out' in link.get('href'):
            builds.append(link.get('href'))
        elif 'md5sum.txt' in link.get('href'):
            print('md5sum.txt found!')
            builds.append(link.get('href'))
            is_md5sum = True
    if is_md5sum:
        return builds

b = get_urls(url_t, 'build0058/')
print(b)

