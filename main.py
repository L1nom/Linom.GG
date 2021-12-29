import streamlit as st
from riotwatcher import LolWatcher, ApiError
import pandas as pd
from apikey import RIOT_API_KEY
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
# SUMMONER INFORMATION
st.title("LINOM.GG!")
# add_selectbox = st.sidebar.selectbox(
#     "How would you like to be contacted?",
#     ("Email", "Home phone", "Mobile phone")
# )
# global variables
# create your own python file and enter your own riot api key
api_key = RIOT_API_KEY

watcher = LolWatcher(api_key)
my_region = 'na1'

# use IGN for control flow
ign = st.text_input("Enter your league name")
if not ign:
    st.warning("Please enter a name")
    st.stop()
me = watcher.summoner.by_name(my_region, ign)
# st.write(me)
# st.write('test')

# Lets get some champions static information
data_version = watcher.data_dragon.versions_for_region(my_region)
latest_champion_ver = data_version['n']['champion']
latest_icon_ver = data_version['n']['profileicon']
static_champ_list = watcher.data_dragon.champions(latest_champion_ver, False, 'en_US')
static_icon_list = watcher.data_dragon.profile_icons(latest_icon_ver, 'en_US')
# st.write(data_version)

# st.write(static_champ_list['data']['Aatrox'])  # test for champion data
# profile icon in png champion splash is jpg
# need function for image links later on

# Display some user statistics
# st.write('<img src="https://ddragon.leagueoflegends.com/cdn/11.17.1/img/champion/Aatrox.png" width="40" height="40">', unsafe_allow_html=True)

# champion icon:   https://ddragon.leagueoflegends.com/cdn/11.17.1/img/champion/Ahri.png
# profile icon:    https://ddragon.leagueoflegends.com/cdn/11.17.1/img/profileicon/1594.png
# champion splash: https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Aatrox_0.jpg


def image_link(image_type, name):
    url = " https://ddragon.leagueoflegends.com/cdn/{}/img/{}/{}.png"
    data_version = watcher.data_dragon.versions_for_region(my_region)
    latest_champion_ver = data_version['n']['champion']
    latest_icon_ver = data_version['n']['profileicon']
    static_icon_list = watcher.data_dragon.profile_icons(latest_icon_ver, 'en_US')
    if image_type == "champion":
        url = ("<img src='https://ddragon.leagueoflegends.com/cdn/{}/img/{}/{}.png'width='40' height='40'>".format(latest_champion_ver, "champion", name))
    elif image_type == "icon":
        url = ("https://ddragon.leagueoflegends.com/cdn/{}/img/{}/{}.png".format(latest_icon_ver, "profileicon", int(name)))
    return url

c1, c2 = st.columns((1, 1))
with c1:
    st.image(data_version['cdn'] + '/' + latest_icon_ver + '/' + 'img/profileicon/' + str(me["profileIconId"]) + '.png', width=60)
    st.write(me['name'], "LVL: ", me['summonerLevel'])
    my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])
    # st.write(my_ranked_stats)

    ranked_dictionary = {
        "solo": {"rank": "Unranked"},
        "flex": {"rank": "Unranked"}
    }
    # USE DICTIONARY
    # solo_wr = "N/A"
    # flex_wr = "N/A"
    # solo_rank = "Unranked"
    # flex_rank = "Unranked"
    for rank in my_ranked_stats:
        if "SOLO" in rank["queueType"]:
            ranked_dictionary["solo"]["rank"] = rank['tier'] + " " + rank['rank']
            ranked_dictionary["solo"]["wins"] = rank["wins"]
            ranked_dictionary["solo"]["loss"] = rank["losses"]
            ranked_dictionary["solo"]["total_games"] = rank["wins"] + rank["losses"]
            ranked_dictionary["solo"]["points"] = rank["leaguePoints"]
            ranked_dictionary["solo"]["wr"] = str(round(ranked_dictionary["solo"]["wins"] / ranked_dictionary["solo"]["total_games"] * 100, 1)) + '%'
            if "miniSeries" in rank:
                promos = rank["miniSeries"]["progress"].replace("N", "X")
                ranked_dictionary["solo"]["promos"] = promos
        if "FLEX" in rank["queueType"]:
            ranked_dictionary["flex"]["rank"] = rank['tier'] + " " + rank['rank']
            ranked_dictionary["flex"]["wins"] = rank["wins"]
            ranked_dictionary["flex"]["loss"] = rank["losses"]
            ranked_dictionary["flex"]["total_games"] = rank["wins"] + rank["losses"]
            ranked_dictionary["flex"]["points"] = rank["leaguePoints"]
            ranked_dictionary["flex"]["wr"] = str(round(ranked_dictionary["flex"]["wins"] / ranked_dictionary["flex"]["total_games"] * 100, 1)) + '%'
            if "miniSeries" in rank:
                promos = rank["miniSeries"]["progress"].replace("N", "X")
                ranked_dictionary["flex"]["promos"] = promos
    # st.write(ranked_dictionary)
    for key, value in ranked_dictionary.items():
        if value["rank"] != "Unranked":
            st.write("{}: {} {}LP | {}W - {}L".format(key.title(), value["rank"], value["points"], value["wins"], value["loss"]))
            if "promos" in value.keys():
                st.write(value["promos"])
            st.write("Winrate: {}".format(value["wr"]))
        else:
            st.write(key.title() + ": " + value["rank"])

