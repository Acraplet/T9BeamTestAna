#!/bin/bash

DATA_DIR=/data/wcte_data/
DEST=wcte-gw:/media/wcte/T7/WCTE/data/2023/
#rsync -aRv $DATA_DIR/./root_files/ $DEST
rsync -aRv $DATA_DIR/./midas_files/ $DEST
#rsync -aRv $DATA_DIR/./hist_files/ $DEST
