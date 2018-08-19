TEXT=data/lm_wmt14_en_de
DESTFOLD=data-bin/lm_wmt14

# Do 2 languages' preprocessing parallelly
for LANG in en de; do
    DEST=${DESTFOLD}_$LANG
    SOURCE=data-bin/wmt14_en_de/dict.$LANG.txt

    python preprocess.py --only-source \
    --trainpref $TEXT/train.$LANG --validpref $TEXT/valid.$LANG --testpref $TEXT/test.$LANG \
    --destdir $DEST \
    --srcdict $SOURCE &
done