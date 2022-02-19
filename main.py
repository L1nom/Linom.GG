import streamlit as st
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

with open('riot.txt') as f:
   st.download_button('Download Riot Verification', f)

# SUMMONER INFORMATION
st.title("LINOM.GG!")
api_key = st.secrets["RIOT_API_KEY"]
watcher = LolWatcher(api_key)
my_region = 'na1'

# use IGN for control flow
try:
    ign = st.text_input("Enter a summoner name")
    if not ign:
        st.warning("Please enter a name")
        st.stop()
except ApiError as err:
    if err.response.status_code == 404:
        st.warning("Please enter a valid summoner name")
        st.stop()
    else:
        raise

me = watcher.summoner.by_name(my_region, ign)

data_version = watcher.data_dragon.versions_for_region(my_region)
latest_champion_ver = data_version['n']['champion']
latest_icon_ver = data_version['n']['profileicon']
static_champ_list = watcher.data_dragon.champions(latest_champion_ver, False, 'en_US')
static_icon_list = watcher.data_dragon.profile_icons(latest_icon_ver, 'en_US')


# champion icon:   https://ddragon.leagueoflegends.com/cdn/11.17.1/img/champion/Ahri.png
# profile icon:    https://ddragon.leagueoflegends.com/cdn/11.17.1/img/profileicon/1594.png
# champion splash: https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Aatrox_0.jpg


def image_link(image_type, name):
    """
    :param image_type: champion, icon
    :param name: json data name
    :return: formatted url for the image icon
    """

    url = " https://ddragon.leagueoflegends.com/cdn/{}/img/{}/{}.png"
    data_version = watcher.data_dragon.versions_for_region(my_region)
    latest_champion_ver = data_version['n']['champion']
    latest_icon_ver = data_version['n']['profileicon']
    static_icon_list = watcher.data_dragon.profile_icons(latest_icon_ver, 'en_US')
    if image_type == "champion":
        url = ("<img src='https://ddragon.leagueoflegends.com/cdn/{}/img/{}/{}.png'width='40' height='40'>".format(
            latest_champion_ver, "champion", name))
    elif image_type == "icon":
        url = ("https://ddragon.leagueoflegends.com/cdn/{}/img/{}/{}.png".format(latest_icon_ver, "profileicon",
                                                                                 int(name)))
    return url


c1, c2 = st.columns((1, 1))
# separate into summoner info and top played champions
# c1 for summoner info
with c1:
    st.image(data_version['cdn'] + '/' + latest_icon_ver + '/' + 'img/profileicon/' + str(me["profileIconId"]) + '.png',
             width=60)
    st.write(me['name'], "LVL: ", me['summonerLevel'])
    my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])

    ranked_dictionary = {
        "solo": {"rank": "Unranked"},
        "flex": {"rank": "Unranked"}
    }

    for rank in my_ranked_stats:
        if "SOLO" in rank["queueType"]:
            ranked_dictionary["solo"]["rank"] = rank['tier'] + " " + rank['rank']
            ranked_dictionary["solo"]["wins"] = rank["wins"]
            ranked_dictionary["solo"]["loss"] = rank["losses"]
            ranked_dictionary["solo"]["total_games"] = rank["wins"] + rank["losses"]
            ranked_dictionary["solo"]["points"] = rank["leaguePoints"]
            ranked_dictionary["solo"]["wr"] = str(
                round(ranked_dictionary["solo"]["wins"] / ranked_dictionary["solo"]["total_games"] * 100, 1)) + '%'
            if "miniSeries" in rank:
                promos = rank["miniSeries"]["progress"].replace("N", "X")
                ranked_dictionary["solo"]["promos"] = promos
        if "FLEX" in rank["queueType"]:
            ranked_dictionary["flex"]["rank"] = rank['tier'] + " " + rank['rank']
            ranked_dictionary["flex"]["wins"] = rank["wins"]
            ranked_dictionary["flex"]["loss"] = rank["losses"]
            ranked_dictionary["flex"]["total_games"] = rank["wins"] + rank["losses"]
            ranked_dictionary["flex"]["points"] = rank["leaguePoints"]
            ranked_dictionary["flex"]["wr"] = str(
                round(ranked_dictionary["flex"]["wins"] / ranked_dictionary["flex"]["total_games"] * 100, 1)) + '%'
            if "miniSeries" in rank:
                promos = rank["miniSeries"]["progress"].replace("N", "X")
                ranked_dictionary["flex"]["promos"] = promos

    for key, value in ranked_dictionary.items():
        if value["rank"] != "Unranked":
            st.write("{}: {} {}LP | {}W - {}L".format(key.title(), value["rank"], value["points"], value["wins"],
                                                      value["loss"]))
            if "promos" in value.keys():
                st.write(value["promos"])
            st.write("Winrate: {}".format(value["wr"]))
        else:
            st.write(key.title() + ": " + value["rank"])

