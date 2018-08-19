SETTING=transformer_lm
LANG=de

dr='0.005'
cl='0.0'
SAVE_DIR=checkpoints/wmt14.lm.$LANG.joined-dict.transformer.drop$dr.clip$cl
echo Using checkpoint destination $SAVE_DIR

CUDA_VISIBLE_DEVICES=0 python eval_lm.py data-bin/lm_wmt14_$LANG \
  --path $SAVE_DIR/checkpoint_best.pt \
  --max-tokens 4096  \
  --sample-break-mode eos
  #--gen-subset valid

