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
	"""
	__slots__ = ("places", "chans", "patterns", "presets", "chosenPlace", "chosenChan", \
				"chosenPat", "chosenParams", "state", "port", "s", "finish")
	
	def __init__(self, placeFile, patternNamesFile, presetNamesFile):
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
		self.state = 0
		#Initialize port to 1535
		self.port = 1535
		#Initialize finished to be False.
		self.finish = False
	
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
	
	def killSocket(self):
	
	
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
			self.state = 1
	
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
			self.state = 2
		#Otherwise, go back to the main menu.
		else:
			self.state = 0
			
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
			self.state = 3
		
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
			self.state = 0
			
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
			self.state = 4
		#If the state is the back state, we have to kill the socket before returning
		#to the main menu.
		elif self.chosenChan == 4:
			#Have to kill the socket.
			self.state = 50
		#If the chosen channel is not the preset channel, or back, we go to the 
		#pattern select screen.
		else:
			self.state = 5
	
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
			self.state = 3
		#If the chosen pat was the other extra option,
		elif self.chosenPat == len(self.presets)+1:
			#Go to a state that clears out the current socket collection,
			#then returns to the main menu.
			self.state = 50
			#Add better socket closing code.
			
		#If the input was for an actual pattern, 
		else:
			#handle the parameter input of the pattern.
			self.clearScreen()
			#    param list     list of pattern objects      input dialog member
			self.chosenParams = self.presets[self.chosenPat].inputParameters()
			#Afterwards, go to a confirmation state.
			self.state = 10
	
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
			self.state = 3
		#If the chosen pat is the second auxillary appended choice,
		elif self.chosenPat == len(self.patterns)+1:
			#go to a state that clears out the current socket collection,
			#then returns to the main menu.
			self.state = 50
			#Better socket kill code.
		#Otherwise the input was that of an actual pattern.
		else:
			#handle the parameter input of the pattern.
			#   list of params   list of pattern objects      input dialog member
			self.clearScreen()
			self.chosenParams = self.patterns[self.chosenPat].inputParameters()
			#Afterwards, go to a confirmation state.
			self.state = 10
		
	
	#The main functionality of the program.
	def handle(self):
		#Main menu.
		if self.state == 0:
			mainMenu()

		#Verification.
		elif self.state == 1:
			verifScreen()
		
		#The creation of the socket.
		elif self.state == 2:
			createSocket()
				
		
		#Channel selection.
		elif self.state == 3:
			selectChannel()
		
		#Preset selection.
		elif self.state == 4:
			selectPreset()
			
		#Pattern selection.
		elif self.state == 5:
			selectPattern()
		
		#Confirms selection.
		elif self.state == 10:
			#Proper input.
			properInput = False
			sincerity = None
			settingName = None
			pNames = []
			pVals = []
			if self.chosenChan == 3:
				#Create setting info if it is a preset.
				settingName = "Preset{ " + str(self.presets[self.chosenPat].getName()) + " ("+str(self.chosenPat) +")"
				pNames = self.presets[self.chosenPat].getParamNameList()
				pVals  = self.presets[self.chosenPat].getParamValList()
			else:
				#Create setting info if it is a pattern.
				settingName = "Pattern{ " + str(self.patterns[self.chosenPat].getName()) + " ("+str(self.chosenPat) +")"
				pNames = self.patterns[self.chosenPat].getParamNameList()
				pVals  = self.patterns[self.chosenPat].getParamValList()
			while not properInput:
				self.clearScreen()	
				print("===================================")
				print("| Are you sure of your update?    |")
				print("| I hope you aren't going to be   |")
				print("| a dick to epilleptics...        |")
				print("|=T================================")
				print("| |Server: "+str(self.chosenPlace.getName()))
				print("| |Bank: "+str(self.chosenPlace.getBankName()))
				print("| |Channel: "+str(self.chans[self.chosenChan]))
				print("| |"+str(settingName))
				for i in range(len(pNames)):
					print("| |"+str(pNames[i])+"{ "+str(pVals[i]))
				print("==^================================")
				try:
					enteredInput = input("| YES=1 NO=0 =============> ")
				except:
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				try:
					sincerity = int(enteredInput)
					if sincerity < 0 or sincerity > 1:
						raise ValueError
					else:
						properInput = True
				except:
					self.clearScreen()
					try:
						input("***********************************\n"+ \
						"* Invalid choice. Press enter...  *\n"+ \
						"***********************************")
					except:
						print("\nkeyboard exit. Goodbye.")
						sys.exit(0)
					self.clearScreen()
			if sincerity == 1:
				#Calculate the checksum. It's the integer-divided average of
				#the first 8 bytes of the message.
				checksum = (153 + int(self.chosenPlace.getBank()) + int(self.chosenChan) + int(self.chosenPat) + int(pVals[0]) + int(pVals[1]) + int(pVals[2]) + int(pVals[3]))//8
							
				#Write to the socket.
				b = bytearray(9) #Create a byte array.
				b[0] = 153
				b[1] = self.chosenPlace.getBank()
				b[2] = self.chosenChan
				b[3] = self.chosenPat
				b[4] = int(pVals[0])
				b[5] = int(pVals[1])
				b[6] = int(pVals[2])
				b[7] = int(pVals[3])
				b[8] = checksum
				try:
					self.s.sendall(b)
					self.state = 50
				except:
					self.clearScreen()
					try:
						input("************************************\n"+ \
						"*    Transmission unsuccessful.   *\n"+ \
						"*          Press enter...         *\n"+ \
						"***********************************")
					except:
						print("\nkeyboard exit. Goodbye.")
						sys.exit(0)
					self.clearScreen()
					self.state = 50
					
			else:
				self.state = 50
			
		#Socket smoke stack.
		elif self.state == 50:
			killSocket();
				
				
				
				
				
				
				
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
		self.address = address
		self.name = name
		self.bank = bank
		self.bankName = bankName
	
	def __str__(self):
		toReturn = str(str(self.bankName)+ "\n|\t@"+str(self.name)+" ("+str(self.address)+")")
		return toReturn
	
	#Returns the address of this Place object.
	def getAddress(self):
		return self.address
	
	#Returns the name of this Place object.
	def getName(self):
		return self.name
	
	#Returns the chosen bank value of this Place object.
	def getBank(self):
		return self.bank
	
	def getBankName(self):
		return self.bankName
			

class LumaSetting(object):
	"""
		This encapsulates the input of a single pattern (OR PRESET)
		SLOTS:
		params:       List of parameter names.
		paramvals:    List of inputed values. This is the eventual
					  contents of parambytes 1-4, so for every param
                      byte without a parameter input we will store a zero.
		paramsfilled: boolean representing if we have gotten the 
					  parameters from the user.
		preset:		  boolean signalling if this is infact a preset as
					  opposed to a pattern.
		value:        numerical representation of the pattern.
	"""

	__slots__ = ("params", "name", "value", "paramVals", "paramsfilled", "preset")

	def __init__(self, name, value, params, preset):
		self.name = name
		#To avoid having a parameter with a new line, we create an extra, and remove it.
		self.params = params[:-1]
		self.paramVals = []
		self.paramsfilled = False
		self.preset = preset
		

	
	def __str__(self):
		return str(self.name)
	
	#Localized script to read in the parameters of this pattern.
	def inputParameters(self):
		if not self.preset:
			print("==================================")
			print("| Enter the parameters of your   |")
			print("| selected pattern.              |")
			print("| Values must range from 0-255   |")
			print("==================================")
			for i in range(4):
				
				if not self.preset:
					#Try to gliss in a parameter value...
					try:
						properInput = False
						currentInput = None
						while not properInput:
							try:
								currentInput = None
								properInput = False 
								try:
									#(x/y) name: 
									currentInput = input("("+str(i+1)+"/"+str(len(self.params))+") "+str(self.params[i])+": ")
								except:
									print("\nkeyboard exit. Goodbye.")
									sys.exit(0)
									
								enteredInput = int(currentInput)
								#We're packing this into a single character, so we need max min verif.
								if enteredInput < 0 or enteredInput > 255:
									raise ValueError
								properInput = True
							except ValueError:
								print("Improper input. Please enter a value between 0 and 255")
						#Add the input to paramValues.		
						self.paramVals.append(currentInput)
						
					#...but if we've already gone through all the params
					#add merely a zero.
					except IndexError:
						self.paramVals.append(0)
			if len(self.paramVals) == 4:
				self.paramsfilled = True
		else:
			print("==================================")
			print("| Presets haven't parameters.    |")
			print("| Press enter to complete        |")
			print("| update.                        |")
			print("==================================")
			for i in range(4):
				self.paramVals.append(0)
		
	
	#Returns whether or not the parameter collection dialog has been completed.
	def gottenParams(self):
		return self.paramsfilled
	
	#Returns the name of this LumaSetting.
	def getName(self):
		return self.name
	
	#Returns the numerical value of this LumaSetting.
	def getVal(self):
		return self.value
	
	#Returns the list of parameter names.
	def getParamNameList(self):
		return self.params
		
	#Returns the list of parameter values.
	def getParamValList(self):
		return self.paramVals


#Main program definition.
def main():
	script = Luma("places.lcf","patterns.lcf","presets.lcf")
	while(True):
		script.handle()
		
main()

