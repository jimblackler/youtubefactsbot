youtubefactsbot
===============

I regularly read [Reddit](http://www.reddit.com) on a phone, and I've come to admire a particular bot [autowikibot](http://www.reddit.com/user/autowikibot). When someone posts a link to a Wikipedia article the bot replies with an excerpt from the article directly into the conversation. Without the bot replying, in order to understand why the link was posted I'd have to follow the link - taking me out of the app, incurring a delay and data use.

I noticed that there was a similar problem to be solved with YouTube links. Reddit users regularly post these but unlike Wikipedia links there's nothing in the URL to indicate what the article might be about, just a string of digits such as "dQw4w9WgXcQ". When I'm reading a conversation on Reddit and someone posts a YouTube link without explanation it's frustrating; I have to leave the Reddit app to know why that post was made.

I built a bot in Python using the [Reddit API](https://www.reddit.com/dev/api) (via the superb [PRAW](https://praw.readthedocs.org/en/v2.1.19/)), the [Google API for YouTube](https://developers.google.com/youtube/v3/) for video statistics, all hosted on the cloud application platform [Heroku](https://www.heroku.com/home).

It's up and running now, and can be seen in action at http://www.reddit.com/user/youtubefactsbot


What is Reddit and what are bots?
=================================

Redit is a massive and hugely popular discussion website. It has hundreds of millions of users, and thousands of subreddits (discussion pages). As well as internet users talking amongst themselves, the Reddit API allows the creation of 'bots'. These can look like normal Reddit accounts, but their activity is controlled by an automated processes. The bots join in conversations; they typically react to a phrase and reply in order to provide information or amusement.
 
 
How does it work?
=================

A bot is really nothing more than a manually-registered Reddit account being controlled through the API by a long-running program on a computer somewhere. Comments are fetched and and analysed by the program; if it chooses to reply, it does so through a POST to the API.

PRAW makes this process very easy with a helper method called comment_stream(). This allows you to get a look at submissions and comments as they are posted. Provided not much extra processing is needed, it's feasible to keep up with the comment stream and react to every post.

My bot simply runs a regular expression over the comment to extract YouTube links, gets the video ID and fetches the data from the YouTube API. Most of the logic in the app is around formatting the comments and obeying Bot Etiquette.


Bot etiquette
=============

From the outset with this project I wanted to ensure that the bot would be found useful and not annoying by Reddit users. It's important to remember that a bot is a machine process injecting itself into a human conversation. This is one reason why bots have a mixed reputation on Reddit, even though subreddit moderators can choose to ban individual bots (very likely if they cause annoyance). I took care to err on the side of caution with the bot's interaction.

At the time of writing, the bot:

* Only replies to very short comments; normally just a raw link without context.

* Doesn't reply to a comment if there's a reply already, so as not to break the flow of the conversation.

* Attempts to delete any of its comments if they are downvoted (effectively allowing readers to delete bot comments).

* Only adds a single comment to any given submission (thread); except in very large threads.

In addition, the creator of autowikibot made not only the source for his bot online, but also (via Reddit's wiki feature) the user and subreddit blacklist. These are users who have requested the bot not reply to them, and subreddits that have banned the bot. By applying the same blacklists to the youtubefacts bot from day one I was able to reduce the risk that the bot would comment where it wasn't wanted. 
 
Mainly I took care to make the information posted by the bot about the videos as information-dense as possible in order to justify its position in the threads. I have a ton of information available from the API, but a lot of it (such as bit rate, comment count and more) simply would be interesting enough to justify it's place in the thread. I decided not even to include the channel (YouTube poster) name. I include the video name, running time, view count and posting date. I also include the first line of the description as it often adds useful information about the context. I don't do this if it contains a link so as not to potentially introduce spammy links into Reddit threads, and also because those kinds of comments tend to be promotional rather than informative.


Source
======

The source is also online at https://github.com/jimblackler/youtubefactsbot and licensed under GPL.

If you want your own implementation you'll have to register applications on both Reddit and Google API (YouTube), sign into both accounts locally, and upload the secrets and tokens folder to your application on Heroku.

Hope you enjoy the bot.