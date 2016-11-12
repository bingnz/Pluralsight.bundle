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
            ),
            DirectoryObject(
                key = Callback(NewMenu),
                thumb = R('NewStuff.png'),
                title = L('NEW_COURSES')
            ),
            DirectoryObject(
                key = Callback(PopularMenu),
                thumb = R('Popular.png'),
                title = L('POPULAR_COURSES')
            ),
            InputDirectoryObject(
                key = Callback(SearchResults),
                thumb = R('Search.png'),
                title = L('SEARCH')
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
            title1 = L('RECENT_COURSES'),
            no_cache = True
        )

    for recent in recentlyViewed:
        oc.add(
            Course(recent.name)
        )

    return oc

def CourseObject(course):
    return DirectoryObject(
                key = Callback(Modules, courseName = course.name),
                title = course.title + ' ({0})'.format(course.level),
                duration = course.duration,
                summary = course.description,
                thumb = course.image,
                art = course.image
            )

@route(PREFIX + '/new')
@handle_client_error
def NewMenu():
    Log.Info('NewMenu')
    newCourses = g_client.new_courses()
    oc = ObjectContainer(
            title1 = L('NEW_COURSES'),
            no_cache = True
        )

    for course in newCourses:
        oc.add(
            CourseObject(course)
        )

    return oc

@route(PREFIX + '/popular')
@handle_client_error
def PopularMenu():
    Log.Info('PopularMenu')
    popularCourses = g_client.popular_courses()
    oc = ObjectContainer(
            title1 = L('POPULAR_COURSES'),
            no_cache = True
        )

    for course in popularCourses:
        oc.add(
            CourseObject(course)
        )

    return oc

@route(PREFIX + '/search')
@handle_client_error
def SearchResults(query):
    Log.Info('SearchResults query=\'%s\'', query)
    oc = ObjectContainer(
            title1 = F('SEARCH_RESULTS_FORMAT', query)
        )

    courses = g_client.search(query)

    for course in courses:
        oc.add(
            CourseObject(course)
        )

    return oc

@route(PREFIX + '/course')
@handle_client_error
def Course(courseName):
    Log.Info('Course: %s', courseName)

    course = g_client.get_course(courseName)

    courseContainer = CourseObject(course)

    Log.Debug('Course \'%s\' has %d modules.', courseName, len(course.modules))

    return courseContainer

@route(PREFIX + '/modules')
@handle_client_error
def Modules(courseName):
    Log.Info('Modules: %s', courseName)

    course = g_client.get_course(courseName)

    oc = ObjectContainer(
             title1 = course.title
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

    oc.add(DirectoryObject(
        key = Callback(RelatedCourses, courseName = courseName),
        title = L('RELATED_COURSES'),
        thumb = R('More.png')
    ))

    return oc

@route(PREFIX + '/relatedcourses')
@handle_client_error
def RelatedCourses(courseName):
    Log.Debug('Related courses: %s', courseName)
    relatedCourses = g_client.related_courses(courseName)
    oc = ObjectContainer(
            title1 = L('RELATED_COURSES'),
            title2 = courseName,
            no_cache = True
        )

    for course in relatedCourses:
        oc.add(
            Course(course.name)
        )

    return oc

@route(PREFIX + '/clips')
@handle_client_error
def Clips(courseName, moduleName):
    Log.Info('Clips: %s - %s', courseName, moduleName)

    course = g_client.get_course(courseName)
    matchingModules = filter(lambda x: x.name == moduleName, course.modules)
    module = matchingModules[0] if matchingModules else None

    Log.Debug('Clips for module: {0}'.format(repr(module)))

    oc = ObjectContainer(
             title1 = module.title
         )

    for clip in module.clips:
        Log.Debug('Clip: {0} - {1}'.format(clip.url, repr(clip)))

        oc.add(EpisodeObject(
            url = clip.url,
            index = clip.index,
            title = clip.title,
            show = module.title,
            duration = clip.duration,
            thumb = course.image
        ))

    return oc
