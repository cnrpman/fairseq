SETTING=transformer_lm
LANG=en

CUDA_VISIBLE_DEVICES=0,1,2,3 python train.py data-bin/lm_wmt14_$LANG \
  --task language_modeling --arch $SETTING \
  --max-epoch 5 \
  --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 25.0 \
  --lr-scheduler inverse_sqrt --warmup-init-lr 1e-07 --warmup-updates 4000 \
  --lr 0.001 --min-lr 1e-09  \
  --dropout 0.025 --weight-decay 0.0 --criterion label_smoothed_cross_entropy --label-smoothing 0.1 \
  --update-freq 2 \
  --share-decoder-input-output-embed \
  --max-tokens 6144 --save-dir checkpoints/wmt14.lm.en.joined-dict.transformer.drop0001.25clip