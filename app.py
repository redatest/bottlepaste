#!/usr/bin/env  python2
import os.path
import datetime
import tempfile
import os, tempfile
from os.path import dirname,basename
from bottle import redirect, route,error, run,request,HTTPResponse, debug, static_file,jinja2_view as view, jinja2_template as template
from wtforms import Form ,validators,TextField,PasswordField,TextAreaField,SelectField
from pygments import highlight
from pygments.lexers import get_all_lexers, guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter

from sqlalchemy import create_engine,desc
from sqlalchemy import Column , DateTime , Integer , String
from sqlalchemy.ext.declarative  import  declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib

import settings


engine = create_engine('sqlite:///bottlepaste.db',echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Paste(Base): 
	__tablename__ = 'pastes'
	
	id = Column(Integer,primary_key=True)
	title = Column(String)
	author = Column(String)
	language = Column(String)
	code = Column(String)
	publishdate=Column(DateTime)
	
	def __str__(self):
		return "(%d, %s, %s, %s, %s)"%(self.id, self.title, self.author, self.language, self.code)
		
	def gravatar_url(self):
		return  "http://www.gravatar.com/avatar/%s?s=50&d=retro" % hashlib.md5(self.author).hexdigest()


#fits here
if not os.path.isfile('bottlepaste.db'):
        Base.metadata.create_all(engine)

def highlighted_code(acode,alang):
	lexer=None
	if alang:
		try:
			lexer=get_lexer_by_name(alang)
		except:
			lexer=None
	if lexer is None:
		lexer=guess_lexer(acode)
	formatter=HtmlFormatter(linenos=True)
	return highlight(acode, lexer, formatter)


def last_n(n):
	s1=Session()
	q = s1.query(Paste).order_by((Paste.publishdate.desc())).limit(n)
	return q
        
    
last_five= lambda : last_n(5)

settings.init()


#DON'T TOUCH
#pygments
languages_list=[(l[1][0], l[0]) for l in get_all_lexers()] #tuples of long/short names
languages_list.sort(key = lambda el: el[0])
languages_list.insert(0,('YOU GUESS', ''))

@route('/public/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=settings.staticdir)


class PasteForm(Form):
	author = TextField('author',[validators.Length(max=10)])
	title  = TextField('title',[validators.Length(max=10)])
	language   = SelectField('language', choices=languages_list)
	code   = TextAreaField('code',validators=[validators.required()])



	
@route("/About")
def about():
    return template('templates/about.html',last5=last_five())

@route("/Contact")
def contact():
    return template('templates/contact.html',last5=last_five())
 
@error(404)
def error404(error):
    return template('templates/404.html')
    
    
@route("/")
def home():
	frm = PasteForm()
	return template('templates/home.html',form=frm,last5=last_five())




@route('/new', method="POST")

def new():
	frm = PasteForm(request.POST)
	
	if frm.validate():
		#errors = ["Form is valid"]
		
		newPaste = Paste(title=frm.title.data,author=frm.author.data,\
				language=frm.language.data,code=frm.code.data,publishdate=datetime.datetime.now())
		s=Session()
		s.add(newPaste)
		s.commit()
		
		redirect('view/%d'%newPaste.id)	
	else:

		return template('templates/home.html',errors=frm.errors,form=frm,code=frm.code)

@route('/view/<n:int>')
def view(n):
	s=Session()
	paste = s.query(Paste).filter_by(id=n).first()
	
	code = highlighted_code(paste.code,paste.language)
        last5=last_five()
        
	return template('templates/result.html',locals())


@route('/raw/<n:int>')
def raw(n):
    s = Session()
    paste=s.query(Paste).filter(Paste.id==n).first()
    #if not paste 404
    h={}
    h['Content-Type'] = 'text/plain'
    return HTTPResponse(paste.code, **h)

@route('/download/<n:int>')
def download(n):

    f=tempfile.NamedTemporaryFile(delete=False)
    fname=f.name
    #print "F: ", f
    #print "fname: ", fname
    #print "fdir: ", dirname(fname)
    s=Session()
    paste=s.query(Paste).filter(Paste.id==n).first()
    f.write(paste.code)
    f.close()
    ret=static_file(basename(fname), root=dirname(fname), download=fname, mimetype="text")
    os.unlink(fname)
    return ret
    
if __name__=="__main__":
    run(reloader=True,debug=True, port=9000)
