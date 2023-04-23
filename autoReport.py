import time
import requests

# https://developers.track.toggl.com/docs/authentication/index.html#http-basic-auth-with-api-token
token = ''
# report.hacknote cookie
cookie = ''
# report.hacknote team_id
team_id = ''
# bark_key
# https://github.com/Finb/Bark
bark_key = ''


def getYearAndWeek():
    timestamp = int(time.time())
    if (timestamp % 604800) > 4 * 86400 or (timestamp % 604800) < 2 * 86400:
        timestamp = timestamp - 604800
    local_time = time.localtime(timestamp)
    year = time.strftime("%Y", local_time)
    week = time.strftime("%W", local_time)
    month = time.strftime("%m", local_time)
    day = time.strftime("%d", local_time)
    weekDay = time.strftime("%w", local_time)
    # 找到上周一的年月日
    if int(weekDay) == 0:
        weekDay = 7
    monday = int(day) - int(weekDay) + 1
    if monday <= 0:
        month = int(month) - 1
        if month == 0:
            month = 12
            year = int(year) - 1
        if month == 2:
            if int(year) % 4 == 0:
                dayNum = 29
            else:
                dayNum = 28
        elif month == 4 or month == 6 or month == 9 or month == 11:
            dayNum = 30
        else:
            dayNum = 31
        monday = dayNum + monday
    # 找到上周日的年月日
    sunday = int(day) - int(weekDay) + 7
    if sunday > 31:
        month = int(month) + 1
        if month == 13:
            month = 1
            year = int(year) + 1
        if month == 2:
            if int(year) % 4 == 0:
                dayNum = 29
            else:
                dayNum = 28
        elif month == 4 or month == 6 or month == 9 or month == 11:
            dayNum = 30
        else:
            dayNum = 31
        sunday = sunday - dayNum

    date_of_monday = str(year) + "-" + str(month) + "-" + str(monday)
    date_of_sunday = str(year) + "-" + str(month) + "-" + str(sunday)
    return year, str(int(week)), date_of_monday, date_of_sunday


def getTasks(start_date, end_date):
    try:
        # 获取任务
        headers = {
            'Content-Type': 'application/json',
        }

        params = {
            'start_date': start_date,
            'end_date': end_date,
        }

        response = requests.get(
            'https://api.track.toggl.com/api/v9/me/time_entries',
            params=params,
            headers=headers,
            auth=(token, 'api_token'),
        )
        return response.json()
    except Exception as e:
        sendBarkMessage('获取任务失败', str(e))


def format_task(tasks):
    format_tasks_map = {}
    for task in tasks:
        format_task = format_tasks_map.get(task['description']) or []
        format_task.append(task)
        format_tasks_map[task['description']] = format_task
    return format_tasks_map


def calculateTime(tasksMap):
    tasksTime = {}
    totalTime = 0
    for tasks in tasksMap:
        time = 0
        for task in tasksMap[tasks]:
            time += task['duration']
        tasksTime[tasks] = time
        totalTime += time
    return tasksTime, totalTime


def convertSecondToHour(second):
    hour = int(second / 3600)
    min = int((second - hour * 3600) / 60)
    sec = second - hour * 3600 - min * 60

    def addZero(num):
        return '0' + str(num) if num < 10 else str(num)
    return addZero(hour) + ':' + addZero(min) + ':' + addZero(sec)


def formatTotalTime(totalTime):
    # timestamp to hour fix 2
    return round(totalTime / 3600, 2)


def formatOutput(tasksTime):
    output = "## pug\n"
    for task in tasksTime:
        output += "- " + task + " " + \
            convertSecondToHour(tasksTime[task]) + "\n"
    return output


def report(yearweek, timeDetails, totalTime):

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8',
        'Cookie': cookie,
        'Origin': 'http://report.hackplan.com',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://report.hackplan.com/dashboard',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    }

    json_data = {
        'yearweek': yearweek,
        'content': [
            {
                'question': '本周主要在做哪些工作？',
                'answer': timeDetails,
            },
            {
                'question': '下周计划要做哪些工作？',
                'answer': None,
            },
            {
                'question': '有哪些外部因素可以改进你的工作？',
                'answer': None,
            },
            {
                'question': '有哪些内部因素可以改进你的工作？',
                'answer': None,
            },
            {
                'question': '本周工作的时长？',
                'answer': totalTime,
            },
        ],
        'team_id': team_id,
    }

    response = requests.post(
        'http://report.hackplan.com/api/teams/{}/reports'.format(team_id),
        # cookies=cookies,
        headers=headers,
        json=json_data,
        verify=False,
    )


def sendBarkMessage(content):
    if bark_key:
        response = requests.get(
            'https://api.day.app/{}/{}/{}'.format(
                bark_key, "pug report", content),
        )


def main():
    # 取这周是第几周，判断上周起止日期
    year, week, date_of_monday, date_of_sunday = getYearAndWeek()
    tasks = getTasks(date_of_monday, date_of_sunday)
    format_tasks_map = format_task(tasks)
    tasksTime, totalTime = calculateTime(format_tasks_map)
    timeDetails = formatOutput(tasksTime)
    reportTotalTime = str(formatTotalTime(totalTime)) + \
        'h\n\n' + convertSecondToHour(totalTime)
    report(year + week, timeDetails, reportTotalTime)
    # 发送通知
    sendBarkMessage(str(formatTotalTime(totalTime)) + 'h')
