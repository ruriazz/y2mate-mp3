import json
import os
import contextlib
import requests
import time
from typing import Optional, Dict, Any
from copy import deepcopy
from tqdm import tqdm
from secrets import token_urlsafe


FOLDER_SAVE = './Musics'
REPLACE_ON_EXISTS = True

class Helpers:
    @staticmethod
    def y2mate():
        try:
            for source in Helpers.get_sources():
                save_to = os.path.join(FOLDER_SAVE, source.replace(':', '/').replace('.txt', ''))
                with open(source, 'r') as file:
                    urls = [
                        f"{i}".strip()
                        for i in (file.read() or '').split('\n')
                        if f"{i}".strip()
                    ]
                    file.close()

                with contextlib.suppress(Exception):
                    os.makedirs(save_to, exist_ok=True)

                new_urls = deepcopy(urls)
                for _, source_url in enumerate(urls):
                    url, filename = Helpers.get_audio_link(source_url)
                    print(f"\nStarting download '{filename}'")
                    download_save = f"{save_to}/{filename}"
                    if os.path.exists(download_save):
                        if REPLACE_ON_EXISTS:
                            os.remove(download_save)
                        else:
                            download_save = f"{save_to}/{token_urlsafe(6)}_{filename}"

                    if Helpers.download(url, download_save):
                        new_urls.remove(source_url)
                        open(source, 'w').write("\n".join(new_urls))
                print(f'\n\n{save_to} Complete!\n\n')
                os.remove(source)
            print('\nComplete All!!!!\n')
            return True
        except Exception as err:
            print('\nRetry ...\n')
            return False
        
    @staticmethod
    def get_sources():
        file_list = os.listdir('./sources')
        return sorted([os.path.join('./sources', file) for file in file_list if os.path.isfile(os.path.join('./sources', file))])

    @staticmethod
    def get_audio_link(source: str):
        if not (analize_result := Helpers.analize_url(source)):
            return

        mp3 = analize_result['links']['mp3']

        sf = 0
        data_link = None
        for key in mp3:
            link = mp3[key]
            if link['f'] == 'mp3':
                size = float((link.get('size') or '0 MB').split(' ')[0])
                if size >= sf:
                    data_link = link

        if data_link:
            if converted_link := Helpers.get_convert(analize_result['vid'], data_link['k']):
                if not converted_link.get('dlink'):
                    print('Got response:', json.dumps(converted_link, indent=3))
                    dly = (float(converted_link['e_time']) / 100) + 1
                    print(f'time.sleep({dly})')
                    time.sleep(dly)

                return converted_link['dlink'], f"{analize_result['title']}.{data_link['f']}"

    @staticmethod
    def analize_url(source: str) -> Optional[Dict[str, Any]]:
        with contextlib.suppress(Exception):
            resp = requests.post('https://www.y2mate.com/mates/id814/analyzeV2/ajax', data={
                'k_query': source,
                'k_page': 'home',
                'hl': 'id',
                'q_auto': 0
            })

            if resp.status_code == 200:
                return resp.json()
            
    @staticmethod
    def get_convert(vid: str, k: str) -> Optional[Dict[str, Any]]:
        resp = requests.post('https://www.y2mate.com/mates/convertV2/index', data={'vid': vid, 'k': k})
        if resp.status_code == 200:
            return resp.json()
        
    @staticmethod
    def download(source: str, location: str) -> bool:
        response = requests.get(source, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        try:
            with open(location, 'wb') as file:
                progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))
                progress_bar.close()
            file.close()
            print(f'File saved at "{location}"')
            return True
        except Exception as err:
            print('Error:', err)
            os.remove(location)
            return False




if __name__ == '__main__':
    nd = Helpers.y2mate()
    while not nd:
        time.sleep(2.5)
        nd = Helpers.y2mate()
