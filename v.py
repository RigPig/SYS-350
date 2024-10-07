import getpass
passwd = getpass.getpass()
from pyVim.connect import SmartConnect
import ssl
s = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
s.verify_mode = ssl.CERT_NONE
si = SmartConnect(host="vcenter.kevin.local", user="kevin-adm@kevin.local", pwd=passwd, sslContext=s)
aboutInfo = si.content.about
print(aboutInfo)
print(aboutInfo.fullName)