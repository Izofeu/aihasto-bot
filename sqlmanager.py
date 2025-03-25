import asyncio
import aiomysql as sqlm
import datetime

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
                "`issuer_id` varchar(40) NOT NULL," +
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
                "`issuer_id` varchar(40) NOT NULL DEFAULT '0'," +
                "`expiration_date` DATETIME NOT NULL," +
                "`issue_date` DATETIME NOT NULL DEFAULT '2025-01-01 00:00:00'," +
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
        
    async def addtemprole(self, id, issuer_id, duration, role_type, reason = False):
        # Prepare the query for adding a temprole record
        query = "UPDATE `temproles` SET removed = 1 WHERE account_id = " + str(id) + " AND role_type = " + str(role_type) + ";"
        await self.query(query)
        if reason:
            query = (
            "INSERT INTO `temproles` (`account_id`, `issuer_id`, `expiration_date`, `issue_date`, `role_type`, `reason`) VALUES (" +
            str(id) + ", " + str(issuer_id) + ", '" + str(duration) + "', '" + datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S") + "', " + str(role_type) + ", %s" +
            ");"
            )
            await self.query(query, [reason])
            return
        else:
            query = (
            "INSERT INTO `temproles` (`account_id`, `issuer_id`, `expiration_date`, `role_type`) VALUES (" +
            str(id) + ", '" + str(duration) + "', " + str(role_type) +
            ");"
            )
        await self.query(query)
        return
        
    async def removetemprole(self, id, role_type):
        query = "DELETE FROM `temproles` WHERE removed = 0 AND account_id = " + str(id) + " AND role_type = " + str(role_type) + ";"
        await self.query(query)
        return
        
    async def getexpiredtemproles(self, currentdate):
        # Get all expired temp roles
        query = "SELECT `account_id`, `role_type` FROM `temproles` WHERE removed = 0 AND expiration_date < '" + currentdate + "';"
        result = await self.query(query)
        return result
        
    async def markexpiredtemprolesasremoved(self, currentdate):
        query = "UPDATE `temproles` SET removed = 1 WHERE expiration_date < '" + currentdate + "';"
        await self.query(query)
        return
        
    async def deleteoldtemproles(self):
        query = "DELETE FROM `temproles` WHERE expiration_date < DATE(NOW() - INTERVAL 30 DAY);"
        await self.query(query)
        return
        
    async def addwarning(self, issuerid, id, expirydate, reason):
        query = ("INSERT INTO `warns` (`account_id`, `issuer_id`, `expiration_date`, `reason`) VALUES (" +
        str(id) + ", " + str(issuerid) + ", '" + str(expirydate) + "', %s);")
        await self.query(query, [reason])
        return
        
    async def removewarnings(self, id, issuerid = False):
        query = "DELETE FROM `warns` WHERE account_id = " + str(id) + ";"
        if issuerid:
            query = "DELETE FROM `warns` WHERE issuer_id = " + str(issuerid) + " AND account_id = " + str(id) + ";"
        await self.query(query)
        return
        
    async def deleteexpiredwarns(self, date):
        query = "DELETE FROM `warns` WHERE expiration_date < '" + str(date) + "';"
        await self.query(query)
        return
        
    async def getwarnings(self, id):
        query = "SELECT issuer_id, expiration_date, reason FROM `warns` WHERE account_id = " + str(id) + " ORDER BY id DESC LIMIT 10;"
        result = await self.query(query)
        query = "SELECT COUNT(id) FROM `warns` WHERE account_id = " + str(id) + ";"
        count = await self.query(query)
        return count[0][0], result
        
    async def getflooders(self, id):
        query = "SELECT issuer_id, expiration_date, issue_date, reason FROM `temproles` WHERE account_id = " + str(id) + " ORDER BY issue_date DESC LIMIT 5;"
        result = await self.query(query)
        query = "SELECT COUNT(id) FROM `temproles` WHERE account_id = " + str(id) + ";"
        count = await self.query(query)
        return count[0][0], result
        
    async def isflooder(self, id):
        query = "SELECT COUNT(id) FROM `temproles` WHERE account_id = " + str(id) + " AND removed = 0 AND role_type = " + str(self.flooderrole) + ";"
        result = await self.query(query)
        return int(result[0][0])
        
    async def getwarncount(self, id):
        query = "SELECT COUNT(id) FROM `warns` WHERE account_id = " + str(id) + ";"
        result = await self.query(query)
        return int(result[0][0])