import os
import bottle

templatesdir=os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/')
staticdir=os.path.join(os.path.dirname(__file__), 'public').replace('\\','/')


def init():
    bottle.TEMPLATE_PATH.insert(0, templatesdir)

