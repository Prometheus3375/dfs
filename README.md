# Distributed File System
## 0. Requirements

If you are going to use source code, download and install [Python 3.7.5](https://www.python.org/downloads/release/python-375/).

I recommend to use [Docker](https://www.docker.com/), docker images for this project you can download [here](https://hub.docker.com/repository/docker/ssemenyuk/dfs).

Servers where you are going to deploy this system must not use ports 9000 and 9001.

## 1. Installation
### General

To use this system you need to have at least 4 servers, they can be EC2 instances from Amazon Web Services.
1 server is name server. It manages other servers which are storage servers.
Name server communicates with client while storage serves store clients' files and communicates with clients only for file exchange.

### Storage Server

Download docker image of storage server.
```
$ docker pull ssemenyuk/dfs:storage
```
Run container from this image.
```
$ docker run --name storage -ti -p 9001:9001/tcp ssemenyuk/dfs:storage /bin/bash
```
Bash will be opened inside container. Start storage server.
```
# python3 code/StorageServer.py
```
Enter public IP of this storage server.
```
Input public IP address or domain name of this server: <public IP or domain name>
```
Example:
```
Input public IP address or domain name of this server: 15.188.145.145
```
The program will remember this choice. To reset, delete file `myip.txt` inside container.

Wait until program response.
```
Server started
```
Press Ctrl+Z and then type `bg 1`.
```
^Z
[1]+  Stopped                 python3 code/StorageServer.py
# bg 1
[1]+ python3 code/StorageServer.py &
```
Server is running. You may look logs in file `Slog.txt`. All client data is stored inside `storage` directory.

**Perform such actions for each storage server.**

#### Shutdown

Type `fg 1` and then press Ctrl+C.

### Name Server

Download docker image of name server.
```
$ docker pull ssemenyuk/dfs:server
```
Run container from this image.
```
$ docker run --name server -ti -p 9000:9000/tcp ssemenyuk/dfs:server /bin/bash
```
Bash will be opened inside container. Start name server.
```
# python3 code/NameServer.py
```
Enter network address with netmask where all storage servers are situated.
```
Input network address where storages are situated: <net address with netmask>
```
Example:
```
Input network address where storages are situated: 172.31.0.0/20
```
The program will remember this choice. To reset, delete file `storage_net.txt` inside container.

Wait until program response.
```
Server started
```
Press Ctrl+Z and then type `bg 1`.
```
^Z
[1]+  Stopped                 python3 code/StorageServer.py
# bg 1
[1]+ python3 code/StorageServer.py &
```
Server is running. It will find available storages automatically. You may look logs in file `Nlog.txt`.

#### Shutdown

Type `fg 1` and then press Ctrl+C. Do not press Ctrl+C again, wait until program will end. 
Name server writes to disk its own virtual file system and virtual file systems of all connected storages. 
Its own VFS is saved to file `ActualFS.txt`. VFS of each storage server is written to `storage_backup` directory under IP of storage server.
