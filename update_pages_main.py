import requests
import json
import os
import update_pages_functions as upf
from pathlib import Path
from yahoo_fin import stock_info as si
import get_price_data as upd
import time
import numpy as np
from datetime import datetime as dt
import math


def main(tickers):
    # updates data/ticker.json with the most recent news data. overwrites
    # Assuming the Flask app is running on the default localhost:5000
    
    file_path = Path(__file__).parent.joinpath("data").absolute()
    # print(file_path)

    for item in tickers:
        print("\n", item)

        priceData = upd.getPrices(item)
        priceData = priceData.reset_index()
        # print(priceData)

        # separate the price data into lists of days
        dtime = list(priceData["Datetime"])
        closes = list(priceData["Close"][item])

        dailyPriceData = {}
        daysData = []
        lastDate = dtime[0]
        # for each new day, add the days prices to a new list in daily data
        for i in range(len(dtime)):
            if dtime[i].day != lastDate.day:
                dailyPriceData[str(lastDate.month) + " " + str(lastDate.day) + " " + str(lastDate.year)] = daysData
                daysData = []
                lastDate = dtime[i]

            daysData.append(closes[i])
        dailyPriceData[str(lastDate.month) + " " + str(lastDate.day) + " " + str(lastDate.year)] = daysData

        # print(len(dailyPriceData["4 2 2025"]))

        try:
            url = 'http://127.0.0.1:5000/' + item

            response = requests.get(url)

            print("Status Code:", response.status_code)

            if response.status_code == 200:  # make sure it was a good response
                articleData = response.json()
                articles = articleData["articles"]
                # print(articles)
                
                # get the most important articles per day

                # sort articles in order of date
                sortKey = "publication_date"
                timeFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
                sortedArticlesDate = list(reversed(sorted(articles, key=lambda x: dt.strptime(x[sortKey], timeFormat))))

                # place articles into their own days in a dictionary
                dailyArticles = {}
                daysArticles = []
                lArtDate = dt.strptime(sortedArticlesDate[0]["publication_date"], timeFormat)  # last article date
                for article in sortedArticlesDate:
                    # print(article["publication_date"])
                    # print(article)
                    
                    pubDate = dt.strptime(article["publication_date"], timeFormat)
                    if pubDate.day != lArtDate.day:
                        dailyArticles[str(lArtDate.month) + " " + str(lArtDate.day) + " " + str(lArtDate.year)] = daysArticles
                        daysArticles = []
                        lArtDate = pubDate
                    
                    daysArticles.append(article)
                dailyArticles[str(lArtDate.month) + " " + str(lArtDate.day) + " " + str(lArtDate.year)] = daysArticles  # place remainder in the dict

                # print(dailyArticles["4 2 2025"])
                print(list(dailyArticles.keys()))

                postDict = {}  # these are the important articles that will get posted for each day keys are month day year
                # loop through the dictionary of daily articles and calculate important data for each
                for key in dailyArticles:
                    # put together the data for this key (date) to post to pages
                    postDict[key] = {}

                    # sort articles in order of sentimentScore to make them easy to work with
                    sortKey = "sentimentScore"
                    sortedArticles = list(reversed(sorted(dailyArticles[key], key=lambda x: float(x[sortKey]))))

                    # get top good/bad articles
                    important = []
                    numImportant = 3
                    i = 0
                    # best
                    for article in sortedArticles:
                        important.append(article)
                        if i >= numImportant-1:
                            break
                        i += 1

                    i = 0
                    # worst
                    for article in sortedArticles[::-1]:  # loop reverse
                        important.append(article)
                        if i >= numImportant-1:
                            break
                        i += 1

                    # get average sentiment score
                    avgScore = 0
                    i = 0
                    for article in sortedArticles:
                        score = float(article["sentimentScore"])
                        avgScore += score

                        i += 1
                    avgScore /= i

                    postDict[key]["importantArticles"] = important
                    postDict[key]["avgScore"] = avgScore
                    # print(key, avgScore)

                # get a list of article dates from price data and get average sentiment scores and pct changes
                scores = []
                pctChanges = []
                keys = list(dailyPriceData.keys())
                print(keys)
                for index, key in enumerate(dailyPriceData):
                    if key in postDict:  # if there are articles for this date
                        # get the article score
                        scores.append(postDict[key]["avgScore"])
                        
                        # the percent change is calculated as the change from yesterday's open to today's open
                        #  unless it is current day, then it does open to last price
                        # get percent change
                        pOpen = dailyPriceData[key][0]
                        
                        if index + 1 < len(keys):
                            pClose = dailyPriceData[keys[index + 1]][0]
                        else:
                            pClose = dailyPriceData[key][-1]
                        
                        pctChange = (pClose - pOpen) / pOpen
                        pctChanges.append(pctChange)
                        # print(key, pOpen, pClose)

                # remove non days with price data articles from the dict
                toRemove = []
                for key in dailyArticles:
                    if key not in keys:
                        toRemove.append(key)

                for key in toRemove:
                    # print(key)
                    del postDict[key]

                # we should change this later to only remove articles older than price data

                # calculate the volatility score for the stock
                print(scores)
                print(pctChanges)
                coef = getR(scores, pctChanges)
                print(coef)

                postDict["coef"] = coef
                postDict["avgCoef"] = getAverageR()

                # once we have all the data, dump results to a ticker.json
                ticker_path = file_path.joinpath(item + ".json")  # data directory file

                if not math.isnan(coef):
                    if os.path.exists(ticker_path):
                        with open(ticker_path, "w") as f:
                            json.dump(postDict, f, indent=4)
                    else:
                        with open(ticker_path, "x") as f:
                            json.dump(postDict, f, indent=4)

        except requests.exceptions.ConnectionError:
            pass

        except KeyError as e:
            print("KeyError:", e)

        except IndexError as e:
            print("IndexError:", e)

        # except TypeError as e:
            # print("TypeError:", e)

        time.sleep(60)


