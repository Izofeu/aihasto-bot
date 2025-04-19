from extrafunctions import getdatefordb, getutctimestamp, isemptyreason, getauthor

class notemanager:
    def __init__(self, cfg, sql, responsemanager, logmanager):
        self.cfg = cfg
        self.sqlm = sql
        self.responsem = responsemanager
        self.logm = logmanager
        # Modes
        self.assignnote = 1
        self.unassignnote = 2
        self.breaknote = 3
        
        # Types
        self.t_assign = 1
        self.t_break = 2
        
        self.alldata = None
        
    async def assign(self, context, issuerid, targetid, type, reason = False, root = False):
        issuedate = getdatefordb()
        timestamp = getutctimestamp()
        reason = isemptyreason(reason)
        if type == self.assignnote:
            await self.sqlm.addnote_nodate(issuerid, targetid, self.t_assign, reason, root)
            await self.responsem.respond(context, "Assigned <@" + str(targetid) + "> to <@" + str(issuerid) + ">.")
            await self.logm.sendlog(self.logm.assignments, context, target = targetid, reason = reason, altauthor = issuerid)
        elif type == self.unassignnote:
            await self.sqlm.removenote(issuerid, targetid, self.t_assign)
            await self.responsem.respond(context, "Removed <@" + str(targetid) + "> from <@" + str(issuerid) + ">.")
            await self.logm.sendlog(self.logm.assignments, context, mode = self.logm.removeassignments, target = targetid, reason = reason, altauthor = issuerid)
        elif type == self.breaknote:
            pass
        return
    
    async def generatetree(self, context):
        def getfromalldata(userid):
            array = []
            for id in self.alldata:
                #[0] - account_id
                #[1] - issuer_id
                if str(id[0]) == str(userid):
                    array.append(id[1])
            return array
        async def addtomessage(message, append):
            if (len(message) + len(append)) > 1200:
                await self.responsem.respond(context, message)
                return append
            return message + append
        async def recursiontree(userid, message, depth = 1):
            if depth > 6:
                return message
            assigneeinfo = getfromalldata(userid)
            emojis = "🟥🟩🟦🟨🟪⬛"
            for assignees in assigneeinfo:
                message = await addtomessage(message, (emojis[:depth] + "<@" + str(assignees) + ">\n"))
                message = await recursiontree(assignees, message, (depth + 1))
            return message
        rootinfo = await self.sqlm.getroot(self.t_assign)
        message = ""
        self.alldata = await self.sqlm.getallassigns(self.t_assign)
        for root in rootinfo:
            message += "\n<@" + str(root[0]) + ">:\n"
            message = await recursiontree(root[0], message)
        if not message:
            message = "No tree to display (no root assigns)."
        self.alldata = None
        await self.responsem.respond(context, message)
        return
    
    async def getnote(self, context, targetid, type):
        author = getauthor(context)
        if type == self.t_assign:
            countassigners, assignerinfo = await self.sqlm.getnotesbyissuer(targetid, self.t_assign)
            countassignees, assigneeinfo = await self.sqlm.getnotesbytarget(targetid, self.t_assign)
            message = ""
            # Assigners
            if countassigners == 0:
                message += "<@" + str(targetid) + "> doesn't have any parent moderators.\n"
            else:
                message += "<@" + str(targetid) + "> has " + str(countassigners) + " parent moderators:\n"
                for info in assignerinfo:
                    message += "<@" + str(info[0]) + "> assigned the following tasks to <@" + str(targetid) + ">: " + str(info[3]) + "\n"
            message += "\n"
            # Assignees (example shoulder-arm)
            if countassignees == 0:
                message += "<@" + str(targetid) + "> doesn't have any child moderators.\n"
            else:
                message += "<@" + str(targetid) + "> has " + str(countassignees) + " child moderators:\n"
                for shoulder in assigneeinfo:
                    message += "<@" + str(shoulder[0]) + "> - " + str(shoulder[3]) + "\n"

            await self.responsem.respond(context, message)
        elif type == self.t_break:
            pass
        return