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
        self.cur = None
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
    async def query(self, query, params = False, maintainconnection = False, connect = True):
        if connect:
            await self.lock.acquire()
        try:
            if connect:
                await self.condisconnect(0)
                self.cur = await self.connection.cursor()
            if self.firstRun:
                # Run a create table if not exists query once
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `warns`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`issuer_id` varchar(40) NOT NULL," +
                "`expiration_date` DATETIME NOT NULL," +
                "`reason` VARCHAR(512) NOT NULL DEFAULT 'No reason provided.'," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await self.cur.execute(tablequery)
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `temproles`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`issuer_id` varchar(40) NOT NULL DEFAULT '0'," +
                "`expiration_date` DATETIME NOT NULL," +
                "`issue_date` DATETIME NOT NULL DEFAULT '2025-01-01 00:00:00'," +
                "`role_type` INT NOT NULL," +
                "`reason` VARCHAR(512) NOT NULL DEFAULT 'No reason provided.'," +
                "`removed` BOOL NOT NULL DEFAULT 0," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await self.cur.execute(tablequery)
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `timeouts`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`issuer_id` varchar(40) NOT NULL DEFAULT '0'," +
                "`expiration_date` DATETIME NOT NULL," +
                "`issue_date` DATETIME NOT NULL DEFAULT '2025-01-01 00:00:00'," +
                "`reason` VARCHAR(512) NOT NULL DEFAULT 'No reason provided.'," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await self.cur.execute(tablequery)
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `notes`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "`issuer_id` varchar(40) NOT NULL DEFAULT '0'," +
                "`expiration_date` DATETIME NULL," +
                "`issue_date` DATETIME NULL," +
                "`reason` VARCHAR(512) NULL DEFAULT 'No reason provided.'," +
                "`notetype` INT NOT NULL," +
                "`isroot` BOOLEAN NOT NULL DEFAULT 0," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await self.cur.execute(tablequery)
                tablequery = (
                "CREATE TABLE IF NOT EXISTS `reportscount`" +
                "(" +
                "`id` INT NOT NULL AUTO_INCREMENT," +
                "`account_id` varchar(40) NOT NULL," +
                "PRIMARY KEY (id)" +
                ");"
                )
                await self.cur.execute(tablequery)
                self.firstRun = False
            # Execute our query
            if params:
                await self.cur.execute(query, params)
            else:
                await self.cur.execute(query)
            # Fetch the result of a query
            result = await self.cur.fetchall()
            rowid = self.cur.lastrowid
            if not maintainconnection:
                await self.cur.close()
                # Close connection
                await self.condisconnect(1)
            # Return the query result
        finally:
            if not maintainconnection:
                self.lock.release()
        return result, rowid
    
    async def getreportcount(self, id):
        query = "SELECT COUNT(id) FROM `reportscount` WHERE account_id = " + str(id)
        count = await self.query(query)
        return int(count[0][0])
    
    async def updatewarnreason(self, caseid, reason):
        query = "UPDATE `warns` SET reason = %s WHERE id = " + caseid
        await self.query(query, [reason])
        return
        
    async def updatetimeoutreason(self, caseid, reason):
        query = "UPDATE `timeouts` SET reason = %s WHERE id = " + caseid
        await self.query(query, [reason])
        return
        
    async def updatetemprolereason(self, caseid, reason):
        query = "UPDATE `temproles` SET reason = %s WHERE id = " + caseid
        await self.query(query, [reason])
        return
    
    async def getroot(self, notetype):
        query = "SELECT DISTINCT account_id FROM notes WHERE notetype = " + str(notetype) + " AND isroot = 1"
        rootinfo, rowid = await self.query(query)
        return rootinfo
        
    async def getallassigns(self, notetype):
        query = "SELECT account_id, issuer_id FROM notes WHERE notetype = " + str(notetype)
        assigns, rowid = await self.query(query)
        return assigns
    
    async def getnotesbytarget(self, id, notetype):
        query = "SELECT issuer_id, expiration_date, issue_date, reason FROM notes WHERE notetype = " + str(notetype) + " AND account_id = " + str(id)
        notes, rowid = await self.query(query, maintainconnection = True)
        query = "SELECT COUNT(id) FROM `notes` WHERE notetype = " + str(notetype) + " AND account_id = " + str(id)
        count, rowid = await self.query(query, maintainconnection = False, connect = False)
        return count[0][0], notes
        
    async def getnotesbyissuer(self, id, notetype):
        query = "SELECT account_id, expiration_date, issue_date, reason FROM notes WHERE notetype = " + str(notetype) + " AND issuer_id = " + str(id)
        notes, rowid = await self.query(query, maintainconnection = True)
        query = "SELECT COUNT(id) FROM `notes` WHERE notetype = " + str(notetype) + " AND issuer_id = " + str(id)
        count, rowid = await self.query(query, maintainconnection = False, connect = False)
        return count[0][0], notes
    
    async def addnote_nodate(self, id, issuer_id, notetype, reason, root):
        query = "INSERT INTO `notes` (account_id, issuer_id, reason, notetype, isroot) VALUES (" + str(id) + ", " + str(issuer_id) + ", %s, " + str(notetype) + ", " + str(root) + ")"
        await self.query(query, [reason])
        return
        
    async def addnote_date(self, id, issuer_id, notetype, issuedate, expirydate, reason):
        query = (
        "INSERT INTO `notes` (account_id, issuer_id, expiration_date, issue_date, reason, notetype) VALUES (" +
        str(id) + ", " + str(issuer_id) + ", '" + expirydate + "', '" + issuedate + "', %s, " + str(notetype) + ")"
        )
        await self.query(query, [reason])
        return
        
    async def removenote(self, id, issuer_id, notetype):
        query = "DELETE FROM `notes` WHERE account_id = " + str(id) + " AND issuer_id = " + str(issuer_id) + " AND notetype = " + str(notetype)
        await self.query(query)
        return
    
    async def addtimeout(self, id, issuer_id, duration, reason):
        query = (
        "INSERT INTO `timeouts` (account_id, issuer_id, expiration_date, issue_date, reason) VALUES (" +
        str(id) + ", " + str(issuer_id) + ", '" + str(duration) + "', '" + datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S") + "', %s);"
        )
        _, rowid = await self.query(query, [reason])
        return rowid
        
    async def removetimeout(self, id):
        query = "DELETE FROM `timeouts` WHERE account_id = " + str(id) + " ORDER BY id DESC LIMIT 1;"
        await self.query(query)
        return
        
    async def addtemprole(self, id, issuer_id, duration, role_type, reason = False):
        # Prepare the query for adding a temprole record
        query = "UPDATE `temproles` SET removed = 1 WHERE account_id = " + str(id) + " AND role_type = " + str(role_type) + ";"
        await self.query(query, maintainconnection = True)
        query = (
        "INSERT INTO `temproles` (`account_id`, `issuer_id`, `expiration_date`, `issue_date`, `role_type`, `reason`) VALUES (" +
        str(id) + ", " + str(issuer_id) + ", '" + str(duration) + "', '" + datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S") + "', " + str(role_type) + ", %s" +
        ");"
        )
        _, rowid = await self.query(query, [reason], connect = False, maintainconnection = False)
        return rowid
        
    async def removetemprole(self, id, role_type):
        query = "DELETE FROM `temproles` WHERE removed = 0 AND account_id = " + str(id) + " AND role_type = " + str(role_type) + ";"
        await self.query(query)
        return
        
    async def getexpiredtemproles(self, currentdate):
        # Get all expired temp roles
        query = "SELECT `account_id`, `role_type` FROM `temproles` WHERE removed = 0 AND expiration_date < '" + currentdate + "';"
        result, rowid = await self.query(query)
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
        _, rowid = await self.query(query, [reason])
        return rowid
        
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
        
    async def getflooders(self, id):
        # Gets executed 1st
        query = "SELECT issuer_id, issue_date, reason FROM `temproles` WHERE role_type = " + str(self.flooderrole) + " AND account_id = " + str(id) + " ORDER BY issue_date DESC LIMIT 5;"
        result, rowid = await self.query(query, maintainconnection = True)
        query = "SELECT COUNT(id) FROM `temproles` WHERE role_type = " + str(self.flooderrole) + " AND account_id = " + str(id) + ";"
        count, rowid = await self.query(query, maintainconnection = True, connect = False)
        return count[0][0], result
        
    async def getwarnings(self, id):
        # Gets executed 2nd
        query = "SELECT issuer_id, expiration_date, reason FROM `warns` WHERE account_id = " + str(id) + " ORDER BY id DESC LIMIT 5;"
        result, rowid = await self.query(query, maintainconnection = True, connect = False)
        query = "SELECT COUNT(id) FROM `warns` WHERE account_id = " + str(id) + ";"
        count, rowid = await self.query(query, maintainconnection = True, connect = False)
        return count[0][0], result
        
    async def gettimeouts(self, id):
        # Gets executed 3rd, closes connection
        query = "SELECT issuer_id, expiration_date, issue_date, reason FROM `timeouts` WHERE account_id = " + str(id) + " ORDER BY issue_date DESC LIMIT 5;"
        result, rowid = await self.query(query, maintainconnection = True, connect = False)
        query = "SELECT COUNT(id) FROM `timeouts` WHERE account_id = " + str(id) + ";"
        count, rowid = await self.query(query, maintainconnection = False, connect = False)
        return count[0][0], result
        
    async def isflooder(self, id):
        query = "SELECT COUNT(id) FROM `temproles` WHERE account_id = " + str(id) + " AND removed = 0 AND role_type = " + str(self.flooderrole) + ";"
        result, rowid = await self.query(query)
        return int(result[0][0])
        
    async def getpunishments(self, id):
        try:
            # Flooders
            floodercount, flooders = await self.getflooders(id)
            # Warnings
            warncount, warnings = await self.getwarnings(id)
            # Timeouts
            timeoutcount, timeouts = await self.gettimeouts(id)
        except Exception as e:
            print(e)
            # In case something ever goes wrong, release the AIO lock
            if self.lock.locked():
                self.lock.release()
        return [[floodercount, flooders], [warncount, warnings], [timeoutcount, timeouts]]