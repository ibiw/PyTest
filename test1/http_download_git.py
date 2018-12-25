"""
    HTTP download script
    Download a file with content requests and threading

    Note:
       Content-Length, offset in Content-Range, and file seek must be integer

    Logic:
        get Content-Length from request.head(url)
        calculators offsets through Content-Length and how many threading
        add offset to new headers
        content request each part of the downloaded file
        threading

    1. check build tags to see if there is new build on the server
        check_tag(url=base_url)
        args: base_url, exist_tags(both are global)

    2. if new tag, get builds urls of those tags
        get_urls(tag, url=base_url)
        args: tag, base_url(global)

    3. download new image one by one with default 80 threadings
        requests threading(objc)
        args: urls, local path(both are global)

    4. md5 check  args: filename, md5sum.txt
        do md5 check after download, and re-download it if md5 failed

    5. write tag  and send email if all images downloaded and passed md5 check
        args: tag, exist_tags(global)

    6. log support
        Logger

    7. Email support
        mail_to

"""
import sys
import datetime
import threading
import time
import hashlib
import subprocess
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import argparse
import requests
from bs4 import BeautifulSoup
import daemon


class Logger:
    """This is a logger class for logging"""
    def __init__(self, file_name):
        self.file = file_name
        # create logger
        # use __name__ to avoid log imported modules
        self.logger = logging.getLogger(__name__)

        # set default log level
        self.logger.setLevel(logging.INFO)

        # create file_handler
        self.file_handler = logging.FileHandler(self.file, 'a')

        # create file formatter
        self.file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

        # add formatter to handler
        self.file_handler.setFormatter(self.file_formatter)

        # add handlers to logger
        self.logger.addHandler(self.file_handler)

    def info(self, log_message):
        """log level is info"""
        self.logger.info(log_message)
        print(log_message)

    def warning(self, log_message):
        """log level is warning"""
        self.logger.warning(log_message)
        print(log_message)


# log_file = 'http_download.log'
LOG_MSG = Logger('http_download.log')


class ContentRequest:
    """Use to content to download with threading"""
    def __init__(self, url, threads, path=''):
        self.url = url
        self.threads = threads
        self.file = path + self.url.split('/')[-1]
        self.resp = {}
        self.reload = ()  # use tuple to avoid duplicate value
        self.content_length = 0

    def get_offset(self):
        """calculate the offset base on the content-length and threadings"""
        # try 3 times to avoid keyError
        for i in range(3):
            try:
                resp = requests.head(self.url)
                self.content_length = int(resp.headers['Content-Length'])
                offset = int(self.content_length / self.threads)
            except KeyError as key_error:
                LOG_MSG.warning(key_error)
        for i in range(self.threads):
            if i < self.threads - 1:
                yield (i * offset, (i + 1) * offset)
            else:
                yield (i * offset, '')

    # {'Content': 'Bytes=0-81421', 'Accept-Encoding': '*'}
    def request_content(self, headers):
        """request content download, the response code should be 206"""
        for i in range(1, 6):  # try 5 times when expect any error
            try:
                offset = headers['Range'].split('=')[1].split('-')[0]
                resp = requests.get(self.url, headers=headers)
                if resp.status_code == 206:  # 206 Partial Content
                    self.resp[offset] = resp
                else:
                    LOG_MSG.info(resp.status_code)
                    self.reload += (headers, )
                return
            except requests.exceptions.RequestException as error:
                LOG_MSG.warning(error.args)
                LOG_MSG.warning('--Error! Retry in {} seconds...'.format(i * 3))
                time.sleep(i * 3)

        LOG_MSG.info('--Failed to get {} / {} in 5 times retry.'.format(headers, self.file))

    def write_file(self, resp):
        """save to binary file with file seek"""
        with open(self.file, 'wb') as download_file:
            for item in resp:
                # (resp.headers['Content-Range'].split('-')[0].split(' ')[-1])
                # Content-Range: bytes 0-81421/814210
                start = int(item.headers['Content-Range'].split('-')[0].split(' ')[-1])
                download_file.seek(start)
                download_file.write(item.content)

    def start(self):
        """start for threading download"""
        start_time = time.time()
        offset_range = self.get_offset()
        # replace the get_headers function with one line  use generator
        # headers = self.get_headers(offset_range)
        # {'Content': 'Bytes=0-81421', 'Accept-Encoding': '*'}
        headers = ({'Range': 'Bytes={}-{}'.format(*item), 'Accept-Encoding': '*'}
                   for item in offset_range)
        threads_list = []

        for header in headers:
            thread = threading.Thread(target=self.request_content, args=(header,))
            thread.start()
            threads_list.append(thread)

        for thread in threads_list:
            thread.join()

        if not self.reload:
            # for resp in self.resp.values():
            self.write_file(self.resp.values())
            time_used = time.time() - start_time
            speed_mb = self.content_length / time_used / 1000000
            # use round to limit the length after decimal
            LOG_MSG.info('File {} downloaded in {} seconds. (Speed: {} MB/s)'.format(
                self.file.split('/')[-1], round(time_used, 2), round(speed_mb, 2)))
        else:
            LOG_MSG.warning('Error!')
            LOG_MSG.info(self.reload)


