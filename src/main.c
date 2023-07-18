// SPDX-License-Identifier: GPL-2.0-or-later
/*
 *  nautilus-btrfs/src/main.c
 *
 *  Copyright (C) 2023 Marko Petrović <petrovicmarko2006@gmail.com>
 */

#include <unistd.h>
#include <main.h>
#include <sys/ioctl.h>
#include <linux/btrfs.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <linux/limits.h>

int main(int argc, char *argv[], char *envp[])
{
	int action = parse_args(argc, argv);
	if (action == SUBVOL_CREATE) {
		setuid(getuid());
		chdir_check(argv[2]);

		int parentfd = open_check(".", O_RDONLY | O_DIRECTORY);
		struct btrfs_ioctl_vol_args_v2 args = { 0 };
		strcpy(args.name, argv[3]);

		if (ioctl(parentfd, BTRFS_IOC_SUBVOL_CREATE_V2, &args) < 0) {
			fprintf(stderr, "Error creating subvolume!\n%m");
			exit(4);
		}
	}

	if (action == SNAPSHOT_CREATE) {
		char *parent_dir = malloc(PATH_MAX);
		/* PATH_MAX-1 in order to leave space for terminator byte */
		strncpy(parent_dir, argv[argc-2], PATH_MAX-1);
		strncat(parent_dir, "/..", PATH_MAX-1);
		
		
		access_check(argv[argc-2], R_OK);
		access_check(parent_dir, W_OK);
		
		/* Execute snapshot utility */
		execve("/bin/snapshot", argv, envp);
		execve("/sbin/snapshot", argv, envp);
		fprintf(stderr, "Error: Cannot launch helper /bin/snapshot utility!\n%m");
		exit(5);
	}

	if (action == SUBVOL_DELETE) {
		char *parent_dir = malloc(PATH_MAX);
		/* PATH_MAX-1 in order to leave space for terminator byte */
		strncpy(parent_dir, argv[argc-1], PATH_MAX-1);
		strncat(parent_dir, "/..", PATH_MAX-1);

		access_check(parent_dir, W_OK);

		/* Execute snapshot utility */
		execve("/bin/snapshot", argv, envp);
		execve("/sbin/snapshot", argv, envp);
		fprintf(stderr, "Error: Cannot launch helper /bin/snapshot utility!\n%m");
		exit(5);
	}
}
