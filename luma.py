#Import this to allow us to exit.
import sys
#SOCKETS!!
import socket
#For various quirks.
import os

class Luma(object):
	"""
		This is a script for writing commands to luma through
		a means that is not a super pretty java applet.
		SLOTS:
		places:       List of places to choose from. 
		chans:        Names of channels. (Red, Green, Blue, Presets)
		chosenPlace:  The place chosen by the user from places.
		chosenChan:   The numerical channel chosen by the user.
		chosenPat:    The numerical pattern or preset chosen by the user.
		chosenParams: The parameters configured during handling of the chosen LumaSetting's dialog.
		state:        The current state of execution.
		port:         The port to connect to.
		s:            Our socket.
		finished:     Boolean of whether or not we've finished executing the dialog.
		
		variousStates:Dedicated values representing menu states.
	"""
	__slots__ = ("places", "chans", "patterns", "presets", "chosenPlace", "chosenChan", \
				"chosenPat", "chosenParams", "state", "port", "s", "finish"
				"mmState", "verifState", "sCreateState", "chanState", "prSelectState", "paSelectState", "confirmState" )
	
	def __init__(self, placeFile, patternNamesFile, presetNamesFile):
	"""
	Initializes the Luma object.
	Loads all the data stored in the config files and populates all the patterns,
	channels, presets, and places.
	"""
		#Load the potential places from file.
		self.places = []
		placeList = open(placeFile)
		for line in placeList:
			#line arranged like this: "[address] [name] [bankValue] [bankName]
			lineContents = line.split("%")
			self.places.append(Place(lineContents[0], lineContents[1], int(lineContents[2]), lineContents[3]))

		#Make a channel dictionary.
		self.chans = ["Red", "Green", "Blue", "Presets"]

		#Load the patterns, with their names and parameter names read in from file.
		self.patterns = []
		patternList = open(patternNamesFile)
		for line in patternList:
			#Line organized like this: "[name] [value] [param 1] [param 2]...[param x]
			lineContents = line.split("%")
			name = lineContents[0]
			value = int(lineContents[1])
			paramNames = []
			for i in range(2, len(lineContents), 1):
				paramNames.append(lineContents[i])
			#Add a new pattern to patterns.
			self.patterns.append(LumaSetting(name, value, paramNames, False))
		
		#Load the presets, with their names read in from file.
		self.presets = []
		presetList = open(presetNamesFile)
		for line in presetList:
			lineContents = line.split("%")
			name = lineContents[0]
			value = int(lineContents[1])
			self.presets.append(LumaSetting(name, value, [], True))

		#Initialize state to 0 so that the program starts at the intended menu.
		self.state = self.mmState
		#Initialize port to 1535
		self.port = 1535
		#Initialize finished to be False.
		self.finish = False
		
		#Initialize state values.
		self.mmState = 0
		self.verifState = 1
		self.sCreateState = 2
		self.chanState = 3
		self.prSelectState = 4
		self.paSelectState = 5
		self.confirmState = 10
	
	def bumpUp(self):
	"""
	Bumps the location of text by 5 lines.
	"""
		for i in range(5):
			print("\n")
			
	
	def clearScreen(self):
	"""
	Submits the local OS's clear command to the input stream of the terminal instance
	this script is running in.
	"""
		os.system('cls' if os.name == 'nt' else 'clear')
		self.bumpUp()
	
	
	def finished(self):
	"""
	Returns whether execution of the menu code is done. Shouldn't ever be,
	since the program is exited from within the menu code.
	"""
		return self.finish
		
	
	def killSocket(self, stateToGoTo):
	"""
	Kills the client's socket. The script should return to a 
	state prior to socket creation.
	"""
		try:
			#Clear the screen.
			self.clearScreen()
			#Print the alert that the connection is closing.
			print("***************************")
			print("<   Closing connection.   >")
			print("***************************")
			
			#Alert that the socket is being shut down.
			print("...shutting down.")
			#closes down both read(RD) and write(WR) streams.
			self.s.shutdown(socket.SHUT_RDWR)
			
			#Alert that the socket is being closed.
			print("...closing.")
			#Closes, and defocuses the socket instance.
			self.s.close()
			
			#Alert that the procedure has been completed.
			print("...completed.")
			
			#Go to the state specified.
			self.state = stateToGoTo
		
		#If anything goes wrong above, it will be due to the closing
		#of the socket. Since shutdown is data-safe, it will be because
		#the socket was never connected.
		except:
			#Print the notification.
			print("\n\n")
			print("***************************")
			print("<  Error disconnecting:   >")
			print("<  Socket already dead.   >")
			print("<  Press enter...         >")
			print("***************************")
			try:
				#Make the user press enter so we know he knows.
				input("")
			except:
				#Still have to catch the keyboard exit.
				print("\nkeyboard exit. Goodbye.")
				sys.exit(0)
		finally:
			#No matter what, we must go to the specified state.
			self.state = stateToGoTo;
	
	def handle(self):
	"""
	The main functionality of the program.
	"""
		#Main menu.
		if self.state == self.mmState:
			mainMenu()

		#Verification.
		elif self.state == self.verifState:
			verifScreen()
		
		#The creation of the socket.
		elif self.state == self.sCreateState:
			createSocket()
				
		
		#Channel selection.
		elif self.state == self.chanState:
			selectChannel()
		
		#Preset selection.
		elif self.state == self.prSelectState:
			selectPreset()
			
		#Pattern selection.
		elif self.state == self.paSelectState:
			selectPattern()
		
		#Confirms selection.
		elif self.state == self.confirmState:
			confirmation()
	
	
	def mainMenu(self):
	"""
	This handles the dialog and input for the main menu.
	The input algorithm here is used in every menu besides the
	parameter input dialog. It takes no inputs. It is at this screen
	that we choose a Location, which encapsulates the bank byte,
	server name, and server address. At the next screen we verify
	this choice.
	"""
		
		#Try for some proper input...
		properInput = False
		chosenIndex = None
		while not properInput:
			
			#Clear the screen of any pre-existing text.
			self.clearScreen()
			#Print the Title prompt.
			print("===================================")
			print("| Welcome to Luma's Text Client!  |")
			print("|                                 |")
			print("| First choose a location:        |")
			print("|==================================")
			
			
			#This loop prints a numerical list of all the locations that
			#were loaded from the config file.
			for i in range(len(self.places)):
				print("|"+str(i)+"{ "+str(self.places[i]))
				
			#Prints one final item for the list: an exit option.
			print("|=+==OTHER OPTIONS=================")
			print("|"+str(len(self.places))+"{ Exit Luma Text Client")
			
			#Footer serif.
			print("===================================")
			
			#This is where input is handled.
			try:
				#Take the input with this input prompt.
				enteredIndex = input("|YOUR CHOICE===============> ")
			except:
				#Catch the keyboard exit exception so we can exit casually.
				print("\nkeyboard exit. Goodbye.")
				sys.exit(0)
			try:
				#Try to convert the input to a number, and if it succeeds,
				#copy it as the chosen menu index.
				chosenIndex = int(enteredIndex)
				if chosenIndex < 0 or chosenIndex > len(self.places):
					raise ValueError
				else:
					#We prompt the user repeatedly until he enters a valid choice,
					#hence when he does make a proper choice, we need to stop the loop.
					properInput = True
			except:
				#If it doesn't succeed, print out an invalid input message.
				self.clearScreen()
				try:
					input("***********************************\n"+ \
					"* Invalid choice. Press enter...  *\n"+ \
					"***********************************")
				except:
					#At every input stage we must catch keyboard input.
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				self.clearScreen()
		#If the chosen menu index is equal to the length of the list of locations,
		#it is inherently the index of the exit option we appended. Hence, we exit.
		if chosenIndex == len(self.places):
			self.clearScreen()
			sys.exit(0)
		#Otherwise we copy the chosen Place object (which encapsulates the 
		#bank byte, server name, and server address) into our chosenPlace class 
		#variable for later use, then set the next state we want to handle to 1--the
		#verification screen.
		else:
			#						places is a list of Places
			self.chosenPlace = self.places[chosenIndex]
			self.state = self.mmState
			
	
	def verifScreen(self):
	"""
	The verification screen exists to allow users to check their selection before
	connecting to it. On CSH-Net this may be seen as a hindrance since on a lan
	these connections are made so fast. However, when connecting from afar, these
	connections may take several seconds to establish.
	Having to read five lines of text, though it might take longer than the connection
	time, is more stimulating (thus less agrivating) than waiting for the connection
	to time out, or successfully connect and then having to disconnect.
	This screen too takes no inputs. It is here that the Place is finalized, and at
	the next screen the connection is actually established.
	"""
		#Try for some proper input.
		properInput = False
		choice = None
		while not properInput:
			#Clear the screen of the previous menu.
			self.clearScreen()
			#Create the verification dialog according to theme.
			print("===================================")
			print("| Are you sure you wish to        |")
			print("| connect to:                     |")
			print("|=========T========================")
			print("| Bank:   | " + str(self.chosenPlace.getBankName())) #Print the bank name.
			print("| Server: | " + str(self.chosenPlace.getName()))		#Print the server name.
			print("| Address:| " + str(self.chosenPlace.getAddress()))	#Print the server address.
			print("==========^========================")
			
			#Get the choice of verification from the user.
			try:
				enteredInput = input("| YES=1 NO=0 =============> ")
			except:
				#once again capture the keyboard exit error.
				sys.exit(0)
				print("\nkeyboard exit. Goodbye.")
			try:
				#If we don't get that exit exception, try to convert the choice to a number.
				choice = int(enteredInput)
				#If the choice isn't 0 or 1, raise a value error.
				if choice < 0 or choice > 1:
					raise ValueError
				#Otherwise flag the input loop not to repeat.
				else:
					properInput = True
			except:
				#If the int conversion fails or that ValueError is raised,
				#clear the screen and print the invalid input prompt.
				try:
					self.clearScreen()
					try:
						input("***********************************\n"+ \
						"* Invalid choice. Press enter...  *\n"+ \
						"***********************************")
					except:
						#Capture the exit.
						sys.exit(0)
						print("\nkeyboard exit. Goodbye.")
					#Clear the screen after the user "enters" past this dialog.
					self.clearScreen()
				except:
					#Exit if there is any other type of error.
					sys.exit(0)
		
		#If the choice is 1, go to the Socket Creation stage,
		if choice == 1:
			self.state = self.sCreateState
		#Otherwise, go back to the main menu.
		else:
			self.state = self.mmState
			
			
	def createSocket(self):
	"""
	This is where the socket to the server is created. It uses the address
	encapsulated in the chosenPlace object, as well as the port specified
	during initialization. Note that the socket is a class variable.
	"""
		
		#We try to do a lot of things...
		try:
			#Construct the socket:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			
			#Set its timeout to 3 seconds:
			self.s.settimeout(3)
			
			#Connect it to the address of the chosenPlace at our port:
			self.s.connect((self.chosenPlace.getAddress(), self.port))
			
			#And finally clear the screen.
			self.clearScreen()
			
			#This was taken out due to annoyance. It was a "success" alert.
			# input("***********************************\n"+ \
			# "*      Connection successful.     *\n"+ \
			# "*          Press enter...         *\n"+ \
			# "***********************************")
			# self.clearScreen()
			
			#If all this is successful, go to the channel select screen.
			self.state = self.chanState
		
		#And if any of it fails...
		except:
			#Clear the screen,
			self.clearScreen()
			
			#Prompt to the user that the connection was not
			#successfully established,
			try:
				input("***********************************\n"+ \
				"*     Connection unsuccessful.    *\n"+ \
				"*          Press enter...         *\n"+ \
				"***********************************")
			except:
				#Yet again catch the keyboard exit.
				sys.exit(0)
				print("\nkeyboard exit. Goodbye.")
			
			#Penultimately clear the screen...
			self.clearScreen()
			#and return to the main menu.
			self.state = self.mmState
			
			
	def selectChannel(self):
	"""
	This is the screen where one selects the channel. Recall that the presets
	are accessed by setting the channel to channel 3, the 4th channel.
	It is here where the channel byte is finalized.
	"""
		#Proper input.
		properInput = False
		chosenChan = None
		while not properInput:
		
			#Clear the screen of previous dialog.
			self.clearScreen()
			#Print the channel menu.
			print("===================================")
			print("| Preset or per-channel pattern?  |")
			print("|                                 |")
			print("|===========T======================")
			print("| 0{Red     |")
			print("| 1{Green   |") 
			print("| 2{Blue    |")
			print("| 3{Presets |")
			print("|===========+==OTHER OPTIONS=======")
			print("| 4{Back    |")
			print("============^======================")
			try:
				#Try to get the input.
				enteredInput = input("| YOUR CHOICE ============> ")
			except:
				#Catch that keyboard exit. Here we have to close the socket before
				#exiting.
				print("\nkeyboard exit. Goodbye.")
				sys.exit(0)
			
			#Try to convert the user input to an int for setting the chosen channel.
			try:
				self.chosenChan = int(enteredInput)
				#If the input is an int, but out of range, 
				if self.chosenChan < 0 or self.chosenChan > 4:
					# we must also raise an error.
					raise ValueError
				#Otherwise, flag the input loop to close.
				else:
					properInput = True
			#If an error is raised during the above, it would have been due to an input error.
			except:
				#Clear previous dialog.
				self.clearScreen()
				#Spit out the invalid choice prompt.
				try:
					input("***********************************\n"+ \
					"* Invalid choice. Press enter...  *\n"+ \
					"***********************************")
				except:
					#Catch that keyboard exit. Here we have to close the socket before
					#exiting.
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				
				#Ultimately clear the screen of even the error prompts.
				self.clearScreen()
				
		#If the chosen channel is the preset channel, go to the presets screen.
		if self.chosenChan == 3:
			self.state = self.prSelectState
		#If the state is the back state, we have to kill the socket before returning
		#to the main menu.
		elif self.chosenChan == 4:
			#Have to kill the socket.
			self.state = self.paSelectState0
		#If the chosen channel is not the preset channel, or back, we go to the 
		#pattern select screen.
		else:
			self.state = self.paSelectState
			
	
	def selectPreset(self):
	"""
	This is the screen where one selects their preset. To get to this screen, one must
	have selected channel 3, the preset channel. If they would have selected any other
	channel, they would have gone to the pattern selection screen. In both preset and
	pattern selection we store the choice in chosenPat, since the choice made in either
	occupies the same byte in the transmitted message.
	"""
		#Getting proper input.
		properInput = False
		chosenPat = None
		while not properInput:
			
			#Clear the screen of any previous dialog.
			self.clearScreen()
			#Draw out the preset selection box.
			print("===================================")
			print("| Select a preset:                |")
			print("|                                 |")
			print("|=T================================")
			
			#This loop prints out a numbered, formatted list of 
			#the available presets.
			for i in range(len(self.presets)):
				print("| | "+str(i)+"{ "+str(self.presets[i]))
			
			#Additionally we append a back option, and a main menu option.
			print("|=+==OTHER OPTIONS=================")
			print("| |"+str(len(self.presets))+"{ back")
			print("| |"+str(len(self.presets)+1)+"{ Main Menu")
			print("==^================================")
			
			try:
				#Prompt the user for their choice of preset.
				enteredInput = input("| YOUR CHOICE ============> ")
			except:
				#Catch the keyboard exit. Don't forget we have to
				#close the socket.
				print("\nkeyboard exit. Goodbye.")
				sys.exit(0)
			
			#Try yet again to convert the user's input to an int for
			#easy consumption.
			try:
				#Convert the input to an int and store it as chosenPat.
				self.chosenPat = int(enteredInput)
				
				#If that input is out of range of the choices presented in
				#the menu...
				if self.chosenPat < 0 or self.chosenPat > len(self.presets)+1:
					#raise an error.
					raise ValueError
				#Otherwise the input was good and we need to signal to the input
				#loop that it needs to shut the hell up and die.
				else:
					properInput = True
			#Here again if an error happened above it would have been due to the
			#input not being good in the ways checked. So we...
			except:
				#...clear the screen...
				self.clearScreen()
				#...alert the user to their mistake...
				try:
					input("***********************************\n"+ \
					"* Invalid choice. Press enter...  *\n"+ \
					"***********************************")
				except:
					#...accounting for keyboard exits...
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				#...and clear the screen of the prompt.
				self.clearScreen()
		
		#If the chosen pat was the first "OTHER OPTION",
		if self.chosenPat == len(self.presets):
			#go back to the channel selection screen.
			self.state = self.chanState
		#If the chosen pat was the other extra option,
		elif self.chosenPat == len(self.presets)+1:
			#Go to a state that clears out the current socket collection,
			#then returns to the main menu.
			self.state = self.paSelectState0
			#Add better socket closing code.
			
		#If the input was for an actual pattern, 
		else:
			#handle the parameter input of the pattern.
			self.clearScreen()
			#    param list     list of pattern objects      input dialog member
			self.chosenParams = self.presets[self.chosenPat].inputParameters()
			#Afterwards, go to a confirmation state.
			self.state = self.confirmState
			
	
	def selectPattern(self):
	"""
	The dialog for selecting a pattern for one of the three independent color
	channels. To get to this dialog, the user would have had to choose either
	the red, blue, or green channel at the channel selection dialog screen.
	(Channels 0, 1, and 2 respectively.)
	"""
		#Proper input.
		properInput = False
		self.chosenPat = None
		while not properInput:
		
			#Clear the screen of yet other pre-existing evidence of interaction.
			self.clearScreen()
			
			#Create the header for the list of patterns.
			print("===================================")
			print("| Select a pattern:               |")
			print("|                                 |")
			print("|=T================================")
			
			#Draw the list of patterns.
			for i in range(len(self.patterns)):
				print("| | "+str(i)+"{ "+str(self.patterns[i]))
			
			#Append a back and Main Menu option to the list.
			print("|=+==OTHER OPTIONS=================")			
			print("| |"+str(len(self.patterns))+"{ back")
			print("| |"+str(len(self.patterns)+1)+"{ Main Menu")
			print("==^================================")
			
			#Get the input from the user...
			try:
				enteredInput = input("| YOUR CHOICE ============> ")
			#Again catching the elusive Keyboard Exit, Pokemon #9001.
			except:
				print("\nkeyboard exit. Goodbye.")
				sys.exit(0)
			
			#Again test the input to make sure it's a number and within range.
			try:
				self.chosenPat = int(enteredInput)
				if self.chosenPat < 0 or self.chosenPat > len(self.patterns)+1:
					raise ValueError
				else:
					properInput = True
			#If it's not, print the error prompt again.
			except:
				self.clearScreen()
				try:
					input("***********************************\n"+ \
					"* Invalid choice. Press enter...  *\n"+ \
					"***********************************")
				except:
				#Here too we must account for the keyboard exit.
					print("\nkeyboard exit. Goodbye.")
					#Close the socket.
					sys.exit(0)
				#And clear the screen.
				self.clearScreen()
		
		#If the chosen pat is the first auxillary appended choice,
		if self.chosenPat == len(self.patterns):
			#go back to the channel selection screen.
			self.state = self.chanState
		#If the chosen pat is the second auxillary appended choice,
		elif self.chosenPat == len(self.patterns)+1:
			#go to a state that clears out the current socket collection,
			#then returns to the main menu.
			self.state = self.paSelectState0
			#Better socket kill code.
		#Otherwise the input was that of an actual pattern.
		else:
			#handle the parameter input of the pattern.
			#   list of params   list of pattern objects      input dialog member
			self.clearScreen()
			self.chosenParams = self.patterns[self.chosenPat].inputParameters()
			#Afterwards, go to a confirmation state.
			self.state = self.confirmState
	

	def confirmation(self):
	"""
	This displays a confirmation dialog, constructs the message, and then transmits it.
	"""
		#Proper input.
		properInput = False
		
		#Sincerity is a boolean representing that of the user.
		sincerity = None
		
		#Stores the name of the chosen LumaSetting object for user review.
		settingName = None
		
		#Similarly stores the list of parameter names for user review.
		pNames = []
		
		#And yet further we store the selected values of those parameters--for review, of course.
		pVals = []
		
		#If the chosen channel was the preset channel, populate the review variables as such.
		if self.chosenChan == 3:
			#Create setting info if it is a preset.
			settingName = "Preset{ " + str(self.presets[self.chosenPat].getName()) + " ("+str(self.chosenPat) +")"
			pNames = self.presets[self.chosenPat].getParamNameList()
			pVals  = self.presets[self.chosenPat].getParamValList()
			
		#Likewise, if the chosen channel was the preset channel, populate the reiview variables as such.
		else:
			#Create setting info if it is a pattern.
			settingName = "Pattern{ " + str(self.patterns[self.chosenPat].getName()) + " ("+str(self.chosenPat) +")"
			pNames = self.patterns[self.chosenPat].getParamNameList()
			pVals  = self.patterns[self.chosenPat].getParamValList()
		
		#While the user-entered input is not valid,
		while not properInput:
		
			#Clear the screen...
			self.clearScreen()
			#Print an epillepsy warning, and a verification message.
			print("===================================")
			print("| Are you sure of your update?    |")
			print("| I hope you aren't going to be   |")
			print("| a dick to epilleptics...        |")
			print("|=T================================")
			#Below the warning and message we post the choices the user has
			#made so that they may review them.
			#Server name:
			print("| |Server: "+str(self.chosenPlace.getName()))
			#Bank name:
			print("| |Bank: "+str(self.chosenPlace.getBankName()))
			#Channel name:
			print("| |Channel: "+str(self.chans[self.chosenChan]))
			#Pattern/Preset name:
			print("| |Setting: "+str(settingName))
			
			#Now in a loop we print out the parameter names along
			#with their respective values.
			for i in range(len(pNames)):
				print("| |"+str(pNames[i])+"{ "+str(pVals[i]))
			
			#Footing serif.
			print("|=^==OPTIONS=======================")
			print("| 0: SUBMIT                       |")
			print("| 1: Go to Location/Main Menu     |")
			print("| 2: Go to Channel Menu           |")
			print("| 3: Go to Pattern/Preset Menu    |")
			print("| 4: Exit the client              |")
			print("===================================")
			#Try to garner verification input.
			try:
				#Give the user a prompt to base their input off of.
				enteredInput = input("| YES=1 NO=0 =============> ")
			except:
				#We still have to check for keyboard exiting.
				print("\nkeyboard exit. Goodbye.")
				#Kill the socket. Though we say we're going to
				#the main screen, we never do since we immediately exit.
				self.killSocket(self.mmState)
				sys.exit(0)
			
			#Try to get an answer from the user.
			try:
				#Attempt to convert their input to a number.
				sincerity = int(enteredInput)
				#If its a number, but not a choice, raise an error.
				if sincerity < 0 or sincerity > 4:
					raise ValueError
				#Otherwise, the input was valid.
				else:
					#Flag the input loop not to repeat.
					properInput = True
			
			#If an error was raised above, it was because of invalid input.
			except:
				#clear the screen so we merely see this prompt.
				self.clearScreen()
				try:
					input("***********************************\n"+ \
					"* Invalid choice. Press enter...  *\n"+ \
					"***********************************")
				except:
					#Here again we must check for keyboard input.
					print("\nkeyboard exit. Goodbye.")
					#And also we must kill the socket.
					self.killSocket(self.mmState)
					sys.exit(0)
				
				#Clear the screen of the prompt after it has been passed.
				self.clearScreen()
				
		if sincerity == 0:
			#Calculate the checksum. It's the integer-divided average of
			#the first 8 bytes of the message.
			checksum = (153 + int(self.chosenPlace.getBank()) + int(self.chosenChan) + int(self.chosenPat) + int(pVals[0]) + int(pVals[1]) + int(pVals[2]) + int(pVals[3]))//8
						
			#Write to the socket.
			b = bytearray(9) #Create a byte array for the message.
			b[0] = 153							#Continuity byte.
			b[1] = self.chosenPlace.getBank()	#Bank byte.
			b[2] = self.chosenChan				#Channel byte.
			b[3] = self.chosenPat				#Pattern/Preset byte.
			b[4] = int(pVals[0])				#Parameter byte A.
			b[5] = int(pVals[1])				#Parameter byte B.
			b[6] = int(pVals[2])				#Parameter byte C.
			b[7] = int(pVals[3])				#Parameter byte D.
			b[8] = checksum						#Checksum byte.
			
			#Attempt to send the data.
			try:
				#Send the data...
				self.s.sendall(b)
				#And kill the socket.
				self.killSocket(self.mmState)
			#If the transmission was unsuccessful...
			except:
				#Clear the screen...
				self.clearScreen()
				#Tell the user of the problem, and make them press enter to continue.
				try:
					input("************************************\n"+ \
					"*    Transmission unsuccessful.   *\n"+ \
					"*          Press enter...         *\n"+ \
					"***********************************")
				except:
					#YET AGAIN test for keyboard exiting.
					print("\nkeyboard exit. Goodbye.")
					self.killSocket(self.mmState)
					sys.exit(0)
				
				#If the transmission was unsuccesful, we clear the screen of the above prompt,
				self.clearScreen()
				#And kill the socket, returning to the main screen.
				self.killSocket(self.mmState);
		
		#If the user did not want to send their selection,
		else:
		
			#To return to the main menu we must kill the socket,
			#so we simply tell the socket kill routine to return us to state 0.
			if sincerity = 1:
				self.killSocket(self.mmState)
			
			#To return to the channel selection screen, we must simply set
			#the state to 3.
			if sincerity = 2:
				self.state = self.chanState
			
			#To return to the preset/pattern selection screen, we...
			if sincerity = 3:
				#must take into account the chosen pattern.
				if chosenChan == 3:
					#Go to the preset screen.
					self.state = self.prSelectState
				else
					#Go to the pattern screen.
					self.state = self.paSelectState
			
			#If the sincerity choice is 4, we must exit.
			if sincerity = 4:
				self.killSocket(self.mmState)
				sys.exit(0)
			
			#we kill the socket and return to the main menu.
			self.killSocket(self.mmState)
			
	
	


				
