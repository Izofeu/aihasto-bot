import os

class parseconfig:
    # Prepare the config class
    def __init__(self, configname):
        self.configname = configname
        self.config = {}
        self.loaded = False
    def load(self):
        # If config is loaded, print a reload config message
        if self.loaded:
            print("Reloading config file...")
            self.config = {}
        try:
            configfile = open(self.configname, "rt")
            # Load the config lines into a dictionary
            for line in configfile:
                # Ignore lines that start with #
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    self.config[key.strip()] = self.converttype(value.strip())
            configfile.close()
            self.loaded = True
        except:
            print("error")
    def converttype(self, value):
        # Convert value to int if the value is an int
        try:
            value = int(value)
            return value
        except:
            pass
        return value
    def get(self, key):
        try:
            # Obtain a value from a key.
            value = self.config[key]
            if isinstance(value, int):
                return self.config[key]
            try:
                firstchar = value[0]
                lastchar = value[-1]
                if firstchar == "[" and lastchar == "]":
                    rawarray = self.config[key][1:-1].split(",")
                    if len(rawarray) > 0:
                        newarray = []
                        try:
                            int(rawarray[0])
                            for element in rawarray:
                                newarray.append(int(element))
                            return newarray
                        except:
                            return rawarray
                    else:
                        return []
            except Exception as e:
                print(e)
            return self.config[key]
        except:
            raise Exception("The key " + str(key) + " does not exist / error obtaining key.")
            return False
    def loadtoken(self, tokenfile):
        # Load bot token
        if not self.loaded:
            print("Config file is not loaded!")
            return False
        else:
            try:
                tokenfile = open(tokenfile, "rt")
                token = tokenfile.read()
                tokenfile.close()
                return token
            except:
                print("Error reading the token file!")
                return False
    def setarray(self, keyname, array):
        value = "["
        firstrun = True
        for element in array:
            if firstrun:
                firstrun = False
            else:
                value += ","
            value += str(element)
        value += "]"
        self.set(keyname, value)
        return
    # Set a config key
    def set(self, keyname, valuename):
        try:
            keyname = str(keyname)
            if valuename is not None:
                valuename = str(valuename) + "\n"
            # If a key is found, replace it instead of creating a new line
            foundKey = False
            # This is used to remove lack of new lines when a new key is added
            firstRun = True
            configfile = open(self.configname, "rt")
            secondconfig = open(self.configname + ".new", "wt")
            for line in configfile:
                # Config save removes comment lines and new lines
                # Should be fixed in the future
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    # If current key is the same as the one we want to write, replace it instead
                    if key.strip() == keyname.strip():
                        key = keyname.strip()
                        value = valuename
                        foundKey = True
                        if valuename is None:
                            continue
                    if not firstRun:
                        # Fix for lack of new lines when a new key is added
                        secondconfig.write("\n")
                    else:
                        firstRun = False
                    secondconfig.write(key + "=" + value.strip())
            # A key wasn't found in any of the lines, add it at the end
            if not foundKey:
                secondconfig.write("\n" + keyname + "=" + valuename.strip())
            configfile.close()
            secondconfig.close()
            # File rewrite has been successful, replace the config files
            os.remove(self.configname)
            os.rename(self.configname + ".new", self.configname)
            # Automatically the new config file after updating a key
            self.load()
        except:
            print("Error writing to config file.")
        return