CC := gcc
HEADER_DIR := ./include
SRC_DIR := src
SRCS := $(wildcard $(SRC_DIR)/*)

# Define the C++ object files:
#
# This uses Suffix Replacement within a macro:
#   $(name:string1=string2)
#         For each word in 'name' replace 'string1' with 'string2'.
# Below we are replacing the suffix .cpp of all words in the macro SRCS
# with the .o suffix.
#
OBJS := $(SRCS:.cpp=.o)
INCLUDES := -I$(HEADER_DIR)
HEADER_FILES := $(wildcard $(HEADER_DIR)/*)
USERNAME := $(shell logname)
XDG_DATA_HOME := $(shell bash -c '				\
	if [[ $$XDG_DATA_HOME == "" ]]; then			\
		XDG_DATA_HOME="/home/$$USERNAME/.local/share";	\
	fi;							\
	echo "$$XDG_DATA_HOME"					\
')

all: $(OBJS)
	$(CC) $(INCLUDES) -o nautilus-btrfs $(OBJS)
	@echo  "nautilus-btrfs has been compiled"
# This is a suffix replacement rule for building .o's from .cpp's.
# It uses automatic variables $<: the name of the prerequisite of
# the rule(a .cpp file) and $@: the name of the target of the rule (a .o file).
# (See the gnu make manual section about automatic variables)
%.o: %.cpp $(HEADER_FILES)
	$(CC) $(INCLUDES) -c $< -o $@
clean:
	rm -f $(SRC_DIR)/*.o
	rm -f nautilus-btrfs
install:
	cp nautilus-btrfs /usr/local/bin/nautilus-btrfs
	@chown root /usr/local/bin/nautilus-btrfs
	@chgrp root /usr/local/bin/nautilus-btrfs
	@chmod 4755 /usr/local/bin/nautilus-btrfs
	@mkdir -p "$(XDG_DATA_HOME)/nautilus-python/extensions"
	cp nautilus-btrfs.py "$(XDG_DATA_HOME)/nautilus-python/extensions/nautilus-btrfs.py"
	@chown $(USERNAME) "$(XDG_DATA_HOME)/nautilus-python/extensions/nautilus-btrfs.py"
	@chgrp $(USERNAME) "$(XDG_DATA_HOME)/nautilus-python/extensions/nautilus-btrfs.py"
	@chmod 755 "$(XDG_DATA_HOME)/nautilus-python/extensions/nautilus-btrfs.py"
	@echo "nautilus-btrfs utility has been installed"
remove:
	rm /usr/local/bin/nautilus-btrfs
	rm "$(XDG_DATA_HOME)/nautilus-python/extensions/nautilus-btrfs.py"
	@rm -rf "$(XDG_DATA_HOME)/nautilus-python/extensions/__pycache__"
	@echo "Snapshot utility has been removed"
