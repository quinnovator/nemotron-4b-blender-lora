# sandbox/Dockerfile: pinned to the Blender version installed on the host (5.2.2 LTS)
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates wget xz-utils coreutils libgl1 libegl1 libxi6 libxxf86vm1 \
      libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 libxext6 libx11-6 \
      libwayland-client0 libdbus-1-3 && rm -rf /var/lib/apt/lists/*
ARG BLENDER_URL=https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz
RUN wget -qO- "$BLENDER_URL" | tar -xJ -C /opt \
 && ln -s /opt/blender-*/blender /usr/local/bin/blender
COPY base_empty.blend extract_scene.py save_scene.py run_job.sh /opt/
RUN chmod 0555 /opt/run_job.sh && chmod 0444 /opt/*.py /opt/base_empty.blend
