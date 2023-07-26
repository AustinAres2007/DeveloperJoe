#!/bin/sh

DIR=$(cd "$(dirname "$0")"; pwd)
DB_PATH="$DIR/../dependencies/dg_database.db"
DB_JOURNAL_PATH="$DIR/../dependencies/dg_database.db-journal"

cd $DIR

if [ -e $DB_PATH ]
then
    rm $DB_PATH
    echo "Removed Database file."
    if [ -e $DB_JOURNAL_PATH ]
    then
        rm $DB_JOURNAL_PATH
        echo "Removed Database Journal file."
    fi
else
    echo "No Database file."
fi
        