def check_tag(url, exist_tags):
    """check if there is new build in the server with compare with local exist tags"""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="lxml")
    links = soup.find_all('a')  # Finds all hrefs
    builds = []  # list builds to save all the builds from server
    tags = []  # list tags to save all the tags that are not download yet
    for link in links:
        if 'build' in link.get('href'):
            builds.append(link.get('href'))
            # l.warning(link.get('href'))
    with open(exist_tags, 'r') as exist_tags_file:
        f_data = exist_tags_file.read()

    for build in builds:
        if build[:-1] not in f_data:  # use [:-1] to remove the '/' in tag
            tags.append(build)
    if not tags:
        # LOG_MSG.info('There is no new build on the Server!') # to reduce the logs
        return []
    LOG_MSG.info(tags)
    return tags


def get_urls(url, tag):
    """get all .out urls if md5sum.txt is ready"""
    url += tag
    md5 = 'md5sum.txt'

    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="lxml")
    links = soup.find_all('a')

    # get builds with .out includes in its name if md5sum.txt is ready
    md5_url = [url + link.get('href') for link in links if md5 in link.get('href')]
    if len(md5_url) == 1:
        out_url = {url + link.get('href') for link in links if '.out' in link.get('href')}
        return md5_url + list(out_url)
    LOG_MSG.info('---{} in {} is not ready yet.'.format(md5, tag))
    return []


def mail_to(email_dict, tag):
    """send email to a email list"""
    from_add = 'ryanwang@test.com'
    to_add = email_dict.values()
    msg = MIMEMultipart()
    msg['From'] = from_add
    msg['Subject'] = 'New build : {}'.format(tag)

    body = ''
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.test.com', 587)
    server.starttls()
    server.login(from_add, base64.b64decode('UwlWZUAmMjT1UTY=').decode('utf-8'))
    text = msg.as_string()
    server.sendmail(from_add, to_add, text)
    server.quit()


