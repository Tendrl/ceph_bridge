class RequestStateError(Exception):
    def __init___(self, err):
        self.message = "Request state error. Error:" + \
                       " {}".format(err)
        super(RequestStateError,self).__init__(self.message)