def getR(x, y):
    """ Documentation
    Given a list of length n, x, and a list of length n, y, returns the correlation coefficient for the sets.
    
    :param: x: list: list 1
    :param: y: list: list 2
    """

    x = np.array(x.copy())
    y = np.array(y.copy())

    co_matrix = np.corrcoef(x, y)
    coef = co_matrix[0, 1]

    return coef


def calcVScore(score, pctChange):
    """ Documentation
    The vScore is an indicator of how much the stock moved vs its article score. If the number is positive,
    the price moved in the same direction as indicated by the article score. The higher (lower) the number indicates
    a higher move in price and a higher article score. While the vScore can be high due to a high price change,
    if the article score is low, it will be very unlikely.
    """

    vScore = score * (pctChange * 100)
    return vScore


def getDayMovers():
    # Get most active tickers by volume
    most_active = si.get_day_most_active()

    return list(most_active["Symbol"])


def getAverageR():
    dir_path = Path(__file__).parent.joinpath("data").absolute()
    avgCoef = 0
    i = 0
    for filename in os.listdir(dir_path):
        file_path = dir_path.joinpath(filename)
        with open(file_path, 'r') as f:
            data = json.load(f)
            value = float(data['coef'])
            if not math.isnan(value):
                avgCoef += value
                i += 1

    if i > 0:
        avgCoef /= i
        return avgCoef
    else:
        return 0



