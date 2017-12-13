#!/usr/bin/env python
import os
import jinja2
import webapp2
from google.appengine.ext import ndb
from google.appengine.api import users


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        user = users.get_current_user()
        params["user"] = user

        if user:
            logged_in = True
            logout_url = users.create_logout_url('/')
            params["logout_url"] = logout_url
        else:
            logged_in = False
            login_url = users.create_login_url('/guestbook')
            params["login_url"] = login_url

        params["logged_in"] = logged_in

        template = jinja_env.get_template(view_filename)

        return self.response.out.write(template.render(params))

class Message(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    message = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    deleted = ndb.BooleanProperty(default=False)



class AdminSite(BaseHandler):
    def get(self):
        if not users.is_current_user_admin():  # check if current user is admin
            return self.write("You are not admin!")
        messages = Message.query(Message.deleted == False).fetch()
        params = {"messages": messages}
        return self.render_template("admin-site.html", params=params)


class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("main.html")


class Guestbook(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == False).fetch()

        params = {"messages": messages}

        return self.render_template("guestbook.html", params=params)

    def post(self):
        user = users.get_current_user()

        if not user:

            return self.write("You are not logged in!")

        name = self.request.get("name")
        email = self.request.get("email")
        message = self.request.get("message")

        if not name:
            name = "Anonymous"

        if "<script>" in message:
            return self.write("Can't hack me!")


        msg_object = Message(name = name, email = email, message=message.replace("<script>", ""))
        msg_object.put()
        messages = Message.query(Message.deleted == False).fetch()
        params = {"messages": messages}


        return self.redirect_to("guestbook-site", params=params)


class MessageEdit(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_edit.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        text = self.request.get("message")
        message.message = text
        message.put()

        return self.redirect_to("guestbook-site" and "admin-site")

class MessageDelete(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_delete.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        message.deleted = True
        message.put()

        return self.redirect_to("guestbook-site" and "admin-site")


class MessagesDeleted(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == True).fetch()

        params = {"messages": messages}

        return self.render_template("deleted_messages.html", params=params)


class MessageRestore(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_restore.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        message.deleted = False
        message.put()

        return self.redirect_to("guestbook-site" and "admin-site")


class MessageCompleteDeleted(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))

        params = {"message": message}

        return self.render_template("message_delete_complete.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))

        message.key.delete()

        return self.redirect_to("deleted-messages")


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/guestbook', Guestbook, name="guestbook-site"),
    webapp2.Route('/message/<message_id:\d+>/edit', MessageEdit, name="message-edit"),
    webapp2.Route('/message/<message_id:\d+>/delete', MessageDelete, name="message-delete"),
    webapp2.Route('/message/<message_id:\d+>/restore', MessageRestore, name="message-restore"),
    webapp2.Route('/message/<message_id:\d+>/complete-delete', MessageCompleteDeleted, name="message-delete-complete"),
    webapp2.Route('/deleted', MessagesDeleted, name="deleted-messages"),
    webapp2.Route('/admin-site', AdminSite, name="admin-site"),
], debug=True)