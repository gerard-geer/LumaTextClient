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
	
	#Ten newlines.
	def bumpUp(self):
		for i in range(5):
			print("\n")
	
	#85 newlines.NOT.
	def clearScreen(self):
		os.system('cls' if os.name == 'nt' else 'clear')
		#self.bumpUp()
	
	#Returns whether execution of the menu code is done. Shouldn't ever be,
	#The program is exited from within the menu code.
	def finished(self):
		return self.finish
	
	#The main functionality of the program.
	def handle(self):
		#Main menu.
		if self.state == 0:
			#Try for some proper input...
			properInput = False
			chosenIndex = None
			while not properInput:
				self.clearScreen()
				print("===================================")
				print("| Welcome to Luma's Text Client!  |")
				print("|                                 |")
				print("| First choose a location:        |")
				print("|==================================")
				for i in range(len(self.places)):
					print("|"+str(i)+"{ "+str(self.places[i]))
				print("|"+str(len(self.places))+"{ Exit Luma Text Client")
				print("===================================")
				try:
					enteredIndex = input("|YOUR CHOICE===============> ")
				except:
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				try: 
					chosenIndex = int(enteredIndex)
					if chosenIndex < 0 or chosenIndex > len(self.places):
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
			if chosenIndex == len(self.places):
				self.clearScreen()
				sys.exit(0)
			else:
				self.chosenPlace = self.places[chosenIndex]
				self.state = 1

		#Verification.
		elif self.state == 1:
			#Try for some proper input.
			properInput = False
			choice = None
			while not properInput:
				self.clearScreen()
				print("===================================")
				print("| Are you sure you wish to        |")
				print("| connect to:                     |")
				print("|=========T========================")
				print("| Bank:   | " + str(self.chosenPlace.getBankName()))
				print("| Server: | " + str(self.chosenPlace.getName()))
				print("| Address:| " + str(self.chosenPlace.getAddress()))
				print("==========^========================")
				try:
					enteredInput = input("| YES=1 NO=0 =============> ")
				except:
					sys.exit(0)
					print("\nkeyboard exit. Goodbye.")
				try:
					choice = int(enteredInput)
					if choice < 0 or choice > 1:
						raise ValueError
					else:
						properInput = True
				except:
					try:
						self.clearScreen()
						try:
							input("***********************************\n"+ \
							"* Invalid choice. Press enter...  *\n"+ \
							"***********************************")
						except:
							sys.exit(0)
							print("\nkeyboard exit. Goodbye.")
						self.clearScreen()
					except:
						sys.exit(0)
			if choice == 1:
				self.state = 2
			else:
				self.state = 0
		
		#The creation of the socket.
		elif self.state == 2:
			try:
				self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.s.settimeout(3)
				self.s.connect((self.chosenPlace.getAddress(), self.port))
				self.clearScreen()
				# input("***********************************\n"+ \
				# "*      Connection successful.     *\n"+ \
				# "*          Press enter...         *\n"+ \
				# "***********************************")
				# self.clearScreen()
				self.state = 3
			except:
				self.clearScreen()
				try:
					input("***********************************\n"+ \
					"*     Connection unsuccessful.    *\n"+ \
					"*          Press enter...         *\n"+ \
					"***********************************")
				except:
					sys.exit(0)
					print("\nkeyboard exit. Goodbye.")
				self.clearScreen()
				self.state = 0
				
		
		#Channel selection.
		elif self.state == 3:
			#Proper input.
			properInput = False
			chosenChan = None
			while not properInput:
				self.clearScreen()
				print("===================================")
				print("| Preset or per-channel pattern?  |")
				print("|                                 |")
				print("|===========T======================")
				print("| 0{Red     |")
				print("| 1{Green   |") 
				print("| 2{Blue    |")
				print("| 3{Presets |")
				print("| 4{Back    |")
				print("============^======================")
				try:
					enteredInput = input("| YOUR CHOICE ============> ")
				except:
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				try:
					self.chosenChan = int(enteredInput)
					if self.chosenChan < 0 or self.chosenChan > 4:
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
			#If the chosen channel is the preset channel, go to the presets screen.
			if self.chosenChan == 3:
				self.state = 4
			elif self.chosenChan == 4:
				#Have to kill the socket.
				self.state = 50
			else:
				self.state = 5
		
		#Preset selection.
		elif self.state == 4:
			#Proper input.
			properInput = False
			chosenPat = None
			while not properInput:
				self.clearScreen()
				print("===================================")
				print("| Select a preset:                |")
				print("|                                 |")
				print("|=T================================")
				for i in range(len(self.presets)):
					print("| | "+str(i)+"{ "+str(self.presets[i]))
				print("| |"+str(len(self.presets))+"{ back")
				print("| |"+str(len(self.presets)+1)+"{ Main Menu")
				print("==^================================")
				try:
					enteredInput = input("| YOUR CHOICE ============> ")
				except:
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				try:
					self.chosenPat = int(enteredInput)
					if self.chosenPat < 0 or self.chosenPat > len(self.presets)+1:
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
			if self.chosenPat == len(self.presets):
				#Go back to the channel selection screen.
				self.state = 3
			elif self.chosenPat == len(self.presets)+1:
				#Go to a state that clears out the current socket collection,
				#then returns to the main menu.
				self.state = 50
			else:
				#handle the parameter input of the pattern.
				self.clearScreen()
				self.chosenParams = self.presets[self.chosenPat].inputParameters()
				#Afterwards, go to a confirmation state.
				self.state = 10
		
		#Pattern selection.
		elif self.state == 5:
			#Proper input.
			properInput = False
			self.chosenPat = None
			while not properInput:
				self.clearScreen()
				print("===================================")
				print("| Select a pattern:               |")
				print("|                                 |")
				print("|=T================================")
				for i in range(len(self.patterns)):
					print("| | "+str(i)+"{ "+str(self.patterns[i]))
				print("| |"+str(len(self.patterns))+"{ back")
				print("| |"+str(len(self.patterns)+1)+"{ Main Menu")
				print("==^================================")
				try:
					enteredInput = input("| YOUR CHOICE ============> ")
				except:
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
				try:
					self.chosenPat = int(enteredInput)
					if self.chosenPat < 0 or self.chosenPat > len(self.patterns)+1:
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
			if self.chosenPat == len(self.patterns):
				#Go back to the channel selection screen.
				self.state = 3
			elif self.chosenPat == len(self.patterns)+1:
				#Go to a state that clears out the current socket collection,
				#then returns to the main menu.
				self.state = 50
			else:
				#handle the parameter input of the pattern.
				self.clearScreen()
				self.chosenParams = self.patterns[self.chosenPat].inputParameters()
				#Afterwards, go to a confirmation state.
				self.state = 10
		
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
			try:
				self.clearScreen()
				print("/^^^^^^^^^^^^^^^^^^^^^^^^^\\")
				print("<   Closing connection.   >")
				print("\\vvvvvvvvvvvvvvvvvvvvvvvvv/")
				print("...shutting down.")
				self.s.shutdown(socket.SHUT_RDWR)
				print("...closing.")
				self.s.close()
				print("...completed.")
				self.state = 0
			except:
				print("\n\n")
				print("/^^^^^^^^^^^^^^^^^^^^^^^^^\\")
				print("<  Error disconnecting.   >")
				print("<  Press enter...         >")
				print("\\vvvvvvvvvvvvvvvvvvvvvvvvv/")
				try:
					input("")
				except:
					print("\nkeyboard exit. Goodbye.")
					sys.exit(0)
			finally:
				self.state = 0
				
				
				
				
				
				
				
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