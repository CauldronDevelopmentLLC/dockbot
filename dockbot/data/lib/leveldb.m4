define(`LEVELDB_VERSION', ifdef(`LEVELDB_VERSION', LEVELDB_VERSION, 1.18))
define(`LEVELDB_BASE', leveldb-LEVELDB_VERSION)
define(`LEVELDB_PKG', `v'LEVELDB_VERSION.tar.gz)

WGET(https://github.com/google/leveldb/archive/LEVELDB_PKG)

RUN tar xf LEVELDB_PKG &&\
  cd LEVELDB_BASE &&\
  make &&\
  cp libleveldb.a /usr/lib &&\
  cp -av include/leveldb/ /usr/include/ &&\
  cd .. &&\
  rm -rf LEVELDB_PKG LEVELDB_BASE
