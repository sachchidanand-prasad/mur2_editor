"""
The RestAPI addresses
"""
from datetime import datetime,timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required, logout_user
from flask import render_template, current_app
# errors
from flask import abort
from flask_babel import lazy_gettext as _l

# the part of the applications
from app.auth import bp
# the databse types
from app.models import User, Article, WriterRelationship, Images
# the db
from app import db
# forms
from app.main.forms import SearchForm, UploadForm, photos, EditProfileForm, DeleteProfileForm
from app.auth.email import send_password_reset_email
# blueprint
from app.main import bp
# delete directory
import shutil

mobils = ["Android", "webOS", "iPhone", "iPad", "iPod", "BlackBerry", "IEMobile", "Opera Mini", "Mobile", "mobile", "CriOS"]

# recordin last user logging
from flask import g
from flask_babel import get_locale
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm() # for search
    g.locale = str(get_locale()) # for international languages
    
    
# logo page
@bp.route('/' )
def root():
    return render_template("root.html", title='Home Page')

@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.user', username=current_user.username))
    else:
        return redirect( url_for('main.root') )


# user home page
from flask_login import login_required
@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    deleteform = DeleteProfileForm()
    page = request.args.get('page', 1, type=int)
    # we need to set up in the add_columns the data in the templates
    articles =   Article.query.order_by(Article.timestamp.desc()).join( WriterRelationship ).join(User).filter(User.id == current_user.id ).add_columns(  Article.id, Article.title,  Article.abstract, Article.status )
    return render_template('user.html', user=user, articles=articles, deleteform=deleteform )

# markdown editor
from flask import Markup
@bp.route('/edit/<articleid>')
@login_required
def editor(articleid):
    # this is a hack as Javascript can access this 
    mur2language = str(request.accept_languages).split(",")[0]
    # the article
    article = Article(title="", abstract='', markdown='', html="")
    # if it is not a new article
    if int(articleid) != -1:
        # articleRelation = writerrelationship.query.filter_by(article_id=articleid).all()
        articleRelation =   Article.query.filter_by(id=articleid).join( WriterRelationship ).join(User).add_columns( User.id ).all()
        # check writer have got right to edit 
        canEdit = False
        for ar in articleRelation:
            if ar.id == current_user.id:
                canEdit = True
                break
        if not canEdit:
            abort(401)
        article = Article.query.filter_by(id=articleid).first()
    
        # Article not in editing status we redirect to reading
        if article.status != 'editing':
            flash(_l('You can not edit this article'))
            return redirect(url_for('main.reader', article_id=article.id) )
    
    wordpresslogin = False
    if 'mur2_wpc_accesstoken' in request.cookies:
        wordpresslogin = True
    
    # distinct between desktop and mobil users
    desktop = True
    useragent = request.headers.get('User-Agent')    
    if any(phone  in useragent.lower() for phone in mobils):
        desktop = False
        
    timestamp = 0
    if article.timestamp is not None:
        article.timestamp.replace(tzinfo=timezone.utc).timestamp()
        
    return render_template('editor.html', 
                           article_markdown=Markup(article.markdown
                                                   .encode('unicode_escape').decode('utf-8')
                                                   .replace("'", "\\\'")
                                                   .replace('<', '&lt;')  ),
                           article_title = Markup(article.title
                                                  .encode('unicode_escape').decode('utf-8')
                                                  .replace("'", "\\\'")
                                                  .replace('<', '&lt;')),
                           article_abstract=Markup(article.abstract
                                                   .encode('unicode_escape').decode('utf-8')
                                                   .replace("'", "\\\'")
                                                   .replace('<', '&lt;')), 
                           article_id = str(articleid), 
                           language=mur2language,
                           wordpresslogin = wordpresslogin,
                           desktop=desktop,
                           articleTimestamp = timestamp
                          )

# markdown editor without login
@bp.route('/editor', methods=['GET', 'POST'])
def free_editor():
    # this is a hack as Javascript can access this 
    mur2language = str(request.accept_languages).split(",")[0]
    # the article
    article = Article(title="", abstract='', markdown='', html="")
    # fix the article content to a demo text 
    with current_app.open_resource("static/demo.md", 'r') as file:  
        demo = file.read() 
    
    wordpresslogin = False
    if 'mur2_wpc_accesstoken' in request.cookies:
        wordpresslogin = True
    mediumlogin = False
    if 'mur2_medium_accesstoken' in request.cookies:
        mediumlogin = True
        
    # distinct between desktop and mobil users
    desktop = True
    useragent = request.headers.get('User-Agent')   
    print(useragent);
    if any(phone  in useragent.lower() for phone in mobils):
        desktop = False
    
    return render_template('editor.html', 
                           article_markdown=Markup(demo.encode('unicode_escape').decode('utf-8')
                                                   .replace("'", "\\\'")
                                                  .replace('<', '&lt;')),
                           article_title = Markup(article.title.encode('unicode_escape').decode('utf-8')
                                                  .replace("'", "\\\'")
                                                 .replace('<', '&lt;')),
                           article_abstract=Markup(article.abstract.encode('unicode_escape').decode('utf-8')
                                                   .replace("'", "\\\'")
                                                  .replace('<', '&lt;')), 
                           article_id = str(-2), 
                           language=mur2language,
                           wordpresslogin = wordpresslogin,
                           mediumlogin = mediumlogin,
                           desktop=desktop,
                           articleTimestamp = 0
                          )

