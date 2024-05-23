FROM thepaeth/ckan-base:2.9.9-py2

RUN pip install -e git+https://gitlab.nectec.or.th/opend/ckanext-xloader.git#egg=ckanext-xloader && \
    pip install -r ${SRC_DIR}/ckanext-xloader/requirements.txt && \
    pip install -r ${SRC_DIR}/ckanext-xloader/dev-requirements.txt && \
    pip install -U requests[security] && \
    # pip install -e ${SRC_DIR}/ckanext-pages && \
    pip install -e git+https://gitlab.nectec.or.th/opend/ckanext-thai_gdc.git#egg=ckanext-thai_gdc && \
    pip install -r ${SRC_DIR}/ckanext-thai-gdc/requirements.txt && \
    pip install -e git+https://github.com/ckan/ckanext-geoview.git#egg=ckanext-geoview && \
    pip install -e git+https://github.com/nectec-opend/ckanext-cesiumpreview.git#egg=ckanext-cesiumpreview && \
    pip install -e git+https://gitlab.nectec.or.th/opend/ckanext-discovery.git#egg=ckanext-discovery && \
    pip install -e git+https://github.com/conwetlab/ckanext-oauth2.git#egg=ckanext-oauth2 && \
    pip install -e git+https://gitlab.nectec.or.th/opend/ckanext-opendstats.git#egg=ckanext-opendstats


RUN pip install -e 'git+https://github.com/menphurk236/ckanext-doat.git#egg=ckanext-doat'
# Install and configure supervisor
RUN pip install supervisor && \
    mkdir /etc/supervisord.d

# Copy all setup files
COPY .setup ${APP_DIR}
COPY .\setup\supervisor.worker.conf /etc/supervisord.d/worker.conf
COPY .\setup\supervisor.cron.conf /etc/supervisord.d/cron.conf
COPY .\setup\supervisord.conf /etc/supervisord.conf
# COPY ./setup ${APP_DIR}
# COPY ./setup/supervisor.worker.conf /etc/supervisord.d/worker.conf
# COPY ./setup/supervisord.conf /etc/supervisord.con

# Create a local user and group to run the app
RUN addgroup -S -g 92 ckan && \
    # adduser -S -G ckan -u 92 ckan -h /srv/app
    adduser -u 92 -h /home/ckan -s /bin/bash -D -G ckan ckan
# adduser -u 92 -h /srv/app -H -D -S -G ckan 

# Create local storage folder
RUN mkdir -p $CKAN_STORAGE_PATH && \
    chown -R ckan:ckan $CKAN_STORAGE_PATH && \
    rm -rf /root/.cache/pip/*

# Create ckan cron job file
RUN echo "0 * * * * ckan -c /srv/app/ckan.ini tracking update >> /var/log/ckan_tracking.log && ckan -c /srv/app/ckan.ini search-index rebuild -r >> /var/log/ckan_rebuild.log" > /etc/crontabs/root

RUN echo "0 0 * * * paster --plugin=ckanext-xloader xloader submit all -c /srv/app/ckan.ini >> /var/log/ckan_xloader.log" >> /etc/crontabs/root

RUN echo "0 0 * * * ckan -c /srv/app/ckan.ini opendstats fetch >> /var/log/ckanext_opendstats.log" >> /etc/crontabs/root

VOLUME $CKAN_STORAGE_PATH

# Create entrypoint directory for children image scripts
ONBUILD RUN mkdir /docker-entrypoint.d

RUN chown -R ckan /srv/app && \
    chmod -R +x /srv/app/prerun.py /srv/app/start_ckan.sh

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD curl --fail http://localhost:5000/api/3/action/status_show || exit 1

ENTRYPOINT ["/srv/app/start_ckan.sh"]
# CMD [ "ls", "-la" ]
