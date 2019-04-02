

class SSExcept(Exception):
    ''' The Base Class For all Simple Spotify Exceptions! '''

class ClientExcept(SSExcept) :
    ''' Base Class For all exceptions regarding client and client authentication '''


class InsufficientCredentials(ClientExcept):
    ''' Exception Raised When Not enough credentials are submitted when creating a client '''

class InvalidCredentials(ClientExcept,ValueError) :
    ''' exception raised when the credentials supplied are invalid or likely invalid '''