def test():
    data = {'setting': {'refresh': {'duration': 20, 'requireUserAction': False, 'limit': 30, 'tabFocus': {'outOfFocusDuration': 3}, 'sameSizeRefresh': True, 'reserved': {'duration': 60}}, 'lazyLoad': False, 'tracking': {'performance': True, 'metrics': True}, 'taboolaSetting': {'pageType': 'article', 'publisherId': 'yahooweb-network'}, 'consent': {'allowOnlyLimitedAds': False, 'allowOnlyNonPersonalizedAds': False}, 'userInfo': {'age': 0, 'gender': ''}}, 'feature': {'enableAdCollapse': True, 'enableAdStacking': True, 'enableNewPremiumAdLogic': True, 'enableUserSegments': True}, 'positions': {'sda-E2E': {'id': 'sda-E2E', 'path': '/22888152279/us/yfin/ros/dt/us_yfin_ros_dt_top_center', 'region': 'index', 'size': [[3, 1], [970, 250], [728, 90]], 'kvs': {'loc': 'top_center'}, 'customSizeConfig': {'Horizon': True}}}, 'i13n': {'_yrid': '3l6tu2hjv8nve', 'colo': 'gq1', 'lang': 'en-US', 'mrkt': 'us', 'navtype': 'server', 'site': 'finance', 'ver': 'nimbus', 'pg_name': 'article', 'pt': 'content', 'theme': 'auto', 'auth_state': 'signed_out', 'partner': 'none', '_vuid': '5sU2SKSZDdnfeZC261r7kw', 'uuid': '38e5c5c8-57d9-3b7a-88ec-e4a4c84f7823', 'pct': 'story', 'spaceId': '1183300100', 'type': 'story', 'videoPosition': 'top', 'p_cpos': 1, 'p_hosted': 'hosted', 'pstaid': '38e5c5c8-57d9-3b7a-88ec-e4a4c84f7823', 'pstaid_p': '38e5c5c8-57d9-3b7a-88ec-e4a4c84f7823', 'pstcat': 'business', 'lmsid': 'a0V0W00000HOSDEUA5', 'pl2': 'seamless-article', 'hashtag': 'investments;finance', 'pd': 'modal', 'spaceid': '1183300100', 'consent': {'allowContentPersonalization': True, 'allowCrossDeviceMapping': True, 'allowFirstPartyAds': True, 'allowSellPersonalInfo': True, 'canEmbedThirdPartyContent': True, 'canSell': True, 'consentedVendors': ['acast', 'brightcove', 'dailymotion', 'facebook', 'flourish', 'giphy', 'instagram', 'nbcuniversal', 'playbuzz', 'scribblelive', 'soundcloud', 'tiktok', 'vimeo', 'twitter', 'youtube', 'masque']}, 'authed': '0', 'ynet': '0', 'ssl': '1', 'spdy': '0', 'ytee': '0', 'mode': 'normal', 'tpConsent': True, 'adblock': '0', 'bucket': '', 'device': 'desktop', 'bot': '0', 'browser': 'unknown', 'app': 'unknown', 'ecma': 'default', 'environment': 'prod', 'gdpr': False, 'dir': 'ltr', 'intl': 'us', 'network': 'mobile', 'os': 'other', 'region': 'US', 'time': 1744068590273, 'tz': 'America/Los_Angeles', 'usercountry': 'US', 'rmp': '0', 'webview': '0', 'feature': ['awsCds', 'disableInterstitialUpsells', 'disableServiceRewrite', 'disableSubsSpotlightNav', 'disableBack2Classic', 'disableYPFTaxArticleDisclosure', 'enable1PVideoTranscript', 'enableAdRefresh20s', 'enableAnalystRatings', 'enableAPIRedisCaching', 'enableArticleCSN', 'enableArticleRecommendedVideoInsertionTier34', 'enableChartbeat', 'enableChatSupport', 'enableCommunityPostsSidebar', 'enableCompare', 'enableCompareConvertCurrency', 'enableConsentAndGTM', 'enableCrumbRefresh', 'enableCSN', 'enableCurrencyConverter', 'enableDarkMode', 'enableDockAddToFollowing', 'enableDockCondensedHeader', 'enableDockNeoOptoutLink', 'enableDockPortfolioControl', 'enableExperimentalDockModules', 'enableFollow', 'enableGCPRecommendationsUserEvents', 'enableLazyQSP', 'enableLiveBlogStatus', 'enableLivePage', 'enableStreamingNowBar', 'enableLocalSpotIM', 'enableMarketsLeafHeatMap', 'enableMultiQuote', 'enableNeoArticle', 'enableNeoAuthor', 'enableNeoBasicPFs', 'enableNeoGreen', 'enableNeoHouseCalcPage', 'enableNeoInvestmentIdea', 'enableNeoMortgageCalcPage', 'enableNeoQSPReportsLeaf', 'enableNeoResearchReport', 'enableNeoTopics', 'enablePersonalFinanceArticleReadMoreAlgo', 'enablePersonalFinanceNewsletterIntegration', 'enablePersonalFinanceZillowIntegration', 'enablePf2SubsSpotlight', 'enablePfPremium', 'enablePfStreaming', 'enablePinholeScreenshotOGForQuote', 'enablePlus', 'enablePortalStockStory', 'enablePrivateCompany', 'enablePrivateCompanyBanner', 'enableQSPChartEarnings', 'enableQSPChartNewShading', 'enableQSPChartRangeTooltips', 'enableQSPEarnings', 'enableQSPEarningsVsRev', 'enableQSPHistoryPlusDownload', 'enableQSPNavIcon', 'enableQuoteLookup', 'enableRecentQuotes', 'enableResearchHub', 'enableScreenerHeatMap', 'enableSECFiling', 'enableSigninBeforeCheckout', 'enableSmartAssetMsgA', 'enableStockStoryPfPage', 'enableStockStoryTimeToBuy', 'enableStreamOnlyNews', 'enableSubsFeatureBar', 'enableTradeNow', 'enableUpgradeBadge', 'enableYPFArticleReadMoreAll', 'enableOnePortfolio', 'enableVideoInHero', 'enableDockQuoteEventsDateRangeSelect', 'enablePfDetailDockCollapse', 'enablePfPrivateCompany', 'enableHoneyLinks', 'enableNeoPortfolioDetail', 'enableCompareFeatures', 'enableGenericHeatMap', 'enableQSPIndustryHeatmap', 'enableStatusBadge'], 'isDebug': False, 'isForScreenshot': False, 'isWebview': False, 'pnrID': '', 'isError': False, 'areAdsEnabled': True, 'ccpa': {'warning': '', 'footerSequence': ['terms_and_privacy', 'dashboard'], 'links': {'dashboard': {'url': 'https://guce.yahoo.com/privacy-dashboard?locale=en-US', 'label': 'Privacy Dashboard', 'id': 'privacy-link-dashboard'}, 'terms_and_privacy': {'multiurl': True, 'label': '${terms_link}Terms${end_link} and ${privacy_link}Privacy Policy${end_link}', 'urls': {'terms_link': 'https://guce.yahoo.com/terms?locale=en-US', 'privacy_link': 'https://guce.yahoo.com/privacy-policy?locale=en-US'}, 'ids': {'terms_link': 'privacy-link-terms-link', 'privacy_link': 'privacy-link-privacy-link'}}}}, 'yrid': '3l6tu2hjv8nve', 'user': {'age': 0, 'firstName': None, 'gender': '', 'year': 0}, 'abk': '0', 'lu': '0'}}

    print(data.keys())
    print(data['i13n']['time'])


if __name__ == "__main__":
    print(getAverageR())

    """ Examples of vScore calculation
    print(calcVScore(-0.6, -0.04))
    print(calcVScore(-0.8, -0.1))
    print(calcVScore(0.5, 0.08))
    print(calcVScore(-0.45, 0.06))
    print(calcVScore(0.55, -0.05))
    print(calcVScore(1.0, 0.15))
    # """

    # test()

    # """
    while True:
        mostActive = getDayMovers()
        if "SPY" not in mostActive: mostActive.insert(0, "SPY")

        print(mostActive)
        print(len(mostActive))
        main(mostActive)

        upf.commit_and_push()
    # """