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
        
    async def getnote(self, context, target, type):
        author = getauthor(context)
        if type == self.t_assign:
            countassigners, assignerinfo = await self.sqlm.getnotesbyissuer(target.id, self.t_assign)
            countassignees, assigneeinfo = await self.sqlm.getnotesbytarget(target.id, self.t_assign)
            message = ""
            # Assigners
            if countassigners == 0:
                message += "<@" + str(target.id) + "> doesn't have any parent moderators.\n"
            else:
                message += "<@" + str(target.id) + "> has " + str(countassigners) + " parent moderators:\n"
                for info in assignerinfo:
                    message += "<@" + str(info[0]) + "> - " + str(info[3]) + "\n"
            message += "\n"
            # Assignees (example shoulder-arm)
            if countassignees == 0:
                message += "<@" + str(target.id) + "> doesn't have any child moderators.\n"
            else:
                message += "<@" + str(target.id) + "> has " + str(countassignees) + " child moderators:\n"
                for shoulder in assigneeinfo:
                    message += "**\\| -**<@" + str(shoulder[0]) + "> - " + str(shoulder[3]) + "\n"
                    # Example arm-hand
                    countassigneesarm, assigneeinfoarm = await self.sqlm.getnotesbytarget(shoulder[0], self.t_assign)
                    for arm in assigneeinfoarm:
                        message += "**\\| \\| -**<@" + str(arm[0]) + "> - " + str(arm[3]) + "\n"
                        # Example hand-puppet
                        countassigneeshand, assigneeinfohand = await self.sqlm.getnotesbytarget(arm[0], self.t_assign)
                        for hand in assigneeinfohand:
                            message += "**\\| \\| \\| -**<@" + str(hand[0]) + "> - " + str(hand[3]) + "\n"
                    
                    
            await self.responsem.respond(context, message)
        elif type == self.t_break:
            pass
        return