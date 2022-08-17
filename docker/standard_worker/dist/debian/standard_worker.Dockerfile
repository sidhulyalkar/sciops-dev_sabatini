ARG PY_VER
ARG WORKER_BASE_HASH
FROM datajoint/djbase:py${PY_VER}-debian-${WORKER_BASE_HASH}

USER root
RUN apt-get update && \
    apt-get install -y ssh git ffmpeg libsm6 libxext6

USER anaconda:anaconda

ARG REPO_OWNER
ARG REPO_NAME
WORKDIR $HOME

# Clone the workflow
RUN git clone -b sciops-dev https://github.com/datajoint-company/sciops-dev_sabatini.git

# Install the workflow
ARG DEPLOY_KEY
COPY --chown=anaconda $DEPLOY_KEY $HOME/.ssh/id_ed25519
RUN ssh-keyscan github.com >> $HOME/.ssh/known_hosts && \
    pip install ./${REPO_NAME}