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
        self.flooderrole = 1
        self.gladiatorrole = 2
        self.mrmustardrole = 3
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
            raise Exception("Cannot open db password file.")
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
                raise Exception("Couldn't connect to database.")
        return
    async def query(self, query, params = False):
        async with self.lock:
            await self.condisconnect(0)
            cur = await self.connection.cursor()
            if self.firstRun:
                # Run a create table if not exists query once
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
                "CREATE TABLE IF NOT EXISTS `temproles`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`expiration_date` DATETIME NOT NULL," +
                "`role_type` INT NOT NULL," +
                "`reason` VARCHAR(512) NOT NULL DEFAULT 'No reason provided or ported punishment.'," +
                "`removed` BOOL NOT NULL DEFAULT 0," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await cur.execute(tablequery)
                # Port database code goes here
                if self.cfg.get("portdatabase") == 1:
                    tablequery = "SELECT `account_id`, `expiration_date`, `removed` FROM `flooders`;"
                    await cur.execute(tablequery)
                    result = await cur.fetchall()
                    for x in result:
                        aid = str(x[0])
                        date = str(x[1])
                        removed = str(x[2])
                        tablequery = "INSERT INTO `temproles` (`account_id`, `expiration_date`, `role_type`, `removed`) VALUES ('" + aid + "', '" + date + "', " + str(self.flooderrole) + ", " + removed + ");"
                        await cur.execute(tablequery)
                        #tablequery = "DELETE FROM `flooders`;"
                        #await cur.execute(tablequery)
                    self.cfg.set("portdatabase", 0)
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
        "INSERT INTO `temproles` (`account_id`, `expiration_date`, `role_type`) VALUES (" +
        str(id) + ", '" + str(duration) + "', " + str(self.flooderrole) +
        ");"
        )
        await self.query(query)
        return
        
    async def getexpiredflooders(self, currentdate):
        # Get all expired flooders
        query = "SELECT `account_id` FROM `temproles` WHERE removed = 0 AND role_type = " + str(self.flooderrole) + " AND expiration_date < '" + currentdate + "';"
        result = await self.query(query)
        return result
        
    async def markflooderasremoved(self, id):
        query = "UPDATE `temproles` SET removed = 1 WHERE role_type = " + str(self.flooderrole) + " AND account_id = " + str(id) + ";"
        await self.query(query)
        return
    
    async def removeflooder(self, id):
        query = "DELETE FROM `temproles` WHERE account_id = " + str(id) + " AND removed = 0 AND role_type = " + str(self.flooderrole) + ";"
        await self.query(query)
        return
        
    async def removeoldflooders(self):
        query = "DELETE FROM `temproles` WHERE role_type = " + str(self.flooderrole) + " AND expiration_date < DATE(NOW() - INTERVAL 30 DAY);"
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
        query = "SELECT COUNT(id) FROM `temproles` WHERE role_type = " + str(self.flooderrole) + " AND account_id = " + str(id) + ";"
        result = await self.query(query)
        return int(result[0][0])
        
    async def isflooder(self, id):
        query = "SELECT COUNT(id) FROM `temproles` WHERE account_id = " + str(id) + " AND removed = 0 AND role_type = " + str(self.flooderrole) + ";"
        result = await self.query(query)
        return int(result[0][0])
        
    async def getwarncount(self, id):
        query = "SELECT COUNT(id) FROM `warns` WHERE account_id = " + str(id) + ";"
        result = await self.query(query)
        return int(result[0][0])
        
    async def addgladiator(self, id, date):
        await self.removegladiator(id)
        query = "INSERT INTO `temproles`(`account_id`, `expiration_date`, `role_type`) VALUES (" + str(id) + ", '" + str(date) + "', " + str(self.gladiatorrole) + ");"
        await self.query(query)
        return
        
    async def removegladiator(self, id = 0, date = False):
        if not date:
            query = "DELETE FROM `temproles` WHERE role_type = " + str(self.gladiatorrole) + " AND account_id = " + str(id) + ";"
            await self.query(query)
            return
        else:
            query = "SELECT account_id FROM `temproles` WHERE role_type = " + str(self.gladiatorrole) + " AND expiration_date < '" + str(date) + "';"
            returnquery = await self.query(query)
            query = "DELETE FROM `temproles` WHERE role_type = " + str(self.gladiatorrole) + " AND expiration_date < '" + str(date) + "';"
            await self.query(query)
            return returnquery