# test for different tmp solutions
@bp.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html');

# save markdown for article
from flask import Flask, jsonify

# to make the html code from the markdown
import markdown
import markdown.extensions.fenced_code
@bp.route('/markdownsave', methods=['POST'])
@login_required
def markdownsave():
    # read the data which was sent from the editor.js
    markdowntxt = request.files['file'].read()
    htmltxt = request.files['htmlfile'].read()

    # some encoding 
    markdowntxt = markdowntxt.decode('utf-8')
    htmltxt = htmltxt.decode('utf-8')


    article_id = int((request.form['article_id']))        
    article_title = (request.form['article_title'])
    article_abstract = (request.form['article_abstract'])  
    
    
    # save the data 
    #   new Article
    if article_id <= -1:
        # check the Article do not exist
        a = Article.query.filter_by(title=article_title).filter_by(abstract=article_abstract).join(WriterRelationship).filter(WriterRelationship.writer_id == current_user.id).first()
        if a is not None:
            # we should return something more meaningfull ???
            abort(401)
           
        # create new Artilce
        a = Article(title=article_title, abstract=article_abstract, markdown=markdowntxt, html=htmltxt, status="editing")        
        db.session.add(a)
        # get the new object id
        db.session.flush()         
        # save in DB
        db.session.commit()                
        
        # get the user also
        user = User.query.filter_by(id=current_user.id).first_or_404()
        
        # add Writerrelationship
        w = WriterRelationship(article_id=a.id, 
                               writer_id= current_user.id)
        db.session.add(w)
        db.session.commit()    
        
        return jsonify({'result': "OK", 'id': a.id})
    else:
        a = Article.query.filter_by(id=article_id).first_or_404()
        
        if a.status is not None and a.status != 'editing':
            raise RuntimeError("The  Article status is not 'edited'! ")
        elif a.status is None:
            a.status = 'editing'
        
        # update if somethings changed
        change = False
        if a.title != article_title:
            change = True
            a.title = article_title
        if a.html != htmltxt:
            change = True
            a.html = htmltxt
        if a.abstract != article_abstract:
            change = True
            a.abstract = article_abstract
        if a.markdown != markdowntxt:
            change = True
            a.markdown = markdowntxt

        # if anything changed
        if change:
            db.session.commit()
    
    # return a OK json 
    flash(_l("Your changes have been saved."))
    return jsonify(result="OK")
    

@bp.route('/delete', methods=["POST"])
@login_required
def delete_object():
        # which kind of object we delete 'article' etc...
        object_type = request.form['object_type']
        object_id = int(request.form['object_id']) 
    
        # check object type
        if object_type != 'article' and object_type != 'user' and object_type != 'file' :
            abort(make_response(_l("Object type should be 'article', 'file' or 'user'!"), 400))
        
        if object_type == 'article' :
            articleRelation =   Article.query.filter_by(id=object_id).join( WriterRelationship ).join(User).add_columns( User.id ).all()
            # check user have right to delete the Article
            canEdit = False
            for ar in articleRelation:
                if ar.id == current_user.id:
                    canEdit = True
                    break
            if not canEdit:
                abort(make_response(_l("User no right to delete this") + _l("Article"), 401))        
            else:
                # delete
                Article.query.filter_by(id=object_id).delete()
                db.session.commit()
            return redirect(url_for('main.user', username=current_user.username ))
        elif object_type == 'user' :

            # delete just the own user is possible
            # delete Articles
            articles = Article.query.order_by(Article.timestamp.desc()).join( WriterRelationship ).join(User).filter(User.id == current_user.id ).add_columns(  Article.id )
            for a in articles:
                print(a.id)
                Article.query.filter_by(id=a.id).delete()
            # delete users
            User.query.filter_by(id=current_user.id ).delete()
            db.session.commit()
            # logout
            logout_user()
            return redirect(url_for('main.index'))
        elif object_type == 'file' :
            # what is the DB id of the object
            object_id = request.form['object_id']
            # check user is the owner of the file
            i = Images.query.filter_by(id=object_id).first_or_404()
            if i.user_id != current_user.id:
                abort(make_response(_l("User no right to delete this") + _l("File"), 401)) 
            else:
                # delete the file
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username, i.addresss.split("/")[-1]))
                # delete from db
                Images.query.filter_by(id=object_id).delete()
                db.session.commit()
                return redirect(url_for('main.media'))
   
    
