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

    def emit(self, record):
        """Store a new log record in database."""
        author = ""
        if os.getenv("SUDO_USER"):
            author = os.getenv("SUDO_USER")
        elif os.getenv("USER"):
            author = os.getenv("USER")

        newrec = LogEntry(author=author, msg=record.msg)
        newrec.save()
