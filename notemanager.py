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
        
    async def assign(self, context, issuerid, targetid, type, reason = False):
        issuedate = getdatefordb()
        timestamp = getutctimestamp()
        reason = isemptyreason(reason)
        if type == self.assignnote:
            await self.sqlm.addnote_nodate(issuerid, targetid, self.t_assign, reason)
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
        rootinfo = await self.sqlm.getroot(self.t_assign)
        message = ""
        for root in rootinfo:
            message += "<@" + str(root[0]) + ">:\n"
            countassignees, assigneeinfo = await self.sqlm.getnotesbytarget(root[0], self.t_assign)
            for shoulder in assigneeinfo:
                message += "🟥<@" + str(shoulder[0]) + ">\n"
                # Example arm-hand
                countassigneesarm, assigneeinfoarm = await self.sqlm.getnotesbytarget(shoulder[0], self.t_assign)
                for arm in assigneeinfoarm:
                    message += "🟥🟩<@" + str(arm[0]) + ">\n"
                    # Example hand-puppet
                    countassigneeshand, assigneeinfohand = await self.sqlm.getnotesbytarget(arm[0], self.t_assign)
                    for hand in assigneeinfohand:
                        message += "🟥🟩🟦<@" + str(hand[0]) + ">\n"
            message += "\n"
        if not message:
            message = "No tree to display."
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
                    message += "<@" + str(info[0]) + ">"
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