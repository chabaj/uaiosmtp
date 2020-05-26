from enum import Enum

class Global(Enum):
    PositiveCompletion = 200
    PositiveIntermediate = 300
    TransientNegativeCompletion = 400
    PermanentNegativeCompletion = 500


class Specific(Enum):
    Syntax = 0
    Information = 10
    Connection = 20
    MailSystem = 50


class Status(Enum):
    SystemStatus = 211
    SystemHelp = 211
    HelpMessage = 214
    ServiceReady = 220
    ServiceClosing = 221
    RequestedMailActionOkay = 250
    UserNotLocalWithForward = 251
    CannotVerifyUser = 252
    StartMailInput = 354
    ServiceNotAvailable = 421
    RequestedMailActionNotTaken = 450
    RequestActionAborted = 451
    InsufficientSystemStorage = 452
    ServerUnableToAccommodateArguement = 455
    CommandSyntaxError = 500
    ArgumentSyntaxError = 501
    CommandNotImplemeted = 502
    BadSequenceOfCommands = 503
    CommandArgumentNotImplemented = 504
    MailboxUnavailable = 550
    UserNotLocalWithoutForward = 551
    ExceededStorageAllocation = 552
    MailboxNotAllowed = 553
    TransactionFailed = 554
    MailFromRcptToArguementNotRecognized = 555


def _reply(writer, status, line, last=True):
    writer.write('{}'.format(status).encode('utf-8'))
    if last:
        writer.write(b' ')
    else:
        writer.write(b'-')
    writer.write(line)
    writer.write(b'\r\n')

async def reply(writer, status, *lines):
    for line in lines[:-1]:
        _reply(writer, status, line, last=False)
    _reply(writer, status, lines[-1], last=True)
    await writer.drain()

