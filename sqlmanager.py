import asyncio
import aiomysql as sqlm
class sqlmanager:
    def __init__(self, cfg):
        self.lock = asyncio.Lock()
        # Prepare cfg
        self.cfg = cfg
        self.dbuser = self.cfg.get("dbuser")
        self.dbaddress = self.cfg.get("dbaddress")
        self.dbname = self.cfg.get("dbname")
        self.dbport = self.cfg.get("dbport")
        self.dbpassword = ""
        # Unused variable
        self.connected = False
        self.connection = None
        # Variable for running a check query once
        self.firstRun = True
        passwordfile = self.cfg.get("dbpwdfile")
        try:
            file = open(passwordfile, "rt")
            self.dbpassword = file.read()
            file.close()
        except:
            raise CannotOpenDbPasswordFile
    # Connect / Disconnect from database
    async def condisconnect(self, mode):
        if mode == 1:
            self.connection.close()
            self.connected = False
        else:
            try:
                self.connection = await sqlm.connect(host = self.dbaddress, user = self.dbuser, password = self.dbpassword, port = self.dbport, db = self.dbname, autocommit=True)
                self.connected = True
            except:
                print("Couldn't connect to database.")
        return
    async def query(self, query, params = False):
        async with self.lock:
            await self.condisconnect(0)
            cur = await self.connection.cursor()
            if self.firstRun:
                # Run a create table if not exists query once
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `flooders`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`expiration_date` DATETIME NOT NULL," +
                "`removed` BOOL NOT NULL DEFAULT 0," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await cur.execute(tablequery)
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `warns`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`expiration_date` DATETIME NOT NULL," +
                "`reason` VARCHAR(512) NOT NULL," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await cur.execute(tablequery)
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `gladiators`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`expiration_date` DATETIME NOT NULL," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await cur.execute(tablequery)
                self.firstRun = False
            # Execute our query
            if params:
                await cur.execute(query, params)
            else:
                await cur.execute(query)
            # Fetch the result of a query
            result = await cur.fetchall()
            await cur.close()
            # Close connection
            await self.condisconnect(1)
            # Return the query result
        return result
        
    async def addflooder(self, id, duration):
        # Prepare the query for adding a flooder record
        query = (
        "INSERT INTO `flooders` (`account_id`, `expiration_date`) VALUES (" +
        str(id) + ", '" + str(duration) + "'"
        ");"
        )
        await self.query(query)
        return
        
    async def getexpiredflooders(self, currentdate):
        # Get all expired flooders
        query = "SELECT account_id FROM flooders WHERE removed = 0 AND expiration_date < '" + currentdate + "';"
        result = await self.query(query)
        return result
        
    async def markflooderasremoved(self, id):
        query = "UPDATE `flooders` SET removed = 1 WHERE account_id = " + str(id) + ";"
        await self.query(query)
        return
    
    async def removeflooder(self, id):
        query = "DELETE FROM `flooders` WHERE account_id = " + str(id) + " AND removed = 0;"
        await self.query(query)
        return
        
    async def removeoldflooders(self):
        query = "DELETE FROM `flooders` WHERE expiration_date < DATE(NOW() - INTERVAL 30 DAY);"
        await self.query(query)
        return
        
    async def addwarning(self, id, expirydate, reason):
        query = ("INSERT INTO `warns` (`account_id`, `expiration_date`, `reason`) VALUES (" +
        str(id) + ", '" + str(expirydate) + "', %s);")
        await self.query(query, [reason])
        return
        
    async def removewarnings(self, id):
        query = "DELETE FROM `warns` WHERE account_id = " + str(id) + ";"
        await self.query(query)
        return
        
    async def deleteexpiredwarns(self, date):
        query = "DELETE FROM `warns` WHERE expiration_date < '" + str(date) + "';"
        await self.query(query)
        return
        
    async def getwarnings(self, id):
        query = "SELECT id, expiration_date, reason FROM `warns` WHERE account_id = " + str(id) + " ORDER BY id DESC LIMIT 3;"
        result = await self.query(query)
        query = "SELECT COUNT(id) FROM `warns` WHERE account_id = " + str(id) + ";"
        count = await self.query(query)
        return count, result
        
    async def getfloodercount(self, id):
        query = "SELECT COUNT(id) FROM `flooders` WHERE account_id = " + str(id) + ";"
        result = await self.query(query)
        return int(result[0][0])
        
    async def isflooder(self, id):
        query = "SELECT COUNT(id) FROM `flooders` WHERE account_id = " + str(id) + " AND removed = 0;"
        result = await self.query(query)
        return int(result[0][0])
        
    async def getwarncount(self, id):
        query = "SELECT COUNT(id) FROM `warns` WHERE account_id = " + str(id) + ";"
        result = await self.query(query)
        return int(result[0][0])
        
    async def addgladiator(self, id, date):
        await self.removegladiator(id)
        query = "INSERT INTO `gladiators`(`account_id`, `expiration_date`) VALUES (" + str(id) + ", '" + str(date) + "');"
        await self.query(query)
        return
        
    async def removegladiator(self, id, date = False):
        if not date:
            query = "DELETE FROM `gladiators` WHERE account_id = " + str(id) + ";"
            await self.query(query)
        else:
            query = "DELETE FROM `gladiators` WHERE expiration_date < '" + str(date) + "';"
            await self.query(query)
        return