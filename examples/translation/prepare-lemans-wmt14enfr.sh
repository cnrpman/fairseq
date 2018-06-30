#!/bin/bash
# Adapted from https://github.com/pytorch/fairseq/blob/master/examples/translation/prepare-wmt14en2fr.sh
# Edited by Junyi

echo 'Cloning Moses github repository (for tokenization scripts)...'
git clone https://github.com/moses-smt/mosesdecoder.git

SCRIPTS=mosesdecoder/scripts
TOKENIZER=$SCRIPTS/tokenizer/tokenizer.perl
NORM_PUNC=$SCRIPTS/tokenizer/normalize-punctuation.perl
REM_NON_PRINT_CHAR=$SCRIPTS/tokenizer/remove-non-printing-char.perl

URLS=(
    "http://www-lium.univ-lemans.fr/~schwenk/cslm_joint_paper/data/bitexts.tgz"
    "http://www-lium.univ-lemans.fr/~schwenk/cslm_joint_paper/data/dev+test.tgz"
)
FILES=(
    "bitexts.tgz"
    "dev+test.tgz"
)
TRAIN_DIR="bitexts.selected"
VALID_PATH="dev/ntst1213"
TEST_PATH="dev/ntst14"

if [ ! -d "$SCRIPTS" ]; then
    echo "Please set SCRIPTS variable correctly to point to Moses scripts."
    exit
fi

src=en
tgt=fr
lang=en-fr
prep=lemans_wmt14_en_fr
tmp=$prep/tmp
orig=orig

mkdir -p $orig $tmp $prep

cd $orig

echo "downloading and unpacking..."
for ((i=0;i<${#URLS[@]};++i)); do
    file=${FILES[i]}
    if [ -f $file ]; then
        echo "$file already exists, skipping download"
    else
        url=${URLS[i]}
        wget "$url"
        if [ -f $file ]; then
            echo "$url successfully downloaded."
        else
            echo "$url not successfully downloaded."
            exit -1
        fi
        tar zxvf $file
    fi
done

gunzip $TRAIN_DIR/*.gz
cd ..

echo "combining train data..."
for l in $src $tgt; do
    cat $orig/$TRAIN_DIR/*.$l > $prep/train.$l
done

echo "moving data"
for l in $src $tgt; do
    mv $orig/$VALID_PATH.$l $prep/valid.$l
    mv $orig/$TEST_PATH.$l $prep/test.$l
done
