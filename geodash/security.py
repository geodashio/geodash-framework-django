from django.contrib.auth.models import User, Group

from guardian.shortcuts import get_users_with_perms, get_perms, remove_perm, assign_perm


def check_perms_view(request, map_obj, raiseErrors=False):
    access = False
    if map_obj.published:
        access = True
    else:
        if not request.user.is_authenticated():
            if raiseErrors:
                raise Http404("Not authenticated.")
        if request.user.has_perm("view_geodashdashboard", map_obj):
            acceess = True
        else:
            if raiseErrors:
                raise Http404("Not authorized.")
    return access

def expand_perms(map_obj):
    allperms = get_users_with_perms(map_obj, attach_perms=True)
    return {
        "advertised": map_obj.advertised,
        "published": map_obj.published,
        'view_geodashdashboard': sorted([x.username for x in allperms if 'view_geodashdashboard' in allperms[x]]),
        'change_geodashdashboard':sorted([x.username for x in allperms if 'change_geodashdashboard' in allperms[x]]),
        'delete_geodashdashboard':sorted([x.username for x in allperms if 'delete_geodashdashboard' in allperms[x]])
    }

def expand_users(request, map_obj):
    users = []
    if request.user.has_perm("change_geodashdashboard", map_obj):
        users =[{'id': x.username, 'text': x.username} for x in User.objects.exclude(username='AnonymousUser')]
    return users

def geodash_assign_default_perms(map_obj, user):
    for perm in ["view_geodashdashboard", "change_geodashdashboard", "delete_geodashdashboard"]:
        assign_perm(perm, user, map_obj)
        #UserObjectPermission.objects.assign_perm(
        #    perm,
        #    user=user,
        #    obj=map_obj)
