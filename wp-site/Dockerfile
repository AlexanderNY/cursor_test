FROM wordpress:6.6-php8.2-apache

RUN apt-get update \
	&& apt-get install -y --no-install-recommends libpq-dev curl \
	&& docker-php-ext-install pdo pdo_pgsql pgsql \
	&& rm -rf /var/lib/apt/lists/*

# PG4WP v3 (tested with WP 6.5.x). Drop-in intercepts mysqli for PostgreSQL.
ARG PG4WP_REF=ea843d1560a40cce42b9297323636bde59a9bc70
RUN curl -fsSL "https://codeload.github.com/PostgreSQL-For-Wordpress/postgresql-for-wordpress/tar.gz/${PG4WP_REF}" \
	| tar -xz -C /tmp \
	&& mv "/tmp/postgresql-for-wordpress-${PG4WP_REF}/pg4wp" /opt/pg4wp \
	&& rm -rf "/tmp/postgresql-for-wordpress-${PG4WP_REF}"

# INSERT IGNORE (core_updater.lock) is rewritten to INSERT INTO before insert-id
# lookup. Stock PG4WP still parses the original SQL, so the table name is empty
# and the catalog query becomes ''::regclass. WordPress then reports the update
# as already in progress.
COPY patches/pg4wp-insert-ignore-regclass.patch /tmp/pg4wp-insert-ignore-regclass.patch
RUN patch -p1 -d /opt/pg4wp < /tmp/pg4wp-insert-ignore-regclass.patch \
	&& rm /tmp/pg4wp-insert-ignore-regclass.patch

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
	&& chmod +x /usr/local/bin/docker-entrypoint.sh