def start_download(item, urls, tag, email_dict):
    """start to download image and call it in main() to make code clean"""
    LOG_MSG.info('Start to download build: {}'.format(tag[:-1]))
    # new_tag format match previous one(# Home/Images/FortiWeb/v6.00/images/build0058/)
    # in case roll back to old ftp download script
    new_tag = (item['base_url'] + tag).replace('http://172.16.100.71', '/Home')[:-1] + '\n'
    item['path'] += tag  # item['path'] used for create local dir
    LOG_MSG.info('Local path is: {}'.format(item['path']))
    # make new tag dir
    subprocess.call('mkdir {}'.format(item['path']), shell=True)

    # download md5sum.txt first, open it, and del its url in the list
    download = ContentRequest(urls[0], 1, item['path'])
    download.start()
    time.sleep(0.1)
    all_md5 = open(item['path'] + urls[0].split('/')[-1], 'r').read()
    del urls[0]

    # try 5 times totally if urls is not empty
    # remove md5 check passed url from urls
    for i in range(5):
        passed_urls = []  # for those passed md5 check image
        for url in urls:
            # threads = 80
            LOG_MSG.info('Start to download file {} {}/{}'.format(
                url.split('/')[-1], urls.index(url) + 1, len(urls)))
            download = ContentRequest(url, 80, item['path'])
            download.start()

            # checksum = hashlib.md5(open('*.out', 'rb').read()).hexdigest()
            checksum = hashlib.md5(open(item['path'] + url.split('/')[-1], 'rb').read()).hexdigest()
            # remove the url if it passed md5 check
            if checksum in all_md5:
                LOG_MSG.info('md5 check passed in #{} time.'.format(i + 1))
                passed_urls.append(url)
            else:
                LOG_MSG.info('{} md5 check failed'.format(url.split('/')[-1]))

        # got the urls that did not passed md5 check
        urls = list(set(urls) - set(passed_urls))
        if not urls:
            send_path = '\\\\172.22.1.234' + item['path'].replace('/volume1', '').replace('/', '\\')
            mail_to(email_dict, send_path)
            LOG_MSG.info('{} Email send'.format(len(email_dict)))
            LOG_MSG.info('All files passed md5 check')
            LOG_MSG.info('{} downloaded successfully!'.format(tag[:-1]))
            # write the new tag to item['exist_tags']
            with open(item['exist_tags'], 'a') as file:
                file.write(new_tag)
                # recover the original item['path'] value in case there is more tags
                item['path'] = item['path'].replace(tag, '')
                break  # exit for loop
        else:
            LOG_MSG.info('---{} files failed md5 check in No.{} times: {}'.format(
                len(urls), i + 1, urls))

    # What valuables look like:
    # base_url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/build0058/'
    # base_url = 'http://172.16.100.71/Images/FortiWeb/v6.00/images/'
    # exist_tags = 'Build_download_test.txt'
    # threads = 80
    # path = '/volume1/FWB/test-image/fwb/'
    # /home/Images/FortiWeb/v6.00/images/build0056
    # Home/Images/FortiWeb/v6.00/images/build0058/
    # http://172.16.100.71/Images/FortiWeb/v6.00/images/build0058/


def arg_parser():
    """cli options parser function"""
    # the parameters for all branches
    # main_url used only to make base_url shorter
    main_url = 'http://172.16.100.71/Images/FortiWeb/'
    dict_build = {
        'c': {
            'base_url': main_url + 'v5.00/images/',
            'path': '/volume1/FWB/CM-image/5.0.0/',
            'exist_tags': '/volume1/FWB/Build_download.txt',
            'doc': 'CM_build',
            'seq': 3},
        'n': {
            'base_url': main_url + 'v6.00/images/',
            'path': '/volume1/FWB/CM-image/6.0.0/',
            'exist_tags': '/volume1/FWB/Build_download_NoMainBranch.txt',
            'doc': 'image_600',
            'seq': 1},
        'm': {
            'base_url': main_url + 'v6.00/images/NoMainBranch/fwb_6-0_openapi_mitb/',
            'path': '/volume1/FWB/CM-image/NoMainBranch/fwb_6-0_openapi_mitb/',
            'exist_tags': '/volume1/FWB/Build_download_NoMainBranch.txt',
            'doc': 'NoMainBranch_602',
            'seq': 6},
        'p': {
            'base_url': main_url + 'v6.00/images/NoMainBranch/fwb_6-0_adfs_proxy/',
            'path': '/volume1/FWB/CM-image/NoMainBranch/fwb-6-0_adfs_proxy/',
            'exist_tags': '/volume1/FWB/Build_download_NoMainBranch_ap.txt',
            'doc': 'NoMainBranch_602_adfs_proxy',
            'seq': 9},
        'w': {
            'base_url': main_url + 'v6.00/images/NoMainBranch/fwb_6-0_new_wvs/',
            'path': '/volume1/FWB/CM-image/NoMainBranch/fwb_6-0_new_wvs/',
            'exist_tags': '/volume1/FWB/Build_download_NoMainBranch_nwvs.txt',
            'doc': 'NoMainBranch_602_adfs_proxy',
            'seq': 9},
        't': {
            'base_url': main_url + 'v6.00/images/',
            'path': '/volume1/FWB/test-image/fwb/',
            'exist_tags': 'Build_download_test.txt',
            'doc': 'test_fwb',
            'seq': 99},
    }

    # the parser for command line options
    parser = argparse.ArgumentParser(description='HTTP image download script.')

    parser.add_argument("-c", "--CM_build", action="store_true", help="Download CM build")
    parser.add_argument("-n", "--image_600", action="store_true", help="Download 600 image")
    parser.add_argument(
        "-m", "--NoMainBranch_602", action="store_true", help="Download NoMainBranch_602")
    parser.add_argument(
        "-p", "--NoMainBranch_602_ap", action="store_true", help="Download NoMainBranch_602_ap")
    parser.add_argument(
        "-w", "--NoMainBranch_nwvs", action="store_true", help="Download NoMainBranch_nwvs")
    parser.add_argument("-t", "--Test_FWB", action="store_true", help="Only for test purpose")
    parser.add_argument("-a", "--all", action="store_true", help="Download all branches")
    parser.add_argument("-d", "--daemon", action="store_true", help="Rubn as a daemon")

    args = parser.parse_args()

    # put branch parameters in to build
    if args.CM_build:
        build = [dict_build['c']]
        is_test = False  # for test purpose only

    elif args.image_600:
        build = [dict_build['n']]
        is_test = False

    elif args.NoMainBranch_602:
        build = [dict_build['m']]
        is_test = False

    elif args.NoMainBranch_602_ap:
        build = [dict_build['p']]
        is_test = False

    elif args.NoMainBranch_nwvs:
        build = [dict_build['w']]
        is_test = False

    elif args.Test_FWB:
        build = [dict_build['t']]
        is_test = True

    elif args.all:
        dict_build.pop('t', None)  # exclusive test one
        build = dict_build.values()
        build = sorted(build, key=lambda x: x['seq'])  # sort as seq to download 6.0 first
        is_test = False

    else:
        sys.exit('Please use -h or --help for help')

    return build, is_test


