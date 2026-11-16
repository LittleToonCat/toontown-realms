cd `dirname $0`
cd ..
cd astron

DYLD_LIBRARY_PATH=lib ./astrond-darwin --loglevel info config/astrond.yml
