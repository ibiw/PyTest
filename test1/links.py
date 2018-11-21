"""
    1. check build tags
        check_tag(url=base_url)
        args: base_url, exist_tags(both are global)

    2. get builds urls
        get_urls(tag, url=base_url)
        args: tag, base_url(global)

    3. download
        requests threading(objc)
        args: urls, local path(both are global)

    4. md5 check  args: filename, md5sum.txt
        tbd... going to do it after file doanloaded

    5. write tag  args: exist_tags
        args: tag, exist_tags(global)

    6. log
        tbd
"""
from bs4 import BeautifulSoup
import requests
import time


# check if there is no build in the server through compare with local exist tags
def check_tag(url, exist_tags):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="lxml")
    links = soup.find_all('a')  # Finds all hrefs
    builds = []  # list builds to save all the builds from server
    tags = []  # list tags to save all the tags that are not download yet
    for link in links:
        if 'build' in link.get('href'):
            builds.append(link.get('href'))
            # print(link.get('href'))
    f = open(exist_tags, 'r')
    f_data = f.read()
    for build in builds:
        if build[:-1] not in f_data:  # use [:-1] to remove the '/' in tag
            tags.append(build)
    if len(tags) == 0:
        print('There is no new build on the Server')
    else:
        print(tags)
        return tags

# if md5sum.txt is ready, add md5 and *.out* files in the list
def get_urls(url, tag):
    url += tag
    builds = []
    md5 = 'md5sum.txt'

    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="lxml")
    links = soup.find_all('a')

    # get builds with .out includes in its name
    for link in links:
        if '.out' in link.get('href') or md5 in link.get('href'):
            builds.append(link.get('href'))

    # check if md5 is ready and make sure it is in the first position of the list
    if builds[-1] == md5:
        print('---{} founded in position: {}/{}!'.format(md5, builds.index(md5), len(builds) - 1))
        builds.reverse()
    elif builds[-1] != md5 and md5 in builds:
        print('---{} founded in position: {}/{}!'.format(md5, builds.index(md5), len(builds) - 1))
        builds.remove(md5)
        builds.append(md5)
    else:
        print('---{} is not ready yet.'.format(md5))
        return []

    # get the url
    # builds = [url + build for build in builds]  # which one is faster?
    builds = map(lambda b: url + b, builds)
    return builds


def main():
    # base_url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/build0058/'
    base_url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/'
    exist_tags = 'Build_download_test.txt'

    tags = check_tag(base_url, exist_tags)

    for tag in tags:
        builds = get_urls(base_url, tag)
        for build in builds:
            print(build)


if __name__ == '__main__':
    t1 = time.time()
    main()
    print(time.time() - t1)