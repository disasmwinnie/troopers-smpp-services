# Troopers SMPP-Services

These are the three SMPP-services for the [Troopers17](https://troopers.de), I hacked down during the conference, partly with Simon.

In case you missed it, there was a GSM network and an [SMPP](https://en.wikipedia.org/wiki/Short_Message_Peer-to-Peer) gateway to enable kinky  stuff (broad definition), if you send an SMS to them.

A prerequisite is the [python-smpplib](https://github.com/podshumok/python-smpplib) egg. You'll find service specific dependencies in the respective *requirements.txt* files. If you want to test your service there's a [SMPP gateway simulator](https://github.com/smn/logica-smpp-sim) you can use. One of ERNW's guys wrote a [blog post](https://insinuator.net/2017/03/troopers17-gsm-network-how-about-your-own-smpp-service/) with more detailed instructions - you should have a look at it.

### LED-Wall (sms-ledwall)

This service basically shows the content of your SMS on an LED screen/wall.
The incoming messages are put into a queue with capacity of 30 messages, which are pulled every 5-seconds.
The latter should be adjusted, depending on how long your screen needs to print the 160 characters.
If the queue is full, messages are rejected.

The LED mappings are specific to your LED-wall. The one's in this service are specific to @[talynrae](https://twitter.com/talynrae)'s custom build wall.

### Message of The Day (sms-msgoftheday)

This service reads the messages from a text file.
It splits every line by pipe "|".
The first element is the time range in hours, the latter is the actual service.
The con visitors could send an SMS and, depending on the current time, she gets current information about the conference events, e.g., information about evening program or talks.

### TicTacToe

The TicTacToe logic, basically the whole *tictactoe.py* file, is made by Simon Otto.
I made the SMPP stuff and glued multiple pounds of CSS/JS libraries, until something like a web app evolved.

The idea behind this service was, that there would be an additional Raspberry Pi plugged into a huge display, which accesses the app server of the service.
Con visitors could meet in the lobby (in front of the TV, where most healthy families gather) in order to socialize and play TicTacToe with their badges.

However, at some point we run out of time and decided to see some of the talks (we coded way into the main conference time).
Therefore, the service never made it online.
An open TODO is to implement a timeout, in order to kick inactive players, and test it properly.
Although, we made multiple runs, I am sure there are some bugs to catch.
Testing with the SMPP-Gateway-Simulator is not sufficient, since more then one player is involved.
As soon as we visit the production environment again, this should fixed quickly ;-)


This SMPP-Service expects two players to start the game.
The moves are made by sending an SMS with "X Y" messages, whereas both values must be between 0 and 2.
The first two players, who send an SMS with "join" to the services are added to the current game.
Others have to wait until the game is over, or the players leave the game with an "exit" SMS.

The game field is shown on a web application, which also contains status messages.
It is an Flask-based web-socket app, which refreshes the game field as soon as players send SMS to the service.
