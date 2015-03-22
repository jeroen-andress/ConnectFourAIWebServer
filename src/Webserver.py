#!/usr/bin/env python

import tornado.ioloop, tornado.web, tornado.httpserver, tornado.template
import os, sys, json, uuid, signal, pickle
import ConnectFourAI


class ConnectFourWebServer(tornado.web.Application):
     def __init__(self):
          self._session = {}
          
          handlers = [    (r"/", ConnectFourMainHandler),
          (r"/ChooseColumn/([0-6])", ConnectFourChooseColumnHandler),
          (r"/GetPlayboard", ConnectFourPlayboardHandler),
          (r"/GetWinner", ConnectFourWinnerHandler),
          (r"/IsTied", ConnectFourTiedHandler),
          (r"/Reset", ConnectFourResetHandler),
          (r"/GetStatistics", ConnectFourStatisticsHandler)]

          settings = {"static_path": os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Static'), "template_path": os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Templates')}

          tornado.web.Application.__init__(self, handlers, **settings)

     def addSession(self, id):
          self._session[id] = {}
          self.reset(id)

     def makeAIMove(self, id):
          result = int(self._session[id]["AIPlayer"].MakeMove())

          self._updateStatistics(id)

          return result

     def move(self, id, column):
          self._session[id]["Playboard"].MoveWhite(column)

          self._updateStatistics(id)

     def getColumns(self, id):
          return int(self._session[id]["Playboard"].GetColumns())

     def getRows(self, id):
          return int(self._session[id]["Playboard"].GetRows())

     def getField(self, id, row, column):
          return int(self._session[id]["Playboard"].GetField(row, column))

     def getWinner(self, id):
          return self._session[id]["Playboard"].GetWinner()

     def isFull(self, id):
          return self._session[id]["Playboard"].IsFull()

     def hasSession(self, id):
          return id in self._session

     def reset(self, id):
          Playboard =  ConnectFourAI.ConnectFourPlayboard()
          AIPlayer = ConnectFourAI.ConnectFourPlayerMinimaxAlphaBeta(Playboard, ConnectFourAI.ConnectFourPlayboard.RED, 8)

          self._session[id]["Playboard"] = Playboard
          self._session[id]["AIPlayer"] = AIPlayer

          if not "Statistics" in self._session[id]:
               self._session[id]["Statistics"] = {"RedWins": 0, "WhiteWins": 0, "Tied": 0}

     def getStatistics(self, id):
          return self._session[id]["Statistics"]

     def _updateStatistics(self, id):
          statistics = self.getStatistics(id)
          winner = self.getWinner(id)
          tied = winner == ConnectFourAI.ConnectFourPlayboard.NONE and self.isFull(id)

          if (winner ==  ConnectFourAI.ConnectFourPlayboard.RED):
              statistics["RedWins"] += 1
          elif (winner ==  ConnectFourAI.ConnectFourPlayboard.WHITE):
              statistics["WhiteWins"] += 1
          elif (tied):
              statistics["Tied"] += 1

     def getPlayboard(self, id):
          rows = self.getRows(id)
          columns = self.getColumns(id)

          Result = []
          for i in range(0, rows):
               Column = []
               for j in range(0, columns):
                    Column.append(self.getField(id, i, j))

               Result.append(Column)

          return Result


     def saveLastState(self, filename=".laststate"):
          file = open(filename, "wb")

          dump = {}
          for id in self._session:
               dump[id] = {}
               dump[id]["Playboard"] = self.getPlayboard(id)
               dump[id]["Statistics"] = self.getStatistics(id)

          pickle.dump(dump, file)
          file.close()

     def restoreLastState(self, filename=".laststate"):
          if os.path.isfile(filename):
               file = open(filename, "rb")

               dump = pickle.load(file)

               for id in dump:
                    self.addSession(id)
                    self._session[id]["Statistics"] = dump[id]["Statistics"]

               file.close()
               

class ConnectFourMainHandler(tornado.web.RequestHandler):
     def get(self):
          sessionID = self.get_cookie("session");

          if not sessionID:
               sessionID = str(uuid.uuid4())
               self.set_cookie("session", sessionID)
               print "Create new session with sessionID: '%s'" % sessionID
          else:
               sessionID = self.get_cookie("session")
               print "continue session: '%s'" % str(sessionID)

          if not self.application.hasSession(sessionID):
               self.application.addSession(sessionID)

          self.render("MainTemplate.html", sessionID=sessionID)

class ConnectFourPlayboardHandler(tornado.web.RequestHandler):
     def post(self):
          try:
               sessionID = self.get_argument('session')
               rows = self.application.getRows(sessionID)
               columns = self.application.getColumns(sessionID)

               Result = self.application.getPlayboard(sessionID)

               self.write(json.dumps(Result))
          except Exception as e:
               sys.stderr.write("%s\n" % e)
               self.set_status(400)
               self.write_error(400)
               return

class ConnectFourChooseColumnHandler(tornado.web.RequestHandler):
     def post(self, Column):
          try:
               sessionID = self.get_argument('session')
               self.application.move(sessionID, int(Column))

               winner = self.application.getWinner(sessionID)
               tied = winner == ConnectFourAI.ConnectFourPlayboard.NONE and self.application.isFull(sessionID)

               if (winner == ConnectFourAI.ConnectFourPlayboard.NONE and not tied):
                   self.write(str(self.application.makeAIMove(sessionID)))
               else:
                   self.write("-1")
                   
          except Exception as e:
               sys.stderr.write("%s\n" % e)
               self.set_status(400)
               self.write_error(400)
               return

class ConnectFourWinnerHandler(tornado.web.RequestHandler):
    def post(self):
          try:
               self.write(str(self.application.getWinner(self.get_argument('session'))))
          except:
               self.set_status(400)
               self.write_error(400)
               return

class ConnectFourTiedHandler(tornado.web.RequestHandler):
    def post(self):
         try:
               sessionID = self.get_argument('session')
               return self.write(str(self.application.getWinner(sessionID) == ConnectFourAI.ConnectFourPlayboard.NONE and self.application.isFull(sessionID)))
         except:
               self.set_status(400)
               self.write_error(400)
               return

class ConnectFourResetHandler(tornado.web.RequestHandler):
     def post(self):
         try:
               sessionID = self.get_argument('session')
               self.application.reset(sessionID)
         except:
               self.set_status(400)
               self.write_error(400)
               return

class ConnectFourStatisticsHandler(tornado.web.RequestHandler):
     def post(self):
          try:
               sessionID = self.get_argument("session")

               statistics = self.application.getStatistics(sessionID)
               self.write(json.dumps(statistics))
          except:
               self.set_status(400)
               self.write_error(400)
               return

if __name__ == "__main__":
     webserver = ConnectFourWebServer()
     server = tornado.httpserver.HTTPServer(webserver)
     server.listen(8080)
     instance = tornado.ioloop.IOLoop.instance()

     webserver.restoreLastState()

     try:
          instance.start()
     except:
          webserver.saveLastState()
          instance.stop()