# c2 for champion mastery info
with c2:
    # st.write(static_champ_list)
    champ_dict = {}
    for key in static_champ_list['data']:
        row = static_champ_list['data'][key]
        champ_dict[row['key']] = row['id']
        # if row['id'] == "MonkeyKing":
        #     champ_dict[row['key']] = "Wukong"
    # add corrections for void champions, fiddlesticks

    mastery = watcher.champion_mastery.by_summoner(my_region, me['id'])
    champion_mastery = []
    for champion in mastery:
        single_champ = {}
        single_champ['Champion'] = champ_dict[str(champion['championId'])]
        if single_champ['Champion'] == 'MonkeyKing':
            single_champ['Champion'] = 'Wukong'
        single_champ['Mastery Level'] = champion['championLevel']
        single_champ['Champion Points'] = champion['championPoints']
        champion_mastery.append(single_champ)

    df_champ_mastery = pd.DataFrame(champion_mastery[0:10])
    df_champ_mastery.index += 1
    champ_icon = []
    try:
        for i in range(10):
            champ_icon.append(image_link('champion', champ_dict[str(mastery[i]['championId'])]))
    except:
        pass
    df_champ_mastery.insert(0, 'Icon', champ_icon)
    st.write(df_champ_mastery.to_html(escape=False), unsafe_allow_html=True)


queue_type = st.selectbox('Queue Type', ['Normal', 'Ranked'])
if not queue_type:
    st.stop()

match_list = watcher.match.matchlist_by_puuid('americas', me['puuid'], type=queue_type.lower())

spell_dict = watcher.data_dragon.summoner_spells(data_version["v"], 'en_US')["data"]
spell_icon = {}
for key, value in spell_dict.items():
    spell_icon[str(value["key"])] = key
print(spell_icon)


for i in range(len(match_list) - 10):
    # columns for showing match data and gold graph
    c3, c4 = st.columns([1, 1])

    match_detail = watcher.match.by_id('americas', match_list[i])

    participants = []
    for row in match_detail['info']['participants']:
        participants_row = {}
        participants_row['Win'] = row['win']
        participants_row["Summoner"] = row["summonerName"]
        participants_row['Icon'] = image_link('champion', row['championName'])
        participants_row['champion'] = row['championName']
        if participants_row['champion'] == 'MonkeyKing':
            participants_row['champion'] = 'Wukong'
        participants_row[
            'Spell1'] = "<img src='https://ddragon.leagueoflegends.com/cdn/{}/img/spell/{}.png''width='40' height='40'>".format(
            latest_icon_ver, spell_icon[str(row['summoner1Id'])])
        participants_row[
            'Spell2'] = "<img src='https://ddragon.leagueoflegends.com/cdn/{}/img/spell/{}.png''width='40' height='40'>".format(
            latest_icon_ver, spell_icon[str(row['summoner2Id'])])
        participants_row['LVL'] = row['champLevel']
        participants_row['K/D/A'] = (str(row['kills']) + "/" + str(row['deaths']) + "/" + str(row['assists']))
        participants_row['DMG'] = row['totalDamageDealt']
        participants_row['Gold'] = row['goldEarned']
        participants.append(participants_row)

    df = pd.DataFrame(participants)

    # match history
    with c3:
        st.subheader("Game {}".format(i + 1) + ": " + match_detail["info"]["gameMode"])
        # st.dataframe(df)
        st.write(df.to_html(escape=False), unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)

    # gold is sorted in n + 1 time intervals, where n is the game time rounded up to minutes, including minute 0
    game_1 = watcher.match.timeline_by_match('americas', match_list[i])
    gold = {}
    for k in range(len(game_1['info']['frames'])):
        gold['{}'.format(k)] = {}
    for value in gold.values():
        for l in range(1, 11):
            value['{}'.format(l)] = 0

    for m in range(len(game_1['info']['frames'])):
        for n in range(1, 11):
            gold['{}'.format(m)]['{}'.format(n)] = game_1['info']['frames'][m]['participantFrames']['{}'.format(n)][
                'totalGold']

    team_1_gold = []
    team_2_gold = []
    for key in gold.keys():
        team1 = 0
        team2 = 0
        for o in range(1, 6):
            team1 += gold[key]['{}'.format(o)]
            team2 += gold[key]['{}'.format(o + 5)]
        team_1_gold.append(team1)
        team_2_gold.append(team2)
    frame_size = [val for val in range(len(team_1_gold))]

    gold_diff = np.array(team_1_gold) - np.array(team_2_gold)

    # gold graph
    with c4:
        st.write("<br>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)

        chart_data = pd.DataFrame(
            zip(team_1_gold, team_2_gold, gold_diff),
            columns=['Team 1', 'Team 2', 'Gold Difference'])

        st.line_chart(chart_data)


