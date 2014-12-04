"""Logging module for SLAM, actions are recorded in the SLAM database."""

import logging
import os
from django.db import models


class LogEntry(models.Model):
    """Represent an entry in the database for a log record."""

    date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=255)
    msg = models.TextField()

    def __unicode__(self):
        """Return a string representation of the log record."""
        return str(self.date) + ": " + self.author + ": " + self.msg


class DbLogHandler(logging.Handler):
    """Log handler that store log records in database."""

    author = None
    
    def emit(self, record):
        """Store a new log record in database."""
        if not self.author:
            if os.getenv("SUDO_USER"):
                self.author = os.getenv("SUDO_USER")
            elif os.getenv("USER"):
                self.author = os.getenv("USER")
            else:   #pour tester anomalie, on garantie le author non null
                self.author = "userfictif"

        newrec = LogEntry(author=self.author, msg=record.msg)
        newrec.save()
