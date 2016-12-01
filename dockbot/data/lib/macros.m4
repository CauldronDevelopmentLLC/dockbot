define(`CPU_COUNT', `$(grep -c ^processor /proc/cpuinfo)')
define(`CONCURRENCY', CPU_COUNT)

define(`_', `patsubst(`$1', `
', ` ')')

define(`WGET', `RUN wget --quiet _(`$1')')
