#!/bin/env bash
#================================================================
# HEADER
#================================================================
#% SYNOPSIS
#+    ${SCRIPT_NAME} [-h] [-o[SD_PATH]] [-i[ethoscope_ID]]
#%
#% DESCRIPTION
#%    Ethoscope Installation script
#%    Creates an SD card ready to go into an ethoscope
#%
#% OPTIONS
#%    -o [path]                 Set the pat to the SD CARD
#%    -i [id]                   Specify the ethoscope ID (integer)
#%    -h                        Print this help
#%
#% EXAMPLES
#%    ${SCRIPT_NAME} -o /dev/mmcblk0 -i 12
#%
#================================================================
#- IMPLEMENTATION
#-    version         ${SCRIPT_NAME} 1.0
#-    author          Giorgio Gilestro
#-    copyright       Copyright (c) http://lab.gilest.ro
#-    license         GNU General Public License
#-
#================================================================
#  HISTORY
#     2018/10/03 : ggilestro : Script created and released
# 
#================================================================
# END_OF_HEADER
#================================================================


   #== usage functions ==#
SCRIPT_HEADSIZE=$(head -200 ${0} |grep -n "^# END_OF_HEADER" | cut -f1 -d:)
SCRIPT_NAME="$(basename ${0})"

usage() { printf "Usage: "; head -${SCRIPT_HEADSIZE:-99} ${0} | grep -e "^#+" | sed -e "s/^#+[ ]*//g" -e "s/\${SCRIPT_NAME}/${SCRIPT_NAME}/g" ; }
usagefull() { head -${SCRIPT_HEADSIZE:-99} ${0} | grep -e "^#[%+-]" | sed -e "s/^#[%+-]//g" -e "s/\${SCRIPT_NAME}/${SCRIPT_NAME}/g" ; exit 1;}
scriptinfo() { head -${SCRIPT_HEADSIZE:-99} ${0} | grep -e "^#-" | sed -e "s/^#-//g" -e "s/\${SCRIPT_NAME}/${SCRIPT_NAME}/g"; }


WEB_URL="https://s3.amazonaws.com/ethoscope/"
OS_FILE="ethoscope_os_20160721.tar.gz"
TMP_DIR=/tmp
MIN_CARD_SIZE=8589934592 #8GB


prompt_confirm() {
  while true; do
    read -r -n 1 -p "${1:-Continue?} [y/n]: " REPLY
    case $REPLY in
      [yY]) echo ; return 0 ;;
      [nN]) echo ; return 1 ;;
      *) printf " \033[31m %s \n\033[0m" "invalid input"
    esac 
  done  
}

#Check if options were passed
while getopts o:i:h: option
  do
    case "${option}"
    in
      o) SDCARD=${OPTARG};;
      i) ID=${OPTARG};;
      h) usagefull;;
    esac
  done

#Check root permissions or exit
if [[ $EUID -ne 0 ]]; then
   echo "Error: This script must be run as root. Exiting now." 
   exit 1
fi


echo "Welcome to the ETHOSCOPE installation script".
echo "This program will help you create a new SD card for your machine."
read -p "Please press the Enter key to get started."


#if SD CARD Path is not passed by the user, try to detect it automatically
if [[ -z $SDCARD ]]; then
   echo "You have not passed a path to your SD card." 
   echo "I will try to identify this automatically for you"
   echo "To start, make sure your SD card is NOT inserted into this machine".
   read -p "If it is currently inserted, please remove it now, then press the Enter key to continue"
   lsblk -dp | grep -o '^/dev[^ ]*' > ${TMP_DIR}/before-sd

   read -p "Now please insert the card and press the Enter key when ready."
   sleep 2
   lsblk -dp | grep -o '^/dev[^ ]*' > ${TMP_DIR}/after-sd

   NUMCARD=`diff ${TMP_DIR}/before-sd ${TMP_DIR}/after-sd | grep "^>" | wc -l`
   SDCARD=`diff ${TMP_DIR}/before-sd ${TMP_DIR}/after-sd | egrep "^>" | sed "s/> //"`
   CARDSIZE=`blockdev --getsize64 $SDCARD`
    
   if [[ $NUMCARD != 1 ]]; then
      echo "Something is wrong. I found more than 1 card. Exiting now"
      exit 1
   fi

   if [[ -z $SDCARD ]]; then
      echo "I could not find any card. Exiting now."
      exit 1
   fi
   
   if (( $CARDSIZE <= $MIN_CARD_SIZE )); then
      echo "The card size is too small. You should be using a card with at least 8GB capacity (32GB reccomended). Exiting now."
      exit 1
   fi
   
   
   echo "I found a card on path $SDCARD with size ${CARDSIZE} byte"
   prompt_confirm "Do you want to continue using this card?" || exit 0
fi

#If Ethoscope ID was not passed on commandline, prompt the user for it
if [[ -z $ID ]]; then
   echo "You have not passed an ID for the ethoscope you are making." 
   read -p "Which number do you want to assign to this machine? If this is the first machine you are creating, use 1: " ID

   if ! [[ "$ID" =~ ^[0-9]+$ ]]
      then
        echo "Sorry integers only"
        exit 1
   fi

   prompt_confirm "This will be ethoscope_`printf "%03d" $ID`. Do you want to continue?" || exit 0
fi

ID=`printf "%03d" $ID`

#All the info are gathered, proceed.
echo "I will now create a card for ethoscope $ID using the card in $SDCARD"
prompt_confirm "Are you sure this is what you want to do?" || exit 0

#Create partitions
echo -e "Creating partitions\n"
echo "o
p
n
p
1

+100M
t
c
n
p
2


w"| fdisk $SDCARD || exit 1

echo -e "Partitions succesfully created\n"

#Formatting partitions
echo "Formatting the partitions"
mkdir -p ${TMP_DIR}/{boot,root}

if [[ $SDCARD = *"mmcbl"*  ]] ; then
   PART1=${SDCARD}p1
   PART2=${SDCARD}p2
fi

if [[ $SDCARD == "/dev/sd"* ]] ; then
   PART1=${SDCARD}1
   PART2=${SDCARD}2
fi

if [[ -z $PART1 ]]; then
   echo "Problem finding partitions. Exiting"
   exit 1
fi

umount /dev/mmcblk0* || [ $? -eq 1 ]

mkfs.vfat ${PART1} || exit 1
mount ${PART1} ${TMP_DIR}/boot || exit 1
mkfs.ext4 ${PART2} || exit 1 
mount ${PART2} ${TMP_DIR}/root || exit 1


echo "Downloading last version of the file if not yet present. This may take a while"

cd ${TMP_DIR}
wget -c ${WEB_URL}${OS_FILE} || exit 1

echo "Uncompressing the file - this may take some time. Please wait"

bsdtar -vxpf ${TMP_DIR}/${OS_FILE} -C ${TMP_DIR}/root || exit 1
sync
mv ${TMP_DIR}/root/boot/* ${TMP_DIR}/boot/

echo "now writing the information regarding ID"
UUID=`blkid $PART1 | egrep '[0-9A-F]{4}-[0-9A-F]{4}' -o`
echo ${ID}-${UUID} > ${TMP_DIR}/root/etc/machine-id
echo "ethoscope_$ID" > ${TMP_DIR}/root/etc/machine-name
echo "ethoscope_$ID" > ${TMP_DIR}/root/etc/hostname

umount ${TMP_DIR}/{boot,root}
rm -f ${TMP_DIR}/{before-sd,after-sd}

echo "All done! You can now remove the card and insert it into your new ethoscope"

