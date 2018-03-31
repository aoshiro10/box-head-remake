import socket
from _thread import *
from queue import Queue
import pygame

#Connects to server
#Code from 112 Sockets Demo
HOST = '128.237.131.95'
PORT = 50114
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server.connect((HOST,PORT))
print("connected to server")

#Controls the received messages
#Code from 112 Sockets Demo
def handleServerMsg(server, serverMsg):
  server.setblocking(1)
  msg = ""
  command = ""
  while True:
    msg += server.recv(10).decode("UTF-8")
    command = msg.split("\n")
    while (len(command) > 1):
      readyMsg = command[0]
      msg = "\n".join(command[1:])
      serverMsg.put(readyMsg)
      command = msg.split("\n")

#Code from 112 Sockets Demo
def checkReceivedMessages(serverMsg, player2):
  #Checks if there is a message in the queue
  containsMessage = 0
  if (serverMsg.qsize() > containsMessage):
    msg = serverMsg.get(False)
    
    if msg.startswith("newPlayer"):
      #Player connected
      print("Second Player Connected")
      player2.connected = True
      player2.health = 35
    elif msg.startswith("move"):
      moveCharacters = 4
      msg = msg[moveCharacters:]
      #Second Player moved
      msg = msg.split()
      #X position value
      xIndex = 0
      #Y position value
      yIndex = 1
      #Direction value
      dIndex = 2
      #Shot value
      sIndex = 3
      x = int(msg[xIndex])
      y = int(msg[yIndex])
      d = int(msg[dIndex])
      s = int(msg[sIndex])
      movePlayer(player2, x, y, d, s)
    elif msg.startswith("board"):
      syncronizeBoards(msg)
    elif msg.startswith("host"):
      MultiplayerData.started = True
    elif msg.startswith("zombies"):
      #Message with the zombies position and health
      msg = msg.replace("zombies","")
      Zombies.syncronizeZombiePos(msg)
    serverMsg.task_done()


#Server part ends here


def syncronizeBoards(msg):
  #Formats the board so that it removes the python set syntax
  msg = msg.replace("board", "")
  msg = msg.replace("{","")
  msg = msg.replace("}","")
  msg = msg.replace(", ", " ")
  msg = msg.replace("(", "")
  msg = msg.replace(")", "")
  #Creates a list for each value
  listWithPos = msg.split()
  setWithWalls = set()
  #Goes through all the data and puts it in a set with all the wall pos
  firstIndex = 0
  valuesPerWall = 2
  for value in range(firstIndex, len(listWithPos), valuesPerWall):
    row = int(listWithPos[value])
    followingIndex = 1
    col = int(listWithPos[value + followingIndex])
    setWithWalls.add((row, col))
  cols = Board.colsGlobal
  rows = Board.rowsGlobal
  noWall = 0
  emptyBoard = [([noWall] * cols) for row in range(rows)]
  #With the wall pos, sets the board according to the message received
  for wall in setWithWalls:
    rowIndex = 0
    colIndex = 1
    row, col = wall[rowIndex], wall[colIndex]
    wall = 1
    emptyBoard[row][col] = wall
  Table.table = emptyBoard

#Sends message that player moved
def sendMessagePlayerMoved(x, y, direction,shoot):
  typeMessage = "move"
  d = 0
  if direction == "DOWN":
    d = 1
  elif direction == "RIGHT":
    d = 2
  elif direction == "LEFT":
    d = 3
  msg = typeMessage + "%d %d %d %d\n" % (x, y, d, shoot) 
  server.send(msg.encode())

#Sends the random generated board
def sendMessageBoard(setWithWallPos):
  typeMessage = "board"
  #sends the board a string with the wall pos
  pos = str(setWithWallPos)
  msg = typeMessage + pos + "\n"
  server.send(msg.encode())

#Sends the positions of every zombie
def sendMessageZombiesPos():
  typeMessage = "zombies"
  pos = str(Zombies.zombiesPos)
  #Formats the string to send as least useless data as possible
  pos = pos.replace("[","")
  pos = pos.replace("]","")
  pos = pos.replace(", ", " ")
  pos = pos.replace("(", "")
  pos = pos.replace(")", "")
  msg = typeMessage + pos + "\n"
  server.send(msg.encode())

#Sends message that other player started the game
def sendMessageHostStarted():
  typeMessage = "hostStarted"
  msg = typeMessage +  "\n"
  server.send(msg.encode())

