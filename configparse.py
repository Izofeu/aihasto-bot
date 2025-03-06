import os

class parseconfig:
    def __init__(self, configname):
        self.configname = configname
        self.config = {}
        self.loaded = False
    def load(self):
        if self.loaded:
            print("Reloading config file...")
        try:
            configfile = open(self.configname, "rt")
            for line in configfile:
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    self.config[key.strip()] = self.converttype(value.strip())
            configfile.close()
            self.loaded = True
        except:
            print("error")
    def converttype(self, value):
        # string to int
        try:
            value = int(value)
            return value
        except:
            pass
        return value
    def get(self, key):
        try:
            return self.config[key]
        except:
            print("The key does not exist.")
            return False
    def loadtoken(self):
        if not self.loaded:
            print("Config file is not loaded!")
            return False
        else:
            try:
                tokenfile = self.get("tokenfile")
                tokenfile = open(tokenfile, "rt")
                token = tokenfile.read()
                tokenfile.close()
                return token
            except:
                print("Error reading the token file!")
                return False
    def set(self, keyname, valuename):
        try:
            keyname = str(keyname)
            valuename = str(valuename) + "\n"
            foundKey = False
            firstRun = True
            configfile = open(self.configname, "rt")
            secondconfig = open(self.configname + ".new", "wt")
            for line in configfile:
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if key.strip() == keyname.strip():
                        key = keyname.strip()
                        value = valuename
                        foundKey = True
                    if not firstRun:
                        secondconfig.write("\n")
                    else:
                        firstRun = False
                    secondconfig.write(key + "=" + value.strip())
            if not foundKey:
                secondconfig.write("\n" + keyname + "=" + valuename.strip())
            configfile.close()
            secondconfig.close()
            os.remove(self.configname)
            os.rename(self.configname + ".new", self.configname)
            self.load()
        except:
            print("Error writing to config file.")
        return