# ----------------------------------------------------------------------------------------------------------------------
# CHAMPION MASTERY
with c2:
    # st.write(static_champ_list)
    champ_dict = {}
    for key in static_champ_list['data']:
        row = static_champ_list['data'][key]
        champ_dict[row['key']] = row['id']
        # if row['id'] == "MonkeyKing":
        #     champ_dict[row['key']] = "Wukong"
    # add corrections for void champions
    # st.write("Champ Dictionary", champ_dict)
    # st.stop()

    mastery = watcher.champion_mastery.by_summoner(my_region, me['id'])
    # st.write(mastery[0:10]) # this is sorted from most mastery to least automatically
    champion_mastery = []
    for champion in mastery:
        single_champ = {}
        single_champ['Champion'] = champ_dict[str(champion['championId'])]
        if single_champ['Champion'] == 'MonkeyKing':
            single_champ['Champion'] = 'Wukong'
        single_champ['Mastery Level'] = champion['championLevel']
        single_champ['Champion Points'] = champion['championPoints']
        champion_mastery.append(single_champ)

    # st.write(champion_mastery[0:10])
    df_champ_mastery = pd.DataFrame(champion_mastery[0:10])
    df_champ_mastery.index += 1
    # st.write(df_champ_mastery)
    # need to make table into full html, and then convert the that to html st.write, icon can then be printed
    # need function to create image links
    champ_icon = []
    try:
        for i in range(10):
            champ_icon.append(image_link('champion', champ_dict[str(mastery[i]['championId'])]))
    except:
        pass
    champion_mastery_icon = ["<img src='https://ddragon.leagueoflegends.com/cdn/11.17.1/img/champion/Aatrox.png'width='40' height='40'>"] * 10
    # df_champ_mastery["icon"] = champion_mastery_icon
    df_champ_mastery.insert(0, 'Icon', champ_icon)
    st.write(df_champ_mastery.to_html(escape=False), unsafe_allow_html=True)
    # st.dataframe(df_champ_mastery)
    # add champion image in table??
# st.stop() #Riot API Status error, cannot access match data
# ----------------------------------------------------------    ------------------------------------------------------------
# need to use try and except for api response error
# my_matches = watcher.match.matchlist_by_puuid(my_region, me['accountId'])
c3, c4 = st.columns((1, 1))
with c3:
    queue_type = st.selectbox('Queue Type', ['Normal', 'Ranked'])
    if not queue_type:
        st.stop()

    match_list = watcher.match.matchlist_by_puuid('americas',me['puuid'], type=queue_type.lower())
    # st.write(watcher.match.by_id('americas', match_list[1]))
    # fetch last match detail into table need to change id value to actual terms
    for i in range(len(match_list)-15):
        # last_match = my_matches['matches'][i]
        # match_detail = watcher.match.by_id(my_region, last_match['gameId'])
        match_detail = watcher.match.by_id('americas', match_list[i])

        # st.stop()
        # st.write(match_detail)
        participants = []
        for row in match_detail['info']['participants']:
            participants_row = {}
            participants_row['Win'] = row['win']
            participants_row['Icon'] = image_link('champion', row['championName'])
            participants_row['champion'] = row['championName']
            if participants_row['champion'] == 'MonkeyKing':
                participants_row['champion'] = 'Wukong'
            participants_row['Spell1'] = row['summoner1Id']
            participants_row['Spell2'] = row['summoner2Id']

            participants_row['LVL'] = row['champLevel']
            participants_row['K/D/A'] = (str(row['kills']) + "/" + str(row['deaths']) + "/" + str(row['assists']))
            participants_row['DMG'] = row['totalDamageDealt']
            participants_row['Gold'] = row['goldEarned']
            participants.append(participants_row)

            # champ static list data to dict for looking up

        # print dataframea

        df = pd.DataFrame(participants)
        st.subheader("Game {}".format(i + 1))
        # st.dataframe(df)
        st.write(df.to_html(escape=False), unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)

    # champion_list = ["None"]
    # for value in champ_dict:
    #     champion_list.append(value)
    #
    # champion_selected = st.selectbox('Champion:', champ_dict.values())
    # st.write(champion_selected)
# with c4:
#     st.write("<br>", unsafe_allow_html=True)
#     st.write("<br>", unsafe_allow_html=True)
#     st.write("<br>", unsafe_allow_html=True)
#     st.write("<br>", unsafe_allow_html=True)
#     st.write("<br>", unsafe_allow_html=True)
#     st.write("<br>", unsafe_allow_html=True)
#
#     st.write(df.to_html(escape=False), unsafe_allow_html=True)
#     st.write("<br>", unsafe_allow_html=True)


# start looking at time line json and accumulate gold
# graph the gold
#