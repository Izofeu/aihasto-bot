class parseconfig:
    def __init__(self, configname):
        self.configname = configname
        self.config = {}
        self.loaded = False
    def load(self):
        try:
            configfile = open(self.configname, "rt")
            for line in configfile:
                if line and not line.startswith("#"):
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