#Moves second player with data from server
def movePlayer(player2, x, y, d, s):
  player2.x = x
  player2.y = y
  player2.x0 = player2.x - (player2.width//2)
  player2.y0 = player2.y - (player2.height//2)
  if d == 0:
    player2.facing = "UP"
  elif d == 1:
    player2.facing = "DOWN"
  elif d == 2:
    player2.facing = "RIGHT"
  elif d == 3:
    player2.facing = "LEFT"
  #Player is shooting
  if s == 1:
    player2.shoot()

class Enemy(pygame.sprite.Sprite):
  def __init__(self, screen, entrance, player1=None,player2=None, board=None, host=False, speed=6, health=5):
    pygame.sprite.Sprite.__init__(self)
    self.host = host
    self.screen = screen
    self.width = 25
    self.height = 25
    self.x0 = 0
    self.y0 = 0
    divideByTwo = 2
    self.x = self.x0 + (self.width)//divideByTwo
    self.y = self.y0 + (self.height)//divideByTwo
    self.entrance = entrance
    #If the enemy was created by a non-host, there is no need to use the following data
    if self.host == True:
      self.board = board
      self.player1 = player1
      self.player2 = player2
      x = 0
      y = 0
      #Sents the positions for each entrance
      leftCenter = 0
      topCenter = 1
      rightCenter = 2
      bottomCenter = 3
      if entrance == leftCenter:
        x = -40
        y = 350
      elif entrance == topCenter:
        x = 350
        y = -40
      elif entrance == rightCenter:
        x = 790
        y = 350
      elif entrance == bottomCenter:
        x = 350
        y = 790
      self.x0 = x
      self.y0 = y
      self.x = self.x0 + (self.width)//divideByTwo
      self.y = self.y0 + (self.height)//divideByTwo
      self.speed = speed
      self.health = health
      #Direction it is facing
      self.facing = "UP"
      self.closestPlayer = self.findClosestHero()
      self.closestPlayerCell = getCurrentCell(self.closestPlayer.x, self.closestPlayer.y)
      self.movementDirections = None
    
    self.enemyImg = pygame.image.load('assets/enemy.png')
    self.enemyImg = pygame.transform.scale(self.enemyImg, (self.width, self.height))
    self.rect = self.enemyImg.get_rect()
    
  #Updates the image according to the zombie position
  def updateImage(self):
    if getCurrentCell(self.x, self.y) == None:
      return 
    self.screen.blit(self.enemyImg, (self.x0, self.y0))
    width = self.width
    height = self.height
    maxZombieY = 725
    screenHeight = 750
    #Does not update the zombie position if it is under the menu bar
    if self.y0 >= maxZombieY:
      height = screenHeight - self.y0 
    rect = pygame.Rect(self.x0,self.y0,self.width, self.height)
    pygame.display.update([rect])
    Board.updateRects.append(rect)
  
  #returns if the zombie is not inside the screen
  def offScreen(self):
    return getCurrentCell(self.x, self.y) == None

  #Moves the player into the screen
  def moveToScreen(self):
    leftCenter = 0
    topCenter = 1
    rightCenter = 2
    if self.entrance == leftCenter:
      self.x += self.speed
      self.x0 += self.speed
    elif self.entrance == topCenter:
      self.y += self.speed
      self.y0 += self.speed
    elif self.entrance == rightCenter:
      self.x -= self.speed
      self.x0 -= self.speed
    else:
      self.y -= self.speed
      self.y0 -= self.speed

  #Finds zombie's path
  def moveEnemy(self):
    #If the player is not the host, there is no need to find the zombie's path
    if self.host == False:
      return 

    if self.offScreen():
      self.moveToScreen()
      return 

    currentCell = getCurrentCell(self.x, self.y)
    self.closestPlayer = self.findClosestHero()
    
    #If there are no players left, the game is over
    if self.closestPlayer == None:
      return

    #Finds the closetsPlayer to the zombie
    if self.closestPlayerCell != getCurrentCell(self.closestPlayer.x, self.closestPlayer.y):
      self.closestPlayerCell = getCurrentCell(self.closestPlayer.x, self.closestPlayer.y)
      self.needsNewDirection(currentCell)
    
    #There is no more directions to move to, find more.
    if self.movementDirections == None:
      self.needsNewDirection(currentCell)

    #Zombie is at the player
    if self.movementDirections == []:
      return
    
    firstIndex = 0
    nRow, nCol = self.movementDirections[firstIndex]
    empty = 0
    if currentCell == self.movementDirections[firstIndex] and (self.x, self.y) == getCenterCell(nRow, nCol):
      self.movementDirections.pop(firstIndex)
    elif len(self.movementDirections) > empty:
      nextCell = self.movementDirections[firstIndex]

      if nextCell in Zombies.zombiesCells and currentCell != nextCell:
        return None
      self.movePlayer(nextCell)


      
  def needsNewDirection(self, currentCell):
    playerCell = getCurrentCell(self.closestPlayer.x, self.closestPlayer.y)
    if currentCell == playerCell:
      return None
    
    self.movementDirections = self.getMovementDirections(currentCell, playerCell)

    if self.movementDirections == None:
      self.movementDirections = []

  def movePlayer(self, nextCell):
    currentCell = getCurrentCell(self.x, self.y)
    cRow, cCol = currentCell
    nRow, nCol = nextCell
    nX, nY = getCenterCell(nRow, nCol)
    x, y = self.x, self.y
    dx, dy = abs(nX - x), abs(nY - y)
    noDifference = 0
    if (nX - x) > noDifference and (nY - y) > noDifference:
      self.r = 315
    elif (nX - x) < noDifference and (nY - y) < noDifference:
      self.r = 135
    elif (nX - x) > noDifference and (nY - y) < noDifference:
      self.r = 45
    elif (nX - x) < noDifference and (nY - y) > noDifference:
      self.r = 225
    elif (nX - x) > noDifference:
      self.r = 0
    elif (nX - x) < noDifference:
      self.r = 180
    elif (nY - y) > noDifference:
      self.r = 270
    elif (nY - y) < noDifference:
      self.r = 90

    #Finds the direction of movement, and moves the player
    if dx < self.speed:  
      step = (nX - x)
      self.x = nX
      self.x0 += step
    if dy < self.speed:
      step = (nY - y)
      self.y = nY
      self.y0 += step
    if dx >= self.speed:
      
      if nX > x:
        self.x += self.speed
        self.x0 += self.speed
      elif nX < x:
        self.x -= self.speed
        self.x0 -= self.speed
    if dy >= self.speed:
      if nY > y:
        self.y += self.speed
        self.y0 += self.speed
      elif nY < y:
        self.y -= self.speed
        self.y0 -= self.speed

  #Using backtracking, it is finding the path towards the zombie
  def getMovementDirections(self,currentPos, finalPos, visited=None, depth = 0):
    table = self.board
    if visited == None:
        visited = set()
    visited.add(currentPos)
    maxSearches = 100
    #If the depth is too big, return anything and make the zombie walk in a random direction.
    if currentPos == finalPos or depth > maxSearches:
      return []
    else:
      #The directions are changed according to the zombie position to optimise the search
      directions = self.findDirections(currentPos, finalPos)
      for direction in directions:
        dy,dx = direction
        y,x = currentPos
        tempPos = (y + dy, x + dx)
        if self.isValid(tempPos,visited, direction, currentPos,finalPos):
          increment = 1
          solution = self.getMovementDirections(tempPos, finalPos,visited, depth+increment)
          if (solution != None):
            return [tempPos] + solution
      visited.remove(currentPos)
      return None

  #Finds the ultimate direction for the backtracking search
  def findDirections(self, currentPos, finalPos):
    table = self.board
    cRow, cCol = currentPos
    fRow, fCol = finalPos
    dCol = (cCol-fCol)
    dRow = (cRow-fRow)
    n = (-1, 0)
    s = (1, 0)
    e = (0, 1)
    w = (0, -1)
    nw = (-1, -1)
    ne = (-1, 1)
    sw = (1, -1)
    se = (1, 1)
    noDifference = 0
    #Checks if the zombie is in the same line
    if dCol == noDifference and dRow != noDifference:
      if dRow > noDifference:
        tRow, tCol = n
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          #Finds how big the wall is
          width, direction = self.findWallWidth(tempPos)
          #Finds what way the wall is bigger
          if direction == "Left":
            return [e, w, s]
          else:
            return [w, e, s]
          return [n, w, e, s]
      elif dRow < noDifference:
        tRow, tCol = s
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          #Finds how big the wall is
          width, direction = self.findWallWidth(tempPos)
          #Finds what way the wall is bigger
          if direction == "Left":
            return [e, w, n]
          else:
            return [w, e, n]
        return [s, w, e, n]
    if dRow == noDifference and dCol != noDifference:
      if dCol < noDifference:
        tRow, tCol = e
        tempRow, tempCol = (cRow + tRow, cCol + tCol)    
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          #Finds how big the wall is
          height, direction = self.findWallHeight(tempPos)
          if direction == "Up":
            return [s, n, w]
          else:
            return [n, s, w]
        return [e, n, s, w]
      elif dCol > noDifference:
        tRow, tCol = w
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          height, direction = self.findWallHeight(tempPos)
          if direction == "Up":
            return [s, n, e]
          else:
            return [n, s, e]
        return [w, n, s, e]
    #Checks if the zombie is in a different col
    if dCol > noDifference:
      tRow, tCol = w
      tempRow, tempCol = (cRow + tRow, cCol + tCol)
      tempPos = (tempRow, tempCol)
      wall = 1
      if table[tempRow][tempCol] == wall:
        if dCol == wall:
          return [s, n, e]
        height, direction = self.findWallHeight(tempPos)
        if height < abs(dRow):
          if (dRow > noDifference):
            return [n, s, e]          
          return [s, n, e]
        elif direction == "Up":
          return [s, n, e]
        else:
          return [n, s, e]
      if dRow > noDifference:
        tRow, tCol = n
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
                
          if dRow == wall:
            return [w, e, s]
                
          width, direction = self.findWallWidth(tempPos)
          if width < abs(dCol):
            if dCol < noDifference:
              return [e, w, s]
            return [w, e, s]
          elif direction == "Left":
            return [e, w, s]
          else:
            return [w, e, s]
        return [nw, w, n, s, e] 
      else:  
        tRow, tCol = s
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          if dRow == -1:
            return [w, e, n]
          width, direction = self.findWallWidth(tempPos)
          if width < abs(dCol):
            if dCol < noDifference:
              return [e, w, n]          
            return [w, e, n]
          elif direction == "Left":
            return [e, w, n]
          else:
            return [w, e, n]
        return [sw, w, s, n, s] 
    else:
      tRow, tCol = e
      tempRow, tempCol = (cRow + tRow, cCol + tCol)
      tempPos = (tempRow, tempCol)
      wall = 1
      if table[tempRow][tempCol] == wall:    
        if dRow == wall:
          return [n, s, w]
        if dRow == -wall:
          return [s, n, w]
        height, direction = self.findWallHeight(tempPos)
        if height < abs(dRow):
          if (dRow > noDifference):
            return [n, s, w]      
          return [s, n, w]    
        elif direction == "Up":
          return [s, n, w]
        else:
          return [n, s, w]
      if dRow > noDifference:
        tRow, tCol = n
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          wall = 1
          if dRow == wall:
            return [e, w, s]
          width, direction = self.findWallWidth(tempPos)
          if width < abs(dCol):
            if (dCol < noDifference):
              return [e, w, s]            
            return [w, e, s]
          elif direction == "Left":
            return [e, w, s]
          else:
            return [w, e, s]
        return [ne, e, n, s, w] 
      else:
        tRow, tCol = s
        tempRow, tempCol = (cRow + tRow, cCol + tCol)
        tempPos = (tempRow, tempCol)
        wall = 1
        if table[tempRow][tempCol] == wall:
          if dRow == -1:
            return [e, w, n]
          width, direction = self.findWallWidth(tempPos)
          if width < abs(dCol):        
            if dCol < noDifference:
              return [e, w, n]
            return [w, e, n]
                
          elif direction == "Left":
            return [e, w, n]
          else:
            return [w, e, n]
        return [se, e, s, n, w] 
    samePos = (0,0)
    return [samePos]

  #Finds how big is the wall's width
  def findWallWidth(self, pos):
    table = self.board
    right = 0
    y, x = pos
    cols = 25
    left = 0
    tempRightX = x
    tempLeftX = x
    #Right
    wall = 1
    clearCell = 0
    while True:
      tempRightX += wall
      if tempRightX>=cols:
        break
      if table[y][tempRightX] == clearCell:
        break
      right += wall
    #Left
    while True:
      tempLeftX -= wall
      if tempLeftX<clearCell:
        break
      if table[y][tempLeftX] == clearCell:
        break
      left += wall
    
    if right > left:
      return (right, "Right")
    return (left, "Left")
    
  #Finds how big is the wall's height
  def findWallHeight(self, pos):
    table = self.board
    up = 0
    y, x = pos
    rows = 25
    down = 0
    tempUpY = y
    tempDownY = y
    wall = 1
    clearCell = 0
    #Down
    while True:
      tempDownY += wall
      
      if tempDownY>=rows:
        break
      if table[tempDownY][x] == clearCell:
        break
      down += wall
    #Up
    while True:
      tempUpY -= wall
      if tempUpY<clearCell:
        break
      if table[tempUpY][x] == clearCell:
        break
      up += wall
    if down > up:
      return (down, "Down")
    return (up, "Up")
    
  #Checks if cell is valid for movement
  def isValid(self, tempPos, visited, direction, currentPos, finalPos):
    table = self.board
    rows = len(table)
    firstIndex = 0
    cols = len(table[firstIndex])
    #Check if cell was already visited
    if tempPos in visited:
      return False
    row, col = tempPos
    row, col = int(row), int(col)
    minCell = 0
    #Checks if cell is in the board
    if row < minCell or col < minCell or row >= rows or col >= cols:
      return False
    wall = 1
    #Checks if cell is a wall
    if table[row][col] == wall:
      return False
    dRow, dCol = direction
    #diagonal movement
    if dRow != 0 and dCol != 0:
      cRow, cCol = currentPos
      tRow, tCol = cRow + dRow, cCol + dCol
      if table[cRow][tCol] == 1 or table[tRow][cCol] == 1:
        return False
    if tempPos == finalPos:
      return True
    if tempPos in Zombies.zombiesCells and tempPos != currentPos:
      return False
    return True
  
  #Returns the closes player
  def findClosestHero(self):
    #Check if player has health
    if self.player2.health <= 0 and self.player1.health > 0:
      return self.player1
    elif self.player1.health <= 0 and self.player2.health > 0:
      return self.player2
    elif self.player1.health <=0 and self.player2.health <= 0:
      return None
    #Gets the distance between players and return closest one
    distanceToPlayer1 = distance(self.player1.x, self.player1.y, self.x, self.y)
    distanceToPlayer2 = distance(self.player2.x, self.player2.y, self.x, self.y)
    if distanceToPlayer1 > distanceToPlayer2:
      return self.player2
    if self.player1.host:
      return self.player1
    else:
      return self.player2

#Returns the coordinates of the center of the cell
def getCenterCell(row, col):
  cellSize = Board.cellSizeGlobal
  half = 2
  x = (col * cellSize) + cellSize//half
  y = (row * cellSize) + cellSize//half
  return (x, y)


#returns the distance between two points
def distance(x0,y0,x1,y1):
  squared = 2
  squareRoot = 0.5
  return (((x0-x1)**squared)+((y0-y1)**squared))**squareRoot

#Class with all the bullets instances
class Bullets(object):
  bulletsList = pygame.sprite.Group()

#Class that conrtols zombies and contains every instance
class Zombies(object):
  zombiesList = pygame.sprite.Group()
  zombiesPos = []
  zombiesCells = set()

  #Stores the position of every zombie with its health level
  @staticmethod
  def checkZombiesPos():
    setWithPos = []
    for zombie in Zombies.zombiesList:
      location = (zombie.x0, zombie.y0, zombie.health)
      setWithPos.append(location)
    Zombies.zombiesPos = setWithPos
    
  #Receives the zombies positions from the host and adjusts the zombies
  @staticmethod
  def syncronizeZombiePos(msg):
    listWithValues = msg.split()
    #Checks how many zombies where sent
    threeItems = 3
    zombiesReceived = len(listWithValues)//threeItems
    index = 0
    #Goes through all the zombies and adjusts its position
    for zombie in Zombies.zombiesList:
      #If there are too many values, one zombie died
      if index >= len(listWithValues):
        Zombies.zombiesList.remove(zombie)
        continue
      x0 = int(listWithValues[index])
      increment = 1
      y0 = int(listWithValues[index+increment])
      health = int(listWithValues[index+increment+increment])
      half = 2
      x = x0 + (zombie.width//half)
      y = y0 + (zombie.height//half)
      zombie.x0 = x0
      zombie.y0 = y0
      zombie.health = health
      zombie.x = x
      zombie.y = y
      index += 3
    #If there are too little zombies, add more
    if len(Zombies.zombiesList) < zombiesReceived:
      while len(Zombies.zombiesList) != zombiesReceived:
        instance = Enemy(PygameData.screen, 0)
        Zombies.zombiesList.add(instance)

  #Checks if zombies where hit by a bullet
  @staticmethod
  def checkCollision():
    for zombie in Zombies.zombiesList:
      for bullet in Bullets.bulletsList:
        #Positions are used to check if the sprites are overlapping
        zX0 = zombie.x0
        zX1 = zX0 + zombie.width
        zY0 = zombie.y0
        zY1 = zY0 + zombie.height
        bX0 = bullet.x
        bX1 = bX0 + bullet.width
        bY0 = bullet.y
        bY1 = bY0 + bullet.height
        zTopLeft = (zX0, zY0)
        zBottomRight = (zX1, zY1)
        bTopLeft = (bX0, bY0)
        bBottomRight = (bX1, bY1)
        #If the sprites overlap, delete the bullet and decrease the zombie's health
        if checkSquareCollide(zTopLeft, zBottomRight, bTopLeft, bBottomRight):
          Bullets.bulletsList.remove(bullet)
          if zombie.host:
            if zombie.health > 0:
              zombie.health -= 1
            if zombie.health == 0:
              Zombies.zombiesList.remove(zombie)
  
  #Updates the cells where the zombies are located
  @staticmethod
  def checkZombieCells():
    cellSet = set()
    for zombie in Zombies.zombiesList:
      cell = getCurrentCell(zombie.x, zombie.y, zombie)
      cellSet.add(cell)
    Zombies.zombiesCells = cellSet

#Checks if two rectangles are overlapping
#Code from http://www.geeksforgeeks.org/find-two-rectangles-overlap/
def checkSquareCollide(l1, r1, l2, r2):
  firstItem = 0
  secondItem = 1
  if r1[firstItem] < l2[firstItem] or r2[firstItem] < l1[firstItem]:
    return False
  if r1[secondItem] < l2[secondItem] or l1[secondItem] > r2[secondItem]:
    return False
  return True

#player class
class hero(pygame.sprite.Sprite):
  def __init__(self, x, y,r,screen, board, playerName, secondary = False):
    pygame.sprite.Sprite.__init__(self)
    self.host = False
    self.connected = False
    self.board = board
    self.health = 35
    if secondary:
      self.health = 0
    self.ammo = 50
    self.x0 = x
    self.y0 = y
    self.width = 25
    self.height = 25
    self.x = self.x0 + (self.width//2)
    self.y = self.y0 + (self.height//2)
    self.speed = 6
    self.screen = screen
    self.heroImg = pygame.image.load('assets/hero.png')
    self.width = 25
    self.height = 25
    self.heroImg = pygame.transform.scale(self.heroImg, (self.width, self.height))
    #Direction moved
    self.facing = "UP"
    self.r = r
    self.rect = pygame.Rect(self.x,self.y,self.width, self.height)
    self.playerName = playerName

  def __repr__(self):
    return self.playerName
  
  #Checks if there is a zombie attacking the player
  #If there is, decrease health by one
  def decreaseHealth(self):
    currentCell = getCurrentCell(self.x, self.y)
    alive = 0
    if currentCell in Zombies.zombiesCells and self.health > alive:
      damage = 1
      self.health -= damage

  #Changes the direction the sprite is facing
  #Updates the image
  def updateImage(self):
    if self.health > 0:
      self.screen.blit(self.heroImg, (self.x0,self.y0))
    #Reset rotation
    iR = -self.r
    self.r = 0
    self.heroImg = pygame.transform.rotate(self.heroImg, iR)
    if self.facing == "DOWN":
      self.r = 180
    elif self.facing == "RIGHT":
      self.r = 270
    elif self.facing == "LEFT":
      self.r = 90
    self.heroImg = pygame.transform.rotate(self.heroImg, self.r)
    for shot in Bullets.bulletsList:
      if shot.hit:
        Bullets.bulletsList.remove(shot)
      xMax = 760
      xMin = -10
      yMax = 760
      yMin = -10
      #If the bullet is off the screen, stop using it.
      if shot.x > xMax or shot.x < xMin or shot.y > yMax or shot.y < yMin:
        Bullets.bulletsList.remove(shot)
      shot.move()
    x0 = self.x-self.speed
    y0 = self.y-self.speed
    x1 = x0 + 5
    y1 = y0 + 5
    rect = pygame.Rect(self.x0-15,self.y0-15,self.width+30, self.height+30)
    #Updates the screen with new image
    pygame.display.update([rect])
    if rect != self.rect:
      Board.updateRects.append(rect)
  
  #Shoots a bullet
  def shoot(self):
    empty = 0
    if self.ammo>empty:
      shot = bullet(self)
      Bullets.bulletsList.add(shot)
      bulletNumber = 1
      self.ammo-=bulletNumber

import random
class Ammo(pygame.sprite.Sprite):
  def __init__(self, table, player1, player2, screen):
    self.screen = screen
    self.player1 = player1
    self.player2 = player2
    self.img = pygame.image.load('assests/ammo.png')
    self.table = table
    rows = len(table)
    cols = len(table[0])
    pygame.sprite.Sprite.__init__(self)
    findLocation = True
    self.width = 25
    self.height = 25
    self.row = 0
    self.col = 0
    while findLocation:
      cell = 1
      row = random.randint(cell, rows-cell)
      col = random.randint(cell, cols-cell)
      clearCell = 0
      if table[row][col] == clearCell:
        self.row = row
        self.col = col
        findLocation = False
    self.x, self.y = getCenterCell(self.row, self.col)
    self.img = pygame.transform.scale(self.img, (self.width, self.height))
    self.x0, self.y0 = ((self.x - self.width//2), (self.y - self.height//2))
    self.rect = pygame.Rect(self.x0, self.y0, self.width, self.height)
    self.collected = False

  #Updates the image
  def updateImage(self):
    self.screen.blit(self.img, (self.x0,self.y0))
    pygame.display.update([self.rect])
  
  def checkIfCollected(self):
    player1Cell = getCurrentCell(self.player1.x, self.player1.y)
    player2Cell = getCurrentCell(self.player2.x, self.player2.y)
    currentCell = getCurrentCell(self.x, self.y)
    if currentCell == player1Cell:
      self.player1.ammo += 10
      self.collected = True
    if currentCell == player2Cell and self.player2.health > 0:
      self.player2.ammo += 10
      self.collected = True

#Class of bullets
class bullet(pygame.sprite.Sprite):
  def __init__(self, shooter):
    pygame.sprite.Sprite.__init__(self)
    self.board = shooter.board
    self.width = 5
    self.height = 5
    half = 2
    self.x = shooter.x0 + (shooter.width//half) - (self.width//half) 
    self.y = shooter.y0 + (shooter.height//half) - (self.height//half)
    self.screen = shooter.screen
    self.hit = False
    self.direction = shooter.r
    self.img = pygame.image.load('assests/bullet.png')
    self.speed = 10
    self.img = pygame.transform.scale(self.img, (self.width, self.height))
    self.screen.blit(self.img, (self.x,self.y))
    self.rect = self.img.get_rect()

  #Moves the bullet
  def move(self):
    n = 0
    e = 180
    s = 270
    w = 90
    #Checks the direction of movement and moves in that direction
    if self.direction == n:
      self.y -= self.speed
    elif self.direction == e:
      self.y += self.speed
    elif self.direction == s:
      self.x += self.speed
    elif self.direction == w:
      self.x -= self.speed
    #Updates the bullets image to new position
    self.screen.blit(self.img, (self.x,self.y))
    rect = pygame.Rect(self.x,self.y,self.width, self.height)
    
    #Check if it went out of screen
    if getCurrentCell(self.x, self.y) == None:
      Bullets.bulletsList.remove(self)
      return 
    cRow, cCol = getCurrentCell(self.x, self.y)
    firstItem = 0
    maxRow = len(self.board)
    maxCol = len(self.board[firstItem])
    rows = len(self.board)
    cols = len(self.board[firstItem])
    #Check if it went out of screen
    minCell = 0
    wall = 1
    #Updates position
    pygame.display.update([rect])
    Board.updateRects.append(rect)
    if cRow < minCell or cRow >= rows or cCol < minCell or cCol >= cols:
      Bullets.bulletsList.remove(self)
      return
    #Checks if it hit a wall
    elif self.board[cRow][cCol] == wall:
      Bullets.bulletsList.remove(self)

#Returns an empty board with the walls around    
def emptyBoard():
    rows = 25
    cols = 25
    emptyCell = 0
    emptyBoard = [([emptyCell] * cols) for row in range(rows)]
    #Walls around 
    row = 0
    wall = 1
    opening1 = 11
    opening2 = 12
    opening3 = 13
    opening = {opening1, opening2, opening3}
    for col in range(cols):
      if col not in opening:
        emptyBoard[row][col] = wall
    row = 24
    for col in range(cols):
      if col not in opening:
        emptyBoard[row][col] = wall
    col = 0
    for row in range(rows):
      if row not in opening:
        emptyBoard[row][col] = wall
    col = 24
    for row in range(rows):
      if row not in opening:
        emptyBoard[row][col] = wall
    return emptyBoard

import random
#Creates a random board
def populateBoard():
  board = emptyBoard()
  goal = 20
  maxAttempts = 2000
  tries = 0
  walls = 0 
  #Attempts to place a wall until it reached the goal
  #Due to efficiency, if it does not find a solution beofre the max attempts
  #Return what ever it has
  while walls != goal and maxAttempts > tries:
    tries += 1
    minCell = 3
    maxCell = 22
    row = random.randint(minCell, maxCell)
    col = random.randint(minCell, maxCell)
    maxLength = 4
    minLength = 3
    length = random.randint(minLength, maxLength)
    horizontalIndex = 0
    verticalIndex = 1
    #Gets a direction the wall will be in
    direction = ["horizontal", "vertical"][random.randint(horizontalIndex, verticalIndex)]
    #Check if wall is valid
    if isValidPos(board, row, col, direction, length):
      #If it is valid, place the walls
      board = placeWalls(board, row, col, length, direction)
      wall = 1
      walls += wall
  return board

#Returns a board with the walls inputed
def placeWalls(board, row, col, length, direction):
    wall = 1
    if direction == "horizontal":
      for colNumber in range(col, col+length):
        board[row][colNumber] = wall
    else:
      for rowNumber in range(row, row+length):
        board[rowNumber][col] = wall
    return board

#Check if wall is valid
def isValidPos(board, row, col, direction, length):
  delta = 2
  #Checks in the horizontal direction
  if direction == "horizontal":
    minRow = 0
    maxRow = 25
    minCol = 3
    maxCol = 24
    if row - delta < minRow or row + delta>= maxRow or col < minCol or col + length>= maxCol:
      return False
    lowerError = 2
    upperError = 3
    for rowNumber in range(row-lowerError, row+upperError):
      for colNumber in range(col-lowerError, col+length+lowerError):
        playerInitialRow = 9
        playerInitialCol = 10
        #Checks if wall is covering player's initial position
        if (rowNumber, colNumber) == (playerInitialRow, playerInitialCol):
          return False
        wall = 1
        #Checks if there is wall there already
        if board[rowNumber][colNumber] == wall:
          return False
  #Checks in the vertical direction      
  if direction == "vertical":
    minRow = 3
    maxRow = 24
    minCol = 0
    maxCol = 25
    if row < minRow or row + length >= maxRow or col - delta< minCol or col + delta  >= maxCol:
      return False
    lowerError = 2
    upperError = 3
    for rowNumber in range(row-lowerError, row+length+lowerError):
      for colNumber in range(col-lowerError, col+upperError):
        playerInitialRow = 9
        playerInitialCol = 10
        #Checks if wall is covering player's initial position
        if (rowNumber, colNumber) == (playerInitialRow, playerInitialCol):
          return False
        wall = 1
        #Checks if there is wall there already
        if board[rowNumber][colNumber] == wall:
          return False
  return True

#Class containing the game's table
class Table(object):
  table = populateBoard()

class Board(object):
  cellSizeGlobal = 30
  rowsGlobal = 25
  colsGlobal = 25
  updateRects = []
  def __init__(self, width, height, surface, table):
    self.board = Table.table
    self.surface = surface
    self.cellSize = 30
    self.rows = height//self.cellSize
    self.cols = width//self.cellSize
    self.rockImg = pygame.image.load('assests/rock.png')
    self.grassImg = pygame.image.load('assests/grass.png')

  #Gets top left corner coordinates of cell
  def getCoordinates(self, row, col):
    x = row * self.cellSize
    y = col * self.cellSize
    return x, y

  #Draws each individual cell
  def drawCell(self, row, col):
    x, y = self.getCoordinates(row,col)
    red = 250
    green = 250
    blue = 250
    color = (red, green, blue)
    rect = (x,y,self.cellSize,self.cellSize)
    width = 1
    #If value is 1, it is a wall
    wall = 1
    img = None
    if self.board[col][row] == wall:
      img = self.rockImg
      img = pygame.transform.scale(img, (self.cellSize, self.cellSize))
      self.surface.blit(img, (x,y))
    else:
      img = self.grassImg
      img = pygame.transform.scale(img, (self.cellSize, self.cellSize))
      self.surface.blit(img, (x,y))
  
  #Draws board by each individual cell
  def drawBoard(self):
    rows = self.rows
    cols = self.cols
    for row in range(rows):
      for col in range(cols):
        self.drawCell(row,col)
    pygame.display.flip()
  
  #Updates the screen
  def updateCellsRects(self):
    rows = self.rows
    cols = self.cols
    for row in range(rows):
      for col in range(cols):
        self.drawCell(row,col)
    #Updates the cells position on the screen
    pygame.display.update(Board.updateRects)
    Board.updateRects = []

#Instructions scene image
class InstructionsField(object):
  def __init__(self, screen):
    self.x = 100
    self.width = 550
    self.height = 400
    self.y = 175
    self.screen = screen
    self.img = pygame.image.load('assests/instructions.png')
    self.screen.blit(self.img, (self.x,self.y))
    self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
  
  #Updates the image
  def updateImage(self):
    self.screen.blit(self.img, (self.x,self.y))
    pygame.display.flip()

#Class to creating buttons
class Button(object):
  def __init__(self, option, x, y, width, height, screen):
    self.x = x
    self.y = y
    self.screen = screen
    self.width = width
    self.height = height
    self.option = option
    red = 255
    green = 175
    blue = 0
    #Background color
    self.color = (red, green, blue)

  #Sets the text and displays the button
  def updateImage(self):
    area = pygame.Rect(self.x,self.y,self.width,self.height)
    pygame.draw.rect(self.screen, self.color, area)
    fontSize = 15
    font = pygame.font.SysFont("monospace", fontSize)
    text = ""
    #Checks the different types of buttons
    if self.option == "singlePlayer":
      text = "SINGLE PLAYER"
    elif self.option == "multiPlayer":
      text = " MULTIPLAYER"
    elif self.option == "help":
      text = "     HELP"
    elif self.option == "backButton":
      text = "     BACK"
    elif self.option == "play":
      text = "     PLAY"
    elif self.option == "waiting for second player":
      text = "waiting for second player..."
    elif self.option == "second player connected":
      text = "   second player connected"
    elif self.option == "paused":
      text = " GAME PAUSED"
    elif self.option == "pressedP":
      text = " Press 'P' To Continue"
    elif self.option == "GAMEOVER":
      text = "  GAME OVER"
    elif self.option == "BACK":
      text = "     BACK"
    label = font.render(text, 1, (0,0,0))
    self.screen.blit(label, (self.x + 10, self.y + 15))
    pygame.display.update(area)

  #Checks if the player clicked the buttton
  def checkClick(self, mouseX, mouseY):
    if mouseX > self.x and mouseX < (self.x + self.width) and mouseY > self.y and mouseY < (self.y + self.height):
      return True

#Checks if the other player started the game
class MultiplayerData(object):
  started = False
  
#Contains the screen attribute of pygame
class PygameData(object):
  width = 750
  height = 800
  screen = pygame.display.set_mode((width, height))

#Main function
#Main structure from 112 Sockets Demo
def run(serverMsg, width=750, height=750):
  pygame.init()
  clock = pygame.time.Clock()
  screen = PygameData.screen
  #Name of the window
  pygame.display.set_caption("Boxhead")
  #Player's initial position
  xPos = 302
  yPos = 302
  rotation = 0
  #Wave variable 
  wave = 0
  #Wave dictionaries
  #Each wave have different values
  zombies = {1:4, 2:5, 3:6, 4:8, 5:10, 6:12, 7:15}
  healths = {1:5, 2:5, 3:5, 4:5, 5:5, 6:6, 7:8}
  speeds = {1:5, 2:5, 3:5, 4:6, 5:7, 6:7, 7:8}
  #Zombies on the game
  zombiesLeft = 0
  entrance = 0
  #Creates the table
  table = Table.table
  #Prints the board
  board = Board(width, height, screen, table)
  board.drawBoard()
  #Checks if board was sent to the second player
  sentBoardToSecondPlayer = False
  #Get positions of walls of the random generated table
  setWithWallPos = getWallPos(table)
  #Creates the two players
  player1 = hero(xPos,yPos,rotation,screen, table, "player1")
  player2 = hero(xPos,yPos,rotation,screen, table, "player2", True)
  #Creates the hero sprite group
  heroSpriteGroup = pygame.sprite.Group(player1, player2)
  ammoList = pygame.sprite.Group()
  #Games attributes
  playing = True
  fps = 45
  timer = 0
  #Scenes
  Menu = 0
  Instructions = 1
  Multiplayer = 2
  Game = 3
  Pause = 4
  Over = 5
  #Menu Items
  singlePlayerButton = Button("singlePlayer", 305, 300, 140, 50, screen)
  multiPlayerButton = Button("multiPlayer", 305, 400, 140, 50, screen)
  helpButton = Button("help", 305, 500, 140, 50, screen)
  #Instructions Items
  backButton = Button("backButton", 305, 700, 140, 50, screen)
  #Multiplayer Items
  playButton = Button("play", 305, 600, 140, 50, screen)
  waitingForSecondPlayerButton = Button("waiting for second player", 240,300, 270, 50, screen)
  playerConnectedButton = Button("second player connected", 240,300,270, 50, screen)
  instructionsTextField = InstructionsField(screen)
  #Paused game Items
  pausedButton = Button("paused", 305, 300, 140, 50, screen)
  continueText = Button("pressedP", 265, 600, 220, 50, screen)
  #Game Over Items
  gameOverText = Button("GAMEOVER", 305, 300, 140, 50, screen)
  #Scene
  scene = Menu
  #code modifed from 112 Sockets Demo
  while playing:
    #Frames per second
    time = clock.tick(fps) 
    frame = 1
    reset = 10
    timer = (timer + frame) % reset
    #Checks for player inputs
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        playing = False
      elif event.type == pygame.KEYDOWN and scene == Pause:
        #Unpauses the game
        if event.key == pygame.K_p:
          scene = Game
          board.drawBoard()
          continue
      elif event.type == pygame.KEYDOWN and scene == Game:
        if event.key == pygame.K_p and MultiplayerData.started == False:
          scene = Pause
          continue
        keyDown(event.key, player1, table, setWithWallPos)
    #Checks if player received messages
    checkReceivedMessages(serverMsg, player2)
    red = 215
    green = 215
    blue = 215
    screen.fill((red, green, blue))
    #Menu scene
    if scene == Over:
      gameOverText.updateImage()
      backButton.updateImage()
      leftButton = 0
      #Checks if left button was pressed
      if pygame.mouse.get_pressed()[leftButton]:
        #Mouse positions
        mouseX, mouseY = pygame.mouse.get_pos()
        #Checks if each button was clicked
        if backButton.checkClick(mouseX, mouseY):
          scene = Menu
          heroSpriteGroup.remove(player1, player2)
          player1 = hero(xPos,yPos,rotation,screen, table, "player1")
          player2 = hero(xPos,yPos,rotation,screen, table, "player2", True)
          heroSpriteGroup = pygame.sprite.Group(player1, player2)
          wave = 0
          for zombie in Zombies.zombiesList:
            Zombies.zombiesList.remove(zombie)
          for ammo in ammoList:
            ammoList.remove(ammo)
    elif scene == Pause:
      pausedButton.updateImage()
      continueText.updateImage()
    elif scene == Menu:
      #Updates button images
      singlePlayerButton.updateImage()
      multiPlayerButton.updateImage()
      helpButton.updateImage()
      leftButton = 0
      #Checks if left button was pressed
      if pygame.mouse.get_pressed()[leftButton]:
        #Mouse positions
        mouseX, mouseY = pygame.mouse.get_pos()
        #Checks if each button was clicked
        if singlePlayerButton.checkClick(mouseX, mouseY):
          scene = Game
          player1.host = True
          board.drawBoard()
          continue
        elif multiPlayerButton.checkClick(mouseX, mouseY):
          scene = Multiplayer
          board.drawBoard()
          continue
        elif helpButton.checkClick(mouseX, mouseY):
          scene = Instructions
          board.drawBoard()
          continue
    #Instructions scene
    elif scene == Instructions:
      backButton.updateImage()
      instructionsTextField.updateImage()
      if pygame.mouse.get_pressed()[0]:
        mouseX, mouseY = pygame.mouse.get_pos()
        #Checks if each button was clicked
        if backButton.checkClick(mouseX, mouseY):
          scene = Menu
          board.drawBoard()
          continue
    #Multiplayer scene
    elif scene == Multiplayer:
      if MultiplayerData.started:
        player1.board = Table.table
        player2.board = Table.table
        table = Table.table
        setWithWallPos = getWallPos(table)
        board.board = table
        scene = Game
        board.drawBoard()
        continue
      backButton.updateImage()
      #Player 2 connected
      if player2.connected:
        if sentBoardToSecondPlayer == False:
          sendMessageBoard(setWithWallPos)
          sentBoardToSecondPlayer = True
        playerConnectedButton.updateImage()
        playButton.updateImage()
      #Player 2 is not connected
      else:
        waitingForSecondPlayerButton.updateImage()
      #Checks if left mouse button was clicked
      if pygame.mouse.get_pressed()[0]:
        mouseX, mouseY = pygame.mouse.get_pos()
        #Checks if each button was clicked
        if backButton.checkClick(mouseX, mouseY):
          scene = Menu
          board.drawBoard()
          continue
        if playButton.checkClick(mouseX, mouseY) and player2.connected:
          sendMessageHostStarted()
          player1.host = True
          scene = Game
          board.drawBoard()
          continue
    #Game scene
    elif scene == Game:
      if len(Zombies.zombiesList) == 0:
        wave += 1
        if wave <= 7:
          zombiesLeft = zombies[wave]
        else:
          zombiesLeft = 15
      possibleEntrances = 4
      empty = 0
      if len(ammoList) == empty:
        ammoInstance = Ammo(table, player1, player2, screen)
        ammoList.add(ammoInstance)
      for ammo in ammoList:
        if ammo.collected:
          ammoList.remove(ammo)
        else:
          ammo.updateImage()
          ammo.checkIfCollected()
      #Spawn Zombies
      for zombieCount in range(possibleEntrances):
        if zombiesLeft > 0:
          if entrance not in Zombies.zombiesCells:
            if player1.host:
              speed = 6
              health = 5
              if wave <= 7:
                speed = speeds[wave]
                health = healths[wave]
              else:
                speed = 8
                health = 8
              #Instanciates zombies
              zombieInstance = Enemy(screen, entrance, player1, player2, table, True, speed, health)
              Zombies.zombiesList.add(zombieInstance)
              zombieInstance.x
            else:
              #If this is not the host, instanciates zombies that do not move
              zombieInstance = Enemy(screen, entrance, player1, player2, table, False)
              Zombies.zombiesList.add(zombieInstance)
            zombiesLeft -= 1
          #Change entrace
          entrance = (entrance + 1) % 4
      #Updates the screen with moved items
      board.updateCellsRects()   
      #Check if any zombie collided
      Zombies.checkCollision()
      Zombies.checkZombieCells()
      #Updates every zombie's image
      for zombieInstance in Zombies.zombiesList:
        zombieInstance.updateImage()
      if timer == 5 and player1.host:
        #Every 5 frames, move player or update its position from host
        for zombieInstance in Zombies.zombiesList:
          zombieInstance.moveEnemy()
          if player2.connected:
            Zombies.checkZombiesPos()
            sendMessageZombiesPos()
      #Checks if zombie was attacked
      if timer == 5:
        player1.decreaseHealth()
        player2.decreaseHealth()
      #Draws players
      player1.updateImage()
      player2.updateImage()
      #Create Game Info
      area = pygame.Rect(0,750,750, 50)
      color = (153, 153, 153)
      pygame.draw.rect(screen, color, area)
      font = pygame.font.SysFont("monospace", 15)
      text = "PLAYER 1 HEALTH: %d    PLAYER 2 HEALTH: %d    AMMUNITION: %d    WAVE: %d" %(player1.health, player2.health, player1.ammo, wave)
      label = font.render(text, 1, (0,0,0))
      screen.blit(label, (10, 765))
      pygame.display.update(area)
      if player1.health <= 0 and player2.health <= 0:
        scene = Over
  #Player closed screen
  pygame.quit()

#Returns a set with tuples of wall pos
def getWallPos(table):
  setWithWalls = set()
  for row in range(len(table)):
    for col in range(len(table)):
      #Checks if local pos is a wall
      if table[row][col] == 1:
        pos = (row, col)
        setWithWalls.add(pos)
  return setWithWalls

#Gets the current cell for the center of the player
def getCurrentCell(x,y, zombie=False):
  if x < 0 or y < 0 or x > 750 or y > 750:
    if zombie != False:
      return zombie.entrance
    return None
  cellSize = Board.cellSizeGlobal
  row = y//cellSize
  col = x//cellSize
  return (row,col)

#Returns a set with the cells surrounding the cell
def getCellsAround(currentCell):
  cells = set()
  #Current Coordinates
  cRow, cCol = currentCell
  directions = [(-1,-1),(0,-1),(1,-1),
                (-1,0),        (1,0),
                (-1,1), (0,1),(1,1)]
  for direction in directions:
    dRow, dCol = direction
    tempRow = cRow + dRow
    tempCol = cCol + dCol
    #Checks if temp coordinate is valid
    if validCell(tempRow,tempCol):
      coordinate = (tempRow, tempCol)
      cells.add(coordinate)
  return cells

def validCell(row, col):
  maxRow = Board.rowsGlobal
  maxCol = Board.colsGlobal
  if row < 0 or row >= maxRow or col < 0 or col >= maxCol:
    return False
  return True
#Check if movement is valid
def movementIsValid(keysym, hero, table, setWithWallPos):
  if hero.health <= 0:
    return
  x0 = hero.x0
  y0 = hero.y0
  x1 = x0 + hero.width
  y1 = y0 + hero.height
  speed = hero.speed
  #Center pos
  x = (x0 + x1)//2
  y = (y0 + y1)//2
  if ((x0 - speed) < 0 and keysym == pygame.K_LEFT) or ((x1+speed) >= 750 and keysym == pygame.K_RIGHT) or ((y0-speed) < 0 and keysym == pygame.K_UP) or ((y1 + speed)>= 750 and keysym == pygame.K_DOWN):
    return False
  currentCell = getCurrentCell(x, y)
  cellAround = getCellsAround(currentCell)
  wallsAround = getWallsAround(setWithWallPos, cellAround)
  if len(wallsAround) == 0:
    return True
  wallsInMovementDirection = getWallsInMovementDirection(keysym, wallsAround, currentCell)
  if keysym == pygame.K_LEFT:
    if overlapsWall(wallsInMovementDirection["LEFT"], x0, y0, x1, y1,speed, "LEFT"):
      return False
  elif keysym == pygame.K_RIGHT:
    if overlapsWall(wallsInMovementDirection["RIGHT"], x0, y0, x1, y1,speed, "RIGHT"):
      return False
  elif keysym == pygame.K_UP:
    if overlapsWall(wallsInMovementDirection["UP"], x0, y0, x1, y1,speed, "UP"):
      return False 
  elif keysym == pygame.K_DOWN:
    if overlapsWall(wallsInMovementDirection["DOWN"], x0, y0, x1, y1,speed, "DOWN"):
      return False
  return True
  
def overlapsWall(wallSet, x0, y0, x1, y1, delta, direction):
  for wall in wallSet:
    Cx0,Cx1,Cy0,Cy1 = getCellPos(wall)
    if direction == "LEFT":
      tempX0 = x0 - delta
      #Overlap from top
      if (tempX0 < Cx1) and (y0 < Cy1) and (y1 > Cy1):
        return True
      #Overlap from center
      if (tempX0 < Cx1) and (y0 > Cy0) and (y1 < Cy1):
        return True
      #Overlap from bottom
      if (tempX0 < Cx1) and (y0 < Cy0) and (y1 > Cy0):
        return True
    elif direction == "RIGHT":
      tempX1 = x1 + delta
      #Overlap from top
      if (tempX1 > Cx0) and (y1 > Cy0) and (y0 < Cy0):
        return True
      #Overlap from center
      if (tempX1 > Cx0) and (y0 > Cy0) and (y1 < Cy1):
        return True
      #Overlap from bottom
      if (tempX1 > Cx0) and (y0 < Cy1) and (y1 > Cy0):
        return True
    elif direction == "UP":
      tempY0 = y0 - delta
      #Overlap from left
      if (tempY0 < Cy1) and (x0 < Cx0) and (x1 > Cx0):
        return True
      #Overlap from center
      if (tempY0 < Cy1) and (x0 > Cx0) and (x1 < Cx1):
        return True
      #Overlap from right
      if (tempY0 < Cy1) and (x0 < Cx1) and (x1 > Cx1):
        return True
    elif direction == "DOWN":
      tempY1 = y1 + delta
      #Overlap from left
      if (tempY1 > Cy0) and (x0 < Cx0) and (x1 > Cx0):
        return True
      #Overlap from center
      if (tempY1 > Cy0) and (x0 > Cx0) and (x1 < Cx1):
        return True
      #Overlap from right
      if (tempY1 > Cy0) and (x0 < Cx1) and (x1 > Cx1):
        return True
  return False

def getCellPos(cell):
  row, col = cell
  cellSize = Board.cellSizeGlobal
  y0 = row*cellSize
  y1 = y0 + cellSize
  x0 = col*cellSize
  x1 = x0 + cellSize
  return x0,x1,y0,y1

def getWallsAround(setWithWallPos, cellAround):
  walls = set()
  for cell in cellAround:
    if cell in setWithWallPos:
      walls.add(cell)
  return walls
  
#Checks the walls in each direciton
def getWallsInMovementDirection(keysym, wallsAround, currentCell):
  currentRow, currentCol = currentCell
  direction = {"UP": set(), "DOWN": set(), "RIGHT": set(), "LEFT": set()}
  for wall in wallsAround:
    wallRow, wallCol = wall
    if wallRow > currentRow:
      direction["DOWN"].add(wall)
    elif wallRow < currentRow:
      direction["UP"].add(wall)
    if wallCol > currentCol:
      direction["RIGHT"].add(wall)
    elif wallCol < currentCol:
      direction["LEFT"].add(wall)
  return direction

#Responds to keyDown
#Check if movement is valid
#If it is valid, perform movement and send to server movement
def keyDown(keysym, hero, table, setWithWallPos):
  #Check if hits the wall or not enough ammo
  if not movementIsValid(keysym, hero, hero, setWithWallPos):
    return None
  shoot = 0
  if keysym == pygame.K_LEFT:
    hero.facing = "LEFT"
    hero.x0 -= hero.speed
    hero.x -= hero.speed
  elif keysym == pygame.K_RIGHT:
    hero.facing = "RIGHT"
    hero.x0 += hero.speed
    hero.x += hero.speed
  elif keysym == pygame.K_UP:
    hero.facing = "UP"
    hero.y0 -= hero.speed
    hero.y -= hero.speed
  elif keysym == pygame.K_DOWN:
    hero.facing = "DOWN"
    hero.y += hero.speed
    hero.y0 += hero.speed
  elif keysym == pygame.K_SPACE:
    shoot = 1
    hero.shoot()
  sendMessagePlayerMoved(hero.x,hero.y,hero.facing,shoot)
  
queueSize = 100
serverMsg = Queue(queueSize)
start_new_thread(handleServerMsg, (server, serverMsg))

run(serverMsg)
