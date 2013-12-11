from classWorkLocal import WorkLocal
from classWorkClient import WorkClient
import pdb

# class WorkPlant:
#     def __init__(ip="local", numport=None, authkey=None, parent=None):
#         self.ip = ip
#         self.numport = numport
#         self.authkey = authkey
#         self.parent = parent

def getWP(ip="local", numport=None, authkey=None, plant=None):        
    plt = None
    msg = ""
    err = ""
    if ip == "local":
        plt = WorkLocal()
        msg = "Started local plant"
    else:
        try:    
            plt = WorkClient(ip, numport, authkey)
            if plt.testConnect():
                msg = "Connected to work server."
            else:
                err = "No remote work server available, starting local plant..."
        except Exception as e:
            err = "Error connecting to remote work server, starting local plant..."
            plt = WorkLocal()
            msg = "Started local plant"
    return plt, msg, err

if __name__ == '__main__':
    plt, msg, err = getWP("127.0.0.1", 55444, "shufflin")
    print msg
