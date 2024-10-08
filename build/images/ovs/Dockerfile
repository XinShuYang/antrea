# Copyright 2022 Antrea Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:24.04 AS ovs-debs

# Some patches may not apply cleanly if a non-default version is provided.
# See build/images/deps/ovs-version for the default version.
ARG OVS_VERSION

# Install dependencies for building OVS deb packages
# We only install python3 packages and we only support building OVS >= 2.13.0.
RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends wget curl git ca-certificates build-essential fakeroot \
            bzip2 autoconf automake debhelper dh-python dh-autoreconf libssl-dev libtool openssl procps \
            python3-all python3-twisted python3-zope.interface python3-sphinx \
            libunbound-dev

COPY apply-patches.sh /

# Download OVS source code and build debs
RUN wget -q -O - https://www.openvswitch.org/releases/openvswitch-$OVS_VERSION.tar.gz  | tar xz -C /tmp && \
    cd /tmp/openvswitch* && \
    /apply-patches.sh && \
    DEB_BUILD_OPTIONS='parallel=8 nocheck' fakeroot debian/rules binary && \
    cd /tmp && mkdir ovs-debs && \
    mv libopenvswitch_*.deb openvswitch-common_*.deb openvswitch-switch_*.deb python*-openvswitch_*.deb \
       openvswitch-ipsec_*.deb ovs-debs/ && \
    cd / && rm -rf /tmp/openvswitch*


FROM ubuntu:24.04

LABEL maintainer="Antrea <projectantrea-dev@googlegroups.com>"
LABEL description="A Docker image based on Ubuntu 24.04 which includes Open vSwitch built from source."

COPY --from=ovs-debs /tmp/ovs-debs/* /tmp/ovs-debs/
COPY charon-logging.conf /tmp

# Install OVS debs, iptables, logrotate, and strongSwan; update the OVS
# logrotate config file; update the strongSwan logging config.
# We clean-up apt cache after installing packages to reduce the size of the
# final image.
RUN apt-get update && \
    apt-get install -y --no-install-recommends iptables logrotate libstrongswan-standard-plugins && \
    # -f / --fix-broken will take care of installing all missing dependencies
    apt-get -f -y --no-install-recommends install /tmp/ovs-debs/*.deb && \
    # make sure that openvswitch packages will not be upgraded by mistake
    # in practice, the packages should not be upgraded anyway since they were installed using a .deb
    apt-mark hold *openvswitch* && \
    rm -rf /var/cache/apt/* /var/lib/apt/lists/* && \
    sed -i "/rotate /a\    #size 100M" /etc/logrotate.d/openvswitch-switch && \
    sed -i "/^.*filelog.*{/r /tmp/charon-logging.conf" /etc/strongswan.d/charon-logging.conf && \
    rm -rf /tmp/*
