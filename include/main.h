// SPDX-License-Identifier: GPL-2.0-or-later
/*
 *  nautilus-btrfs/src/main.h
 *
 *  Copyright (C) 2023 Marko Petrović <petrovicmarko2006@gmail.com>
 */

#ifndef MAIN_H
#define MAIN_H

#define SNAPSHOT_CREATE		1
#define SUBVOL_DELETE		2
#define SUBVOL_CREATE		3
#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>

extern int parse_args(int argc, char* argv[]);

/* Error-checking functions as wrappers around regular system calls */
extern int open_check(const char *pathname, int flags);
extern void access_check(const char *pathname, int mode);
extern void chdir_check(const char *path);

#endif