class Place(object):
	"""
		This class holds the information used to connect to the server.
		SLOTS:
		address:   The hostname of the server.
		name:      The name of the general place of the server, e.g. "Vator Lobby".
		bank:      The pwm bank you want to use on the server. There are two
		           per connected arduino.
	    bankName:  A more specific name, generally referring to the bank.
	"""
	
	__slots__ = ("address", "name", "bank", "bankName")
	
	def __init__(self, address, name, bank, bankName):
	"""
	Initializes this place object.
	"""
		self.address = address
		self.name = name
		self.bank = bank
		self.bankName = bankName
		
	
	def __str__(self):
	"""
	Returns a string representation of the data this Place object is encapsulating.
	"""
		toReturn = str(str(self.bankName)+ "\n|\t@"+str(self.name)+" ("+str(self.address)+")")
		return toReturn
		
	
	def getAddress(self):
	"""
	Returns the address of this Place object.
	"""
		return self.address
		
	
	def getName(self):
	"""
	Returns the name of this Place object.
	"""
		return self.name
		
	
	def getBank(self):
	"""
	Returns the bank value of this Place object.
	"""
		return self.bank
	
	def getBankName(self):
		return self.bankName
			

class LumaSetting(object):
	"""
		This encapsulates the input of a single pattern (OR PRESET)
		SLOTS:
		params:       	List of parameter names.
		
		paramvals:	List of inputed values. This is the eventual
				contents of parambytes 1-4, so for every param
                      		byte without a parameter input we will store a zero.
                      		
		paramsfilled: 	Boolean representing if we have gotten the 
				parameters from the user.
				
		preset:		Boolean signalling if this is infact a preset as
				opposed to a pattern.
				
		value:        	numerical representation of the pattern.
	"""

	__slots__ = ("params", "name", "value", "paramVals", "paramsfilled", "preset")

	def __init__(self, name, value, params, preset):
	"""
	Initializes this LumaSetting object.
	"""
		self.name = name
		#To avoid having a parameter with a new line, we create an extra, and remove it.
		self.params = params[:-1]
		self.paramVals = []
		self.paramsfilled = False
		self.preset = preset
		

	
	def __str__(self):
	"""
	When we want to print out data about this LumaSetting, we only want its name.
	"""
		return str(self.name)
		
	
	#Localized script to read in the parameters of this pattern.
	def inputParameters(self):
	"""
	In this routine we read in the parameters of this LumaSetting.
	
	If this LumaSetting has less than four parameters, after we
	finish getting the few parameters we do need, we fill the rest
	of the four slots with zeros.
	
	Remember that the extra parameters will ultimately be ignored.
	"""
		
		#If this LumaSetting is not flagged as a preset, we go through
		#and get input for each of its parameters.
		if not self.preset:
			
			#Print a header for the loop.
			print("==================================")
			print("| Enter the parameters of your   |")
			print("| selected pattern.              |")
			print("| Values must range from 0-255   |")
			print("==================================")
			
			#We cycle through each of the four parameter slots.
			#If there is not a parameter that is required for
			#the current slot, we simply place in a zero,
			#as stated above.
			for i in range(4):
				
				#Try to gliss in a parameter value...
				try:
					properInput = False
					currentInput = None
					
					#While the input is not verified as acceptable, we repeat the prompt.
					while not properInput:
					
						try:
							#Clear the value to store the input for the current parameter.
							currentInput = None
							#mark the input as false, since it has not been entered yet.
							properInput = False 
							
							#Get the input for this current parameter with a formatted prompt.
							#Here we also account for keyboard exiting.
							try:
								#(x/y) name: 
								currentInput = input("("+str(i+1)+"/"+str(len(self.params))+") "+str(self.params[i])+": ")
							except:
								print("\nkeyboard exit. Goodbye.")
								sys.exit(0)
							
							#Try to convert the input to an int.
							enteredInput = int(currentInput)
							#We're packing this into a single character(byte), so we need max min verif.
							if enteredInput < 0 or enteredInput > 255:
								raise ValueError
							properInput = True
						
						#If an error occurs above, it is due to the input being invalid.
						except ValueError:
							print("Improper input. Please enter a value between 0 and 255")
							
					#Add the input to paramValues.		
					self.paramVals.append(currentInput)
					
				#...but if we've already gone through all the params
				#add merely a zero.
				except IndexError:
					self.paramVals.append(0)
			#If the length of the string we've appended every entered parameter to is four,
			if len(self.paramVals) == 4:
				#record that it is so.
				self.paramsfilled = True
		else:
			print("==================================")
			print("| Presets haven't parameters.    |")
			print("| Press enter to complete        |")
			print("| update.                        |")
			print("==================================")
			for i in range(4):
				self.paramVals.append(0)
		

	def gottenParams(self):
	"""
	Returns whether or not the parameter collection dialog has been completed.
	"""
		return self.paramsfilled
	

	def getName(self):
	"""
	Returns the name of this LumaSetting.
	"""
		return self.name
	

	def getVal(self):
	"""
	Returns the numerical value of this LumaSetting.
	"""
		return self.value
	

	def getParamNameList(self):
	"""
	Returns the list of parameter names.
	"""
		return self.params
		

	def getParamValList(self):
	"""
	Returns the list of parameter values.
	"""
		return self.paramVals


def main():
	"""
	Main program definition. Simply creates an instance of the
	Luma class, and never stops running it.
	"""
	
	#Pass in the names of the config files.
	#.lcf = Luma Config File.
	script = Luma("places.lcf","patterns.lcf","presets.lcf")
	
	#Never stop running the script. The program is exited by
	#the user.
	while(True):
		script.handle()

#execute the program.		
main()

