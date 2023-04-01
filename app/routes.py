import os
import openai
import json
import trafilatura
import tiktoken
from app import app, db, login_manager
from app.forms import SummarizeFromText, SummarizeFromURL, openAI_debug_form
from app.models import Entry_Post
from flask import render_template, flash, redirect, url_for, request
from trafilatura import extract
from trafilatura.settings import use_config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Float, Integer, String, MetaData, ForeignKey
from flask_migrate import Migrate
from flask_login import login_required, current_user, UserMixin
from flask_login import login_user, logout_user, login_required

# -------------------- Utility functions --------------------

#This is the function that will be called to summarize the text
def num_tokens_from_string(prompt):
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(prompt))
    return num_tokens

#This is the function that will be called to trip the text to the maximum number of tokens
def trim_text_to_tokens(text, max_tokens):
    encoding = tiktoken.get_encoding("cl100k_base")
    return encoding.decode(encoding.encode(text)[:max_tokens])

#calculate average senence length in tokens
def avg_sentence_length(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)/len(text.split('.')) 

#Used to inject the enumerate function into the templates
@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)

# Custom Jinja filter to replace newline characters with <br> tags
def nl2br(value):
    return value.replace('\n', '<br>')


# -------------------- Basic Authentication --------------------


#Define the Username and Password to access the Logs
summarizeMeUser = os.getenv("summarizeMeUser") or "user1"
summarizeMePassword = os.getenv("summarizeMePassword") or "pass1"
users = {summarizeMeUser:{'pw':summarizeMePassword}}
 
class User(UserMixin):
  pass

#Define the Username and Password to access the Logs and Debugging  
@login_manager.user_loader
def user_loader(username):
  if username not in users:
    return

  user = User()
  user.id = username
  return user

@login_manager.request_loader
def request_loader(request):
  username = request.form.get('username')
  if username not in users:
    return
  user = User()
  user.id = username
  user.is_authenticated = request.form['pw'] == users[username]['pw']
  return user



# -------------------- Flask app configurations --------------------
app.jinja_env.filters['nl2br'] = nl2br
openai.api_key = os.getenv("OPENAI_API_KEY")

# -------------------- Global variables --------------------

openAI_summary = "" 
test2summarize = ""
url = ""
global_is_trimmed = False
global_form_prompt = ""




# -------------------- Routes --------------------
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/summarizeText', methods=['GET', 'POST'])
def summarizeText():
    form = SummarizeFromText()
    global openAI_summary
    global test2summarize
    global url
    url = ""
    global global_is_trimmed
    global global_form_prompt
    if form.validate_on_submit():
      #openAI_summary = openAI_summarize("Summarize the below text in a few short bullet points: \n" + form.summarize.data)
      openAI_summary, global_is_trimmed, global_form_prompt = openAI_summarize("Summarize the below text in a few short bullet points: \n\n" + test2summarize)
      test2summarize = form.summarize.data
      return redirect(url_for('summarizeText'))
    if (openAI_summary):
      write_to_db(0,"0",test2summarize,openAI_summary["choices"][0]['message']['content'])
      # Calculate token count and average tokens per sentence
      token_count = num_tokens_from_string(test2summarize)
      avg_tokens_per_sentence = avg_sentence_length(test2summarize) 
      openAI_summary_str = json.dumps(openAI_summary, indent=4)     
      return render_template(
        'summarizeText.html', 
        title='Summarize From Text', 
        form=form,
        test2summarize=test2summarize.split('\n'), 
        openAI_summary=openAI_summary["choices"][0]['message']['content'].split('\n'),  
        token_count=token_count, avg_tokens_per_sentence=avg_tokens_per_sentence, 
        openAI_json=openAI_summary_str, 
        is_trimmed=global_is_trimmed, 
        form_prompt_nerds=global_form_prompt)
    else:
        return render_template('summarizeText.html', title='Summarize From Text', form=form)


