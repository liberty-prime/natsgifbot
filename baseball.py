from discord.ext import commands

from urllib.request import urlopen, Request
import urllib.parse
from datetime import datetime, timedelta, time, date

import mymlbstats
from bs4 import BeautifulSoup

class Baseball():
    def __init__(self,bot):
        self.bot = bot
        
    @commands.command()
    async def br(self, *query:str):
        """get link to a player's Baseball-Reference page"""
        url = "http://www.baseball-reference.com/search/search.fcgi?search=%s&results=" % urllib.parse.quote_plus(' '.join(query))
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        res = urlopen(req)
        await self.bot.say(res.url)
        
    @commands.command()
    async def fg(self, *query:str):
        """get a link to a player's Fangraphs page"""
        url = "http://www.fangraphs.com/players.aspx?lastname=%s" % urllib.parse.quote_plus(' '.join(query))
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        res = urlopen(req)
        await self.bot.say("<"+res.url+">")#disable embed because it's shit

    def convert_date_to_delta(self, args):
        now = datetime.now().date()
        datelist = args[-1].split('/')
        if len(datelist[2]) == 2:
            if int("20" + datelist[2]) <= now.year:
                datelist[2] = "20" + datelist[2]
            else:
                datelist[2] = "19" + datelist[2]
        other = date(int(datelist[2]), int(datelist[0]), int(datelist[1]))
        delta = other - now
        direction = ''
        if delta.days > 0:
            direction = '+'
        return direction + str(delta.days)

    @commands.command()
    async def mlb(self,*team :str):
        """Get MLB info

        Help is now too long for a discord message. Check the github link for full help.

        Supported sub commands:
        blank
        <team>
        <division>
        standings <division>
        [l]sp <team>
        line <player>
        ohtani
        <part> <team>
        linescore <team>

            each of the previous commands can end in a number of (+days or -days) to change the date

        dl <team>
        batters <team>
        pitchers <team>

        last [n] <team>
        next [n] <team>

        [h][c][b,p]stats <player> [year] [year2]
        splits <split> <player> [year]
        vs <team> <player>
        [b]last <player> [n]
        [b]log [n] <player>
        [p,f]leaders <stat>

        highlight <query>

        help - https://github.com/efitz11/natsgifbot/blob/master/mlbhelp.txt
        """
        delta=None

        team = ["wsh" if x.lower() == "nats" else x for x in team]

        reddit = False
        for i in team:
            if i.lower() == 'reddit':
                reddit = True
                team.remove(i)

        if len(team) > 0 and (team[-1].startswith('-') or team[-1].startswith('+')):
            delta = team[-1]
            team = team[:-1]

        if len(team) > 0 and len(team[-1].split('/')) == 3:
            delta = self.convert_date_to_delta(team)
            team = team[:-1]

        if len(team) == 0 or (len(team) == 1 and team[0] == 'live'):
            liveonly=False
            if len(team) == 1:
                liveonly = True
            output = mymlbstats.get_all_game_info(delta=delta, liveonly=liveonly)
            await self.bot.say("```python\n" + output + "```")
            return

        if team[0] == 'help':
            await self.bot.say("https://github.com/efitz11/natsgifbot/blob/master/mlbhelp.txt")
            return

        if team[0] in ["sp","lsp"]:
            teamname = ' '.join(team[1:])
            if team[0] == "lsp":
                scoring_plays = mymlbstats.list_scoring_plays(teamname, delta,lastonly=True)
            else:
                scoring_plays = mymlbstats.list_scoring_plays(teamname, delta)
            print(teamname,scoring_plays)
            if len(scoring_plays) > 0:
                output = "```"
                lastinning = ""
                for play in scoring_plays:
                    if play[0] != lastinning:
                        if len(lastinning) != 0:
                            output = output + "```\n```"
                            if len(output) + len(play[0]) > 1600:
                                await self.bot.say(output[:-3])
                                output = "```"
                        output = output + play[0] + "\n"
                        lastinning = play[0]
                    output = output + "\t" + play[1] + "\n"
                output = output + "```"
                await self.bot.say(output)
                return
            else:
                await self.bot.say("No scoring plays")
                return
        elif team[0] == 'line':
            player = '+'.join(team[1:])
            if len(player) == 0:
                out = get_daily_leaders(delta=delta)
                await self.bot.say("ESPN's daily leaders:\n```%s```"% out)
                return
            else:
                out = mymlbstats.get_player_line(player, delta)
            if len(out) == 0:
                await self.bot.say("couldn't find stats")
            else:
                await self.bot.say("```%s```" % out)
            return
        # elif team[0] in ['stats','bstats','pstats','hstats','hbstats','hpstats']:
        elif team[0].endswith('stats'):
            active = 'Y'
            if team[0].startswith('h'):
                team[0] = team[0][1:]
                active = 'N'
            career = False
            if team[0].startswith('c'):
                team[0] = team[0][1:]
                career = True
            year = None
            year2 = None
            if team[-1].isdigit():
                year = team[-1]
                team = team[0:-1]
            if team[-1].isdigit():
                year2 = year
                year = team[-1]
                team = team[0:-1]
            player = '+'.join(team[1:])
            t = None
            if team[0] in ['bstats']:
                t = "hitting"
            elif team[0] == 'pstats':
                t = "pitching"
            await self.bot.say("```%s```" % mymlbstats.get_player_season_stats(player,type=t,year=year,year2=year2,active=active, career=career, reddit=reddit))
            return
        elif team[0] == 'compare':
            year = None
            if team[-1].isdigit():
                year = team[-1]
                team = team[0:-1]
            team = team[1:]
            playerlist = []
            for t in team:
                playerlist.append(t)
            if year is None:
                await self.bot.say("```%s```" % mymlbstats.compare_player_stats(playerlist))
            else:
                await self.bot.say("```%s```" % mymlbstats.compare_player_stats(playerlist, year=year))
        elif team[0] == 'splits':
            split = team[1]
            if team[-1].isdigit():
                year = team[-1]
                player = ' '.join(team[2:-1])
                await self.bot.say("```%s```" % mymlbstats.get_player_season_splits(player,split,year=year))
            else:
                player = ' '.join(team[2:])
                await self.bot.say("```%s```" % mymlbstats.get_player_season_splits(player,split))
            return
        elif team[0] == 'vs':
            opp = team[1]
            year = None
            if team[-1].isdigit():
                year = team[-1]
                team = team[0:-1]
            #     player = ' '.join(team[2:-1])
            #     await self.bot.say("```%s```" % mymlbstats.player_vs_team(player,opp,year=year))
            # else:
            player = ' '.join(team[2:])
            # await self.bot.say("```%s```" % mymlbstats.player_vs_team(player,opp))
            await self.bot.say("```%s```" % mymlbstats.batter_or_pitcher_vs(player,opp,year=year,reddit=reddit))
            return
        elif team[0].lower() == "dl":
            team = ' '.join(team[1:])
            await self.bot.say("```%s```" % mymlbstats.get_team_dl(team))
            return
        elif team[0] in ['batters','pitchers']:
            h = (team[0] == 'batters')
            team = ' '.join(team[1:])
            await self.bot.say("```%s```" % mymlbstats.print_roster(team, hitters=h))
        elif team[0] in ['past', 'next']:
            num = 2
            backwards = team[0] == 'past'
            if team[1].isdigit():
                num = int(team[1])
                team = ' '.join(team[2:])
            else:
                team = ' '.join(team[1:])
            await self.bot.say("```%s```" % mymlbstats.get_team_schedule(team,num,backward=backwards))
            return
        elif team[0].startswith("last") or team[0].startswith("blast"):
            forcebatting = False
            if team[0].startswith('blast'):
                team[0] = team[0][1:]
                forcebatting = True
            if team[1].isdigit():
                days = int(team[1])
                team = team[2:]
            else:
                team = team[1:]
                days = None
            await self.bot.say("```%s```" % mymlbstats.get_player_trailing_splits('+'.join(team), days, forcebatting=forcebatting))
            return
        elif team[0].endswith("log"):
            forcebatting = team[0].startswith("b")
            if team[-1].isdigit():
                num = int(team[-1])
                team = team[:-1]
            else:
                num=5
            player = '+'.join(team[1:])
            await self.bot.say("```%s```" % mymlbstats.get_player_gamelogs(player,num,forcebatting=forcebatting))
            return
        elif team[0].endswith("leaders") or team[0].endswith("losers"):
            stat = team[1]
            opts = []
            for i in range(2,len(team)):
                opts.append(team[i])
            stattype = 'bat'
            if team[0].startswith('p'):
                t = team[0][1:]
                stattype = 'pit'
            elif team[0].startswith('f'):
                t = team[0][1:]
                stattype = 'fld'
            else:
                t = team[0]
            if t == "losers":
                opts.append("reverse=yes")
            fg = FG(stat.lower(),options=opts)
            output = fg.get_stat_leaders_str(stattype=stattype)
            await self.bot.say(output)
            return
        elif team[0] == 'ohtani':
            out = mymlbstats.get_ohtani_line(delta)
            if len(out) > 0:
                await self.bot.say("```%s```" % out)
            else:
                await self.bot.say("No stats found")
            return
        elif team[0] in ['batting','pitching','notes','info','bench','bullpen']:
            part = team[0]
            team = ' '.join(team[1:]).lower()
            out = mymlbstats.print_box(team, part=part, delta=delta)
            if out is not None:
                await self.bot.say("```%s```" % out)
            return
        elif team[0] == "linescore":
            team = ' '.join(team[1:]).lower()
            out = mymlbstats.print_linescore(team, delta=delta)
            await self.bot.say("```%s```" % out)
            return
        elif team[0] == "highlight":
            query = ' '.join(team[1:])
            await self.bot.say(mymlbstats.search_highlights(query))
            return
        elif team[0] == "plays":
            inning = int(team[-1])
            team = ' '.join(team[1:-1]).lower()
            await self.bot.say(mymlbstats.get_inning_plays(team, inning, delta=delta))
        elif team[0] == "standings":
            div = team[1]
            await self.bot.say(mymlbstats.get_div_standings(div))
        else:
            teamname = ' '.join(team).lower()
            output = mymlbstats.get_single_game(teamname,delta=delta)
            if len(output) > 0:
                await self.bot.say("```python\n" + output + "```")
            else:
                await self.bot.say("no games found")

    #######################################
    ##### BEGIN MINOR LEAGUE COMMANDS #####
    #######################################

    def _find_delta(self, args):
        delta = None
        if len(args) > 0 and (args[-1].startswith('-') or args[-1].startswith('+')):
            delta = args[-1]
            args = args[:-1]

        if len(args) > 0 and len(args[-1].split('/')) == 3:
            delta = self.convert_date_to_delta(args)
            args = args[:-1]
        return delta, args

    @commands.group(pass_context=True)
    async def milb(self, ctx):
        """Get info on minor leagues
        !milb [team] [date or delta] - print scoreboard for [team] affiliates, defaults to Nats
                date/delta optional - date is MM/DD/[YY]YY format, delta is +days or -days
        """
        if ctx.invoked_subcommand is None:
            args = ctx.message.system_content[6:].split(' ')
            delta, args = self._find_delta(args)

            if args[0] == '':
                await self.bot.say("```python\n%s```" % mymlbstats.get_milb_aff_scores(delta=delta))
            else:
                teamid = mymlbstats.get_teamid(' '.join(args))
                if teamid is None:
                    await self.bot.say('Invalid subcommand passed')
                else:
                    await self.bot.say("```python\n%s```" % mymlbstats.get_milb_aff_scores(teamid=teamid, delta=delta))

    @milb.command()
    async def stats(self, *query:str):
        """get a minor league player's stats
        !milb stats <player> [year] - year is optional, defaults to current"""
        if query[-1].isdigit():
            year = query[-1]
            player = ' '.join(query[:-1])
            await self.bot.say("```%s```" % mymlbstats.get_milb_season_stats(player,year=year))
        else:
            player = ' '.join(query)
            await self.bot.say("```%s```" % mymlbstats.get_milb_season_stats(player))

    @milb.command()
    async def log(self, *query:str):
        """get a minor league player's game logs
        !milb log <player> [num] - num defaults to last 5 games, maximum of 15"""
        if query[-1].isdigit():
            num = query[-1]
            player = ' '.join(query[:-1])
            await self.bot.say("```%s```" % mymlbstats.get_milb_log(player,number=num))
        else:
            player = ' '.join(query)
            await self.bot.say("```%s```" % mymlbstats.get_milb_log(player))

    @milb.command()
    async def batting(self, *query:str):
        """print minor league team batting box score
        !milb batting <team> - prints the team's batting part of the box score
        """
        delta, query = self._find_delta(query)
        team = ' '.join(query)
        await self.bot.say("```%s```" % mymlbstats.get_milb_box(team))

    @milb.command()
    async def pitching(self, *query:str):
        """print minor league team pitching box score
        !milb pitching <team> - prints the team's pitching part of the box score
        """
        delta, query = self._find_delta(query)
        team = ' '.join(query)
        await self.bot.say("```%s```" % mymlbstats.get_milb_box(team,part='pitching'))

    @milb.command()
    async def notes(self, *query:str):
        """print minor league team batting notes
        !milb pitching <team> - prints the team's batting notes from the box score
        """
        delta, query = self._find_delta(query)
        team = ' '.join(query)
        await self.bot.say("```%s```" % mymlbstats.get_milb_box(team,part='notes'))

