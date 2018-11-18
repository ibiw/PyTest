import threading
import random
import time


def splitter_words(words):
    words_list = words.split()
    new_list = []

    while words_list:
        new_list.append(words_list.pop(random.randrange(0, len(words_list))))
    print(new_list)
    print('\n')
    time.sleep(1)

if  __name__ == "__main__":
    words = 'I am a handsome beast. World.'
    num_threads = 5
    thread_list = []

    print('Starting...\n')
    for i in range(num_threads):
        t = threading.Thread(target=splitter_words, args=(words,))
        t.start()
        thread_list.append(t)
    print('\nThread Count:' + str(threading.activeCount()))
    print('Ending...\n')
