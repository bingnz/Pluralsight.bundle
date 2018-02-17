#!/bin/bash

plexServer=$(launchctl list | grep -i plex | awk '{print $1}')

if [ ! -z $plexServer ]; then
	echo "Stopping server..."
    kill $plexServer
fi

echo "Removing existing..."
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Caches/com.plexapp.plugins.pluralsight
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Data/com.plexapp.plugins.pluralsight
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Pluralsight.bundle
rm -f  ~/Library/Logs/Plex\ Media\ Server/PMS\ Plugin\ Logs/com.plexapp.plugins.pluralsight*

echo "Installing latest..."
cp -r . ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Pluralsight.bundle

if [ ! -z $plexServer ]; then
	echo "Starting server..."
    sleep 2
    open -a /Applications/Plex\ Media\ Server.app
fi
echo "Done."
