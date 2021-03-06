"""
Simple Flask web site 
"""

import flask
# from flask import render_template
from flask import request  # Data from a submitted form
from flask import url_for
from flask import jsonify # For AJAX transactions

import json
import logging
import argparse  # For the vocabulary list
import sys

# Our own modules
from letterbag import LetterBag
from vocab import Vocab
from jumble import jumbled

###
# Globals
###
app = flask.Flask(__name__)
import CONFIG
app.secret_key = CONFIG.COOKIE_KEY  # Should allow using session variables

#
# One shared 'Vocab' object, read-only after initialization,
# shared by all threads and instances.  Otherwise we would have to
# store it in the browser and transmit it on each request/response cycle, 
# or else read it from the file on each request/responce cycle,
# neither of which would be suitable for responding keystroke by keystroke.
#

def get_command_line():
  """
  Returns a namespace of command-line argument values
  """
  parser = argparse.ArgumentParser(
    description="Vocabulary anagram through a web server")
  parser.add_argument("vocab", type=argparse.FileType('r'),
                      default="data/vocab.txt",
                      help="A file containing vocabulary words, one per line")
  args = parser.parse_args()
  return args

CMDLN = get_command_line()
WORDS = Vocab( CMDLN.vocab )

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  flask.g.vocab = WORDS.as_list();
  flask.session["target_count"] = min( len(flask.g.vocab), CONFIG.SUCCESS_COUNT )
  flask.session["jumble"] = jumbled(flask.g.vocab, flask.session["target_count"])
  flask.session["matches"] = [ ]
  app.logger.debug("Session variables have been set")
  assert flask.session["matches"] == [ ]
  assert flask.session["target_count"] > 0
  app.logger.debug("At least one seems to be set correctly")
  return flask.render_template('vocab.html')

@app.route("/keep_going")
def keep_going():
  """
  After initial use of index, we keep the same scrambled
  word and try to get more matches
  """
  flask.g.vocab = WORDS.as_list();
  return flask.render_template('vocab.html')
  

@app.route("/success")
def success():
  return flask.render_template('success.html')

#######################


@app.route("/_check")
def check():
  """
 FIXED: 
 to check if letter is in the jumble 
  """
  text = request.args.get("text", type=str)
  jumble = request.args.get("jumble",type=str)
  ## Is it good? 
  
  #jumble contains letter(s)
  in_jumble = LetterBag(jumble).contains(text)
  
  #jumble contains entire word
  matched = WORDS.has(text)
  
  rslt = {"contains_text": in_jumble, "contains_word": matched}
  return jsonify(result=rslt)
 

@app.route("/_example")
def example():
  """
  Example ajax request handler
  """
  app.logger.debug("Got a JSON request");
  rslt = { "key": "value" }
  return jsonify(result=rslt)


#################
# Functions used within the templates
#################

@app.template_filter( 'filt' )
def format_filt( something ):
    """
    Example of a filter that can be used within
    the Jinja2 code
    """
    return "Not what you asked for"
  
###################
#   Error handlers
###################
@app.errorhandler(404)
def error_404(e):
  app.logger.warning("++ 404 error: {}".format(e))
  return flask.render_template('404.html'), 404

@app.errorhandler(500)
def error_500(e):
   app.logger.warning("++ 500 error: {}".format(e))
   assert app.debug == False #  I want to invoke the debugger
   return flask.render_template('500.html'), 500

@app.errorhandler(403)
def error_403(e):
  app.logger.warning("++ 403 error: {}".format(e))
  return flask.render_template('403.html'), 403



#############

# Set up to run from cgi-bin script, from
# gunicorn, or stand-alone.
#

if __name__ == "__main__":
    # Standalone. 
    app.debug = True
    app.logger.setLevel(logging.DEBUG)
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
else:
    # Running from cgi-bin or from gunicorn WSGI server, 
    # which makes the call to app.run.  Gunicorn may invoke more than
    # one instance for concurrent service.
    #FIXME:  Debug cgi interface 
    app.debug=False

