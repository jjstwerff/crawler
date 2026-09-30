#!/usr/bin/env bash
# K2 live smoke (plan #6): host + observer on one Xvfb display — drive the
# host with held keys, stop it, then compare the two exit lines: the scene keys
# MUST be equal (the replica invariant, live over the wire). Run:
#   FLAGS="<the LOFTFLAGS lib list>" xvfb-run -a -s "-screen 0 800x600x24" tools/k2_smoke.sh
# then: grep key= /tmp/k2_host.log /tmp/k2_obs.log
set +e
export LIBGL_ALWAYS_SOFTWARE=1
loft --interpret $FLAGS src/story.loft > /tmp/k2_host.log 2>&1 &
HPID=$!
HW=""
for _ in $(seq 1 40); do sleep 0.5; HW=$(xdotool search --name "M0" 2>/dev/null | tail -1); [ -n "$HW" ] && break; done
[ -z "$HW" ] && { echo "no host window"; kill $HPID; exit 1; }
sleep 2   # host fully up
loft --interpret $FLAGS src/observe.loft > /tmp/k2_obs.log 2>&1 &
OPID=$!
OW=""
for _ in $(seq 1 40); do sleep 0.5; OW=$(xdotool search --name "observer" 2>/dev/null | tail -1); [ -n "$OW" ] && break; done
[ -z "$OW" ] && { echo "no observer window"; kill $HPID $OPID; exit 1; }
sleep 3   # genesis + replay settle
xdotool windowfocus "$HW"; sleep 0.3
xdotool keydown w; sleep 1.5; xdotool keyup w       # glide forward ~90 ticks
sleep 0.5
xdotool keydown a; sleep 0.5; xdotool keyup a       # turn
sleep 2                                              # let the observer drain
xdotool windowfocus "$HW"; sleep 0.3
xdotool keydown Escape; sleep 0.4; xdotool keyup Escape
for _ in $(seq 1 20); do kill -0 $HPID 2>/dev/null || break; sleep 0.5; done
for _ in $(seq 1 20); do kill -0 $OPID 2>/dev/null || break; sleep 0.5; done
kill $HPID $OPID 2>/dev/null
exit 0
