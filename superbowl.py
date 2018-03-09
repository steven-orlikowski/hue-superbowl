import urllib2
import operator
import time
import requests
import json

# LEAGE STRINGS
NCAA_FB = 'ncf'
NFL = 'nfl'
MLB = 'mlb'
NBA = 'nba'
NHL = 'nhl'
NCAA_BB = 'mens-college-basketball'

my_league = NFL

team_1 = 'New England' #Patriots
team_2 = 'Atlanta' #Falcons
team_tie = 'tie'
bridge_ip = '127.0.0.1'
api_key = 'steven'
bulb_0_id = '1'
bulb_1_id = '2'
bulb_hues = {team_1: [0,25500], team_2: [46920,46920], team_tie : [25500,25500]}
bulb_0_state_url = 'http://' + bridge_ip + '/api/' + api_key + '/lights/' + bulb_0_id + '/state'
bulb_1_state_url = 'http://' + bridge_ip + '/api/' + api_key + '/lights/' + bulb_1_id + '/state'
blink_seconds = .25
blink_number = 3
seconds_between_espn_requests = 5

#todo: not sure if the tag in requests.post should be json= or data=

def lights_off():
    print 'Lights off ', bulb_0_state_url
    r = requests.post(bulb_0_state_url, json={"on":False})
    print r.status_code, r.reason
    print 'Lights off ', bulb_1_state_url
    r = requests.post(bulb_1_state_url, json={"on":False})
    print r.status_code, r.reason

def lights_on(team):
    my_hue = bulb_hues[team][0]
    print 'Lights on hue ', team, ' ', my_hue, bulb_0_state_url
    r = requests.post(bulb_0_state_url, json={"on":True, "sat":254, "bri":254, "hue":my_hue})
    print r.status_code, r.reason
    my_hue = bulb_hues[team][1]
    print 'Lights on hue ', team, ' ', my_hue, bulb_1_state_url
    r = requests.post(bulb_1_state_url, json={"on":True, "sat":254, "bri":254, "hue":my_hue})
    print r.status_code, r.reason

def lights_blink(team):
    print 'Blink lights for ', team
    for i in range(0, blink_number):
        lights_on(team)
        time.sleep(blink_seconds)
        lights_off()
        time.sleep(blink_seconds)

def get_light_info():
    get_lights_url = 'http://' + bridge_ip + '/api/' + api_key + '/lights'
    while True:
        print 'Getting lights info: ', get_lights_url
        r = requests.get(get_lights_url)
        print r.status_code, r.reason
        print r.text
        time.sleep(10)

def get_scores(league, team_filter=None):
    scores = []
    STRIP = "()1234567890 "
    if team_filter:
        team_filter = team_filter.lower().split(', ')

    try:
        # visit espn bottomline website to get scores as html page
        url = 'http://sports.espn.go.com/' + league + '/bottomline/scores'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        page = response.read()

        # url decode the page and split into list
        data = urllib2.unquote(str(page)).split('&' + league + '_s_left')

        for i in range(1, len(data)):

            # get rid of junk at beginning of line, remove ^ which marks team with ball
            main_str = data[i][data[i].find('=') + 1:].replace('^', '')

            # extract time, you can use the ( and ) to find time in string
            time = main_str[main_str.rfind('('):main_str.rfind(')') + 1].strip()

            # extract score, it should be at start of line and go to the first (
            score = main_str[0:main_str.rfind('(')].strip()

            # extract espn gameID use the keyword gameId to find it
            gameID = main_str[main_str.rfind('gameId') + 7:].strip()

            if gameID == '':
                # something wrong happened
                continue

            # split score string into each teams string
            team1_name = ''
            team1_score = '0'
            team2_name = ''
            team2_score = '0'

            if (' at ' not in score):
                teams = score.split('  ')
                team1_name = teams[0][0:teams[0].rfind(' ')].lstrip(STRIP)
                team2_name = teams[1][0:teams[1].rfind(' ')].lstrip(STRIP)
                team1_score = teams[0][teams[0].rfind(' ') + 1:].strip()
                team2_score = teams[1][teams[1].rfind(' ') + 1:].strip()
            else:
                teams = score.split(' at ')
                team1_name = teams[0].lstrip(STRIP)
                team2_name = teams[1].lstrip(STRIP)

            # add to return dictionary
            if (not team_filter) or (team1_name.lower() in team_filter or team2_name.lower() in team_filter):
                scores.append({team1_name : int(team1_score) , team2_name : int(team2_score)})

    except Exception as e:
        # print(str(e))
        raise e

    return scores


def light_test():
    print "Testing lights for ", team_1
    lights_blink(team_1)
    print "Testing lights for ", team_2
    lights_blink(team_2)
    print "Testing lights for ", team_tie
    lights_blink(team_tie)


def game_loop():
    score = {team_1:0, team_2:0}
    first_run = True
    # Set initial lights state (tie)
    lights_on(team_tie)
    while True:
        # Get all the scores
        new_scores = get_scores(my_league, team_1)
        if len(new_scores) > 0:
            now = time.strftime("%c")
            print now
            # Get current score from ESPN
            new_score = new_scores[0]
            print new_score
            # If the score has changed, blink the lights accordingly
            if new_score != score:
                #Don't blink if the game has already started when we start the script
                if first_run == False:
                    # Blink lights if a team scored
                    if new_score[team_1] > score[team_1]:
                        print team_1, ' scored. Blink lights.'
                        lights_blink(team_1)
                    if new_score[team_2] > score[team_2]:
                        print team_2, ' scored. Blink lights.'
                        lights_blink(team_2)
                first_run = False
                # Get the winning team
                winning_team = ''
                if new_score[team_1] == new_score[team_2]:
                    winning_team = team_tie
                    print 'game is tied'
                else:
                    winning_team = max(new_score.iteritems(), key=operator.itemgetter(1))[0]
                    print winning_team, " is winning"
                #Set lights for winning team
                lights_on(winning_team)
                # Set new score
                score = new_score
        else:
            print 'Game not found'
        # Sleep before the next request
        time.sleep(seconds_between_espn_requests)




if __name__ == '__main__':
    #light_test()
    #get_light_info()
    game_loop()




