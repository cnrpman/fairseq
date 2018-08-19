SETTING=transformer_lm
LANG=de

dr='0.001'
cl='0.0'
SAVE_DIR=checkpoints/wmt14.lm.$LANG.joined-dict.transformer.drop$dr.clip$cl
echo Using checkpoint destination $SAVE_DIR

CUDA_VISIBLE_DEVICES=0,1,2,3 python train.py data-bin/lm_wmt14_$LANG \
  --task language_modeling --arch $SETTING \
  --sample-break-mode eos \
  --max-epoch 5 \
  --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm $cl \
  --lr-scheduler inverse_sqrt --warmup-init-lr 1e-07 --warmup-updates 4000 \
  --lr 0.001 --min-lr 1e-09  \
  --dropout $dr --weight-decay 0.0 --criterion label_smoothed_cross_entropy --label-smoothing 0.1 \
  --update-freq 2 \
  --shuffle \
  --share-decoder-input-output-embed \
  --max-tokens 6144 --save-dir $SAVE_DIR

CUDA_VISIBLE_DEVICES=0 python eval_lm.py data-bin/lm_wmt14_$LANG \
  --path $SAVE_DIR/checkpoint_best.pt \
  --max-tokens 4096  \
  --sample-break-mode eos 