def setup(bot):
    bot.add_cog(Baseball(bot))

class FG:
    bdash = ['bb%','k%','iso','babip','avg','obp','slg','woba','wrc+','bsr','off','def','fwar',9]
    bstd = ['g','ab','pa','h','1b','2b','3b','hr','r','rbi','bb','ibb','so','hbp','sf','sh','gdp','sb','cs',3]
    badv = ['ops','iso','spd','babip','ubr','wgdp','wsb','wrc','wraa',10]
    batting = [bdash,bstd,badv]
    pdash = ['w','l','sv','g','gs','ip','k/9','bb/9','hr/9','babip','lob%','gb%','hr/fb','era','fip','xfip','fwar',3]
    pstd = ['w','l','era','g','gs','cg','sho','sv','hld','bs','ip','tbf','h','r','er','hr','bb','ibb','hbp','wp','bk','so',3]
    padv = ['k/9','bb/9','k/bb','hr/9','k%','bb%','k-bb%','avg','whip','babip','lob%','era-','fip-','xfip-','era','fip','e-f','xfip','siera',3]
    pitching = [pdash,pstd,padv]
    fstd = ['po','a','e','fe','te','dp','dps','dpt','dpf','scp','sb','cs','pb','wp','fp',7]
    fadv = ['drs','biz','plays','rzr','ooz','cpp','rpp','tzl','fsr','arm','dpr','rngr','errr','uzr','uzr/150','def',10]
    fielding = [fstd,fadv]

    asec = ['era','fip','xfip','whip','era-','fip-','xfip-','babip']
    count = ['bsr','off','def','fwar','g','ab','pa','h','1b','2b','3b','hr','r','rbi','bb','ibb','so','hbp','sf','sh','gdp','sb','cs',
             'w','l','sv','g','gs','ip','fwar','cg','sho','sv','hld','bs','tbf','wp','bk',
             'po','a','e','fe','te','dp','pb','drs']

    baseurl = "https://www.fangraphs.com/leaders.aspx?"

    teams = {'angels':1,'astros':21,'athletics':10,'bluejays':14,'braves':16,'brewers':23,'cardinals':28,
             'cubs':17,'diamondbacks':15,'dodgers':22,'giants':30,'indians':5,'mariners':11,'marlins':20,
             'mets':25,'nationals':24,'orioles':2,'padres':29,'phillies':26,'pirates':27,'rangers':13,
             'rays':12,'redsox':3,'reds':18,'rockies':19,'royals':7,'tigers':6,'twins':8,'whitesox':4,
             'yankees':9,
             'laa':1,'hou':21,'oak':10,'tor':14,'atl':16,'mil':23,'stl':28,
             'chc':17,'ari':15,'lad':22,'sf':30,'cle':5,'sea':11,'mia':20,
             'nym':25,'wsh':24,'bal':2,'sd':29,'phi':26,'pit':27,'tex':13,
             'tb':12,'bos':3,'cin':18,'col':19,'kc':7,'det':6,'min':8,'cws':4,'nyy':9}

    def __init__(self, stat, options=[]):
        self.stat = stat
        self.options = options
        self.order = ['d','a']
        self.delta = 0

    def _get_options_str(self):
        # set defaults
        pos = 'all'
        lg = 'all'
        qual = 'y'
        season = '2018'
        team = '0'
        month='33'
        if self.stat in self.count:
            qual = '0'

        for s in self.options:
            if '=' in s:
                t = s.split('=')
                opt = t[0].lower()
                val = t[1].lower()
                if opt == 'pos':
                    pos = val
                elif opt == 'lg':
                    lg = val
                elif opt == 'qual':
                    qual = val
                elif opt == 'season':
                    if month == '33':
                        month='0'
                    season = val
                elif opt == 'split':
                    if val == 'last7':
                        month='1'
                    elif val == 'last14':
                        month='2'
                    elif val == 'last30':
                        month='3'
                    # elif val == 'risp':
                    #     month='29'
                    # elif val == 'vl':
                    #     month='13'
                    # elif val == 'vr':
                    #     month='14'
                elif opt == 'team':
                    if val in self.teams:
                        team = str(self.teams[val])
                    else:
                        team = val
                    self.delta = 1
                elif opt == 'reverse':
                    self.order = ['a','d']
        return "pos=%s&lg=%s&qual=%s&season=%s&month=%s&team=%s" % (pos,lg,qual,season,month,team)

    def get_stat(self, stattype='bat'):
        #parse options
        optstr = self._get_options_str()
        url = self.baseurl + optstr + "&stats="+stattype
        if stattype == 'bat':
            list = self.batting
        elif stattype == 'pit':
            list = self.pitching
        elif stattype == 'fld':
            list = self.fielding
        count = -1
        if stattype == 'fld':
            count = 0
        found = False
        for l in list:
            if self.stat in l:
                found = True
                if count == -1:
                    count = 8
                index = l.index(self.stat) + l[-1] - self.delta
                order = self.order[0]
                if self.stat in self.asec:
                    order = self.order[1]
                url = url + "&type=%d&sort=%d,%s" % (count,index, order)
                break
            count += 1
        if not found:
            return "No matching stat"
        print(url)
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        s = urlopen(req).read().decode('utf-8')
        srchstr = "<table class=\"rgMasterTable\""
        endstr = "</table>"
        s = s[s.find(srchstr)+len(srchstr):]
        s = s[:s.find(endstr)+len(endstr)]
        soup = BeautifulSoup(s,'html.parser')
        list = []
        headers = soup.find_all("th", class_="rgHeader")
        row = []
        for h in headers:
            row.append(h.get_text())
        list.append((row[1],row[2],row[index]))
        rows = soup.find_all("tr", {'class':['rgRow','rgAltRow']})
        for r in rows:
            cells = r.find_all('td')
            row = []
            for c in cells:
                row.append(c.get_text())
            list.append((row[1],row[2],row[index]))
        return list

    def get_stat_leaders_str(self, length=10, stattype='bat'):
        list = self.get_stat(stattype=stattype)
        if list == "No matching stat":
            return "```%s```" % list
        output = "```"
        length = min(length + 1, len(list))
        print(length)
        for i in range(length): #+1 to include title row
            l = list[i]
            if len(l[2].strip()) == 0:
                continue
            output = output + l[0].ljust(20) + l[2].rjust(5) + "\n"
        output = output + "```"
        return output

def get_daily_leaders(delta=None):
    url = "http://www.espn.com/mlb/stats/dailyleaders"
    if delta != None:
        delta = int(delta)
        day = datetime.now() + timedelta(days=delta)
        url = url + "/_/date/%d%02d%02d" % (day.year, day.month, day.day)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = urlopen(req).read().decode('latin-1')
    soup = BeautifulSoup(s, 'html.parser')
    table = soup.find_all("table", class_="tablehead")[1]
    # print(table)
    rows = table.find_all("tr")
    output = ""
    count = 0
    for r in rows:
        if count > 1 and count < 12:
            cells = r.find_all('td')
            player = cells[1].get_text().ljust(20)
            team = cells[2].get_text().ljust(4)
            stats = cells[5].get_text()
            output = output + "%s %s %s\n" % (team, player, stats)
        count += 1
    return output

if __name__ == "__main__":
    # fg = FG('fwar')
    # print(fg.get_stat_leaders_str())
    print(get_daily_leaders(delta="-1"))
