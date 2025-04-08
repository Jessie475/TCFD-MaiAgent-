import json
import os
import sseclient
from urllib.parse import urljoin
from typing import Any, Dict, List, Union, Generator
import urllib3
import requests

# 禁用不安全請求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MaiAgentHelper:
    def __init__(
        self,
        api_key,
        base_url='http://140.119.63.98:443/api/v1/',
        storage_url='https://nccu-ici-rag-minio.jp.ngrok.io/magt-bkt'
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.storage_url = storage_url

    def create_conversation(self, web_chat_id):
        try:
            # 建立 conversation
            # response = requests.post(
            #     url=f'{self.base_url}conversations/',
            #     headers={'Authorization': f'Api-Key {self.api_key}'},
            #     json={
            #         'webChat': web_chat_id,
            #     }
            # )
            response = requests.post(
                url=f'{self.base_url}conversations/',
                headers={'Authorization': f'Api-Key {self.api_key}'},
                json={
                    'webChat': web_chat_id,
                },
                verify=False  # 忽略 SSL 驗證
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"回應內容: {e.response.text}")
            exit(1)
        except Exception as e:
            print(f"其他錯誤: {str(e)}")
            exit(1)

    def send_message(self, conversation_id, content, attachments=None):
        try:
            # 傳送訊息
            # response = requests.post(
            #     url=f'{self.base_url}messages/',
            #     headers={'Authorization': f'Api-Key {self.api_key}'},
            #     json={
            #         'conversation': conversation_id,
            #         'content': content,
            #         'attachments': attachments or [],
            #     }
            # )
            response = requests.post(
                url=f'{self.base_url}messages/',
                headers={'Authorization': f'Api-Key {self.api_key}'},
                json={
                    'conversation': conversation_id,
                    'content': content,
                    'attachments': attachments or [],
                },
                verify=False  # 忽略 SSL 驗證
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(response.text)
            print(e)
            exit(1)

        return response.json()

    def get_upload_url(self, file_path, model_name, field_name='file'):
        assert os.path.exists(file_path), 'File does not exist'

        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)

        url = f'{self.base_url}upload-presigned-url/'

        headers = {'Authorization': f'Api-Key {self.api_key}', 'Content-Type': 'application/json'}

        payload = {
            'filename': filename,
            'fileSize': file_size,
            'modelName': model_name,
            'fieldName': field_name
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)  # 忽略 SSL 驗證

        response.raise_for_status()

        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
            return None


    def upload_file_to_s3(self, file_path, upload_data):
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            data = {
                'key': upload_data['fields']['key'],
                'x-amz-algorithm': upload_data['fields']['x-amz-algorithm'],
                'x-amz-credential': upload_data['fields']['x-amz-credential'],
                'x-amz-date': upload_data['fields']['x-amz-date'],
                'policy': upload_data['fields']['policy'],
                'x-amz-signature': upload_data['fields']['x-amz-signature'],
            }

            # response = requests.post(self.storage_url, data=data, files=files)
            response = requests.post(self.storage_url, data=data, files=files, verify=False)  # 忽略 SSL 驗證

            if response.status_code == 204:
                print('File uploaded successfully')
                return upload_data['fields']['key']
            else:
                print(f'Error uploading file: {response.status_code}')
                print(response.text)
                return None

    def update_attachment(self, conversation_id, file_id, original_filename):
        url = f'{self.base_url}conversations/{conversation_id}/attachments/'

        payload = {
            'file': file_id,
            'filename': original_filename,
            'type': 'image',
        }

        try:
            # response = requests.post(url, headers=headers, json=payload)
            response = requests.post(url, headers=HEADERS, json=payload, verify=False)  # 忽略 SSL 驗證
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(response.text)
            print(e)
            exit(1)
        except Exception as e:
            print(e)
            exit(1)

        return response.json()
    
    def update_attachment_without_conversation(self, file_id, original_filename, type):
        url = f'{self.base_url}attachments/'

        headers = {
            'Authorization': f'Api-Key {self.api_key}',
        }

        payload = {
            'file': file_id,
            'filename': original_filename,
            'type': type,
        }

        try:
            # response = requests.post(url, headers=headers, json=payload)
            response = requests.post(url, headers=headers, json=payload, verify=False)  # 忽略 SSL 驗證
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(response.text)
            print(e)
            exit(1)
        except Exception as e:
            print(e)
            exit(1)

        return response.json()

    def update_chatbot_files(self, chatbot_id, file_key, original_filename):
        url = f'{self.base_url}chatbots/{chatbot_id}/files/'

        headers = {
            'Authorization': f'Api-Key {self.api_key}',
        }

        payload = {'files': [{'file': file_key, 'filename': original_filename}]}

        try:
            # response = requests.post(url, headers=headers, json=payload)
            response = requests.post(url, headers=headers, json=payload, verify=False)  # 忽略 SSL 驗證
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(response.text)
            print(e)
            exit(1)
        except Exception as e:
            print(e)
            exit(1)

        return response.json()

    def upload_batch_qa_file(self, web_chat_id: str, file_key: str, original_filename: str):
        url = f'{self.base_url}web-chats/{web_chat_id}/batch-qas/'

        try:
            # response = requests.post(
            #     url,
            #     headers={
            #         'Authorization': f'Api-Key {self.api_key}',
            #     },
            #     json={
            #         'file': file_key,
            #         'filename': original_filename,
            #     }
            # )
            response = requests.post(
                url,
                headers={
                    'Authorization': f'Api-Key {self.api_key}',
                },
                json={
                    'file': file_key,
                    'filename': original_filename,
                },
                verify=False  # 忽略 SSL 驗證
            )
            response.raise_for_status()
            print('Successfully uploaded batch QA file')
        except requests.exceptions.RequestException as e:
            print(response.text)
            print(e)
            exit(3)
        except Exception as e:
            print(e)
            exit(3)

        return response.json()
    

    def download_batch_qa_excel(self, webchat_id: str, batch_qa_file_id: str):
        url = urljoin(self.base_url, f'web-chats/{webchat_id}/batch-qas/{batch_qa_file_id}/export-excel/')

        headers = {
            'Authorization': f'Api-Key {self.api_key}',
        }

        # response = requests.get(url, headers=headers)
        response = requests.get(url, headers=headers, verify=False)  # 忽略 SSL 驗證

        if response.status_code == 200:
            content_disposition = response.headers.get('Content-Disposition')
            filename = 'chatbot_records.xlsx'
            if content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')

            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f'Successfully downloaded: {filename}')
            return filename
        else:
            print(f'Error: {response.status_code}')
            print(response.text)
            return None

    def upload_attachment(self, conversation_id, file_path):
        upload_url = self.get_upload_url(file_path, 'attachment')
        file_key = self.upload_file_to_s3(file_path, upload_url)

        return self.update_attachment(conversation_id, file_key, os.path.basename(file_path))

    def upload_attachment_without_conversation(self, file_path, type):
        upload_url = self.get_upload_url(file_path, 'attachment')
        file_key = self.upload_file_to_s3(file_path, upload_url)
        return self.update_attachment_without_conversation(file_key, os.path.basename(file_path), type)

    def upload_knowledge_file(self, chatbot_id, file_path):
        upload_url = self.get_upload_url(file_path, 'chatbot-file')
        file_key = self.upload_file_to_s3(file_path, upload_url)

        return self.update_chatbot_files(chatbot_id, file_key, os.path.basename(file_path))

    def delete_knowledge_file(self, chatbot_id, file_id):
        url = f'{self.base_url}chatbots/{chatbot_id}/files/{file_id}/'

        headers = {
            'Authorization': f'Api-Key {self.api_key}',
        }

        try:
            # response = requests.delete(url, headers=headers)
            response = requests.delete(url, headers=headers, verify=False)  # 忽略 SSL 驗證
            response.raise_for_status()
            print(f'成功刪除知識庫檔案，ID: {file_id}')
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"回應內容: {e.response.text}")
        except Exception as e:
            print(f"其他錯誤: {str(e)}")

    def get_conversations(url: str, headers) -> List[Dict[str, Any]]:
        """
        從 API 獲取對話列表並返回所有訊息
        """
        all_messages = []  # 存放所有訊息的列表

        # while url:
        response = requests.get(url, headers)
            # if response.status_code != 200:
            #     print(response.text)
            #     print(f"請求失敗，狀態碼: {response.status_code}")
            #     break

            # data = response.json()
            # all_messages.extend(data["results"])  # 累積結果
            # url = data.get("next")  # 更新為下一個請求的 URL
        
        data = json.loads(response.text)
        print(data['results'][1]['content'])
        return all_messages

    def get_inbox_items(self):
        inbox_items = []

        url = f'{self.base_url}inboxes/'
        while True:
            try:
                # response = requests.get(
                #     url=url,
                #     headers={'Authorization': f'Api-Key {self.api_key}'},
                # )
                response = requests.get(
                    url=url,
                    headers={'Authorization': f'Api-Key {self.api_key}'},
                    verify=False  # 忽略 SSL 驗證
                )
                response.raise_for_status()
                data = response.json()
                inbox_items.extend(data['results'])
                url = data.get('next')
                if not url:
                    break
            except requests.exceptions.RequestException as e:
                print(f"請求錯誤: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"回應內容: {e.response.text}")
                exit(1)
            except Exception as e:
                print(f"其他錯誤: {str(e)}")
                exit(1)

        return inbox_items

    def display_inbox_items(self, inbox_items):
        for inbox_item in inbox_items:
            inbox_id = inbox_item['id']
            webchat_id = inbox_item['channel']['id']
            webchat_name = inbox_item['channel']['name']
            print(f'Inbox ID: {inbox_id}, Webchat ID: {webchat_id}, Webchat Name: {webchat_name}')

    def create_chatbot_completion(self, chatbot_id: str, content: str, attachments: list = None, conversation_id: str = None, is_streaming: bool = False) -> Union[dict, Generator]:
        """
        建立聊天機器人回應

        Args:
            chatbot_id: 聊天機器人 ID
            content: 訊息內容
            attachments: 附件列表
            conversation_id: 對話 ID
            is_streaming: 是否使用串流模式

        Returns:
            串流模式時回傳 Generator，非串流模式回傳 dict
            回應格式: {
                "conversationId": str,
                "content": str,
                "done": bool
            }
        """
        url = f'{self.base_url}chatbots/{chatbot_id}/completions/'

        headers = {
            'Authorization': f'Api-Key {self.api_key}',
        }
        
        payload = {
            'conversation': conversation_id,
            'message': {
                'content': content,
                'attachments': attachments or []
            },
            'is_streaming': is_streaming
        }

        try:
            if not is_streaming:
                return self._handle_non_streaming_completion(url, headers, payload)
            return self._handle_streaming_completion(url, headers, payload)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"請求失敗: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\n回應內容: {e.response.text}"
            raise RuntimeError(error_msg)

    def _handle_non_streaming_completion(self, url: str, headers: dict, payload: dict) -> dict:
        """處理非串流模式的回應"""
        # response = requests.post(
        #     url,
        #     headers=headers,
        #     json=payload
        # )
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False  # 忽略 SSL 驗證
        )
        response.raise_for_status()
        return response.json()

    def _handle_streaming_completion(self, url: str, headers: dict, payload: dict) -> Generator:
        """處理串流模式的回應"""
        # response = requests.post(
        #     url,
        #     headers=headers,
        #     json=payload,
        #     stream=True
        # )
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            verify=False  # 忽略 SSL 驗證
        )
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    yield data
                except json.JSONDecodeError as e:
                    print(f"JSON 解析失敗: {event.data}")
                    continue


