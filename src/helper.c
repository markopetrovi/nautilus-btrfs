// SPDX-License-Identifier: GPL-2.0-or-later
/*
 *  nautilus-btrfs/src/helper.c
 *
 *  Copyright (C) 2023 Marko Petrović <petrovicmarko2006@gmail.com>
 */

#include <main.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>

int parse_args(int argc, char* argv[])
{
	if (argc < 3)
		goto out;
	
	if (!strcmp(argv[1], "createsubvol")) {
		if (argc != 4)
			goto out;
		for (int i = 0; i < 255; i++) {
			if (argv[3][i] == '\0')
				return SUBVOL_CREATE;
		}
		fprintf(stderr, "Subvolume name is too large!\n");
		exit(1);
	}
	if (!strcmp(argv[1], "delete"))
		return SUBVOL_DELETE;
	if (!strcmp(argv[1], "create")) {
		if (argc < 4)
			goto out;
		for (int i = 0; i < 255; i++) {
			if (argv[argc-1][i] == '\0')
				return SNAPSHOT_CREATE;
		}
		fprintf(stderr, "Snapshot name is too large!\n");
		exit(1);
	}
	
out:
	fprintf(stderr, "Wrong usage of the helper program!\n"
		"This helper is part of the nautilus-btrfs extension. "
		"Use it only as a part of that extension.\n");
	exit(1);
}

/* Error-checking functions as wrappers around regular system calls */
int open_check(const char *pathname, int flags)
{
	int fd = open(pathname, flags);
	if (fd < 0) {
		fprintf(stderr, "open(%s) failed: %i\n%m", pathname, errno);
		exit(3);
	}
	return fd;
}
void access_check(const char *pathname, int mode)
{
	int ret = access(pathname, mode);
	if (ret < 0) {
		fprintf(stderr, "Error: %m\n%s", pathname);
		exit(6);
	}
}
void chdir_check(const char *path)
{
	int ret = chdir(path);
	if (ret < 0) {
		fprintf(stderr, "Error: %m\n%s", path);
		exit(7);
	}
}
