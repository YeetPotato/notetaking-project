#link for reference: https://developers.google.com/workspace/drive
#pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
from random import randint #just for fun
import os.path #some file handling stuff
import json

#google drive related functions and libaries
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import google.auth
from googleapiclient.errors import HttpError    
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive'] #defines permissions; in this case it allows edit and re

def get_drive_service(): #creates service(used to access and modify things)
    creds = None #login system
    if os.path.exists('token.json'): #cache for user
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else: #this is when first attempt. Is using manual for now due to errors
            flow = InstalledAppFlow.from_client_secrets_file(
                'info.json', SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob' # Set the redirect URI to Out-of-Band
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'Please visit this URL: {auth_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open('token.json', 'w') as token: #saving cache
            token.write(creds.to_json())
    
    service = build('drive', 'v3', credentials=creds) #returns service
    return service

def upload(service,path,name,temp_path='downloads/temp.docx',targetMimeType='application/vnd.google-apps.document'):
    basename=str(os.path.basename(path)) #for refrence for now
    file_metadata = {'name':name,'mimeType':targetMimeType} #the thing being uploaded
    
    media = MediaFileUpload(path, mimetype="application/pdf") #object for uploading
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    # print(f'File ID: {file.get("id")}')

    return file.get("id")

def download_file(service,file_id):
    request = service.files().get_media(fileId=file_id) #files is class for files/ .get is method to get specific file/ alt=media sets it as download

    metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute() #getting name and type info
    original_filename = metadata.get('name')#usually infcludes file type ie: test.pdf
    mime_type = metadata.get('mimeType')
    destination = os.path.join("./downloads", original_filename) 

    # #handing exports for docs
    if(mime_type=="application/vnd.google-apps.document"):
        mime_type = 'application/pdf' # .pdf
        destination = os.path.join("./downloads",original_filename + '.pdf')
    
    request = service.files().export_media(fileId=file_id, mimeType=mime_type)#download request

    fh = io.FileIO(destination, 'wb') #obj for info 
    downloader = MediaIoBaseDownload(fh, request) #googleapiclient.http libary, chunks downloads
    done = False

    while not done: #basic chunking for now
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")

def getFolderId(service,folder_name='Notetaking test'):
    search_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false" #listing folders with possible names
    results = service.files().list(q=search_query, pageSize=1, fields="files(id, name)").execute() #filtering queries
    #more filetering
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        return None
    
def move_to_target_foler(service,file_id,folder_id):
  try:
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents"))
    # Move the file to the new folder
    file = (
        service.files()
        .update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        )
        .execute()
    )
    return file.get("parents")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None

def copy_to_folder(folder="163VEIezinnshb3jc1IBa-4oXdiwv2_qK",docID="1-eDdjq1dBI9wNjgEn6Ip16PFTWBRCYgTFAPNW1am5tw"):
    temp_obj=get_drive_service()
    download_file(temp_obj,docID)

    fileid=upload(temp_obj,'downloads/1+1=7.pdf',f'{randint(1,10000)}+{randint(1,1000)}={randint(2,2000)}.pdf')
    folder=getFolderId(temp_obj)
    move_to_target_foler(temp_obj,fileid,folder)

    user_name=temp_obj.about().get(fields='user/displayName').execute().get('user', {}).get('displayName')
    temp_data={}

    try:
        with open(f'users/{user_name}.json','r') as file:
            temp_data=json.load(file)
            temp_data['saved_files'].append(fileid)
    except:
        temp_data['saved_files']=[fileid]
    temp_data['saved_folder']=folder

    with open(f'users/{user_name}.json','w') as file:
        json.dump(temp_data,file,indent=4)

copy_to_folder()
