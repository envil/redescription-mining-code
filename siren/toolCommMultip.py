from classWorkPlant import WorkPlant
from classWorkClient import WorkClient
import pdb

def getWP(ip="local", numport=None, authkey=None, plant=None):        
    plt = None
    msg = ""
    err = ""
    if ip == "local":
        plt = WorkPlant()
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
            plt = WorkPlant()
            msg = "Started local plant"
    return plt, msg, err

if __name__ == '__main__':
    plt, msg, err = getWP("127.0.0.1", 55444, "shufflin")
    print msg
