from functools import wraps

TITLE = 'Pluralsight Courses'
PREFIX = '/video/pluralsight'

ART = 'art-default.png'
ICON = 'icon-default.png'

g_client = SharedCodeService.client.Client()

def handle_client_error(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SharedCodeService.client.ClientError as e:
            return MessageContainer(header = L('ERROR_HEADER'), message = e.message)
    return func_wrapper

def Start():
    Log.Info('Starting %s plugin.', TITLE)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0'

    try:
        g_client.login()
        Log.Debug('Logged in.')
    except SharedCodeService.client.LoginError as e:
        Log.Error('ERROR: Login failed. %s', repr(e))

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)
    DirectoryItem.thumb = R(ICON)
    Log.Debug('Leaving Start function.')

def ValidatePrefs():
    Log.Info('Preferences changed.')
    try:
        g_client.login(reset = True)
    except SharedCodeService.client.LoginError as e:
        return MessageContainer(header = L('LOGIN_FAILED_HEADER'), message = e.message)
    return MessageContainer(header = L('LOGIN_SUCCEEDED_HEADER'), message = L('LOGIN_SUCCEEDED_MESSAGE'))

@handler(PREFIX, TITLE)
def MainMenu():
    Log.Info('MainMenu')
    oc = ObjectContainer(
        no_cache = True,
        objects = [
            DirectoryObject(
                key = Callback(RecentMenu),
                thumb = R('Recent.png'),
                title = L('RECENT_COURSES')
            )
        ]
    )

    return oc

@route(PREFIX + '/recent')
@handle_client_error
def RecentMenu():
    Log.Info('RecentMenu')
    recentlyViewed = g_client.recently_viewed()
    oc = ObjectContainer(
            title2 = L('RECENT_COURSES'),
            no_cache = True
        )

    for recent in recentlyViewed:
        oc.add(
            Course(recent.name)
        )

    return oc

@route(PREFIX + '/course')
@handle_client_error
def Course(courseName):
    Log.Info('Course: %s', courseName)

    course = g_client.get_course(courseName)

    courseContainer = DirectoryObject(
        key = Callback(Modules, courseName = courseName),
        title = course.title + ' ({0})'.format(course.level),
        duration = course.duration,
        summary = course.description,
        thumb = course.image,
        art = course.image
    )

    Log.Debug('Course \'%s\' has %d modules.', courseName, len(course.modules))

    return courseContainer

@route(PREFIX + '/modules')
@handle_client_error
def Modules(courseName):
    Log.Info('Modules: %s', courseName)

    course = g_client.get_course(courseName)

    oc = ObjectContainer(
             title2 = course.title
         )

    for module in course.modules:
        oc.add(TVShowObject(
            key = Callback(Clips, courseName = courseName, moduleName = module.name),
            rating_key = module.url,
            rating = course.rating * 10.0,
            title = module.title,
            duration = module.duration,
            summary = module.description,
            thumb = course.image,
            episode_count = len(module.clips),
            tags = [course.level]
        ))

    return oc

@route(PREFIX + '/clips')
@handle_client_error
def Clips(courseName, moduleName):
    Log.Info('Clips: %s - %s', courseName, moduleName)

    course = g_client.get_course(courseName)
    matchingModules = filter(lambda x: x.name == moduleName, course.modules)
    module = matchingModules[0] if matchingModules else None

    oc = ObjectContainer(
             title2 = module.title
         )

    for clip in module.clips:
        Log.Debug('Clip: {0} - {1}'.format(clip.url, repr(clip)))
        oc.add(EpisodeObject(
            url = clip.url,
            index = clip.index,
            title = clip.title,
            show = module.title,
            duration = clip.duration,
            writers = [module.author],
            thumb = course.image
        ))

    return oc
