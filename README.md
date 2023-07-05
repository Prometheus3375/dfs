# Distributed File System
## 0. Requirements

If you are going to use source code, download and install [Python 3.7.5](https://www.python.org/downloads/release/python-375/).

I recommend to use [Docker](https://www.docker.com/), docker images for this project you can download [here](https://hub.docker.com/repository/docker/prometheus3375/dfs).

Servers where you are going to deploy this system must not use ports 9000 and 9001.

## 1. Installation
### General

To use this system you need to have at least 4 servers, they can be EC2 instances from Amazon Web Services.
1 server is name server. It manages other servers which are storage servers.
Name server communicates with client while storage serves store clients' files and communicates with clients only for file exchange.

### Storage Server

Download docker image of storage server.
```
$ docker pull prometheus3375/dfs:storage
```
Run container from this image.
```
$ docker run --name storage -ti -p 9001:9001/tcp prometheus3375/dfs:storage /bin/bash
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
$ docker pull prometheus3375/dfs:server
```
Run container from this image.
```
$ docker run --name server -ti -p 9000:9000/tcp prometheus3375/dfs:server /bin/bash
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

### Client

Download docker image of client.
```
$ docker pull prometheus3375/dfs:client
```
Run container from this image.
```
$ docker run --name client -ti prometheus3375/dfs:client /bin/bash
```
Bash will be opened inside container. Start client.
```
# python3 code/Client.py
```
Enter public IP address or domain name of name server.
```
Input DFS server IP address or domain name: <public Ip address or domain name>
```
Example:
```
Input DFS server IP address or domain name: 15.188.77.193
```
The program will remember this choice. To reset, delete file `server_ip.txt` inside container.


Client is running, you may send commands to name server. Type `exit` to exit.

## 2. Usage

### Name and Storage Servers

All necessary usage information is described in installation section.

### Client
Here is the list of all available commands.
1. `exit` - shutdowns client.
2. `cd <path>` - changes current working directory in local virtual file system (VFS).
3. `ls [<path>]` - lists contents of current working directory. If path argument is given, lists contents of specified directory.
4. `abs <path>` - prints absolute path of given path. Passed path must exist.
5. `walk` - prints all paths in local VFS.

All commands above do not require Internet connection. Connection to the name server is required on client startup and for all next commands.

1. `update` - updates local replica of VFS.
2. `flush` - cleans all storage servers and print available space.
3. `mkfile <path>` - creates empty file in specified path in DFS.
4. `mkdir <path>` - creates empty directory in specified path in DFS.
5. `info <path>` - gets size, last access and last modification time of specified file in DFS.
6. `rm <path>` - removes an entity from specified path in DFS. If this entity is non-empty directory, asks for confirmation.
7. `re <path> <new name>` - renames an entity from specified path in DFS.
8. `mv <what> <to>` - moves a file from `what` argument to directory `to`. This directory may not exist.
9. `cp <what> <to>` - copies a file from `what` argument to directory `to`. This directory may not exist.

For next commands connection to storage servers is required. Necessary storage server will be given by the name server.

1. `upload <local file> <path in DFS>` - uploads a file to DFS in specified path.
2. `download <file in DFS> <local path>` - downloads specified file from DFS.

**Be aware that all DFS paths are converted to lower case.**

## 3. Component diagram

![component diagram image](Diagrams/Component%20Diagram.png)
