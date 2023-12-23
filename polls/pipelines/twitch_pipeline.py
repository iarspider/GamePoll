from django.conf import settings

from polls.models import TwitchUser


def get_user(backend, access_token):
    user_info_url = "https://api.twitch.tv/helix/users"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-ID": settings.SOCIAL_AUTH_TWITCH_KEY,
        "Accept": "application/vnd.twitchtv.v5+json",
    }
    response = backend.request(user_info_url, method="GET", headers=headers)
    return response


def get_subscription(backend, access_token, user_id):
    user_info_url = "https://api.twitch.tv/helix/subscriptions/user"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-ID": settings.SOCIAL_AUTH_TWITCH_KEY,
        "Accept": "application/vnd.twitchtv.v5+json",
    }
    response = backend.request(
        user_info_url,
        method="GET",
        headers=headers,
        params={"broadcaster_id": settings.BROADCASTER_ID, "user_id": user_id},
    )
    return response


def fetch_user_details(backend, details, user=None, *args, **kwargs):
    if user:
        # Fetch additional user details using the user's token
        if backend.name == "twitch":
            access_token = kwargs["response"].get("access_token")

            if not TwitchUser.objects.filter(user=user).exists():
                response = get_user(backend, access_token)
                print(dir(response))
                if response.status_code == 200:
                    user_info = response.json().get("data")[0]
                    user.username = user_info.get("login")
                    user.email = user_info.get("email")
                    user.first_name = user_info.get("display_name")
                    user.save()
                    twitch_user = TwitchUser()
                    twitch_user.user = user
                    twitch_user.twitch_user_id = user_info.get("id")
                    twitch_user.save()

            twitch_user = TwitchUser.objects.get(user=user)

            res = get_subscription(backend, access_token, twitch_user.twitch_user_id)
            if res.status_code == 200:
                twitch_user.subscribed = True
            else:
                twitch_user.subscribed = False

            twitch_user.save()
