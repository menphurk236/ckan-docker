FROM openknowledge/ckan-base:2.9.9-py2

RUN  pip install -e git+https://github.com/ckan/ckanext-scheming.git@release-3.0.0#egg=ckanext-scheming

RUN  pip install -e git+https://github.com/ckan/ckanext-dcat.git@v1.4.0#egg=ckanext-dcat && \
    pip install -r https://raw.githubusercontent.com/ckan/ckanext-dcat/v1.4.0/requirements-py2.txt

# Install the extension(s) you wrote for your own project
RUN pip install -e 'git+https://github.com/menphurk236/ckanext-doat.git#egg=ckanext-doat'

# Install any extensions needed by your CKAN instance
# See Dockerfile.dev for more details and examples

# Copy custom initialization scripts
COPY docker-entrypoint.d/* /docker-entrypoint.d/

# Apply any patches needed to CKAN core or any of the built extensions (not the
# runtime mounted ones)
COPY patches ${APP_DIR}/patches

RUN for d in $APP_DIR/patches/*; do \
    if [ -d $d ]; then \
    for f in `ls $d/*.patch | sort -g`; do \
    cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
    done ; \
    fi ; \
    done