def main():
    """Main function for http download"""
    # email list
    email_dict = {
        'dwguo': 'dwguo@test.com',
        'jyzheng': 'jyzheng@test.com',
        'fhxi': 'fhxi@test.com',
        'taosong': 'taosong@test.com',
        'yangsong': 'yangsong@test.com',
        'shchen': 'shchen@test.com',
        'luliang': 'luliang@test.com',
        'xiaoyang': 'yangxiao@test.com',
        'wmqi': 'wmqi@test.com',
        'fwang01': 'fwang01@test.com',
        'hyyi': 'hyi@test.com',
        'zhangpp': 'pengpengzhang@test.com',
        'xnluo': 'xnluo@test.com',
        'huanliu': 'huanliu@test.com',
        'wjdu': 'wjdu@test.com',
        'zwk': 'wkzhang@test.com',
        'hml': 'minlinghan@test.com',
        'ibiw': 'ibiw@test.com',
        'ryanwang': 'ryanwang@test.com',
    }

    # for cli option -t test
    email_test = {
        'ryanwang': 'ryanwang@test.com',
        'ibiw': 'ibiw@163.com',
    }

    build, is_test = arg_parser()
    for i, item in enumerate(build, 1):
        # base_url = item['base_url']
        # exist_tags = item['exist_tags']
        # path = item['path']

        tags = check_tag(item['base_url'], item['exist_tags'])
        if not tags:
            if i == len(build) and len(build) > 1:
                LOG_MSG.info('There is no new build for all branches')
            elif len(build) == 1:
                LOG_MSG.info('There is no new build for: {}'.format(item['doc']))

        for tag in tags:
            urls = get_urls(item['base_url'], tag)
            # download urls if not Test
            if urls and not is_test:
                time_start = datetime.datetime.now()
                start_download(item, urls, tag, email_dict)
                LOG_MSG.info('Time used of {} is : {}\n'.format(
                    tag, datetime.datetime.now() - time_start))
            # only download first 2 .out files and Email to admin if test is True
            elif urls and is_test:
                urls = urls[:3]
                time_start = datetime.datetime.now()
                start_download(item, urls, tag, email_test)
                LOG_MSG.info('Time used of {} is : {}\n'.format(
                    tag, datetime.datetime.now() - time_start))
        time.sleep(3)


if __name__ == '__main__':
    # track all the branches every 15 minutes
    # run as daemon if with -d or --daemon
    if len(sys.argv) == 3 and sys.argv[-1] == '-d':
        print('xxx')
        with daemon.DaemonContext():
            while True:
                main()
                time.sleep(900)

    else:
        try:
            while True:
                main()
                time.sleep(900)
        except KeyboardInterrupt:
            sys.exit('\nQuit with Ctrl-c')  # capture ctrl-c exit in cli
        # use a general exception to catch any error
        except Exception as any_error:
            LOG_MSG.warning(any_error)
