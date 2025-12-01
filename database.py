#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
import mysql.connector
from openai import OpenAI
import openai
import io
import os
client = OpenAI(api_key="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")
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Yeet-5679",
  database="notetaker_data"
)

# hash the password for safety
def add_user(username, password):
    mycursor = mydb.cursor()
    sql = "insert into user_info (Username, Password, User_ID) select %s, %s, coalesce(max(User_ID), 0) + 1 from user_info"
    val = (username, password)
    try:
      mycursor.execute(sql, val)
      mydb.commit()
      mycursor.close()
      return "Attempt successful."
    except Exception as e:
      mydb.rollback()
      mycursor.close()
      return f"ERROR: {e}"
    """except mysql.connector.errors.IntegrityError as e:
      mydb.rollback()
      mycursor.close()
      return "ERROR: Username is taken."""
    
    
def log_in(username, password):
  mycursor = mydb.cursor()
  sql = "select Password from user_info where Username = %s"
  val = (username,)
  mycursor.execute(sql, val)
  id = mycursor.fetchone()
  if id:
    return id[0] == password
  return "ERROR: Username not found."
    
def get_id(username):
  mycursor = mydb.cursor()
  sql = "select User_ID from user_info where Username = %s"
  val = (username,)
  mycursor.execute(sql, val)
  id = mycursor.fetchone()
  mycursor.close()
  if id:
    return id[0]
  return -1
  
def add_chunk(userid, meetingname, chunkid, total, audio):
  mycursor = mydb.cursor()
  sql = "insert into processing (User_ID, Meeting_Name, Chunk_ID, Audio, Total_Chunks) values (%s, %s, %s, %s, %s)"
  val = (userid, meetingname, chunkid, audio, total)
  try:
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()
    return "Attempt successful."
  except mysql.connector.errors.IntegrityError as e:
    mydb.rollback()
    mycursor.close()
    return "ERROR: Chunk already sent."
  except Exception as e:
    mydb.rollback()
    mycursor.close()
    return f"ERROR: {e}"

def get_transcript(userid, meetingname, chunkid):
  mycursor = mydb.cursor()
  sql = "select Audio from processing where User_ID = %s and Meeting_Name = %s and Chunk_ID = %s"
  val = (userid, meetingname, chunkid)
  mycursor.execute(sql, val)
  audio = mycursor.fetchone()
  mycursor.close()
  if audio:
    audio_file = io.BytesIO(audio[0])
    audio_file.name = "audio.wav"
    try:
      transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
      )
    except openai.OpenAIError as e:
      return f"OPENAIERROR: {e}"
    except Exception as e:
      return f"ERROR: {e}"
    mycursor = mydb.cursor()
    sql2 = "update processing set Transcript = %s where User_ID = %s and Meeting_Name = %s and Chunk_ID = %s"
    val2 = (transcript.text, userid, meetingname, chunkid)
    try:
      mycursor.execute(sql2, val2)
      mydb.commit()
      mycursor.close()
      return "Attempt successful."
    except Exception as e:
      mydb.rollback()
      mycursor.close()
      return f"ERROR: {e}"
  return "ERROR: Audio not found."

def generate_summary(userid, meetingname):
  mycursor = mydb.cursor()
  sql = "select Transcript from processing where User_ID = %s and Meeting_Name = %s"
  val = (userid, meetingname)
  mycursor.execute(sql, val)
  chunks = mycursor.fetchall()
  mycursor.close()
  if chunks:
    print("sup")
    full_transcript = " ".join(chunk[0] for chunk in chunks)
    print("dude")
    messages = [
        {"role": "system", "content": "You are an assistant that summarizes and takes notes from transcripts. Avoid using specially formatted text unless absolutely necessary."},
        {"role": "user", "content": f"Here is the transcript:\n\n{full_transcript}\n\nPlease provide a summary."}
    ]
    try:
      summary_response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=messages
      )
      summary = summary_response.choices[0].message.content
    except openai.OpenAIError as e:
      return f"OPENAIERROR: {e}"
    except Exception as e:
      return f"ERROR: {e}"
    messages.append({"role": "assistant", "content": summary})
    messages.append({"role": "user", "content": "Now give me detailed notes."})
    try:
      notes_response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=messages
      )
      notes = notes_response.choices[0].message.content
    except openai.OpenAIError as e:
      return f"OPENAIERROR: {e}"
    except Exception as e:
      return f"ERROR: {e}"
    print(summary)
    print(len(notes))
    mycursor = mydb.cursor()
    sql2 = "insert into summaries values (%s, %s, %s, %s)"
    val2 = (userid, meetingname, summary, notes)
    try:
      mycursor.execute(sql2, val2)
      mydb.commit()
      mycursor.close()
      return "Attempt successful."
    except Exception as e:
      mydb.rollback()
      mycursor.close()
      return f"ERROR: {e}"
  return "ERROR: No chunks found."

def has_all_chunks(userid, meetingname):
  mycursor = mydb.cursor()
  sql = "select Total_Chunks from processing where User_ID = %s and Meeting_Name = %s"
  val = (userid, meetingname)
  mycursor.execute(sql, val)
  counts = mycursor.fetchall()
  mycursor.close()
  if counts:
    print(len(counts))
    print(counts[0][0])
    return len(counts) == counts[0][0]
  return False
  
def process_chunk(username, meetingname, chunkid, total, audio):
  print("hi")
  id = get_id(username)
  if id == -1:
    return "ERROR: UserID not found."
  result = add_chunk(id, meetingname, chunkid, total, audio)
  if result != "Attempt successful.":
    return result
  result = get_transcript(id, meetingname, chunkid)
  if result != "Attempt successful.":
    print("phutt")
    return result
  if has_all_chunks(id, meetingname):
    print("summarizing")
    return generate_summary(id, meetingname)
  return "Not all chunks received."

def get_summary(username, meetingname):
  id = get_id(username)
  if id == -1:
    return "ERROR: UserID not found."
  sql = "select Summary from summaries where User_ID = %s and Meeting_Name = %s"
  val = (id, meetingname)
  mycursor = mydb.cursor()
  mycursor.execute(sql, val)
  result = mycursor.fetchone()
  if result is None:
    return "ERROR: Summary not generated. Chunks may not all be sent."
  if result:
    return result[0]
  return "ERROR: No such meeting found."

def get_notes(username, meetingname):
  id = get_id(username)
  if id == -1:
    return "ERROR: UserID not found."
  sql = "select Notes from summaries where User_ID = %s and Meeting_Name = %s"
  val = (id, meetingname)
  mycursor = mydb.cursor()
  mycursor.execute(sql, val)
  result = mycursor.fetchone()
  if result is None:
    return "ERROR: Notes not generated. Chunks may not all be sent."
  if result:
    return result[0]
  return "ERROR: No such meeting found."
  
"""
1. add_user
2. log_in
3. all the database stuff
  - receive username and all chunk info
  - use get_id to add_chunk
  - get_transcript immediately after
  - check if all chunks present
  - if so, generate summary, otherwise wait
4. get_summary
5. get_notes
"""


#mycursor.execute("insert into processing values (1, 'asdf', 0, 'potato', 'NULL')")
#mydb.commit()

# print(add_user("phutt3", "potato"))
# print(get_id("potato"))
# print(add_chunk(1, "asdf", 2, "potato"))
"""
with open("D:/Leo/notetaker_project/harvard.wav", "rb") as f:
  testaudio = f.read()
add_chunk(0, "test", 1, testaudio)"""
#generate_summary(0, "potato")
