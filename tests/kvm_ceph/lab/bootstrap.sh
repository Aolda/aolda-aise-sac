#!/usr/bin/env bash
# Disposable Ubuntu 24.04 lab only. Refuses to replace an existing cluster.
# Run AFTER installing matching ceph-mon/mgr/osd/common packages.
set -euo pipefail
umask 077
[[ ${AISE_CEPH_LAB_CONFIRMED:-} == yes && $EUID == 0 ]]
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]]
[[ ! -e /etc/ceph/ceph.conf && ! -e /var/lib/ceph/osd/ceph-0 ]]
[[ ! -e /var/lib/aise-ceph-test ]]
install -d -m 0750 -g ceph /var/lib/aise-ceph-test
lab=/var/lib/aise-ceph-test
cluster_id=$(cat /proc/sys/kernel/random/uuid)
printf '%s\n' "$cluster_id" > "$lab/fsid"
cat > /etc/ceph/ceph.conf <<CONFIG
[global]
fsid = $cluster_id
mon_initial_members = aise-test
mon_host = 127.0.0.1
public_network = 127.0.0.0/8
cluster_network = 127.0.0.0/8
public_addr = 127.0.0.1
cluster_addr = 127.0.0.1
ms_bind_ipv6 = false
osd_pool_default_size = 1
osd_pool_default_min_size = 1
osd_memory_target = 1073741824
[mon]
mon_allow_pool_size_one = true
[osd.0]
bluestore_block_size = 3221225472
CONFIG
chmod 0644 /etc/ceph/ceph.conf
ceph-authtool --create-keyring "$lab/mon.keyring" --gen-key -n mon. >/dev/null
ceph-authtool --create-keyring /etc/ceph/ceph.client.admin.keyring --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow *' --cap mgr 'allow *' >/dev/null
ceph-authtool "$lab/mon.keyring" --import-keyring /etc/ceph/ceph.client.admin.keyring >/dev/null
monmaptool --create --add aise-test 127.0.0.1 --fsid "$cluster_id" "$lab/monmap"
chgrp ceph "$lab/mon.keyring" "$lab/monmap"
chmod 0640 "$lab/mon.keyring" "$lab/monmap"
install -d -o ceph -g ceph /var/lib/ceph/mon/ceph-aise-test
ceph-mon --mkfs -i aise-test --monmap "$lab/monmap" --keyring "$lab/mon.keyring" --setuser ceph --setgroup ceph
rm "$lab/mon.keyring" "$lab/monmap"
chown -R ceph:ceph /var/lib/ceph/mon/ceph-aise-test
systemctl start ceph-mon@aise-test
for attempt in $(seq 1 20); do
  if timeout 5 ceph status >/dev/null 2>&1; then break; fi
  sleep 1
done
timeout 10 ceph status
ceph mon enable-msgr2
ceph config set mon auth_allow_insecure_global_id_reclaim false
for option in auth_cluster_required auth_service_required auth_client_required; do
  ceph config set mon "$option" cephx
done
systemctl restart ceph-mon@aise-test
install -d -o ceph -g ceph /var/lib/ceph/mgr/ceph-aise-test
ceph auth get-or-create mgr.aise-test mon 'allow profile mgr' osd 'allow *' mds 'allow *' -o /var/lib/ceph/mgr/ceph-aise-test/keyring
chown ceph:ceph /var/lib/ceph/mgr/ceph-aise-test/keyring
systemctl start ceph-mgr@aise-test
osd_uuid=$(cat /proc/sys/kernel/random/uuid)
osd_secret=$(ceph-authtool --gen-print-key)
printf '{"cephx_secret":"%s"}\n' "$osd_secret" > "$lab/osd-new.json"
osd_id=$(ceph osd new "$osd_uuid" -i "$lab/osd-new.json")
[[ "$osd_id" == 0 ]]
install -d -o ceph -g ceph /var/lib/ceph/osd/ceph-0
ceph-authtool --create-keyring /var/lib/ceph/osd/ceph-0/keyring --name osd.0 --add-key "$osd_secret" >/dev/null
unset osd_secret
rm "$lab/osd-new.json"
# BlueStore regular-file backing: no partition, LVM or loop-device operations.
truncate -s 3G /var/lib/ceph/osd/ceph-0/block
chown -R ceph:ceph /var/lib/ceph/osd/ceph-0
ceph-osd -i 0 --mkfs --osd-uuid "$osd_uuid" --setuser ceph --setgroup ceph
systemctl start ceph-osd@0
ceph osd crush add osd.0 0.003 host=aise-test root=default
for attempt in $(seq 1 20); do
  if ceph osd stat -f json | python3 -c 'import json,sys; s=json.load(sys.stdin); sys.exit(not(s["num_up_osds"]==1 and s["num_in_osds"]==1))'; then break; fi
  sleep 2
done
ceph osd stat -f json | python3 -c 'import json,sys; s=json.load(sys.stdin); assert s["num_up_osds"]==1 and s["num_in_osds"]==1'
ceph osd pool create aise-security-test 8
ceph osd pool application enable aise-security-test rados
ceph auth get-or-create client.aise-test mon 'allow r' osd 'allow rw pool=aise-security-test' -o "$lab/client.keyring"
chmod 0600 "$lab/client.keyring"
printf 'aise isolated Ceph verification\n' > "$lab/input"
timeout 30 rados -n client.aise-test -k "$lab/client.keyring" -p aise-security-test put baseline-probe "$lab/input"
timeout 30 rados -n client.aise-test -k "$lab/client.keyring" -p aise-security-test get baseline-probe "$lab/output"
cmp "$lab/input" "$lab/output"
ceph status
