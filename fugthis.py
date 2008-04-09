import logging
import cgi
import wsgiref.handlers
import os
import string

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import urlfetch


class Photo(db.Model):
  url = db.StringProperty(multiline=False)
  mime = db.StringProperty(multiline=False)
  image = db.BlobProperty() 

class Fugging(db.Model):
  author = db.UserProperty()
  link = db.StringProperty(multiline=False)
  title = db.StringProperty(multiline=False)
  message = db.StringProperty(multiline=True)
  photo = db.ReferenceProperty(Photo)
  date = db.DateTimeProperty(auto_now_add=True)
  
class Fugs(webapp.RequestHandler):
  def post(self):
    if users.get_current_user():
      fugging = Fugging()
      fugging.author = users.get_current_user()
      fugging.link = self.request.get('link')
      fugging.title = self.request.get('title')
      fugging.message = self.request.get('message')
      photourl = self.request.get('photo')
      result = urlfetch.fetch(photourl);
      if (result.status_code == 200):
        photo = Photo()
        photo.image = result.content
        photo.url = photourl
        # logging.debug(string.join(result.headers.keys(),''))
        h = result.headers
        if 'Content-Type' in h:
          photo.mime = h['Content-Type']
        elif 'content-type' in h:
          photo.mime = h['content-type']
        photo.put()
        fugging.photo = photo
        fugging.put()   
      self.redirect('/')
    else:
      url = users.create_login_url(self.request.uri)
      self.redirect(url)
    
  def get(self):
    fuggings = Fugging.all().order('-date')
    if users.get_current_user():
      logged_in = True
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      logged_in = False
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    who = 'everyone'
    template_values = {
      'fuggings': fuggings,
      'logged_in': logged_in,
      'who' : who,
      'url': url,
      'url_linktext': url_linktext,
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
      

class Images(webapp.RequestHandler):
  def get(self, key):
    photo = db.get(key)
    # logging.info(photo.mime)
    
    self.response.headers['Content-Type'] = photo.mime.encode('ascii', 'ignore')
    self.response.out.write(photo.image)
    
    
def main():
  application = webapp.WSGIApplication([('/', Fugs),
                                        (r'/images/(.*)', Images)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()