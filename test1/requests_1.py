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
"""
import requests
import threading
import time


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
        print(self.content_length)
        offset = int(self.content_length / self.threads)
        for i in range(self.threads):
            if i < self.threads - 1:
                yield (i * offset, (i + 1) * offset)
            else:
                yield (i * offset, '')

    # {'Content': 'Bytes=0-81421', 'Accept-Encoding': '*'}
    @staticmethod
    def get_headers(offsets):
        for item in offsets:
            # print(item)
            # yield {'Range': 'Bytes=%s-%s' % item, 'Accept-Encoding': '*'}
            # format(*item) is same as % item that put the values in tuple to {} one by one
            yield {'Range': 'Bytes={}-{}'.format(*item), 'Accept-Encoding': '*'}

    # request content download, the response code should be 206
    def request_content(self, headers):
        for i in range(1, 6):
            try:
                offset = headers['Range'].split('=')[1].split('-')[0]
                resp = requests.get(self.url, headers=headers)
                if resp.status_code == 206:
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
        headers = self.get_headers(offset_range)
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
            speed_kb = self.content_length / time_used / 1000000
            print('File {} downloaded successful in {} seconds. (speed: {} MB/s)'.format(self.file.split('/')[-1], round(time_used, 2), round(speed_kb, 2)))
        else:
            print('Error!')
            print(self.reload)


def main():
    # get Content-Size
    url = 'http://greenteapress.com/thinkpython2/thinkpython2.pdf'
    threads = 100
    path = '/home/rw/Downloads/'

    d = ContentRequest(url, threads, path)
    d.start()


if __name__ == '__main__':
    # start_time = time.time()
    main()
    # print("--- %s seconds ---" % (time.time() - start_time))