# reading an article
# there the Author of the ARticle can set publishing relationship
# the journal editor can confirm this on the Journal page
from flask import Markup
@bp.route('/reader/<article_id>')
def reader(article_id):
    a = Article.query.filter_by(id=article_id).join( WriterRelationship ).join(User).add_columns(  Article.html, Article.title,  Article.abstract, Article.status, Article.id, (User.id).label("uid"), User.username, WriterRelationship.confirmed ).first_or_404()
    return render_template('read.html', article_content=Markup(a.html), 
                           title=a.title, author=a.username, article=a )


# editing the profile
@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    deleteform = DeleteProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_l('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form, deleteform=deleteform, userid=current_user.id)




@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    deleteform = DeleteProfileForm()
    articles, total = Article.search(g.search_form.q.data, page,
                               current_app.config['ARTICLE_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['ARTICLE_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', articles=articles,
                           next_url=next_url, deleteform=deleteform, prev_url=prev_url)


# export the data to other formats
import requests
import datetime
import json
import re
import string
import random
import os
from flask import make_response, send_file
# for pandoc
import subprocess
from subprocess import Popen, PIPE
from subprocess import check_output
def run_os_command(command):
    stdout = check_output(command).decode('utf-8')
    return stdout
def  make_pandoc_md(mdtxt):
            # make some change on the markdown to work with pandoc
            # change $$ if it is in line
            points = []
            for m in re.finditer(r'(?:(?<=(?: |\w))\$\$([^\n\$]+?)\$\$)|(?:\$\$([^\n\$]+?)\$\$(?=(?: |\w)))',  mdtxt):
                points.append( (m.start(), m.end()) )
            for m in reversed(points):
                mdtxt = mdtxt[:m[0]] + ' $' + mdtxt[m[0]:m[1]+1].replace('$$', '').strip() + '$ '+  mdtxt[m[1]+1:]
            
            
            return mdtxt
def make_latex(mdtxt, title, abstract, language):
            mdtxt = make_pandoc_md(mdtxt)
            title = title
            abstract = abstract
    
            # save to file
            #  # generate random string for dir
            letters = string.ascii_letters
            dirname = '/tmp/mur2_export_'+''.join(random.choice(letters) for i in range(16))+'/'
            os.mkdir(dirname)
            mdname = dirname+'pdf.md'
            file = open(mdname, 'w')
            file.write(mdtxt)
            file.close()
            
            print(title)

            # make latex
            # '--filter',  'pandoc-xnos', # https://github.com/tomduck/pandoc-eqnos 
            result = run_os_command(['/usr/bin/pandoc', 
                                     mdname, 
                                     '-M', 'title='+title.replace("$$", "$")+'',
                                     '-M', 'abstract='+abstract+"",
                                     '-f', 'markdown', 
                                     '-t',  'latex', 
                                     '-V', 'lang='+language,
                                     '-V',  'CJKmainfont=Noto Serif CJK SC',
                                     '-s',                                      
                                     '-o', dirname+'mur2.tex'])
            return dirname
    
@bp.route('/export_data', methods=['POST'])
@login_required
def exportdata():
    if request.method == 'POST':
        destination = request.form['destination']
        # save to Wordpress.com
        if destination == 'wp':  
            article_id = (request.form['article_id'])
            wpcom_id = (request.form['wpcom_id'])
            wpcom_address = (request.form['wpcom_address'])

            if int(article_id) > 0 :
                a =  Article.query.filter_by(id=article_id).first_or_404()
                # new article
                if a.wpcom_id is None:           
                    a.wpcom_address = wpcom_address
                    a.wpcom_id = wpcom_id
                    db.session.commit()
        elif destination == 'medium': 
            article_id = (request.form['article_id'])
            # publish on Medium
            acceskey = (request.form['acceskey'])
            # get the user id
            headers = {"Authorization": "Bearer "+acceskey, 
                       "Content-Type": "application/json", 
                       "Accept": "application/json",
                       "Accept-Charset": "utf-8"}
                
            x = requests.get('https://api.medium.com/v1/me', headers=headers).json()
            
            
            
            # post
            content = (request.form['article_content']).replace("https://tex.s2cms.ru/svg", "https://tex.s2cms.ru/png")
            postdata = { "title": (request.form['article_title']),
                        "contentFormat": "html",
                        "content": content,
                        "publishStatus": "draft"}
            post = requests.post('https://api.medium.com/v1/users/'+x['data']['id']+'/posts', json=postdata, headers=headers )
            
            if post.status_code == 201 :
                post = post.json()
                # save on Mur2 system
                if int(article_id) > 0 :
                    a =  Article.query.filter_by(id=article_id).first_or_404()
                    # new article
                    if a.medium_id is None:           
                        a.medium_address = post['data']['url']
                        a.medium_id = post['data']['id']
                        db.session.commit()
                
               
                return jsonify({"result":"OK", "link": post['data']['url']})  
            else:
                return post.text, post.status_code
            
                        
        elif destination == 'pdf': 
            # read the data which was sent from the editor.js
            mdtxt = request.files['mdfile'].read()
            # some encoding 
            mdtxt = mdtxt.decode('utf-8')
            article_title = (request.form['article_title'])
            article_abstract = (request.form['article_abstract']) 
            endnotetext = (request.form['endnotetext']) 
            language = (request.form['language']) 

            # dirname = make_latex(mdtxt, article_title, article_abstract)
            mdtxt = make_pandoc_md(mdtxt)
            article_title = make_pandoc_md(article_title)
            article_abstract = make_pandoc_md(article_abstract)
            
            dirname = make_latex(mdtxt, article_title, article_abstract, language)
            
            # make pdf
            result = run_os_command(['/usr/bin/pandoc', 
                                     dirname + 'mur2.tex', 
                                     '-M', 'title='+article_title+'',
                                     '-M', 'abstract='+article_abstract+'',
                                     '-f', 'latex', 
                                     '-V',  'CJKmainfont=Noto Serif CJK SC', 
                                     '-V', 'lang='+language,
                                     '--pdf-engine=xelatex',
                                     '-s', 
                                     '-o', dirname + 'mur2.pdf'])
            return send_file(os.path.join(dirname, 'mur2.pdf'))

            
        elif destination == 'latex': 
            # read the data which was sent from the editor.js
            mdtxt = request.files['mdfile'].read()
            # some encoding 
            mdtxt = mdtxt.decode('utf-8')
            article_title = (request.form['article_title'])
            article_abstract = (request.form['article_abstract']) 
            language = (request.form['language']) 
            
            dirname = make_latex(mdtxt, article_title, article_abstract, language)

            # clear up tmp files
            #   do in cron ass it is troublesome to be sure it was transfared before deleteing
            
            return send_file(os.path.join(dirname, 'mur2.tex'))
        elif destination == "epub":
            # read the data which was sent from the editor.js
            mdtxt = request.files['mdfile'].read()
            # some encoding 
            mdtxt = mdtxt.decode('utf-8')
            article_title = (request.form['article_title'])
            article_abstract = (request.form['article_abstract']) 
            endnotetext = (request.form['endnotetext']) 
            language = (request.form['language']) 

            # dirname = make_latex(mdtxt, article_title, article_abstract)
            mdtxt = make_pandoc_md(mdtxt)
            article_title = make_pandoc_md(article_title)
            article_abstract = make_pandoc_md(article_abstract)
            
            dirname = make_latex(mdtxt, article_title, article_abstract, language)
            # make pdf
            result = run_os_command(['/usr/bin/pandoc', 
                                     dirname + 'mur2.tex', 
                                     '-M', 'title='+article_title+'',
                                     '-M', 'abstract='+article_abstract+'',
                                     '-f', 'latex', 
                                     '-V',  'CJKmainfont=Noto Serif CJK SC', 
                                     '-V', 'lang='+language,
                                     '-s', 
                                     '-o', dirname + 'mur2.epub'])
            return send_file(os.path.join(dirname, 'mur2.epub'))
            
            
    # return a OK json 
    return jsonify(result="OK")            
            
# Upload files
from flask_uploads import configure_uploads, patch_request_class
# DB local DB to know what file for which user
import os
@bp.route('/media', methods=['GET', 'POST'])
@login_required
def media():
    form = UploadForm()
    deleteform = DeleteProfileForm()
    if request.method == 'POST':
        # check how many files the user have
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
        userfilesize = sum(os.path.getsize(os.path.join(path, f)) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        if userfilesize > current_app.config['MAX_USER_FILES_SIZE']:
            flash(_l("No more disk space quota for ")+current_user.username)
        
        filename = photos.save(form.photo.data, folder=current_user.username )
        file_url = photos.url(filename)
        
        # save in DB
        image = Images(user_id=current_user.id, addresss=file_url)
        db.session.add(image)
        db.session.commit()
        
        return redirect(url_for('main.media'))
    user_files = Images.query.filter_by(user_id=current_user.id).all()
    return render_template('media.html', form=form, files=user_files, deleteform=deleteform)