@app.route('/summarizeURL', methods=['GET', 'POST'])
def summarizeURL():
    form = SummarizeFromURL()
    global openAI_summary
    global test2summarize
    global url
    global global_is_trimmed
    global global_form_prompt
    if form.validate_on_submit():
      newconfig = use_config()
      newconfig.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
      downloaded = trafilatura.fetch_url(form.summarize.data)
      url = form.summarize.data
      test2summarize = extract(downloaded, config=newconfig)
      #openAI_summary = openAI_summarize("Summarize the below text in a few short bullet points: \n\n" + test2summarize)
      openAI_summary, global_is_trimmed, global_form_prompt = openAI_summarize("Summarize the below text in a few short bullet points: \n\n" + test2summarize)
      return redirect(url_for('summarizeURL'))
    if (openAI_summary):
      write_to_db(1,url,test2summarize,openAI_summary["choices"][0]['message']['content'])
      # Calculate token count and average tokens per sentence
      token_count = num_tokens_from_string(test2summarize)
      avg_tokens_per_sentence = avg_sentence_length(test2summarize)
      openAI_summary_str = json.dumps(openAI_summary, indent=4)
      #return render_template('summarizeURL.html', title='Summarize From URL', form=form, test2summarize=test2summarize.split('\n'), openAI_summary=openAI_summary["choices"][0]['message']['content'].split('\n'), token_count=token_count, avg_tokens_per_sentence=avg_tokens_per_sentence, openAI_json=openAI_summary_str, is_trimmed=global_is_trimmed, form_prompt_nerds=global_form_prompt)
      return render_template(
        'summarizeURL.html',
        title='Summarize From URL',
        form=form,
        test2summarize=test2summarize.split('\n'),
        openAI_summary=openAI_summary["choices"][0]['message']['content'].split('\n'),
        token_count=token_count,
        avg_tokens_per_sentence=avg_tokens_per_sentence,
        openAI_json=openAI_summary_str,
        is_trimmed=global_is_trimmed,
        form_prompt_nerds=global_form_prompt
      )
    else:
        return render_template(
          'summarizeURL.html',
          title='Summarize From URL',
          form=form
        )



# Routes for the login and logout pages
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form.get('username')
    if request.form.get('pw') == users.get(username, {}).get('pw'):
      user = User()
      user.id = username
      login_user(user)
      return redirect(url_for('logs'))
  return render_template('login.html')

@app.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('index'))

@app.route('/logs')
@login_required
def logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    entries = Entry_Post.query.order_by(Entry_Post.id.desc()).paginate(page=page, per_page=per_page)
    return render_template('logs.html', entries=entries)    

@app.route('/openAI-debug', methods=['GET', 'POST'])
@login_required
def openAI_debug():
    form = openAI_debug_form()
    global openAI_summary
    global test2summarize
    if form.validate_on_submit():
      openai_api_form_prompt = form.openAI_debug_form_prompt.data
      openai_api_form_key = form.openAI_debug_form_key.data
      test2summarize = openai_api_form_prompt
      openAI_summary = openAI_summarize_debug(openai_api_form_key, openai_api_form_prompt)
      return redirect(url_for('openAI_debug'))
    if (openAI_summary):
      openAI_summary_str = json.dumps(openAI_summary, indent=4)
      return render_template('openai-debug.html', title='openAI-debug', form=form,openai_key = os.getenv("OPENAI_API_KEY"), test2summarize=test2summarize, openAI_summary=openAI_summary_str, just_summary = openAI_summary["choices"][0]['message']['content'] )
    else:
        return render_template('openai-debug.html', title='openAI-debug', form=form, openai_key = os.getenv("OPENAI_API_KEY"))


# Functions to call the OpenAI API
def openAI_summarize(form_prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # Count tokens in the form_prompt
    token_count = num_tokens_from_string(form_prompt)
    max_tokens = 3500
    is_trimmed = False
    # Trim the form_prompt if the token count exceeds the model's maximum limit
    if token_count > max_tokens:
        form_prompt = trim_text_to_tokens(form_prompt, max_tokens)
        is_trimmed = True
    message = {"role": "user", "content": form_prompt}
    print("message: " + str(message))
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[message],#[{"role": "user", "content": form_prompt}],
      temperature=0.7,
      max_tokens=500,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=1
    )
    return response, is_trimmed, form_prompt

def openAI_summarize_debug(form_openai_key, form_prompt):
    openai.api_key = form_openai_key
    message = {"role": "user", "content": form_prompt}
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[message],
      temperature=0.7,
      max_tokens=2000,
      top_p=1.0,
      frequency_penalty=0.0,
      presence_penalty=1
      )
    print(json.dumps(response, indent=4)) 
    return response



# Function to write to the database
def write_to_db(posttype, url, test2summarizedb, openAIsummarydb):
  entry = Entry_Post(posttype = posttype, url = url, test2summarize = test2summarizedb, openAIsummary = openAIsummarydb)       
  db.session.add(entry)
  db.session.commit()
  db.session.close()
