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
import datetime
import requests
import threading
import time
import hashlib
import subprocess
import sys

"""
    Download a file with content requests and threading

    Note:
        must use integer Content-Length, offset in Content-Range, and file seek.

    Logic:
        get Content-Length from request.head(url)
        calculators offsets through Content-Length and threadings
        add offset to new headers
        content request each part of the downloaded file
        threading

    HTTP Header:
        1. request.head
        {'Date': 'Sun, 18 Nov 2018 15:42:14 GMT', 'Server': 'Apache', 'Last-Modified': 'Fri, 17 Nov 2017 21:04:42 GMT', 'ETag': '"c6c82-55e3415e20e80"', 'Accept-Ranges': 'bytes', 'Content-Length': '814210', 'Keep-Alive': 'timeout=2, max=100', 'Connection': 'Keep-Alive', 'Content-Type': 'application/pdf'}
        2. request.get
        {'Date': 'Sun, 18 Nov 2018 15:44:31 GMT', 'Server': 'Apache', 'Last-Modified': 'Fri, 17 Nov 2017 21:04:42 GMT', 'ETag': '"c6c82-55e3415e20e80"', 'Accept-Ranges': 'bytes', 'Content-Length': '8143', 'Content-Range': 'bytes 56994-65136/814210', 'Keep-Alive': 'timeout=2, max=100', 'Connection': 'Keep-Alive', 'Content-Type': 'application/pdf'}
"""


class ContentRequest(object):
    def __init__(self, url, threads, path=''):
        self.url = url
        self.threads = threads
        self.file = path + self.url.split('/')[-1]
        self.resp = {}
        self.reload = ()  # use tuple to avoid duplicate value
        self.content_length = 0

    # calculate the offset base on the content-length and threading
    def get_offset(self):
        resp = requests.head(self.url)
        self.content_length = int(resp.headers['Content-Length'])
        offset = int(self.content_length / self.threads)
        for i in range(self.threads):
            if i < self.threads - 1:
                yield (i * offset, (i + 1) * offset)
            else:
                yield (i * offset, '')

    # {'Content': 'Bytes=0-81421', 'Accept-Encoding': '*'}
    # request content download, the response code should be 206
    def request_content(self, headers):
        for i in range(1, 6):
            try:
                offset = headers['Range'].split('=')[1].split('-')[0]
                resp = requests.get(self.url, headers=headers)
                if resp.status_code == 206:  # 206 Partial Content
                    self.resp[offset] = resp
                else:
                    print(resp.status_code)
                    self.reload += (headers, )
                return
            except requests.exceptions.RequestException as e:
                print(e.args)
                print('--Error! Retry in {} seconds...'.format(i * 3))
                time.sleep(i * 3)
        print('--Failed to get {} / {} in 5 times retry.'.format(headers, self.file))

    # save to binary file
    def write_file(self, resp):
        with open(self.file, 'wb') as f:
            for r in resp:
                # (resp.headers['Content-Range'].split('-')[0].split(' ')[-1])  # Content-Range: bytes 0-81421/814210
                start = int(r.headers['Content-Range'].split('-')[0].split(' ')[-1])
                f.seek(start)
                f.write(r.content)

    def start(self):
        start_time = time.time()
        offset_range = self.get_offset()
        # replace the get_headers function with one line  use generator
        # headers = self.get_headers(offset_range)
        # {'Content': 'Bytes=0-81421', 'Accept-Encoding': '*'}
        headers = ({'Range': 'Bytes={}-{}'.format(*item), 'Accept-Encoding': '*'} for item in offset_range)
        threads_list = []

        for header in headers:
            s = threading.Thread(target=self.request_content, args=(header,))
            s.start()
            threads_list.append(s)

        for s in threads_list:
            s.join()

        if len(self.reload) == 0:
            # for resp in self.resp.values():
            self.write_file(self.resp.values())
            time_used = time.time() - start_time
            speed_mb = self.content_length / time_used / 1000000
            # use round to limit the length after decimal
            print('File {} downloaded in {} seconds. (Speed: {} MB/s)'.format(self.file.split('/')[-1], round(time_used, 2), round(speed_mb, 2)))
        else:
            print('Error!')
            print(self.reload)


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
    with open(exist_tags, 'r') as f:
        f_data = f.read()

    for build in builds:
        if build[:-1] not in f_data:  # use [:-1] to remove the '/' in tag
            tags.append(build)
    if len(tags) == 0:
        print('---There is no new build on the Server!')
        return []
    else:
        print(tags)
        return tags


