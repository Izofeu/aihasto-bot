import asyncio
import aiomysql as sqlm
class sqlmanager:
    def __init__(self, cfg):
        # Prepare cfg
        self.cfg = cfg
        self.dbuser = self.cfg.get("dbuser")
        self.dbaddress = self.cfg.get("dbaddress")
        self.dbname = self.cfg.get("dbname")
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
                self.connection = await sqlm.connect(host = self.dbaddress, user = self.dbuser, password = self.dbpassword, db = self.dbname, autocommit=True)
                self.connected = True
            except:
                print("Couldn't connect to database.")
        return
    async def query(self, query):
        await self.condisconnect(0)
        cur = await self.connection.cursor()
        if self.firstRun:
            # Run a create table if not exists query once
            tablequery = (
            "CREATE TABLE IF NOT EXISTS `flooders`" +
            "(" +
            "`id` INT NOT NULL AUTO_INCREMENT," +
            "`account_id` varchar(40) NOT NULL UNIQUE," +
            "`expiration_date` DATETIME NOT NULL," +
            "PRIMARY KEY (id)" +
            ");"
            )
            await cur.execute(tablequery)
            self.firstRun = False
        # Execute our query
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
        query = "DELETE FROM `flooders` WHERE account_id = " + str(id) + ";"
        await self.query(query)
        query = (
        "INSERT INTO `flooders` (`account_id`, `expiration_date`) VALUES (" +
        str(id) + ", '" + str(duration) + "'"
        ");"
        )
        await self.query(query)
        return
    async def getexpiredflooders(self, currentdate):
        # Get all expired flooders
        query = "SELECT account_id FROM flooders WHERE expiration_date < '" + currentdate + "';"
        result = await self.query(query)
        return result
    async def removeflooder(self, id):
        # Remove a flooder record from the database
        query = "DELETE FROM `flooders` WHERE account_id = " + str(id) + ";"
        await self.query(query)
        return