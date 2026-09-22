#!/usr/bin/env bash
set -Eeuo pipefail

wait_for_postgres() {
	local host="${WORDPRESS_DB_HOST:-host.docker.internal}"
	local port="5432"
	if [[ "$host" == *:* ]]; then
		port="${host##*:}"
		host="${host%%:*}"
	fi
	echo >&2 "Waiting for PostgreSQL at ${host}:${port} db=${WORDPRESS_DB_NAME:-db_wp}..."
	php -r '
		$host = getenv("WORDPRESS_DB_HOST") ?: "host.docker.internal";
		$port = "5432";
		if (str_contains($host, ":")) {
			[$host, $port] = explode(":", $host, 2);
		}
		$dsn = sprintf(
			"pgsql:host=%s;port=%s;dbname=%s",
			$host,
			$port,
			getenv("WORDPRESS_DB_NAME") ?: "db_wp"
		);
		$user = getenv("WORDPRESS_DB_USER") ?: "postgres";
		$password = getenv("WORDPRESS_DB_PASSWORD") ?: "";
		for ($i = 0; $i < 30; $i++) {
			try {
				new PDO($dsn, $user, $password);
				fwrite(STDERR, "PostgreSQL is ready\n");
				exit(0);
			} catch (Throwable $exception) {
				sleep(2);
			}
		}
		fwrite(STDERR, "PostgreSQL is not reachable\n");
		exit(1);
	'
}

install_pg4wp() {
	local dest="/var/www/html/wp-content"
	if [ ! -d /opt/pg4wp ]; then
		echo >&2 "PG4WP is missing at /opt/pg4wp"
		return 1
	fi
	mkdir -p "$dest"
	rm -rf "$dest/pg4wp"
	cp -a /opt/pg4wp "$dest/pg4wp"
	cp /opt/pg4wp/db.php "$dest/db.php"
	if [ "$(id -u)" = '0' ]; then
		chown -R www-data:www-data "$dest/pg4wp" "$dest/db.php" || true
	fi
	echo >&2 "PG4WP drop-in installed in wp-content"
}

if [[ "${1-}" == apache2* ]] || [ "${1-}" = 'php-fpm' ]; then
	uid="$(id -u)"
	gid="$(id -g)"
	if [ "$uid" = '0' ]; then
		case "$1" in
			apache2*)
				user="${APACHE_RUN_USER:-www-data}"
				group="${APACHE_RUN_GROUP:-www-data}"
				pound='#'
				user="${user#$pound}"
				group="${group#$pound}"
				;;
			*)
				user='www-data'
				group='www-data'
				;;
		esac
	else
		user="$uid"
		group="$gid"
	fi

	wait_for_postgres

	if [ ! -e index.php ] && [ ! -e wp-includes/version.php ]; then
		if [ "$uid" = '0' ] && [ "$(stat -c '%u:%g' .)" = '0:0' ]; then
			chown "$user:$group" .
		fi

		echo >&2 "WordPress not found in $PWD - copying now..."
		if [ -n "$(find -mindepth 1 -maxdepth 1 -not -name wp-content)" ]; then
			echo >&2 "WARNING: $PWD is not empty! (copying anyhow)"
		fi
		sourceTarArgs=(
			--create
			--file -
			--directory /usr/src/wordpress
			--owner "$user" --group "$group"
		)
		targetTarArgs=(
			--extract
			--file -
		)
		if [ "$uid" != '0' ]; then
			targetTarArgs+=( --no-overwrite-dir )
		fi
		for contentPath in \
			/usr/src/wordpress/.htaccess \
			/usr/src/wordpress/wp-content/*/*/ \
		; do
			contentPath="${contentPath%/}"
			[ -e "$contentPath" ] || continue
			contentPath="${contentPath#/usr/src/wordpress/}"
			if [ -e "$PWD/$contentPath" ]; then
				echo >&2 "WARNING: '$PWD/$contentPath' exists! (not copying the WordPress version)"
				sourceTarArgs+=( --exclude "./$contentPath" )
			fi
		done
		tar "${sourceTarArgs[@]}" . | tar "${targetTarArgs[@]}"
		echo >&2 "Complete! WordPress has been successfully copied to $PWD"
	fi

	wpEnvs=( "${!WORDPRESS_@}" )
	if [ ! -s wp-config.php ] && [ "${#wpEnvs[@]}" -gt 0 ]; then
		for wpConfigDocker in \
			wp-config-docker.php \
			/usr/src/wordpress/wp-config-docker.php \
		; do
			if [ -s "$wpConfigDocker" ]; then
				echo >&2 "No 'wp-config.php' found in $PWD, but 'WORDPRESS_...' variables supplied; copying '$wpConfigDocker'"
				awk '
					/put your unique phrase here/ {
						cmd = "head -c1m /dev/urandom | sha1sum | cut -d\\  -f1"
						cmd | getline str
						close(cmd)
						gsub("put your unique phrase here", str)
					}
					{ print }
				' "$wpConfigDocker" > wp-config.php
				if [ "$uid" = '0' ]; then
					chown "$user:$group" wp-config.php || true
				fi
				break
			fi
		done
	fi

	install_pg4wp
fi

exec "$@"