# if md5sum.txt is ready, add md5 and *.out* files in the list
def get_urls(url, tag):
    url += tag
    md5 = 'md5sum.txt'

    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="lxml")
    links = soup.find_all('a')

    # get builds with .out includes in its name if md5sum.txt is ready
    md5_url = [url + link.get('href') for link in links if md5 in link.get('href')]
    if len(md5_url) == 1:
        # out_url = {url + link.get('href') for link in links if '.out' in link.get('href')}
        out_url = {url + link.get('href') for link in links if '400D' in link.get('href') if '.out' in link.get('href')}
        return md5_url + list(out_url)
    else:
        print('---{} in {} is not ready yet.'.format(md5, tag))
        return []


def main():
    # base_url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/build0058/'
    base_url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/'
    exist_tags = 'Build_download_test.txt'
    threads = 80
    path = '/volume1/FWB/test-image/fwb/'
    # /home/Images/FortiWeb/v6.00/images/build0056
    # Home/Images/FortiWeb/v6.00/images/build0058/
    # http://172.16.100.71/Images/FortiWeb/v6.00/images/build0058/

    tags = check_tag(base_url, exist_tags)
    if len(tags) == 0:
        sys.exit('---Exit for there is no new build!')

    for tag in tags:
        urls = get_urls(base_url, tag)
        # download md5sum.txt first, open it, and del its url in the list
        if len(urls) != 0:
            # new_tag format match previous one(# Home/Images/FortiWeb/v6.00/images/build0058/)
            # in case roll back to old script
            new_tag = (base_url + tag).replace('http://172.16.100.71', '/Home')[:-1] + '\n'
            path += tag  # path used for create local dir
            print('Local Path is: ', path)
            # make new tag dir
            subprocess.call('mkdir {}'.format(path), shell=True)

            d = ContentRequest(urls[0], 1, path)
            d.start()
            time.sleep(0.1)
            all_md5 = open(path + urls[0].split('/')[-1], 'r').read()
            del urls[0]

            n = 5
            # try 5 times totally if urls is not empty
            for i in range(n):
                passed_urls = []  # for those passed md5 check image
                for url in urls:
                    d = ContentRequest(url, threads, path)
                    d.start()

                    # checksum = hashlib.md5(open('*.out', 'rb').read()).hexdigest()
                    checksum = hashlib.md5(open(path + url.split('/')[-1], 'rb').read()).hexdigest()
                    # remove the url if it passed md5 check
                    if checksum in all_md5:
                        print('-md5 check passed in {}/{}'.format(i + 1, n))
                        passed_urls.append(url)
                    else:
                        print('---{} md5 check failed'.format(url.split('/')[-1]))

                # got the urls that did not passed md5 check
                urls = list(set(urls) - set(passed_urls))
                if len(urls) == 0:
                    print('---All files passed md5 check')
                    # write the new tag to exist_tags
                    with open(exist_tags, 'a') as f:
                        f.write(new_tag)
                        path = path.replace(tag, '')  # recover the original path value in case there is more tags
                        break  # exit for loop
                else:
                    print('---{} files failed md5 check in No.{} times: {}'.format(len(urls), i + 1, urls))


if __name__ == '__main__':
    # time.sleep(40000)
    t1 = datetime.datetime.now()
    main()
    print(datetime.datetime.now() - t1)
