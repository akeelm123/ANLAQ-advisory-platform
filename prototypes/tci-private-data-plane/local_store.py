"""Single-instance encrypted checkpoint store for the synthetic local pilot."""
import fcntl,hashlib,os,secrets,stat,tempfile,time
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from data_plane import DataPlane,Invalid
from pilot_storage import seal_synthetic,restore_synthetic,write_synthetic_archive,MAX_TEST_RETENTION,LIMIT

ROLES=("contributor","assessor","reviewer","owner")
def _derive(passphrase,salt):
    if not isinstance(passphrase,str) or not 16<=len(passphrase)<=256 or not isinstance(salt,bytes) or len(salt)!=32:
        raise Invalid("Use a unique local vault passphrase of at least 16 characters")
    master=hashlib.scrypt(passphrase.encode(),salt=salt,n=2**15,r=8,p=1,dklen=32,maxmem=128*1024*1024)
    return tuple(HKDF(algorithm=hashes.SHA256(),length=32,salt=salt,info=("TCI-local-"+label).encode()).derive(master) for label in ("vault","evidence","audit"))

def _private_file(path,maxsize):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077 or st.st_size>maxsize:raise Invalid("Local vault file permissions or size invalid")
        with os.fdopen(fd,"rb",closefd=False) as f:return f.read(maxsize+1)
    finally:os.close(fd)

class LocalStore:
    def __init__(self,path,register,spec,clock=time.time,retention=MAX_TEST_RETENTION):
        self.path=Path(path).expanduser();self.register=register;self.spec=spec;self.clock=clock;self.retention=retention;self.dp=None;self.keys=None;self.lock=None
        if type(retention) is not int or not 1<=retention<=MAX_TEST_RETENTION:raise Invalid("Synthetic checkpoint retention limit")
        self.path.mkdir(parents=True,mode=0o700,exist_ok=True)
        st=self.path.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077:raise Invalid("Local vault directory must be owner-only (0700), not a symlink")
        fd=os.open(self.path/"pilot.lock",os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            st=os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077:raise Invalid("Local vault lock permissions invalid")
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (OSError,Invalid) as ex:os.close(fd);raise Invalid("Local vault already in use or lock invalid") from ex
        self.lock=fd
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
    @property
    def current(self):return self.path/"current.tci"
    @property
    def saltfile(self):return self.path/"salt.bin"
    def _dirsync(self):
        fd=os.open(self.path,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    def initialize(self,passphrase,accounts,title="Synthetic local pilot"):
        if self.dp or self.current.exists() or self.saltfile.exists() or self.current.is_symlink() or self.saltfile.is_symlink():raise Invalid("Vault exists or initialisation incomplete; do not overwrite")
        if set(accounts)!=set(ROLES) or any(not isinstance(x,(tuple,list)) or len(x)!=2 for x in accounts.values()):raise Invalid("Four named role accounts required")
        names=[x[0] for x in accounts.values()];passwords=[x[1] for x in accounts.values()]
        if any(not isinstance(n,str) or not n.strip() for n in names) or len({n.strip().casefold() for n in names})!=4 or len(set(passwords))!=4 or passphrase in passwords:raise Invalid("Distinct named users, passwords and vault passphrase required")
        salt=secrets.token_bytes(32);self.keys=_derive(passphrase,salt);vault,evidence,audit=self.keys
        self.dp=DataPlane(":memory:",evidence,audit,self.register,self.spec,clock=self.clock)
        aid=self.dp.bootstrap_assessment("Synthetic local tenant",title,"Fictional records only; independent role review")
        for role,(name,pw) in accounts.items():
            uid=self.dp.bootstrap_user(name,pw);self.dp.bootstrap_membership(aid,uid,role)
        self.dp.db.execute("PRAGMA temp_store=MEMORY")
        fd=os.open(self.saltfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,"wb") as f:f.write(salt);f.flush();os.fsync(f.fileno())
        self.checkpoint(initial=True);return aid
    def unlock(self,passphrase):
        if self.dp:raise Invalid("Already unlocked")
        salt=_private_file(self.saltfile,32);self.keys=_derive(passphrase,salt);vault,evidence,audit=self.keys
        self.dp=restore_synthetic(_private_file(self.current,LIMIT+65536),vault,evidence,audit,self.register,self.spec,confirmed_synthetic=True,clock=self.clock)
        self.dp.db.execute("PRAGMA temp_store=MEMORY");return self.dp
    def checkpoint(self,initial=False):
        if self.dp is None or self.keys is None:raise Invalid("Vault not unlocked")
        blob=seal_synthetic(self.dp,self.keys[0],self.retention,confirmed_synthetic=True,clock=self.clock)
        if initial:
            write_synthetic_archive(self.current,blob);self._dirsync();return
        # A complete authenticated image is written and synced before the atomic pointer replacement.
        fd,name=tempfile.mkstemp(prefix=".checkpoint-",dir=self.path)
        try:
            with os.fdopen(fd,"wb") as f:f.write(blob);f.flush();os.fsync(f.fileno())
            os.replace(name,self.current);self._dirsync()
        finally:
            if os.path.exists(name):os.unlink(name)
    def backup(self,path):
        if self.dp is None:raise Invalid("Vault not unlocked")
        # Archive only. Salt must be separately retained to derive the keys.
        blob=seal_synthetic(self.dp,self.keys[0],self.retention,confirmed_synthetic=True,clock=self.clock)
        return write_synthetic_archive(path,blob)
    def recover_backup(self,archive_path,salt_path,passphrase):
        if self.dp or self.current.exists() or self.saltfile.exists() or self.current.is_symlink() or self.saltfile.is_symlink():raise Invalid("Recovery requires a new empty vault; never overwrite")
        salt=_private_file(Path(salt_path),32);self.keys=_derive(passphrase,salt)
        self.dp=restore_synthetic(_private_file(Path(archive_path),LIMIT+65536),*self.keys,self.register,self.spec,confirmed_synthetic=True,clock=self.clock)
        self.dp.db.execute("PRAGMA temp_store=MEMORY")
        fd=os.open(self.saltfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,"wb") as f:f.write(salt);f.flush();os.fsync(f.fileno())
        self.checkpoint(initial=True)
        return self.dp
    def close(self):
        if self.dp:self.dp.close();self.dp=None
        self.keys=None
        if self.lock is not None:os.close(self.lock);self.lock=None
